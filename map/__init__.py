from flask import Blueprint

map_bp = Blueprint('map', __name__, url_prefix='/map')

from . import routes
