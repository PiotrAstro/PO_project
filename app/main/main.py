

from app.models import Ingredient, Recipe, RecipeType


def get_ingredients() -> list[Ingredient]:
    # This function should return a list of ingredients with the given ids
    return Ingredient.query.all()

def get_recepie_types() -> list[RecipeType]:
    # This function should return a list of all the categories of ingredients
    return RecipeType.query.all()

def construct_browsing_recepies_get_query(recepie_name: str, recepie_include: list[int], recepie_exclude: list[int], recepie_categories: list[int]) -> str:
    # This function should return a query string to be used in the browsing_recepies function
    query = f'?name={recepie_name}'
    if recepie_include:
        query += f'&include={",".join(map(str, recepie_include))}'
    if recepie_exclude:
        query += f'&exclude={",".join(map(str, recepie_exclude))}'
    if recepie_categories:
        query += f'&categories={",".join(map(str, recepie_categories))}'
    return query

def browse_recepies(recepie_name: str, recepie_include: list[int], recepie_exclude: list[int], recepie_categories: list[int]) -> list[Recipe]:
    # create this query
    recepies = Recipe.query.filter(Recipe.name.ilike(f'%{recepie_name}%')).all()
    if recepie_include:
        recepies = [recepie for recepie in recepies if all(include_id in recepie.ingredients for include_id in recepie_include)]
    if recepie_exclude:
        recepies = [recepie for recepie in recepies if not any(exclude_id in recepie.ingredients for exclude_id in recepie_exclude)]
    if recepie_categories:
        recepies = [recepie for recepie in recepies if recepie.recipe_type_id in recepie_categories]
    return recepies