from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

# =========================
# USER MODEL
# =========================

class User(UserMixin, db.Model):

    id = db.Column(db.Integer, primary_key=True)

    first_name = db.Column(db.String(150), nullable=False)
    last_name = db.Column(db.String(150), nullable=False)

    email = db.Column(db.String(150), unique=True, nullable=False)
    phone = db.Column(db.String(50), nullable=False)

    password = db.Column(db.String(255), nullable=False)

    is_admin = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# =========================
# ACCESS KEY MODEL
# =========================

class AccessKey(db.Model):

    __tablename__ = "access_keys"

    id = db.Column(db.Integer, primary_key=True)

    access_key = db.Column(db.String(255), unique=True, nullable=False)

    assigned_email = db.Column(db.String(255))

    is_used = db.Column(db.Boolean, default=False)

    used_by_email = db.Column(db.String(255))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# =========================
# RESTAURANT MODEL
# =========================

class Restaurant(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    owner_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    restaurant_name = db.Column(
        db.String(255),
        nullable=False
    )

    business_type = db.Column(
        db.String(100)
    )

    phone = db.Column(
        db.String(50)
    )

    email = db.Column(
        db.String(255)
    )

    address = db.Column(
        db.String(255)
    )

    city = db.Column(
        db.String(100)
    )

    province = db.Column(
        db.String(100)
    )

    country = db.Column(
        db.String(100)
    )

    postal_code = db.Column(
        db.String(30)
    )

    timezone = db.Column(
        db.String(100)
    )

    pos_provider = db.Column(
        db.String(100)
    )

    api_connected = db.Column(
        db.Boolean,
        default=False
    )

    clover_access_token = db.Column(
        db.Text
    )

    clover_merchant_id = db.Column(
        db.String(255)
    )

    last_sync_at = db.Column(
        db.DateTime
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

# =========================
class DailySales(db.Model):
# =========================

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    restaurant_id = db.Column(
        db.Integer,
        db.ForeignKey("restaurant.id"),
        nullable=False
    )

    date = db.Column(
        db.Date,
        nullable=False
    )

    sales = db.Column(
        db.Float,
        default=0
    )

    labor_cost = db.Column(
        db.Float,
        default=0
    )

    waste_cost = db.Column(
        db.Float,
        default=0
    )

    covers = db.Column(
        db.Integer,
        default=0
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )