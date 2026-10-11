"""
Data Export & Compliance Audit Inspection Endpoints
"""

import io
import pandas as pd
from fastapi import APIRouter, Depends, Query, Response
from fastapi.responses import StreamingResponse
from src.api.database import get_db_connection
from src.api.dependencies import require_roles

router = APIRouter(prefix="/reports", tags=["Reporting & Audits"])
analyst_access = require_roles("Admin", "Analyst", "Healthcare Staff")
admin_access = require_roles("Admin")


@router.get("/export/encounters/csv")
def export_encounters_csv(limit: int = Query(500, le=5000), current_user: dict = Depends(analyst_access)):
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute(
            """
            SELECT encounter_id, patient_nbr, age, time_in_hospital,
                   num_lab_procedures, num_medications, readmitted
            FROM encounters
            ORDER BY encounter_id DESC
            LIMIT %s
            """,
            (limit,)
        )
        rows = cur.fetchall()
        df = pd.DataFrame(rows)
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)

        return Response(
            content=csv_buffer.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=encounters_export.csv"}
        )
    finally:
        cur.close()
        conn.close()


@router.get("/export/encounters/excel")
def export_encounters_excel(limit: int = Query(500, le=5000), current_user: dict = Depends(analyst_access)):
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute(
            """
            SELECT encounter_id, patient_nbr, age, time_in_hospital,
                   num_lab_procedures, num_medications, readmitted
            FROM encounters
            ORDER BY encounter_id DESC
            LIMIT %s
            """,
            (limit,)
        )
        rows = cur.fetchall()
        df = pd.DataFrame(rows)
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Encounters")
        excel_buffer.seek(0)

        return StreamingResponse(
            excel_buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=encounters_export.xlsx"}
        )
    finally:
        cur.close()
        conn.close()


@router.get("/audit-logs")
def get_audit_logs(limit: int = Query(50, le=200), current_user: dict = Depends(admin_access)):
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute(
            """
            SELECT audit_id, username, action, resource_type, resource_id, outcome, detail, created_at
            FROM audit_logs
            ORDER BY audit_id DESC
            LIMIT %s
            """,
            (limit,)
        )
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()
