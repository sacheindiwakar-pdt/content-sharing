"""
Healthcare Operational Analytics & KPI Aggregations
"""

from fastapi import APIRouter, Depends, Query
from src.api.database import get_db_connection
from src.api.dependencies import require_roles

router = APIRouter(prefix="/analytics", tags=["Analytics"])
analytics_access = require_roles("Admin", "Healthcare Staff", "Analyst")


def fetch_all(sql, params=()):
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute(sql, params)
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()


@router.get("/overview")
def get_kpi_overview(current_user: dict = Depends(analytics_access)):
    rows = fetch_all(
        """
        SELECT 
            (SELECT COUNT(*) FROM patients) AS total_patients,
            COUNT(*) AS total_encounters,
            AVG(time_in_hospital) AS avg_length_of_stay,
            SUM(CASE WHEN readmitted IN ('<30', '>30') THEN 1 ELSE 0 END) AS total_readmissions,
            SUM(CASE WHEN readmitted = '<30' THEN 1 ELSE 0 END) AS early_readmissions_under_30,
            AVG(num_lab_procedures) AS avg_lab_procedures,
            AVG(num_medications) AS avg_medications
        FROM encounters
        """
    )
    r = rows[0] if rows else {}
    total_enc = int(r.get("total_encounters") or 0)
    total_readm = int(r.get("total_readmissions") or 0)
    readm_rate = round((total_readm / total_enc * 100), 2) if total_enc > 0 else 0.0

    return {
        "total_patients": int(r.get("total_patients") or 0),
        "total_encounters": total_enc,
        "average_length_of_stay": round(float(r.get("avg_length_of_stay") or 0), 2),
        "total_readmissions": total_readm,
        "early_readmissions_under_30": int(r.get("early_readmissions_under_30") or 0),
        "readmission_rate_percent": readm_rate,
        "average_lab_procedures": round(float(r.get("avg_lab_procedures") or 0), 1),
        "average_medications": round(float(r.get("avg_medications") or 0), 1)
    }


@router.get("/admissions")
def get_admission_trends(current_user: dict = Depends(analytics_access)):
    rows = fetch_all(
        """
        SELECT 
            e.admission_type_id,
            COALESCE(a.description, 'Standard Admission') AS admission_type,
            COUNT(*) AS total_encounters,
            ROUND(AVG(e.time_in_hospital), 2) AS avg_stay_days
        FROM encounters e
        LEFT JOIN admission_types a ON e.admission_type_id = a.admission_type_id
        GROUP BY e.admission_type_id, a.description
        ORDER BY total_encounters DESC
        """
    )
    return {"admission_breakdown": rows}


@router.get("/readmissions")
def get_readmission_insights(current_user: dict = Depends(analytics_access)):
    rows = fetch_all(
        """
        SELECT 
            readmitted AS status,
            COUNT(*) AS encounters,
            ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM encounters), 2) AS percentage
        FROM encounters
        GROUP BY readmitted
        ORDER BY encounters DESC
        """
    )
    total = sum(int(r["encounters"]) for r in rows)
    readmitted = sum(int(r["encounters"]) for r in rows if r["status"] in ("<30", ">30"))

    return {
        "total_encounters": total,
        "readmitted_encounters": readmitted,
        "readmission_rate_percent": round(100.0 * readmitted / total, 2) if total else 0.0,
        "status_breakdown": rows
    }


@router.get("/length-of-stay")
def get_length_of_stay_analysis(current_user: dict = Depends(analytics_access)):
    rows = fetch_all(
        """
        SELECT 
            CASE 
                WHEN time_in_hospital BETWEEN 1 AND 2 THEN '1-2 Days (Short)'
                WHEN time_in_hospital BETWEEN 3 AND 5 THEN '3-5 Days (Moderate)'
                WHEN time_in_hospital BETWEEN 6 AND 9 THEN '6-9 Days (Extended)'
                ELSE '10+ Days (Prolonged)'
            END AS stay_bracket,
            COUNT(*) AS encounter_count,
            ROUND(AVG(time_in_hospital), 2) AS avg_stay
        FROM encounters
        WHERE time_in_hospital IS NOT NULL
        GROUP BY stay_bracket
        ORDER BY MIN(time_in_hospital)
        """
    )
    return {"length_of_stay_distribution": rows}


@router.get("/demographics")
def get_demographic_trends(current_user: dict = Depends(analytics_access)):
    by_age = fetch_all(
        """
        SELECT age, COUNT(*) AS encounters,
               SUM(CASE WHEN readmitted IN ('<30', '>30') THEN 1 ELSE 0 END) AS readmitted_count
        FROM encounters
        GROUP BY age
        ORDER BY age
        """
    )
    by_gender = fetch_all(
        """
        SELECT p.gender, COUNT(*) AS total_patients
        FROM patients p
        GROUP BY p.gender
        """
    )
    return {
        "age_groups": by_age,
        "gender_distribution": by_gender
    }
