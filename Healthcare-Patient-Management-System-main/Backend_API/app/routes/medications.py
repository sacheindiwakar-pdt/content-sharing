import mysql.connector
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.database import get_db_connection
from app.dependencies import require_roles
from app.schemas import MedicationCreate, MedicationReplace, MedicationUpdate

router=APIRouter(prefix="/medications",tags=["Medications"])
access=require_roles("Admin","Healthcare Staff")

@router.get("")
def list_medications(limit:int=Query(100,ge=1,le=500),offset:int=Query(0,ge=0),encounter_id:int|None=None,_:dict=Depends(access)):
    connection=get_db_connection(); cursor=connection.cursor(dictionary=True)
    try:
        if encounter_id is None: cursor.execute("SELECT encounter_id, medication, medication_status FROM encounter_medications ORDER BY encounter_id, medication LIMIT %s OFFSET %s",(limit,offset))
        else: cursor.execute("SELECT encounter_id, medication, medication_status FROM encounter_medications WHERE encounter_id=%s ORDER BY medication LIMIT %s OFFSET %s",(encounter_id,limit,offset))
        return cursor.fetchall()
    finally: cursor.close(); connection.close()

@router.get("/{encounter_id}")
def get_medications(encounter_id:int,_:dict=Depends(access)):
    connection=get_db_connection(); cursor=connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT encounter_id, medication, medication_status FROM encounter_medications WHERE encounter_id=%s ORDER BY medication",(encounter_id,)); return cursor.fetchall()
    finally: cursor.close(); connection.close()

@router.post("",status_code=status.HTTP_201_CREATED)
def create_medication(payload:MedicationCreate,_:dict=Depends(access)):
    connection=get_db_connection(); cursor=connection.cursor(dictionary=True)
    try:
        cursor.execute("INSERT INTO encounter_medications (encounter_id,medication,medication_status) VALUES (%s,%s,%s)",(payload.encounter_id,payload.medication,payload.medication_status)); connection.commit(); return payload.model_dump()
    except mysql.connector.IntegrityError as exc:
        connection.rollback(); raise HTTPException(status_code=409,detail="Medication key already exists or encounter does not exist") from exc
    finally: cursor.close(); connection.close()

@router.put("/{encounter_id}/{medication}")
def replace_medication(encounter_id:int,medication:str,payload:MedicationReplace,_:dict=Depends(access)):
    connection=get_db_connection(); cursor=connection.cursor(dictionary=True)
    try:
        cursor.execute("UPDATE encounter_medications SET medication_status=%s WHERE encounter_id=%s AND medication=%s",(payload.medication_status,encounter_id,medication))
        if cursor.rowcount==0:
            cursor.execute("SELECT 1 FROM encounter_medications WHERE encounter_id=%s AND medication=%s",(encounter_id,medication))
            if not cursor.fetchone(): raise HTTPException(status_code=404,detail="Medication record not found")
        connection.commit(); return {"encounter_id":encounter_id,"medication":medication,"medication_status":payload.medication_status}
    finally: cursor.close(); connection.close()

@router.patch("/{encounter_id}/{medication}")
def update_medication(encounter_id:int,medication:str,payload:MedicationUpdate,_:dict=Depends(access)):
    if "medication_status" not in payload.model_fields_set: raise HTTPException(status_code=400,detail="Provide medication_status")
    return replace_medication(encounter_id,medication,MedicationReplace(medication_status=payload.medication_status),_)

@router.delete("/{encounter_id}/{medication}",status_code=204)
def delete_medication(encounter_id:int,medication:str,_:dict=Depends(access)):
    connection=get_db_connection(); cursor=connection.cursor()
    try:
        cursor.execute("DELETE FROM encounter_medications WHERE encounter_id=%s AND medication=%s",(encounter_id,medication))
        if cursor.rowcount==0: raise HTTPException(status_code=404,detail="Medication record not found")
        connection.commit()
    finally: cursor.close(); connection.close()
