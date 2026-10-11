"""
Patient CRUD, Search, and History Endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from src.api.database import get_db_connection
from src.api.dependencies import require_roles
from src.api.schemas import PatientResponse, PatientCreate, PatientUpdate
from src.services.audit_service import record_audit

router = APIRouter(prefix="/patients", tags=["Patients"])

read_access = require_roles("Admin", "Healthcare Staff", "Analyst")
write_access = require_roles("Admin", "Healthcare Staff")
admin_access = require_roles("Admin")


@router.get("", response_model=List[PatientResponse])
def list_patients(
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
    gender: Optional[str] = Query(None),
    race: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    current_user: dict = Depends(read_access)
):
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    try:
        query = "SELECT patient_nbr, race, gender FROM patients WHERE 1=1"
        params = []

        if gender:
            query += " AND gender = %s"
            params.append(gender)
        if race:
            query += " AND race = %s"
            params.append(race)
        if search:
            query += " AND CAST(patient_nbr AS TEXT) LIKE %s"
            params.append(f"%{search}%")

        query += " ORDER BY patient_nbr LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        cur.execute(query, tuple(params))
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()


@router.get("/{patient_nbr}", response_model=PatientResponse)
def get_patient_by_id(patient_nbr: int, current_user: dict = Depends(read_access)):
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT patient_nbr, race, gender FROM patients WHERE patient_nbr = %s", (patient_nbr,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Patient record not found")
        return row
    finally:
        cur.close()
        conn.close()


@router.post("", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
def create_patient(payload: PatientCreate, current_user: dict = Depends(write_access)):
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT patient_nbr FROM patients WHERE patient_nbr = %s", (payload.patient_nbr,))
        if cur.fetchone():
            raise HTTPException(status_code=409, detail=f"Patient {payload.patient_nbr} already exists")

        cur.execute(
            "INSERT INTO patients (patient_nbr, race, gender) VALUES (%s, %s, %s)",
            (payload.patient_nbr, payload.race, payload.gender)
        )
        conn.commit()
        record_audit(
            username=current_user["username"],
            action="CREATE",
            resource_type="PATIENT",
            resource_id=str(payload.patient_nbr),
            detail=f"Created patient {payload.patient_nbr}",
            user_id=current_user["user_id"]
        )
        return payload.model_dump()
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cur.close()
        conn.close()


@router.patch("/{patient_nbr}", response_model=PatientResponse)
def update_patient(patient_nbr: int, payload: PatientUpdate, current_user: dict = Depends(write_access)):
    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="Provide at least one field to update")

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT patient_nbr, race, gender FROM patients WHERE patient_nbr = %s", (patient_nbr,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Patient record not found")

        for k, v in updates.items():
            if v is not None:
                row[k] = v

        cur.execute(
            "UPDATE patients SET race = %s, gender = %s WHERE patient_nbr = %s",
            (row["race"], row["gender"], patient_nbr)
        )
        conn.commit()
        record_audit(
            username=current_user["username"],
            action="UPDATE",
            resource_type="PATIENT",
            resource_id=str(patient_nbr),
            detail=f"Updated patient fields: {list(updates.keys())}",
            user_id=current_user["user_id"]
        )
        return row
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cur.close()
        conn.close()


@router.delete("/{patient_nbr}", status_code=status.HTTP_200_OK)
def delete_patient(patient_nbr: int, current_user: dict = Depends(admin_access)):
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT patient_nbr FROM patients WHERE patient_nbr = %s", (patient_nbr,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Patient record not found")

        # Delete dependent diagnoses and medications first
        cur.execute("SELECT encounter_id FROM encounters WHERE patient_nbr = %s", (patient_nbr,))
        encs = [r["encounter_id"] for r in cur.fetchall()]
        for eid in encs:
            cur.execute("DELETE FROM encounter_diagnoses WHERE encounter_id = %s", (eid,))
            cur.execute("DELETE FROM encounter_medications WHERE encounter_id = %s", (eid,))

        cur.execute("DELETE FROM encounters WHERE patient_nbr = %s", (patient_nbr,))
        cur.execute("DELETE FROM patients WHERE patient_nbr = %s", (patient_nbr,))
        conn.commit()

        record_audit(
            username=current_user["username"],
            action="DELETE",
            resource_type="PATIENT",
            resource_id=str(patient_nbr),
            detail=f"Deleted patient {patient_nbr} and associated encounters",
            user_id=current_user["user_id"]
        )
        return {"status": "success", "message": f"Patient {patient_nbr} successfully deleted"}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cur.close()
        conn.close()


@router.get("/{patient_nbr}/encounters")
def get_patient_encounter_history(patient_nbr: int, current_user: dict = Depends(read_access)):
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute(
            """
            SELECT e.*, a.description as admission_type, d.description as discharge_disposition
            FROM encounters e
            LEFT JOIN admission_types a ON e.admission_type_id = a.admission_type_id
            LEFT JOIN discharge_dispositions d ON e.discharge_disposition_id = d.discharge_disposition_id
            WHERE e.patient_nbr = %s
            ORDER BY e.encounter_id DESC
            """,
            (patient_nbr,)
        )
        encounters = cur.fetchall()

        for enc in encounters:
            cur.execute("SELECT diagnosis_position, diagnosis_code FROM encounter_diagnoses WHERE encounter_id = %s ORDER BY diagnosis_position", (enc["encounter_id"],))
            enc["diagnoses"] = cur.fetchall()
            cur.execute("SELECT medication, medication_status FROM encounter_medications WHERE encounter_id = %s", (enc["encounter_id"],))
            enc["medications"] = cur.fetchall()

        return encounters
    finally:
        cur.close()
        conn.close()
