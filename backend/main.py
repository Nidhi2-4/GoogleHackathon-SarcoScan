"""SarcoScan API. Start it from the repo root: uvicorn backend.main:app --reload"""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .analysis import model_connected, tabular_connected
from . import seed, storage
from .db import Base, engine, upgrade_schema
from .routers import admin, auth, patients, visits


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ponytail: tables are created at startup. Move to Alembic once real data has to survive a schema change.
    Base.metadata.create_all(engine)
    upgrade_schema()
    seed.demo_doctor()  # the public demo login; remove before real patient data
    # Load all four models now (about 10 s) so the first screening does not wait for them.
    model_connected()
    tabular_connected()
    yield


app = FastAPI(title="SarcoScan API", lifespan=lifespan)

# No CORS middleware on purpose: the web app forwards /api to this server, so the browser only ever
# talks to the web app's own address. See docs/SECURITY.md, section 3.

app.include_router(auth.router)
app.include_router(patients.router)
app.include_router(visits.router)
app.include_router(admin.router)


@app.api_route("/", methods=["GET", "HEAD"])
def root():
    """This server is the API only. The web app is a separate service; say so instead of "Not Found"."""
    return {"service": "SarcoScan API", "health": "/api/v1/health", "note": "Open the web app, not this address."}


@app.api_route("/api/v1/ping", methods=["GET", "HEAD"])
def ping():
    """For uptime monitors. Answers HEAD as well as GET, and touches neither the database nor the models."""
    return {"status": "ok"}


@app.get("/api/v1/health")
def health():
    return {
        "status": "ok", "model_connected": model_connected(), "tabular_connected": tabular_connected(),
        "storage": storage.backend(),
    }
