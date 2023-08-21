from app import db
from datetime import datetime


class Jobs(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_title = db.Column(db.String, nullable=True)
    job_link = db.Column(db.String, nullable=True)
    job_description = db.Column(db.String, nullable=True)
    proposal = db.relationship('Proposals', backref='jobs', uselist=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"{self.job_title}"


class Proposals(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    proposal = db.Column(db.String, nullable=True)
    job_id = db.Column(db.Integer, db.ForeignKey(Jobs.id))
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

