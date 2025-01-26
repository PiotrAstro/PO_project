from flask import Blueprint, redirect, render_template, request, url_for, flash
from flask_login import login_required, current_user, login_user
from functools import wraps
import app.login_forms as login_forms
import app.client.client as client_module
from app.models import Client
from app import db
from sqlalchemy import text
from app.client.client import (
    get_recipes_for_client,
    create_recipe,
    get_recipe_types,
    get_ingredients,
    update_recipe,
    remove_recipe,
    add_recipe_type,
    add_ingredient,
    get_recipe_by_id,
    get_recipe_ingredients,
    get_recipe_for_view
)

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
        user = client_module.get_user(username, password)
        if user:
            login_user(user)
            return redirect(url_for('client.panel'))
        else:
            flash('Invalid username or password.')
    return render_template('login.html', form=form)



@client_bp.route('/manage_reviews')
@client_required
def manage_reviews():
    reviews = client_module.get_reviews(current_user.id)
    return render_template('client/manage_reviews.html', reviews=reviews), 200


@client_bp.route('/add_review', methods=['GET', 'POST'])
@client_required
def add_review():
    if request.method == 'POST':
        try:
            recipe_id = int(request.form['recipe_id'])
            rating = int(request.form['rating'])
            description = request.form['description']

            print(f"Rating: {rating}")
            print(f"Description: {description}")

            if rating < 1 or rating > 5:
                flash('Rating must be between 1 and 5.')
                return redirect(url_for('client.add_review'))

            success = client_module.add_review(current_user.id, recipe_id, rating, description)
            if success:
                flash('Review added successfully.')
            else:
                flash('Review already exists for this recipe.')
            return redirect(url_for('client.manage_reviews'))
        except Exception as e:
            print(f"Error adding review: {e}")
            flash('An error occurred while adding the review.')
            return redirect(url_for('client.add_review'))

    recipes = client_module.get_all_recipes()
    return render_template('client/add_review.html', recipes=recipes), 200


@client_bp.route('/edit_review/<int:review_id>', methods=['GET', 'POST'])
@client_required
def edit_review(review_id):
    if request.method == 'POST':
        try:
            rating = int(request.form['rating'])
            description = request.form['description']

            if rating < 1 or rating > 5:
                flash('Rating must be between 1 and 5.')
                return redirect(url_for('client.edit_review', review_id=review_id))

            success = client_module.edit_review(current_user.id, review_id, rating, description)
            if success:
                flash('Review updated successfully.')
            else:
                flash('Review not found or unauthorized.')
            return redirect(url_for('client.manage_reviews'))
        except Exception as e:
            print(f"Error editing review: {e}")
            flash('An error occurred while editing the review.')
            return redirect(url_for('client.edit_review', review_id=review_id))

    reviews = client_module.get_reviews(current_user.id)
    review = next((r for r in reviews if r.recipe_id == review_id), None)
    if not review:
        flash('Review not found or unauthorized.')
        return redirect(url_for('client.manage_reviews'))

    return render_template('client/edit_review.html', review=review), 200


@client_bp.route('/delete_review/<int:review_id>', methods=['POST'])
@client_required
def delete_review(review_id):
    try:
        success = client_module.delete_review(current_user.id, review_id)
        if success:
            flash('Review deleted successfully.')
        else:
            flash('Review not found or unauthorized.')
    except Exception as e:
        print(f"Error deleting review: {e}")
        flash('An error occurred while deleting the review.')
    return redirect(url_for('client.manage_reviews'))


@client_bp.route('/request', methods=['GET', 'POST'])
@client_required
def create_request():
    if request.method == 'POST':
        try:
            recipe_ids = request.form.getlist('recipe_ids')
            with_delivery = request.form.get('with_delivery') == 'true'
            electronic_payment = request.form.get('electronic_payment') == 'true'
            address = request.form.get('address')

            print(f"Selected recipes: {recipe_ids}")
            print(f"With Delivery: {with_delivery}")
            print(f"Electronic Payment: {electronic_payment}")
            print(f"Address: {address}")

            if not recipe_ids:
                flash('You must select at least one recipe.')
                return redirect(url_for('client.create_request'))

            if with_delivery and not address:
                flash('Address is required for delivery.')
                return redirect(url_for('client.create_request'))

            request_id = client_module.create_request(
                client_id=current_user.id,
                withDelivery=with_delivery,
                address=address,
                electronic_payment=electronic_payment
            )

            client_module.associate_recipes_to_request(
                request_id=request_id,
                recipe_ids=recipe_ids
            )

            flash('Request created successfully.')
            return redirect(url_for('client.panel'))
        except Exception as e:
            db.session.rollback()
            print(f"Error creating request: {e}")
            flash('An error occurred while creating the request.')
            return redirect(url_for('client.create_request'))

    recipes = client_module.get_all_recipes()
    return render_template('client/create_request.html', recipes=recipes), 200


@client_bp.route('/browse_offers', methods=['GET'])
@client_required
def browse_offers():
    try:
        offers = client_module.get_available_offers(current_user.id)
        return render_template('client/browse_offers.html', offers=offers), 200
    except Exception as e:
        print(f"Error fetching offers: {e}")
        flash('An error occurred while fetching offers.')
        return redirect(url_for('client.panel'))



@client_bp.route('/accept_offer/<int:offer_id>', methods=['POST'])
@client_required
def accept_offer_route(offer_id):
    try:
        success = client_module.accept_offer(offer_id, current_user.id)
        if success:
            flash('Offer accepted successfully.')
        else:
            flash('Offer not found or already accepted.')
        return redirect(url_for('client.panel'))
    except Exception as e:
        db.session.rollback()
        print(f"Error accepting offer: {e}")
        flash('An error occurred while accepting the offer.')
        return redirect(url_for('client.browse_offers'))


