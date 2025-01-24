from flask import Blueprint, render_template, request

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('main/index.html'), 200


@main_bp.route('/browsing-recepies')
def browsing_recepies():
    # take values from get
    recepie_name = request.args.get('name')
    recepie_include = request.args.get('include')
    recepie_exclude = request.args.get('exclude')
    recepie_categories = request.args.get('categories')

    return render_template('main/index.html'), 200
