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



def create_request(client_id, withDelivery, address, electronic_payment) :
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


def get_available_offers(client_id: int):
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
            'waitingTime': offer.waitingTime.strftime('%H:%M:%S') if offer.waitingTime else None
        })

    return offer_list


def accept_offer(offer_id: int, client_id: int) -> bool:
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


def get_orders(client_id: int):
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