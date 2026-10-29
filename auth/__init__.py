
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user
from sqlalchemy import select
from werkzeug.security import check_password_hash

from extensions import db
from models import User

auth = Blueprint("auth", __name__, url_prefix="/auth")


@auth.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not email or len(email) > 255 or "@" not in email:
            flash("Enter a valid email address.", "error")
            return render_template("auth/register.html")

        if len(password) < 12:
            flash("Use a password with at least 12 characters.", "error")
            return render_template("auth/register.html")

        if password != confirm_password:
            flash("The passwords do not match.", "error")
            return render_template("auth/register.html")

        existing_user = db.session.scalar(
            select(User).where(User.email == email)
        )

        if existing_user:
            flash("An account with that email already exists.", "error")
            return render_template("auth/register.html")

        user = User(email=email, role="user")
        user.set_password(password)

        try:
            db.session.add(user)
            db.session.commit()
        except Exception:
            db.session.rollback()
            app_logger = __import__("logging").getLogger(__name__)
            app_logger.exception("Registration failed")
            flash("We could not create your account. Please try again.", "error")
            return render_template("auth/register.html")

        login_user(user)
        flash("Your account was created successfully.", "success")
        return redirect(url_for("home"))

    return render_template("auth/register.html")


@auth.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = db.session.scalar(
            select(User).where(User.email == email)
        )

        if user and user.check_password(password):
            login_user(user)
            flash("Welcome back.", "success")
            return redirect(url_for("home"))

        flash("Invalid email or password.", "error")

    return render_template("auth/login.html")


@auth.route("/logout", methods=["POST"])
def logout():
    if current_user.is_authenticated:
        logout_user()
        flash("You have been logged out.", "success")

    return redirect(url_for("auth.login"))
