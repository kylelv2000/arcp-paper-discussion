from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, current_app
from flask_login import login_user, login_required, logout_user, current_user
from flask_mail import Message
from arcp.extensions import db, mail
from arcp.models import User, Paper, EmailConfig, EmailRecipient

admin_bp = Blueprint('admin', __name__)

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
        
    recipients = EmailRecipient.query.all()
    return render_template('admin_dashboard.html', email_config=email_config, recipients=recipients)

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

@admin_bp.route('/admin/recipient/add', methods=['POST'])
@login_required
def add_recipient():
    if not current_user.is_admin:
        return jsonify({'status': 'error', 'message': '无权限'}), 403
        
    email = request.form['email']
    if EmailRecipient.query.filter_by(email=email).first():
        flash('该邮箱已存在', 'warning')
        return redirect(url_for('admin.admin_dashboard'))
        
    new_recipient = EmailRecipient(email=email)
    db.session.add(new_recipient)
    db.session.commit()
    flash('收件人已添加', 'success')
    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/admin/recipient/delete/<int:id>')
@login_required
def delete_recipient(id):
    if not current_user.is_admin:
        return jsonify({'status': 'error', 'message': '无权限'}), 403
        
    recipient = EmailRecipient.query.get_or_404(id)
    db.session.delete(recipient)
    db.session.commit()
    flash('收件人已删除', 'success')
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
    
    # 获取后续3次的安排
    future_papers = Paper.query.filter(Paper.date > upcoming_paper.date).order_by(Paper.date).limit(3).all()
    
    # 准备邮件内容
    subject = f"论文讲解提醒: {upcoming_paper.date.strftime('%Y/%m/%d')}"
    recipients = [r.email for r in EmailRecipient.query.all()]
    
    if not recipients:
        flash('没有收件人，请先添加收件人', 'warning')
        return redirect(url_for('admin.admin_dashboard'))
    
    body = f"""
提醒：下次论文讲解安排

时间：{upcoming_paper.date.strftime('%Y/%m/%d')}
讲解人：{upcoming_paper.presenter}
论文名称：{upcoming_paper.title}

未来安排：
"""
    
    for paper in future_papers:
        body += f"\n{paper.date.strftime('%Y/%m/%d')} - {paper.presenter} - {paper.title}"
    
    body += "\n\n请访问我们的网站 查看和编辑具体安排。"
    
    try:
        msg = Message(
            subject=subject, 
            recipients=recipients, 
            body=body,
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
