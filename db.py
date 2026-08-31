import sqlite3

from werkzeug.security import generate_password_hash


DATABASE = "database.db"


def get_db_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def create_database():
    connection = get_db_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            service TEXT NOT NULL,
            description TEXT NOT NULL,
            preferred_date TEXT NOT NULL,
            preferred_time TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending',
            FOREIGN KEY (customer_id) REFERENCES customers (id)
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS staff (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'Staff'
        )
    """)

    existing_staff = connection.execute(
        "SELECT id FROM staff WHERE email = ?",
        ("staff@repairservice.com",)
    ).fetchone()

    if existing_staff is None:
        connection.execute(
            """
            INSERT INTO staff (name, email, password, role)
            VALUES (?, ?, ?, ?)
            """,
            (
                "Repair Service Staff",
                "staff@repairservice.com",
                generate_password_hash("Staff123!"),
                "Staff"
            )
        )

    connection.commit()
    connection.close()