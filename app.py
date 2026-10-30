"""Flask application for the StudCalc timber engineering prototype."""

import math
import os

from dotenv import load_dotenv
from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import current_user, login_required
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import select, update

from extensions import db, login_manager, migrate
from models import CalculationHistory, SavedProject, User

# Load local environment variables from .env during development.
load_dotenv()

# ---------------------------------------------------------------------
# Application configuration
# ---------------------------------------------------------------------

app = Flask(__name__)

# Never use a hard-coded secret key in a deployed application.
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
if not app.config["SECRET_KEY"]:
    raise RuntimeError(
        "SECRET_KEY is missing. Set it in your local .env file."
    )

# SQLite is the local default. Render can supply a PostgreSQL URL.
database_url = os.getenv(
    "DATABASE_URL",
    "sqlite:///stud_calculator.db",
)

# Support the older PostgreSQL URL prefix used by some providers.
if database_url.startswith("postgres://"):
    database_url = database_url.replace(
        "postgres://", "postgresql://", 1
    )

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Improve session-cookie security.
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = (
    os.getenv("COOKIE_SECURE", "false").lower() == "true"
)

# Protect all POST forms against cross-site request forgery.
csrf = CSRFProtect(app)

# Initialize database, migration, and authentication extensions.
db.init_app(app)
migrate.init_app(app, db)
login_manager.init_app(app)

# Register the authentication blueprint before serving any requests.
from auth import auth  # noqa: E402

app.register_blueprint(auth)


@login_manager.user_loader
def load_user(user_id):
    """Reload the logged-in user from the database session."""
    try:
        return db.session.get(User, int(user_id))
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------
# Calculator configuration
# ---------------------------------------------------------------------

# Prototype load factors. These are not verified code-prescribed loads.
LOAD_FACTORS = {
    "office": {
        "dead_load": 1.2,
        "live_load": 1.6,
        "wind_load": 1.4,
        "seismic_load": 1.5,
        "snow_load": 1.3,
    },
    "garden": {
        "dead_load": 1.3,
        "live_load": 1.5,
        "wind_load": 1.4,
        "seismic_load": 1.5,
        "snow_load": 1.3,
    },
    "residential": {
        "dead_load": 1.4,
        "live_load": 1.7,
        "wind_load": 1.4,
        "seismic_load": 1.5,
        "snow_load": 1.3,
    },
    "building": {
        "dead_load": 1.5,
        "live_load": 1.8,
        "wind_load": 1.5,
        "seismic_load": 1.6,
        "snow_load": 1.4,
    },
}

# Prototype material values. Verify the properties and units before use.
MATERIAL_STRENGTHS = {
    "C-30": 30,
    "C-40": 40,
    "T-35": 35,
    "MCG-15": 15,
}

DEFAULT_FORM_VALUES = {
    "project_id": "",
    "k2data": "1.74",
    "length": "20",
    "depth": "0.5",
    "width": "0.5",
    "k_mode": "0.5",
    "material": "C-30",
    "load_type": "office",
    "options": ["dead_load", "live_load"],
}


def get_form_values(source=None):
    """Collect form inputs or provide defaults for a new calculation."""
    if source is None:
        return DEFAULT_FORM_VALUES.copy()

    # getlist() is needed because multiple load checkboxes can be selected.
    return {
        "project_id": source.get("project_id", ""),
        "k2data": source.get("k2data", "1.74"),
        "length": source.get("length", "20"),
        "depth": source.get("depth", "0.5"),
        "width": source.get("width", "0.5"),
        "k_mode": source.get("k_mode", "0.5"),
        "material": source.get("material", "C-30"),
        "load_type": source.get("load_type", "office"),
        "options": source.getlist("options"),
    }


def render_calculator(
    form_values,
    *,
    phi=None,
    fd=None,
    total_load=None,
    utilization_ratio=None,
    final_report=False,
):
    """Render the calculator with consistent data for every outcome."""
    user_projects = []

    if current_user.is_authenticated:
        user_projects = db.session.scalars(
            select(SavedProject)
            .where(SavedProject.user_id == current_user.id)
            .order_by(SavedProject.name)
        ).all()

    return render_template(
        "index.html",
        form_values=form_values,
        projects=user_projects,
        phi=phi,
        fd=fd,
        total_load=total_load,
        utilization_ratio=utilization_ratio,
        final_report=final_report,
    )


# ---------------------------------------------------------------------
# Main calculator
# ---------------------------------------------------------------------

