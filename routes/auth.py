"""
Authentication routes for The Oracle application.
"""
from flask import Blueprint, request, render_template, redirect, url_for, session, flash
from models.user import User

auth_bp = Blueprint('auth', __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.authenticate(username, password)
        if user:
            session["username"] = user.username
            return redirect(url_for("readings.index"))
        else:
            flash("Invalid credentials.", "error")
            return render_template("login.html")
    return render_template("login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        confirm_password = request.form.get("confirm_password")

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template("register.html")

        user = User.create(username, password)
        if user:
            flash("Account created successfully! Please log in.", "success")
            return redirect(url_for("auth.login"))
        else:
            flash("Username already exists.", "error")
            return render_template("register.html")
    return render_template("register.html")


@auth_bp.route("/profile", methods=["GET", "POST"])
def profile():
    if "username" not in session:
        return redirect(url_for("auth.login"))

    user = User.get_by_username(session["username"])
    if not user:
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        birthdate = request.form["birthdate"]
        about_me = request.form["about_me"]
        birth_time = request.form.get("birth_time", "")
        birth_latitude = request.form.get("birth_latitude", "")
        birth_longitude = request.form.get("birth_longitude", "")
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        confirm_new_password = request.form.get("confirm_new_password")

        # Handle password change
        if current_password and new_password:
            if new_password != confirm_new_password:
                flash("New passwords do not match.", "error")
                return render_template("profile.html",
                                     username=user.username,
                                     user_birthdate=user.birthdate,
                                     user_about_me=user.about_me,
                                     user_birth_time=user.birth_time,
                                     user_birth_latitude=user.birth_latitude,
                                     user_birth_longitude=user.birth_longitude)

            if not user.change_password(current_password, new_password):
                flash("Current password is incorrect.", "error")
                return render_template("profile.html",
                                     username=user.username,
                                     user_birthdate=user.birthdate,
                                     user_about_me=user.about_me,
                                     user_birth_time=user.birth_time,
                                     user_birth_latitude=user.birth_latitude,
                                     user_birth_longitude=user.birth_longitude)

        if user.update_profile(birthdate=birthdate, about_me=about_me,
                              birth_time=birth_time, birth_latitude=birth_latitude, birth_longitude=birth_longitude):
            flash("Profile updated successfully!", "success")
            return redirect(url_for("auth.profile"))
        else:
            flash("Failed to update profile.", "error")

    return render_template("profile.html",
                         username=user.username,
                         user_birthdate=user.birthdate,
                         user_about_me=user.about_me,
                         user_birth_time=user.birth_time,
                         user_birth_latitude=user.birth_latitude,
                         user_birth_longitude=user.birth_longitude)


@auth_bp.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("auth.login"))
