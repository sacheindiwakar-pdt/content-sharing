import mysql.connector
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.database import get_db_connection
from app.dependencies import require_roles
from app.schemas import PatientResponse, PatientCreate, PatientReplace, PatientUpdate

router = APIRouter(prefix="/patients", tags=["Patients"])
patient_read = require_roles("Admin", "Healthcare Staff")
patient_write = require_roles("Admin", "Healthcare Staff")

@router.get("", response_model=list[PatientResponse])
def get_patients(limit: int = Query(10, ge=1, le=100), offset: int = Query(0, ge=0), _: dict = Depends(patient_read)):
    connection = get_db_connection(); cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT patient_nbr, race, gender FROM patients ORDER BY patient_nbr LIMIT %s OFFSET %s", (limit, offset))
        return cursor.fetchall()
    finally:
        cursor.close(); connection.close()

@router.get("/{patient_nbr}", response_model=PatientResponse)
def get_patient(patient_nbr: int, _: dict = Depends(patient_read)):
    connection = get_db_connection(); cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT patient_nbr, race, gender FROM patients WHERE patient_nbr=%s", (patient_nbr,))
        row = cursor.fetchone()
        if not row: raise HTTPException(status_code=404, detail="Patient not found")
        return row
    finally:
        cursor.close(); connection.close()

@router.post("", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
def create_patient(payload: PatientCreate, _: dict = Depends(patient_write)):
    connection = get_db_connection(); cursor = connection.cursor()
    try:
        cursor.execute("INSERT INTO patients (patient_nbr, race, gender) VALUES (%s, %s, %s)", (payload.patient_nbr, payload.race, payload.gender))
        connection.commit()
        return payload.model_dump()
    except mysql.connector.IntegrityError as exc:
        connection.rollback(); raise HTTPException(status_code=409, detail="Patient ID already exists or violates a database constraint") from exc
    finally:
        cursor.close(); connection.close()

@router.put("/{patient_nbr}", response_model=PatientResponse)
def replace_patient(patient_nbr: int, payload: PatientReplace, _: dict = Depends(patient_write)):
    connection = get_db_connection(); cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT patient_nbr FROM patients WHERE patient_nbr=%s", (patient_nbr,))
        if not cursor.fetchone(): raise HTTPException(status_code=404, detail="Patient not found")
        cursor.execute("UPDATE patients SET race=%s, gender=%s WHERE patient_nbr=%s", (payload.race, payload.gender, patient_nbr))
        connection.commit()
        return {"patient_nbr": patient_nbr, **payload.model_dump()}
    except Exception:
        connection.rollback(); raise
    finally:
        cursor.close(); connection.close()

@router.patch("/{patient_nbr}", response_model=PatientResponse)
def update_patient(patient_nbr: int, payload: PatientUpdate, _: dict = Depends(patient_write)):
    changes = payload.model_dump(exclude_unset=True)
    if not changes: raise HTTPException(status_code=400, detail="Provide at least one field to update")
    connection = get_db_connection(); cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT patient_nbr, race, gender FROM patients WHERE patient_nbr=%s", (patient_nbr,))
        row = cursor.fetchone()
        if not row: raise HTTPException(status_code=404, detail="Patient not found")
        row.update(changes)
        cursor.execute("UPDATE patients SET race=%s, gender=%s WHERE patient_nbr=%s", (row["race"], row["gender"], patient_nbr))
        connection.commit(); return row
    except Exception:
        connection.rollback(); raise
    finally:
        cursor.close(); connection.close()
