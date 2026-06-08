"""应用启动时的数据库自举与轻量迁移。

项目未使用 Alembic，新增的表通过 ``db.create_all()`` 自动补齐；
对于历史部署，将已有讲解人/收件人迁移为成员，保证下拉与通知可用。
"""
import os
from sqlalchemy import text, inspect
from arcp.extensions import db
from arcp.models import Member, MeetingConfig, EmailRecipient, Paper


def ensure_database(app):
    with app.app_context():
        os.makedirs(app.config['PAPER_UPLOAD_FOLDER'], exist_ok=True)
        os.makedirs(app.config['REIMBURSEMENT_UPLOAD_FOLDER'], exist_ok=True)

        # 仅创建缺失的表，不会改动已存在的表
        db.create_all()

        # 为已存在的表补齐新增列（create_all 不会修改既有表）
        _ensure_columns()

        # 确保存在每周开会日配置
        if not MeetingConfig.query.first():
            db.session.add(MeetingConfig())

        # 首次引入成员表时，从历史数据迁移成员，避免下拉为空、收件人丢失
        if not Member.query.first():
            _seed_members_from_history()

        db.session.commit()


def _ensure_columns():
    """针对 SQLite 的轻量列迁移：缺失则 ALTER TABLE 补齐。"""
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    if 'member' not in tables:
        return
    columns = {col['name'] for col in inspector.get_columns('member')}
    if 'archived' not in columns:
        db.session.execute(text(
            'ALTER TABLE member ADD COLUMN archived BOOLEAN NOT NULL DEFAULT 0'
        ))
        db.session.commit()

    # 历史的字符串年级（phd/master）迁移为 1~8 的整数年级
    db.session.execute(text("UPDATE member SET grade='5' WHERE grade='phd'"))
    db.session.execute(text("UPDATE member SET grade='2' WHERE grade='master'"))
    # 其余非 1~8 的非法值统一回落为 1 年级
    db.session.execute(text("UPDATE member SET grade='1' WHERE grade NOT GLOB '[1-8]'"))
    db.session.commit()

    if 'paper' in tables:
        paper_columns = {col['name'] for col in inspector.get_columns('paper')}
        if 'pdf_filename' not in paper_columns:
            db.session.execute(text('ALTER TABLE paper ADD COLUMN pdf_filename VARCHAR(255)'))
        if 'pdf_original_filename' not in paper_columns:
            db.session.execute(text('ALTER TABLE paper ADD COLUMN pdf_original_filename VARCHAR(255)'))
        db.session.commit()


def _seed_members_from_history():
    seen = set()
    order = 0

    # 1) 已有讲解人 -> 成员（年级未知，默认 1 年级，邮箱留空待补全）
    for (name,) in db.session.query(Paper.presenter).distinct():
        if name and name not in seen:
            db.session.add(Member(name=name, grade=1, email=None, order_index=order))
            seen.add(name)
            order += 1

    # 2) 已有邮件收件人 -> 成员（仅有邮箱，用邮箱本地名占位姓名）
    for recipient in EmailRecipient.query.all():
        local = recipient.email.split('@')[0]
        name = local
        suffix = 1
        while name in seen:
            suffix += 1
            name = f'{local}{suffix}'
        db.session.add(Member(name=name, grade=1, email=recipient.email, order_index=order))
        seen.add(name)
        order += 1
