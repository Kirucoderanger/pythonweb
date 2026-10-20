"""
from flask import Flask, render_template, request

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def home():
    result = None
    if request.method == "POST":
        try:
            # Extract inputs from the HTML form 'name' attributes
            # float() allows both whole numbers and decimals
            num1 = float(request.form.get("num1", 0))
            num2 = float(request.form.get("num2", 0))
            
            # Perform the multiplication
            result = num1 * num2
        except ValueError:
            result = "Error: Please enter valid numbers."

    return render_template("index.html", result=result)

if __name__ == "__main__":
    app.run(debug=True)
"""
import os
from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Use SQLite locally, or PostgreSQL on Render if available
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///prototype.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# Define your database model
class Calculation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    num1 = db.Column(db.Float, nullable=False)
    num2 = db.Column(db.Float, nullable=False)
    result = db.Column(db.Float, nullable=False)

# Automatically create the database tables
with app.app_context():
    db.create_all()

@app.route("/", methods=["GET", "POST"])
def home():
    current_result = None
    if request.method == "POST":
        try:
            n1 = float(request.form.get("num1", 0))
            n2 = float(request.form.get("num2", 0))
            current_result = n1 + n2
            
            # Save the record to the database
            new_calc = Calculation(num1=n1, num2=n2, result=current_result)
            db.session.add(new_calc)
            db.session.commit()
        except ValueError:
            current_result = "Error: Invalid numbers."

    # Fetch the last 5 entries from the database to display in the prototype
    history = Calculation.query.order_by(Calculation.id.desc()).limit(5).all()
    return render_template("index.html", result=current_result, history=history)

if __name__ == "__main__":
    app.run(debug=True)
