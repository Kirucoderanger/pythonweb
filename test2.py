
import os
import math
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import current_user
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from extensions import db, migrate, login_manager
from flask_wtf.csrf import CSRFProtect

from flask import flash, redirect, url_for
from flask_login import login_required
from sqlalchemy import select

from extensions import db
from models import User, SavedProject, CalculationHistory

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
if not app.config["SECRET_KEY"]:
    raise RuntimeError(
        "SECRET_KEY is missing. Set it in your local .env file."
    )
    
csrf = CSRFProtect(app)

app.config["DATABASE_URL"] = os.getenv("DATABASE_URL",
    "sqlite:///stud_calculator.db",)
if not app.config["DATABASE_URL"]:
    raise RuntimeError(
        "DATABASE_URL is missing. Set it in your local .env file."
    )
    
# Normalize older Render PostgreSQL URLs if necessary.
if app.config["DATABASE_URL"].startswith("postgres://"):
    app.config["DATABASE_URL"] = app.config["DATABASE_URL"].replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = app.config["DATABASE_URL"]
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = (
    os.environ.get("COOKIE_SECURE", "false").lower() == "true"
)

db.init_app(app)
migrate.init_app(app, db)
login_manager.init_app(app)


from models import User, SavedProject, CalculationHistory

@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.get(User, int(user_id))
    except (ValueError, TypeError):
        return None

# Register the authentication blueprint during application setup.
from auth import auth
app.register_blueprint(auth)

k2data = {
        "pinpin": 1.74,
        "fixedfixed": 0.41
    }

"""    
@app.route("/", methods=["GET", "POST"])
def home():
    
    #from auth import auth
    #app.register_blueprint(auth)
    
    
    k2 = float(request.form.get("k2data", "1.74"))
    length = float(request.form.get("length", "20"))
    
    depth = float(request.form.get("depth", "0.5"))
    width = float(request.form.get("width", "0.5"))
    IZ = (width * depth**3) / 12
    AZ = width * 0.5
    E0 = 20
    G0 = 10
    strength = 30 
    k_mode = float(request.form.get("k_mode", 0.5))
    #partial material properties based on user selection
    gama_factor = 1.5
    dead_load = 1.2
    live_load = 1.6
    wind_load = 1.4
    seismic_load = 1.5
    snow_load = 1.3
    
    #report the utilization ratio based on the selected load types and material properties
    final_report = False
     
    
    
    if request.method == "POST":
            try:
                # Get the selected load types from the form
                selected_load_type = request.form.getlist("load_type")
                if selected_load_type == "office":
                    dead_load = 1.2
                    live_load = 1.6
                if selected_load_type == "garden":
                    dead_load = 1.3
                    live_load = 1.5
                if selected_load_type == "residential":
                    dead_load = 1.4
                    live_load = 1.7
                    wind_load = 1.4
                    seismic_load = 1.5
                    snow_load = 1.3
                if selected_load_type == "building":
                    dead_load = 1.5
                    live_load = 1.8
                    wind_load = 1.5
                    seismic_load = 1.6
                    snow_load = 1.4
            except ValueError:
                selected_load_type = "Error: Invalid load type."
                
    # collect selected load types from checkboxes add rhe corresponding values to the total load
    total_load = 0
    selected_loads = request.form.getlist("options")
    for load in selected_loads:
        if load == "dead_load":
            total_load += dead_load
        elif load == "live_load":
            total_load += live_load
        elif load == "wind_load":
            total_load += wind_load
        elif load == "seismic_load":
            total_load += seismic_load
        elif load == "snow_load":
            total_load += snow_load
    
                    
                    
                
    
    
    if request.method == "POST":
        try:
            material = request.form.get("material", 0)
            if material == "C-30":
                    strength = 30
                    E0 = strength - 9
                    G0 = strength * 0.5
            if material == "C-40":
                    strength = 40
                    E0 = strength - 9
                    G0 = strength * 0.5
            if material == "T-35":
                    strength = 35
                    E0 = strength - 9
                    G0 = strength * 0.5
            if material == "MCG-15":
                    strength = 15
                    E0 = strength - 9
                    G0 = strength * 0.5
        except ValueError:
            material = "Error: Invalid numbers."
            
        
    
    # phi is k2 times AZ over length squere root of E0 times IZ over G0
    
    #phi = k2 * AZ
    
    phi = k2 * AZ * (IZ / length) ** 0.5 * (E0 * IZ / G0) ** 0.5
    
    # Design strength FD is phi times strength
    fd = k_mode * phi * (strength / gama_factor)
    
    #utilization ratio is total load over fd
    utilization_ratio = total_load / fd 
    if utilization_ratio <= 1:
        utilization_ratio = "The design is safe. The utilization ratio is within acceptable limits.", utilization_ratio
    else:
        utilization_ratio = "The design is not safe. The utilization ratio exceeds 1.", utilization_ratio

    final_report = True 
    
    return render_template("index.html", phi=phi, k_mode=k_mode, fd=fd, total_load=total_load, utilization_ratio=utilization_ratio, final_report=final_report)
    
    
"""

