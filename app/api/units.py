from flask import Blueprint, request, jsonify
from app.services.unit_service import UnitService
from app.api.auth import token_required

units_bp = Blueprint('units', __name__)


@units_bp.route('/', methods=['GET'])
def get_units():
    """Get all units or filter by query parameters"""
    floor_level = request.args.get('floor_level')
    status = request.args.get('status')
    units = UnitService.get_all_units(floor_level, status)
    return jsonify(units)


@units_bp.route('/available', methods=['GET'])
def get_available_units():
    """Get all available units"""
    units = UnitService.get_available_units()
    return jsonify(units)


@units_bp.route('/user/<int:user_id>', methods=['GET'])
@token_required
def get_user_units(user_id):
    """Get units owned or rented by a user"""
    units = UnitService.get_user_units(user_id)
    return jsonify(units)
