from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
# from models import *


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///upworkbot.db'
db = SQLAlchemy(app)
migrate = Migrate(app, db)


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


@app.route("/jobs", methods=['GET'])
def get_jobs():
    try:
        qs = Jobs.query.all()
        jobs_list = []
        if qs:
            for job in qs:
                job_dict = {
                    'id': job.id,
                    'job_title': job.job_title,
                    'job_link': job.job_link,
                    'job_description': job.job_description,
                }
                jobs_list.append(job_dict)
            return jsonify({'success': True, 'message': '', 'data': jobs_list})
        return jsonify({'success': False, 'message': 'Not found', 'data': jobs_list})
    except Exception as e:
        return jsonify({'success': False, 'message': 'Something went wrong', 'data': None})


@app.route("/job/proposal/", methods=['GET'])
def get_proposal():
    try:
        id = request.args.get('id')
        qs = Proposals.query.filter_by(job_id=id).first()
        if qs:
            job_dict = {
                'job_id': qs.job_id,
                'job_proposal': qs.proposal,
            }
            return jsonify({'success': True, 'message': '', 'data': job_dict})
        return jsonify({'success': False, 'message': 'Not found', 'data': None})
    except Exception as e:
        return jsonify({'success': False, 'message': 'Something went wrong', 'data': None})


if __name__ == "__main__":
    app.run(debug=True)