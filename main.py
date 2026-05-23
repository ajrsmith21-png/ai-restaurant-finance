import csv
import io
import requests
import os

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    abort
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
from datetime import date, timedelta, datetime


def clean_money(value):
    if value is None:
        return 0.0

    try:
        cleaned = str(value).replace("$", "").replace(",", "").strip()
        return float(cleaned) if cleaned else 0.0
    except ValueError:
        return 0.0


def clean_percent(value):
    if value is None:
        return 0.0

    try:
        cleaned = str(value).replace("%", "").replace(" ", "").strip()
        return round(float(cleaned), 2) if cleaned else 0.0
    except ValueError:
        return 0.0


def clean_int(value):
    if value is None:
        return 0

    try:
        return int(float(str(value).strip()))
    except (ValueError, TypeError):
        return 0


def clean_date(value):
    if value is None:
        return None

    raw = str(value).strip()
    if not raw:
        return None

    date_formats = [
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%m/%d/%y",
        "%d-%m-%Y",
        "%Y/%m/%d"
    ]

    for fmt in date_formats:
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue

    try:
        return date.fromisoformat(raw)
    except ValueError:
        return None


app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

if not app.config["SECRET_KEY"]:
    raise ValueError("SECRET_KEY environment variable missing")

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

with app.app_context():
    db.create_all()

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

    if needs_restaurant_setup:
        return redirect(url_for("setup_restaurant"))

    restaurant_id = request.args.get("restaurant_id")

    if restaurant_id:
        try:
            restaurant_id = int(restaurant_id)
        except ValueError:
            restaurant_id = None

    if not restaurant_id:
        restaurant_id = session.get("restaurant_id")

    first_location = next(iter(locations), None)

    if not restaurant_id and first_location:
        restaurant_id = first_location.id

    selected_restaurant = next(
        (r for r in locations if r.id == restaurant_id),
        None
    )

    if selected_restaurant is None and first_location:
        selected_restaurant = first_location
        session["restaurant_id"] = selected_restaurant.id
    elif selected_restaurant:
        session["restaurant_id"] = selected_restaurant.id

    today = date.today()

    if selected_restaurant:
        today_data = DailySales.query.filter_by(
            restaurant_id=selected_restaurant.id,
            date=today
        ).order_by(DailySales.id.desc()).first()

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

        labor_percent = round((labor_cost / sales) * 100, 1) if sales else 0
        waste_percent = round((waste_cost / sales) * 100, 1) if sales else 0

        profit_impact_percent = round(
            ((labor_cost + waste_cost) / sales) * 100,
            1
        ) if sales else 0

        hourly_data = []

        hours = 12
        for i in range(hours):
            hourly_data.append({
                "hour": f"{i+1}:00",
                "sales": round(today_data.sales / hours, 2) if today_data else 0,
                "covers": round(today_data.covers / hours, 2) if today_data else 0,
                "labor_cost": round(today_data.labor_cost / hours, 2) if today_data else 0,
                "sales_per_server_hour": round(today_data.sales / hours, 2) if today_data else 0,
                "covers_per_server_hour": round(today_data.covers / hours, 2) if today_data else 0,
                "labor_percent": round((today_data.labor_cost / today_data.sales) * 100, 1) if today_data and today_data.sales else 0
            })

        seven_day_data = []

        for i in range(7):
            day = today - timedelta(days=i)

            day_data = DailySales.query.filter_by(
                restaurant_id=selected_restaurant.id,
                date=day
            ).order_by(DailySales.id.desc()).first()

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
    else:
        sales = 0
        labor_cost = 0
        waste_cost = 0
        covers = 0

        labor_percent = 0
        waste_percent = 0
        profit_impact_percent = 0

        hourly_data = []
        for i in range(12):
            hourly_data.append({
                "hour": f"{i+1}:00",
                "sales": 0,
                "covers": 0,
                "labor_cost": 0,
                "sales_per_server_hour": 0,
                "covers_per_server_hour": 0,
                "labor_percent": 0
            })

        seven_day_data = []
        for i in range(7):
            day = today - timedelta(days=i)
            seven_day_data.append({
                "date": str(day),
                "sales": 0,
                "labor_cost": 0,
                "waste_cost": 0,
                "covers": 0
            })

    return render_template(
        "dashboard.html",
        sales=sales,
        labor_cost=labor_cost,
        waste_cost=waste_cost,
        covers=covers,
        needs_restaurant_setup=needs_restaurant_setup,
        hourly_data=hourly_data,
        seven_day_data=seven_day_data
    )

