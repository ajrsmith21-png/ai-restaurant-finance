from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()


# =========================
# BUSINESS MODEL
# =========================

class Business(db.Model):

    __tablename__ = "businesses"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    business_name = db.Column(
        db.String(255),
        nullable=False
    )

    business_email = db.Column(
        db.String(255)
    )

    business_phone = db.Column(
        db.String(50)
    )

    business_address = db.Column(
        db.String(500)
    )

    pos_provider = db.Column(
        db.String(100)
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    users = db.relationship(
        "User",
        backref="business",
        lazy=True
    )


# =========================
# USER MODEL
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
        db.String(50),
        nullable=False
    )

    password = db.Column(
        db.String(255),
        nullable=False
    )

    business_id = db.Column(
        db.Integer,
        db.ForeignKey("businesses.id")
    )


# =========================
# ACCESS KEY MODEL
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

    business_id = db.Column(
        db.Integer,
        db.ForeignKey("businesses.id"),
        nullable=False
    )

    is_used = db.Column(
        db.Boolean,
        default=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )