from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config
from app.models import db

# Initialize extensions
# login_manager = LoginManager()
# login_manager.login_view = 'auth.login'

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    with app.app_context():
        db.create_all()
    # login_manager.init_app(app)

    # # Register blueprints
    # from app.auth import bp as auth_bp
    # app.register_blueprint(auth_bp)

    # from app.main import bp as main_bp
    # app.register_blueprint(main_bp)

    return app