@app.route("/", methods=["GET", "POST"])
def home():
    """Display the calculator and process submitted calculations."""

    if request.method == "GET":
        # A project load redirects here with saved values in the session.
        saved_values = session.pop("calculator_prefill", None)
        form_values = get_form_values()

        if saved_values:
            form_values.update(saved_values)

        return render_calculator(form_values)

    # Capture form values before validation so the user does not lose them.
    form_values = get_form_values(request.form)

    try:
        # Parse the numeric inputs.
        k2 = float(form_values["k2data"])
        length = float(form_values["length"])
        depth = float(form_values["depth"])
        width = float(form_values["width"])
        k_mode = float(form_values["k_mode"])

        numeric_values = [k2, length, depth, width, k_mode]

        # Reject NaN and infinity, which are not valid design inputs.
        if not all(math.isfinite(value) for value in numeric_values):
            raise ValueError("Please enter valid finite numbers.")

        # Dimensions and calculation factors must be positive.
        if min(length, depth, width, k2, k_mode) <= 0:
            raise ValueError(
                "Length, depth, width, K₂, and K mode must be greater than zero."
            )

        # Validate the selected load category.
        load_type = form_values["load_type"]
        if load_type not in LOAD_FACTORS:
            raise ValueError("Please select a valid load category.")

        # Validate the selected material.
        material = form_values["material"]
        if material not in MATERIAL_STRENGTHS:
            raise ValueError("Please select a valid material.")

        # Validate the load checkboxes.
        selected_loads = form_values["options"]
        allowed_loads = set(LOAD_FACTORS[load_type])

        if (
            not selected_loads
            or len(selected_loads) != len(set(selected_loads))
            or not set(selected_loads).issubset(allowed_loads)
        ):
            raise ValueError("Select at least one valid load.")

        # Retrieve the prototype factors for the selected category.
        factors = LOAD_FACTORS[load_type]
        total_load = sum(factors[name] for name in selected_loads)

        # Retrieve the prototype material properties.
        strength = MATERIAL_STRENGTHS[material]
        E0 = strength - 9
        G0 = strength * 0.5
        gama_factor = 1.5

        # -------------------------------------------------------------
        # Existing prototype calculation formula.
        # This formula and its units still require engineering review.
        # -------------------------------------------------------------
        IZ = (width * depth**3) / 12
        AZ = width * 0.5

        phi = (
            k2
            * AZ
            * math.sqrt(IZ / length)
            * math.sqrt(E0 * IZ / G0)
        )

        fd = k_mode * phi * (strength / gama_factor)

        # Prevent division by zero and reject invalid intermediate results.
        if not math.isfinite(fd) or fd <= 0:
            raise ValueError(
                "The calculated denominator is invalid. Please check the inputs."
            )

        ratio = total_load / fd

        if not math.isfinite(ratio):
            raise ValueError("The calculated ratio is not a finite number.")

        # These messages describe prototype output, not structural certification.
        if ratio <= 1:
            status = "Prototype utilization ratio is at or below 1."
        else:
            status = "Prototype utilization ratio exceeds 1."

        utilization_ratio = (status, ratio)

    except (ValueError, TypeError, OverflowError) as error:
        flash(str(error), "error")
        return render_calculator(form_values)

    # -------------------------------------------------------------
    # Validate the selected project before saving any history.
    # Users may only assign calculations to projects they own.
    # -------------------------------------------------------------
    project = None
    project_id = form_values["project_id"].strip()

    if project_id:
        if not current_user.is_authenticated:
            flash("Please log in before saving to a project.", "error")
            return render_calculator(form_values)

        try:
            project_id = int(project_id)
        except (ValueError, TypeError):
            flash("Invalid project selection.", "error")
            return render_calculator(form_values)

        project = db.session.scalar(
            select(SavedProject).where(
                SavedProject.id == project_id,
                SavedProject.user_id == current_user.id,
            )
        )

        if project is None:
            flash(
                "Project not found or you do not have access to it.",
                "error",
            )
            return render_calculator(form_values)

    # Anonymous visitors can calculate, but their results are not persisted.
    if current_user.is_authenticated:
        # Save the latest input values into the selected project, if any.
        if project:
            project.input_data = {
                "k2data": form_values["k2data"],
                "length": form_values["length"],
                "depth": form_values["depth"],
                "width": form_values["width"],
                "k_mode": form_values["k_mode"],
                "material": material,
                "load_type": load_type,
                "options": selected_loads,
            }

        # Save an immutable snapshot of this calculation in the history.
        history = CalculationHistory(
            user_id=current_user.id,
            project_id=project.id if project else None,
            inputs={
                "k2data": k2,
                "length": length,
                "depth": depth,
                "width": width,
                "k_mode": k_mode,
                "material": material,
                "load_type": load_type,
                "options": selected_loads,
            },
            results={
                "phi": phi,
                "fd": fd,
                "total_load": total_load,
                "status": status,
                "utilization_ratio": ratio,
            },
        )

        try:
            db.session.add(history)
            db.session.commit()

            if project:
                flash(
                    f"Calculation saved to project: {project.name}",
                    "success",
                )
            else:
                flash("Calculation added to your history.", "success")

        except Exception:
            db.session.rollback()
            app.logger.exception("Could not save calculation history.")
            flash(
                "The calculation completed, but saving the record failed.",
                "warning",
            )

    # Keep the submitted values visible after calculating.
    return render_calculator(
        form_values,
        phi=phi,
        fd=fd,
        total_load=total_load,
        utilization_ratio=utilization_ratio,
        final_report=True,
    )


