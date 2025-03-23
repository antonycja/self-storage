from marshmallow import Schema, fields, validate, validates_schema, ValidationError


class LoginSchema(Schema):
    """Schema for login requests"""
    email = fields.Email(required=True, error_messages={
                         "required": "Email is required"})
    password = fields.Str(required=True, error_messages={
                          "required": "Password is required"})


class SignupSchema(Schema):
    """Schema for signup requests"""
    name = fields.Str(required=True, validate=validate.Length(min=2, max=50), error_messages={"required": "Name is required",
                                                                                              "validator_failed": "Name must be between 2 and 50 characters"})
    surname = fields.Str(required=True, validate=validate.Length(min=2, max=50), error_messages={"required": "Surname is required",
                                                                                                 "validator_failed": "Surname must be between 2 and 50 characters"})
    email = fields.Email(required=True, error_messages={
                         "required": "Email is required"})
    password = fields.Str(required=True, validate=validate.Length(
        min=6), error_messages={"required": "Password is required", "validator_failed": "Password must be at least 6 characters long"})
