
from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="user")
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    projects = db.relationship(
        "SavedProject",
        back_populates="owner",
        cascade="all, delete-orphan",
    )
    calculations = db.relationship(
        "CalculationHistory",
        back_populates="owner",
        cascade="all, delete-orphan",
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == "admin"


class SavedProject(db.Model):
    __tablename__ = "saved_projects"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    name = db.Column(db.String(150), nullable=False)
    input_data = db.Column(db.JSON, nullable=False, default=dict)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    owner = db.relationship("User", back_populates="projects")
    calculations = db.relationship(
        "CalculationHistory",
        back_populates="project",
    )


class CalculationHistory(db.Model):
    __tablename__ = "calculation_history"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    project_id = db.Column(
        db.Integer,
        db.ForeignKey("saved_projects.id"),
        nullable=True,
        index=True,
    )
    inputs = db.Column(db.JSON, nullable=False)
    results = db.Column(db.JSON, nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    owner = db.relationship("User", back_populates="calculations")
    project = db.relationship("SavedProject", back_populates="calculations")

class DesignStandard(db.Model):
    """A design standard supported by the application."""

    __tablename__ = "design_standards"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), nullable=False)
    edition = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    jurisdiction = db.Column(db.String(100), nullable=False, default="Europe")
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    is_default = db.Column(db.Boolean, nullable=False, default=False)
    source_status = db.Column(
        db.String(30), nullable=False, default="mock_unverified"
    )
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        db.UniqueConstraint(
            "code", "edition", name="uq_design_standard_code_edition"
        ),
    )

    def __repr__(self):
        return f"<DesignStandard {self.code} {self.edition}>"


class TimberStrengthClass(db.Model):
    """Timber strength-class properties from a declared property standard."""

    __tablename__ = "timber_strength_classes"

    id = db.Column(db.Integer, primary_key=True)
    property_standard = db.Column(
        db.String(50), nullable=False, default="EN 338:2016"
    )
    material_type = db.Column(
        db.String(30), nullable=False, default="softwood"
    )
    strength_class = db.Column(db.String(20), nullable=False)
    description = db.Column(db.String(200), nullable=False)

    # Characteristic strengths, in MPa = N/mm².
    fm_k_mpa = db.Column(db.Float, nullable=False)
    ft_0_k_mpa = db.Column(db.Float, nullable=False)
    fc_0_k_mpa = db.Column(db.Float, nullable=False)
    fv_k_mpa = db.Column(db.Float, nullable=False)

    # Elastic properties, in MPa = N/mm².
    e_0_mean_mpa = db.Column(db.Float, nullable=False)
    e_0_05_mpa = db.Column(db.Float, nullable=False)

    # Density, in kg/m³.
    rho_k_kg_m3 = db.Column(db.Float, nullable=False)
    rho_mean_kg_m3 = db.Column(db.Float, nullable=False)

    source_status = db.Column(
        db.String(30), nullable=False, default="mock_unverified"
    )
    source_reference = db.Column(
        db.String(200), nullable=False, default="Needs verification against EN 338"
    )
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        db.UniqueConstraint(
            "property_standard",
            "material_type",
            "strength_class",
            name="uq_timber_class_standard_type_grade",
        ),
    )

    def __repr__(self):
        return (
            f"<TimberStrengthClass "
            f"{self.property_standard} {self.strength_class}>"
        )
        
        