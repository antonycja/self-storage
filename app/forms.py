from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional, ValidationError


class LoginForm(FlaskForm):
    email = StringField(label="Email", validators=[
        DataRequired(message="Email is required."),
        Email(message="Enter valid email.")
    ])
    password = PasswordField(label="Password", validators=[
        DataRequired(message="Password is required"),
        Length(min=6, message="Password must be at least 6 characters long.")
    ])
    submit = SubmitField(label="Login")


class SignUpForm(FlaskForm):
    name = StringField(label="Name", validators=[
                       DataRequired(message="Name is required.")])
    surname = StringField(label="Surname", validators=[
                          DataRequired(message="Surname is required.")])
    email = StringField(label="Email", validators=[
        DataRequired(message="Email is required."),
        Email(message="Enter valid email.")
    ])
    password = PasswordField(label="Password", validators=[DataRequired(message="Password is required."), Length(
        min=6, message="Password must be at least 6 characters long."), EqualTo("confirm", message="Passwords must match")])
    confirm = PasswordField(label="Repeat Password")
    submit = SubmitField(label="Sign Up")


class EditProfileForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    surname = StringField('Surname', validators=[DataRequired()])
    old_password = PasswordField("Old Password", validators=[Optional()])
    new_password = PasswordField('New Password', validators=[Optional(), Length(min=6)])
    confirm_new_password = PasswordField('Confirm New Password', validators=[Optional(), EqualTo('new_password', message='Passwords must match')])
    submit = SubmitField('Update Profile')

    # def __init__(self, user, *args, **kwargs):
    #     super(EditProfileForm, self).__init__(*args, **kwargs)
    #     self.name.data = user.name
    #     self.surname.data = user.surname

    def validate_old_password(self, field):
        """Ensure old password is required if changing the password"""
        if self.new_password.data and not field.data:
            raise ValidationError("Old password is required to set a new password.")
