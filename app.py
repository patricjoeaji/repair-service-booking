from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId
from bson.errors import InvalidId
import os

from db import customers, bookings, staff, create_database


app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")


 # FIRST LOGIN
 
@app.route("/")
def first_login():
    return render_template("first_login.html")


 # CUSTOMER LOGIN
 
@app.route("/customer-login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"].strip()
        password = request.form["password"]

        customer = customers.find_one({
            "email": email
        })

        if customer and check_password_hash(
            customer["password"],
            password
        ):

            session["customer_id"] = str(customer["_id"])
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

        name = request.form["name"].strip()
        email = request.form["email"].strip()
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if not name or not email or not password:
            return render_template(
                "register.html",
                error="Please complete all fields"
            )

        if password != confirm_password:
            return render_template(
                "register.html",
                error="Passwords do not match"
            )

        existing_customer = customers.find_one({
            "email": email
        })

        if existing_customer:
            return render_template(
                "register.html",
                error="An account with this email already exists"
            )

        hashed_password = generate_password_hash(password)

        customers.insert_one({
            "name": name,
            "email": email,
            "password": hashed_password
        })

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

        if (
            not service
            or not description
            or not preferred_date
            or not preferred_time
        ):
            return render_template(
                "create_booking.html",
                error="Please complete all booking fields"
            )

        try:
            customer_id = ObjectId(
                session["customer_id"]
            )
        except (InvalidId, TypeError):
            session.clear()
            return redirect(url_for("login"))

        bookings.insert_one({
            "customer_id": customer_id,
            "service": service,
            "description": description,
            "preferred_date": preferred_date,
            "preferred_time": preferred_time,
            "status": "Pending"
        })

        return redirect(url_for("booking_success"))

    return render_template("create_booking.html")


 # VIEW CUSTOMER BOOKINGS
 
@app.route("/view-bookings")
def view_bookings():

    if "customer_id" not in session:
        return redirect(url_for("login"))

    try:
        customer_id = ObjectId(
            session["customer_id"]
        )
    except (InvalidId, TypeError):
        session.clear()
        return redirect(url_for("login"))

    customer_bookings = list(
        bookings.find({
            "customer_id": customer_id
        }).sort("_id", -1)
    )

    return render_template(
        "view_bookings.html",
        bookings=customer_bookings
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

        email = request.form["email"].strip()
        password = request.form["password"]

        staff_member = staff.find_one({
            "email": email
        })

        if staff_member and check_password_hash(
            staff_member["password"],
            password
        ):

            session["staff_id"] = str(
                staff_member["_id"]
            )

            session["staff_name"] = staff_member["name"]

            session["staff_role"] = staff_member["role"]

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

    all_bookings = list(
        bookings.find().sort("_id", -1)
    )

    booking_list = []

    for booking in all_bookings:

        customer = customers.find_one({
            "_id": booking.get("customer_id")
        })

        booking_list.append({
            "id": str(booking["_id"]),
            "customer_name": (
                customer["name"]
                if customer
                else "Unknown"
            ),
            "customer_email": (
                customer["email"]
                if customer
                else "Unknown"
            ),
            "service": booking.get("service", ""),
            "description": booking.get("description", ""),
            "preferred_date": booking.get(
                "preferred_date",
                ""
            ),
            "preferred_time": booking.get(
                "preferred_time",
                ""
            ),
            "status": booking.get(
                "status",
                "Pending"
            )
        })

    return render_template(
        "staff_bookings.html",
        bookings=booking_list
    )


 # UPDATE BOOKING STATUS
 
@app.route(
    "/update-booking-status/<booking_id>",
    methods=["POST"]
)
def update_booking_status(booking_id):

    if "staff_id" not in session:
        return redirect(url_for("staff_login"))

    status = request.form.get("status")

    allowed_statuses = [
        "Pending",
        "Confirmed",
        "In Progress",
        "Completed",
        "Cancelled"
    ]

    if status not in allowed_statuses:
        return redirect(url_for("staff_bookings"))

    try:
        booking_object_id = ObjectId(booking_id)
    except (InvalidId, TypeError):
        return redirect(url_for("staff_bookings"))

    bookings.update_one(
        {
            "_id": booking_object_id
        },
        {
            "$set": {
                "status": status
            }
        }
    )

    return redirect(url_for("staff_bookings"))


 # LOGOUT
 
@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


 # RUN APPLICATION
 
if __name__ == "__main__":

    create_database()

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )