"""Create the first admin and doctor. Run from the repo root: python -m backend.seed

The public demo doctor shown on the sign-in page needs no command: the API creates it at startup
(demo_doctor below, called from main.py).
"""
import os

from sqlalchemy import select

from .db import Base, SessionLocal, engine
from .models import Role, User
from .security import hash_password

USERS = (
    ("Sunita Nair", "admin@sarcoscan.local", Role.admin, "SEED_ADMIN_PASSWORD"),
    ("Dr. Arvind Rao", "doctor@sarcoscan.local", Role.doctor, "SEED_DOCTOR_PASSWORD"),
)
# Public on purpose: the sign-in page shows it. Keep in step with frontend/web/src/lib/demo.ts.
DEMO_DOCTOR = ("Demo Doctor", "demo1@doctor.com", "demo@123")


def demo_doctor() -> None:
    """Make sure the demo doctor exists. Remove the call in main.py before real patient data."""
    name, email, password = DEMO_DOCTOR
    with SessionLocal() as db:
        if not db.scalar(select(User.id).where(User.email == email)):
            db.add(User(name=name, email=email, password_hash=hash_password(password), role=Role.doctor))
            db.commit()


def main() -> None:
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        for name, email, role, variable in USERS:
            if db.scalar(select(User.id).where(User.email == email)):
                continue
            password = os.environ.get(variable, "")
            if not password:
                raise SystemExit(f"{variable} must be set in .env.")
            db.add(User(name=name, email=email, password_hash=hash_password(password), role=role))
        db.commit()
    print("Seed users are ready.")


if __name__ == "__main__":
    main()
