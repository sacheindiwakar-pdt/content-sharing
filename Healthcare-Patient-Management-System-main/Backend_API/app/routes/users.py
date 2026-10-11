import mysql.connector
from fastapi import APIRouter, Depends, HTTPException, status
from app.database import get_db_connection
from app.dependencies import require_roles
from app.schemas import UserCreate, UserResponse, UserUpdate
from app.security import hash_password

router = APIRouter(prefix="/users", tags=["User Administration"])
admin_only = require_roles("Admin")

@router.get("", response_model=list[UserResponse])
def list_users(_: dict = Depends(admin_only)):
    connection = get_db_connection(); cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT user_id, username, role, is_active FROM users ORDER BY user_id")
        return cursor.fetchall()
    finally:
        cursor.close(); connection.close()

@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, _: dict = Depends(admin_only)):
    connection = get_db_connection(); cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("INSERT INTO users (username, password_hash, role, is_active) VALUES (%s, %s, %s, TRUE)",
                       (payload.username, hash_password(payload.password), payload.role))
        user_id = cursor.lastrowid
        connection.commit()
        return {"user_id": user_id, "username": payload.username, "role": payload.role, "is_active": True}
    except mysql.connector.IntegrityError as exc:
        connection.rollback()
        raise HTTPException(status_code=409, detail="Username already exists or violates a database constraint") from exc
    finally:
        cursor.close(); connection.close()

@router.patch("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, payload: UserUpdate, current: dict = Depends(admin_only)):
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=400, detail="Provide role and/or is_active")
    connection = get_db_connection(); cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT user_id, username, role, is_active FROM users WHERE user_id=%s", (user_id,))
        target = cursor.fetchone()
        if not target:
            raise HTTPException(status_code=404, detail="User not found")
        if target["username"] == current["username"] and changes.get("is_active") is False:
            raise HTTPException(status_code=400, detail="You cannot deactivate your own account")
        role = changes.get("role", target["role"])
        active = changes.get("is_active", target["is_active"])
        cursor.execute("UPDATE users SET role=%s, is_active=%s WHERE user_id=%s", (role, active, user_id))
        connection.commit()
        return {"user_id": user_id, "username": target["username"], "role": role, "is_active": active}
    finally:
        cursor.close(); connection.close()
