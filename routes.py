from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from database import db, ensure_columns
from models import Customer, Order, Payment, FollowUp
import logging, traceback, datetime

bp = Blueprint("main", __name__)
logger = logging.getLogger("saree_crm.app")

# Helper validators
def coerce_amount(value, default=0.0):
    try:
        if value in (None, ""):
            return float(default)
        return float(str(value).replace(",", "").strip())
    except Exception:
        return float(default)

def validate_order_payload(payload):
    """
    Returns (valid, data_or_errors)
    Enforces: amount numeric, if payment_status == 'Paid' then payment_mode required.
    """
    errors = {}
    data = {}
    data["customer_id"] = int(payload.get("customer_id") or 0)
    data["saree_name"] = payload.get("saree_name", "").strip()
    data["amount"] = coerce_amount(payload.get("amount", 0.0))
    data["order_status"] = payload.get("order_status", "New").strip()
    data["delivery_status"] = payload.get("delivery_status", "Pending").strip()
    data["payment_status"] = payload.get("payment_status", "Pending").strip()
    data["payment_mode"] = payload.get("payment_mode") or None
    data["notes"] = payload.get("notes") or None

    if not data["customer_id"]:
        errors["customer_id"] = "Customer is required."
    if not data["saree_name"]:
        errors["saree_name"] = "Saree name is required."
    if data["payment_status"].lower() == "paid" and not data["payment_mode"]:
        errors["payment_mode"] = "Payment mode required when payment status is Paid."
    return (len(errors)==0, data if not errors else errors)

@bp.route("/")
def dashboard():
    customers_count = Customer.query.count()
    orders_count = Order.query.count()
    due_amount = db.session.query(db.func.sum(Order.amount)).filter(Order.payment_status != "Paid").scalar() or 0.0
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(6).all()
    return render_template("dashboard.html", customers_count=customers_count, orders_count=orders_count,
                           due_amount=due_amount, recent_orders=recent_orders)

# Customers
@bp.route("/customers")
def customers_view():
    customers = Customer.query.order_by(Customer.created_at.desc()).all()
    return render_template("customers.html", customers=customers)

@bp.route("/customers/add", methods=["POST"])
def customers_add():
    try:
        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        email = request.form.get("email", "").strip()
        address = request.form.get("address", "").strip()
        if not name:
            flash("Customer name is required.", "danger")
            return redirect(url_for("main.customers_view"))
        c = Customer(name=name, phone=phone or None, email=email or None, address=address or None)
        db.session.add(c); db.session.commit()
        flash("Customer added.", "success")
    except Exception:
        logger.error(traceback.format_exc())
        flash("Failed to add customer.", "danger")
    return redirect(url_for("main.customers_view"))

# Orders
@bp.route("/orders")
def orders_view():
    orders = Order.query.order_by(Order.created_at.desc()).all()
    customers = {c.id: c for c in Customer.query.all()}
    return render_template("orders.html", orders=orders, customers=customers)

@bp.route("/orders/add", methods=["POST"])
def orders_add():
    try:
        ok, result = validate_order_payload(request.form)
        if not ok:
            for k,v in result.items():
                flash(f"{k}: {v}", "danger")
            return redirect(url_for("main.orders_view"))

        order = Order(**result)
        db.session.add(order)
        db.session.commit()
        flash("Order created.", "success")
    except Exception:
        logger.error(traceback.format_exc())
        flash("Failed to create order.", "danger")
    return redirect(url_for("main.orders_view"))

@bp.route("/orders/<int:order_id>/edit", methods=["POST"])
def orders_edit(order_id):
    try:
        order = Order.query.get_or_404(order_id)
        ok, result = validate_order_payload(request.form)
        if not ok:
            for k,v in result.items():
                flash(f"{k}: {v}", "danger")
            return redirect(url_for("main.orders_view"))
        for k,v in result.items():
            setattr(order, k, v)
        db.session.commit()
        flash("Order updated.", "success")
    except Exception:
        logger.error(traceback.format_exc())
        flash("Failed to update order.", "danger")
    return redirect(url_for("main.orders_view"))

# Payments
@bp.route("/payments")
def payments_view():
    payments = Payment.query.order_by(Payment.received_at.desc()).all()
    customers = {c.id: c for c in Customer.query.all()}
    return render_template("payments.html", payments=payments, customers=customers)

@bp.route("/payments/add", methods=["POST"])
def payments_add():
    try:
        customer_id = int(request.form.get("customer_id") or 0)
        amount = coerce_amount(request.form.get("amount", 0.0))
        mode = request.form.get("mode", "").strip()
        order_id = request.form.get("order_id") or None
        notes = request.form.get("notes") or None
        if not customer_id or amount <= 0 or not mode:
            flash("Customer, amount (>0) and mode are required.", "danger")
            return redirect(url_for("main.payments_view"))
        p = Payment(customer_id=customer_id, amount=amount, mode=mode, order_id=int(order_id) if order_id else None, notes=notes)
        db.session.add(p)
        # If order_id provided, try to auto mark order Paid
        if p.order_id:
            o = Order.query.get(p.order_id)
            if o:
                o.payment_status = "Paid"
                o.payment_mode = p.mode
        db.session.commit()
        flash("Payment recorded.", "success")
    except Exception:
        logger.error(traceback.format_exc())
        flash("Failed to record payment.", "danger")
    return redirect(url_for("main.payments_view"))

# Followups
@bp.route("/followups")
def followups_view():
    followups = FollowUp.query.order_by(FollowUp.follow_date.asc()).all()
    customers = {c.id: c for c in Customer.query.all()}
    return render_template("followups.html", followups=followups, customers=customers)

@bp.route("/followups/add", methods=["POST"])
def followups_add():
    try:
        customer_id = int(request.form.get("customer_id") or 0)
        order_id = request.form.get("order_id") or None
        follow_date = request.form.get("follow_date")
        notes = request.form.get("notes") or None
        if not customer_id or not follow_date:
            flash("Customer and follow date are required.", "danger")
            return redirect(url_for("main.followups_view"))
        dt = datetime.datetime.fromisoformat(follow_date)
        fu = FollowUp(customer_id=customer_id, order_id=int(order_id) if order_id else None, follow_date=dt, notes=notes)
        db.session.add(fu); db.session.commit()
        flash("Follow-up scheduled.", "success")
    except Exception:
        logger.error(traceback.format_exc())
        flash("Failed to schedule follow-up.", "danger")
    return redirect(url_for("main.followups_view"))

# Reports (simple)
@bp.route("/reports")
def reports_view():
    total_customers = Customer.query.count()
    total_orders = Order.query.count()
    total_paid = db.session.query(db.func.sum(Payment.amount)).scalar() or 0.0
    total_due = db.session.query(db.func.sum(Order.amount)).filter(Order.payment_status != "Paid").scalar() or 0.0
    return render_template("reports.html", total_customers=total_customers, total_orders=total_orders,
                           total_paid=total_paid, total_due=total_due)

# Small JSON API endpoints
@bp.route("/api/customers")
def api_customers():
    cs = Customer.query.order_by(Customer.created_at.desc()).limit(100).all()
    return jsonify([c.to_dict() for c in cs])
