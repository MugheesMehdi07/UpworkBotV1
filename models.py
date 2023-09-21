from app import db
from datetime import datetime
# from signals import notification


class Jobs(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_title = db.Column(db.String, nullable=True)
    job_link = db.Column(db.String, nullable=True)
    job_description = db.Column(db.String, nullable=True)
    posted_on = db.Column(db.DateTime, nullable=True)
    bidding_done = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"{self.job_title}"


class JobStatus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    total_jobs = db.Column(db.Integer, nullable=True)
    added_on = db.Column(db.DateTime, default=datetime.now)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

    # def __repr__(self):
    #     return f"JobStatus(id={self.id}, total_jobs={self.total_jobs}, posted_on={self.posted_on})"
