"""
User Administration Routes (Admin Only)
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from src.api.database import get_db_connection
from src.api.dependencies import require_roles
from src.api.schemas import UserCreate, UserResponse
from src.api.security import hash_password
from src.services.audit_service import record_audit

router = APIRouter(prefix="/users", tags=["User Administration"])
admin_access = require_roles("Admin")


@router.get("", response_model=List[UserResponse])
def list_users(current_user: dict = Depends(admin_access)):
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT user_id, username, role, is_active FROM users ORDER BY user_id")
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, current_user: dict = Depends(admin_access)):
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT user_id FROM users WHERE username = %s", (payload.username,))
        if cur.fetchone():
            raise HTTPException(status_code=409, detail="Username already exists")

        pwd_hash = hash_password(payload.password)
        cur.execute(
            "INSERT INTO users (username, password_hash, role, is_active) VALUES (%s, %s, %s, 1)",
            (payload.username, pwd_hash, payload.role)
        )
        conn.commit()

        cur.execute("SELECT user_id, username, role, is_active FROM users WHERE username = %s", (payload.username,))
        created = cur.fetchone()

        record_audit(
            username=current_user["username"],
            action="CREATE_USER",
            resource_type="USER",
            resource_id=str(created["user_id"]),
            detail=f"Created user {payload.username} with role {payload.role}",
            user_id=current_user["user_id"]
        )
        return created
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cur.close()
        conn.close()
