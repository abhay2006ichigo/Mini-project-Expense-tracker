"""
Flask Application for Personal Expense Tracker & Budget Management with Multi-User Isolation.
"""

import os
import calendar
import secrets
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional
from functools import wraps
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash

import database

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static")
)
app.secret_key = os.environ.get("SECRET_KEY", "expense-tracker-secret-key-2026")

# Top-level WSGI aliases for Vercel, Gunicorn, and other WSGI servers
application = app

# Category color palette matching design system and screenshots
CATEGORY_COLORS = {
    "Entertainment": "#8b5cf6",  # Purple
    "Food": "#ef4444",           # Red/Coral
    "Transport": "#3b82f6",      # Blue
    "Shopping": "#f97316",       # Orange
    "Bills": "#10b981",          # Green
    "Health": "#06b6d4",         # Cyan/Teal
    "Education": "#ec4899",      # Pink
    "Travel": "#0ea5e9",         # Sky Blue
    "Other": "#94a3b8"           # Gray
}

CATEGORY_ICONS = {
    "Entertainment": "film",
    "Food": "utensils",
    "Transport": "car",
    "Shopping": "shopping-bag",
    "Bills": "receipt",
    "Health": "heart-pulse",
    "Education": "graduation-cap",
    "Travel": "plane",
    "Other": "tag"
}

CATEGORY_BG_CLASSES = {
    "Entertainment": "cat-bg-entertainment",
    "Food": "cat-bg-food",
    "Transport": "cat-bg-transport",
    "Shopping": "cat-bg-shopping",
    "Bills": "cat-bg-bills",
    "Health": "cat-bg-health",
    "Education": "cat-bg-education",
    "Travel": "cat-bg-travel",
    "Other": "cat-bg-other"
}

def format_inr(amount: float) -> str:
    """Formats a float into Indian Rupee style string (e.g. ₹19,824)."""
    is_negative = amount < 0
    abs_amt = abs(round(amount))
    s = str(abs_amt)
    if len(s) <= 3:
        res = s
    else:
        last3 = s[-3:]
        remaining = s[:-3]
        groups = []
        while len(remaining) > 2:
            groups.insert(0, remaining[-2:])
            remaining = remaining[:-2]
        if remaining:
            groups.insert(0, remaining)
        res = ",".join(groups) + "," + last3

    prefix = "-₹" if is_negative else "₹"
    return f"{prefix}{res}"

def format_compact_inr(amount: float) -> str:
    """Formats a number compactly (e.g. ₹1.2k, ₹30k)."""
    abs_amt = abs(amount)
    prefix = "-₹" if amount < 0 else "₹"
    if abs_amt >= 10000000:
        return f"{prefix}{abs_amt/10000000:.1f}Cr"
    elif abs_amt >= 100000:
        return f"{prefix}{abs_amt/100000:.1f}L"
    elif abs_amt >= 1000:
        return f"{prefix}{abs_amt/1000:.1f}k"
    else:
        return f"{prefix}{int(abs_amt)}"

# Jinja template filters
@app.template_filter('inr')
def inr_filter(value):
    try:
        return format_inr(float(value))
    except (ValueError, TypeError):
        return f"₹{value}"

@app.template_filter('compact_inr')
def compact_inr_filter(value):
    try:
        return format_compact_inr(float(value))
    except (ValueError, TypeError):
        return f"₹{value}"

# Initialize DB on start safely
try:
    with app.app_context():
        database.init_db(seed_sample_data=True)
except Exception as e:
    app.logger.warning(f"Database initialization deferred: {e}")

@app.route("/health")
def health_check():
    """Lightweight liveness probe used by hosting platforms."""
    try:
        database.get_db_connection().close()
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        app.logger.error(f"Health check failed: {e}")
        return jsonify({"status": "error"}), 503

@app.before_request
def ensure_database():
    """Ensure database tables exist in serverless environments."""
    if not getattr(app, "_db_initialized", False):
        try:
            database.init_db(seed_sample_data=True)
            app._db_initialized = True
        except Exception as e:
            app.logger.warning(f"Database auto-init check: {e}")

# ----------------- Auth Helpers ----------------- #

