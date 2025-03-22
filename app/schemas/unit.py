from marshmallow import Schema, fields, validate, EXCLUDE, pre_load
from app.models.enums import UnitStatus
from app.schemas.user import UserResponseSchema


class UnitBaseSchema(Schema):
    """Base Schema for unit data"""
    class Meta:
        unknown = EXCLUDE
    unit_name = fields.Str(required=True)
    country = fields.Str(required=True)
    city = fields.Str(required=True)
    address_link = fields.Str(required=True)
    size_sqm = fields.Float(
        required=True,
        validate=validate.Range(min=0),
        error_messages={"validator_failed": "Size must be greater than 0"})

    monthly_rate = fields.Float(
        required=True,
        validate=validate.Range(min=0),
        error_messages={
            "validator_failed": "Monthly rate must be greater than 0"})
    currency = fields.Str(load_default="ZAR")
    climate_controlled = fields.Boolean(load_default=False)
    floor_level = fields.Str(required=True)
    rental_duration_days = fields.Int(
        required=True,
        validate=validate.Range(min=1),
        error_messages={
            "validator_failed": "Rental duration must be at least 1 day"})

    security_features = fields.List(fields.Str())


class UnitCreateSchema(UnitBaseSchema):
    """Schema for unit creation"""
    @pre_load
    def process_status(self, data, **kwargs):
        """Convert status to uppercase before validation"""
        if 'status' in data and isinstance(data['status'], str):
            data['status'] = data['status'].upper()
        return data

    status = fields.String(
        required=True,
        validate=validate.OneOf(
            choices=[status.name for status in UnitStatus]
        )
    )
    user_id = fields.Int(dump_only=True)


class UnitUpdateSchema(UnitBaseSchema):
    """Schema for unit updates"""
    status = fields.Enum(UnitStatus, by_value=True)
    tenant_id = fields.Int(allow_none=True)
    shared_user_emails = fields.List(fields.Email(), load_default=list)
    user_id = fields.Int()


class UnitResponseSchema(UnitBaseSchema):
    """Schema for unit responses"""
    unit_id = fields.Str(dump_only=True)
    status = fields.Enum(UnitStatus, by_value=True)
    owner = fields.Nested(UserResponseSchema, dump_only=True)
    tenant = fields.Nested(UserResponseSchema, dump_only=True, allow_none=True)
    shared_user_email = fields.List(fields.Email(), dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
