"""Passwords, the login token, role checks, and the audit log."""
import secrets
import uuid
from datetime import timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .config import settings
from .db import get_db, get_or_404
from .models import AuditLog, Patient, Role, User, Visit, now

# Who may read patient data. Only a doctor writes it, and only for their own patients (see own_patient).
STAFF = (Role.doctor, Role.admin)

_hasher = PasswordHasher()
# Checked when the email is unknown, so a wrong email takes as long as a wrong password.
_DUMMY_HASH = _hasher.hash(secrets.token_urlsafe(16))
_bearer = HTTPBearer(auto_error=False)


def _not_logged_in() -> HTTPException:
    return HTTPException(
        status.HTTP_401_UNAUTHORIZED,
        "Not logged in or the session has expired",
        headers={"WWW-Authenticate": "Bearer"},
    )


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, hashed: str | None) -> bool:
    try:
        return _hasher.verify(hashed or _DUMMY_HASH, password) and hashed is not None
    except (VerificationError, InvalidHashError):
        return False


def create_access_token(user: User) -> str:
    issued = now()
    claims = {
        "sub": str(user.id),
        "role": user.role.value,
        "iat": issued,
        "exp": issued + timedelta(days=settings.token_days),
    }
    return jwt.encode(claims, settings.jwt_secret, algorithm="HS256")


def current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise _not_logged_in()
    try:
        claims = jwt.decode(credentials.credentials, settings.jwt_secret, algorithms=["HS256"])
        user_id = uuid.UUID(claims["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise _not_logged_in() from None
    # The role is taken from the user's row, so a deactivated or demoted user loses access at once.
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise _not_logged_in()
    return user


def require_roles(*roles: Role):
    """Dependency: the caller must be logged in with one of these roles."""

    def check(user: User = Depends(current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Your role is not allowed to do this")
        return user

    return check


def own_patient(db: Session, user: User, patient_id: uuid.UUID) -> Patient:
    """The patient, if this user may see them: their own doctor, or an admin (read only).
    Anyone else gets the same 404 as for a missing patient, so other doctors' patients stay invisible."""
    patient = get_or_404(db, Patient, patient_id, "patient")
    if user.role != Role.admin and patient.doctor_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No such patient")
    return patient


def own_visit(db: Session, user: User, visit_id: uuid.UUID) -> tuple[Visit, Patient]:
    """The visit and its patient, under the same rule as own_patient."""
    visit = get_or_404(db, Visit, visit_id, "visit")
    try:
        return visit, own_patient(db, user, visit.patient_id)
    except HTTPException:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No such visit") from None


def client_ip(request: Request) -> str:
    """The caller's address. The web app's /api proxy runs on this machine and adds the browser's
    address as the last X-Forwarded-For entry; only a connection from this machine is trusted to say so."""
    host = request.client.host if request.client else ""
    forwarded = request.headers.get("x-forwarded-for", "")
    if host in ("127.0.0.1", "::1") and forwarded:
        return forwarded.split(",")[-1].strip()
    return host


class Audit:
    """Dependency that records who did what. Rows hold ids only, never patient names."""

    def __init__(self, request: Request, db: Session = Depends(get_db)):
        self.db = db
        self.ip = client_ip(request)

    def log(self, user: User, action: str, entity_type: str, entity_id: uuid.UUID | None = None) -> None:
        self.db.add(
            AuditLog(user_id=user.id, action=action, entity_type=entity_type, entity_id=entity_id, ip_address=self.ip)
        )