# ---------------------------------------------------------------------
# Calculation history
# ---------------------------------------------------------------------

@app.route("/history")
@login_required
def calculation_history():
    """Show the latest 100 calculations belonging to the current user."""
    history_records = db.session.scalars(
        select(CalculationHistory)
        .where(CalculationHistory.user_id == current_user.id)
        .order_by(CalculationHistory.created_at.desc())
        .limit(100)
    ).all()

    return render_template(
        "history.html",
        history_records=history_records,
    )


# ---------------------------------------------------------------------
# Saved project management
# ---------------------------------------------------------------------

@app.route("/projects", methods=["GET", "POST"])
@login_required
def projects():
    """Create projects and display the current user's saved projects."""
    if request.method == "POST":
        name = request.form.get("name", "").strip()

        if not name or len(name) > 150:
            flash(
                "Project name must be between 1 and 150 characters.",
                "error",
            )
            return redirect(url_for("projects"))

        project = SavedProject(
            user_id=current_user.id,
            name=name,
            input_data={},
        )

        try:
            db.session.add(project)
            db.session.commit()
            flash("Project created successfully.", "success")
        except Exception:
            db.session.rollback()
            app.logger.exception("Could not create project.")
            flash("Could not create the project.", "error")

        return redirect(url_for("projects"))

    user_projects = db.session.scalars(
        select(SavedProject)
        .where(SavedProject.user_id == current_user.id)
        .order_by(SavedProject.updated_at.desc())
    ).all()

    return render_template("projects.html", projects=user_projects)


@app.route("/projects/<int:project_id>/rename", methods=["POST"])
@login_required
def rename_project(project_id):
    """Rename a project only if it belongs to the current user."""
    project = db.session.scalar(
        select(SavedProject).where(
            SavedProject.id == project_id,
            SavedProject.user_id == current_user.id,
        )
    )

    if project is None:
        flash("Project not found.", "error")
        return redirect(url_for("projects"))

    name = request.form.get("name", "").strip()

    if not name or len(name) > 150:
        flash(
            "Project name must be between 1 and 150 characters.",
            "error",
        )
        return redirect(url_for("projects"))

    project.name = name

    try:
        db.session.commit()
        flash("Project renamed successfully.", "success")
    except Exception:
        db.session.rollback()
        app.logger.exception("Could not rename project.")
        flash("Could not rename the project.", "error")

    return redirect(url_for("projects"))


@app.route("/projects/<int:project_id>/delete", methods=["POST"])
@login_required
def delete_project(project_id):
    """Delete an owned project while retaining its calculation history."""
    project = db.session.scalar(
        select(SavedProject).where(
            SavedProject.id == project_id,
            SavedProject.user_id == current_user.id,
        )
    )

    if project is None:
        flash("Project not found.", "error")
        return redirect(url_for("projects"))

    try:
        # Keep history records and unlink them before deleting the project.
        db.session.execute(
            update(CalculationHistory)
            .where(
                CalculationHistory.project_id == project.id,
                CalculationHistory.user_id == current_user.id,
            )
            .values(project_id=None)
        )

        db.session.delete(project)
        db.session.commit()
        flash("Project deleted. Its calculation history was retained.", "success")

    except Exception:
        db.session.rollback()
        app.logger.exception("Could not delete project.")
        flash("Could not delete the project.", "error")

    return redirect(url_for("projects"))


@app.route("/projects/<int:project_id>/load", methods=["POST"])
@login_required
def load_project(project_id):
    """Load an owned project's saved inputs into the calculator form."""
    project = db.session.scalar(
        select(SavedProject).where(
            SavedProject.id == project_id,
            SavedProject.user_id == current_user.id,
        )
    )

    if project is None:
        flash("Project not found.", "error")
        return redirect(url_for("projects"))

    if not project.input_data:
        flash(
            "This project has no saved calculator inputs yet. "
            "Select it on the calculator and run a calculation first.",
            "error",
        )
        return redirect(url_for("projects"))

    # The session holds these values for the next GET request to the calculator.
    session["calculator_prefill"] = {
        **project.input_data,
        "project_id": str(project.id),
    }

    flash(
        f"Loaded inputs from '{project.name}'. Review them before calculating.",
        "success",
    )
    return redirect(url_for("home"))


# ---------------------------------------------------------------------
# Development entry point
# ---------------------------------------------------------------------

if __name__ == "__main__":
    # Debug mode is for local development only, not public production hosting.
    app.run(debug=True)
    