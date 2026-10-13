"""Passwords, tokens, role checks, the audit log, and the login rate limit."""
import hashlib
import secrets
import time
import uuid
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from .config import settings
from .db import get_db
from .models import AuditLog, RefreshToken, Role, User, now

STAFF = (Role.technician, Role.doctor, Role.admin)
SCREENERS = (Role.technician, Role.doctor)

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
        "type": "access",
        "iat": issued,
        "exp": issued + timedelta(minutes=settings.access_minutes),
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
    if claims.get("type") != "access":
        raise _not_logged_in()
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


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _as_utc(moment: datetime) -> datetime:
    # SQLite returns naive datetimes; PostgreSQL returns aware ones.
    return moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc)


def issue_refresh_token(db: Session, user: User) -> str:
    token = secrets.token_urlsafe(48)
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=_token_hash(token),
            expires_at=now() + timedelta(days=settings.refresh_days),
        )
    )
    return token


def rotate_refresh_token(db: Session, token: str) -> tuple[User, str]:
    """Swap a valid refresh token for a new one. The caller commits."""
    row = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == _token_hash(token)))
    if row is None:
        raise _not_logged_in()
    if row.revoked:
        # A used token came back, so it may have been stolen. Sign the user out everywhere.
        db.execute(update(RefreshToken).where(RefreshToken.user_id == row.user_id).values(revoked=True))
        db.commit()
        raise _not_logged_in()
    user = db.get(User, row.user_id)
    if _as_utc(row.expires_at) < now() or user is None or not user.is_active:
        raise _not_logged_in()
    row.revoked = True
    return user, issue_refresh_token(db, user)


def revoke_refresh_token(db: Session, token: str) -> None:
    db.execute(update(RefreshToken).where(RefreshToken.token_hash == _token_hash(token)).values(revoked=True))


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


_login_attempts: dict[str, deque[float]] = defaultdict(deque)


def limit_login(request: Request) -> None:
    """Dependency: at most 5 login attempts per minute from one address."""
    # ponytail: kept in memory, per process. Move to Redis if the API runs with more than one worker.
    attempts = _login_attempts[client_ip(request)]
    cutoff = time.monotonic() - 60
    while attempts and attempts[0] < cutoff:
        attempts.popleft()
    if len(attempts) >= 5:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Too many login attempts. Try again in a minute.")
    attempts.append(time.monotonic())
