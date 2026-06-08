from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, current_app
from flask_login import login_user, login_required, logout_user, current_user
from flask_mail import Message
from arcp.extensions import db, mail
from arcp.models import User, Paper, EmailConfig, Member, MeetingConfig, WEEKDAY_LABELS, GRADE_CHOICES, GRADE_MIN, GRADE_MAX
from arcp.services import (
    ordered_members, archived_members, reset_member_order, next_order_index,
    notification_emails, schedule_new_round, build_notification_content,
)

admin_bp = Blueprint('admin', __name__)


def _parse_grade(raw, fallback):
    """将表单年级解析为 1~8 的整数，非法时返回 fallback。"""
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return fallback
    return value if GRADE_MIN <= value <= GRADE_MAX else fallback

@admin_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated:
        return redirect(url_for('admin.admin_dashboard'))
        
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password) and user.is_admin:
            login_user(user)
            return redirect(url_for('admin.admin_dashboard'))
        else:
            flash('登录失败，请检查用户名和密码', 'danger')
    
    return render_template('admin_login.html')

@admin_bp.route('/admin/logout')
@login_required
def admin_logout():
    logout_user()
    flash('已退出登录', 'success')
    return redirect(url_for('main.index'))

@admin_bp.route('/admin/change_password', methods=['POST'])
@login_required
def change_admin_password_web():
    if not current_user.is_admin:
        flash('无权限修改密码', 'danger')
        return redirect(url_for('main.index'))
        
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    # 验证当前密码
    if not current_user.check_password(current_password):
        flash('当前密码不正确', 'danger')
        return redirect(url_for('admin.admin_dashboard'))
    
    # 验证新密码长度
    if len(new_password) < 8:
        flash('新密码长度必须至少为8个字符', 'danger')
        return redirect(url_for('admin.admin_dashboard'))
    
    # 验证两次输入的新密码是否一致
    if new_password != confirm_password:
        flash('两次输入的新密码不一致', 'danger')
        return redirect(url_for('admin.admin_dashboard'))
    
    # 修改密码
    current_user.set_password(new_password)
    db.session.commit()
    flash('密码已成功修改', 'success')
    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('无权限访问此页面', 'danger')
        return redirect(url_for('main.index'))
        
    email_config = EmailConfig.query.first()
    if not email_config:
        email_config = EmailConfig()
        db.session.add(email_config)
        db.session.commit()

    meeting_config = MeetingConfig.query.first()
    if not meeting_config:
        meeting_config = MeetingConfig()
        db.session.add(meeting_config)
        db.session.commit()

    members = ordered_members()
    archived = archived_members()
    return render_template(
        'admin_dashboard.html',
        email_config=email_config,
        members=members,
        archived_members=archived,
        meeting_config=meeting_config,
        weekday_labels=WEEKDAY_LABELS,
        grade_choices=GRADE_CHOICES,
    )

@admin_bp.route('/admin/meeting_config', methods=['POST'])
@login_required
def update_meeting_config():
    if not current_user.is_admin:
        return jsonify({'status': 'error', 'message': '无权限'}), 403

    meeting_config = MeetingConfig.query.first()
    if not meeting_config:
        meeting_config = MeetingConfig()
        db.session.add(meeting_config)

    try:
        weekday = int(request.form['weekday'])
    except (KeyError, ValueError):
        weekday = meeting_config.weekday
    if 0 <= weekday <= 6:
        meeting_config.weekday = weekday
    db.session.commit()
    flash('每周开会日已更新', 'success')
    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/admin/email_config', methods=['POST'])
@login_required
def update_email_config():
    if not current_user.is_admin:
        return jsonify({'status': 'error', 'message': '无权限'}), 403
        
    email_config = EmailConfig.query.first()
    if not email_config:
        email_config = EmailConfig()
        db.session.add(email_config)
    
    email_config.days_before = int(request.form['days_before'])
    time_str = request.form['notification_time']
    email_config.notification_time = datetime.strptime(time_str, '%H:%M').time()
    email_config.enabled = 'enabled' in request.form
    
    db.session.commit()
    flash('邮件通知设置已更新，下次检查时生效', 'success')
    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/admin/member/add', methods=['POST'])
@login_required
def add_member():
    if not current_user.is_admin:
        return jsonify({'status': 'error', 'message': '无权限'}), 403

    name = request.form.get('name', '').strip()
    grade = _parse_grade(request.form.get('grade'), GRADE_MIN)
    email = request.form.get('email', '').strip() or None

    if not name:
        flash('成员姓名不能为空', 'warning')
        return redirect(url_for('admin.admin_dashboard'))
    if Member.query.filter_by(name=name).first():
        flash('该成员已存在', 'warning')
        return redirect(url_for('admin.admin_dashboard'))

    member = Member(name=name, grade=grade, email=email, order_index=next_order_index())
    db.session.add(member)
    db.session.commit()
    flash('成员已添加', 'success')
    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/admin/member/edit/<int:id>', methods=['POST'])
