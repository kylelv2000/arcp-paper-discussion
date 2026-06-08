from arcp.extensions import db

# 年级取值范围：0~8；0 表示未入学，9 表示“其他”
GRADE_MIN = 0
GRADE_MAX = 8
GRADE_OTHER = 9
GRADE_CHOICES = list(range(GRADE_MIN, GRADE_MAX + 1)) + [GRADE_OTHER]


class Member(db.Model):
    """讨论班成员：将讲解人与邮箱绑定为同一身份。"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    grade = db.Column(db.Integer, nullable=False, default=1)  # 0~8，9=其他
    email = db.Column(db.String(120))
    last_grade_update_year = db.Column(db.Integer, nullable=True)
    # 自定义排序值，安排新轮与后台展示均按此升序
    order_index = db.Column(db.Integer, nullable=False, default=0)
    # 归档标记：已毕业成员归档后不参与下拉、排轮与通知，但保留历史记录
    archived = db.Column(db.Boolean, nullable=False, default=False)

    @property
    def grade_label(self):
        if self.is_other_grade:
            return '其他'
        try:
            grade = int(self.grade)
        except (TypeError, ValueError):
            return '未知'
        if grade == 0:
            return '0年级'
        return f'{self.grade}年级'

    @property
    def is_other_grade(self):
        try:
            return int(self.grade) == GRADE_OTHER
        except (TypeError, ValueError):
            return False

    @property
    def is_schedulable(self):
        return not self.archived and not self.is_other_grade

    @property
    def grade_class(self):
        return 'grade-other' if self.is_other_grade else f'grade-{self.grade}'

    @property
    def grade_priority(self):
        # 数字越大年级越高、越靠前；取负值使升序排序时高年级在前
        try:
            if int(self.grade) == GRADE_OTHER:
                return 999
            return -int(self.grade)
        except (TypeError, ValueError):
            return 0
