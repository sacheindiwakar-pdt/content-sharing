"""
FastAPI Dependencies for Security, JWT Authentication and Role-Based Access Control (RBAC)
"""

from typing import Callable
from fastapi import Depends, HTTPException, status
from src.api.database import get_db_connection
from src.api.security import decode_access_token, oauth2_scheme


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    try:
        payload = decode_access_token(token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )

    username = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token claims",
            headers={"WWW-Authenticate": "Bearer"}
        )

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT user_id, username, role, is_active FROM users WHERE username=%s", (username,))
        user = cur.fetchone()
        if not user or not user["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User inactive or removed",
                headers={"WWW-Authenticate": "Bearer"}
            )
        return user
    finally:
        cur.close()
        conn.close()


def require_roles(*roles: str) -> Callable:
    def checker(user: dict = Depends(get_current_user)) -> dict:
        if user["role"] not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Requires one of roles: {', '.join(roles)}"
            )
        return user
    return checker
