from datetime import datetime, timezone
from decimal import Decimal

from .extensions import db


def utc_now():
    return datetime.now(timezone.utc)


class DailyRecord(db.Model):
    __tablename__ = "daily_records"

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, unique=True, nullable=False, index=True)
    gross_revenue = db.Column(db.Numeric(12, 2), nullable=False)
    kilometers = db.Column(db.Numeric(10, 2), nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    expenses = db.relationship(
        "Expense", back_populates="record", cascade="all, delete-orphan", lazy="selectin"
    )

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

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    is_default = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)
    expenses = db.relationship("Expense", back_populates="category", lazy="dynamic")


class Expense(db.Model):
    __tablename__ = "expenses"

    id = db.Column(db.Integer, primary_key=True)
    record_id = db.Column(db.Integer, db.ForeignKey("daily_records.id"), nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False, index=True)
    description = db.Column(db.String(180), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    record = db.relationship("DailyRecord", back_populates="expenses")
    category = db.relationship("Category", back_populates="expenses")
