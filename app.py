from flask import Flask, render_template, request, redirect, session, url_for,flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

from datetime import datetime

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
            cur.execute("INSERT INTO donors(name, blood_group, mobile, email, password) VALUES (?, ?, ?, ?, ?)",
                        (name, blood_group, mobile, email, hashed_pass))
            conn.commit()
            conn.close()
            return redirect(url_for("login"))

        except:
            return "❌ Email already exists. Try another."

    return render_template("register.html", title="Register")


# ---------- DONOR LOGIN ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM donors WHERE email = ?", (email,))
        user = cur.fetchone()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            return redirect(url_for("user_dashboard"))
        else:
            return "❌ Invalid email or password"

    return render_template("login.html", title="Login")


# ----------------- User Dashboard -----------------
@app.route("/dashboard")
def user_dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    user = conn.execute("SELECT * FROM donors WHERE id = ?", (session['user_id'],)).fetchone()
    conn.close()
    return render_template("dashboard.html", user=user)

@app.route("/request-blood", methods=["GET", "POST"])
def request_blood():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        blood_group = request.form["blood_group"]
        units = request.form["units"]
        request_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = get_db()
        conn.execute(
            "INSERT INTO blood_requests(donor_id, blood_group, units, request_date) VALUES(?,?,?,?)",
            (session["user_id"], blood_group, units, request_date)
        )
        conn.commit()
        conn.close()
        flash("Blood request submitted successfully!", "success")
        return redirect(url_for("dashboard"))

    return render_template("request_blood.html")

# ---------------- DONATE BLOOD ----------------
@app.route("/donate", methods=["GET", "POST"])
def donate():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        units = request.form["units"]
        location = request.form["location"]
        donation_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = get_db()
        conn.execute(
            "INSERT INTO donation_history(donar_id, donation_date, units, location) VALUES(?,?,?,?)",
            (session["user_id"], donation_date, units, location)
        )
        # Optional: update last_donation in donors table
        conn.execute("UPDATE donors SET last_donation = ? WHERE id = ?", (donation_date, session["user_id"]))
        conn.commit()
        conn.close()
        flash("Thank you for donating blood!", "success")
        return redirect(url_for("dashboard"))

    return render_template("donate.html")

# ---------------- BLOOD STOCK ----------------
@app.route("/blood-stock")
def blood_stock():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    # Example: count total units per blood group
    stock = conn.execute("""
        SELECT blood_group, SUM(units) as total_units
        FROM donation_history
        GROUP BY blood_group
    """).fetchall()
    conn.close()
    return render_template("blood_stock.html", stock=stock)

# ---------------- PROFILE ----------------
@app.route("/profile")
def profile():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    user = conn.execute("SELECT * FROM donors WHERE id = ?", (session["user_id"],)).fetchone()
    conn.close()
    return render_template("profile.html", user=user)


# ---------- USER LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ---------- ADMIN LOGIN ----------
@app.route("/admin", methods=["GET", "POST"])
def admin():
    # Show admin login page
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM admin WHERE username=?", (username,))
        admin = cur.fetchone()

        if admin and admin["password"] == password:
            session["admin_logged_in"] = True
            session["admin_username"] = username
            return redirect(url_for("admin_dashboard"))
        else:
            return "❌ Invalid Admin Credentials"

    return render_template("admin_login.html", title="Admin Login")


# ---------- ADMIN DASHBOARD ----------
@app.route("/admin/dashboard")
def admin_dashboard():

    if not session.get("admin_logged_in"):
        return redirect("/admin")

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM donors")
    donors = cur.fetchall()

    return render_template("admin_dashboard.html",
                           donors=len(donors),
                           donor_list=donors,
                           units=120,
                           title="Admin Panel")

@app.route('/admin/manage-donors')
def manage_donors():
    return render_template('manage_donors.html')

@app.route('/admin/manage-requests')
def manage_requests():
    return render_template('manage_requests.html')

@app.route('/admin/manage-stock')
def manage_stock():
    return render_template('manage_stock.html')


# ---------- ADMIN LOGOUT ----------
@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect("/admin")



# ---------- START SERVER ----------
if __name__ == "__main__":
    app.run(debug=True,port = 1234)
