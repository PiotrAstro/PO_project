from flask import Blueprint, redirect, render_template, request, url_for
from flask_login import login_required, current_user, login_user
from functools import wraps
import app.login_forms as login_forms
import app.restaurant.restaurant as restaurant
from app.models import Restaurant, db
from sqlalchemy import text

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


# @restaurant_bp.route('/browse_requests')
# @restaurant_required
# def browse_requests():
#     requests = db.session.execute(
#         text('''
#             SELECT * 
#             FROM "Request" 
#             WHERE id NOT IN (
#                 SELECT request_id FROM "Offer"
#             )
#             ''')
#         ).fetchall()

#     return render_template('restaurant/browse_requests.html', requests=requests), 200
@restaurant_bp.route('/browse_requests')
@restaurant_required
def browse_requests():
    requests = db.session.execute(
        text('''
            SELECT r.id AS request_id,
                   c.name || ' ' || c.surname AS client_name,
                   string_agg(ri.name, ', ') AS ordered_items,
                   r."withDelivery",
                   r.address,
                   r."electronicPayment"
            FROM "Request" r
            JOIN "Client" c ON r.client_id = c.id
            JOIN "RecipeRequest" rr ON r.id = rr.request_id
            JOIN "Recipe" ri ON rr.recipe_id = ri.id
            WHERE r.id NOT IN (
                SELECT request_id FROM "Offer"
            )
            GROUP BY r.id, c.name, c.surname, r."withDelivery", r.address, r."electronicPayment"
        ''')
    ).fetchall()

    return render_template('restaurant/browse_requests.html', requests=requests)



@restaurant_bp.route('/make_offer/<int:request_id>', methods=['GET', 'POST'])
@restaurant_required
def make_offer(request_id):
    if request.method == 'POST':
        price = request.form['price']
        notes = request.form['notes']
        waiting_time = request.form['waitingTime']
        restaurant_id = current_user.id

        if float(price) <= 0:
            return "Price must be positive", 400

        db.session.execute(
            text('''
                INSERT INTO "Offer" (request_id, restaurant_id, price, notes, "waitingTime")
                VALUES (:request_id, :restaurant_id, :price, :notes, :waiting_time)
            '''),
            {
                'request_id': request_id,
                'restaurant_id': restaurant_id,
                'price': price,
                'notes': notes,
                'waiting_time': waiting_time
            }
        )
        db.session.commit()

        return redirect(url_for('restaurant.browse_requests'))

    return render_template('restaurant/make_offer.html', request_id=request_id)
