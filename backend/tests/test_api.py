"""Run from the repo root: python -m pytest backend"""
import base64
import os
import tempfile
from pathlib import Path

# Settings are read when backend is imported, so the test values go in first.
_db_file = Path(tempfile.mkdtemp()) / "test.db"
os.environ.update(
    DATABASE_URL=f"sqlite:///{_db_file.as_posix()}?check_same_thread=false",
    JWT_SECRET="test-secret-test-secret-test-secret-1234",
    FIELD_KEY=base64.b64encode(os.urandom(32)).decode(),
    HASH_KEY=base64.b64encode(os.urandom(32)).decode(),
    UPLOAD_DIR=str(_db_file.parent / "uploads"),
)

import io  # noqa: E402
import sys  # noqa: E402

sys.modules["ml.predict"] = None  # these tests check the API with no model, on any machine
sys.modules["ml.tabular"] = None

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from PIL import Image  # noqa: E402
from sqlalchemy import text  # noqa: E402

from backend import security  # noqa: E402
from backend.analysis import sarcopenia_stage  # noqa: E402
from backend.db import Base, SessionLocal, engine  # noqa: E402
from backend.main import app  # noqa: E402
from backend.models import Role, Stage, User  # noqa: E402

PASSWORD = "correct-horse-battery"
LOGIN = "/api/v1/auth/login"
SIGNUP = "/api/v1/auth/signup"
PATIENT = {
    "mrn": "MRN-00412",
    "name": "Kamala Deshpande",
    "age": 68,
    "sex": "female",
    "height_cm": 152,
    "weight_kg": 49.5,
    "phone": "98200 00142",
    "consent_given": True,
}


@pytest.fixture()
def client():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        # Two doctors to check that neither sees the other's patients; a technician from before the role was retired.
        for name, role in (("admin", Role.admin), ("doctor", Role.doctor), ("doctor2", Role.doctor),
                           ("technician", Role.technician)):
            db.add(User(name=name, email=f"{name}@test.local", password_hash=security.hash_password(PASSWORD), role=role))
        db.commit()
    with TestClient(app) as test_client:
        yield test_client


def login(client, role):
    response = client.post(LOGIN, json={"email": f"{role}@test.local", "password": PASSWORD})
    assert response.status_code == 200, response.text
    return {"Authorization": "Bearer " + response.json()["access_token"]}


def test_login_returns_a_token_and_no_cookie(client):
    response = client.post(LOGIN, json={"email": "doctor@test.local", "password": PASSWORD})
    assert "set-cookie" not in response.headers
    headers = {"Authorization": "Bearer " + response.json()["access_token"]}
    assert client.get("/api/v1/auth/me", headers=headers).json()["role"] == "doctor"
    assert client.get("/api/v1/auth/me", headers={"Authorization": "Bearer nonsense"}).status_code == 401


def test_signup_makes_a_doctor_who_starts_with_no_patients(client):
    assert client.post("/api/v1/patients", json=PATIENT, headers=login(client, "doctor")).status_code == 201
    new = {"name": "New Doctor", "email": "New@Test.local", "password": "x", "role": "admin"}  # role is ignored
    created = client.post(SIGNUP, json=new)
    assert created.status_code == 201, created.text
    headers = {"Authorization": "Bearer " + created.json()["access_token"]}
    me = client.get("/api/v1/auth/me", headers=headers).json()
    assert (me["email"], me["role"]) == ("new@test.local", "doctor")
    assert client.get("/api/v1/patients", headers=headers).json() == []
    assert client.post(SIGNUP, json=new).status_code == 409
    assert client.post(LOGIN, json={"email": "new@test.local", "password": "x"}).status_code == 200


def test_the_demo_doctor_exists_after_startup(client):
    assert client.post(LOGIN, json={"email": "demo1@doctor.com", "password": "demo@123"}).status_code == 200


def test_wrong_password_and_unknown_email_look_the_same(client):
    wrong = client.post(LOGIN, json={"email": "doctor@test.local", "password": "nope"})
    unknown = client.post(LOGIN, json={"email": "nobody@test.local", "password": "nope"})
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json()