@app.route("/setup-restaurant", methods=["GET", "POST"])
@login_required
def setup_restaurant():

    locations = Restaurant.query.filter_by(
        owner_id=current_user.id
    ).all()

    if locations:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        restaurant_name = request.form.get("restaurant_name")
        address = request.form.get("address")

        restaurant = Restaurant(
            owner_id=current_user.id,
            restaurant_name=restaurant_name or "",
            address=address or ""
        )

        db.session.add(restaurant)
        db.session.commit()

        session["restaurant_id"] = restaurant.id
        return redirect(url_for("dashboard"))

    return """
    <h1>Set Up Your Restaurant</h1>
    <form method="post">
      <label>Name: <input name="restaurant_name" type="text" required /></label><br/>
      <label>Address: <input name="address" type="text" /></label><br/>
      <button type="submit">Create Restaurant</button>
    </form>
    """

@app.route("/add-sales", methods=["GET", "POST"])
@login_required
def add_sales():

    locations = Restaurant.query.filter_by(
        owner_id=current_user.id
    ).all()

    restaurant_id = session.get("restaurant_id")

    first_location = next(iter(locations), None)

    if not restaurant_id and first_location:
        restaurant_id = first_location.id

    selected_restaurant = next(
        (r for r in locations if r.id == restaurant_id),
        None
    )

    if selected_restaurant is None and first_location:
        selected_restaurant = first_location
        session["restaurant_id"] = selected_restaurant.id

    if not selected_restaurant:
        return redirect(url_for("dashboard"))

    today = date.today()

    if request.method == "POST":
        sales = request.form.get("sales") or 0
        labor_cost = request.form.get("labor_cost") or 0
        waste_cost = request.form.get("waste_cost") or 0
        covers = request.form.get("covers") or 0

        try:
            sales = float(sales)
        except ValueError:
            sales = 0

        try:
            labor_cost = float(labor_cost)
        except ValueError:
            labor_cost = 0

        try:
            waste_cost = float(waste_cost)
        except ValueError:
            waste_cost = 0

        try:
            covers = float(covers)
        except ValueError:
            covers = 0

        record = DailySales.query.filter_by(
            restaurant_id=selected_restaurant.id,
            date=today
        ).first()

        if not record:
            record = DailySales(
                restaurant_id=selected_restaurant.id,
                date=today,
                sales=sales,
                labor_cost=labor_cost,
                waste_cost=waste_cost,
                covers=covers
            )
            db.session.add(record)
        else:
            record.sales = sales
            record.labor_cost = labor_cost
            record.waste_cost = waste_cost
            record.covers = covers

        db.session.commit()
        return redirect(url_for("dashboard"))

    return """
    <h1>Add Sales</h1>
    <form method="post">
      <label>Sales: <input name="sales" type="number" step="0.01" /></label><br/>
      <label>Labor Cost: <input name="labor_cost" type="number" step="0.01" /></label><br/>
      <label>Waste Cost: <input name="waste_cost" type="number" step="0.01" /></label><br/>
      <label>Covers: <input name="covers" type="number" step="1" /></label><br/>
      <button type="submit">Save</button>
    </form>
    """

