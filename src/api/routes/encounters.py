"""
Encounter CRUD, Filtering, and Detail Endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from src.api.database import get_db_connection
from src.api.dependencies import require_roles
from src.api.schemas import EncounterResponse, EncounterCreate, EncounterUpdate
from src.services.audit_service import record_audit

router = APIRouter(prefix="/encounters", tags=["Encounters"])

read_access = require_roles("Admin", "Healthcare Staff", "Analyst")
write_access = require_roles("Admin", "Healthcare Staff")
admin_access = require_roles("Admin")

COLS = [
    "patient_nbr", "age", "admission_type_id", "discharge_disposition_id",
    "admission_source_id", "time_in_hospital", "payer_code", "medical_specialty",
    "num_lab_procedures", "num_procedures", "num_medications", "number_outpatient",
    "number_emergency", "number_inpatient", "number_diagnoses", "change",
    "diabetesMed", "readmitted", "weight", "max_glu_serum", "A1Cresult"
]


@router.get("", response_model=List[EncounterResponse])
def list_encounters(
    limit: int = Query(25, ge=1, le=200),
    offset: int = Query(0, ge=0),
    patient_nbr: Optional[int] = Query(None),
    readmitted: Optional[str] = Query(None),
    age: Optional[str] = Query(None),
    admission_type_id: Optional[int] = Query(None),
    current_user: dict = Depends(read_access)
):
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    try:
        query = f"SELECT encounter_id, {', '.join(COLS)} FROM encounters WHERE 1=1"
        params = []

        if patient_nbr is not None:
            query += " AND patient_nbr = %s"
            params.append(patient_nbr)
        if readmitted:
            query += " AND readmitted = %s"
            params.append(readmitted)
        if age:
            query += " AND age = %s"
            params.append(age)
        if admission_type_id:
            query += " AND admission_type_id = %s"
            params.append(admission_type_id)

        query += " ORDER BY encounter_id DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        cur.execute(query, tuple(params))
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()


@router.get("/{encounter_id}")
def get_encounter_detail(encounter_id: int, current_user: dict = Depends(read_access)):
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute(
            f"""
            SELECT e.encounter_id, {', '.join(['e.' + c for c in COLS])},
                   a.description AS admission_type_name,
                   d.description AS discharge_disposition_name,
                   s.description AS admission_source_name
            FROM encounters e
            LEFT JOIN admission_types a ON e.admission_type_id = a.admission_type_id
            LEFT JOIN discharge_dispositions d ON e.discharge_disposition_id = d.discharge_disposition_id
            LEFT JOIN admission_sources s ON e.admission_source_id = s.admission_source_id
            WHERE e.encounter_id = %s
            """,
            (encounter_id,)
        )
        enc = cur.fetchone()
        if not enc:
            raise HTTPException(status_code=404, detail="Encounter record not found")

        cur.execute("SELECT diagnosis_position, diagnosis_code FROM encounter_diagnoses WHERE encounter_id = %s ORDER BY diagnosis_position", (encounter_id,))
        enc["diagnoses"] = cur.fetchall()

        cur.execute("SELECT medication, medication_status FROM encounter_medications WHERE encounter_id = %s", (encounter_id,))
        enc["medications"] = cur.fetchall()

        return enc
    finally:
        cur.close()
        conn.close()


@router.post("", response_model=EncounterResponse, status_code=status.HTTP_201_CREATED)
def create_encounter(payload: EncounterCreate, current_user: dict = Depends(write_access)):
    data = payload.model_dump()
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT patient_nbr FROM patients WHERE patient_nbr = %s", (data["patient_nbr"],))
        if not cur.fetchone():
            raise HTTPException(status_code=400, detail=f"Patient {data['patient_nbr']} does not exist in patients master")

        cur.execute("SELECT encounter_id FROM encounters WHERE encounter_id = %s", (data["encounter_id"],))
        if cur.fetchone():
            raise HTTPException(status_code=409, detail=f"Encounter {data['encounter_id']} already exists")

        all_cols = ["encounter_id"] + COLS
        vals = [data[c] for c in all_cols]
        placeholders = ", ".join(["%s"] * len(all_cols))

        cur.execute(
            f"INSERT INTO encounters ({', '.join(all_cols)}) VALUES ({placeholders})",
            tuple(vals)
        )
        conn.commit()

        record_audit(
            username=current_user["username"],
            action="CREATE",
            resource_type="ENCOUNTER",
            resource_id=str(data["encounter_id"]),
            detail=f"Created encounter for patient {data['patient_nbr']}",
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


@router.patch("/{encounter_id}", response_model=EncounterResponse)
def update_encounter(encounter_id: int, payload: EncounterUpdate, current_user: dict = Depends(write_access)):
    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="Provide at least one field to update")

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute(f"SELECT encounter_id, {', '.join(COLS)} FROM encounters WHERE encounter_id = %s", (encounter_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Encounter record not found")

        for k, v in updates.items():
            row[k] = v

        set_clause = ", ".join([f"{k} = %s" for k in updates.keys()])
        params = [updates[k] for k in updates.keys()] + [encounter_id]

        cur.execute(f"UPDATE encounters SET {set_clause} WHERE encounter_id = %s", tuple(params))
        conn.commit()

        record_audit(
            username=current_user["username"],
            action="UPDATE",
            resource_type="ENCOUNTER",
            resource_id=str(encounter_id),
            detail=f"Updated encounter fields: {list(updates.keys())}",
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


@router.delete("/{encounter_id}", status_code=status.HTTP_200_OK)
def delete_encounter(encounter_id: int, current_user: dict = Depends(admin_access)):
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT encounter_id FROM encounters WHERE encounter_id = %s", (encounter_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Encounter record not found")

        cur.execute("DELETE FROM encounter_diagnoses WHERE encounter_id = %s", (encounter_id,))
        cur.execute("DELETE FROM encounter_medications WHERE encounter_id = %s", (encounter_id,))
        cur.execute("DELETE FROM encounters WHERE encounter_id = %s", (encounter_id,))
        conn.commit()

        record_audit(
            username=current_user["username"],
            action="DELETE",
            resource_type="ENCOUNTER",
            resource_id=str(encounter_id),
            detail=f"Deleted encounter {encounter_id}",
            user_id=current_user["user_id"]
        )
        return {"status": "success", "message": f"Encounter {encounter_id} successfully deleted"}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cur.close()
        conn.close()