def test_only_admin_reads_the_audit_log(client):
    assert client.get("/api/v1/audit-logs").status_code == 401
    assert client.get("/api/v1/audit-logs", headers=login(client, "doctor")).status_code == 403
    assert client.get("/api/v1/audit-logs", headers=login(client, "admin")).status_code == 200


def test_patient_is_encrypted_at_rest_and_still_searchable(client):
    headers = login(client, "doctor")
    created = client.post("/api/v1/patients", json=PATIENT, headers=headers)
    assert created.status_code == 201, created.text
    assert created.json()["name"] == "Kamala Deshpande"

    with engine.connect() as connection:
        name, phone = connection.execute(text("SELECT name, phone FROM patients")).one()
    assert "Kamala" not in name and "98200" not in phone

    for query in ("kamala", "MRN-004", "+91 9820000142"):
        found = client.get("/api/v1/patients", params={"q": query}, headers=headers).json()
        assert [p["mrn"] for p in found] == ["MRN-00412"], query
    assert client.get("/api/v1/patients", params={"q": "nobody"}, headers=headers).json() == []
    assert client.post("/api/v1/patients", json=PATIENT, headers=headers).status_code == 409
    no_phone = {**PATIENT, "mrn": "MRN-00413", "phone": None}
    assert client.post("/api/v1/patients", json=no_phone, headers=headers).json()["phone"] is None
    assert client.get("/api/v1/patients").status_code == 401


def test_consent_is_required(client):
    body = {**PATIENT, "consent_given": False}
    assert client.post("/api/v1/patients", json=body, headers=login(client, "doctor")).status_code == 422


def test_audit_log_records_ids_not_names(client):
    headers = login(client, "doctor")
    patient_id = client.post("/api/v1/patients", json=PATIENT, headers=headers).json()["id"]
    client.get(f"/api/v1/patients/{patient_id}", headers=headers)

    response = client.get("/api/v1/audit-logs", headers=login(client, "admin"))
    actions = [row["action"] for row in reversed(response.json())]
    assert actions == ["LOGIN", "CREATE", "VIEW", "LOGIN"]
    assert response.json()[1]["entity_id"] == patient_id
    assert "Kamala" not in response.text


def png(width=512, height=640):
    buffer = io.BytesIO()
    Image.linear_gradient("L").resize((width, height)).save(buffer, format="PNG")  # grey with contrast, like an X-ray
    return buffer.getvalue()


def test_sarcopenia_stage_rule():
    assert sarcopenia_stage("female", 19.0, 10.0, True) is Stage.none
    assert sarcopenia_stage("female", 16.4, 10.6, None) is Stage.possible
    assert sarcopenia_stage("female", 16.4, 10.6, True) is Stage.probable
    assert sarcopenia_stage("female", 16.4, 13.0, True) is Stage.severe
    assert sarcopenia_stage("male", 27.9, None, False) is Stage.possible
    assert sarcopenia_stage("male", 28.0, None, True) is Stage.none


