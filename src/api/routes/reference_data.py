"""
Reference Data Endpoints: Admission Types, Discharge Dispositions, Admission Sources
"""

from fastapi import APIRouter, Depends
from src.api.database import get_db_connection
from src.api.dependencies import require_roles

router = APIRouter(prefix="/reference-data", tags=["Reference Data"])
read_access = require_roles("Admin", "Healthcare Staff", "Analyst")


@router.get("/admission-types")
def get_admission_types(current_user: dict = Depends(read_access)):
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT admission_type_id, description FROM admission_types ORDER BY admission_type_id")
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()


@router.get("/discharge-dispositions")
def get_discharge_dispositions(current_user: dict = Depends(read_access)):
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT discharge_disposition_id, description FROM discharge_dispositions ORDER BY discharge_disposition_id")
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()


@router.get("/admission-sources")
def get_admission_sources(current_user: dict = Depends(read_access)):
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT admission_source_id, description FROM admission_sources ORDER BY admission_source_id")
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()
