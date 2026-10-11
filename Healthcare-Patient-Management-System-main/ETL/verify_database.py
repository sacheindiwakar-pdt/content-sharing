
import csv
import os
import mysql.connector

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed"
DB_NAME = os.getenv("DB_NAME", "healthcare_management")

CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "")
}

TABLES = {
    "patients": "patients.csv",
    "encounters": "encounters.csv",
    "encounter_diagnoses": "encounter_diagnoses.csv",
    "encounter_medications": "encounter_medications.csv",
    "admission_types": "admission_types.csv",
    "discharge_dispositions": "discharge_dispositions.csv",
    "admission_sources": "admission_sources.csv"
}

CHECKS = {
    "encounters_without_patients": """
        SELECT COUNT(*) FROM encounters e
        LEFT JOIN patients p ON e.patient_nbr = p.patient_nbr
        WHERE p.patient_nbr IS NULL
    """,
    "diagnoses_without_encounters": """
        SELECT COUNT(*) FROM encounter_diagnoses d
        LEFT JOIN encounters e ON d.encounter_id = e.encounter_id
        WHERE e.encounter_id IS NULL
    """,
    "medications_without_encounters": """
        SELECT COUNT(*) FROM encounter_medications m
        LEFT JOIN encounters e ON m.encounter_id = e.encounter_id
        WHERE e.encounter_id IS NULL
    """,
    "invalid_admission_types": """
        SELECT COUNT(*) FROM encounters e
        LEFT JOIN admission_types a
          ON e.admission_type_id = a.admission_type_id
        WHERE a.admission_type_id IS NULL
    """,
    "invalid_discharge_dispositions": """
        SELECT COUNT(*) FROM encounters e
        LEFT JOIN discharge_dispositions d
          ON e.discharge_disposition_id = d.discharge_disposition_id
        WHERE d.discharge_disposition_id IS NULL
    """,
    "invalid_admission_sources": """
        SELECT COUNT(*) FROM encounters e
        LEFT JOIN admission_sources s
          ON e.admission_source_id = s.admission_source_id
        WHERE s.admission_source_id IS NULL
    """
}

def csv_count(filename):
    with open(DATA / filename, encoding="utf-8-sig", newline="") as f:
        return sum(1 for _ in csv.DictReader(f))

def main():
    connection = mysql.connector.connect(
        **CONFIG, database=DB_NAME
    )
    cursor = connection.cursor()
    failures = []

    try:
        print("\n--- DATABASE VERIFICATION ---")

        for table, filename in TABLES.items():
            cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
            actual = cursor.fetchone()[0]
            expected = csv_count(filename)
            passed = actual == expected

            print(
                f"{'PASS' if passed else 'FAIL'}: {table}: "
                f"database={actual:,}, CSV={expected:,}"
            )

            if not passed:
                failures.append(f"Row count mismatch: {table}")

        for name, query in CHECKS.items():
            cursor.execute(query)
            count = cursor.fetchone()[0]
            passed = count == 0

            print(
                f"{'PASS' if passed else 'FAIL'}: "
                f"{name} = {count}"
            )

            if not passed:
                failures.append(f"Relationship failure: {name}")

        if failures:
            raise RuntimeError("; ".join(failures))

        print("\nAll database verification checks passed.")

    finally:
        cursor.close()
        connection.close()

if __name__ == "__main__":
    main()
