from flask import Flask, render_template, request, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

from db import get_db_connection, create_database

app = Flask(__name__)


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
            return render_template(
                "customer_home.html",
                customer_name=customer["name"]
            )

        return "Invalid email or password"

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            return "Passwords do not match"

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
            return "An account with this email already exists"

        connection.close()

        return redirect(url_for("login"))

    return render_template("register.html")


if __name__ == "__main__":
    create_database()
    app.run(debug=True)