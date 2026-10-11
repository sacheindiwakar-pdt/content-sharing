"""
Automated Pytest Suite for ETL Data Quality, Ingestion, and Schema Rules
"""

import pytest
import pandas as pd
from pathlib import Path
from src.services.etl_pipeline import validate_and_clean_dataset
from src.api.database import get_db_connection


def test_data_cleaning_and_deduplication():
    sample_data = pd.DataFrame([
        {"encounter_id": 101, "time_in_hospital": "3", "num_lab_procedures": "45", "num_medications": "10", "number_diagnoses": "5"},
        {"encounter_id": 101, "time_in_hospital": "3", "num_lab_procedures": "45", "num_medications": "10", "number_diagnoses": "5"}, # Duplicate
        {"encounter_id": 102, "time_in_hospital": "?", "num_lab_procedures": "20", "num_medications": "8", "number_diagnoses": "3"},
    ])

    cleaned_df, report = validate_and_clean_dataset(sample_data)
    assert len(cleaned_df) == 2, "Duplicate encounter should have been dropped"
    assert report["duplicate_encounters_removed"] == 1
    assert cleaned_df.loc[cleaned_df["encounter_id"] == 102, "time_in_hospital"].iloc[0] == 0


def test_database_table_integrity():
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT COUNT(*) AS cnt FROM patients")
        patients_cnt = cur.fetchone()["cnt"]
        assert patients_cnt > 0, "Patients table should contain populated records"

        cur.execute("SELECT COUNT(*) AS cnt FROM encounters")
        encounters_cnt = cur.fetchone()["cnt"]
        assert encounters_cnt > 0, "Encounters table should contain populated records"

        cur.execute("SELECT COUNT(*) AS cnt FROM admission_types")
        adm_cnt = cur.fetchone()["cnt"]
        assert adm_cnt > 0, "Admission types terminology should be seeded"
    finally:
        cur.close()
        conn.close()