def test_screening_flow_from_visit_to_review(client, monkeypatch):
    doctor = login(client, "doctor")
    patient_id = client.post("/api/v1/patients", json=PATIENT, headers=doctor).json()["id"]
    visit = client.post(f"/api/v1/patients/{patient_id}/visits", headers=doctor).json()
    assert visit["bmi"] == 21.4
    base = f"/api/v1/visits/{visit['id']}"

    def upload(content):
        return client.post(f"{base}/xray", files={"file": ("knee.png", content, "image/png")}, headers=doctor)

    assert client.post(f"{base}/analyze", headers=doctor).status_code == 409  # no X-ray yet
    bad_history = {"sarcf_score": 5, "history": {"owns_a_cat": True}}
    assert client.post(f"{base}/clinical-inputs", json=bad_history, headers=doctor).status_code == 422
    inputs = {"sarcf_score": 5, "chair_stand_5_sec": 10.6, "waist_cm": 78, "history": {"steroid_use": True}}
    assert client.post(f"{base}/clinical-inputs", json=inputs, headers=doctor).status_code == 200
    readings = {"left": [15.2, 15.8, 15.5], "right": [16.0, 16.4, 16.1]}
    grip = client.post(f"{base}/grip", json=readings, headers=doctor).json()
    assert grip == {"best_left": 15.8, "best_right": 16.4, "best_kg": 16.4, "cutoff_kg": 18.0, "low": True}

    assert upload(b"not an image at all").status_code == 415
    too_small = upload(png(100, 100))
    assert too_small.status_code == 201 and too_small.json()["qc_passed"] is False
    for not_an_xray in (Image.new("L", (512, 640), 90), Image.new("RGB", (512, 640), (200, 30, 30))):  # blank, colour
        buffer = io.BytesIO()
        not_an_xray.save(buffer, format="PNG")
        assert upload(buffer.getvalue()).json()["qc_passed"] is False
    assert client.post(f"{base}/analyze", headers=doctor).status_code == 409  # only a failed image so far
    good_bytes = png()
    xray = upload(good_bytes).json()
    assert xray["qc_passed"] is True

    # With the body-measurement models answering "low muscle", the same visit becomes probable.
    seen = {}
    fake = {"low_muscle": True, "low_muscle_prob": 0.9, "bone_loss": True, "bone_loss_prob": 0.7}
    monkeypatch.setattr("backend.routers.visits.run_tabular_models", lambda *a: seen.update(args=a) or fake)
    with_models = client.post(f"{base}/analyze", headers=doctor).json()
    assert with_models["sarcopenia_stage"] == "probable" and with_models["low_muscle"] is True
    assert with_models["bone_loss"] is True and with_models["bone_loss_prob"] == 0.7
    assert seen["args"][5:] == (78, None, 15.8, 16.4, {"steroid_use": True})  # waist, arm, grips, history
    monkeypatch.undo()

    result = client.post(f"{base}/analyze", headers=doctor).json()
    assert result["sarcopenia_stage"] == "possible"  # low grip, and no muscle evidence without the models
    assert result["low_muscle"] is None and result["history"] == {"steroid_use": True}
    assert result["model_connected"] is False and result["osteoporosis_tier"] is None
    assert result["sarcf_positive"] is True and result["chair_stand_slow"] is False

    image_url = f"/api/v1/xrays/{xray['id']}/image"
    assert client.get(image_url, headers=doctor).content == good_bytes
    assert client.get(image_url).status_code == 401
    assert client.get(f"/api/v1/xrays/{xray['id']}/overlay", headers=doctor).status_code == 404

    decision = {"agrees_with_ai": False, "final_stage": "probable", "notes": "Refer for DEXA."}
    admin = login(client, "admin")
    assert client.post(f"{base}/review", json=decision, headers=admin).status_code == 403  # admin only reads
    assert client.post(f"{base}/review", json=decision, headers=doctor).status_code == 201
    final = client.get(f"{base}/result", headers=doctor).json()
    assert final["status"] == "reviewed"
    assert final["sarcopenia_stage"] == "possible" and final["review"]["final_stage"] == "probable"

    history = client.get(f"/api/v1/patients/{patient_id}/history", headers=doctor).json()
    assert [(h["best_grip_kg"], h["sarcopenia_stage"], h["final_stage"]) for h in history] == [
        (16.4, "possible", "probable")
    ]
    visits = client.get("/api/v1/visits", headers=doctor).json()
    assert [(v["visit_id"], v["performed_by_name"], v["reviewed_by_name"]) for v in visits] == [
        (visit["id"], "doctor", "doctor")
    ]
    assert client.head("/api/v1/ping").status_code == 200 and client.get("/api/v1/ping").json() == {"status": "ok"}
    assert client.get("/api/v1/health").json() == {
        "status": "ok", "model_connected": False, "tabular_connected": False, "storage": "local",
    }
    assert client.post(f"/api/v1/patients/{patient_id}/visits", headers=admin).status_code == 403
    assert client.post("/api/v1/patients", json={**PATIENT, "mrn": "MRN-9"}, headers=admin).status_code == 403
    assert client.get(f"{base}/result", headers=admin).status_code == 200  # but may read every patient
    assert [p["id"] for p in client.get("/api/v1/patients", headers=admin).json()] == [patient_id]

    # Another doctor cannot see this patient at all: same answer as for a patient that does not exist.
    other = login(client, "doctor2")
    assert client.get("/api/v1/patients", headers=other).json() == []
    assert client.get("/api/v1/visits", headers=other).json() == []
    for url in (f"/api/v1/patients/{patient_id}", f"/api/v1/patients/{patient_id}/history", f"{base}/result", image_url):
        assert client.get(url, headers=other).status_code == 404, url
    assert client.post(f"{base}/grip", json=readings, headers=other).status_code == 404
    assert client.post(f"/api/v1/patients/{patient_id}/visits", headers=other).status_code == 404


