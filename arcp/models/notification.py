from datetime import datetime
from arcp.extensions import db

class EmailConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    days_before = db.Column(db.Integer, default=1)
    notification_time = db.Column(db.Time, default=datetime.strptime('09:00', '%H:%M').time())
    enabled = db.Column(db.Boolean, default=True)

class EmailRecipient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)

class SentNotification(db.Model):
    """记录已发送的通知，防止重复发送"""
    id = db.Column(db.Integer, primary_key=True)
    paper_id = db.Column(db.Integer, nullable=False)
    sent_date = db.Column(db.Date, nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
