import requests
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

from models import db, User, AccessKey, Restaurant, DailySales
from urllib.parse import quote
from datetime import date, timedelta

app = Flask(__name__)

app.config["SECRET_KEY"] = "change_this_later"

# =========================
# DATABASE CONFIG
# =========================

database_url = os.getenv("DATABASE_URL")

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


# =========================
# ROUTES
# =========================

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
        confirm_password = request.form.get("confirm_password")
        access_key_value = request.form.get("access_key")

        if password != confirm_password:
            return "Passwords do not match"

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return "Email already exists"

        access_key = AccessKey.query.filter_by(
            access_key=access_key_value,
            is_used=False
        ).first()

        if not access_key:
            return "Invalid or already used access key"

        if access_key.assigned_email:
            if access_key.assigned_email.lower() != email.lower():
                return "This access key is assigned to a different email"

        hashed_password = generate_password_hash(password)

        new_user = User(
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            email=email,
            password=hashed_password
        )

        db.session.add(new_user)
        db.session.flush()

        access_key.is_used = True
        access_key.used_by_email = email

        db.session.commit()

        login_user(new_user)
        return redirect(url_for("dashboard"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()

        if not user:
            return "User not found"

        if not check_password_hash(user.password, password):
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

    locations = Restaurant.query.filter_by(
        owner_id=current_user.id
    ).all()

    needs_restaurant_setup = len(locations) == 0

    from models import DailySales
    from datetime import date

    today = date.today()

    today_data = DailySales.query.filter_by(
        restaurant_id=locations[0].id if locations else None,
        date=today
    ).first()

    if today_data:
        sales = today_data.sales
        labor_cost = today_data.labor_cost
        waste_cost = today_data.waste_cost
        covers = today_data.covers
    else:
        sales = 0
        labor_cost = 0
        waste_cost = 0
        covers = 0

    return render_template(
        "dashboard.html",
        sales=sales,
        labor_cost=labor_cost,
        waste_cost=waste_cost,
        covers=covers,
        needs_restaurant_setup=needs_restaurant_setup
    )

# =========================
# CALCULATIONS (OUTSIDE IF BLOCK)
# =========================

labor_percent = round((labor_cost / sales) * 100, 1) if sales else 0
waste_percent = round((waste_cost / sales) * 100, 1) if sales else 0

profit_impact_percent = round(
    ((labor_cost + waste_cost) / sales) * 100,
    1
) if sales else 0

# =========================
# HOURLY DATA (TEMP SIMPLIFIED)
# =========================

hourly_records = DailySales.query.filter_by(
    restaurant_id=locations[0].id if locations else None,
    date=today
).all()

hourly_data = []

for record in hourly_records:

    hourly_data.append({
        "hour": "Day Summary",
        "sales": record.sales,
        "covers": record.covers,
        "labor_cost": record.labor_cost,
        "sales_per_server_hour": round(record.sales / 8, 2) if record.sales else 0,
        "covers_per_server_hour": round(record.covers / 8, 2) if record.covers else 0,
        "labor_percent": round((record.labor_cost / record.sales) * 100, 1) if record.sales else 0
    })

# 👇 ADD THIS RIGHT HERE
seven_day_data = []

for i in range(7):

    day = today - timedelta(days=i)

    day_data = DailySales.query.filter_by(
        restaurant_id=locations[0].id if locations else None,
        date=day
    ).first()

    if day_data:
        seven_day_data.append({
            "date": str(day),
            "sales": day_data.sales,
            "labor_cost": day_data.labor_cost,
            "waste_cost": day_data.waste_cost,
            "covers": day_data.covers
        })
    else:
        seven_day_data.append({
            "date": str(day),
            "sales": 0,
            "labor_cost": 0,
            "waste_cost": 0,
            "covers": 0
        })


@app.route("/settings")
@login_required
def settings():

    active_settings_tab = request.args.get("tab", "user-info")

    restaurant = Restaurant.query.filter_by(
        owner_id=current_user.id
    ).first()

    return render_template(
        "settings.html",
        active_page="settings",
        active_settings_tab=active_settings_tab,
        restaurant=restaurant
    )


@app.route("/settings/restaurant/save", methods=["POST"])
@login_required
def save_restaurant():

    restaurant = Restaurant(
        owner_id=current_user.id
    )

    restaurant.restaurant_name = request.form.get("restaurant_name")
    restaurant.business_type = request.form.get("business_type")
    restaurant.phone = request.form.get("phone")
    restaurant.email = request.form.get("email")
    restaurant.address = request.form.get("address")
    restaurant.city = request.form.get("city")
    restaurant.province = request.form.get("province")
    restaurant.country = request.form.get("country")
    restaurant.postal_code = request.form.get("postal_code")
    restaurant.timezone = request.form.get("timezone")
    restaurant.pos_provider = request.form.get("pos_provider")

    db.session.add(restaurant)
    db.session.commit()

    return redirect(url_for("locations"))


@app.route("/admin")
@login_required
def admin():

    if not current_user.is_admin:
        return redirect(url_for("dashboard"))

    return render_template("admin.html")


@app.route("/waste-analytics")
@login_required
def waste_analytics():
    return render_template("waste_analytics.html", active_page="waste")


@app.route("/locations")
@login_required
def locations():

    locations = Restaurant.query.filter_by(
        owner_id=current_user.id
    ).all()

    return render_template(
        "locations.html",
        active_page="locations",
        locations=locations
    )


@app.route("/labour-tracking")
@login_required
def labour_tracking():
    return render_template("labour_tracking.html", active_page="labour")


@app.route("/reports")
@login_required
def reports():
    return render_template("reports.html", active_page="reports")


@app.route("/seed-data")
@login_required
def seed_data():

    from models import DailySales
    from datetime import date, timedelta

    restaurant = Restaurant.query.filter_by(
        owner_id=current_user.id
    ).first()

    if not restaurant:
        return "No restaurant found for this user"

    restaurant_id = restaurant.id

    today = date.today()

    # create 14 days of fake data
    for i in range(14):

        day = today - timedelta(days=i)

        entry = DailySales(
            restaurant_id=restaurant_id,
            date=day,
            sales=round(4000 + (i * 120), 2),
            labor_cost=round(1200 + (i * 40), 2),
            waste_cost=round(200 + (i * 10), 2),
            covers=round(140 + (i * 5))
        )

        db.session.add(entry)

    db.session.commit()

    return "Seeded 14 days of data"

@app.route("/debug/add-sales")
@login_required
def debug_add_sales():

    locations = Restaurant.query.filter_by(owner_id=current_user.id).all()

    if not locations:
        return "No restaurant found"

    today = date.today()

    record = DailySales.query.filter_by(
        restaurant_id=locations[0].id,
        date=today
    ).first()

    if not record:
        record = DailySales(
            restaurant_id=locations[0].id,
            date=today,
            sales=0,
            labor_cost=0,
            waste_cost=0,
            covers=0
        )

        db.session.add(record)

    record.sales += 500
    record.covers += 10

    db.session.commit()

    return "Added +500 sales"

# =========================
# CLOVER OAUTH
# =========================

@app.route("/auth/clover")
@login_required
def clover_login():

    restaurant_id = request.args.get("restaurant_id")
    client_id = os.getenv("CLOVER_CLIENT_ID")

    redirect_uri = "https://ai-restaurant-finance.onrender.com/auth/clover/callback"

    url = (
        "https://sandbox.dev.clover.com/oauth/authorize"
        f"?client_id={client_id}"
        f"&redirect_uri={quote(redirect_uri, safe='')}"
        f"&state={restaurant_id}"
        "&response_type=code"
        "&scope=customers:read%20merchant:read%20orders:read%20payments:read%20employees:read"
    )

    return redirect(url)


@app.route("/auth/clover/callback")
def clover_callback():

    print("🔥 CLOVER CALLBACK HIT")

    code = request.args.get("code")
    restaurant_id = request.args.get("state")

    if not code or not restaurant_id:
        return "Missing OAuth data", 400

    client_id = os.getenv("CLOVER_CLIENT_ID")
    client_secret = os.getenv("CLOVER_CLIENT_SECRET")

    if not client_id or not client_secret:
        return "Missing Clover credentials", 500

    try:
        response = requests.post(
            "https://sandbox.dev.clover.com/oauth/token",
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code
            },
            timeout=10
        )

        data = response.json()

    except Exception as e:
        return f"Clover authentication failed: {str(e)}", 500

    if "access_token" not in data:
        return f"Clover auth failed: {data}", 400

    restaurant = Restaurant.query.filter_by(
        id=int(restaurant_id),
        owner_id=current_user.id
    ).first()

    if not restaurant:
        return "Restaurant not found", 404

    restaurant.pos_provider = "clover"
    restaurant.clover_access_token = data.get("access_token")

    db.session.commit()

    return redirect(url_for("locations"))


if __name__ == "__main__":
    app.run(debug=True)