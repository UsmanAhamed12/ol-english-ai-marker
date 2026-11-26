from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.core.limits import limiter
from app.models import User
from app.schemas import LoginIn, RegisterIn, TokenOut, UserOut
from app.core.security import create_access_token, get_current_user, hash_password, verify_password
from app.services import starter_knowledge

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _issue(user: User) -> TokenOut:
    token, expires_in = create_access_token(user.id)
    return TokenOut(access_token=token, expires_in=expires_in)


@router.post("/register", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
def register(request: Request, payload: RegisterIn, db: Session = Depends(get_db)) -> TokenOut:
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "An account with this email already exists.")

    user = User(
        email=payload.email,
        full_name=payload.full_name.strip()[:120],
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Every new studio starts with the four starter sources already indexed.
    starter_knowledge.ensure(db, user.id)

    return _issue(user)


@router.post("/login", response_model=TokenOut)
@limiter.limit("10/minute")
def login(request: Request, payload: LoginIn, db: Session = Depends(get_db)) -> TokenOut:
    user = db.query(User).filter(User.email == payload.email).first()
    # One message for both failures, so the response can't be used to enumerate accounts.
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Email or password is incorrect.")
    return _issue(user)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> User:
    return user