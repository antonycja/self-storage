from marshmallow import Schema, ValidationError

# Import all schemas for easy access
from .user import UserSchema, UserUpdateSchema, UserResponseSchema
from .unit import UnitBaseSchema, UnitCreateSchema, UnitUpdateSchema, UnitResponseSchema
from .auth import LoginSchema, SignupSchema


