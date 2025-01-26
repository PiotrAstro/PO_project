# app/client/client.py

from typing import List, Optional
from app.models import RecipeReview, Recipe, Client, Request, Offer, Orders, OrderStatus
from app import db
from sqlalchemy import text


def get_user(login: str, password: str) -> Optional[Client]:
    # Ta funkcja powinna zwracać obiekt użytkownika, jeśli login i hasło są poprawne, inaczej None
    user = Client.query.filter_by(login=login, password=password).first()
    return user


def get_reviews(client_id):
    reviews = db.session.execute(
        text('''
            SELECT rr.*, r.name AS recipe_name
            FROM "RecipeReview" rr
            JOIN "Recipe" r ON rr.recipe_id = r.id
            WHERE rr.client_id = :client_id
        '''),
        {'client_id': client_id}
    ).fetchall()
    return reviews


def add_review(client_id, recipe_id, rating, description):
    db.session.execute(
        text('''
            INSERT INTO "RecipeReview" (client_id, recipe_id, rating, description)
            VALUES (:client_id, :recipe_id, :rating, :description)
        '''),
        {
            'client_id': client_id,
            'recipe_id': recipe_id,
            'rating': rating,
            'description': description
        }
    )
    db.session.commit()


def edit_review(client_id, recipe_id, rating, description):
    result = db.session.execute(
        text('''
            UPDATE "RecipeReview"
            SET rating = :rating, description = :description
            WHERE client_id = :client_id AND recipe_id = :recipe_id
        '''),
        {
            'rating': rating,
            'description': description,
            'client_id': client_id,
            'recipe_id': recipe_id
        }
    )
    db.session.commit()
    return result.rowcount > 0


def delete_review(client_id, recipe_id):
    result = db.session.execute(
        text('''
            DELETE FROM "RecipeReview"
            WHERE client_id = :client_id AND recipe_id = :recipe_id
        '''),
        {
            'client_id': client_id,
            'recipe_id': recipe_id
        }
    )
    db.session.commit()
    return result.rowcount > 0


def get_all_recipes():
    recipes = db.session.execute(
        text('''
            SELECT id, name FROM "Recipe"
            ORDER BY name ASC
        ''')
    ).fetchall()
    return recipes


def create_request(client_id, withDelivery, address, electronic_payment):
    try:
        new_request = Request(
            client_id=client_id,
            withDelivery=withDelivery,
            address=address,
            electronicPayment=electronic_payment
        )
        db.session.add(new_request)
        db.session.commit()
        return new_request.id
    except Exception as e:
        db.session.rollback()
        print(f"Error creating request: {e}")
        raise e


def associate_recipes_to_request(request_id, recipe_ids):
    for recipe_id in recipe_ids:
        db.session.execute(
            text('''
                INSERT INTO "RecipeRequest" (recipe_id, request_id)
                VALUES (:recipe_id, :request_id)
            '''),
            {
                'recipe_id': recipe_id,
                'request_id': request_id
            }
        )
    db.session.commit()


def get_available_offers(client_id):
    subquery = db.session.query(Request.id).join(Offer).join(Orders).filter(
        Request.client_id == client_id
    ).distinct().subquery()

    offers = db.session.query(Offer).join(Request).filter(
        Request.client_id == client_id,
        ~Offer.request_id.in_(subquery)
    ).all()

    offer_list = []
    for offer in offers:
        dish_names = [recipe.name for recipe in offer.request.recipes]
        offer_list.append({
            'id': offer.id,
            'dish_names': ', '.join(dish_names),
            'restaurant_name': offer.restaurant.name,
            'price': offer.price,
            'waitingTime': offer.waitingTime.strftime('%H:%M:%S') if offer.waitingTime else None,
            'request_id': offer.request.id,
            'address': offer.request.address
        })

    return offer_list


def accept_offer(offer_id, client_id):
    offer = Offer.query.join(Request).filter(
        Offer.id == offer_id,
        Request.client_id == client_id
    ).first()

    if not offer:
        return False

    existing_order = Orders.query.join(Offer).filter(
        Offer.request_id == offer.request_id
    ).first()

    if existing_order:
        return False

    try:
        new_order = Orders(
            offer_id=offer.id,
            orderStatus=OrderStatus.Registered,
            notes=offer.notes
        )
        db.session.add(new_order)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Error creating order: {e}")
        return False


