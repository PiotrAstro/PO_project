from flask import Blueprint, redirect, render_template, request, url_for
from flask_login import login_required, current_user, login_user
from functools import wraps
import app.login_forms as login_forms
import app.restaurant.restaurant as restaurant
from app.models import Restaurant

restaurant_bp = Blueprint('restaurant', __name__, url_prefix='/restaurant')


def restaurant_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not isinstance(current_user, Restaurant):
            return redirect("/restaurant/login")
        return f(*args, **kwargs)
    return decorated_function


@restaurant_bp.route('/')
@restaurant_required
def index():
    return redirect(url_for('restaurant.panel'))


@restaurant_bp.route('/panel')
@restaurant_required
def panel():
    return render_template('restaurant/panel.html'), 200


@restaurant_bp.route('/login')
def login():
    return render_template('login.html', form=login_forms.LoginForm())


@restaurant_bp.route('/login', methods=['POST'])
def login_post():
    form = login_forms.LoginForm(request.form)
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        user = restaurant.get_user(username, password)
        if user:
            login_user(user)
            return redirect(url_for('restaurant.panel'))
    return redirect(url_for('restaurant.login'))