def get_current_user() -> Optional[Dict[str, Any]]:
    user_id = session.get("user_id")
    if not user_id:
        return None
    return database.get_user_by_id(user_id)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session or not database.get_user_by_id(session["user_id"]):
            if request.path.startswith("/api/"):
                return jsonify({"success": False, "error": "Unauthorized. Please log in."}), 401
            return redirect(url_for("login_view"))
        return f(*args, **kwargs)
    return decorated_function

# ----------------- Authentication Routes ----------------- #

@app.route("/login", methods=["GET", "POST"])
def login_view():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = database.get_user_by_username(username)
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            flash(f"Welcome back, {user['username']}!", "success")
            return redirect(url_for("dashboard_view"))

        flash("Invalid username or password.", "error")

    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register_view():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not username or len(username) < 2:
            flash("Username must be at least 2 characters.", "error")
            return render_template("register.html")

        if not password or len(password) < 4:
            flash("Password must be at least 4 characters.", "error")
            return render_template("register.html")

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template("register.html")

        existing_user = database.get_user_by_username(username)
        if existing_user:
            flash("Username already taken. Please choose another.", "error")
            return render_template("register.html")

        password_hash = generate_password_hash(password)
        new_user_id = database.create_user(username, password_hash)

        # Set initial budget for new user
        now = datetime.now()
        database.set_budget_for_month(new_user_id, 30000.0, now.month, now.year)

        # Log new user in automatically with their brand new empty expense list
        session.clear()
        session["user_id"] = new_user_id
        session["username"] = username.lower()
        flash(f"Welcome, {username}! Your fresh expense list is ready.", "success")
        return redirect(url_for("dashboard_view"))

    return render_template("register.html")

@app.route("/login-demo")
def login_demo():
    """Quick login as demo user with pre-filled sample data."""
    demo_user = database.get_user_by_username("demo")
    if not demo_user:
        database.init_db(seed_sample_data=True)
        demo_user = database.get_user_by_username("demo")

    if demo_user:
        session.clear()
        session["user_id"] = demo_user["id"]
        session["username"] = "demo"
        flash("Logged in to Demo account.", "success")
    return redirect(url_for("dashboard_view"))

@app.route("/guest")
def guest_mode():
    """Instantly creates a fresh guest user with a brand new empty expense list."""
    random_suffix = secrets.token_hex(3)
    guest_username = f"guest_{random_suffix}"
    pw_hash = generate_password_hash("guest123")
    new_user_id = database.create_user(guest_username, pw_hash)

    now = datetime.now()
    database.set_budget_for_month(new_user_id, 30000.0, now.month, now.year)

    session.clear()
    session["user_id"] = new_user_id
    session["username"] = guest_username
    flash(f"Welcome! Started a new personal expense tracker for {guest_username}.", "success")
    return redirect(url_for("dashboard_view"))

@app.route("/logout")
def logout_view():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login_view"))

# ----------------- Page Views (Protected) ----------------- #

@app.route("/")
@app.route("/dashboard")
@login_required
def dashboard_view():
    now = datetime.now()
    cur_month_name = now.strftime("%B")
    cur_year = now.year
    user = get_current_user()
    return render_template("dashboard.html", current_month=cur_month_name, current_year=cur_year, current_user=user)

@app.route("/transactions")
@login_required
def transactions_view():
    user = get_current_user()
    return render_template("transactions.html", current_user=user)

@app.route("/budget")
@login_required
def budget_view():
    now = datetime.now()
    cur_month_name = now.strftime("%B")
    cur_year = now.year
    user = get_current_user()
    return render_template("budget.html", current_month=cur_month_name, current_year=cur_year, current_user=user)

# ----------------- Form Fallbacks (Protected) ----------------- #

@app.route("/add-transaction", methods=["POST"])
@login_required
def add_transaction_form():
    user_id = session["user_id"]
    amount_str = request.form.get("amount", "").strip()
    category = request.form.get("category", "Other").strip()
    note = request.form.get("note", "").strip()
    tx_date = request.form.get("transaction_date", "").strip()

    if not tx_date:
        tx_date = date.today().isoformat()

    try:
        amount = float(amount_str)
        if amount <= 0:
            flash("Amount must be greater than zero.", "error")
            return redirect(request.referrer or url_for("dashboard_view"))
        database.add_transaction(user_id, amount, category, note, tx_date)
        flash("Transaction added successfully!", "success")
    except ValueError:
        flash("Invalid amount entered.", "error")

    return redirect(request.referrer or url_for("dashboard_view"))

