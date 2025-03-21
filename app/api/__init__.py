from flask import Blueprint
from app.api import users, units, auth, rentals

api = Blueprint('api', __name__)
