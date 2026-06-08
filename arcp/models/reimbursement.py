from datetime import datetime
from arcp.extensions import db


class ReimbursementAssignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, nullable=False)
    quarter = db.Column(db.Integer, nullable=False)
    student = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('year', 'quarter', name='uq_reimbursement_year_quarter'),
    )

    @property
    def quarter_label(self):
        return f'Q{self.quarter}'

    @property
    def date_range_label(self):
        ranges = {
            1: '1月 - 3月',
            2: '4月 - 6月',
            3: '7月 - 9月',
            4: '10月 - 12月',
        }
        return ranges.get(self.quarter, '')


class ReimbursementItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, nullable=False)
    quarter = db.Column(db.Integer, nullable=False)
    member_name = db.Column(db.String(100), nullable=False)
    content = db.Column(db.String(500), nullable=False)
    zip_filename = db.Column(db.String(255), nullable=False)
    zip_original_filename = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('year', 'quarter', 'member_name', name='uq_reimbursement_item_member_quarter'),
    )

    @property
    def quarter_label(self):
        return f'Q{self.quarter}'