@client_bp.route('/browse_orders', methods=['GET'])
@client_required
def browse_orders():
    try:
        orders = client_module.get_orders(current_user.id)
        return render_template('client/browse_orders.html', orders=orders), 200
    except Exception as e:
        print(f"Error fetching orders: {e}")
        flash('An error occurred while fetching orders.')
        return redirect(url_for('client.panel'))



@client_bp.route('/manage_recipes', endpoint='manage_recipes')
@client_required
def manage_recipes_view():
    recipes = get_recipes_for_client(current_user.id)
    return render_template('client/manage_recipes.html', recipes=recipes)


@client_bp.route('/add_recipe', methods=['GET', 'POST'], endpoint='add_recipe')
@client_required
def add_recipe_view():
    if request.method == 'POST':
        try:
            name = request.form['name']
            description = request.form['description']
            recipe_steps = request.form['recipeSteps']
            image_name = request.form.get('image_name', 'default.jpg')
            recipe_type_id = int(request.form['recipe_type_id'])
            ingredient_ids = request.form.getlist('ingredient_ids[]')
            quantities = request.form.getlist('quantities[]')

            if not ingredient_ids or not quantities or len(ingredient_ids) != len(quantities):
                raise ValueError("Ingredients and quantities cannot be empty or mismatched.")

            create_recipe(
                client_id=current_user.id,
                recipe_type_id=recipe_type_id,
                name=name,
                description=description,
                recipe_steps=recipe_steps,
                image_name=image_name,
                ingredient_ids=[int(i) for i in ingredient_ids],
                quantities=quantities
            )

            flash("Recipe added successfully.", "success")
            return redirect(url_for('client.manage_recipes'))

        except Exception as e:
            print(f"Error: {e}")
            return "An error occurred while adding the recipe. Please try again.", 400

    recipe_types = get_recipe_types()
    ingredients = get_ingredients()
    return render_template('client/add_recipe.html', recipe_types=recipe_types, ingredients=ingredients)


@client_bp.route('/edit_recipe/<int:recipe_id>', methods=['GET', 'POST'], endpoint='edit_recipe')
@client_required
def edit_recipe_view(recipe_id):
    if request.method == 'POST':
        try:
            name = request.form['name']
            description = request.form['description']
            recipe_steps = request.form['recipeSteps']
            recipe_type_id = int(request.form['recipe_type_id'])
            ingredient_ids = request.form.getlist('ingredient_ids[]')
            quantities = request.form.getlist('quantities[]')

            if not ingredient_ids or not quantities or len(ingredient_ids) != len(quantities):
                raise ValueError("Ingredients and quantities cannot be empty or mismatched.")

            update_recipe(
                recipe_id=recipe_id,
                client_id=current_user.id,
                name=name,
                description=description,
                recipe_steps=recipe_steps,
                recipe_type_id=recipe_type_id,
                ingredient_ids=[int(i) for i in ingredient_ids],
                quantities=quantities
            )

            flash("Recipe updated successfully.", "success")
            return redirect(url_for('client.manage_recipes'))

        except Exception as e:
            print(f"Error: {e}")
            return "An error occurred while updating the recipe. Please try again.", 400

    recipe = get_recipe_by_id(recipe_id, current_user.id)
    if not recipe:
        return "Recipe not found or unauthorized access.", 404

    recipe_ingredients = get_recipe_ingredients(recipe_id)
    recipe_types = get_recipe_types()
    ingredients = get_ingredients()
    return render_template(
        'client/edit_recipe.html',
        recipe=recipe,
        recipe_ingredients=recipe_ingredients,
        recipe_types=recipe_types,
        ingredients=ingredients
    )


@client_bp.route('/remove_recipe/<int:recipe_id>', methods=['POST'], endpoint='remove_recipe')
@client_required
def remove_recipe_view(recipe_id):
    result = remove_recipe(recipe_id, current_user.id)
    if not result:
        flash("Cannot delete recipe linked to existing requests or not found.", "error")
        return redirect(url_for('client.manage_recipes'))

    flash('Recipe deleted successfully.', 'success')
    return redirect(url_for('client.manage_recipes'))


@client_bp.route('/add_recipe_type', methods=['GET', 'POST'], endpoint='add_recipe_type')
@client_required
def add_recipe_type_view():
    if request.method == 'POST':
        recipe_type = request.form['recipe_type']
        add_recipe_type(recipe_type)
        # Zwróć uwagę, że tu kierujemy do endpointu 'client.add_recipe'
        return redirect(url_for('client.add_recipe'))

    return render_template('client/add_recipe_type.html')


@client_bp.route('/add_ingredient', methods=['GET', 'POST'], endpoint='add_ingredient')
@client_required
def add_ingredient_view():
    if request.method == 'POST':
        ingredient_name = request.form['ingredient_name']
        add_ingredient(ingredient_name)
        # Analogicznie, przekierowanie do 'client.add_recipe'
        return redirect(url_for('client.add_recipe'))

    return render_template('client/add_ingredient.html')


@client_bp.route('/view_recipe/<int:recipe_id>', methods=['GET'], endpoint='view_recipe')
@client_required
def view_recipe_view(recipe_id):
    recipe, recipe_ingredients = get_recipe_for_view(recipe_id, current_user.id)
    if not recipe:
        return "Recipe not found or unauthorized access.", 404

    return render_template(
        'client/view_recipe.html',
        recipe=recipe,
        recipe_ingredients=recipe_ingredients
    )