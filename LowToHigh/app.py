from flask import Flask, render_template, request, redirect, url_for, session
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import json

from database import get_db_connection, create_db

app = Flask(__name__)
app.secret_key = "your_secret_key"

# გაშვებისას შეამოწმე DB
create_db()

# ---------------------
# In-memory baskets
# ---------------------
baskets = {}

# ---------------------
# Login Required Decorator
# ---------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

# ---------------------
# Login
# ---------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user"] = user["first_name"]
            session["email"] = email
            return redirect(url_for("home"))
        else:
            return render_template("login.html", error="Invalid email or password")
    return render_template("login.html")

# ---------------------
# Registration
# ---------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("firstname")
        lastname = request.form.get("lastname")
        phone = request.form.get("phone")
        email = request.form.get("email")
        password = generate_password_hash(request.form.get("password"))

        conn = get_db_connection()
        existing_user = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()

        if existing_user:
            conn.close()
            return render_template("register.html", error="Email already exists")

        conn.execute(
            "INSERT INTO users (first_name, last_name, phone, email, password) VALUES (?, ?, ?, ?, ?)",
            (name, lastname, phone, email, password)
        )
        conn.commit()
        conn.close()

        baskets[email] = []
        return redirect(url_for("login"))

    return render_template("register.html")

# ---------------------
# Logout
# ---------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ---------------------
# Home
# ---------------------
@app.route("/")
@login_required
def home():
    user_name = session.get("user")
    with open("menu.json", "r", encoding="utf-8") as f:
        menu_items = json.load(f)

    return render_template("home.html", user_name=user_name, menu_items=menu_items)

# ---------------------
# Basket
# ---------------------
@app.route("/add_to_basket/<item_name>/<int:price>/<path:img>")
@login_required
def add_to_basket(item_name, price, img):
    email = session.get("email")
    basket = baskets.get(email, [])
    for item in basket:
        if item["name"] == item_name:
            item["quantity"] += 1
            break
    else:
        basket.append({"name": item_name, "price": price, "quantity": 1, "img": img})
    baskets[email] = basket
    return redirect(url_for("basket"))

@app.route("/update_basket/<item_name>/<action>", methods=["POST"])
@login_required
def update_basket(item_name, action):
    email = session.get("email")
    basket = baskets.get(email, [])
    for item in basket:
        if item["name"] == item_name:
            if action == "increase":
                item["quantity"] += 1
            elif action == "decrease":
                item["quantity"] -= 1
                if item["quantity"] <= 0:
                    basket.remove(item)
            elif action == "remove":
                basket.remove(item)
            break
    baskets[email] = basket
    return redirect(url_for("basket"))

@app.route("/basket")
@login_required
def basket():
    email = session.get("email")
    user_name = session.get("user")
    basket_items = baskets.get(email, [])
    total = sum(item["price"] * item["quantity"] for item in basket_items)
    return render_template("basket.html", user_name=user_name, basket_items=basket_items, total=total)

# ---------------------
# Checkout
# ---------------------
@app.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    email = session.get("email")
    user_name = session.get("user")
    basket_items = baskets.get(email, [])
    total = sum(item["price"] * item["quantity"] for item in basket_items)
    tables = [1,2,3,4,5,6,7,8]

    if request.method == "POST":
        guests = request.form.get("guests")
        date = request.form.get("date")
        time = request.form.get("time")
        table = request.form.get("table")
        return render_template("confirmation.html",
                               user_name=user_name,
                               guests=guests,
                               date=date,
                               time=time,
                               table=table,
                               total=total)
    return render_template("checkout.html",
                           user_name=user_name,
                           basket_items=basket_items,
                           total=total,
                           tables=tables)

# ---------------------
# About / Contact
# ---------------------
@app.route("/about")
@login_required
def about():
    user_name = session.get("user")
    return render_template("about.html", user_name=user_name)

@app.route("/contact")
@login_required
def contact():
    user_name = session.get("user")
    return render_template("contact.html", user_name=user_name)

if __name__ == "__main__":
    app.run(debug=True)
