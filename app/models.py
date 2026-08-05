from datetime import datetime, timezone
from decimal import Decimal

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db


def utc_now():
    return datetime.now(timezone.utc)


class User(UserMixin, db.Model):
    __tablename__ = "users"
    __table_args__ = (
        db.CheckConstraint(
            "status IN ('pending', 'active', 'disabled')",
            name="ck_users_status",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    supabase_id = db.Column(db.String(255), unique=True, nullable=True, index=True)
    role = db.Column(db.String(20), nullable=False, default="driver")
    status = db.Column(db.String(20), nullable=False, default="active", index=True)
    is_active_account = db.Column(db.Boolean, nullable=False, default=True)
    must_change_password = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)
    records = db.relationship("DailyRecord", back_populates="user", lazy="dynamic")
    categories = db.relationship("Category", back_populates="user", lazy="dynamic")

    @property
    def is_active(self):
        return self.status == "active" and self.is_active_account

    @property
    def is_pending(self):
        return self.status == "pending"

    @property
    def is_disabled(self):
        return self.status == "disabled"

    @property
    def is_admin(self):
        return self.role == "admin"

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def activate(self):
        self.status = "active"
        self.is_active_account = True

    def disable(self):
        self.status = "disabled"
        self.is_active_account = False


class DailyRecord(db.Model):
    __tablename__ = "daily_records"
    __table_args__ = (
        db.UniqueConstraint("user_id", "date", name="uq_daily_records_user_date"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False, index=True)
    gross_revenue = db.Column(db.Numeric(12, 2), nullable=False)
    kilometers = db.Column(db.Numeric(10, 2), nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    expenses = db.relationship(
        "Expense", back_populates="record", cascade="all, delete-orphan", lazy="selectin"
    )
    user = db.relationship("User", back_populates="records")

    @property
    def total_expenses(self):
        return sum((expense.amount for expense in self.expenses), Decimal("0.00"))

    @property
    def net_profit(self):
        return self.gross_revenue - self.total_expenses

    @property
    def gross_per_km(self):
        return self.gross_revenue / self.kilometers if self.kilometers else Decimal("0.00")

    @property
    def cost_per_km(self):
        return self.total_expenses / self.kilometers if self.kilometers else Decimal("0.00")

    @property
    def net_per_km(self):
        return self.net_profit / self.kilometers if self.kilometers else Decimal("0.00")


class Category(db.Model):
    __tablename__ = "categories"
    __table_args__ = (
        db.UniqueConstraint("user_id", "name", name="uq_categories_user_name"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    name = db.Column(db.String(80), nullable=False)
    is_default = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)
    expenses = db.relationship("Expense", back_populates="category", lazy="dynamic")
    user = db.relationship("User", back_populates="categories")


class Expense(db.Model):
    __tablename__ = "expenses"

    id = db.Column(db.Integer, primary_key=True)
    record_id = db.Column(db.Integer, db.ForeignKey("daily_records.id"), nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False, index=True)
    description = db.Column(db.String(180), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    record = db.relationship("DailyRecord", back_populates="expenses")
    category = db.relationship("Category", back_populates="expenses")
