from flask import Blueprint, render_template, request

from app.main.main import browse_recepies, construct_browsing_recepies_get_query, get_ingredients, get_recepie_types

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('main/index.html'), 200


@main_bp.route('/browsing-recepies')
def browsing_recepies():
    # take values from get
    recepie_name = request.args.get('name')
    if not recepie_name:
        recepie_name = ""

    recepie_include = request.args.get('include')
    if recepie_include:
        recepie_include = [int(idx) for idx in recepie_include.split(',')]
    else:
        recepie_include = []
    recepie_exclude = request.args.get('exclude')
    if recepie_exclude:
        recepie_exclude = [int(idx) for idx in recepie_exclude.split(',')]
    else:
        recepie_exclude = []

    recepie_categories = request.args.get('categories')
    if recepie_categories:
        recepie_categories = [int(idx) for idx in recepie_categories.split(',')]
    else:
        recepie_categories = []

    recepie_types = get_recepie_types()
    ingredients = get_ingredients()

    return render_template(
        'main/browsing_recepies.html',
        goto='/search-recepies',
        recepie_name=recepie_name,
        recepie_include=recepie_include,
        recepie_exclude=recepie_exclude,
        recepie_categories=recepie_categories,
        all_recepie_types=recepie_types,
        all_ingredients=ingredients
    )


@main_bp.route('/search-recepies')
def search_recepies():
    # take values from get
    recepie_name_original = request.args.get('name')
    if not recepie_name_original:
        recepie_name_original = ""
    

    recepie_include = request.args.getlist('include')
    if recepie_include:
        recepie_include = [int(idx) for idx in recepie_include]
    else:
        recepie_include = []

    recepie_exclude = request.args.getlist('exclude')
    if recepie_exclude:
        recepie_exclude = [int(idx) for idx in recepie_exclude]
    else:
        recepie_exclude = []

    recepie_categories = request.args.getlist('categories')
    if recepie_categories:
        recepie_categories = [int(idx) for idx in recepie_categories]
    else:
        recepie_categories = []

    browsing_url = "/browsing-recepies" + construct_browsing_recepies_get_query(recepie_name_original, recepie_include, recepie_exclude, recepie_categories)
    recepies_conforming = browse_recepies(recepie_name_original, recepie_include, recepie_exclude, recepie_categories)
    return render_template(
        'main/search_recepies.html',
        goback=browsing_url,
        recepies=recepies_conforming
    )

