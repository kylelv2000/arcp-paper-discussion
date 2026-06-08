from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, request, flash
from arcp.extensions import db
from arcp.models import Paper

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    today = datetime.now().date()
    current_year = today.year
    
    # 获取所有论文，统一按日期升序排列
    papers = Paper.query.order_by(Paper.date).all()
    
    return render_template('index.html', papers=papers, today=today, current_year=current_year)

@main_bp.route('/paper/add', methods=['GET', 'POST'])
def add_paper():
    if request.method == 'POST':
        date_str = request.form['date']
        presenter = request.form['presenter']
        title = request.form['title']
        
        try:
            date_obj = datetime.strptime(date_str, '%Y/%m/%d').date()
            new_paper = Paper(date=date_obj, presenter=presenter, title=title)
            db.session.add(new_paper)
            db.session.commit()
            flash('论文安排已添加', 'success')
            return redirect(url_for('main.index'))
        except Exception as e:
            flash(f'添加失败: {str(e)}', 'danger')
    
    return render_template('paper_form.html')

@main_bp.route('/paper/edit/<int:id>', methods=['GET', 'POST'])
def edit_paper(id):
    paper = Paper.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            date_str = request.form['date']
            paper.date = datetime.strptime(date_str, '%Y/%m/%d').date()
            paper.presenter = request.form['presenter']
            paper.title = request.form['title']
            paper.updated_at = datetime.utcnow()
            db.session.commit()
            flash('论文安排已更新', 'success')
            return redirect(url_for('main.index'))
        except Exception as e:
            flash(f'更新失败: {str(e)}', 'danger')
    
    return render_template('paper_form.html', paper=paper)
