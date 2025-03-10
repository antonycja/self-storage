from marshmallow import Schema, fields, validate, EXCLUDE
from app.models.unit import UnitStatus


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
