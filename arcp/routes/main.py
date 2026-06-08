from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import current_user
from arcp.extensions import db
from arcp.models import Paper
from arcp.services import ordered_members, next_open_meeting_date

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    today = datetime.now().date()
    current_year = today.year
    
    # 获取所有论文，统一按日期升序排列
    papers = Paper.query.order_by(Paper.date).all()

    # 讲解人 -> 年级标签，用于在安排表中展示
    presenter_grade = {m.name: m.grade_label for m in ordered_members()}

    return render_template(
        'index.html', papers=papers, today=today,
        current_year=current_year, presenter_grade=presenter_grade,
    )

@main_bp.route('/paper/add', methods=['GET', 'POST'])
def add_paper():
    # 仅管理员可新建安排；普通用户只能查看与修改
    if not current_user.is_authenticated or not current_user.is_admin:
        flash('无权限新建安排，请联系管理员', 'danger')
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        date_str = request.form['date']
        presenter = request.form['presenter']
        title = request.form.get('title', '').strip()

        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            new_paper = Paper(date=date_obj, presenter=presenter, title=title)
            db.session.add(new_paper)
            db.session.commit()
            flash('论文安排已添加', 'success')
            return redirect(url_for('main.index'))
        except Exception as e:
            flash(f'添加失败: {str(e)}', 'danger')

    # 默认日期：最近一个尚未排安排的开会日
    return render_template(
        'paper_form.html',
        members=ordered_members(),
        default_date=next_open_meeting_date().strftime('%Y-%m-%d'),
    )

@main_bp.route('/paper/edit/<int:id>', methods=['GET', 'POST'])
def edit_paper(id):
    paper = Paper.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            date_str = request.form['date']
            paper.date = datetime.strptime(date_str, '%Y-%m-%d').date()
            paper.presenter = request.form['presenter']
            paper.title = request.form.get('title', '').strip()
            paper.updated_at = datetime.utcnow()
            db.session.commit()
            flash('论文安排已更新', 'success')
            return redirect(url_for('main.index'))
        except Exception as e:
            flash(f'更新失败: {str(e)}', 'danger')

    return render_template('paper_form.html', paper=paper, members=ordered_members())
