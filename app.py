from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

from db import get_db_connection, create_database

app = Flask(__name__)
app.secret_key = "repair-service-booking-secret-key"


 
# CUSTOMER LOGIN
 

@app.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        connection = get_db_connection()

        customer = connection.execute(
            "SELECT * FROM customers WHERE email = ?",
            (email,)
        ).fetchone()

        connection.close()

        if customer and check_password_hash(
            customer["password"],
            password
        ):
            session["customer_id"] = customer["id"]
            session["customer_name"] = customer["name"]

            return redirect(url_for("customer_home"))

        return render_template(
            "login.html",
            error="Invalid email or password"
        )

    return render_template("login.html")


 
# CUSTOMER REGISTRATION
 

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            return render_template(
                "register.html",
                error="Passwords do not match"
            )

        hashed_password = generate_password_hash(password)

        connection = get_db_connection()

        try:
            connection.execute(
                """
                INSERT INTO customers (name, email, password)
                VALUES (?, ?, ?)
                """,
                (name, email, hashed_password)
            )

            connection.commit()

        except sqlite3.IntegrityError:
            connection.close()

            return render_template(
                "register.html",
                error="An account with this email already exists"
            )

        connection.close()

        return redirect(url_for("login"))

    return render_template("register.html")


 
# CUSTOMER HOME  

@app.route("/customer-home")
def customer_home():

    if "customer_id" not in session:
        return redirect(url_for("login"))

    return render_template(
        "customer_home.html",
        customer_name=session["customer_name"]
    )


 
# CREATE REPAIR BOOKING
 
@app.route("/create-booking", methods=["GET", "POST"])
def create_booking():

    if "customer_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        service = request.form["service"]
        description = request.form["description"]
        preferred_date = request.form["preferred_date"]
        preferred_time = request.form["preferred_time"]

        if not service or not description or not preferred_date or not preferred_time:
            return render_template(
                "create_booking.html",
                error="Please complete all booking fields"
            )

        connection = get_db_connection()

        connection.execute(
            """
            INSERT INTO bookings
            (
                customer_id,
                service,
                description,
                preferred_date,
                preferred_time
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                session["customer_id"],
                service,
                description,
                preferred_date,
                preferred_time
            )
        )

        connection.commit()
        connection.close()

        return redirect(url_for("booking_success"))

    return render_template("create_booking.html")


 
# VIEW CUSTOMER BOOKINGS
 

@app.route("/view-bookings")
def view_bookings():

    if "customer_id" not in session:
        return redirect(url_for("login"))

    connection = get_db_connection()

    bookings = connection.execute(
        """
        SELECT *
        FROM bookings
        WHERE customer_id = ?
        ORDER BY id DESC
        """,
        (session["customer_id"],)
    ).fetchall()

    connection.close()

    return render_template(
        "view_bookings.html",
        bookings=bookings
    )


 
# BOOKING SUCCESS
 

@app.route("/booking-success")
def booking_success():

    if "customer_id" not in session:
        return redirect(url_for("login"))

    return render_template("booking_success.html")


 
# STAFF LOGIN
 

@app.route("/staff-login", methods=["GET", "POST"])
def staff_login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        connection = get_db_connection()

        staff = connection.execute(
            "SELECT * FROM staff WHERE email = ?",
            (email,)
        ).fetchone()

        connection.close()

        if staff and check_password_hash(
            staff["password"],
            password
        ):
            session["staff_id"] = staff["id"]
            session["staff_name"] = staff["name"]
            session["staff_role"] = staff["role"]

            return redirect(url_for("staff_dashboard"))

        return render_template(
            "staff_login.html",
            error="Invalid staff email or password"
        )

    return render_template("staff_login.html")


 
# STAFF DASHBOARD
 

@app.route("/staff-dashboard")
def staff_dashboard():

    if "staff_id" not in session:
        return redirect(url_for("staff_login"))

    return render_template(
        "staff_dashboard.html",
        staff_name=session["staff_name"],
        staff_role=session["staff_role"]
    )


 
# STAFF VIEW CUSTOMER BOOKINGS
 

@app.route("/staff-bookings")
def staff_bookings():

    if "staff_id" not in session:
        return redirect(url_for("staff_login"))

    connection = get_db_connection()

    bookings = connection.execute(
        """
        SELECT
            bookings.id,
            customers.name AS customer_name,
            customers.email AS customer_email,
            bookings.service,
            bookings.description,
            bookings.preferred_date,
            bookings.preferred_time,
            bookings.status
        FROM bookings
        JOIN customers
            ON bookings.customer_id = customers.id
        ORDER BY bookings.id DESC
        """
    ).fetchall()

    connection.close()

    return render_template(
        "staff_bookings.html",
        bookings=bookings
    )

@app.route("/update-booking-status/<int:booking_id>", methods=["POST"])
def update_booking_status(booking_id):

    if "staff_id" not in session:
        return redirect(url_for("staff_login"))

    status = request.form["status"]

    allowed_statuses = [
        "Pending",
        "Confirmed",
        "In Progress",
        "Completed",
        "Cancelled"
    ]

    if status not in allowed_statuses:
        return redirect(url_for("staff_bookings"))

    connection = get_db_connection()

    connection.execute(
        """
        UPDATE bookings
        SET status = ?
        WHERE id = ?
        """,
        (status, booking_id)
    )

    connection.commit()
    connection.close()

    return redirect(url_for("staff_bookings"))
 
# LOGOUT
 

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


 
# RUN APPLICATION
 

if __name__ == "__main__":
    create_database()
    app.run(debug=True)