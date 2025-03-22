from marshmallow import Schema, ValidationError, fields, validate, EXCLUDE, validates_schema
from datetime import datetime

from app.schemas.unit import UnitResponseSchema
from app.schemas.user import UserResponseSchema


class RentalBaseSchema(Schema):
    """Base schema for rental data"""
    class Meta:
        unknown = EXCLUDE

    start_date = fields.Date(required=True)  # Changed to Date field
    end_date = fields.Date(required=True)    # Changed to Date field
    rental_fee = fields.Float(validate=validate.Range(min=0))
    deposit_amount = fields.Float(validate=validate.Range(min=0))

    @validates_schema
    def validate_dates(self, data, **kwargs):
        try:
            if data["start_date"] >= data["end_date"]:
                raise ValidationError("End date must be after start date")
            if data['start_date'] < datetime.now().date():
                raise ValidationError('Start date cannot be in the past')
        except:
            pass


class RentalCreateSchema(RentalBaseSchema):
    """Schema for creating a rental"""
    unit_id = fields.Str(required=True)
    tenant_id = fields.Int(dump_only=True)
    monthly_rate = fields.Float(required=True, validate=validate.Range(min=0))


class RentalUpdateSchema(RentalBaseSchema):
    """Schema for rental updates"""
    status = fields.Str(validate=validate.OneOf(
        ["active", "terminated", "expired"]))


class RentalResponseSchema(RentalBaseSchema):
    """Schema for rental responses"""
    id = fields.Int(dump_only=True)
    unit = fields.Nested(UnitResponseSchema, dump_only=True)
    tenant = fields.Nested(UserResponseSchema, dump_only=True)
    status = fields.Str()
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