def get_orders(client_id):
    query = text('''
        SELECT 
            "Orders".id AS order_id, 
            "Orders"."orderStatus", 
            "Orders".notes,
            "Restaurant".name AS restaurant_name,
            "Offer".price, 
            "Offer"."waitingTime", 
            "Request".address,
            STRING_AGG("Recipe".name, ', ') AS dish_names
        FROM 
            "Orders"
        JOIN 
            "Offer" ON "Orders".offer_id = "Offer".id
        JOIN 
            "Request" ON "Offer".request_id = "Request".id
        JOIN 
            "Restaurant" ON "Offer".restaurant_id = "Restaurant".id
        JOIN 
            "RecipeRequest" ON "Request".id = "RecipeRequest".request_id
        JOIN
            "Recipe" ON "RecipeRequest".recipe_id = "Recipe".id
        WHERE 
            "Request".client_id = :client_id
        GROUP BY
            "Orders".id, 
            "Restaurant".name, 
            "Offer".price, 
            "Offer"."waitingTime", 
            "Orders"."orderStatus", 
            "Orders".notes,
            "Request".address
        ORDER BY
            "Orders".id DESC
    ''')

    try:
        result = db.session.execute(query, {'client_id': client_id}).mappings().fetchall()
    except Exception as e:
        print(f"Error executing get_orders query: {e}")
        return []

    orders = []
    for row in result:
        waiting_time = row['waitingTime'].strftime('%H:%M:%S') if row['waitingTime'] else None

        orders.append({
            'id': row['order_id'],
            'dish_names': row['dish_names'],
            'restaurant_name': row['restaurant_name'],
            'price': row['price'],
            'orderStatus': row['orderStatus']
        })

    return orders

# ----------------------------
def get_recipes_for_client(client_id: int):
    """
    Pobiera wszystkie przepisy danego klienta.
    """
    recipes = db.session.execute(
        text('''
            SELECT *
            FROM "Recipe"
            WHERE client_id = :client_id
        '''),
        {'client_id': client_id}
    ).fetchall()
    return recipes


def create_recipe(client_id: int,
                  recipe_type_id: int,
                  name: str,
                  description: str,
                  recipe_steps: str,
                  image_name: str,
                  ingredient_ids: List[int],
                  quantities: List[str]) -> int:
    """
    Tworzy nowy przepis i przypisuje do niego składniki.
    Zwraca ID nowo utworzonego przepisu lub rzuca wyjątek w przypadku błędu.
    """
    try:
        result = db.session.execute(
            text('''
                INSERT INTO "Recipe" (client_id, recipe_type_id, name, description, "recipeSteps", image_name)
                VALUES (:client_id, :recipe_type_id, :name, :description, :recipe_steps, :image_name)
                RETURNING id
            '''),
            {
                'client_id': client_id,
                'recipe_type_id': recipe_type_id,
                'name': name,
                'description': description,
                'recipe_steps': recipe_steps,
                'image_name': image_name
            }
        )
        recipe_id = result.fetchone()[0]

        # Dodawanie składników do tabeli RecipeIngredients
        for ingredient_id, quantity in zip(ingredient_ids, quantities):
            db.session.execute(
                text('''
                    INSERT INTO "RecipeIngredients" (recipe_id, ingredient_id, quantity)
                    VALUES (:recipe_id, :ingredient_id, :quantity)
                '''),
                {'recipe_id': recipe_id, 'ingredient_id': ingredient_id, 'quantity': quantity}
            )

        db.session.commit()
        return recipe_id

    except Exception as e:
        db.session.rollback()
        raise e


def get_recipe_types():
    """
    Pobiera wszystkie możliwe typy przepisów (RecipeType).
    """
    recipe_types = db.session.execute(text('SELECT * FROM "RecipeType"')).fetchall()
    return recipe_types


def get_ingredients():
    """
    Pobiera wszystkie składniki (Ingredient).
    """
    ingredients = db.session.execute(text('SELECT * FROM "Ingredient"')).fetchall()
    return ingredients


def update_recipe(recipe_id: int,
                  client_id: int,
                  name: str,
                  description: str,
                  recipe_steps: str,
                  recipe_type_id: int,
                  ingredient_ids: List[int],
                  quantities: List[str]) -> None:
    """
    Aktualizuje przepis (Recipe) i przypisuje mu nowe składniki (lub zmienione).
    """
    db.session.execute(
        text('''
            UPDATE "Recipe"
            SET name = :name,
                description = :description,
                "recipeSteps" = :recipe_steps,
                recipe_type_id = :recipe_type_id
            WHERE id = :recipe_id
              AND client_id = :client_id
        '''),
        {
            'name': name,
            'description': description,
            'recipe_steps': recipe_steps,
            'recipe_type_id': recipe_type_id,
            'recipe_id': recipe_id,
            'client_id': client_id
        }
    )

    # Najpierw usuwamy wszystkie składniki przepisu, aby potem dodać je ponownie.
    db.session.execute(
        text('''
            DELETE FROM "RecipeIngredients"
            WHERE recipe_id = :recipe_id
        '''),
        {'recipe_id': recipe_id}
    )

    # Dodajemy aktualne składniki
    for ingredient_id, quantity in zip(ingredient_ids, quantities):
        db.session.execute(
            text('''
                INSERT INTO "RecipeIngredients" (recipe_id, ingredient_id, quantity)
                VALUES (:recipe_id, :ingredient_id, :quantity)
            '''),
            {'recipe_id': recipe_id, 'ingredient_id': ingredient_id, 'quantity': quantity}
        )

    db.session.commit()


