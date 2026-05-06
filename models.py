from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()


# =========================
# BUSINESSES
# =========================

class Business(db.Model):

    __tablename__ = "businesses"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    business_name = db.Column(
        db.String(255)
    )

    business_address = db.Column(
        db.String(255)
    )

    business_email = db.Column(
        db.String(255)
    )

    business_phone = db.Column(
        db.String(30)
    )

    pos_provider = db.Column(
        db.String(100)
    )

    pos_connected = db.Column(
        db.Boolean,
        default=False
    )


# =========================
# USERS
# =========================

class User(UserMixin, db.Model):

    __tablename__ = "users"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    first_name = db.Column(
        db.String(100),
        nullable=False
    )

    last_name = db.Column(
        db.String(100),
        nullable=False
    )

    email = db.Column(
        db.String(150),
        unique=True,
        nullable=False
    )

    phone = db.Column(
        db.String(30)
    )

    password = db.Column(
        db.String(200),
        nullable=False
    )

    business_id = db.Column(
        db.Integer,
        db.ForeignKey("businesses.id")
    )


# =========================
# ACCESS KEYS
# =========================

class AccessKey(db.Model):

    __tablename__ = "access_keys"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    access_key = db.Column(
        db.String(255),
        unique=True,
        nullable=False
    )

    is_used = db.Column(
        db.Boolean,
        default=False
    )

    used_by_user_id = db.Column(
        db.Integer
    )