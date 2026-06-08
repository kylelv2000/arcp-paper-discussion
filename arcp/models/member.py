from arcp.extensions import db

# 年级取值范围：1~8 共 8 个档位（数字越大年级越高）
GRADE_MIN = 1
GRADE_MAX = 8
GRADE_CHOICES = list(range(GRADE_MIN, GRADE_MAX + 1))


class Member(db.Model):
    """讨论班成员：将讲解人与邮箱绑定为同一身份。"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    grade = db.Column(db.Integer, nullable=False, default=GRADE_MIN)  # 1~8
    email = db.Column(db.String(120))
    # 自定义排序值，安排新轮与后台展示均按此升序
    order_index = db.Column(db.Integer, nullable=False, default=0)
    # 归档标记：已毕业成员归档后不参与下拉、排轮与通知，但保留历史记录
    archived = db.Column(db.Boolean, nullable=False, default=False)

    @property
    def grade_label(self):
        return f'{self.grade}年级'

    @property
    def grade_priority(self):
        # 数字越大年级越高、越靠前；取负值使升序排序时高年级在前
        try:
            return -int(self.grade)
        except (TypeError, ValueError):
            return 0
