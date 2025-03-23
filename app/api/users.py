from flask import Blueprint, request, jsonify, g
import bcrypt
from app.models.base import db
from app.models.unit import UnitModel
from app.models.user import UserModel
from app.models.rental import RentalModel
from app.api.auth import token_required

users_bp = Blueprint('users', __name__)


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    # Generate a salt and hash the password
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(stored_password: str, provided_password: str) -> bool:
    """Verify a password against its hash using bcrypt"""
    return bcrypt.checkpw(
        provided_password.encode('utf-8'),
        stored_password.encode('utf-8')
    )


@users_bp.route('/', methods=['GET'])
@token_required
def get_users():
    """Get all users"""
    users = db.session.execute(
        db.select(UserModel)
    ).scalars().all()

    return jsonify([{
        'id': user.id,
        'name': user.name,
        'surname': user.surname,
        'email': user.email
    } for user in users])


@users_bp.route('/<int:user_id>', methods=['GET'])
@token_required
def get_user(user_id):
    """Get a specific user"""
    user = db.session.get(UserModel, user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404

    return jsonify({
        'id': user.id,
        'name': user.name,
        'surname': user.surname,
        'email': user.email
    })


@users_bp.route('/', methods=['POST'])
def create_user():
    """Create a new user"""
    data = request.get_json()

    if not data or not all(k in data for k in ('name', 'surname', 'email', 'password')):
        return jsonify({'message': 'Missing required fields'}), 400

    # Check if user already exists
    existing_user = db.session.execute(
        db.select(UserModel).filter_by(email=data['email'])
    ).scalar_one_or_none()

    if existing_user:
        return jsonify({'message': 'User already exists'}), 409

    new_user = UserModel(
        name=data['name'].strip().capitalize(),
        surname=data['surname'].strip().capitalize(),
        email=data['email'].strip().lower(),
        password=hash_password(data['password'])  # Using bcrypt
    )

    db.session.add(new_user)
    db.session.commit()

    return jsonify({
        'id': new_user.id,
        'name': new_user.name,
        'surname': new_user.surname,
        'email': new_user.email
    }), 201


@users_bp.route('/<int:user_id>', methods=['PUT'])
@token_required
def update_user(user_id):
    """Update a user"""
    user = db.session.get(UserModel, user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'message': 'No input data provided'}), 400

    # Update user fields
    if 'name' in data:
        user.name = data['name'].strip().capitalize()
    if 'surname' in data:
        user.surname = data['surname'].strip().capitalize()
    if 'password' in data:
        # Verify old password if provided
        if 'old_password' not in data:
            return jsonify({'message': 'Old password is required'}), 400

        if not verify_password(user.password, data['old_password']):
            return jsonify({'message': 'Invalid old password'}), 401

        user.password = hash_password(data['password'])  # Using bcrypt

    db.session.commit()

    return jsonify({
        'id': user.id,
        'name': user.name,
        'surname': user.surname,
        'email': user.email
    })


@users_bp.route('/<int:user_id>', methods=['DELETE'])
@token_required
def delete_user(user_id):
    """Delete a user"""
    # Check if the authenticated user is trying to delete their own profile
    if str(user_id) != str(g.current_user['id']):
        return jsonify({'message': 'Unauthorized. Can only delete your own profile'}), 403

    user = db.session.get(UserModel, user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404

    # Check for active rentals where user is tenant
    active_rentals = db.session.execute(
        db.select(RentalModel)
        .filter(
            RentalModel.tenant_id == user_id,
            RentalModel.status == 'active'
        )
    ).scalar_one_or_none()

    # Check for active rentals where user is unit owner
    owned_units_with_rentals = db.session.execute(
        db.select(UnitModel)
        .join(RentalModel)
        .filter(
            UnitModel.user_id == user_id,
            RentalModel.status == 'active'
        )
    ).scalar_one_or_none()
    print(active_rentals, owned_units_with_rentals)
    if active_rentals or owned_units_with_rentals:
        return jsonify({
            'message': 'Cannot delete profile with active rentals. Please terminate all rentals first.'
        }), 400

    try:
        db.session.delete(user)
        db.session.commit()
        return jsonify({'message': 'User profile deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Failed to delete user: {str(e)}'}), 500
