from flask import Blueprint, request, jsonify, g
from app.services.rental_service import RentalService
from app.api.auth import token_required
from app.schemas.rental import RentalCreateSchema, RentalUpdateSchema, RentalResponseSchema
from marshmallow import ValidationError
from datetime import datetime, timedelta

rentals_bp = Blueprint('rentals', __name__)

# GET routes


@rentals_bp.route('/', methods=['GET'])
@token_required
def get_rentals():
    """Get all rentals for the current user"""
    rentals = RentalService.get_user_rentals(g.current_user['id'])
    return jsonify(rentals)


@rentals_bp.route('/<int:rental_id>', methods=['GET'])
@token_required
def get_rental(rental_id):
    """Get a specific rental by ID"""
    rental = RentalService.get_rental_by_id(rental_id, g.current_user['id'])
    if not rental:
        return jsonify({"error": "Rental not found"}), 404
    return jsonify(rental)


@rentals_bp.route('/statistics', methods=['GET'])
@token_required
def get_statistics():
    """Get rental statistics for the current user"""
    stats = RentalService.get_rental_statistics(g.current_user['id'])
    return jsonify(stats)

# POST routes


@rentals_bp.route('/', methods=['POST'])
@token_required
def create_rental():
    """Create a new rental agreement"""
    try:
        schema = RentalCreateSchema()
        data = schema.load(request.json)

        # Add tenant ID from token
        data['tenant_id'] = g.current_user['id']

        result = RentalService.create_rental(data)
        if "error" in result:
            return jsonify(result), 400

        return jsonify(result), 201
    except ValidationError as e:
        return jsonify({"error": str(e.messages)}), 400

# PUT/PATCH routes


@rentals_bp.route('/<int:rental_id>', methods=['PATCH'])
@token_required
def update_rental(rental_id):
    """Update a rental agreement"""
    try:
        schema = RentalUpdateSchema()
        data = schema.load(request.json, partial=True)

        result = RentalService.update_rental(
            rental_id=rental_id,
            data=data,
            user_id=g.current_user['id']
        )

        if "error" in result:
            return jsonify(result), 400

        return jsonify(result)
    except ValidationError as e:
        return jsonify({"error": str(e.messages)}), 400


@rentals_bp.route('/<int:rental_id>/terminate', methods=['POST'])
@token_required
def terminate_rental(rental_id):
    """Terminate a rental agreement"""
    result = RentalService.terminate_rental(
        rental_id=rental_id,
        user_id=g.current_user['id']
    )

    if "error" in result:
        return jsonify(result), 400

    return jsonify(result)


@rentals_bp.route('/extend/<int:rental_id>', methods=['POST'])
@token_required
def extend_rental(rental_id):
    """Extend an existing rental agreement"""
    try:
        if 'extension_days' not in request.json:
            return jsonify({"error": "extension_days is required"}), 400

        extension_days = int(request.json['extension_days'])
        if extension_days <= 0:
            return jsonify({"error": "Extension days must be positive"}), 400

        # Get current rental to calculate new end date
        current_rental = RentalService.get_rental_by_id(
            rental_id, g.current_user['id'])
        if not current_rental:
            return jsonify({"error": "Rental not found"}), 404

        # Calculate new end date
        current_end_date = datetime.fromisoformat(current_rental['end_date'])

        # Prepare update data
        update_data = {
            'end_date': current_end_date + timedelta(days=extension_days)
        }

        # Use existing update mechanism
        result = RentalService.update_rental(
            rental_id=rental_id,
            data=update_data,
            user_id=g.current_user['id']
        )

        if "error" in result:
            return jsonify(result), 400

        return jsonify(result)
    except ValueError:
        return jsonify({"error": "Invalid extension days value"}), 400


@rentals_bp.route('/upcoming-expiration', methods=['GET'])
@token_required
def get_upcoming_expirations():
    """Get rentals expiring in the next 30 days"""
    rentals = RentalService.get_upcoming_expirations(g.current_user['id'])
    return jsonify(rentals)


@rentals_bp.route('/history/<string:unit_id>', methods=['GET'])
@token_required
def get_rental_history(unit_id):
    """Get rental history for a specific unit"""
    history = RentalService.get_rental_history(
        unit_id=unit_id,
        user_id=g.current_user['id']
    )
    return jsonify(history)


@rentals_bp.route('/<int:rental_id>/share', methods=['POST'])
@token_required
def share_rental(rental_id):
    """Share rental with other users"""
    try:
        if not request.json or 'email' not in request.json:
            return jsonify({"error": "Email is required"}), 400

        result = RentalService.share_rental(
            rental_id=rental_id,
            email=request.json['email'],
            user_id=g.current_user['id']
        )

        if "error" in result:
            return jsonify(result), 400

        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@rentals_bp.route('/<int:rental_id>/unshare', methods=['POST'])
@token_required
def unshare_rental(rental_id):
    """Remove shared access for a user"""
    try:
        if not request.json or 'email' not in request.json:
            return jsonify({"error": "Email is required"}), 400

        result = RentalService.unshare_rental(
            rental_id=rental_id,
            email=request.json['email'],
            user_id=g.current_user['id']
        )

        if "error" in result:
            return jsonify(result), 400

        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 400
