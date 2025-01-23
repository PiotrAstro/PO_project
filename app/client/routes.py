from flask import Blueprint, redirect, render_template, request
from flask_login import login_required, current_user, login_user
from functools import wraps
import app.login_forms as login_forms
import app.client.client as client
from app.models import Client

client_bp = Blueprint('client', __name__, url_prefix='/client')

def client_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not isinstance(current_user, Client):
            return redirect("/client/login")
        return f(*args, **kwargs)
    return decorated_function

# protected routes

@client_bp.route('/')
@client_required
def index():
    # print client login
    return f"Hello, World!<br>{current_user.login}", 200

# logging

@client_bp.route('/login')
def login():
    return render_template('login.html', form=login_forms.LoginForm())

@client_bp.route('/login', methods=['POST'])
def login_post():
    form = login_forms.LoginForm(request.form)
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        user = client.get_user(username, password)
        if user:
            login_user(user)
            return redirect("/client")
    return redirect("/client/login")