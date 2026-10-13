from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_db
from ..models import User, now
from ..schemas import LoginIn, TokenOut, UserOut
from ..security import (
    Audit,
    create_access_token,
    current_user,
    issue_refresh_token,
    limit_login,
    revoke_refresh_token,
    rotate_refresh_token,
    verify_password,
)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

COOKIE = "refresh_token"
COOKIE_PATH = "/api/v1/auth"


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        COOKIE,
        token,
        max_age=settings.refresh_days * 24 * 60 * 60,
        path=COOKIE_PATH,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="strict",
    )


@router.post("/login", response_model=TokenOut, dependencies=[Depends(limit_login)])
def login(body: LoginIn, response: Response, db: Session = Depends(get_db), audit: Audit = Depends()):
    user = db.scalar(select(User).where(User.email == body.email.strip().lower()))
    password_ok = verify_password(body.password, user.password_hash if user else None)
    if not password_ok or not user.is_active:
        # One message for every failure, so the form does not reveal which emails exist.
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Wrong email or password")
    user.last_login_at = now()
    refresh_token = issue_refresh_token(db, user)
    audit.log(user, "LOGIN", "user", user.id)
    db.commit()
    _set_refresh_cookie(response, refresh_token)
    return TokenOut(access_token=create_access_token(user))


@router.post("/refresh", response_model=TokenOut)
def refresh(response: Response, refresh_token: str | None = Cookie(default=None), db: Session = Depends(get_db)):
    # A missing cookie hashes to nothing in the table, so it is refused like any unknown token.
    user, new_token = rotate_refresh_token(db, refresh_token or "")
    db.commit()
    _set_refresh_cookie(response, new_token)
    return TokenOut(access_token=create_access_token(user))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response, refresh_token: str | None = Cookie(default=None), db: Session = Depends(get_db)):
    if refresh_token:
        revoke_refresh_token(db, refresh_token)
        db.commit()
    response.delete_cookie(COOKIE, path=COOKIE_PATH)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(current_user)):
    return user
