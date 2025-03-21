from flask import Blueprint, request, jsonify, g
from app.services.auth_service import AuthService
from app.services.token_service import TokenService
import jwt
from functools import wraps
from datetime import datetime

auth_bp = Blueprint('auth', __name__)


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing'}), 401

        try:
            if token.startswith('Bearer '):
                token = token[7:]

            # Check if token is blacklisted
            if TokenService.is_blacklisted(token):
                return jsonify({'message': 'Token has been revoked'})

            data = jwt.decode(
                token,
                AuthService.SECRET_KEY,
                algorithms=[AuthService.ALGORITHM]
            )
            current_user = AuthService.get_user_by_email(data['email'])
            if not current_user:
                return jsonify({'message': 'User not found'}), 401

            g.current_user = current_user  # Store user in global context
            g.current_token = token  # Store token in global context

        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token'}), 401

        return f(*args, **kwargs)
    return decorated


@auth_bp.route('/login', methods=['POST'])
def login():
    auth = request.get_json()

    if not auth or not auth.get('email') or not auth.get('password'):
        return jsonify({'message': 'Missing email or password'}), 401

    email = auth.get('email').strip().lower()
    password = auth.get('password')

    user = AuthService.get_user_by_email(email)

    if not user:
        return jsonify({'message': 'User not found'}), 401

    if AuthService.verify_password(user['password'], password):
        token = AuthService.generate_token(email)

        # Remove password from response
        del user['password']

        return jsonify({
            'token': token,
            'user': user
        })

    return jsonify({'message': 'Invalid credentials'}), 401


@auth_bp.route('/protected', methods=['GET'])
@token_required
def protected():
    # Example protected route
    return jsonify({'message': 'This is a protected route'})


@auth_bp.route('/logout', methods=['POST'])
@token_required
def logout():
    """Invalidate the current token"""
    token = g.current_token
    data = jwt.decode(
        token,
        AuthService.SECRET_KEY,
        algorithms=[AuthService.ALGORITHM]
    )

    TokenService.blacklist_token(
        token=token, expires_at=datetime.fromtimestamp(data['exp']))

    return jsonify({'message': 'Successfully logged out',
                    'user': g.current_user['email']})
