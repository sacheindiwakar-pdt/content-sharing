from fastapi import APIRouter, Depends, Query
from app.database import get_db_connection
from app.dependencies import require_roles

router=APIRouter(prefix="/analytics",tags=["Analytics"])
access=require_roles("Admin","Healthcare Staff","Analyst")

def query_all(sql, params=()):
    connection=get_db_connection(); cursor=connection.cursor(dictionary=True)
    try:
        cursor.execute(sql,params); return cursor.fetchall()
    finally: cursor.close(); connection.close()

@router.get("/overview")
def overview(_:dict=Depends(access)):
    rows=query_all("""SELECT (SELECT COUNT(*) FROM patients) AS total_patients,
      COUNT(*) AS total_encounters, AVG(time_in_hospital) AS average_length_of_stay,
      SUM(CASE WHEN readmitted IN ('<30','>30') THEN 1 ELSE 0 END) AS readmitted_encounters,
      100.0*SUM(CASE WHEN readmitted IN ('<30','>30') THEN 1 ELSE 0 END)/NULLIF(COUNT(*),0) AS readmission_rate_percent
      FROM encounters""")
    r=rows[0]
    return {"total_patients":int(r["total_patients"] or 0),"total_encounters":int(r["total_encounters"] or 0),
      "average_length_of_stay":round(float(r["average_length_of_stay"]),2) if r["average_length_of_stay"] is not None else None,
      "readmitted_encounters":int(r["readmitted_encounters"] or 0),"readmission_rate_percent":round(float(r["readmission_rate_percent"]),2) if r["readmission_rate_percent"] is not None else None}

@router.get("/admissions")
def admissions(_:dict=Depends(access)):
    return {"admission_analytics":query_all("""SELECT e.admission_type_id, COALESCE(a.description,'Unknown') AS admission_type,
      COUNT(*) AS total_encounters, ROUND(AVG(e.time_in_hospital),2) AS average_length_of_stay
      FROM encounters e LEFT JOIN admission_types a ON e.admission_type_id=a.admission_type_id
      GROUP BY e.admission_type_id,a.description ORDER BY total_encounters DESC""")}

@router.get("/readmissions")
def readmissions(_:dict=Depends(access)):
    rows=query_all("""SELECT readmitted AS status, COUNT(*) AS encounters,
      ROUND(100.0*COUNT(*)/(SELECT COUNT(*) FROM encounters),2) AS percentage
      FROM encounters GROUP BY readmitted ORDER BY encounters DESC""")
    total=sum(int(r["encounters"]) for r in rows)
    readmitted=sum(int(r["encounters"]) for r in rows if r["status"] in ("<30",">30"))
    return {"total_encounters":total,"known_status_encounters":total,"readmitted_encounters":readmitted,
      "readmission_rate_percent":round(100*readmitted/total,2) if total else 0,
      "status_breakdown":[{"status":r["status"],"encounters":int(r["encounters"]),"percentage":float(r["percentage"] or 0)} for r in rows]}

@router.get("/length-of-stay")
def length_of_stay(_:dict=Depends(access)):
    rows=query_all("""SELECT CASE WHEN time_in_hospital BETWEEN 1 AND 3 THEN '1-3 days'
      WHEN time_in_hospital BETWEEN 4 AND 7 THEN '4-7 days'
      WHEN time_in_hospital BETWEEN 8 AND 14 THEN '8-14 days'
      ELSE '15+ days' END AS length_of_stay_group, COUNT(*) AS total_encounters,
      ROUND(AVG(time_in_hospital),2) AS average_length_of_stay
      FROM encounters WHERE time_in_hospital IS NOT NULL GROUP BY length_of_stay_group
      ORDER BY MIN(time_in_hospital)""")
    return {"length_of_stay_analytics":[{"length_of_stay_group":r["length_of_stay_group"],"total_encounters":int(r["total_encounters"]),"average_length_of_stay":float(r["average_length_of_stay"])} for r in rows]}

@router.get("/diagnoses")
def top_diagnoses(limit:int=Query(10,ge=1,le=100),_:dict=Depends(access)):
    return query_all("""SELECT diagnosis_code, COUNT(*) AS total_records FROM encounter_diagnoses
      WHERE diagnosis_code IS NOT NULL GROUP BY diagnosis_code ORDER BY total_records DESC LIMIT %s""",(limit,))

@router.get("/medications")
def top_medications(limit:int=Query(10,ge=1,le=100),_:dict=Depends(access)):
    return query_all("""SELECT medication, COUNT(*) AS total_records FROM encounter_medications
      GROUP BY medication ORDER BY total_records DESC LIMIT %s""",(limit,))
