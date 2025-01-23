from flask import Blueprint, redirect, render_template, request
from flask_login import login_required, current_user, login_user
from functools import wraps
import app.login_forms as login_forms
import app.deliverer.deliverer as deliverer
from app.models import Deliverer

deliverer_bp = Blueprint('deliverer', __name__, url_prefix='/deliverer')


def deliverer_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not isinstance(current_user, Deliverer):
            return redirect("/deliverer/login")
        return f(*args, **kwargs)
    return decorated_function

# protected routes

@deliverer_bp.route('/')
@deliverer_required
def index():
    # print client login
    return f"Hello, World deliverer!<br>{current_user.login}", 200

# logging

@deliverer_bp.route('/login')
def login():
    return render_template('login.html', form=login_forms.LoginForm())

@deliverer_bp.route('/login', methods=['POST'])
def login_post():
    form = login_forms.LoginForm(request.form)
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        user = deliverer.get_user(username, password)
        if user:
            login_user(user)
            return redirect("/deliverer")
    return redirect("/deliverer/login")