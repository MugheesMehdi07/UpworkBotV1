import asyncio
from flask_admin import Admin
from flask import Flask, jsonify, request, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime, timedelta
from flask_cors import CORS
import sqlalchemy as sa
import os
import pytz
from flask_uploads import UploadSet, configure_uploads, IMAGES
from flask_admin.contrib.sqla import ModelView
from flask import url_for
from markupsafe import Markup


app = Flask(__name__)
cors = CORS(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
admin = Admin()
admin.init_app(app)
# for dev
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///upworkbot.db'

# for prod
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:123456@localhost:5432/upworkbot'
app.config["SECRET_KEY"] = "mysecret"
images = UploadSet("images", IMAGES)
app.config["UPLOADED_IMAGES_DEST"] = 'static/uploads'
configure_uploads(app, images)


class CustomJobView(ModelView):
    column_list = ('id', 'job_title', 'posted_on', 'bidding_done',  'bid_SS', 'SS_upload_time', 'bid_time_difference')
    column_default_sort = ('id', True)

    def _format_image(self, context, model, bid_SS):
        if model.bid_SS:
            image_name = model.bid_SS
            image_url = url_for('static', filename='uploads/' + model.bid_SS)
            return Markup(
                f'<a href="{image_url}" target="_blank"><img src="{image_url}" style="max-height: 100px;"></a>')
        return ''

def job_admin_panel(db):
    from models import Jobs
    custom_job_view = CustomJobView(Jobs, db.session)

    custom_job_view.column_formatters = {
        'bid_SS': lambda v, c, m, p: custom_job_view._format_image(v, m, 'bid_SS')
    }
    return custom_job_view


custom_job_view = job_admin_panel(db)
admin.add_view(custom_job_view)


@app.route("/", methods=['GET'])
def get_jobs():
    try:
        from models import Jobs
        qs = Jobs.query.with_entities(Jobs.id, Jobs.job_link, Jobs.job_title, Jobs.posted_on, Jobs.bidding_done).order_by(Jobs.id.desc()).limit(50).all()
        jobs_list = []
        PST = pytz.timezone('Asia/Karachi')
        if qs:
            for job in qs:
                posted = job.posted_on.astimezone(PST).replace(tzinfo=None)
                job_dict = {
                    'id': job.id,
                    'job_title': job.job_title,
                    'job_link': job.job_link,
                    'posted_on': str(posted),
                    'bidding_done': job.bidding_done
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
                'proposal_by': job_dict['proposal_by']
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


@app.route("/job/bidding/", methods=['POST'])
def bidding():
    try:
        job_dict = request.json
        from models import Jobs
        with app.app_context():
            qs = Jobs.query.filter_by(id=int(job_dict['job_id'])).first()
            if qs:
                qs.bidding_done = True
                db.session.commit()
        response = jsonify({'success': True, 'message': '', 'data': ''})
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


@app.route("/job/image/", methods=['POST'])
def image():
    try:
        job_id = request.form.get('id')
        uploaded_file = request.files['file']
        from models import Jobs
        with app.app_context():
            qs = Jobs.query.filter_by(id=int(job_id)).first()
            current_time = datetime.now()
            if qs:
                image_filename = images.save(uploaded_file)
                delta = current_time - qs.posted_on
                qs.bid_SS = image_filename
                qs.SS_upload_time = current_time
                qs.bid_time_difference = int(delta.total_seconds() / 60)
                db.session.commit()

        response = jsonify({'success': True, 'message': 'File uploaded successfully', 'data': ''})
        response.status_code = 200
        return response
    except Exception as e:
        response = jsonify({'success': False, 'message': 'Something went wrong', 'data': str(e)})
        response.status_code = 400
        return response


if __name__ == "__main__":
    app.run(debug=True)