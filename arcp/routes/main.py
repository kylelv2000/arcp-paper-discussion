import os
import uuid
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from flask import (
    Blueprint, render_template, redirect, url_for, request, flash,
    current_app, send_from_directory, abort,
)
from flask_login import current_user
from arcp.extensions import db
from arcp.models import Member, Paper, ReimbursementAssignment, ReimbursementItem
from arcp.services import ordered_members, schedulable_members, next_open_meeting_date

main_bp = Blueprint('main', __name__)
PDF_MIMETYPES = {'application/pdf', 'application/x-pdf'}
QUARTER_RANGES = {
    1: '1月 - 3月',
    2: '4月 - 6月',
    3: '7月 - 9月',
    4: '10月 - 12月',
}


def _current_year_quarter():
    today = datetime.now().date()
    return today.year, (today.month - 1) // 3 + 1


def _validate_pdf_upload(file):
    if not file:
        return None

    original_name = file.filename or ''
    if not original_name:
        return None

    if not original_name.lower().endswith('.pdf'):
        raise ValueError('只能上传 PDF 文件')

    stream = file.stream
    stream.seek(0, os.SEEK_END)
    size = stream.tell()
    stream.seek(0)
    if size <= 0:
        raise ValueError('PDF 文件不能为空')
    if size > current_app.config['MAX_PDF_UPLOAD_SIZE']:
        raise ValueError('PDF 文件不能超过 20MB')

    header = stream.read(4)
    stream.seek(0)
    if header != b'%PDF':
        raise ValueError('文件内容不是有效的 PDF')
    if file.mimetype and file.mimetype not in PDF_MIMETYPES:
        raise ValueError('只能上传 PDF 文件')

    return original_name


def _delete_paper_pdf(filename):
    if not filename:
        return
    path = os.path.join(current_app.config['PAPER_UPLOAD_FOLDER'], filename)
    if os.path.exists(path):
        os.remove(path)


def _save_paper_pdf(paper, file):
    original_name = _validate_pdf_upload(file)
    if not original_name:
        return

    old_filename = paper.pdf_filename
    stored_name = f'{paper.id}-{uuid.uuid4().hex}.pdf'
    upload_dir = current_app.config['PAPER_UPLOAD_FOLDER']
    os.makedirs(upload_dir, exist_ok=True)

    file.save(os.path.join(upload_dir, stored_name))
    _delete_paper_pdf(old_filename)
    paper.pdf_filename = stored_name
    paper.pdf_original_filename = os.path.basename(original_name)


def _validate_reimbursement_content(content):
    value = (content or '').strip()
    if not value:
        raise ValueError('报销内容不能为空')
    if len(value.split()) > 50:
        raise ValueError('报销内容最多 50 词')
    return value


def _validate_member_name(member_name):
    value = (member_name or '').strip()
    if not value:
        raise ValueError('请选择用户')
    if not Member.query.filter_by(name=value, archived=False).first():
        raise ValueError('用户不存在或已归档')
    return value


def _validate_reimbursement_confirmations(form):
    if form.get('materials_complete') != '1':
        raise ValueError('请确认发票、付款记录、账单流水是否齐全')
    if form.get('teacher_acknowledged') != '1':
        raise ValueError('请确认该信息会给到相关老师审批')


def _require_current_reimbursement_period(year, quarter):
    current_year, current_quarter = _current_year_quarter()
    if year != current_year or quarter != current_quarter:
        raise ValueError('只能添加或修改当前季度的报销事项')


def _build_reimbursement_export_text(year, quarter, owner, items):
    lines = [
        f'{year} Q{quarter} 报销信息',
        f'负责人：{owner or "待安排"}',
        f'报销人数：{len(items)}',
        '',
    ]
    if not items:
        lines.append('当前季度暂无报销信息。')
        return '\n'.join(lines)

    for index, item in enumerate(items, start=1):
        lines.extend([
            f'{index}. {item.member_name}',
            f'报销信息：{item.content}',
            f'发票+付款记录+账单流水是否齐全：{"是" if item.materials_complete else "未确认"}',
            '说明：该信息将给到相关老师审批。',
            '',
        ])
    return '\n'.join(lines).rstrip()


@main_bp.route('/')
def index():
    today = datetime.now().date()
    current_year = today.year
    
    # 获取所有论文，统一按日期升序排列
    papers = Paper.query.order_by(Paper.date).all()

    # 讲解人 -> 年级标签，用于在安排表中展示
    presenter_grade = {m.name: m for m in ordered_members()}

    return render_template(
        'index.html', papers=papers, today=today,
        current_year=current_year, presenter_grade=presenter_grade,
    )


