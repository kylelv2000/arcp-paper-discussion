from arcp.extensions import db

# 0=周一 ... 6=周日，与 Python date.weekday() 对齐
WEEKDAY_LABELS = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']


class MeetingConfig(db.Model):
    """讨论班每周固定开会日，安排新轮时据此推算日期。"""
    id = db.Column(db.Integer, primary_key=True)
    weekday = db.Column(db.Integer, nullable=False, default=2)  # 默认周三

    @property
    def weekday_label(self):
        if 0 <= self.weekday <= 6:
            return WEEKDAY_LABELS[self.weekday]
        return str(self.weekday)
