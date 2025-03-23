from flask import Blueprint, request, jsonify, g
from app.services.unit_service import UnitService
from app.api.auth import token_required
from app.schemas.unit import UnitCreateSchema, UnitUpdateSchema, UnitResponseSchema
from marshmallow import ValidationError

units_bp = Blueprint('units', __name__)

# GET routes


@units_bp.route('/', methods=['GET'])
def get_units():
    """Get all units with optional filters"""
    filters = {
        'city': request.args.get('city'),
        'floor_level': request.args.get('floor_level'),
        'status': request.args.get('status'),
        'min_size': request.args.get('min_size', type=float),
        'max_size': request.args.get('max_size', type=float),
        'min_price': request.args.get('min_price', type=float),
        'max_price': request.args.get('max_price', type=float),
        'features': request.args.getlist('features')
    }
    units = UnitService.search_units(**filters)
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
    if str(g.current_user['id']) != str(user_id):
        return jsonify({"error": "Unauthorized"}), 403
    units = UnitService.get_user_units(user_id)
    return jsonify(units)


@units_bp.route('/<string:unit_id>', methods=['GET'])
@token_required
def get_unit(unit_id):
    """Get a specific unit by ID"""
    unit = UnitService.get_unit_by_id(
        unit_id,
        current_user_id=g.current_user['id'] if g.current_user else None
    )
    if not unit:
        return jsonify({"error": "Unit not found"}), 404
    return jsonify(unit)


@units_bp.route('/statistics', methods=['GET'])
@token_required
def get_statistics():
    """Get unit statistics"""
    stats = UnitService.get_unit_statistics()
    return jsonify(stats)

# POST routes


@units_bp.route('/', methods=['POST'])
@token_required
def create_unit():
    """Create a new unit"""
    try:
        schema = UnitCreateSchema()
        data = schema.load(request.json)
        data['user_id'] = g.current_user['id']

        result = UnitService.create_unit(data)
        if "error" in result:
            return jsonify(result), 400

        return jsonify(result), 201
    except ValidationError as e:
        return jsonify({"error": str(e.messages)}), 400

# PUT/PATCH routes


@units_bp.route('/<string:unit_id>', methods=['PUT', 'PATCH'])
@token_required
def update_unit(unit_id):
    """Update a unit"""
    try:
        # First check if user owns the unit
        unit = UnitService.get_unit_by_id(unit_id)
        if not unit:
            return jsonify({"error": "Unit not found"}), 404
        if str(unit.get('owner', {}).get('id')) != str(g.current_user['id']):
            return jsonify({"error": "Unauthorized - not the owner"}), 403

        schema = UnitUpdateSchema()
        data = schema.load(request.json, partial=True)

        result = UnitService.update_unit(
            unit_id=unit_id,
            data=data,
            user_id=int(g.current_user['id'])
        )

        if "error" in result:
            return jsonify(result), 400

        return jsonify(result)
    except ValidationError as e:
        return jsonify({"error": str(e.messages)}), 400

# DELETE route


@units_bp.route('/<string:unit_id>', methods=['DELETE'])
@token_required
def delete_unit(unit_id):
    """Delete a unit"""
    # First check if user owns the unit
    unit = UnitService.get_unit_by_id(unit_id)
    if not unit:
        return jsonify({"error": "Unit not found"}), 404

    if str(unit.get('owner', {}).get('id')) != str(g.current_user['id']):
        return jsonify({"error": "Unauthorized - not the owner"}), 403

    # Check if unit is currently rented
    if unit.get('tenant_id'):
        return jsonify({"error": "Cannot delete unit while it is rented"}), 400

    result = UnitService.delete_unit(
        unit_id=unit_id,
        user_id=int(g.current_user['id'])
    )

    if "error" in result:
        return jsonify(result), 400

    return result  # Return response for successful deletion

# Bulk operations


# @units_bp.route('/bulk/update-rates', methods=['POST'])
# @token_required
# def bulk_update_rates():
#     """Bulk update rates for units in a city"""
#     try:
#         data = request.json
#         if not all(k in data for k in ['city', 'rate_increase']):
#             return jsonify({"error": "Missing required fields"}), 400

#         result = UnitService.bulk_update_rates(
#             city=data['city'],
#             rate_increase=float(data['rate_increase']),
#             user_id=g.current_user['id']
#         )

#         if "error" in result:
#             return jsonify(result), 400

#         return jsonify(result)
#     except ValueError:
#         return jsonify({"error": "Invalid rate increase value"}), 400

# Security features routes


@units_bp.route('/<string:unit_id>/security', methods=['POST'])
@token_required
def add_security_feature(unit_id):
    """Add security features to a unit"""
    try:
        # First check if user owns the unit
        unit = UnitService.get_unit_by_id(unit_id)
        if not unit:
            return jsonify({"error": "Unit not found"}), 404

        if str(unit.get('owner', {}).get('id')) != str(g.current_user['id']):
            return jsonify({"error": "Unauthorized - not the owner"}), 403

        # Validate request data
        data = request.json
        if not data or 'features' not in data:
            return jsonify({"error": "No features specified"}), 400

        if not isinstance(data['features'], list):
            return jsonify({"error": "Features must be a list"}), 400

        if not data['features']:
            return jsonify({"error": "Features list cannot be empty"}), 400

        # Add security features
        result = UnitService.add_security_features(
            unit_id=unit_id,
            features=data['features'],
            user_id=int(g.current_user['id'])
        )

        if "error" in result:
            return jsonify(result), 400

        return jsonify(result), 201  # Created status code
    except ValidationError as e:
        return jsonify({"error": str(e.messages)}), 400
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500


@units_bp.route('/<string:unit_id>/security', methods=['DELETE'])
@token_required
def remove_security_features(unit_id):
    """Remove security features from a unit"""
    try:
        data = request.json
        unit = UnitService.get_unit_by_id(unit_id)
        if not unit:
            return jsonify({"error": "Unit not found"}), 404

        if str(unit.get('owner', {}).get('id')) != str(g.current_user['id']):
            return jsonify({"error": "Unauthorized - not the owner"}), 403
        
        if not data or 'features' not in data:
            return jsonify({"error": "No features specified"}), 400

        if not isinstance(data['features'], list):
            return jsonify({"error": "Features must be a list"}), 400

        if not data['features']:
            return jsonify({"error": "Features list cannot be empty"}), 400

        result = UnitService.remove_security_features(
            unit_id=unit_id,
            features=data['features'],
            user_id=int(g.current_user['id'])
        )

        if "error" in result:
            return jsonify(result), 400

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500
