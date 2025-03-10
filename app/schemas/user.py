from marshmallow import Schema, fields, validate, EXCLUDE


class UserBaseSchema(Schema):
    """Base schema for user data"""
    class Meta:
        unknown = EXCLUDE

    name = fields.Str(validate=validate.Length(min=2, max=50))
    surname = fields.Str(validate=validate.Length(min=2, max=50))
    email = fields.Email()


class UserSchema(UserBaseSchema):
    """Schema for user creation/updates"""
    id = fields.Int(dump_only=True)  # Read only field
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class UserUpdateSchema(UserBaseSchema):
    """Schema for user profile updates"""
    current_password = fields.Str(load_only=True)  # write-only field
    new_password = fields.Str(load_only=True,
                              validate=validate.Length(min=6),
                              error_messages={
                                  "validator_failed": "New password must be at least 6 characters long"})
    
class UserResponseSchema(UserBaseSchema):
    """Schema for user responses - excludes sensitive data"""
    id = fields.Int()
    created_date = fields.DateTime()
    updated_date = fields.DateTime()
