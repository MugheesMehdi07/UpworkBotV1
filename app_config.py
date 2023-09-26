from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_admin import Admin
from flask_uploads import UploadSet, configure_uploads, IMAGES


app = Flask(__name__)
cors = CORS(app)

# for dev
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///upworkbot.db'

# for prod
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:123456@localhost:5432/upworkbot'
db = SQLAlchemy(app)
migrate = Migrate(app, db)
admin = Admin()
admin.init_app(app)
app.config["SECRET_KEY"] = "mysecret"
images = UploadSet("images", IMAGES)
app.config["UPLOADED_IMAGES_DEST"] = 'static/uploads'
configure_uploads(app, images)
