#app/auth/router.py
"""
HTTP layer for the auth domain: registration, login, refresh, and profile.
"""
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_active_user
from app.auth.models import User
from app.auth.schemas import (
    ChangePasswordRequest,
    EmailVerificationRequest,
    ForgotPasswordRequest,
    LogoutRequest,
    PasswordResetOTPVerificationRequest,
    PasswordResetRequest,
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
async def register(
    user_in: UserCreate, request: Request, db: AsyncSession = Depends(get_db)
):
    service = AuthService(db)
    user = await service.register(
        user_in,
        request_id=getattr(request.state, "request_id", None),
        endpoint=request.url.path,
    )
    return SuccessResponse(
        message="User registered successfully. Please check your email for the verification code.",
        data=UserRead.model_validate(user),
    )


@router.post("/verify-email", response_model=SuccessResponse[None])
async def verify_email(payload: EmailVerificationRequest, db: AsyncSession = Depends(get_db)):
    await AuthService(db).verify_email(payload)
    return SuccessResponse(message="Email verified successfully", data=None)


@router.post("/resend-verification", response_model=SuccessResponse[None])
async def resend_verification(
    payload: ResendVerificationRequest, request: Request, db: AsyncSession = Depends(get_db)
):
    await AuthService(db).resend_email_verification(
        payload.email, request_id=getattr(request.state, "request_id", None)
    )
    return SuccessResponse(message="If eligible, a verification code has been sent", data=None)


@router.post("/forgot-password", response_model=SuccessResponse[None])
async def forgot_password(
    payload: ForgotPasswordRequest, request: Request, db: AsyncSession = Depends(get_db)
):
    await AuthService(db).forgot_password(
        payload.email, request_id=getattr(request.state, "request_id", None)
    )
    return SuccessResponse(message="If eligible, a password reset code has been sent", data=None)


@router.post("/verify-password-reset-otp", response_model=SuccessResponse[None])
async def verify_password_reset_otp(
    payload: PasswordResetOTPVerificationRequest, db: AsyncSession = Depends(get_db)
):
    await AuthService(db).verify_password_reset_otp(payload)
    return SuccessResponse(message="Password reset code verified", data=None)


@router.post("/reset-password", response_model=SuccessResponse[None])
async def reset_password(payload: PasswordResetRequest, db: AsyncSession = Depends(get_db)):
    await AuthService(db).reset_password(payload)
    return SuccessResponse(message="Password reset successfully", data=None)


@router.post("/change-password", response_model=SuccessResponse[None])
async def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await AuthService(db).change_password(current_user, payload)
    return SuccessResponse(message="Password changed successfully", data=None)


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


@router.post("/logout", response_model=SuccessResponse[None])
async def logout(payload: LogoutRequest, db: AsyncSession = Depends(get_db)):
    await AuthService(db).logout(payload.refresh_token)
    return SuccessResponse(message="Logged out successfully", data=None)


@router.post("/logout-all", response_model=SuccessResponse[None])
async def logout_all(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await AuthService(db).logout_all(current_user)
    return SuccessResponse(message="Logged out from all devices", data=None)


@router.get("/me", response_model=SuccessResponse[UserRead])
async def get_me(current_user: User = Depends(get_current_active_user)):
    return SuccessResponse(message="User profile fetched", data=UserRead.model_validate(current_user))
