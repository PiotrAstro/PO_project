from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config
from app.models import Client, Deliverer, Restaurant, db

# Initialize extensions
login_manager = LoginManager()


# login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    user_type = user_id[0]
    id = int(user_id[1:])

    if user_type == 'C':
        return Client.query.get(id)
    elif user_type == 'D':
        return Deliverer.query.get(id)
    elif user_type == 'R':
        return Restaurant.query.get(id)


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.config['SECRET_KEY'] = config_class.SECRET_KEY

    # Initialize extensions
    db.init_app(app)
    with app.app_context():
        db.create_all()

    # # Register blueprints
    from app.restaurant.routes import restaurant_bp
    from app.client.routes import client_bp
    from app.deliverer.routes import deliverer_bp
    from app.main.routes import main_bp

    app.register_blueprint(client_bp)
    app.register_blueprint(deliverer_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(restaurant_bp)

    login_manager.init_app(app)

    return app
