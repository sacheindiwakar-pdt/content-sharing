"""
Authentication Routes: User Login, Token Issuance, and Profile Retrieval
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from src.api.database import get_db_connection
from src.api.dependencies import get_current_user
from src.api.schemas import TokenResponse, UserResponse
from src.api.security import verify_password, create_access_token, TOKEN_MINUTES
from src.services.audit_service import record_audit

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT user_id, username, password_hash, role, is_active FROM users WHERE username=%s", (form_data.username,))
        user = cur.fetchone()

        if not user or not user["is_active"] or not verify_password(form_data.password, user["password_hash"]):
            record_audit(username=form_data.username, action="LOGIN_ATTEMPT", resource_type="AUTH", outcome="FAILED", detail="Invalid credentials")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = create_access_token(user["username"], user["role"])
        record_audit(username=user["username"], action="LOGIN_SUCCESS", resource_type="AUTH", resource_id=str(user["user_id"]), outcome="SUCCESS", user_id=user["user_id"])

        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in_minutes": TOKEN_MINUTES,
            "role": user["role"],
            "username": user["username"]
        }
    finally:
        cur.close()
        conn.close()


@router.get("/me", response_model=UserResponse)
def get_current_profile(current_user: dict = Depends(get_current_user)):
    return current_user
