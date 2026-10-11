import mysql.connector
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.database import get_db_connection
from app.dependencies import require_roles
from app.schemas import EncounterCreate, EncounterReplace, EncounterUpdate

router = APIRouter(prefix="/encounters", tags=["Encounters"])
access = require_roles("Admin", "Healthcare Staff")
COLS = ["patient_nbr","age","admission_type_id","discharge_disposition_id","admission_source_id","time_in_hospital","payer_code","medical_specialty","num_lab_procedures","num_procedures","num_medications","number_outpatient","number_emergency","number_inpatient","number_diagnoses","change","diabetesMed","readmitted","weight","max_glu_serum","A1Cresult"]
SELECT = "encounter_id, " + ", ".join(COLS)

def fetch_one(cursor, encounter_id):
    cursor.execute(f"SELECT {SELECT} FROM encounters WHERE encounter_id=%s", (encounter_id,))
    return cursor.fetchone()

@router.get("")
def list_encounters(limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0), patient_nbr: int | None = None, _: dict = Depends(access)):
    connection=get_db_connection(); cursor=connection.cursor(dictionary=True)
    try:
        if patient_nbr is None:
            cursor.execute(f"SELECT {SELECT} FROM encounters ORDER BY encounter_id LIMIT %s OFFSET %s", (limit,offset))
        else:
            cursor.execute(f"SELECT {SELECT} FROM encounters WHERE patient_nbr=%s ORDER BY encounter_id LIMIT %s OFFSET %s", (patient_nbr,limit,offset))
        return cursor.fetchall()
    finally: cursor.close(); connection.close()

@router.get("/{encounter_id}")
def get_encounter(encounter_id: int, _: dict = Depends(access)):
    connection=get_db_connection(); cursor=connection.cursor(dictionary=True)
    try:
        row=fetch_one(cursor,encounter_id)
        if not row: raise HTTPException(status_code=404,detail="Encounter not found")
        return row
    finally: cursor.close(); connection.close()

@router.post("", status_code=status.HTTP_201_CREATED)
def create_encounter(payload: EncounterCreate, _: dict = Depends(access)):
    data=payload.model_dump(); connection=get_db_connection(); cursor=connection.cursor(dictionary=True)
    try:
        cols=["encounter_id"]+COLS; values=[data[c] for c in cols]
        cursor.execute(f"INSERT INTO encounters ({', '.join(cols)}) VALUES ({', '.join(['%s']*len(cols))})", values)
        connection.commit(); return fetch_one(cursor,data["encounter_id"])
    except mysql.connector.IntegrityError as exc:
        connection.rollback(); raise HTTPException(status_code=409,detail="Encounter ID already exists or a patient/reference ID is invalid") from exc
    finally: cursor.close(); connection.close()

@router.put("/{encounter_id}")
def replace_encounter(encounter_id: int, payload: EncounterReplace, _: dict = Depends(access)):
    data=payload.model_dump(); connection=get_db_connection(); cursor=connection.cursor(dictionary=True)
    try:
        if not fetch_one(cursor,encounter_id): raise HTTPException(status_code=404,detail="Encounter not found")
        assignments=", ".join(f"{c}=%s" for c in COLS)
        cursor.execute(f"UPDATE encounters SET {assignments} WHERE encounter_id=%s", [data[c] for c in COLS]+[encounter_id])
        connection.commit(); return fetch_one(cursor,encounter_id)
    except mysql.connector.IntegrityError as exc:
        connection.rollback(); raise HTTPException(status_code=409,detail="Patient/reference ID is invalid") from exc
    except Exception: connection.rollback(); raise
    finally: cursor.close(); connection.close()

@router.patch("/{encounter_id}")
def update_encounter(encounter_id: int, payload: EncounterUpdate, _: dict = Depends(access)):
    data=payload.model_dump(exclude_unset=True)
    if not data: raise HTTPException(status_code=400,detail="Provide at least one field to update")
    connection=get_db_connection(); cursor=connection.cursor(dictionary=True)
    try:
        if not fetch_one(cursor,encounter_id): raise HTTPException(status_code=404,detail="Encounter not found")
        assignments=", ".join(f"{c}=%s" for c in data)
        cursor.execute(f"UPDATE encounters SET {assignments} WHERE encounter_id=%s", list(data.values())+[encounter_id])
        connection.commit(); return fetch_one(cursor,encounter_id)
    except mysql.connector.IntegrityError as exc:
        connection.rollback(); raise HTTPException(status_code=409,detail="Patient/reference ID is invalid") from exc
    except Exception: connection.rollback(); raise
    finally: cursor.close(); connection.close()
