import os

from pymongo import MongoClient
from werkzeug.security import generate_password_hash


MONGODB_URI = os.environ.get("MONGODB_URI")

if not MONGODB_URI:
    raise RuntimeError(
        "MONGODB_URI environment variable is not set."
    )


client = MongoClient(MONGODB_URI)

db = client["repair_service_booking"]

customers = db["customers"]
bookings = db["bookings"]
staff = db["staff"]


def create_database():

    existing_staff = staff.find_one(
        {"email": "staff@repairservice.com"}
    )

    if existing_staff is None:

        staff.insert_one({
            "name": "Repair Service Staff",
            "email": "staff@repairservice.com",
            "password": generate_password_hash("Staff123!"),
            "role": "Staff"
        })