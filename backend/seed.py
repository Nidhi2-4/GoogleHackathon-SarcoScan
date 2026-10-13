"""Create the first admin, doctor and technician. Run from the repo root: python -m backend.seed"""
import os

from sqlalchemy import select

from .db import Base, SessionLocal, engine
from .models import Role, User
from .security import hash_password

USERS = (
    ("Sunita Nair", "admin@sarcoscan.local", Role.admin, "SEED_ADMIN_PASSWORD"),
    ("Dr. Arvind Rao", "doctor@sarcoscan.local", Role.doctor, "SEED_DOCTOR_PASSWORD"),
    ("Meena Kulkarni", "technician@sarcoscan.local", Role.technician, "SEED_TECHNICIAN_PASSWORD"),
)


def main() -> None:
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        for name, email, role, variable in USERS:
            if db.scalar(select(User.id).where(User.email == email)):
                continue
            password = os.environ.get(variable, "")
            if len(password) < 10:
                raise SystemExit(f"{variable} must be set in .env and be at least 10 characters long.")
            db.add(User(name=name, email=email, password_hash=hash_password(password), role=role))
        db.commit()
    print("Seed users are ready.")


if __name__ == "__main__":
    main()
