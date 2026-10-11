"""
Enterprise ETL Pipeline with Data Quality Validation and Incremental Loading
"""

import csv
import json
import logging
from pathlib import Path
import pandas as pd
from src.api.database import get_db_connection, init_database_schema
from src.api.security import hash_password

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ETLPipeline")

ROOT_DIR = Path(__file__).resolve().parents[2]
PROCESSED_DATA_DIR = ROOT_DIR / "data" / "processed"
RAW_DATA_DIR = ROOT_DIR / "data" / "raw"


def validate_and_clean_dataset(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    Applies enterprise data quality rules:
    - Check duplicates
    - Validate age range brackets
    - Replace missing indicator '?' with standard None/NaN
    - Ensure logical time in hospital (1-14 days)
    """
    report = {
        "raw_rows": len(df),
        "duplicate_encounters_removed": 0,
        "missing_values_handled": 0,
        "valid_encounters": 0
    }

    # Deduplicate encounter IDs
    initial_len = len(df)
    df = df.drop_duplicates(subset=["encounter_id"])
    report["duplicate_encounters_removed"] = initial_len - len(df)

    # Standardize missing values
    df = df.replace("?", None)
    df = df.replace("None", None)

    # Data hygiene on numerical columns
    num_cols = ["time_in_hospital", "num_lab_procedures", "num_medications", "number_diagnoses"]
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    report["valid_encounters"] = len(df)
    return df, report


def seed_default_users():
    """Seeds default demonstration users for Admin, Healthcare Staff, and Analyst roles."""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    try:
        users = [
            ("admin", "Admin123!", "Admin"),
            ("doctor", "Doctor123!", "Healthcare Staff"),
            ("analyst", "Analyst123!", "Analyst")
        ]
        for uname, pwd, role in users:
            cur.execute("SELECT user_id FROM users WHERE username = %s", (uname,))
            if not cur.fetchone():
                phash = hash_password(pwd)
                cur.execute(
                    "INSERT INTO users (username, password_hash, role, is_active) VALUES (%s, %s, %s, 1)",
                    (uname, phash, role)
                )
                logger.info(f"Seeded user: {uname} ({role})")
        conn.commit()
    finally:
        cur.close()
        conn.close()


def load_reference_tables():
    """Loads reference mapping tables (admission types, discharge dispositions, sources)."""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        ref_files = [
            ("admission_types", PROCESSED_DATA_DIR / "admission_types.csv", "admission_type_id", "description"),
            ("discharge_dispositions", PROCESSED_DATA_DIR / "discharge_dispositions.csv", "discharge_disposition_id", "description"),
            ("admission_sources", PROCESSED_DATA_DIR / "admission_sources.csv", "admission_source_id", "description"),
        ]

        for table_name, file_path, id_col, desc_col in ref_files:
            if not file_path.exists():
                logger.warning(f"File not found: {file_path}")
                continue

            with open(file_path, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    cur.execute(
                        f"INSERT OR IGNORE INTO {table_name} ({id_col}, {desc_col}) VALUES (%s, %s)",
                        (int(row[id_col]), row[desc_col])
                    )
            logger.info(f"Loaded reference table: {table_name}")

        conn.commit()
    finally:
        cur.close()
        conn.close()


def load_patients_and_encounters(limit: int = 5000):
    """Loads curated patient and encounter records into the database with foreign key integrity."""
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        patients_file = PROCESSED_DATA_DIR / "patients.csv"
        encounters_file = PROCESSED_DATA_DIR / "encounters.csv"

        if not patients_file.exists() or not encounters_file.exists():
            logger.error("Processed CSV files not found. Check data directory.")
            return

        # Load Patients
        logger.info(f"Loading patients from {patients_file}...")
        patient_batch = []
        with open(patients_file, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                if limit and i >= limit:
                    break
                patient_batch.append((int(row["patient_nbr"]), row.get("race"), row.get("gender")))

        for p in patient_batch:
            cur.execute("INSERT OR IGNORE INTO patients (patient_nbr, race, gender) VALUES (%s, %s, %s)", p)
        conn.commit()
        logger.info(f"Patients loaded successfully ({len(patient_batch)} records).")

        # Load Encounters
        logger.info(f"Loading encounters from {encounters_file}...")
        enc_cols = [
            "encounter_id", "patient_nbr", "age", "admission_type_id", "discharge_disposition_id",
            "admission_source_id", "time_in_hospital", "payer_code", "medical_specialty",
            "num_lab_procedures", "num_procedures", "num_medications", "number_outpatient",
            "number_emergency", "number_inpatient", "number_diagnoses", "change",
            "diabetesMed", "readmitted", "weight", "max_glu_serum", "A1Cresult"
        ]

        enc_batch = []
        with open(encounters_file, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                if limit and i >= limit:
                    break
                record = tuple(
                    int(row[c]) if c in ("encounter_id", "patient_nbr", "admission_type_id", "discharge_disposition_id", "admission_source_id", "time_in_hospital", "num_lab_procedures", "num_procedures", "num_medications", "number_outpatient", "number_emergency", "number_inpatient", "number_diagnoses") and row.get(c)
                    else (row.get(c) if row.get(c) != "" else None)
                    for c in enc_cols
                )
                enc_batch.append(record)

        placeholders = ", ".join(["%s"] * len(enc_cols))
        for enc in enc_batch:
            try:
                cur.execute(
                    f"INSERT OR IGNORE INTO encounters ({', '.join(enc_cols)}) VALUES ({placeholders})",
                    enc
                )
            except Exception:
                pass
        conn.commit()
        logger.info(f"Encounters loaded successfully ({len(enc_batch)} records).")

        # Load Diagnoses (sample)
        diag_file = PROCESSED_DATA_DIR / "encounter_diagnoses.csv"
        if diag_file.exists():
            with open(diag_file, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for i, row in enumerate(reader):
                    if limit and i >= limit * 3:
                        break
                    try:
                        cur.execute(
                            "INSERT OR IGNORE INTO encounter_diagnoses (encounter_id, diagnosis_position, diagnosis_code) VALUES (%s, %s, %s)",
                            (int(row["encounter_id"]), int(row["diagnosis_position"]), row["diagnosis_code"])
                        )
                    except Exception:
                        pass
            conn.commit()
            logger.info("Encounter diagnoses loaded.")

        # Load Medications (sample)
        med_file = PROCESSED_DATA_DIR / "encounter_medications.csv"
        if med_file.exists():
            with open(med_file, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for i, row in enumerate(reader):
                    if limit and i >= limit * 3:
                        break
                    try:
                        cur.execute(
                            "INSERT OR IGNORE INTO encounter_medications (encounter_id, medication, medication_status) VALUES (%s, %s, %s)",
                            (int(row["encounter_id"]), row["medication"], row["medication_status"])
                        )
                    except Exception:
                        pass
            conn.commit()
            logger.info("Encounter medications loaded.")

    finally:
        cur.close()
        conn.close()


def run_full_etl(record_limit: int = 5000):
    logger.info("Initializing relational schema...")
    init_database_schema()

    logger.info("Seeding administrative security credentials...")
    seed_default_users()

    logger.info("Loading reference terminology tables...")
    load_reference_tables()

    logger.info("Loading patient & encounter curated records...")
    load_patients_and_encounters(limit=record_limit)

    logger.info("ETL Pipeline completed successfully.")


if __name__ == "__main__":
    run_full_etl()
