from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from configs import Config
from flask_bcrypt import Bcrypt
from flask_mail import Mail
import os


db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
bcrypt = Bcrypt()
mail = Mail()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)


    mail.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    bcrypt.init_app(app)

    UPLOADS = "./eduplan/static/transcripts"

    #app.config.STATIC_DIRECTORY = "eduplan/static"


    print("Current working directory:", os.getcwd())
    print("Static folder exists:", os.path.isdir("eduplan/static"))
    
    app.config['UPLOAD_FOLDER'] = UPLOADS

    from eduplan.models import User
    from eduplan.forms import RegisterForm, LoginForm


    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id)) 

    from eduplan.routes import main_blueprint
    app.register_blueprint(main_blueprint)

#admin password= SecurePass123
#user passwords are username

    return app