@app.route("/edit-transaction/<int:tx_id>", methods=["POST"])
@login_required
def edit_transaction_form(tx_id):
    user_id = session["user_id"]
    amount_str = request.form.get("amount", "").strip()
    category = request.form.get("category", "Other").strip()
    note = request.form.get("note", "").strip()
    tx_date = request.form.get("transaction_date", "").strip()

    try:
        amount = float(amount_str)
        if amount <= 0:
            flash("Amount must be greater than zero.", "error")
            return redirect(request.referrer or url_for("transactions_view"))
        success = database.update_transaction(user_id, tx_id, amount, category, note, tx_date)
        if success:
            flash("Transaction updated successfully!", "success")
        else:
            flash("Transaction not found.", "error")
    except ValueError:
        flash("Invalid amount entered.", "error")

    return redirect(request.referrer or url_for("transactions_view"))

@app.route("/delete-transaction/<int:tx_id>", methods=["POST"])
@login_required
def delete_transaction_form(tx_id):
    user_id = session["user_id"]
    success = database.delete_transaction(user_id, tx_id)
    if success:
        flash("Transaction deleted successfully!", "success")
    else:
        flash("Failed to delete transaction.", "error")
    return redirect(request.referrer or url_for("transactions_view"))

# ----------------- REST / JSON API Endpoints (Protected) ----------------- #

@app.route("/api/dashboard", methods=["GET"])
@login_required
def api_dashboard():
    user_id = session["user_id"]
    period = request.args.get("period", "30D").upper()
    now = datetime.now()
    cur_month = now.month
    cur_year = now.year
    cur_day = now.day

    # 1. Total spent this month for current user
    cur_month_spent = database.get_monthly_spent(user_id, cur_month, cur_year)

    # Previous month calculations for current user
    prev_month = 12 if cur_month == 1 else cur_month - 1
    prev_year = cur_year - 1 if cur_month == 1 else cur_year
    prev_month_spent = database.get_monthly_spent(user_id, prev_month, prev_year)

    # Month over month spent percentage change
    if prev_month_spent > 0:
        total_change_pct = round(((cur_month_spent - prev_month_spent) / prev_month_spent) * 100, 1)
    else:
        total_change_pct = 0.0 if cur_month_spent == 0 else 100.0

    # 2. Daily Average
    days_elapsed = max(1, cur_day)
    cur_daily_avg = cur_month_spent / days_elapsed

    _, prev_month_days = calendar.monthrange(prev_year, prev_month)
    prev_daily_avg = prev_month_spent / max(1, prev_month_days)

    if prev_daily_avg > 0:
        daily_avg_change_pct = round(((cur_daily_avg - prev_daily_avg) / prev_daily_avg) * 100, 1)
    else:
        daily_avg_change_pct = 0.0 if cur_daily_avg == 0 else 100.0

    # 3. Top Category
    cat_spend_list = database.get_category_spending_for_month(user_id, cur_month, cur_year)
    if cat_spend_list and cur_month_spent > 0:
        top_cat_item = cat_spend_list[0]
        top_cat_name = top_cat_item["category"]
        top_cat_amount = top_cat_item["total"]
        top_cat_pct = round((top_cat_amount / cur_month_spent) * 100, 1)
    else:
        top_cat_name = "None"
        top_cat_amount = 0.0
        top_cat_pct = 0.0

    # 4. Budget & Remaining
    budget_limit = database.get_budget_for_month(user_id, cur_month, cur_year)
    remaining_budget = budget_limit - cur_month_spent
    budget_used_pct = round((cur_month_spent / budget_limit) * 100, 1) if budget_limit > 0 else 0.0

    all_recent_txs = database.get_all_transactions(user_id)

    # 5. Breakdown Time-Series based on period
    breakdown_data = generate_breakdown_series(user_id, period, now)

    # 6. Category share for donut chart
    category_share = []
    for item in cat_spend_list:
        cat = item["category"]
        tot = item["total"]
        pct = round((tot / cur_month_spent) * 100, 1) if cur_month_spent > 0 else 0.0
        category_share.append({
            "category": cat,
            "total": tot,
            "formatted_total": format_inr(tot),
            "percentage": pct,
            "color": CATEGORY_COLORS.get(cat, "#94a3b8"),
            "icon": CATEGORY_ICONS.get(cat, "tag"),
            "bg_class": CATEGORY_BG_CLASSES.get(cat, "cat-bg-other")
        })

    # 7. Recent Transactions (latest 10) grouped by date
    recent_raw = all_recent_txs[:10]
    recent_grouped = group_transactions_by_date(recent_raw)

    return jsonify({
        "current_month_name": now.strftime("%B"),
        "current_year": cur_year,
        "summary": {
            "total_spent": cur_month_spent,
            "formatted_total_spent": format_inr(cur_month_spent),
            "total_change_pct": total_change_pct,
            "total_change_dir": "up" if total_change_pct > 0 else "down",
            "daily_avg": round(cur_daily_avg),
            "formatted_daily_avg": format_inr(round(cur_daily_avg)),
            "daily_avg_change_pct": daily_avg_change_pct,
            "daily_avg_change_dir": "up" if daily_avg_change_pct > 0 else "down",
            "top_category": top_cat_name,
            "top_category_amount": top_cat_amount,
            "top_category_pct": top_cat_pct,
            "monthly_budget": budget_limit,
            "formatted_monthly_budget": format_inr(budget_limit),
            "remaining_budget": remaining_budget,
            "formatted_remaining_budget": format_inr(remaining_budget),
            "budget_used_pct": budget_used_pct,
            "sparklines": generate_summary_sparklines(all_recent_txs)
        },
        "breakdown": breakdown_data,
        "category_share": category_share,
        "recent_grouped": recent_grouped,
        "total_transactions_count": len(all_recent_txs)
    })

