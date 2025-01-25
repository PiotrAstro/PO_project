# app/client/client.py

from typing import List, Optional
from app.models import RecipeReview, Recipe, Client
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
