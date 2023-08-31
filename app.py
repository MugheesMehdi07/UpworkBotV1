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
        qs = Jobs.query.with_entities(Jobs.id, Jobs.job_title, Jobs.posted_on).order_by(Jobs.posted_on.desc()).limit(50).all()
        jobs_list = []
        PST = pytz.timezone('Asia/Karachi')
        if qs:
            for job in qs:
                posted = job.posted_on.astimezone(PST).replace(tzinfo=None) 
                job_dict = {
                    'id': job.id,
                    'job_title': job.job_title,
                    'posted_on': str(posted)
                }
                jobs_list.append(job_dict)
            print('jobs list', jobs_list)
            return jsonify({'success': True, 'message': '', 'data': jobs_list})
        return jsonify({'success': False, 'message': 'Not found', 'data': jobs_list})
    except Exception as e:
        return jsonify({'success': False, 'message': 'Something went wrong', 'data': None})


@app.route("/jobs/", methods=['GET'])
def get_job():
    # try:
    from models import Jobs
    id = request.args.get('id', None)
    qs = Jobs.query.filter_by(id=id).first()
    if qs:
        description = qs.job_description
        if 'hourly range' in description.lower():
            index = description.lower().index('hourly')
            description = description[:index]
        if 'budget' in description.lower():
            index = description.lower().index('budget')
            description = description[:index]
        if 'category' in description.lower():
            index = description.lower().index('category')
        last_word = description.split()[-1]
        if '.' not in last_word and '!' not in last_word:
            description = description + '.'
        job_dict = {
            'job_title': qs.job_title,
            'job_link': qs.job_link,
            'job_description': description,
        }
        # print('qs', job_dict)
        return jsonify({'success': True, 'message': '', 'data': job_dict})
    return jsonify({'success': False, 'message': 'Not found', 'data': None})
    # except Exception as e:
    #     return jsonify({'success': False, 'message': 'Something went wrong', 'data': None})


@app.route("/jobs/proposal", methods=['POST'])
def get_proposal():
    try:
        print('in proposal api')
        job_dict = request.json
        print('job_dict', job_dict)
        if job_dict:
            from JobParser import write_response
            bard_response = write_response(job_dict)

            return jsonify({'success': True, 'message': '', 'data': bard_response})
    except Exception as e:
        return jsonify({'success': False, 'message': 'Something went wrong', 'data': None})


if __name__ == "__main__":
    app.run(debug=True)