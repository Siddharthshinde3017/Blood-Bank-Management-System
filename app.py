from flask import Flask, render_template, request, redirect, session, url_for, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = "bloodbank_secret_key"   # session secret key


# ---------- DATABASE CONNECTION ----------
def get_db():
    import os
    
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "blood_bank.db")
    print("🔥 Flask is using this database:", db_path)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


# ---------- HOME PAGE ----------
@app.route("/")
def home():
    return render_template("home.html", title="Home")


# ---------- DONOR REGISTRATION ----------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        blood_group = request.form["blood_group"]
        mobile = request.form["mobile"]
        email = request.form["email"]
        password = request.form["password"]

        hashed_pass = generate_password_hash(password)

        conn = get_db()
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO donors(name, blood_group, mobile, email, password) VALUES (?, ?, ?, ?, ?)",
                (name, blood_group, mobile, email, hashed_pass)
            )
            conn.commit()
            flash("✅ Registration successful! Please login.", "success")
            return redirect(url_for("login"))

        except sqlite3.IntegrityError:
            flash("❌ Email already exists. Try another.", "danger")
            return redirect(url_for("register"))

        finally:
            conn.close()

    return render_template("register.html", title="Register")


# ---------- DONOR LOGIN ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()
        user = conn.execute("SELECT * FROM donors WHERE email = ?", (email,)).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            flash(f"Welcome {user['name']}!", "success")
            return redirect(url_for("user_dashboard"))
        else:
            flash("❌ Invalid email or password", "danger")
            return redirect(url_for("login"))

    return render_template("login.html", title="Login")


# ---------- USER DASHBOARD ----------
@app.route("/dashboard")
@login_required
def user_dashboard():
    conn = get_db()
    user = conn.execute("SELECT * FROM donors WHERE id = ?", (session["user_id"],)).fetchone()
    conn.close()
    return render_template("dashboard.html", user=user)


# ---------- BLOOD REQUEST ----------
@app.route("/request-blood", methods=["GET", "POST"])
@login_required
def request_blood():
    if request.method == "POST":
        blood_group = request.form["blood_group"]
        units = request.form["units"]
        request_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = get_db()
        conn.execute(
            "INSERT INTO blood_requests(donor_id, blood_group, units, request_date) VALUES (?, ?, ?, ?)",
            (session["user_id"], blood_group, units, request_date)
        )
        conn.commit()
        conn.close()

        flash("✅ Blood request submitted successfully!", "success")
        return redirect(url_for("user_dashboard"))

    return render_template("request_blood.html")


# ---------- DONATE BLOOD ----------
@app.route("/donate", methods=["GET", "POST"])
@login_required
def donate():
    if request.method == "POST":
        units = request.form["units"]
        location = request.form["location"]
        donation_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = get_db()
        conn.execute(
            "INSERT INTO donation_history(donor_id, donation_date, units, location) VALUES(?,?,?,?)",
            (session["user_id"], donation_date, units, location)
        )
        conn.execute("UPDATE donors SET last_donation = ? WHERE id = ?", (donation_date, session["user_id"]))
        conn.commit()
        conn.close()

        flash("✅ Thank you for donating blood!", "success")
        return redirect(url_for("user_dashboard"))

    return render_template("donate.html")


# ---------- BLOOD STOCK ----------
@app.route("/blood-stock")
@login_required
def blood_stock():
    conn = get_db()
    stock = conn.execute("""
        SELECT blood_group, SUM(units) AS total_units
        FROM donation_history
        GROUP BY blood_group
    """).fetchall()
    conn.close()
    return render_template("blood_stock.html", stock=stock)


# ---------- PROFILE ----------
@app.route("/profile")
@login_required
def profile():
    conn = get_db()
    user = conn.execute("SELECT * FROM donors WHERE id = ?", (session["user_id"],)).fetchone()
    conn.close()
    return render_template("profile.html", user=user)


# ---------- USER LOGOUT ----------
@app.route("/logout")
@login_required
def logout():
    session.clear()
    flash("Logged out successfully!", "info")
    return redirect(url_for("home"))


# ---------- ADMIN LOGIN ----------
@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        admin_data = conn.execute("SELECT * FROM admin WHERE username = ?", (username,)).fetchone()
        conn.close()

        if admin_data and check_password_hash(admin_data["password"], password):
            session["admin_logged_in"] = True
            session["admin_username"] = username
            flash(f"Welcome Admin {username}!", "success")
            return redirect(url_for("admin_dashboard"))
        else:
            flash("❌ Invalid Admin Credentials", "danger")
            return redirect(url_for("admin_login"))

    return render_template("admin_login.html", title="Admin Login")


# ---------- ADMIN DASHBOARD ----------
@app.route("/admin/dashboard")
@admin_login_required
def admin_dashboard():
    conn = get_db()
    total_donors = conn.execute("SELECT COUNT(*) AS count FROM donors").fetchone()["count"]
    total_units = conn.execute("SELECT SUM(units) AS total FROM donation_history").fetchone()["total"] or 0
    total_requests = conn.execute("SELECT COUNT(*) AS count FROM blood_requests").fetchone()["count"]
    conn.close()

    return render_template(
        "admin_dashboard.html",
        total_donors=total_donors,
        total_units=total_units,
        total_requests=total_requests
    )


# ---------- ADMIN MANAGEMENT PAGES ----------
@app.route("/admin/manage-donors")
@admin_login_required
def manage_donors():
    return render_template("manage_donors.html")


@app.route("/admin/manage-requests")
@admin_login_required
def manage_requests():
    return render_template("manage_requests.html")


@app.route("/admin/manage-stock")
@admin_login_required
def manage_stock():
    return render_template("manage_stock.html")


# ---------- ADMIN LOGOUT ----------
@app.route("/admin/logout")
@admin_login_required
def admin_logout():
    session.clear()
    flash("Admin logged out successfully!", "info")
    return redirect(url_for("admin_login"))




# ---------- START SERVER ----------
if __name__ == "__main__":
    app.run(debug=True, port=1234)

