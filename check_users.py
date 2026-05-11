import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from models import User
from app import app

with app.app_context():
    users = User.query.all()
    if not users:
        print("No users found.")
    for u in users:
        print(f"ID: {u.id}, Name: {u.name}, Email: {u.email}")
