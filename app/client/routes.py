from flask import Blueprint, redirect, render_template, request, url_for
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




@client_bp.route('/')
@client_required
def index():
    return redirect(url_for('client.panel'))


@client_bp.route('/panel')
@client_required
def panel():
    return render_template('client/panel.html'), 200


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
            return redirect(url_for('client.panel'))
    return redirect(url_for('client.login'))
