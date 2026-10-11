from typing import Callable
from fastapi import Depends, HTTPException, status
from app.database import get_db_connection
from app.security import decode_access_token, oauth2_scheme


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    payload = decode_access_token(token)
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT user_id, username, role, is_active FROM users WHERE username=%s", (username,))
        user = cursor.fetchone()
        if not user or not user["is_active"]:
            raise HTTPException(status_code=401, detail="User is inactive or no longer exists")
        return user
    finally:
        cursor.close()
        connection.close()


def require_roles(*roles: str) -> Callable:
    def checker(user: dict = Depends(get_current_user)) -> dict:
        if user["role"] not in roles:
            raise HTTPException(status_code=403, detail="You do not have permission to perform this action")
        return user
    return checker
