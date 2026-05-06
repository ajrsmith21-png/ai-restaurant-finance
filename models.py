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