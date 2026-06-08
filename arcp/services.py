"""讨论班排期相关的业务逻辑。"""
from datetime import date, timedelta
from flask import render_template
from arcp.extensions import db
from arcp.models import Member, MeetingConfig, Paper, WEEKDAY_LABELS

SITE_URL = 'https://arcp.kylelv.com'

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
    """按"年级高低（高年级优先），相同年级按姓名字典序"重排在册成员。"""
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


def next_open_meeting_date():
    """返回最近一个尚未排安排的开会日，用于新建安排时的默认日期。

    从今天起（含今天）找到最近的开会日，若该开会日已有安排则顺延一周，
    直到找到空闲的开会日。
    """
    weekday = get_meeting_weekday()
    today = date.today()
    candidate = _next_meeting_on_or_after(today, weekday)

    scheduled = {p.date for p in Paper.query.filter(Paper.date >= today).all()}
    while candidate in scheduled:
        candidate += timedelta(weeks=1)
    return candidate


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


def _format_paper(paper):
    """将 Paper 整理为邮件模板使用的简单结构。"""
    return {
        'date': paper.date.strftime('%Y/%m/%d'),
        'weekday': WEEKDAY_LABELS[paper.date.weekday()],
        'presenter': paper.presenter,
        'title': paper.title or '待定',
    }


def build_notification_content(paper, future_papers):
    """构建通知邮件的主题、纯文本与 HTML 内容。

    返回 (subject, text_body, html_body)，纯文本作为不支持 HTML 时的兜底。
    """
    main = _format_paper(paper)
    upcoming = [_format_paper(p) for p in future_papers]

    subject = f"论文讲解提醒：{main['date']}（{main['presenter']}）"

    lines = [
        '提醒：下次论文讲解安排', '',
        f"时间：{main['date']}（{main['weekday']}）",
        f"讲解人：{main['presenter']}",
        f"论文名称：{main['title']}", '',
    ]
    if upcoming:
        lines.append('后续安排：')
        for item in upcoming:
            lines.append(f"  {item['date']}（{item['weekday']}） - {item['presenter']} - {item['title']}")
        lines.append('')
    lines.append(f'请访问讨论班网站查看和编辑具体安排：{SITE_URL}')
    text_body = '\n'.join(lines)

    html_body = render_template(
        'email/notification.html',
        main=main,
        upcoming=upcoming,
        site_url=SITE_URL,
    )
    return subject, text_body, html_body
