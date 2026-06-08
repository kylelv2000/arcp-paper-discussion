from datetime import datetime
from arcp.extensions import db

class Paper(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    presenter = db.Column(db.String(100), nullable=False)
    # 论文名称可留空，由讲解人后续补充
    title = db.Column(db.String(200), nullable=True)
    pdf_filename = db.Column(db.String(255), nullable=True)
    pdf_original_filename = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def has_pdf(self):
        return bool(self.pdf_filename)