@app.route("/", methods=["GET", "POST"])
def home():
    # Keep the existing calculator page and form.
    if request.method == "GET":
        """return render_template(
            "index.html",
            phi=None,
            k_mode=0.5,
            fd=None,
            total_load=None,
            utilization_ratio=None,
            final_report=False,
        )"""
        calculator_inputs = session.pop("calculator_prefill", {})

        user_projects = []
        if current_user.is_authenticated:
            user_projects = db.session.scalars(
                select(SavedProject)
                .where(SavedProject.user_id == current_user.id)
                .order_by(SavedProject.name)
            ).all()

        return render_template(
            "index.html",
            phi=None,
            k_mode=calculator_inputs.get("k_mode", 0.5),
            fd=None,
            total_load=None,
            utilization_ratio=None,
            final_report=False,
            projects=user_projects,
            calculator_inputs=calculator_inputs,
        )

    try:
        # Read and validate numeric inputs.
        k2 = float(request.form.get("k2data", "1.74"))
        length = float(request.form.get("length", "20"))
        depth = float(request.form.get("depth", "0.5"))
        width = float(request.form.get("width", "0.5"))
        k_mode = float(request.form.get("k_mode", "0.5"))

        numeric_values = [k2, length, depth, width, k_mode]
        if not all(math.isfinite(value) for value in numeric_values):
            raise ValueError("Please enter finite numeric values.")

        if length <= 0 or depth <= 0 or width <= 0:
            raise ValueError("Length, depth, and width must be greater than zero.")

        if k2 < 0 or k_mode <= 0:
            raise ValueError("The selected factors must be greater than zero.")

        # Use the first selected occupancy/load type.
        selected_types = request.form.getlist("load_type")
        load_type = selected_types[0] if selected_types else "office"

        load_factors = {
            "office": {
                "dead_load": 1.2, "live_load": 1.6,
                "wind_load": 1.4, "seismic_load": 1.5,
                "snow_load": 1.3,
            },
            "garden": {
                "dead_load": 1.3, "live_load": 1.5,
                "wind_load": 1.4, "seismic_load": 1.5,
                "snow_load": 1.3,
            },
            "residential": {
                "dead_load": 1.4, "live_load": 1.7,
                "wind_load": 1.4, "seismic_load": 1.5,
                "snow_load": 1.3,
            },
            "building": {
                "dead_load": 1.5, "live_load": 1.8,
                "wind_load": 1.5, "seismic_load": 1.6,
                "snow_load": 1.4,
            },
        }

        if load_type not in load_factors:
            raise ValueError("Please select a valid load type.")

        factors = load_factors[load_type]

        # Validate the material selection.
        material = request.form.get("material", "C-30")
        materials = {
            "C-30": 30,
            "C-40": 40,
            "T-35": 35,
            "MCG-15": 15,
        }

        if material not in materials:
            raise ValueError("Please select a valid material.")

        strength = materials[material]
        E0 = strength - 9
        G0 = strength * 0.5
        gama_factor = 1.5

        # Calculate the selected loads.
        selected_loads = request.form.getlist("options")
        allowed_loads = {
            "dead_load", "live_load", "wind_load",
            "seismic_load", "snow_load",
        }

        if not selected_loads or not set(selected_loads).issubset(allowed_loads):
            raise ValueError("Please select at least one valid load.")

        total_load = sum(factors[load] for load in selected_loads)

        # Existing prototype calculation formula retained.
        IZ = (width * depth**3) / 12
        AZ = width * 0.5

        phi = k2 * AZ * math.sqrt(IZ / length) * math.sqrt(
            E0 * IZ / G0
        )
        fd = k_mode * phi * (strength / gama_factor)

        if not math.isfinite(fd) or fd <= 0:
            raise ValueError(
                "The calculated design-strength denominator is invalid. "
                "Check your inputs."
            )

        ratio = total_load / fd

        # These labels are descriptive only, not engineering certification.
        if ratio <= 1:
            status = "Prototype utilization ratio is at or below 1."
        else:
            status = "Prototype utilization ratio exceeds 1."

        utilization_ratio = (status, ratio)
        final_report = True

    except (ValueError, TypeError, OverflowError) as error:
        flash(str(error), "error")
        return render_template(
            "index.html",
            phi=None,
            k_mode=request.form.get("k_mode", "0.5"),
            fd=None,
            total_load=None,
            utilization_ratio=None,
            final_report=False,
        )

    # Save a record only for authenticated users.
    if current_user.is_authenticated:
        history = CalculationHistory(
            user_id=current_user.id,
            inputs={
                "k2": k2,
                "length": length,
                "depth": depth,
                "width": width,
                "k_mode": k_mode,
                "material": material,
                "load_type": load_type,
                "selected_loads": selected_loads,
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
        except Exception:
            db.session.rollback()
            app.logger.exception("Could not save calculation history.")
            flash(
                "Your calculation was completed, but its history could not be saved.",
                "warning",
            )

    return render_template(
        "index.html",
        phi=phi,
        k_mode=k_mode,
        fd=fd,
        total_load=total_load,
        utilization_ratio=utilization_ratio,
        final_report=final_report,
        projects=(
            db.session.scalars(
                select(SavedProject)
                .where(SavedProject.user_id == current_user.id)
            ).all()
            if current_user.is_authenticated else []
        ),
        calculator_inputs={},
    )
    
@app.route("/history")
@login_required
def calculation_history():
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
 
@app.route("/projects", methods=["GET", "POST"])
@login_required
def projects():
    if request.method == "POST":
        name = request.form.get("name", "").strip()

        if not name or len(name) > 150:
            flash("Project name must be between 1 and 150 characters.", "error")
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
            flash("Could not create the project. Please try again.", "error")

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
        flash("Project name must be between 1 and 150 characters.", "error")
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
        db.session.delete(project)
        db.session.commit()
        flash("Project deleted successfully.", "success")
    except Exception:
        db.session.rollback()
        app.logger.exception("Could not delete project.")
        flash("Could not delete the project.", "error")

    return redirect(url_for("projects"))
   

if __name__ == "__main__":
    app.run(debug=True)
