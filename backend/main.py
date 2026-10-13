"""SarcoScan API. Start it from the repo root: uvicorn backend.main:app --reload"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import inspect, text

from .analysis import model_connected, tabular_connected
from .db import Base, engine
from .routers import admin, auth, patients, visits


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ponytail: tables are created at startup. Move to Alembic once real data has to survive a schema change.
    Base.metadata.create_all(engine)
    if engine.dialect.name == "postgresql":
        # ponytail: one hand-written schema fix in place of Alembic. Databases created before the phone
        # number became optional still require it. Safe to repeat; drop this once every database has run it.
        with engine.begin() as connection:
            connection.execute(
                text("ALTER TABLE patients ALTER COLUMN phone DROP NOT NULL, ALTER COLUMN phone_hash DROP NOT NULL")
            )
    # ponytail: create_all never adds a column to a table that already exists, so new optional
    # columns are added here. Replace with Alembic once a change is more than "add a nullable column".
    wanted = {
        "visits": {"waist_cm": "FLOAT", "arm_circ_cm": "FLOAT", "history_json": "TEXT"},
        "analysis_results": {
            "low_muscle": "BOOLEAN", "low_muscle_prob": "FLOAT", "bone_loss": "BOOLEAN", "bone_loss_prob": "FLOAT",
        },
    }
    with engine.begin() as connection:
        for table, columns in wanted.items():
            present = {column["name"] for column in inspect(connection).get_columns(table)}
            for name, kind in columns.items():
                if name not in present:
                    connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {kind}"))
    # Load all four models now (about 10 s) so the first screening does not wait for them.
    model_connected()
    tabular_connected()
    yield


app = FastAPI(title="SarcoScan API", lifespan=lifespan)
app.include_router(auth.router)
app.include_router(patients.router)
app.include_router(visits.router)
app.include_router(admin.router)


@app.get("/api/v1/health")
def health():
    return {"status": "ok", "model_connected": model_connected(), "tabular_connected": tabular_connected()}
