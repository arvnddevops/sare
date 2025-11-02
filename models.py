from datetime import datetime
from database import db
from sqlalchemy import Integer, String, DateTime, Float, Text, Boolean

class Customer(db.Model):
    __tablename__ = "customers"
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(200), nullable=False)
    phone = db.Column(String(40), nullable=True)
    email = db.Column(String(200), nullable=True)
    address = db.Column(Text, nullable=True)
    created_at = db.Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return dict(id=self.id, name=self.name, phone=self.phone, email=self.email, address=self.address)

class Order(db.Model):
    __tablename__ = "orders"
    id = db.Column(Integer, primary_key=True)
    customer_id = db.Column(Integer, nullable=False, index=True)
    saree_name = db.Column(String(200), nullable=False)
    amount = db.Column(Float, nullable=False, default=0.0)
    order_status = db.Column(String(50), nullable=False, default="New")  # e.g., New, Confirmed, Delivered, Cancelled
    delivery_status = db.Column(String(50), nullable=False, default="Pending") # e.g., Pending, Shipped, Delivered
    payment_status = db.Column(String(50), nullable=False, default="Pending") # Pending, Paid, Refund
    payment_mode = db.Column(String(50), nullable=True) # Cash, Card, UPI, etc.
    notes = db.Column(Text, nullable=True)
    created_at = db.Column(DateTime, default=datetime.utcnow)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Payment(db.Model):
    __tablename__ = "payments"
    id = db.Column(Integer, primary_key=True)
    order_id = db.Column(Integer, nullable=True, index=True)
    customer_id = db.Column(Integer, nullable=False, index=True)
    amount = db.Column(Float, nullable=False, default=0.0)
    mode = db.Column(String(50), nullable=False)  # Cash, Card, UPI
    received_at = db.Column(DateTime, default=datetime.utcnow)
    notes = db.Column(Text, nullable=True)

class FollowUp(db.Model):
    __tablename__ = "followups"
    id = db.Column(Integer, primary_key=True)
    customer_id = db.Column(Integer, nullable=False, index=True)
    order_id = db.Column(Integer, nullable=True, index=True)
    follow_date = db.Column(DateTime, nullable=False)
    done = db.Column(Boolean, default=False)
    notes = db.Column(Text, nullable=True)
    created_at = db.Column(DateTime, default=datetime.utcnow)
