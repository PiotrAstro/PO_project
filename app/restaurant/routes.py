import datetime
from flask import Blueprint, redirect, render_template, request, url_for
from flask_login import login_required, current_user, login_user
from functools import wraps
from wtforms.validators import DataRequired

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
import app.login_forms as login_forms
from app.restaurant.form import CreateDeliveryForm, EditOrderForm
import app.restaurant.restaurant as restaurant
from app.models import OrderStatus, Restaurant, db
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

@restaurant_bp.route('/browse-orders')
@restaurant_required
def browse_orders():
    not_finished_orders = restaurant.get_orders(current_user.id)
    return render_template(
        'restaurant/browse_orders.html', 
        orders_by_status=not_finished_orders,
        OrderStatus=OrderStatus  # Pass the enum to the template
    ), 200

@restaurant_bp.route('/edit-order', methods=['GET'])
@restaurant_required
def edit_order():
    form = EditOrderForm()
    order_id = request.args.get('order_id')
    if not order_id:
        return redirect(url_for('restaurant.browse_orders'))
    order = restaurant.get_order(int(order_id), current_user.id)
    if not order:
        return redirect(url_for('restaurant.browse_orders'))
    form.order_id.data = order.id
    form.status.data = order.orderStatus.value
    form.notes.data = order.notes

    status_get = request.args.get('status')
    if status_get:
        form.status.data = status_get
    
    notes_get = request.args.get('notes')
    if notes_get:
        form.notes.data = notes_get
    return render_template('restaurant/edit_order.html', form=form, order=order), 200

@restaurant_bp.route('/edit-order', methods=['POST'])
@restaurant_required
def edit_order_post():
    form = EditOrderForm()
    
    if form.validate_on_submit():
        assert form.order_id.data is not None
        order_id = int(form.order_id.data)
        order = restaurant.get_order(order_id, current_user.id)
        if not order:
            return redirect(url_for('restaurant.browse_orders'))
        new_status = form.status.data
        
        # If status is changed to ready and delivery is required
        if new_status == "Ready":
            if order.offer.request.withDelivery:
                # Store the notes in session for after deliverer selection
                form_select_deliverer = CreateDeliveryForm()
                form_select_deliverer.order_id.data = str(order_id)
                form_select_deliverer.status.data = new_status
                form_select_deliverer.notes.data = form.notes.data
                form_select_deliverer.date.data = datetime.date.today()
                form_select_deliverer.time.data = datetime.datetime.now()
                form_select_deliverer.deliverer_id.choices = [(d.id, f"{d.name} {d.surname}") for d in restaurant.get_available_deliverers(current_user.id)]

                back_url = url_for('restaurant.edit_order', order_id=order_id, status=new_status, notes=form.notes.data)
                return render_template('restaurant/select_deliverer.html', form=form_select_deliverer, order=order, goback=back_url)
            else:
                new_status = "Delivered"
        
        # If no delivery required or different status
        restaurant.update_order(order_id, current_user.id, new_status, form.notes.data)
    return redirect(url_for('restaurant.browse_orders'))

@restaurant_bp.route('/cancel-order', methods=['POST'])
@restaurant_required
def cancel_order():
    order_id = request.form.get('order_id')
    if not order_id:
        return redirect(url_for('restaurant.browse_orders'))
    
    restaurant.cancel_order(int(order_id), current_user.id)
    return redirect(url_for('restaurant.browse_orders'))

@restaurant_bp.route('/select-deliverer', methods=['POST'])
@restaurant_required
def select_deliverer():
    print("Hi")
    form = CreateDeliveryForm()
    form.deliverer_id.choices = [(d.id, f"{d.name} {d.surname}") for d in restaurant.get_available_deliverers(current_user.id)]
    if form.validate_on_submit():
        print("passed!")
        assert form.order_id.data is not None
        order_id = int(form.order_id.data)
        deliverer_id = int(form.deliverer_id.data)
        assert form.date.data is not None
        assert form.time.data is not None
        delivery_due = datetime.datetime.combine(form.date.data, form.time.data.time())
        notes = form.notes.data
        restaurant.update_order_with_delivery(order_id, deliverer_id, delivery_due, notes)
    print("here")
    return redirect(url_for('restaurant.browse_orders'))



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
                SELECT o.request_id
                FROM "Offer" o
                LEFT JOIN "Orders" ord ON o.id = ord.offer_id
                WHERE ord.id IS NOT NULL
            )
            AND r.id NOT IN (
                SELECT o.request_id
                FROM "Offer" o
                WHERE o.restaurant_id = :restaurant_id
            )
            GROUP BY r.id, c.name, c.surname, r."withDelivery", r.address, r."electronicPayment"
        '''),
        {'restaurant_id': current_user.id}
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