@main_bp.route('/reimbursements')
def reimbursements():
    today = datetime.now().date()
    current_year, current_quarter = _current_year_quarter()
    try:
        year = int(request.args.get('year', today.year))
    except (TypeError, ValueError):
        year = today.year

    assignments = {
        item.quarter: item
        for item in ReimbursementAssignment.query.filter_by(year=year).all()
    }
    items_by_quarter = {quarter: [] for quarter in range(1, 5)}
    items = ReimbursementItem.query.filter_by(year=year).order_by(
        ReimbursementItem.quarter,
        ReimbursementItem.created_at,
    ).all()
    for item in items:
        items_by_quarter.setdefault(item.quarter, []).append(item)

    quarters = []
    for quarter in range(1, 5):
        quarter_items = items_by_quarter.get(quarter, [])
        owner = assignments.get(quarter).student if assignments.get(quarter) else ''
        is_current = year == current_year and quarter == current_quarter
        quarters.append({
            'number': quarter,
            'label': f'Q{quarter}',
            'date_range': QUARTER_RANGES[quarter],
            'student': owner,
            'reimbursement_items': quarter_items,
            'is_current': is_current,
            'export_text': _build_reimbursement_export_text(year, quarter, owner, quarter_items),
        })

    return render_template(
        'reimbursements.html',
        year=year,
        quarters=quarters,
        members=ordered_members(),
        current_reimbursement_year=current_year,
        current_reimbursement_quarter=current_quarter,
    )


@main_bp.route('/reimbursements/items/add', methods=['POST'])
def add_reimbursement_item():
    current_year, current_quarter = _current_year_quarter()
    try:
        member_name = _validate_member_name(request.form.get('member_name'))
        content = _validate_reimbursement_content(request.form.get('content'))
        existing = ReimbursementItem.query.filter_by(
            year=current_year,
            quarter=current_quarter,
            member_name=member_name,
        ).first()
        if existing:
            raise ValueError('当前季度该用户已经添加过报销事项')
        _validate_reimbursement_confirmations(request.form)

        item = ReimbursementItem(
            year=current_year,
            quarter=current_quarter,
            member_name=member_name,
            content=content,
            materials_complete=True,
            teacher_acknowledged=True,
        )
        db.session.add(item)
        db.session.commit()
        flash('报销事项已添加', 'success')
    except IntegrityError:
        db.session.rollback()
        flash('当前季度该用户已经添加过报销事项', 'warning')
    except Exception as e:
        db.session.rollback()
        flash(f'添加失败: {str(e)}', 'danger')
    return redirect(url_for('main.reimbursements', year=current_year))


@main_bp.route('/reimbursements/items/<int:id>/edit', methods=['POST'])
def edit_reimbursement_item(id):
    item = ReimbursementItem.query.get_or_404(id)
    try:
        _require_current_reimbursement_period(item.year, item.quarter)
        item.content = _validate_reimbursement_content(request.form.get('content'))
        _validate_reimbursement_confirmations(request.form)
        item.materials_complete = True
        item.teacher_acknowledged = True
        item.updated_at = datetime.utcnow()
        db.session.commit()
        flash('报销事项已更新', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'更新失败: {str(e)}', 'danger')
    return redirect(url_for('main.reimbursements', year=item.year))


@main_bp.route('/reimbursements/items/<int:id>/delete', methods=['POST'])
def delete_reimbursement_item(id):
    item = ReimbursementItem.query.get_or_404(id)
    year = item.year
    try:
        _require_current_reimbursement_period(item.year, item.quarter)
        db.session.delete(item)
        db.session.commit()
        flash('报销事项已删除', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'删除失败: {str(e)}', 'danger')
    return redirect(url_for('main.reimbursements', year=year))

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
            db.session.flush()
            _save_paper_pdf(new_paper, request.files.get('pdf_file'))
            db.session.commit()
            flash('论文安排已添加', 'success')
            return redirect(url_for('main.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'添加失败: {str(e)}', 'danger')

    # 默认日期：最近一个尚未排安排的开会日
    return render_template(
        'paper_form.html',
        members=schedulable_members(),
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
            uploaded_pdf = request.files.get('pdf_file')
            if uploaded_pdf and uploaded_pdf.filename:
                _save_paper_pdf(paper, uploaded_pdf)
            elif request.form.get('remove_pdf') == '1':
                _delete_paper_pdf(paper.pdf_filename)
                paper.pdf_filename = None
                paper.pdf_original_filename = None
            paper.updated_at = datetime.utcnow()
            db.session.commit()
            flash('论文安排已更新', 'success')
            return redirect(url_for('main.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'更新失败: {str(e)}', 'danger')

    return render_template('paper_form.html', paper=paper, members=schedulable_members())


@main_bp.route('/paper/<int:id>/pdf')
def download_paper_pdf(id):
    paper = Paper.query.get_or_404(id)
    if not paper.pdf_filename:
        abort(404)

    path = os.path.join(current_app.config['PAPER_UPLOAD_FOLDER'], paper.pdf_filename)
    if not os.path.exists(path):
        abort(404)

    return send_from_directory(
        current_app.config['PAPER_UPLOAD_FOLDER'],
        paper.pdf_filename,
        as_attachment=True,
        download_name=paper.pdf_original_filename or 'paper.pdf',
        mimetype='application/pdf',
    )