@app.route("/upload-sales", methods=["POST"])
@login_required
def upload_sales():

    csv_file = request.files.get("file")
    if not csv_file or csv_file.filename == "":
        return render_template(
            "upload_sales.html",
            error="No file selected. Please choose a CSV file."
        )

    locations = Restaurant.query.filter_by(
        owner_id=current_user.id
    ).all()

    restaurant_id = session.get("restaurant_id")
    first_location = next(iter(locations), None)

    if not restaurant_id and first_location:
        restaurant_id = first_location.id

    selected_restaurant = next(
        (r for r in locations if r.id == restaurant_id),
        None
    )

    if selected_restaurant is None and first_location:
        selected_restaurant = first_location
        session["restaurant_id"] = selected_restaurant.id

    if not selected_restaurant:
        return render_template(
            "upload_sales.html",
            error="No restaurant found. Please set up a restaurant first."
        )

    try:
        raw_data = csv_file.read().decode("utf-8-sig")
    except Exception as e:
        print(f"File decode error: {str(e)}")
        return render_template(
            "upload_sales.html",
            error="Unable to read file. Please ensure it is a valid CSV file."
        )

    reader = csv.DictReader(io.StringIO(raw_data))

    if not reader.fieldnames:
        print("CSV file is empty or has no headers")
        return render_template(
            "upload_sales.html",
            error="CSV file is empty or has no headers."
        )

    expected_headers = ["date", "sales", "labor_cost", "waste_cost", "covers"]
    headers = [h.strip().lower() for h in reader.fieldnames]

    if headers != expected_headers:
        print(f"Rejected CSV with invalid headers. Expected: {expected_headers}, Got: {headers}")
        return render_template(
            "upload_sales.html",
            error="Invalid file format. Required columns:\ndate,sales,labor_cost,waste_cost,covers"
        )

    uploaded_count = 0
    skipped_count = 0
    row_number = 1

    for row in reader:
        row_number += 1

        date_value = clean_date(row.get("date"))
        sales_value = clean_money(row.get("sales"))
        labor_cost_value = clean_money(row.get("labor_cost"))
        waste_cost_value = clean_money(row.get("waste_cost"))
        covers_value = clean_int(row.get("covers"))

        if not date_value:
            print(f"Skipped row {row_number}: invalid or missing date. Data: {row}")
            skipped_count += 1
            continue

        record = DailySales.query.filter_by(
            restaurant_id=selected_restaurant.id,
            date=date_value
        ).order_by(DailySales.id.desc()).first()

        if not record:
            record = DailySales(
                restaurant_id=selected_restaurant.id,
                date=date_value,
                sales=sales_value,
                labor_cost=labor_cost_value,
                waste_cost=waste_cost_value,
                covers=covers_value
            )
            db.session.add(record)
        else:
            record.sales = sales_value
            record.labor_cost = labor_cost_value
            record.waste_cost = waste_cost_value
            record.covers = covers_value

        uploaded_count += 1

    db.session.commit()

    return render_template(
        "upload_sales.html",
        success=True,
        uploaded_count=uploaded_count,
        skipped_count=skipped_count
    )

@app.route("/upload-sales-page")
@login_required
def upload_sales_page():
    return render_template("upload_sales.html")

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

    first_location = next(iter(locations), None)

    if not first_location:
        return "No restaurant found"

    today = date.today()

    record = DailySales.query.filter_by(
        restaurant_id=first_location.id,
        date=today
    ).first()

    if not record:
        record = DailySales(
            restaurant_id=first_location.id,
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
@app.route("/dev/simulate-day")
@login_required
def dev_simulate_day():

    allow_dev = app.debug or os.getenv("DEV_SIMULATE_ENABLED") == "1"
    if not allow_dev:
        abort(404)

    locations = Restaurant.query.filter_by(
        owner_id=current_user.id
    ).all()

    restaurant_id = session.get("restaurant_id")
    first_location = next(iter(locations), None)

    if not restaurant_id and first_location:
        restaurant_id = first_location.id

    selected_restaurant = next(
        (r for r in locations if r.id == restaurant_id),
        None
    )

    if selected_restaurant is None and first_location:
        selected_restaurant = first_location
        session["restaurant_id"] = selected_restaurant.id

    if not selected_restaurant:
        return redirect(url_for("dashboard"))

    today = date.today()

    record = DailySales.query.filter_by(
        restaurant_id=selected_restaurant.id,
        date=today
    ).first()

    if not record:
        record = DailySales(
            restaurant_id=selected_restaurant.id,
            date=today,
            sales=1000,
            labor_cost=300,
            waste_cost=50,
            covers=80
        )
        db.session.add(record)
    else:
        record.sales = 1000
        record.labor_cost = 300
        record.waste_cost = 50
        record.covers = 80

    db.session.commit()
    return redirect(url_for("dashboard"))
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