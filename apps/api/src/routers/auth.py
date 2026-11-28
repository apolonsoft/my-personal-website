"""Authentication, onboarding, and password recovery router."""

from datetime import datetime, timedelta, timezone
import json
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlmodel import Session, select

from config import get_settings
from database import get_session
from email_service import EmailMessage, EmailSender, get_email_sender
from models import (
    AuthTokenResponse,
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    OnboardingRequest,
    OnboardingStatusResponse,
    PasswordResetToken,
    ProfileRead,
    ResetPasswordRequest,
    User,
    utcnow,
)
from security import (
    create_access_token,
    generate_reset_token,
    hash_password,
    hash_reset_token,
    verify_password,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])
_RESET_TOKEN_TTL_MINUTES = 30


def user_to_profile_read(user: User) -> ProfileRead:
    """Map a User ORM entity to ProfileRead."""
    try:
        links = json.loads(user.social_links_json or "{}")
        if not isinstance(links, dict):
            links = {}
    except (ValueError, TypeError):
        links = {}

    return ProfileRead(
        id=user.id or 0,
        email=user.email,
        role=user.role,
        full_name=user.full_name,
        headline=user.headline,
        bio=user.bio,
        avatar_key=user.avatar_key,
        avatar_url=user.avatar_url,
        social_links={str(k): str(v) for k, v in links.items()},
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


def _issue_token_response(request: Request, user: User) -> AuthTokenResponse:
    settings = get_settings(request)
    if not settings.jwt_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="JWT_SECRET is not configured.",
        )
    token = create_access_token(
        user_id=user.id or 0,
        email=user.email,
        role=user.role,
        secret=settings.jwt_secret,
        expires_seconds=settings.jwt_expires_seconds,
    )
    return AuthTokenResponse(
        access_token=token,
        expires_in=settings.jwt_expires_seconds,
        user=user_to_profile_read(user),
    )


@router.get("/onboarding/status", response_model=OnboardingStatusResponse)
async def onboarding_status(
    session: Annotated[Session, Depends(get_session)],
) -> OnboardingStatusResponse:
    """Return whether at least one admin user already exists."""
    existing = session.exec(select(User.id).limit(1)).first()
    return OnboardingStatusResponse(initialized=existing is not None)


@router.post(
    "/onboarding",
    response_model=AuthTokenResponse,
    status_code=status.HTTP_201_CREATED,
)
async def onboard_default_admin(
    payload: OnboardingRequest,
    request: Request,
    session: Annotated[Session, Depends(get_session)],
) -> AuthTokenResponse:
    """Create the initial admin user (one-time only; returns 409 once initialized)."""
    existing = session.exec(select(User.id).limit(1)).first()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Admin onboarding has already been completed.",
        )

    now = utcnow()
    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        role="admin",
        is_active=True,
        full_name=payload.full_name,
        headline=payload.headline,
        bio=payload.bio,
        created_at=now,
        updated_at=now,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return _issue_token_response(request, user)


@router.post("/login", response_model=AuthTokenResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    session: Annotated[Session, Depends(get_session)],
) -> AuthTokenResponse:
    """Authenticate with email + password and issue an HS256 JWT."""
    user = session.exec(select(User).where(User.email == payload.email)).first()
    if user is None or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return _issue_token_response(request, user)


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    payload: ForgotPasswordRequest,
    request: Request,
    session: Annotated[Session, Depends(get_session)],
    email_sender: Annotated[EmailSender, Depends(get_email_sender)],
) -> MessageResponse:
    """Generate a single-use 30-minute reset token and email it if the user exists."""
    generic_reply = MessageResponse(
        message="If an account with that email exists, a password reset link has been sent."
    )
    user = session.exec(select(User).where(User.email == payload.email)).first()
    if user is None or not user.is_active or user.id is None:
        return generic_reply

    now = utcnow()
    prior_tokens = session.exec(
        select(PasswordResetToken).where(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used_at == None,  # noqa: E711
        )
    ).all()
    for prior in prior_tokens:
        prior.used_at = now
        session.add(prior)

    raw_token, token_hash = generate_reset_token()
    reset_record = PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=now + timedelta(minutes=_RESET_TOKEN_TTL_MINUTES),
        created_at=now,
    )
    session.add(reset_record)
    session.commit()

    settings = get_settings(request)
    reset_url = f"{settings.frontend_url}/reset-password?token={raw_token}"
    text_body = (
        f"Hi {user.full_name},\n\n"
        f"Use the link below to reset your password (valid for {_RESET_TOKEN_TTL_MINUTES} minutes):\n"
        f"{reset_url}\n\n"
        f"If you did not request this, you can safely ignore this email."
    )
    html_body = (
        f"<p>Hi {user.full_name},</p>"
        f"<p>Use the link below to reset your password (valid for {_RESET_TOKEN_TTL_MINUTES} minutes):</p>"
        f'<p><a href="{reset_url}">Reset your password</a></p>'
        f"<p>If you did not request this, you can safely ignore this email.</p>"
    )
    await email_sender.send(
        EmailMessage(
            to=user.email,
            subject="Reset your password",
            text=text_body,
            html=html_body,
        )
    )
    return generic_reply


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    payload: ResetPasswordRequest,
    session: Annotated[Session, Depends(get_session)],
) -> MessageResponse:
    """Validate a single-use reset token and update the user's password."""
    token_hash = hash_reset_token(payload.token)
    record = session.exec(
        select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)
    ).first()

    now = utcnow()
    if record is None or record.used_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or already used reset token.",
        )

    expires_at = record.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at <= now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired.",
        )

    user = session.exec(select(User).where(User.id == record.user_id)).first()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token.",
        )

    user.password_hash = hash_password(payload.new_password)
    user.updated_at = now
    record.used_at = now
    session.add(user)
    session.add(record)
    session.commit()
    return MessageResponse(message="Password has been reset successfully.")
