import pytest
from sqlalchemy import text
from app import create_app, db
from config import TestingConfig

# Importy dla części klienta:
from app.client.client import (
    get_recipes_for_client,
    create_recipe,
    get_recipe_types,
    get_ingredients,
    update_recipe,
    get_recipe_by_id,
    get_recipe_ingredients,
    add_recipe_type,
    add_ingredient,
    get_recipe_for_view
)

# Importy dla części restauracyjnej:
from app.restaurant.restaurant import (
    get_available_requests,
    create_offer
)

# Importujemy modele, by móc tworzyć obiekty testowe w bazie:
from app.models import (
    Client,
    Recipe,
    RecipeType,
    Ingredient,
    Restaurant,
    Request,
    recipe_request as RecipeRequest,
    recipe_ingredients as RecipeIngredients,
    Offer
)


@pytest.fixture(scope='function')
def app_context():
    """
    Tworzy świeżą bazę danych przed każdym testem
    i usuwa wszystkie tabele po każdym teście.
    """
    app = create_app(config_class=TestingConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.mark.usefixtures("app_context")
class TestClientService:

    def test_get_recipes_for_client(self):
        # Tworzymy klienta
        client = Client(
            phoneNumber="123456789",
            address="Client Address",
            name="John",
            surname="Doe",
            login="johndoe",
            password="secret"
        )
        db.session.add(client)
        db.session.commit()

        # Tworzymy 2 przepisy dla tego klienta i 1 przepis dla innego
        recipe_type = RecipeType(type="TestType")
        db.session.add(recipe_type)
        db.session.commit()

        r1 = Recipe(client_id=client.id, recipe_type_id=recipe_type.id,
                    name="Recipe1", description="Desc1", recipeSteps="Steps1",
                    image_name="default.jpg")
        r2 = Recipe(client_id=client.id, recipe_type_id=recipe_type.id,
                    name="Recipe2", description="Desc2", recipeSteps="Steps2",
                    image_name="default.jpg")
        db.session.add_all([r1, r2])
        db.session.commit()

        another_client = Client(
            phoneNumber="987654321",
            address="Other Address",
            name="Jane",
            surname="Smith",
            login="janesmith",
            password="secret2"
        )
        db.session.add(another_client)
        db.session.commit()

        r3 = Recipe(client_id=another_client.id, recipe_type_id=recipe_type.id,
                    name="OtherRecipe", description="...", recipeSteps="...",
                    image_name="default.jpg")
        db.session.add(r3)
        db.session.commit()

        # Testujemy get_recipes_for_client
        my_recipes = get_recipes_for_client(client.id)
        assert len(my_recipes) == 2
        names = {row.name for row in my_recipes}
        assert "Recipe1" in names
        assert "Recipe2" in names

    def test_create_recipe(self):
        # Tworzymy klienta i typ przepisu
        client = Client(
            phoneNumber="111222333",
            address="Test Address",
            name="TestName",
            surname="TestSurname",
            login="testlogin",
            password="testpass"
        )
        db.session.add(client)
        db.session.commit()

        recipe_type = RecipeType(type="SpaghettiType")
        db.session.add(recipe_type)
        db.session.commit()

        # Tworzymy 2 składniki
        i1 = Ingredient(name="Tomato")
        i2 = Ingredient(name="Cheese")
        db.session.add_all([i1, i2])
        db.session.commit()

        # Wywołujemy create_recipe
        recipe_id = create_recipe(
            client_id=client.id,
            recipe_type_id=recipe_type.id,
            name="Spaghetti",
            description="Delicious spaghetti",
            recipe_steps="Boil pasta. Mix sauce.",
            image_name="spaghetti.jpg",
            ingredient_ids=[i1.id, i2.id],
            quantities=["2", "1"]
        )

        # Sprawdzamy, czy przepis faktycznie jest w bazie:
        #created_recipe = Recipe.query.get(recipe_id)
        created_recipe = db.session.get(Recipe, recipe_id)
        assert created_recipe is not None
        assert created_recipe.name == "Spaghetti"
        assert created_recipe.client_id == client.id

        # Sprawdzamy składniki
        rec_ing = db.session.execute(
            text('SELECT ingredient_id, quantity FROM "RecipeIngredients" WHERE recipe_id=:rid'),
            {"rid": recipe_id}
        ).fetchall()
        assert len(rec_ing) == 2
        # Można sprawdzić wartości konkretnie:
        ing_ids = [row[0] for row in rec_ing]
        quantities = [row[1] for row in rec_ing]
        assert i1.id in ing_ids
        assert i2.id in ing_ids
        assert "2" in quantities
        assert "1" in quantities

    def test_get_recipe_types(self):
        rt1 = RecipeType(type="Type1")
        rt2 = RecipeType(type="Type2")
        db.session.add_all([rt1, rt2])
        db.session.commit()

        result = get_recipe_types()
        assert len(result) == 2
        types = {row.type for row in result}
        assert "Type1" in types
        assert "Type2" in types

    def test_get_ingredients(self):
        i1 = Ingredient(name="Ing1")
        i2 = Ingredient(name="Ing2")
        db.session.add_all([i1, i2])
        db.session.commit()

        ings = get_ingredients()
        names = {x.name for x in ings}
        assert len(ings) == 2
        assert {"Ing1", "Ing2"} == names

    def test_update_recipe(self):
        # Setup: klient, przepis i składniki
        client = Client(
            phoneNumber="999888777",
            address="Some Address",
            name="UpdateClient",
            surname="Tester",
            login="update_login",
            password="update_pass"
        )
        db.session.add(client)

        recipe_type = RecipeType(type="InitialType")
        db.session.add(recipe_type)
        db.session.commit()

        recipe = Recipe(
            client_id=client.id,
            recipe_type_id=recipe_type.id,
            name="Old Name",
            description="Old Desc",
            recipeSteps="Old Steps",
            image_name="old.jpg"
        )
        db.session.add(recipe)
        db.session.commit()

        i1 = Ingredient(name="OldIng")
        db.session.add(i1)
        db.session.commit()

        # Dodajemy składnik do przepisu
        db.session.execute(
            text('''
                INSERT INTO "RecipeIngredients" (recipe_id, ingredient_id, quantity)
                VALUES (:rid, :iid, :q)
            '''),
            {"rid": recipe.id, "iid": i1.id, "q": "100g"}
        )
        db.session.commit()

        # Nowe składniki
        i2 = Ingredient(name="NewIng1")
        i3 = Ingredient(name="NewIng2")
        db.session.add_all([i2, i3])
        db.session.commit()

        update_recipe(
            recipe_id=recipe.id,
            client_id=client.id,
            name="New Name",
            description="New Desc",
            recipe_steps="New Steps",
            recipe_type_id=recipe_type.id,
            ingredient_ids=[i2.id, i3.id],
            quantities=["200g", "300g"]
        )

        # Sprawdzamy, czy główne dane się zaktualizowały
        #updated_recipe = Recipe.query.get(recipe.id)
        updated_recipe = db.session.get(Recipe, recipe.id)
        assert updated_recipe is not None
        assert updated_recipe.name == "New Name"
        assert updated_recipe.description == "New Desc"
        assert updated_recipe.recipeSteps == "New Steps"

        # Sprawdzamy, czy stare składniki zostały usunięte i zastąpione nowymi
        r_ings = db.session.execute(
            text('SELECT ingredient_id, quantity FROM "RecipeIngredients" WHERE recipe_id=:rid'),
            {"rid": recipe.id}
        ).fetchall()
        assert len(r_ings) == 2

        ing_ids = [row[0] for row in r_ings]
        quantities = [row[1] for row in r_ings]
        assert i2.id in ing_ids
        assert i3.id in ing_ids
        assert "200g" in quantities
        assert "300g" in quantities

    def test_get_recipe_by_id(self):
        client = Client(
            phoneNumber="111111111",
            address="ClientTest",
            name="TestName",
            surname="TestSurname",
            login="someLogin",
            password="somePass"
        )
        db.session.add(client)
        db.session.commit()

        recipe_type = RecipeType(type="T")
        db.session.add(recipe_type)
        db.session.commit()

        recipe = Recipe(
            client_id=client.id,
            recipe_type_id=recipe_type.id,
            name="GetByID",
            description="...",
            recipeSteps="...",
            image_name="img.jpg"
        )
        db.session.add(recipe)
        db.session.commit()

        found = get_recipe_by_id(recipe.id, client.id)
        assert found is not None
        assert found.name == "GetByID"

        not_found = get_recipe_by_id(recipe.id, 9999)  # inny klient
        assert not_found is None

    def test_get_recipe_ingredients(self):
        # Tworzymy przepis i 2 składniki
        client = Client(
            phoneNumber="333444555",
            address="IngTest",
            name="Ing",
            surname="Test",
            login="ing_login",
            password="ing_pass"
        )
        db.session.add(client)
        db.session.commit()

        rt = RecipeType(type="IngType")
        db.session.add(rt)
        db.session.commit()

        recipe = Recipe(
            client_id=client.id,
            recipe_type_id=rt.id,
            name="IngRecipe",
            description="",
            recipeSteps="",
            image_name="default.jpg"
        )
        db.session.add(recipe)
        db.session.commit()

        i1 = Ingredient(name="Salt")
        i2 = Ingredient(name="Pepper")
        db.session.add_all([i1, i2])
        db.session.commit()

        # Dodajemy powiązania
        db.session.execute(
            text('''
                INSERT INTO "RecipeIngredients" (recipe_id, ingredient_id, quantity)
                VALUES (:rid, :iid, :q)
            '''),
            {"rid": recipe.id, "iid": i1.id, "q": "1 tsp"}
        )
        db.session.execute(
            text('''
                INSERT INTO "RecipeIngredients" (recipe_id, ingredient_id, quantity)
                VALUES (:rid, :iid, :q)
            '''),
            {"rid": recipe.id, "iid": i2.id, "q": "2 tsp"}
        )
        db.session.commit()

        ings = get_recipe_ingredients(recipe.id)
        assert len(ings) == 2
        # Możesz sprawdzić nazwy i ilości:
        names = {row.name for row in ings}
        quants = {row.quantity for row in ings}
        assert names == {"Salt", "Pepper"}
        assert quants == {"1 tsp", "2 tsp"}

    def test_add_recipe_type(self):
        add_recipe_type("MegaType")
        add_recipe_type("UltraType")
        result = db.session.execute(text('SELECT * FROM "RecipeType"')).fetchall()
        assert len(result) == 2
        types = [row.type for row in result]
        assert "MegaType" in types
        assert "UltraType" in types

    def test_add_ingredient(self):
        add_ingredient("Chili")
        add_ingredient("Garlic")
        result = db.session.execute(text('SELECT * FROM "Ingredient"')).fetchall()
        names = {row.name for row in result}
        assert {"Chili", "Garlic"} == names

    def test_get_recipe_for_view(self):
        client = Client(
            phoneNumber="101010101",
            address="ViewAddr",
            name="ViewName",
            surname="ViewSurname",
            login="viewlogin",
            password="viewpass"
        )
        db.session.add(client)
        db.session.commit()

        rt = RecipeType(type="ViewType")
        db.session.add(rt)
        db.session.commit()

        recipe = Recipe(
            client_id=client.id,
            recipe_type_id=rt.id,
            name="ViewRecipe",
            description="DESC",
            recipeSteps="STEPS",
            image_name="view.jpg"
        )
        db.session.add(recipe)
        db.session.commit()

        i1 = Ingredient(name="I1")
        i2 = Ingredient(name="I2")
        db.session.add_all([i1, i2])
        db.session.commit()

        db.session.execute(
            text('''
                INSERT INTO "RecipeIngredients" (recipe_id, ingredient_id, quantity)
                VALUES (:rid, :iid, :q)
            '''),
            {"rid": recipe.id, "iid": i1.id, "q": "10"}
        )
        db.session.execute(
            text('''
                INSERT INTO "RecipeIngredients" (recipe_id, ingredient_id, quantity)
                VALUES (:rid, :iid, :q)
            '''),
            {"rid": recipe.id, "iid": i2.id, "q": "20"}
        )
        db.session.commit()

        r, r_ings = get_recipe_for_view(recipe.id, client.id)
        assert r is not None
        assert r["name"] == "ViewRecipe"
        assert len(r_ings) == 2
        q_values = {row.quantity for row in r_ings}
        assert q_values == {"10", "20"}

        # Spróbuj wywołać z innym client_id:
        r2, r_ings2 = get_recipe_for_view(recipe.id, 9999)
        assert r2 is None
        assert r_ings2 is None


@pytest.mark.usefixtures("app_context")
class TestRestaurantService:

    def test_get_available_requests(self):
        # Tworzymy restaurację
        restaurant = Restaurant(
            name="TestRestaurant",
            address="RestAddr",
            login="restlogin",
            password="restpass"
        )
        db.session.add(restaurant)

        # Tworzymy klienta
        client = Client(
            phoneNumber="777666555",
            address="Some ClientAddr",
            name="ClientName",
            surname="ClientSurname",
            login="clientlogin",
            password="clientpass"
        )
        db.session.add(client)
        db.session.commit()

        # Tworzymy Request + powiązany Recipe
        req = Request(client_id=client.id, withDelivery=True, address="X", electronicPayment=False)
        db.session.add(req)
        db.session.commit()

        # Musi istnieć Recipe + RecipeRequest, bo w get_available_requests jest JOIN z "RecipeRequest"
        rtype = RecipeType(type="ABC")
        db.session.add(rtype)
        db.session.commit()

        recipe = Recipe(
            client_id=client.id,
            recipe_type_id=rtype.id,
            name="RequestRecipe",
            description="..",
            recipeSteps="..",
            image_name="default.jpg"
        )
        db.session.add(recipe)
        db.session.commit()

        # rr = RecipeRequest(request_id=req.id, recipe_id=recipe.id)
        # db.session.add(rr)
        # db.session.commit()
        db.session.execute(
            text('INSERT INTO "RecipeRequest" (request_id, recipe_id) VALUES (:req_id, :rec_id)'),
            {'req_id': req.id, 'rec_id': recipe.id}
        )
        db.session.commit()

        # Na początku request powinien być dostępny
        available = get_available_requests(restaurant.id)
        assert len(available) == 1
        assert available[0].request_id == req.id

        # Gdy dodamy ofertę -> request nie będzie już dostępny
        offer = Offer(
            request_id=req.id,
            restaurant_id=restaurant.id,
            price=50.0,
            notes="OfferNotes",
            waitingTime="00:30:00"
        )
        db.session.add(offer)
        db.session.commit()

        after_offer = get_available_requests(restaurant.id)
        assert len(after_offer) == 0

    def test_create_offer(self):
        restaurant = Restaurant(name="Rest1", address="R1Addr", login="r1", password="r1")
        db.session.add(restaurant)

        client = Client(phoneNumber="222333444", address="ClientX", name="C", surname="X", login="cx", password="cx")
        db.session.add(client)
        db.session.commit()

        req = Request(client_id=client.id, withDelivery=False, address="ReqAddr", electronicPayment=False)
        db.session.add(req)
        db.session.commit()

        # Tworzymy:
        create_offer(restaurant_id=restaurant.id, request_id=req.id, price=99.99, notes="TestOffer", waiting_time="00:20:00")

        # Sprawdzamy w bazie:
        offers = db.session.query(Offer).all()
        assert len(offers) == 1
        assert offers[0].price == 99.99
        assert offers[0].notes == "TestOffer"
        assert str(offers[0].waitingTime) == "0:20:00" or "00:20:00"
