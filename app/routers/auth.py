from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import create_token, get_current_user, hash_password, verify_password
from app.database import get_db
from app.models import User
from app.schemas import TokenResponse, UserCreate, UserLogin, UserRead


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    exists = db.query(User).filter(User.username == payload.username).first()
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="username already exists")
    role = "admin" if db.query(User).count() == 0 else "user"
    user = User(username=payload.username, password_hash=hash_password(payload.password), role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return TokenResponse(access_token=create_token(user.id, user.username, user.role), user=user)


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == payload.username).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid username or password")
    return TokenResponse(access_token=create_token(user.id, user.username, user.role), user=user)


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)):
    return current_user

