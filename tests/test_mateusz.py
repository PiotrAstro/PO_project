import pytest
from app import create_app, db
from app.config import TestingConfig

from app.client.client import (
    get_user,
    get_reviews,
    add_review,
    edit_review,
    delete_review,
    get_all_recipes,
    create_request,
    associate_recipes_to_request,
    get_available_offers,
    accept_offer,
    get_orders
)

from app.models import (
    Client,
    Recipe,
    RecipeReview,
    Restaurant,
    Offer,
    Orders,
    RecipeType
)


@pytest.fixture(scope='function')
def app_context():
    """
    Tworzy nową bazę danych przed każdym testem,
    a po teście zamyka sesję i usuwa wszystkie tabele.
    """
    app = create_app(config_class=TestingConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.mark.usefixtures("app_context")
class TestClientFunctions:

    def test_get_user(self):
        new_client = Client(
            phoneNumber="123456789",
            address="Test Address",
            name="Test",
            surname="User",
            login="testlogin_user",
            password="testpass"
        )
        db.session.add(new_client)
        db.session.commit()

        user = get_user("testlogin_user", "testpass")
        assert user is not None, "Powinno zwrócić obiekt użytkownika przy poprawnym loginie i haśle."
        assert user.login == "testlogin_user"

        user_wrong = get_user("testlogin_user", "wrongpass")
        assert user_wrong is None, "Powinno zwrócić None przy niepoprawnym haśle."

    def test_get_reviews(self):
        client = Client(
            phoneNumber="000111222",
            address="Another Address",
            name="Review",
            surname="Tester",
            login="reviewtester",
            password="reviewtester"
        )
        db.session.add(client)

        recipe_type = RecipeType(type='TestType')
        db.session.add(recipe_type)
        db.session.commit()

        recipe = Recipe(
            client_id=client.id,
            recipe_type_id=recipe_type.id,
            name="Test Recipe",
            description="Test description",
            recipeSteps="Test steps",
            image_name="default.jpg"
        )
        db.session.add(recipe)
        db.session.commit()

        new_review = RecipeReview(
            client_id=client.id,
            recipe_id=recipe.id,
            rating=5,
            description="Great recipe!"
        )
        db.session.add(new_review)
        db.session.commit()

        reviews = get_reviews(client.id)
        assert len(reviews) == 1, "Powinna istnieć dokładnie 1 recenzja."
        assert reviews[0].rating == 5
        assert reviews[0].description == "Great recipe!"
        assert reviews[0].recipe_name == "Test Recipe"

    def test_add_edit_delete_review(self):
        client = Client(
            phoneNumber="999888777",
            address="AddressX",
            name="Review",
            surname="Changer",
            login="reviewchanger",
            password="reviewchanger"
        )
        db.session.add(client)

        recipe_type = RecipeType(type="AnotherTestType")
        db.session.add(recipe_type)
        db.session.commit()

        recipe = Recipe(
            client_id=client.id,
            recipe_type_id=recipe_type.id,
            name="Another Recipe",
            description="Desc",
            recipeSteps="Steps",
            image_name="default.jpg"
        )
        db.session.add(recipe)
        db.session.commit()

        # add_review
        add_review(client.id, recipe.id, rating=3, description="Ok recipe")
        rev = RecipeReview.query.filter_by(client_id=client.id, recipe_id=recipe.id).first()
        assert rev is not None, "Recenzja powinna zostać utworzona."
        assert rev.rating == 3
        assert rev.description == "Ok recipe"

        # edit_review
        success_edit = edit_review(client.id, recipe.id, rating=5, description="Much better!")
        assert success_edit is True, "Edytowanie powinno się powieść."
        edited = RecipeReview.query.filter_by(client_id=client.id, recipe_id=recipe.id).first()
        assert edited.rating == 5
        assert edited.description == "Much better!"

        # delete_review
        success_delete = delete_review(client.id, recipe.id)
        assert success_delete is True, "Usunięcie recenzji powinno się powieść."
        deleted = RecipeReview.query.filter_by(client_id=client.id, recipe_id=recipe.id).first()
        assert deleted is None, "Recenzja powinna zostać usunięta."

    def test_get_all_recipes(self):
        client = Client(
            phoneNumber="111222333",
            address="Some Address",
            name="Recipe",
            surname="Tester",
            login="someclient",
            password="somepass"
        )
        db.session.add(client)

        recipe_type = RecipeType(type="TestType")
        db.session.add(recipe_type)
        db.session.commit()

        r1 = Recipe(
            client_id=client.id,
            recipe_type_id=recipe_type.id,
            name="Test Recipe 1",
            description="Desc 1",
            recipeSteps="Steps 1",
            image_name="default.jpg"
        )
        r2 = Recipe(
            client_id=client.id,
            recipe_type_id=recipe_type.id,
            name="Test Recipe 2",
            description="Desc 2",
            recipeSteps="Steps 2",
            image_name="default.jpg"
        )
        db.session.add_all([r1, r2])
        db.session.commit()

        recipes = get_all_recipes()
        names = [x.name for x in recipes]

        assert len(recipes) == 2, "Powinno zwrócić 2 przepisy."
        assert "Test Recipe 1" in names
        assert "Test Recipe 2" in names

    def test_create_and_associate_request(self):
        client = Client(
            phoneNumber="654654654",
            address="Request Address",
            name="Request",
            surname="Maker",
            login="requestmaker",
            password="requestmaker"
        )
        db.session.add(client)
        db.session.commit()

        req_id = create_request(
            client_id=client.id,
            withDelivery=True,
            address="Test Request Address",
            electronic_payment=True
        )
        assert req_id is not None, "Funkcja powinna zwrócić ID nowego zapytania."

        # Tworzymy RecipeType i dwa przepisy
        recipe_type = RecipeType(type="WrapType")
        db.session.add(recipe_type)
        db.session.commit()

        r1 = Recipe(
            client_id=client.id,
            recipe_type_id=recipe_type.id,
            name="Request Recipe 1",
            description="Desc",
            recipeSteps="Steps",
            image_name="default.jpg"
        )
        r2 = Recipe(
            client_id=client.id,
            recipe_type_id=recipe_type.id,
            name="Request Recipe 2",
            description="Desc",
            recipeSteps="Steps",
            image_name="default.jpg"
        )
        db.session.add_all([r1, r2])
        db.session.commit()

        associate_recipes_to_request(req_id, [r1.id, r2.id])

        from sqlalchemy import text
        results = db.session.execute(
            text('SELECT recipe_id FROM "RecipeRequest" WHERE request_id=:r'),
            {"r": req_id}
        ).fetchall()
        recipe_ids = [row[0] for row in results]
        assert r1.id in recipe_ids
        assert r2.id in recipe_ids

    def test_get_available_offers_and_accept(self):
        client = Client(
            phoneNumber="999000111",
            address="Offers Address",
            name="Offer",
            surname="Tester",
            login="offertester",
            password="offertester"
        )
        db.session.add(client)
        db.session.commit()

        req_id = create_request(client.id, True, "Offer Request Address", True)

        restaurant = Restaurant(
            name="Test Restaurant",
            address="Restaurant Address",
            login="restlogin",
            password="restpass"
        )
        db.session.add(restaurant)
        db.session.commit()

        offer = Offer(
            request_id=req_id,
            restaurant_id=restaurant.id,
            price=50.0,
            notes="Test Offer",
            waitingTime="00:45:00"
        )
        db.session.add(offer)
        db.session.commit()

        offers = get_available_offers(client.id)
        assert len(offers) == 1, "Powinna być dostępna dokładnie 1 oferta."

        accepted = accept_offer(offer.id, client.id)
        assert accepted is True, "Oferta powinna zostać zaakceptowana."

        accepted_again = accept_offer(offer.id, client.id)
        assert accepted_again is False, "Nie można zaakceptować ponownie tej samej oferty."

    def test_get_orders(self):
        client = Client(
            phoneNumber="777555333",
            address="Orders Address",
            name="Order",
            surname="Tester",
            login="ordertester",
            password="ordertester"
        )
        db.session.add(client)
        db.session.commit()

        req_id = create_request(client.id, True, "Test Orders Address", True)

        recipe_type = RecipeType(type="OrderType")
        db.session.add(recipe_type)
        db.session.commit()

        recipe = Recipe(
            client_id=client.id,
            recipe_type_id=recipe_type.id,
            name="OrderDish",
            description="Order dish desc",
            recipeSteps="Steps..",
            image_name="default.jpg"
        )
        db.session.add(recipe)
        db.session.commit()

        associate_recipes_to_request(req_id, [recipe.id])

        restaurant = Restaurant(
            name="Orders Test Restaurant",
            address="Restaurant Address",
            login="ordersrest",
            password="ordersrest"
        )
        db.session.add(restaurant)
        db.session.commit()

        offer = Offer(
            request_id=req_id,
            restaurant_id=restaurant.id,
            price=99.9,
            notes="Order offer notes",
            waitingTime="01:00:00"
        )
        db.session.add(offer)
        db.session.commit()

        accepted = accept_offer(offer.id, client.id)
        assert accepted is True, "accept_offer powinno zwrócić True."

        orders = get_orders(client.id)
        assert len(orders) == 1, "Klient powinien mieć dokładnie 1 zamówienie."
        o = orders[0]
        assert o["restaurant_name"] == "Orders Test Restaurant"
        assert o["price"] == 99.9
        assert "Registered" in str(o["orderStatus"]), "Status powinien być Registered."
