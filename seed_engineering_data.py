
"""
Seed mock Eurocode design standards and timber strength classes.

Run from the project root:
    python seed_engineering_data.py

All timber properties seeded by this file are mock data and require
verification against the licensed standard documentation before use
in engineering calculations.
"""

from app import app
from extensions import db
from models import DesignStandard, TimberStrengthClass


DESIGN_STANDARDS = [
    {
        "code": "EN 1995-1-1",
        "edition": "2004+A2:2014",
        "title": "Eurocode 5: Design of timber structures",
        "jurisdiction": "Europe",
        "is_default": True,
        "source_status": "mock_unverified",
        "notes": (
            "Catalogue placeholder for the first-generation Eurocode 5. "
            "Confirm the applicable national implementation and National Annex."
        ),
    },
    {
        "code": "EN 1995-1-1",
        "edition": "2025",
        "title": "Eurocode 5: Design of timber structures, second generation",
        "jurisdiction": "Europe",
        "is_default": False,
        "source_status": "mock_unverified",
        "notes": (
            "Catalogue placeholder. Confirm publication, national adoption, "
            "transition rules, and applicable National Annex before use."
        ),
    },
]

# Values are representative mock seed data, not approved design data.
# Units:
#   strengths and elastic moduli: MPa = N/mm²
#   densities: kg/m³
#
# Columns:
# grade, fm,k, ft,0,k, fc,0,k, fv,k, E0,mean, E0,05, rho,k, rho,mean
SOFTWOOD_CLASSES = [
    ("C14", 14, 8.0, 16, 3.0, 7000, 4700, 290, 350),
    ("C16", 16, 10.0, 17, 3.2, 8000, 5400, 310, 370),
    ("C18", 18, 11.0, 18, 3.4, 9000, 6000, 320, 380),
    ("C20", 20, 12.0, 19, 3.6, 9500, 6400, 330, 390),
    ("C22", 22, 13.0, 20, 3.8, 10000, 6700, 340, 410),
    ("C24", 24, 14.0, 21, 4.0, 11000, 7400, 350, 420),
    ("C27", 27, 16.0, 22, 4.0, 11500, 7700, 370, 450),
    ("C30", 30, 18.0, 23, 4.0, 12000, 8000, 380, 460),
    ("C35", 35, 21.0, 25, 4.0, 13000, 8700, 400, 480),
    ("C40", 40, 24.0, 26, 4.0, 14000, 9400, 420, 500),
    ("C45", 45, 27.0, 27, 4.0, 15000, 10000, 440, 520),
    ("C50", 50, 30.0, 29, 4.0, 16000, 10700, 460, 550),
]


def seed_design_standards():
    """Insert or update catalogue design-standard records."""
    for item in DESIGN_STANDARDS:
        record = DesignStandard.query.filter_by(
            code=item["code"],
            edition=item["edition"],
        ).first()

        if record is None:
            record = DesignStandard(
                code=item["code"],
                edition=item["edition"],
                title=item["title"],
                jurisdiction=item["jurisdiction"],
                is_default=item["is_default"],
                source_status=item["source_status"],
                notes=item["notes"],
            )
            db.session.add(record)
        else:
            record.title = item["title"]
            record.jurisdiction = item["jurisdiction"]
            record.is_default = item["is_default"]
            record.source_status = item["source_status"]
            record.notes = item["notes"]

    db.session.flush()


def seed_timber_classes():
    """Insert or update mock EN 338 softwood class records."""
    for row in SOFTWOOD_CLASSES:
        (
            grade,
            fm_k,
            ft_0_k,
            fc_0_k,
            fv_k,
            e_0_mean,
            e_0_05,
            rho_k,
            rho_mean,
        ) = row

        record = TimberStrengthClass.query.filter_by(
            property_standard="EN 338:2016",
            material_type="softwood",
            strength_class=grade,
        ).first()

        if record is None:
            record = TimberStrengthClass(
                property_standard="EN 338:2016",
                material_type="softwood",
                strength_class=grade,
                description=f"Softwood strength class {grade}",
            )
            db.session.add(record)

        record.fm_k_mpa = fm_k
        record.ft_0_k_mpa = ft_0_k
        record.fc_0_k_mpa = fc_0_k
        record.fv_k_mpa = fv_k
        record.e_0_mean_mpa = e_0_mean
        record.e_0_05_mpa = e_0_05
        record.rho_k_kg_m3 = rho_k
        record.rho_mean_kg_m3 = rho_mean
        record.source_status = "mock_unverified"
        record.source_reference = (
            "MOCK DATA: verify every value against the applicable EN 338 edition"
        )
        record.is_active = True


def main():
    with app.app_context():
        seed_design_standards()
        seed_timber_classes()
        db.session.commit()

        print("Engineering catalogue seed completed.")
        print(f"Design standards: {DesignStandard.query.count()}")
        print(f"Timber classes: {TimberStrengthClass.query.count()}")
        print("WARNING: timber properties are mock data; not for design use.")


if __name__ == "__main__":
    main()