@login_required
def edit_member(id):
    if not current_user.is_admin:
        return jsonify({'status': 'error', 'message': '无权限'}), 403

    member = Member.query.get_or_404(id)
    name = request.form.get('name', '').strip()
    grade = _parse_grade(request.form.get('grade'), member.grade)
    email = request.form.get('email', '').strip() or None

    if not name:
        flash('成员姓名不能为空', 'warning')
        return redirect(url_for('admin.admin_dashboard'))
    existing = Member.query.filter_by(name=name).first()
    if existing and existing.id != member.id:
        flash('已存在同名成员', 'warning')
        return redirect(url_for('admin.admin_dashboard'))

    member.name = name
    member.grade = grade
    member.email = email
    db.session.commit()
    flash('成员信息已更新', 'success')
    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/admin/member/delete/<int:id>')
@login_required
def delete_member(id):
    if not current_user.is_admin:
        return jsonify({'status': 'error', 'message': '无权限'}), 403

    member = Member.query.get_or_404(id)
    db.session.delete(member)
    db.session.commit()
    flash('成员已删除', 'success')
    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/admin/member/move/<int:id>/<direction>')
@login_required
def move_member(id, direction):
    if not current_user.is_admin:
        return jsonify({'status': 'error', 'message': '无权限'}), 403

    members = ordered_members()
    index = next((i for i, m in enumerate(members) if m.id == id), None)
    if index is None:
        flash('成员不存在', 'warning')
        return redirect(url_for('admin.admin_dashboard'))

    swap = index - 1 if direction == 'up' else index + 1
    if 0 <= swap < len(members):
        a, b = members[index], members[swap]
        a.order_index, b.order_index = b.order_index, a.order_index
        db.session.commit()
    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/admin/member/reset_order')
@login_required
def reset_member_order_route():
    if not current_user.is_admin:
        return jsonify({'status': 'error', 'message': '无权限'}), 403

    reset_member_order()
    flash('已按年级（高年级优先）与姓名重置排序', 'success')
    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/admin/member/archive/<int:id>')
@login_required
def archive_member(id):
    if not current_user.is_admin:
        return jsonify({'status': 'error', 'message': '无权限'}), 403

    member = Member.query.get_or_404(id)
    member.archived = True
    db.session.commit()
    flash(f'成员 {member.name} 已归档', 'success')
    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/admin/member/unarchive/<int:id>')
@login_required
def unarchive_member(id):
    if not current_user.is_admin:
        return jsonify({'status': 'error', 'message': '无权限'}), 403

    member = Member.query.get_or_404(id)
    member.archived = False
    member.order_index = next_order_index()
    db.session.commit()
    flash(f'成员 {member.name} 已恢复为在册成员', 'success')
    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/admin/send_notification_now')
@login_required
def send_notification_now():
    if not current_user.is_admin:
        flash('无权限访问此功能', 'danger')
        return redirect(url_for('main.index'))
    
    # 获取最近的讲解安排
    today = datetime.now().date()
    upcoming_paper = Paper.query.filter(Paper.date >= today).order_by(Paper.date).first()
    
    if not upcoming_paper:
        flash('没有找到未来的论文讲解安排', 'warning')
        return redirect(url_for('admin.admin_dashboard'))
    
    recipients = notification_emails()
    if not recipients:
        flash('没有收件人，请先在成员管理中为成员填写邮箱', 'warning')
        return redirect(url_for('admin.admin_dashboard'))

    # 获取后续3次的安排，准备 HTML + 纯文本内容
    future_papers = Paper.query.filter(Paper.date > upcoming_paper.date).order_by(Paper.date).limit(3).all()
    subject, text_body, html_body = build_notification_content(upcoming_paper, future_papers)

    try:
        msg = Message(
            subject=subject,
            recipients=recipients,
            body=text_body,
            html=html_body,
            sender=('ARCP讨论班', current_app.config['MAIL_DEFAULT_SENDER'])
        )
        mail.send(msg)
        flash('通知邮件已成功发送', 'success')
    except Exception as e:
        flash(f'邮件发送失败: {str(e)}', 'danger')

    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/paper/delete/<int:id>')
@login_required
def delete_paper(id):
    if not current_user.is_admin:
        flash('无权限删除论文安排', 'danger')
        return redirect(url_for('main.index'))
        
    paper = Paper.query.get_or_404(id)
    db.session.delete(paper)
    db.session.commit()
    flash('论文安排已删除', 'success')
    return redirect(url_for('main.index'))

@admin_bp.route('/papers/new_round')
@login_required
def new_round():
    if not current_user.is_admin:
        flash('无权限执行此操作', 'danger')
        return redirect(url_for('main.index'))

    count, message = schedule_new_round()
    flash(message, 'success' if count else 'warning')
    return redirect(url_for('main.index'))

@admin_bp.route('/papers/shift/<direction>')
@login_required
def shift_papers(direction):
    if not current_user.is_admin:
        flash('无权限执行此操作', 'danger')
        return redirect(url_for('main.index'))
        
    today = datetime.now().date()
    # 获取所有未过期的论文安排
    future_papers = Paper.query.filter(Paper.date >= today).all()
    
    if not future_papers:
        flash('没有找到未来的论文安排', 'warning')
        return redirect(url_for('main.index'))
    
    # 根据方向决定是顺延还是提前
    days = 7 if direction == 'forward' else -7
    
    # 修改日期
    for paper in future_papers:
        paper.date = paper.date + timedelta(days=days)
    
    db.session.commit()
    
    if direction == 'forward':
        flash(f'已将{len(future_papers)}个未过期安排顺延一周', 'success')
    else:
        flash(f'已将{len(future_papers)}个未过期安排提前一周', 'success')
    
    return redirect(url_for('main.index'))
