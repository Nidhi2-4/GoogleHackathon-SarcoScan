"""Sign up, sign in, and who am I. One bearer token that the browser keeps. See docs/SECURITY.md."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Role, User, now
from ..schemas import LoginIn, SignupIn, TokenOut, UserOut
from ..security import Audit, create_access_token, current_user, hash_password, verify_password

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/signup", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def signup(body: SignupIn, db: Session = Depends(get_db), audit: Audit = Depends()):
    # ponytail: open to anyone while the database holds made-up patients only. A new account is a doctor
    # with no patients. Close this (or ask for an invite code) before real patient data.
    email = body.email.strip().lower()
    if db.scalar(select(User.id).where(User.email == email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "An account with this email already exists")
    user = User(
        name=body.name.strip(), email=email, role=Role.doctor,
        password_hash=hash_password(body.password), last_login_at=now(),
    )
    db.add(user)
    db.flush()
    audit.log(user, "CREATE", "user", user.id)
    db.commit()
    return TokenOut(access_token=create_access_token(user))


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, db: Session = Depends(get_db), audit: Audit = Depends()):
    user = db.scalar(select(User).where(User.email == body.email.strip().lower()))
    password_ok = verify_password(body.password, user.password_hash if user else None)
    if not password_ok or not user.is_active:
        # One message for every failure, so the form does not reveal which emails exist.
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Wrong email or password")
    user.last_login_at = now()
    audit.log(user, "LOGIN", "user", user.id)
    db.commit()
    return TokenOut(access_token=create_access_token(user))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(current_user)):
    return user