def generate_breakdown_series(user_id: int, period: str, now: datetime) -> Dict[str, Any]:
    all_txs = database.get_all_transactions(user_id)

    tx_by_date: Dict[str, List[Dict[str, Any]]] = {}
    for tx in all_txs:
        d = tx["transaction_date"]
        if d not in tx_by_date:
            tx_by_date[d] = []
        tx_by_date[d].append(tx)

    labels = []
    data_points = []
    max_total = 0.0

    if period == "7D":
        for i in range(6, -1, -1):
            day_dt = now - timedelta(days=i)
            day_str = day_dt.strftime("%Y-%m-%d")
            label = day_dt.strftime("%a")
            labels.append(label)

            cat_totals = {}
            day_total = 0.0
            for tx in tx_by_date.get(day_str, []):
                cat = tx["category"]
                cat_totals[cat] = cat_totals.get(cat, 0.0) + float(tx["amount"])
                day_total += float(tx["amount"])

            if day_total > max_total:
                max_total = day_total

            data_points.append({
                "key": day_str,
                "label": label,
                "categories": cat_totals,
                "total": day_total
            })

    elif period == "30D":
        for i in range(29, -1, -1):
            day_dt = now - timedelta(days=i)
            day_str = day_dt.strftime("%Y-%m-%d")
            label = str(day_dt.day) if (i % 3 == 0 or i == 0) else ""
            labels.append(str(day_dt.day))

            cat_totals = {}
            day_total = 0.0
            for tx in tx_by_date.get(day_str, []):
                cat = tx["category"]
                cat_totals[cat] = cat_totals.get(cat, 0.0) + float(tx["amount"])
                day_total += float(tx["amount"])

            if day_total > max_total:
                max_total = day_total

            data_points.append({
                "key": day_str,
                "label": str(day_dt.day),
                "display_label": label,
                "categories": cat_totals,
                "total": day_total
            })

    elif period == "6M":
        for i in range(5, -1, -1):
            m = now.month - i
            y = now.year
            while m <= 0:
                m += 12
                y -= 1
            month_label = calendar.month_abbr[m]
            prefix = f"{y:04d}-{m:02d}-"
            labels.append(month_label)

            cat_totals = {}
            month_total = 0.0
            for tx in all_txs:
                if tx["transaction_date"].startswith(prefix):
                    cat = tx["category"]
                    cat_totals[cat] = cat_totals.get(cat, 0.0) + float(tx["amount"])
                    month_total += float(tx["amount"])

            if month_total > max_total:
                max_total = month_total

            data_points.append({
                "key": f"{y}-{m:02d}",
                "label": month_label,
                "display_label": month_label,
                "categories": cat_totals,
                "total": month_total
            })

    elif period == "YTD":
        for m in range(1, now.month + 1):
            month_label = calendar.month_abbr[m]
            prefix = f"{now.year:04d}-{m:02d}-"
            labels.append(month_label)

            cat_totals = {}
            month_total = 0.0
            for tx in all_txs:
                if tx["transaction_date"].startswith(prefix):
                    cat = tx["category"]
                    cat_totals[cat] = cat_totals.get(cat, 0.0) + float(tx["amount"])
                    month_total += float(tx["amount"])

            if month_total > max_total:
                max_total = month_total

            data_points.append({
                "key": f"{now.year}-{m:02d}",
                "label": month_label,
                "display_label": month_label,
                "categories": cat_totals,
                "total": month_total
            })

    return {
        "period": period,
        "labels": labels,
        "data_points": data_points,
        "max_total": max_total,
        "category_colors": CATEGORY_COLORS
    }

