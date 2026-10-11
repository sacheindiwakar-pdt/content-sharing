from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.database import get_db_connection
from app.dependencies import get_current_user
from app.schemas import LoginResponse, UserResponse
from app.security import verify_password, create_access_token, TOKEN_MINUTES

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=LoginResponse)
def login(form: OAuth2PasswordRequestForm = Depends()):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT username, password_hash, role, is_active FROM users WHERE username=%s", (form.username,))
        user = cursor.fetchone()
        if not user or not user["is_active"] or not verify_password(form.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid username or password", headers={"WWW-Authenticate": "Bearer"})
        token = create_access_token(user["username"], user["role"])
        return {"access_token": token, "token_type": "bearer", "expires_in_minutes": TOKEN_MINUTES, "role": user["role"]}
    finally:
        cursor.close()
        connection.close()

@router.get("/me", response_model=UserResponse)
def me(user: dict = Depends(get_current_user)):
    return user
