import pytest
from datetime import datetime, timedelta, time
from app import create_app, db
from config import TestingConfig

from app.models import (
    Client, Recipe, RecipeType, Restaurant, Orders, OrderStatus,
    Delivery, DeliveryStatus, Ingredient, Offer, Deliverer, Request
)

from app.deliverer.deliverer import (
    get_deliveries_by_status,
    delivery_done
)

from app.main.main import (
    get_ingredients,
    get_recepie_types,
    browse_recepies
)

from app.restaurant.restaurant import (
    get_orders,
    get_order,
    update_order,
    update_order_with_delivery,
    cancel_order,
    get_available_deliverers
)

@pytest.fixture(scope='function')
def app_context():
    app = create_app(config_class=TestingConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.mark.usefixtures("app_context")
class TestDelivererFunctions:
    def test_get_deliveries_by_status(self):
        # Create test client with all required fields
        client = Client(
            phoneNumber="123456789",
            address="Test Address",
            name="Test",
            surname="Client",
            login="testclient",
            password="testpass"
        )
        db.session.add(client)
        
        # Create deliverer with all required fields
        deliverer = Deliverer(
            name="Test",
            surname="Deliverer",
            login="testdeliv",
            password="testpass"
        )
        db.session.add(deliverer)
        
        # Create restaurant with all required fields
        restaurant = Restaurant(
            name="Test Restaurant",
            address="Test Address",
            login="testrest",
            password="testpass"
        )
        db.session.add(restaurant)
        db.session.commit()

        # Create request with all required fields
        request = Request(
            client_id=client.id,
            withDelivery=True,
            address="Delivery Address",
            electronicPayment=True
        )
        db.session.add(request)
        db.session.commit()

        # Create offer with all required fields including waitingTime
        offer = Offer(
            request_id=request.id,
            restaurant_id=restaurant.id,
            price=50.0,
            notes="Test offer",
            waitingTime=time(0, 45)  # 45 minutes waiting time
        )
        db.session.add(offer)
        db.session.commit()

        # Create order with required offer_id
        order = Orders(
            offer_id=offer.id,
            orderStatus=OrderStatus.InDelivery
        )
        db.session.add(order)
        db.session.commit()

        # Create deliveries
        delivery1 = Delivery(
            deliverer_id=deliverer.id,
            order_id=order.id,
            deliveryStatus=DeliveryStatus.InDelivery,
            deliveryDue=datetime.now() + timedelta(hours=1)
        )
        delivery2 = Delivery(
            deliverer_id=deliverer.id,
            order_id=order.id,
            deliveryStatus=DeliveryStatus.Delivered,
            deliveryDue=datetime.now() - timedelta(hours=1),
            deliveryTime=datetime.now()
        )
        db.session.add_all([delivery1, delivery2])
        db.session.commit()

        # Test the function
        result = get_deliveries_by_status(deliverer.id)
        
        assert len(result[DeliveryStatus.InDelivery]) == 1
        assert len(result[DeliveryStatus.Delivered]) == 1
        assert result[DeliveryStatus.InDelivery][0].id == delivery1.id
        assert result[DeliveryStatus.Delivered][0].id == delivery2.id

    def test_delivery_done(self):
        # Create test data with all required fields
        client = Client(
            phoneNumber="123456789",
            address="Test Address",
            name="Test",
            surname="Client",
            login="testclient",
            password="testpass"
        )
        db.session.add(client)

        deliverer = Deliverer(
            name="Test",
            surname="Deliverer",
            login="testdeliv",
            password="testpass"
        )
        db.session.add(deliverer)

        restaurant = Restaurant(
            name="Test Restaurant",
            address="Test Address",
            login="testrest",
            password="testpass"
        )
        db.session.add(restaurant)
        db.session.commit()

        request = Request(
            client_id=client.id,
            withDelivery=True,
            address="Delivery Address",
            electronicPayment=True
        )
        db.session.add(request)
        db.session.commit()

        offer = Offer(
            request_id=request.id,
            restaurant_id=restaurant.id,
            price=50.0,
            notes="Test offer",
            waitingTime=time(0, 45)
        )
        db.session.add(offer)
        db.session.commit()

        order = Orders(
            offer_id=offer.id,
            orderStatus=OrderStatus.InDelivery
        )
        db.session.add(order)
        db.session.commit()

        delivery = Delivery(
            deliverer_id=deliverer.id,
            order_id=order.id,
            deliveryStatus=DeliveryStatus.InDelivery,
            deliveryDue=datetime.now() + timedelta(hours=1)
        )
        db.session.add(delivery)
        db.session.commit()

        # Test the function
        updated_delivery = delivery_done(deliverer.id, delivery.id)
        
        assert updated_delivery.deliveryStatus == DeliveryStatus.Delivered
        assert updated_delivery.deliveryTime is not None
        assert Orders.query.get(order.id).orderStatus == OrderStatus.Delivered

@pytest.mark.usefixtures("app_context")
class TestMainFunctions:
    def test_get_ingredients(self):
        ingredients = [
            Ingredient(name="Tomato"),
            Ingredient(name="Cheese"),
            Ingredient(name="Flour")
        ]
        db.session.add_all(ingredients)
        db.session.commit()

        result = get_ingredients()
        assert len(result) == 3
        assert {i.name for i in result} == {"Tomato", "Cheese", "Flour"}

    def test_get_recepie_types(self):
        types = [
            RecipeType(type="Italian"),
            RecipeType(type="Mexican"),
            RecipeType(type="Asian")
        ]
        db.session.add_all(types)
        db.session.commit()

        result = get_recepie_types()
        assert len(result) == 3
        assert {t.type for t in result} == {"Italian", "Mexican", "Asian"}

    def test_browse_recepies(self):
        # Create test client
        client = Client(
            phoneNumber="123456789",
            address="Test Address",
            name="Test",
            surname="Client",
            login="testclient",
            password="testpass"
        )
        db.session.add(client)
        db.session.commit()

        # Create recipe types
        italian = RecipeType(type="Italian")
        mexican = RecipeType(type="Mexican")
        db.session.add_all([italian, mexican])
        db.session.commit()

        # Create ingredients
        ingredients = {
            "tomato": Ingredient(name="Tomato"),
            "cheese": Ingredient(name="Cheese"),
            "beef": Ingredient(name="Beef"),
            "beans": Ingredient(name="Beans")
        }
        db.session.add_all(ingredients.values())
        db.session.commit()

        # Create recipes with all required fields
        pizza = Recipe(
            name="Pizza Margherita",
            recipe_type_id=italian.id,
            description="Classic pizza",
            recipeSteps="Test steps",
            client_id=client.id,
            image_name="pizza.jpg"
        )
        
        pasta = Recipe(
            name="Pasta Carbonara",
            recipe_type_id=italian.id,
            description="Classic pasta",
            recipeSteps="Test steps",
            client_id=client.id,
            image_name="pasta.jpg"
        )
        
        taco = Recipe(
            name="Taco",
            recipe_type_id=mexican.id,
            description="Classic taco",
            recipeSteps="Test steps",
            client_id=client.id,
            image_name="taco.jpg"
        )

        db.session.add_all([pizza, pasta, taco])
        db.session.commit()

        # Add ingredients to recipes through the relationship
        db.session.execute(
            db.Table('RecipeIngredients', db.metadata).insert(),
            [
                {'recipe_id': pizza.id, 'ingredient_id': ingredients["tomato"].id, 'quantity': "1"},
                {'recipe_id': pizza.id, 'ingredient_id': ingredients["cheese"].id, 'quantity': "1l"},
                {'recipe_id': pasta.id, 'ingredient_id': ingredients["cheese"].id, 'quantity': "1"},
                {'recipe_id': taco.id, 'ingredient_id': ingredients["beef"].id, 'quantity': "1"},
                {'recipe_id': taco.id, 'ingredient_id': ingredients["beans"].id, 'quantity': "1"},
                {'recipe_id': taco.id, 'ingredient_id': ingredients["cheese"].id, 'quantity': "1kg"}
            ]
        )
        db.session.commit()

        # Test name search
        result = browse_recepies("Pizza", [], [], [])
        assert len(result) == 1
        assert all("Pizza" in r.name for r in result)

        # Test ingredient inclusion
        result = browse_recepies("", [ingredients["tomato"].id], [], [])
        assert len(result) == 1
        assert result[0].name == "Pizza Margherita"

        # Test multiple ingredients
        result = browse_recepies("", [ingredients["cheese"].id, ingredients["beef"].id], [], [])
        assert len(result) == 1
        assert result[0].name == "Taco"

        # Test ingredient exclusion
        result = browse_recepies("", [], [ingredients["beef"].id], [])
        assert len(result) == 2
        assert "Taco" not in [r.name for r in result]

        # Test category filter
        result = browse_recepies("", [], [], [mexican.id])
        assert len(result) == 1
        assert result[0].name == "Taco"

@pytest.mark.usefixtures("app_context")
class TestRestaurantFunctions:
    @pytest.fixture(autouse=True)
    def setup_method(self, app_context):
        self.client = Client(
            phoneNumber="123456789",
            address="Test Address",
            name="Test",
            surname="Client",
            login="testclient",
            password="testpass"
        )
        db.session.add(self.client)

        self.restaurant = Restaurant(
            name="Test Restaurant",
            address="Test Address",
            login="testrest",
            password="testpass"
        )
        db.session.add(self.restaurant)

        self.deliverer = Deliverer(
            name="Test",
            surname="Deliverer",
            login="testdeliv",
            password="testpass"
        )
        db.session.add(self.deliverer)
        db.session.commit()

        self.restaurant.deliverers.append(self.deliverer)
        db.session.commit()

    def test_get_orders(self):
        orders = {}
        for status in OrderStatus:
            request = Request(
                client_id=self.client.id,
                withDelivery=True,
                address="Test Address",
                electronicPayment=True
            )
            db.session.add(request)
            db.session.commit()

            offer = Offer(
                restaurant_id=self.restaurant.id,
                request_id=request.id,
                price=10.0,
                waitingTime=time(0, 30)
            )
            db.session.add(offer)
            db.session.commit()

            order = Orders(
                offer_id=offer.id,
                orderStatus=status
            )
            db.session.add(order)
            orders[status] = order
        db.session.commit()

        result = get_orders(self.restaurant.id)
        
        assert set(result.keys()) == set(OrderStatus)
        
        for status in OrderStatus:
            assert len(result[status]) == 1
            assert orders[status] in result[status]

    def test_get_order(self):
        # Create test data
        request = Request(
            client_id=self.client.id,
            withDelivery=True,
            address="Test Address",
            electronicPayment=True
        )
        db.session.add(request)
        db.session.commit()

        offer = Offer(
            restaurant_id=self.restaurant.id,
            request_id=request.id,
            price=10.0,
            waitingTime=time(0, 30)
        )
        db.session.add(offer)
        db.session.commit()

        order = Orders(
            offer_id=offer.id,
            orderStatus=OrderStatus.Registered
        )
        db.session.add(order)
        db.session.commit()

        result = get_order(order.id, self.restaurant.id)
        assert result is not None
        assert result.id == order.id
        assert result.orderStatus == OrderStatus.Registered

        result = get_order(order.id, self.restaurant.id + 1)
        assert result is None

        result = get_order(order.id + 1, self.restaurant.id)
        assert result is None

    def test_update_order(self):
        request = Request(
            client_id=self.client.id,
            withDelivery=True,
            address="Test Address",
            electronicPayment=True
        )
        db.session.add(request)
        db.session.commit()

        offer = Offer(
            restaurant_id=self.restaurant.id,
            request_id=request.id,
            price=10.0,
            waitingTime=time(0, 30)
        )
        db.session.add(offer)
        db.session.commit()

        order = Orders(
            offer_id=offer.id,
            orderStatus=OrderStatus.Registered
        )
        db.session.add(order)
        db.session.commit()

        result = update_order(order.id, self.restaurant.id, "InPreparation")
        assert result.orderStatus == OrderStatus.InPreparation
        assert result.notes is None

        result = update_order(order.id, self.restaurant.id, "WaitingForDelivery", "Test notes")
        assert result.orderStatus == OrderStatus.WaitingForDelivery
        assert result.notes == "Test notes"

        db_order = Orders.query.get(order.id)
        assert db_order.orderStatus == OrderStatus.WaitingForDelivery
        assert db_order.notes == "Test notes"

    def test_update_order_with_delivery(self):
        # Create test order
        request = Request(
            client_id=self.client.id,
            withDelivery=True,
            address="Test Address",
            electronicPayment=True
        )
        db.session.add(request)
        db.session.commit()

        offer = Offer(
            restaurant_id=self.restaurant.id,
            request_id=request.id,
            price=10.0,
            waitingTime=time(0, 30)
        )
        db.session.add(offer)
        db.session.commit()

        order = Orders(
            offer_id=offer.id,
            orderStatus=OrderStatus.WaitingForDelivery
        )
        db.session.add(order)
        db.session.commit()

        delivery_due = datetime.now() + timedelta(hours=1)
        result = update_order_with_delivery(
            order.id,
            self.deliverer.id,
            delivery_due,
            "Delivery notes"
        )

        assert result.orderStatus == OrderStatus.InDelivery
        assert result.notes == "Delivery notes"

        delivery = Delivery.query.filter_by(order_id=order.id).first()
        assert delivery is not None
        assert delivery.deliverer_id == self.deliverer.id
        assert delivery.deliveryStatus == DeliveryStatus.InDelivery
        assert delivery.deliveryDue == delivery_due

    def test_cancel_order(self):
        # Create test order
        request = Request(
            client_id=self.client.id,
            withDelivery=True,
            address="Test Address",
            electronicPayment=True
        )
        db.session.add(request)
        db.session.commit()

        offer = Offer(
            restaurant_id=self.restaurant.id,
            request_id=request.id,
            price=10.0,
            waitingTime=time(0, 30)
        )
        db.session.add(offer)
        db.session.commit()

        order = Orders(
            offer_id=offer.id,
            orderStatus=OrderStatus.Registered
        )
        db.session.add(order)
        db.session.commit()

        result = cancel_order(order.id, self.restaurant.id)
        assert result.orderStatus == OrderStatus.Canceled

        db_order = Orders.query.get(order.id)
        assert db_order.orderStatus == OrderStatus.Canceled

        with pytest.raises(AssertionError):
            cancel_order(order.id + 1, self.restaurant.id)

    def test_get_available_deliverers(self):
        # Add another deliverer
        deliverer2 = Deliverer(
            name="Second",
            surname="Deliverer",
            login="seconddeliv",
            password="testpass"
        )
        db.session.add(deliverer2)
        db.session.commit()

        # Associate second deliverer with restaurant
        self.restaurant.deliverers.append(deliverer2)
        db.session.commit()

        # Test getting deliverers
        result = get_available_deliverers(self.restaurant.id)
        
        # Verify list contains both deliverers
        assert len(result) == 2
        assert self.deliverer in result
        assert deliverer2 in result

        # Test with non-existent restaurant
        with pytest.raises(Exception):  # or specific exception type
            get_available_deliverers(self.restaurant.id + 1)