def generate_summary_sparklines(all_txs: List[Dict[str, Any]]) -> Dict[str, List[float]]:
    today = date.today()
    spent_series = []
    for i in range(6, -1, -1):
        d = (today - timedelta(days=i)).isoformat()
        amt = sum(t["amount"] for t in all_txs if t["transaction_date"] == d)
        spent_series.append(amt)

    if all(v == 0 for v in spent_series):
        spent_series = [10, 40, 20, 80, 50, 90, 30]

    return {
        "spent": spent_series,
        "avg": [v * 0.8 for v in spent_series],
        "top": [v * 0.6 for v in spent_series],
        "budget": [max(0, 100 - v * 0.5) for v in spent_series]
    }

def group_transactions_by_date(transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    day_totals: Dict[str, float] = {}

    for tx in transactions:
        d_str = tx["transaction_date"]
        if d_str not in grouped:
            grouped[d_str] = []
            day_totals[d_str] = 0.0

        cat = tx["category"]
        tx_item = dict(tx)
        tx_item["color"] = CATEGORY_COLORS.get(cat, "#94a3b8")
        tx_item["icon"] = CATEGORY_ICONS.get(cat, "tag")
        tx_item["bg_class"] = CATEGORY_BG_CLASSES.get(cat, "cat-bg-other")
        tx_item["formatted_amount"] = format_inr(float(tx["amount"]))

        grouped[d_str].append(tx_item)
        day_totals[d_str] += float(tx["amount"])

    result = []
    sorted_dates = sorted(grouped.keys(), reverse=True)
    for d_str in sorted_dates:
        try:
            dt = datetime.strptime(d_str, "%Y-%m-%d")
            date_label = dt.strftime("%a, %b %-d").upper()
        except ValueError:
            date_label = d_str

        result.append({
            "raw_date": d_str,
            "date_label": date_label,
            "day_total": day_totals[d_str],
            "formatted_day_total": format_inr(day_totals[d_str]),
            "transactions": grouped[d_str]
        })

    return result

@app.route("/api/transactions", methods=["GET"])
@login_required
def api_transactions():
    user_id = session["user_id"]
    category = request.args.get("category", "All")
    search = request.args.get("search", "")
    date_from = request.args.get("date_from", "")
    date_to = request.args.get("date_to", "")

    txs = database.get_all_transactions(user_id, category=category, search=search, date_from=date_from, date_to=date_to)
    total_spent = sum(t["amount"] for t in txs)
    grouped = group_transactions_by_date(txs)

    return jsonify({
        "entries_count": len(txs),
        "total_spent": total_spent,
        "formatted_total_spent": format_inr(total_spent),
        "grouped_transactions": grouped
    })

@app.route("/api/budget", methods=["GET"])
@login_required
def api_budget():
    user_id = session["user_id"]
    now = datetime.now()
    month = int(request.args.get("month", now.month))
    year = int(request.args.get("year", now.year))

    monthly_limit = database.get_budget_for_month(user_id, month, year)
    total_spent = database.get_monthly_spent(user_id, month, year)
    remaining = monthly_limit - total_spent
    used_pct = round((total_spent / monthly_limit) * 100, 1) if monthly_limit > 0 else 0.0

    cat_breakdown_raw = database.get_category_spending_for_month(user_id, month, year)
    cat_breakdown = []
    for c in cat_breakdown_raw:
        cat = c["category"]
        tot = c["total"]
        pct = round((tot / total_spent) * 100, 1) if total_spent > 0 else 0.0
        cat_breakdown.append({
            "category": cat,
            "total": tot,
            "formatted_total": format_inr(tot),
            "percentage": pct,
            "color": CATEGORY_COLORS.get(cat, "#94a3b8"),
            "icon": CATEGORY_ICONS.get(cat, "tag"),
            "bg_class": CATEGORY_BG_CLASSES.get(cat, "cat-bg-other")
        })

    return jsonify({
        "month": month,
        "year": year,
        "month_name": calendar.month_name[month],
        "monthly_limit": monthly_limit,
        "formatted_monthly_limit": format_inr(monthly_limit),
        "total_spent": total_spent,
        "formatted_total_spent": format_inr(total_spent),
        "remaining": remaining,
        "formatted_remaining": format_inr(remaining),
        "used_pct": used_pct,
        "categories_breakdown": cat_breakdown
    })

@app.route("/api/add-transaction", methods=["POST"])
@login_required
def api_add_transaction():
    user_id = session["user_id"]
    data = request.get_json(silent=True) or request.form
    try:
        amount = float(data.get("amount", 0))
        if amount <= 0:
            return jsonify({"success": False, "error": "Amount must be greater than zero."}), 400
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "Invalid amount."}), 400

    category = str(data.get("category", "Other")).strip()
    if not category:
        category = "Other"

    note = data.get("note", "")
    if note is not None:
        note = str(note).strip()

    tx_date = data.get("transaction_date", "")
    if not tx_date or not str(tx_date).strip():
        tx_date = date.today().isoformat()
    else:
        tx_date = str(tx_date).strip()

    try:
        datetime.strptime(tx_date, "%Y-%m-%d")
    except ValueError:
        return jsonify({"success": False, "error": "Invalid date format. Use YYYY-MM-DD."}), 400

    new_id = database.add_transaction(user_id, amount, category, note, tx_date)
    created = database.get_transaction_by_id(user_id, new_id)

    return jsonify({
        "success": True,
        "message": "Spend logged successfully!",
        "transaction": created
    }), 201

