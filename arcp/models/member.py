from arcp.extensions import db

# 年级取值与中文标签
GRADE_LABELS = {'phd': '博士', 'master': '硕士'}
# 排序优先级：数值越小越靠前（年级越高越靠前）
GRADE_PRIORITY = {'phd': 0, 'master': 1}


class Member(db.Model):
    """讨论班成员：将讲解人与邮箱绑定为同一身份。"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    grade = db.Column(db.String(20), nullable=False, default='master')  # 'phd' | 'master'
    email = db.Column(db.String(120))
    # 自定义排序值，安排新轮与后台展示均按此升序
    order_index = db.Column(db.Integer, nullable=False, default=0)

    @property
    def grade_label(self):
        return GRADE_LABELS.get(self.grade, self.grade)

    @property
    def grade_priority(self):
        return GRADE_PRIORITY.get(self.grade, 99)
