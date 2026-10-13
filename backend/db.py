"""Database engine, sessions, a 404 helper, and the small schema upgrades run at startup."""
import uuid

from fastapi import HTTPException, status
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import settings

# Connection poolers such as Supabase's (port 6543) give each transaction a different server connection,
# which breaks psycopg's prepared statements after a few repeats of the same query. Turn them off.
_connect_args = {"prepare_threshold": None} if settings.database_url.startswith("postgresql+psycopg") else {}
engine = create_engine(settings.database_url, pool_pre_ping=True, connect_args=_connect_args)
SessionLocal = sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    with SessionLocal() as db:
        yield db


def get_or_404(db: Session, model, record_id: uuid.UUID, what: str):
    """The row with this id, or a 404 that names what was missing."""
    record = db.get(model, record_id)
    if record is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"No such {what}")
    return record


# Columns added after the first databases were created. create_all never adds a column to an
# existing table, so upgrade_schema() adds any that are missing.
_ADDED_COLUMNS = {
    "visits": {"waist_cm": "FLOAT", "arm_circ_cm": "FLOAT", "history_json": "TEXT"},
    "analysis_results": {
        "low_muscle": "BOOLEAN", "low_muscle_prob": "FLOAT", "bone_loss": "BOOLEAN", "bone_loss_prob": "FLOAT",
    },
}


def upgrade_schema() -> None:
    # ponytail: hand-written upgrades in place of Alembic. Each is safe to repeat. Move to Alembic once
    # a change is more than "add a nullable column" or "drop a NOT NULL".
    with engine.begin() as connection:
        if engine.dialect.name == "postgresql":
            # Databases created before the phone number became optional still require it.
            connection.execute(
                text("ALTER TABLE patients ALTER COLUMN phone DROP NOT NULL, ALTER COLUMN phone_hash DROP NOT NULL")
            )
            # Supabase serves every table in "public" over its REST API to anyone holding the project's
            # anon key, which is public by design. Row-level security with no policies gives that key
            # nothing. This API is unaffected: only a table's owner may run this ALTER, and the owner
            # is not bound by row-level security.
            for table in Base.metadata.tables:
                connection.execute(text(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY'))
        uuid_type = "UUID" if engine.dialect.name == "postgresql" else "CHAR(32)"
        for table, columns in {**_ADDED_COLUMNS, "patients": {"doctor_id": uuid_type}}.items():
            present = {column["name"] for column in inspect(connection).get_columns(table)}
            for name, kind in columns.items():
                if name not in present:
                    connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {kind}"))
        # Each patient belongs to one doctor. Patients a doctor registered before the column existed are theirs.
        connection.execute(text(
            "UPDATE patients SET doctor_id = created_by WHERE doctor_id IS NULL"
            " AND created_by IN (SELECT id FROM users WHERE role = 'doctor')"
        ))
        # The technician role is retired; its accounts stay (audit rows point to them) but cannot sign in.
        connection.execute(text("UPDATE users SET is_active = FALSE WHERE role = 'technician' AND is_active"))
        # Logins no longer use refresh tokens (2026-10-12); the old table only held their hashes.
        connection.execute(text("DROP TABLE IF EXISTS refresh_tokens"))