def get_recipe_by_id(recipe_id: int, client_id: int):
    """
    Zwraca pojedynczy przepis (Recipe) dla danego klienta.
    """
    recipe = db.session.execute(
        text('''
            SELECT *
            FROM "Recipe"
            WHERE id = :recipe_id
              AND client_id = :client_id
        '''),
        {'recipe_id': recipe_id, 'client_id': client_id}
    ).fetchone()
    return recipe


def get_recipe_ingredients(recipe_id: int):
    """
    Zwraca składniki powiązane z danym przepisem.
    """
    recipe_ingredients = db.session.execute(
        text('''
            SELECT ri.ingredient_id, i.name, ri.quantity
            FROM "RecipeIngredients" ri
            JOIN "Ingredient" i ON ri.ingredient_id = i.id
            WHERE ri.recipe_id = :recipe_id
        '''),
        {'recipe_id': recipe_id}
    ).fetchall()
    return recipe_ingredients


def remove_recipe(recipe_id: int, client_id: int) -> bool:
    """
    Usuwa przepis o danym ID należący do klienta, o ile nie ma powiązanych zamówień.
    Zwraca True w przypadku powodzenia usunięcia, False jeśli powiązania uniemożliwiają usunięcie.
    """
    # Sprawdzamy, czy przepis w ogóle istnieje i należy do danego klienta
    recipe = db.session.execute(
        text('''
            SELECT *
            FROM "Recipe"
            WHERE id = :recipe_id
              AND client_id = :client_id
        '''),
        {
            'recipe_id': recipe_id,
            'client_id': client_id
        }
    ).fetchone()

    if not recipe:
        return False  # Brak przepisu lub nieautoryzowany dostęp

    # Sprawdzamy, czy są powiązane Requesty (RecipeRequest + Request)
    linked_requests = db.session.execute(
        text('''
            SELECT 1
            FROM "RecipeRequest" rr
            JOIN "Request" r ON rr.request_id = r.id
            WHERE rr.recipe_id = :recipe_id
        '''),
        {'recipe_id': recipe_id}
    ).fetchone()

    if linked_requests:
        return False  # Nie można usunąć przepisu powiązanego z istniejącymi Requestami

    # Usuwamy powiązane składniki
    db.session.execute(
        text('''
            DELETE FROM "RecipeIngredients"
            WHERE recipe_id = :recipe_id
        '''),
        {'recipe_id': recipe_id}
    )

    # Usuwamy sam przepis
    db.session.execute(
        text('''
            DELETE FROM "Recipe"
            WHERE id = :recipe_id
              AND client_id = :client_id
        '''),
        {'recipe_id': recipe_id, 'client_id': client_id}
    )

    # Usuwamy "osierocone" składniki, które nie występują już w żadnym przepisie
    db.session.execute(
        text('''
            DELETE FROM "Ingredient"
            WHERE id NOT IN (
                SELECT DISTINCT ingredient_id
                FROM "RecipeIngredients"
            )
        ''')
    )

    db.session.commit()
    return True


def add_recipe_type(recipe_type: str) -> None:
    """
    Dodaje nowy typ przepisu (RecipeType).
    """
    db.session.execute(
        text('''
            INSERT INTO "RecipeType" (type)
            VALUES (:type)
        '''),
        {'type': recipe_type}
    )
    db.session.commit()


def add_ingredient(ingredient_name: str) -> None:
    """
    Dodaje nowy składnik (Ingredient).
    """
    db.session.execute(
        text('''
            INSERT INTO "Ingredient" (name)
            VALUES (:name)
        '''),
        {'name': ingredient_name}
    )
    db.session.commit()


def get_recipe_for_view(recipe_id: int, client_id: int):
    """
    Zwraca przepis (w formie Mapping lub None) i listę składników do wyświetlenia.
    """
    recipe = db.session.execute(
        text('''
            SELECT *
            FROM "Recipe"
            WHERE id = :recipe_id
              AND client_id = :client_id
        '''),
        {'recipe_id': recipe_id, 'client_id': client_id}
    ).mappings().fetchone()

    if not recipe:
        return None, None

    recipe_ingredients = db.session.execute(
        text('''
            SELECT ri.quantity, i.name
            FROM "RecipeIngredients" ri
            JOIN "Ingredient" i ON ri.ingredient_id = i.id
            WHERE ri.recipe_id = :recipe_id
        '''),
        {'recipe_id': recipe_id}
    ).fetchall()

    return recipe, recipe_ingredients