def test_client_ip_trusts_only_the_local_proxy():
    from starlette.requests import Request

    from backend.security import client_ip

    def request(host, forwarded):
        headers = [(b"x-forwarded-for", forwarded.encode())] if forwarded else []
        return Request({"type": "http", "client": (host, 1234), "headers": headers})

    assert client_ip(request("127.0.0.1", "9.9.9.9, 10.0.0.7")) == "10.0.0.7"  # last entry: the one our proxy added
    assert client_ip(request("203.0.113.5", "1.2.3.4")) == "203.0.113.5"  # a direct caller cannot pick its address
    assert client_ip(request("127.0.0.1", "")) == "127.0.0.1"


def test_only_admin_manages_users(client):
    new = {"name": "New Doctor", "email": "Doc@Test.local", "role": "doctor", "password": "a-long-password"}
    assert client.post("/api/v1/users", json=new, headers=login(client, "doctor")).status_code == 403
    assert client.get("/api/v1/users", headers=login(client, "doctor")).status_code == 403
    assert client.post("/api/v1/users", json=new).status_code == 401

    admin = login(client, "admin")
    assert client.post("/api/v1/users", json={**new, "password": ""}, headers=admin).status_code == 422
    assert client.post("/api/v1/users", json={**new, "role": "technician"}, headers=admin).status_code == 422  # retired
    created = client.post("/api/v1/users", json=new, headers=admin)
    assert created.status_code == 201 and created.json()["email"] == "doc@test.local"
    assert "password" not in created.text
    assert client.post("/api/v1/users", json=new, headers=admin).status_code == 409

    credentials = {"email": "doc@test.local", "password": "a-long-password"}
    assert client.post(LOGIN, json=credentials).status_code == 200
    user_id = created.json()["id"]
    assert client.patch(f"/api/v1/users/{user_id}", json={"is_active": False}, headers=admin).status_code == 200
    assert client.post(LOGIN, json=credentials).status_code == 401  # switched off

    me = next(u for u in client.get("/api/v1/users", headers=admin).json() if u["role"] == "admin")
    assert client.patch(f"/api/v1/users/{me['id']}", json={"is_active": False}, headers=admin).status_code == 409


def test_retired_technician_cannot_sign_in(client):
    assert client.post(LOGIN, json={"email": "technician@test.local", "password": PASSWORD}).status_code == 401


def test_cloudinary_storage_is_private_and_keeps_nothing_on_disk(monkeypatch):
    """With STORAGE_BACKEND=cloudinary: uploads are "authenticated" (never public), reads use a signed URL,
    and nothing is written to the uploads folder. Cloudinary itself is replaced by a fake here."""
    from types import SimpleNamespace

    from backend import storage
    from backend.config import settings

    uploads, urls = [], []
    fake = SimpleNamespace(
        uploader=SimpleNamespace(upload=lambda source, **kw: uploads.append((source.read(), kw))),
        utils=SimpleNamespace(cloudinary_url=lambda public_id, **kw: urls.append((public_id, kw)) or ("https://x", {})),
    )
    monkeypatch.setattr(storage, "_cloud", True)
    monkeypatch.setattr(storage, "cloudinary", fake, raising=False)
    monkeypatch.setattr(storage.urllib.request, "urlopen", lambda url, timeout: io.BytesIO(b"image bytes"))
    before = set(settings.upload_dir.glob("*")) if settings.upload_dir.exists() else set()

    key = storage.save(io.BytesIO(b"image bytes"), ".png")
    assert uploads == [(b"image bytes", {"public_id": f"sarcoscan/{key[:-4]}", "resource_type": "image",
                                         "type": "authenticated"})]
    with storage.working_copy(key) as copy:
        assert copy.read_bytes() == b"image bytes"
    assert not copy.exists()  # the temporary copy is gone
    assert urls[0][1]["type"] == "authenticated" and urls[0][1]["sign_url"] is True
    after = set(settings.upload_dir.glob("*")) if settings.upload_dir.exists() else set()
    assert after == before
