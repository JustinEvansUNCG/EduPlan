from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from configs import Config

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    from eduplan.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id)) 

    from eduplan.routes import main_blueprint
    app.register_blueprint(main_blueprint)

    return app
