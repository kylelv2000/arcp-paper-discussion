"""讨论班排期相关的业务逻辑。"""
from datetime import date, timedelta
from arcp.extensions import db
from arcp.models import Member, MeetingConfig, Paper

# 安排新轮时，新建论文的占位标题
PLACEHOLDER_TITLE = '待定'


def ordered_members():
    """按自定义排序值返回在册（未归档）成员，用于下拉、排轮与展示。"""
    return (Member.query
            .filter_by(archived=False)
            .order_by(Member.order_index, Member.id)
            .all())


def archived_members():
    """返回已归档（毕业）成员，仅用于后台查看与恢复。"""
    return (Member.query
            .filter_by(archived=True)
            .order_by(Member.name)
            .all())


def get_meeting_weekday():
    cfg = MeetingConfig.query.first()
    return cfg.weekday if cfg else 2


def reset_member_order():
    """按"年级高低（博士先于硕士），相同年级按姓名字典序"重排在册成员。"""
    members = Member.query.filter_by(archived=False).all()
    members.sort(key=lambda m: (m.grade_priority, m.name))
    for index, member in enumerate(members):
        member.order_index = index
    db.session.commit()


def next_order_index():
    """新成员追加到末尾时使用的排序值。"""
    last = Member.query.order_by(Member.order_index.desc()).first()
    return (last.order_index + 1) if last else 0


def _next_meeting_on_or_after(d, weekday):
    return d + timedelta(days=(weekday - d.weekday()) % 7)


def _next_meeting_after(d, weekday):
    days = (weekday - d.weekday()) % 7
    return d + timedelta(days=days or 7)


def schedule_new_round():
    """将全体成员按顺序追加到时间表中，每周开会日各排一位。

    返回 (created_count, message)。
    """
    members = ordered_members()
    if not members:
        return 0, '没有可排期的成员，请先在后台添加成员'

    weekday = get_meeting_weekday()
    today = date.today()
    last = Paper.query.order_by(Paper.date.desc()).first()

    # 起始开会日：若已有未过期安排，则接在其后；否则从今天起最近的开会日
    if last and last.date >= today:
        start = _next_meeting_after(last.date, weekday)
    else:
        start = _next_meeting_on_or_after(today, weekday)

    for offset, member in enumerate(members):
        meeting_date = start + timedelta(weeks=offset)
        db.session.add(Paper(date=meeting_date, presenter=member.name, title=PLACEHOLDER_TITLE))
    db.session.commit()

    return len(members), f'已为 {len(members)} 位成员排好新一轮（自 {start.strftime("%Y/%m/%d")} 起）'


def notification_emails():
    """通知收件人 = 填写了邮箱的在册（未归档）成员。"""
    return [m.email for m in Member.query.filter(
        Member.archived == False,  # noqa: E712
        Member.email.isnot(None),
        Member.email != '',
    ).all()]
