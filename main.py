import os

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for
)

from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from models import db, User

app = Flask(__name__)

app.config["SECRET_KEY"] = "change_this_later"

# =========================
# DATABASE CONFIG
# =========================

database_url = os.getenv("DATABASE_URL")

# Render sometimes provides postgres://
# SQLAlchemy prefers postgresql://

if database_url and database_url.startswith("postgres://"):

    database_url = database_url.replace(
        "postgres://",
        "postgresql://",
        1
    )

app.config["SQLALCHEMY_DATABASE_URI"] = database_url

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

login_manager = LoginManager()

login_manager.login_view = "login"

login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):

    return User.query.get(int(user_id))


@app.route("/")
def home():

    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        first_name = request.form.get("first_name")

        last_name = request.form.get("last_name")

        phone = request.form.get("phone")

        email = request.form.get("email")

        password = request.form.get("password")

        existing_user = User.query.filter_by(
            email=email
        ).first()

        if existing_user:

            return "Email already exists"

        hashed_password = generate_password_hash(
            password
        )

        new_user = User(
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            email=email,
            password=hashed_password
        )

        db.session.add(new_user)

        db.session.commit()

        login_user(new_user)

        return redirect(url_for("dashboard"))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email")

        password = request.form.get("password")

        user = User.query.filter_by(
            email=email
        ).first()

        if not user:

            return "User not found"

        if not check_password_hash(
            user.password,
            password
        ):

            return "Incorrect password"

        login_user(user)

        return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():

    logout_user()

    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():

    # CORE METRICS

    sales = 5200
    labor_cost = 1450
    waste_cost = 340
    covers = 186

    # PERCENTAGES

    labor_percent = round((labor_cost / sales) * 100, 1)
    waste_percent = round((waste_cost / sales) * 100, 1)

    # PROFIT IMPACT

    profit_impact_percent = round(
        ((labor_cost + waste_cost) / sales) * 100,
        1
    )

    # HOURLY ANALYTICS

    hourly_data = [

        {
            "hour": "11 AM",
            "sales": 420,
            "covers": 18,
            "labor_cost": 110,
            "sales_per_server_hour": 140,
            "covers_per_server_hour": 6,
            "labor_percent": 26
        },

        {
            "hour": "12 PM",
            "sales": 780,
            "covers": 34,
            "labor_cost": 160,
            "sales_per_server_hour": 195,
            "covers_per_server_hour": 8.5,
            "labor_percent": 20
        },

        {
            "hour": "1 PM",
            "sales": 690,
            "covers": 29,
            "labor_cost": 155,
            "sales_per_server_hour": 172,
            "covers_per_server_hour": 7.2,
            "labor_percent": 22
        },

        {
            "hour": "2 PM",
            "sales": 480,
            "covers": 21,
            "labor_cost": 145,
            "sales_per_server_hour": 120,
            "covers_per_server_hour": 5.2,
            "labor_percent": 30
        },

        {
            "hour": "3 PM",
            "sales": 350,
            "covers": 14,
            "labor_cost": 138,
            "sales_per_server_hour": 88,
            "covers_per_server_hour": 3.5,
            "labor_percent": 39
        }

    ]

    return render_template(
        "dashboard.html",

        sales=sales,
        labor_cost=labor_cost,
        waste_cost=waste_cost,
        covers=covers,

        labor_percent=labor_percent,
        waste_percent=waste_percent,
        profit_impact_percent=profit_impact_percent,

        hourly_data=hourly_data,

        active_page="dashboard"
    )


@app.route("/waste-analytics")
@login_required
def waste_analytics():

    return render_template(
        "waste_analytics.html",
        active_page="waste"
    )


@app.route("/labour-tracking")
@login_required
def labour_tracking():

    return render_template(
        "labour_tracking.html",
        active_page="labour"
    )


@app.route("/reports")
@login_required
def reports():

    return render_template(
        "reports.html",
        active_page="reports"
    )


with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=True)