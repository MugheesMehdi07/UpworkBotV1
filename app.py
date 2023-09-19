import asyncio

from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime, timedelta
from flask_cors import CORS
import sqlalchemy as sa
import pytz


app = Flask(__name__)
cors = CORS(app)
# for dev
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///upworkbot.db'
# for prod
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:123456@localhost:5432/upworkbot'
db = SQLAlchemy(app)
migrate = Migrate(app, db)


@app.route("/", methods=['GET'])
def get_jobs():
    try:
        from models import Jobs
        qs = Jobs.query.with_entities(Jobs.id, Jobs.job_link, Jobs.job_title, Jobs.posted_on).order_by(Jobs.id.desc()).limit(50).all()
        jobs_list = []
        PST = pytz.timezone('Asia/Karachi')
        if qs:
            for job in qs:
                posted = job.posted_on.astimezone(PST).replace(tzinfo=None)
                job_dict = {
                    'id': job.id,
                    'job_title': job.job_title,
                    'job_link': job.job_link,
                    'posted_on': str(posted)
                }
                jobs_list.append(job_dict)
            response = jsonify({'success': True, 'message': '', 'data': jobs_list})
            response.status_code = 200
            return response
        response = jsonify({'success': False, 'message': 'Jobs are not available', 'data': []})
        response.status_code = 400
        return response
    except Exception as e:
        response = jsonify({'success': False, 'message': 'Something went wrong', 'data': None})
        response.status_code = 400
        return response


@app.route("/jobs/", methods=['GET'])
def get_job():
    try:
        from models import Jobs
        id = request.args.get('id', None)
        qs = Jobs.query.filter_by(id=int(id)).first()
        if qs:
            description = description_format(qs.job_description)
            job_dict = {
                'job_id': qs.id,
                'job_title': qs.job_title,
                'job_link': qs.job_link,
                'job_description': description,
            }
            response = jsonify({'success': True, 'message': '', 'data': job_dict})
            response.status_code = 200
            return response
        response = jsonify({'success': False, 'message': 'Job is not available', 'data': None})
        response.status_code = 400
        return response
    except Exception as e:
        response = jsonify({'success': False, 'message': 'Something went wrong', 'data': None})
        response.status_code = 400
        return response


@app.route("/jobs/proposal", methods=['POST'])
def get_proposal():
    try:
        job_dict = request.json
        from models import Jobs
        qs = Jobs.query.filter_by(id=int(job_dict['job_id'])).first()
        if qs:
            description = description_format(qs.job_description)
            job_dict = {
                'Job Title': qs.job_title,
                'Job Link': qs.job_link,
                'Job Description': description,
            }
            from JobParser import write_response
            bard_response = write_response(job_dict)
            if 'An error occurred while' not in bard_response:
                response = jsonify({'success': True, 'message': '', 'data': bard_response})
                response.status_code = 200
                return response
            response = jsonify({'success': False, 'message': '', 'data': bard_response})
            response.status_code = 400
            return response
    except Exception as e:
        response = jsonify({'success': False, 'message': 'Something went wrong', 'data': None})
        response.status_code = 400
        return response


@app.route("/flag/", methods=['GET'])
def flag():
    try:
        flag = request.args.get('flag', None)
        from JobParser import flag_set
        flag_set(flag)
        response = jsonify({'success': True, 'message': '', 'data':''})
        response.status_code = 200
        return response
    except Exception as e:
        response = jsonify({'success': False, 'message': 'Something went wrong', 'data': str(e)})
        response.status_code = 400
        return response


def description_format(description):
    if description:
        if 'hourly range' in description.lower():
            str_index = description.lower().index('hourly')
            description = description[:str_index]
        if 'budget' in description.lower():
            str_index = description.lower().index('budget')
            description = description[:str_index]
        if 'category' in description.lower():
            str_index = description.lower().index('category')
            description = description[:str_index]
        last_word = description.split()[-1]
        if '.' not in last_word and '!' not in last_word:
            description = description + '.'
        return description


if __name__ == "__main__":
    app.run(debug=True)