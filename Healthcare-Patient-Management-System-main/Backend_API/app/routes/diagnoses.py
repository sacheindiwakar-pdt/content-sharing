import mysql.connector
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.database import get_db_connection
from app.dependencies import require_roles
from app.schemas import DiagnosisCreate, DiagnosisReplace, DiagnosisUpdate

router=APIRouter(prefix="/diagnoses",tags=["Diagnoses"])
access=require_roles("Admin","Healthcare Staff")

@router.get("")
def list_diagnoses(limit:int=Query(100,ge=1,le=500),offset:int=Query(0,ge=0),encounter_id:int|None=None,_:dict=Depends(access)):
    connection=get_db_connection(); cursor=connection.cursor(dictionary=True)
    try:
        if encounter_id is None: cursor.execute("SELECT encounter_id, diagnosis_position, diagnosis_code FROM encounter_diagnoses ORDER BY encounter_id, diagnosis_position LIMIT %s OFFSET %s",(limit,offset))
        else: cursor.execute("SELECT encounter_id, diagnosis_position, diagnosis_code FROM encounter_diagnoses WHERE encounter_id=%s ORDER BY diagnosis_position LIMIT %s OFFSET %s",(encounter_id,limit,offset))
        return cursor.fetchall()
    finally: cursor.close(); connection.close()

@router.get("/{encounter_id}")
def get_diagnoses(encounter_id:int,_:dict=Depends(access)):
    connection=get_db_connection(); cursor=connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT encounter_id, diagnosis_position, diagnosis_code FROM encounter_diagnoses WHERE encounter_id=%s ORDER BY diagnosis_position",(encounter_id,)); return cursor.fetchall()
    finally: cursor.close(); connection.close()

@router.post("",status_code=status.HTTP_201_CREATED)
def create_diagnosis(payload:DiagnosisCreate,_:dict=Depends(access)):
    connection=get_db_connection(); cursor=connection.cursor(dictionary=True)
    try:
        cursor.execute("INSERT INTO encounter_diagnoses (encounter_id,diagnosis_position,diagnosis_code) VALUES (%s,%s,%s)",(payload.encounter_id,payload.diagnosis_position,payload.diagnosis_code)); connection.commit()
        return {**payload.model_dump()}
    except mysql.connector.IntegrityError as exc:
        connection.rollback(); raise HTTPException(status_code=409,detail="Diagnosis key already exists or encounter does not exist") from exc
    finally: cursor.close(); connection.close()

@router.put("/{encounter_id}/{diagnosis_position}")
def replace_diagnosis(encounter_id:int,diagnosis_position:int,payload:DiagnosisReplace,_:dict=Depends(access)):
    connection=get_db_connection(); cursor=connection.cursor(dictionary=True)
    try:
        cursor.execute("UPDATE encounter_diagnoses SET diagnosis_code=%s WHERE encounter_id=%s AND diagnosis_position=%s",(payload.diagnosis_code,encounter_id,diagnosis_position))
        if cursor.rowcount==0:
            cursor.execute("SELECT 1 FROM encounter_diagnoses WHERE encounter_id=%s AND diagnosis_position=%s",(encounter_id,diagnosis_position))
            if not cursor.fetchone(): raise HTTPException(status_code=404,detail="Diagnosis record not found")
        connection.commit(); return {"encounter_id":encounter_id,"diagnosis_position":diagnosis_position,"diagnosis_code":payload.diagnosis_code}
    finally: cursor.close(); connection.close()

@router.patch("/{encounter_id}/{diagnosis_position}")
def update_diagnosis(encounter_id:int,diagnosis_position:int,payload:DiagnosisUpdate,_:dict=Depends(access)):
    if "diagnosis_code" not in payload.model_fields_set: raise HTTPException(status_code=400,detail="Provide diagnosis_code")
    return replace_diagnosis(encounter_id,diagnosis_position,DiagnosisReplace(diagnosis_code=payload.diagnosis_code),_)

@router.delete("/{encounter_id}/{diagnosis_position}",status_code=204)
def delete_diagnosis(encounter_id:int,diagnosis_position:int,_:dict=Depends(access)):
    connection=get_db_connection(); cursor=connection.cursor()
    try:
        cursor.execute("DELETE FROM encounter_diagnoses WHERE encounter_id=%s AND diagnosis_position=%s",(encounter_id,diagnosis_position))
        if cursor.rowcount==0: raise HTTPException(status_code=404,detail="Diagnosis record not found")
        connection.commit()
    finally: cursor.close(); connection.close()
