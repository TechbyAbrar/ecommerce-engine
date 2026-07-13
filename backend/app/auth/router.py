#app/auth/router.py
"""
HTTP layer for the auth domain: registration, login, refresh, and profile.
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_active_user
from app.auth.models import User
from app.auth.schemas import (
    EmailVerificationRequest,
    RefreshTokenRequest,
    ResendVerificationRequest,
    Token,
    UserCreate,
    UserLogin,
    UserRead,
)
from app.auth.service import AuthService
from app.common.responses import SuccessResponse
from app.core.dependencies import get_db

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register",
    response_model=SuccessResponse[UserRead],
    status_code=status.HTTP_201_CREATED,
)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    user = await service.register(user_in)
    return SuccessResponse(
        message="User registered. Check your email for the verification code.",
        data=UserRead.model_validate(user),
    )


@router.post("/verify-email", response_model=SuccessResponse[None])
async def verify_email(payload: EmailVerificationRequest, db: AsyncSession = Depends(get_db)):
    await AuthService(db).verify_email(payload)
    return SuccessResponse(message="Email verified successfully", data=None)


@router.post("/resend-verification", response_model=SuccessResponse[None])
async def resend_verification(
    payload: ResendVerificationRequest, db: AsyncSession = Depends(get_db)
):
    await AuthService(db).resend_email_verification(payload.email)
    return SuccessResponse(message="If eligible, a verification code has been sent", data=None)


@router.post("/login", response_model=SuccessResponse[Token])
async def login(credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    token = await service.authenticate(credentials)
    return SuccessResponse(message="Login successful", data=token)


@router.post("/refresh", response_model=SuccessResponse[Token])
async def refresh_token(payload: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    token = await service.refresh(payload.refresh_token)
    return SuccessResponse(message="Token refreshed successfully", data=token)


@router.get("/me", response_model=SuccessResponse[UserRead])
async def get_me(current_user: User = Depends(get_current_active_user)):
    return SuccessResponse(message="User profile fetched", data=UserRead.model_validate(current_user))
