from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
import enum

db = SQLAlchemy()


# Enums
class DeliveryStatus(enum.Enum):
    Delivered = "Delivered"
    InDelivery = "InDelivery"
    Waiting = "Waiting"


class OrderStatus(enum.Enum):
    Canceled = "Canceled"
    InPreparation = "InPreparation"
    WaitingForDelivery = "WaitingForDelivery"
    Registered = "Registered"
    InDelivery = "InDelivery"
    Delivered = "Delivered"


class PaymentStatus(enum.Enum):
    Waiting = "Waiting"
    Completed = "Completed"
    Declined = "Declined"


# Association Tables
restaurant_deliverer = db.Table(
    'RestaurantDeliverer',
    db.Column('deliverer_id', db.Integer, db.ForeignKey('Deliverer.id', ondelete='CASCADE'), primary_key=True),
    db.Column('restaurant_id', db.Integer, db.ForeignKey('Restaurant.id', ondelete='CASCADE'), primary_key=True)
)

recipe_ingredients = db.Table(
    'RecipeIngredients',
    db.Column('recipe_id', db.Integer, db.ForeignKey('Recipe.id', ondelete='RESTRICT'), primary_key=True),
    db.Column('ingredient_id', db.Integer, db.ForeignKey('Ingredient.id', ondelete='RESTRICT'), primary_key=True),
    db.Column('quantity', db.String, nullable=False)
)

recipe_request = db.Table(
    'RecipeRequest',
    db.Column('recipe_id', db.Integer, db.ForeignKey('Recipe.id', ondelete='CASCADE'), primary_key=True),
    db.Column('request_id', db.Integer, db.ForeignKey('Request.id', ondelete='CASCADE'), primary_key=True)
)


# Models
class Client(db.Model, UserMixin):
    __tablename__ = 'Client'

    id = db.Column(db.Integer, primary_key=True)
    phoneNumber = db.Column(db.String, nullable=False)
    address = db.Column(db.String, nullable=False)
    name = db.Column(db.String, nullable=False)
    surname = db.Column(db.String, nullable=False)

    # add login and password, make login unique
    login = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)

    # Relationships
    requests = db.relationship('Request', backref='client', lazy='dynamic')
    recipes = db.relationship('Recipe', backref='client', lazy='dynamic')
    recipe_reviews = db.relationship('RecipeReview', backref='client', lazy='dynamic')
    restaurant_reviews = db.relationship('RestaurantReview', backref='client', lazy='dynamic')

    def get_id(self):
        return f"C{self.id}"


class Request(db.Model):
    __tablename__ = 'Request'

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('Client.id', ondelete='RESTRICT'), nullable=False)
    withDelivery = db.Column(db.Boolean, nullable=False)
    address = db.Column(db.String, nullable=False)
    electronicPayment = db.Column(db.Boolean, nullable=False)

    # Relationships
    recipes = db.relationship('Recipe', secondary=recipe_request, backref='requests', lazy='dynamic')
    offers = db.relationship('Offer', backref='request', lazy='dynamic')


class RecipeType(db.Model):
    __tablename__ = 'RecipeType'

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String, unique=True, nullable=False)

    # Relationships
    recipes = db.relationship('Recipe', backref='recipe_type', lazy='dynamic')


class Recipe(db.Model):
    __tablename__ = 'Recipe'

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('Client.id', ondelete='RESTRICT'), nullable=False)
    recipe_type_id = db.Column(db.Integer, db.ForeignKey('RecipeType.id', ondelete='RESTRICT'), nullable=False)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.Text, nullable=False)
    recipeSteps = db.Column(db.Text, nullable=False)
    image_name = db.Column(db.String, nullable=False)

    # Relationships
    ingredients = db.relationship('Ingredient', secondary=recipe_ingredients, backref='recipes', lazy='dynamic')
    reviews = db.relationship('RecipeReview', backref='recipe', lazy='dynamic')


class Ingredient(db.Model):
    __tablename__ = 'Ingredient'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)


class RecipeReview(db.Model):
    __tablename__ = 'RecipeReview'

    client_id = db.Column(db.Integer, db.ForeignKey('Client.id', ondelete='CASCADE'), primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('Recipe.id', ondelete='CASCADE'), primary_key=True)
    rating = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=False)


class RestaurantReview(db.Model):
    __tablename__ = 'RestaurantReview'

    client_id = db.Column(db.Integer, db.ForeignKey('Client.id', ondelete='CASCADE'), primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('Restaurant.id', ondelete='CASCADE'), primary_key=True)
    rating = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text)


class Deliverer(db.Model, UserMixin):
    __tablename__ = 'Deliverer'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    surname = db.Column(db.String, nullable=False)

    # add login and password, make login unique
    login = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)

    # Relationships
    deliveries = db.relationship('Delivery', backref='deliverer', lazy='dynamic')
    restaurants = db.relationship('Restaurant', secondary=restaurant_deliverer, backref='deliverers', lazy='dynamic')

    def get_id(self):
        return f"D{self.id}"  # Prefix with D for Deliverer


class Restaurant(db.Model, UserMixin):
    __tablename__ = 'Restaurant'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    address = db.Column(db.String, nullable=False)

    # add login and password, make login unique
    login = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)

    # Relationships
    offers = db.relationship('Offer', backref='restaurant', lazy='dynamic')
    reviews = db.relationship('RestaurantReview', backref='restaurant', lazy='dynamic')

    def get_id(self):
        return f"R{self.id}"  # Prefix with D for Deliverer


class Orders(db.Model):
    __tablename__ = 'Orders'

    id = db.Column(db.Integer, primary_key=True)
    offer_id = db.Column(db.Integer, db.ForeignKey('Offer.id', ondelete='RESTRICT'), unique=True, nullable=False)
    orderStatus = db.Column(db.Enum(OrderStatus), nullable=False)
    notes = db.Column(db.Text)

    # Relationships
    delivery = db.relationship('Delivery', backref='order', uselist=False, lazy='select')
    offer = db.relationship('Offer', backref='order', uselist=False, lazy='select')
    payment = db.relationship('Payment', backref='order', uselist=False, lazy='select')


class Delivery(db.Model):
    __tablename__ = 'Delivery'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('Orders.id', ondelete='CASCADE'), nullable=False)
    deliverer_id = db.Column(db.Integer, db.ForeignKey('Deliverer.id', ondelete='RESTRICT'))
    deliveryStatus = db.Column(db.Enum(DeliveryStatus), nullable=False)
    deliveryDue = db.Column(db.DateTime, nullable=False)
    deliveryTime = db.Column(db.DateTime, nullable=False)


class Offer(db.Model):
    __tablename__ = 'Offer'

    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('Request.id', ondelete='RESTRICT'), nullable=False)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('Restaurant.id', ondelete='RESTRICT'), nullable=False)
    price = db.Column(db.Float, nullable=False)
    notes = db.Column(db.Text)
    waitingTime = db.Column(db.Time, nullable=False)


class Payment(db.Model):
    __tablename__ = 'Payment'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('Orders.id', ondelete='RESTRICT'), nullable=False)
    price = db.Column(db.Float, nullable=False)
    paymentStatus = db.Column(db.Enum(PaymentStatus), nullable=False)
