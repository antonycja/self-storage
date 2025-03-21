from marshmallow import Schema, fields, validate, EXCLUDE
from app.models.enums import UnitStatus
from app.schemas.user import UserResponseSchema


class UnitBaseSchema(Schema):
    """Base Schema for unit data"""
    class Meta:
        unknown = EXCLUDE

    size_sqm = fields.Float(
        validate=validate.Range(min=0),
        error_messages={"validator_failed": "Size must be greater than 0"})

    monthly_rate = fields.Float(
        validate=validate.Range(min=0),
        error_messages={
            "validator_failed": "Monthly rate must be greater than 0"})

    climate_controlled = fields.Str(
        validate=validate.OneOf(['yes', 'no']),
        error_messages={
            "validator_failed": "Climate control must be 'yes' or 'no'"})

    floor_level = fields.Str()

    security_features = fields.List(fields.Str())
    rental_duration_days = fields.Int(
        validate=validate.Range(min=1),
        error_messages={
            "validator_failed": "Rental duration must be at least 1 day"})
    
    
class UnitCreateSchema(UnitBaseSchema):
    """Schema for unit creation"""
    status = fields.Enum(UnitStatus, by_value=True, required=True)
    
class UnitUpdateSchema(UnitBaseSchema):
    """Schema for unit updates"""
    status = fields.Enum(UnitStatus, by_value=True)
    tenant_id = fields.Int(allow_none=True)
    shared_user_emails = fields.List(fields.Email())
    
class UnitResponseSchema(UnitBaseSchema):
    """Schema for unit responses"""
    unit_id = fields.Int()
    status = fields.Enum(UnitStatus, by_value=True)
    owner = fields.Nested(UserResponseSchema, dump_only=True)
    tenant = fields.Nested(UserResponseSchema, dump_only=True, allow_none=True)
    shared_user_email = fields.List(fields.Email(), dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)