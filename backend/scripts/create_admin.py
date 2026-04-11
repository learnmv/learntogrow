#!/usr/bin/env python3
"""Create initial admin user."""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import User, UserRole
from app.services.auth import hash_password

# Database configuration (match your config.py)
DB_HOST = os.getenv('DB_HOST', '10.0.0.131')
DB_PORT = os.getenv('DB_PORT', '30432')
DB_NAME = os.getenv('DB_NAME', 'learntogrow_dev')
DB_USER = os.getenv('DB_USER', 'admin')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'admin@123')

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def create_admin():
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        # Check if admin already exists
        existing = db.query(User).filter(User.username == 'admin').first()
        if existing:
            print("Admin user already exists!")
            return

        # Create admin user
        admin = User(
            username='admin',
            email='admin@learntogrow.local',
            hashed_password=hash_password('admin123'),
            role=UserRole.ADMIN,
            full_name='System Administrator',
            is_active=True
        )

        db.add(admin)
        db.commit()
        print("Admin user created successfully!")
        print("Username: admin")
        print("Password: admin123")
        print("Email: admin@learntogrow.local")

    except Exception as e:
        db.rollback()
        print(f"Error creating admin: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_admin()
