import uuid
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token,
)
from app.core.config import settings
from app.models.models import User
from app.schemas.schemas import (
    UserRegister, UserLogin, TokenResponse, UserResponse,
    RefreshTokenRequest, SMTPSettings,
)
from app.services.audit_service import log_action
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(
    payload: UserRegister,
    request: Request,
    db: Session = Depends(get_db),
) -> TokenResponse:
    # Check duplicates
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")

    user = User(
        id=str(uuid.uuid4()),
        email=payload.email,
        username=payload.username,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    log_action(
        db, user_id=user.id, action="register",
        ip_address=request.client.host if request.client else None,
    )

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
def login(
    payload: UserLogin,
    request: Request,
    db: Session = Depends(get_db),
) -> TokenResponse:
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is inactive")

    log_action(
        db, user_id=user.id, action="login",
        ip_address=request.client.host if request.client else None,
    )

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    payload: RefreshTokenRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    decoded = decode_token(payload.refresh_token)
    if decoded.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user_id = decoded.get("sub")
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    access_token = create_access_token(user.id)
    new_refresh_token = create_refresh_token(user.id)
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.put("/smtp-settings")
def update_smtp_settings(
    payload: SMTPSettings,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    current_user.smtp_host = payload.smtp_host
    current_user.smtp_port = payload.smtp_port
    current_user.smtp_username = payload.smtp_username
    current_user.smtp_password = payload.smtp_password
    current_user.smtp_from_name = payload.smtp_from_name
    current_user.smtp_use_tls = payload.smtp_use_tls
    if payload.imap_host:
        current_user.imap_host = payload.imap_host
        current_user.imap_port = payload.imap_port
        current_user.imap_username = payload.imap_username
        current_user.imap_password = payload.imap_password
    db.commit()
    return {"message": "SMTP settings updated successfully"}
