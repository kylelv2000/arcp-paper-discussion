from datetime import datetime, timedelta
import atexit
from flask_mail import Message
from apscheduler.schedulers.background import BackgroundScheduler
from arcp.extensions import db, mail
from arcp.models import EmailConfig, Paper, SentNotification
from arcp.services import notification_emails, build_notification_content

def send_notification(app):
    """检查并发送邮件通知"""
    with app.app_context():
        config = EmailConfig.query.first()
        if not config or not config.enabled:
            return
        
        now = datetime.now()
        today = now.date()
        current_time = now.time()
        notification_time = config.notification_time
        
        # 计算当前时间与通知时间的分钟差
        current_minutes = current_time.hour * 60 + current_time.minute
        notification_minutes = notification_time.hour * 60 + notification_time.minute
        time_diff = abs(current_minutes - notification_minutes)
        
        # 只在通知时间前后30分钟内才发送
        if time_diff > 30:
            return
        
        # 计算应该发送通知的论文日期
        target_date = today + timedelta(days=config.days_before)
        
        # 查找目标日期的论文
        paper = Paper.query.filter(Paper.date == target_date).first()
        if not paper:
            return
        
        # 检查今天是否已经发送过这篇论文的通知
        existing = SentNotification.query.filter_by(
            paper_id=paper.id,
            sent_date=today
        ).first()
        if existing:
            return
        
        # 获取收件人列表（填写了邮箱的成员）
        recipients = notification_emails()
        if not recipients:
            return
        
        # 获取后续3次的安排
        future_papers = Paper.query.filter(Paper.date > paper.date).order_by(Paper.date).limit(3).all()

        # 准备邮件内容（HTML + 纯文本兜底）
        subject, text_body, html_body = build_notification_content(paper, future_papers)

        try:
            msg = Message(
                subject=subject,
                recipients=recipients,
                body=text_body,
                html=html_body,
                sender=('ARCP讨论班', app.config['MAIL_DEFAULT_SENDER'])
            )
            mail.send(msg)
            
            # 记录已发送，防止重复
            notification = SentNotification(paper_id=paper.id, sent_date=today)
            db.session.add(notification)
            db.session.commit()
            print(f"✓ 邮件通知已发送: {paper.title} ({paper.date})")
        except Exception as e:
            print(f"✗ 邮件发送失败: {str(e)}")

def init_scheduler(app):
    """初始化定时任务 - 每30分钟检查一次，确保不漏通知"""
    scheduler = BackgroundScheduler()
    # 每30分钟检查一次，配合30分钟时间窗口，保证至少检查一次
    scheduler.add_job(
        func=send_notification, 
        trigger='interval',
        minutes=30,
        args=[app],
        id='email_notification'
    )
    scheduler.start()
    
    # 启动时立即检查一次
    send_notification(app)
    
    # 确保应用退出时关闭定时任务
    atexit.register(lambda: scheduler.shutdown())
    return scheduler
