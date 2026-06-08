"""应用启动时的数据库自举与轻量迁移。

项目未使用 Alembic，新增的表通过 ``db.create_all()`` 自动补齐；
对于历史部署，将已有讲解人/收件人迁移为成员，保证下拉与通知可用。
"""
from arcp.extensions import db
from arcp.models import Member, MeetingConfig, EmailRecipient, Paper


def ensure_database(app):
    with app.app_context():
        # 仅创建缺失的表，不会改动已存在的表
        db.create_all()

        # 确保存在每周开会日配置
        if not MeetingConfig.query.first():
            db.session.add(MeetingConfig())

        # 首次引入成员表时，从历史数据迁移成员，避免下拉为空、收件人丢失
        if not Member.query.first():
            _seed_members_from_history()

        db.session.commit()


def _seed_members_from_history():
    seen = set()
    order = 0

    # 1) 已有讲解人 -> 成员（年级未知，默认硕士，邮箱留空待补全）
    for (name,) in db.session.query(Paper.presenter).distinct():
        if name and name not in seen:
            db.session.add(Member(name=name, grade='master', email=None, order_index=order))
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
        db.session.add(Member(name=name, grade='master', email=recipient.email, order_index=order))
        seen.add(name)
        order += 1
