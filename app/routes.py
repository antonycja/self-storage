from flask import render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from app.forms import LoginForm, SignUpForm, EditProfileForm
from app.services.user_services import UserService
from datetime import timedelta
from app.models import AuthUser

session_timeout = 1


def register_routes(app):
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'  # Specify where to redirect for login

    # Configure session lifetime
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(
        hours=1)  # Or your session_timeout value
    app.config['SESSION_PERMANENT'] = True

    @login_manager.user_loader
    def load_user(user_id):
        user_dict = UserService.get_user_by_id(user_id)
        if user_dict:
            return AuthUser(user_dict)
        return None

    @app.route("/")
    def home():
        return render_template("home.html")

    @app.route("/login", methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))

        login_form = LoginForm()

        if login_form.validate_on_submit():
            email = login_form.email.data.strip().lower()
            password = login_form.password.data

            user_dict = UserService.get_user_by_email(email)
            if "error" in user_dict.keys():
                flash(user_dict.get('error'), "danger")

            elif user_dict and UserService.verify_password(user_dict['password_hash'], password):
                user = AuthUser(user_dict)
                login_user(user, remember=True)
                return redirect(url_for("dashboard"))

            flash("Invalid username/password", "danger")

        return render_template("login.html", form=login_form)

    @app.route("/signup", methods=['GET', 'POST'])
    def signup():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))

        signup_form = SignUpForm()

        if signup_form.validate_on_submit():
            name = signup_form.name.data.strip().capitalize()
            surname = signup_form.surname.data.strip().capitalize()
            email = signup_form.email.data.strip().lower()
            password = signup_form.password.data.strip()

            response = UserService.create_user(name, surname, email, password)

            if "error" not in response.keys():
                user_dict = UserService.get_user_by_email(email)
                user = AuthUser(user_dict)
                login_user(user, remember=True)
                return redirect(url_for("dashboard"))
            else:
                flash(response['error'], 'danger')

        return render_template("signup.html", form=signup_form)

    @app.route("/dashboard")
    @login_required
    def dashboard():
        client_user = UserService.sanitize_user_data(current_user.__dict__)
        return render_template("dashboard.html", user=client_user)

    @app.route("/logout", methods=['POST'])
    @login_required
    def logout():
        logout_user()
        return redirect(url_for("login"))

    @app.route("/edit-profile", methods=['GET', 'POST'])
    @login_required
    def edit_profile():
        edit_form = EditProfileForm()
        client_user = UserService.sanitize_user_data(current_user.__dict__)

        if request.method == 'GET':
            edit_form.name.data = current_user.name
            edit_form.surname.data = current_user.surname

        name = edit_form.name.data
        surname = edit_form.surname.data
        if edit_form.new_password.data:
            # get old password hash from db
            old_password = UserService.get_user_by_email(
                client_user.get("email")).get("password_hash")
            new_password = edit_form.new_password.data
        if edit_form.validate_on_submit():
            if edit_form.new_password.data:
                response = UserService.update_user(
                    client_user['id'], old_password=old_password, new_password=new_password, name=name, surname=surname)
            else:
                response = UserService.update_user(
                    client_user['id'], name=name, surname=surname)

            if "error" not in response.keys():
                current_user.name = name
                current_user.surname = surname
                flash("Profile updated successfully!", "success")

            else:
                flash(response.get('error'), "danger")

            return redirect(url_for("edit_profile"))

        return render_template("edit_profile.html", form=edit_form, user=client_user)
        pass

    @app.route("/delete-profile", methods=['POST'])
    @login_required
    def delete_profile():
        client_user = UserService.sanitize_user_data(current_user.__dict__)
        id = UserService.get_user_by_email(client_user["email"]).get("id")
        response = UserService.delete_user(id)
        
        if response.get("error"):
            flash(response["error"], "danger")
        else:
            flash(response["success"], "success")
            logout_user()
        return redirect(url_for("home"))
        pass