@app.route("/api/update-transaction/<int:tx_id>", methods=["PUT", "POST"])
@login_required
def api_update_transaction(tx_id):
    user_id = session["user_id"]
    data = request.get_json(silent=True) or request.form
    try:
        amount = float(data.get("amount", 0))
        if amount <= 0:
            return jsonify({"success": False, "error": "Amount must be greater than zero."}), 400
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "Invalid amount."}), 400

    category = str(data.get("category", "Other")).strip()
    note = str(data.get("note", "")).strip()
    tx_date = str(data.get("transaction_date", date.today().isoformat())).strip()

    try:
        datetime.strptime(tx_date, "%Y-%m-%d")
    except ValueError:
        return jsonify({"success": False, "error": "Invalid date format."}), 400

    success = database.update_transaction(user_id, tx_id, amount, category, note, tx_date)
    if not success:
        return jsonify({"success": False, "error": "Transaction not found."}), 404

    updated = database.get_transaction_by_id(user_id, tx_id)
    return jsonify({
        "success": True,
        "message": "Transaction updated successfully!",
        "transaction": updated
    })

@app.route("/api/delete-transaction/<int:tx_id>", methods=["DELETE", "POST"])
@login_required
def api_delete_transaction(tx_id):
    user_id = session["user_id"]
    success = database.delete_transaction(user_id, tx_id)
    if not success:
        return jsonify({"success": False, "error": "Transaction not found or already deleted."}), 404
    return jsonify({"success": True, "message": "Transaction deleted successfully!", "id": tx_id})

@app.route("/api/update-budget", methods=["POST"])
@login_required
def api_update_budget():
    user_id = session["user_id"]
    data = request.get_json(silent=True) or request.form
    try:
        limit = float(data.get("monthly_limit", 0))
        if limit < 0:
            return jsonify({"success": False, "error": "Budget limit cannot be negative."}), 400
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "Invalid budget limit."}), 400

    now = datetime.now()
    month = int(data.get("month", now.month))
    year = int(data.get("year", now.year))

    database.set_budget_for_month(user_id, limit, month, year)
    return jsonify({
        "success": True,
        "message": "Monthly budget updated successfully!",
        "monthly_limit": limit,
        "formatted_monthly_limit": format_inr(limit)
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    host = os.environ.get("HOST", "0.0.0.0")
    debug = os.environ.get("FLASK_DEBUG", "0").lower() in ("1", "true", "yes")
    print(f" * Running Expense Tracker on http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)

