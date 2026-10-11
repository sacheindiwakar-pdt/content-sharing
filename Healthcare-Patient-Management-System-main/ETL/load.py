
from pathlib import Path
import csv
import os

from matplotlib.pyplot import table

from sqlalchemy import table
import mysql.connector
from mysql.connector import Error

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed"
BATCH_SIZE = 1000

DB_NAME = os.getenv("DB_NAME", "healthcare_management")
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "")
}

FILES = {
    "patients": "patients.csv",
    "admission_types": "admission_types.csv",
    "discharge_dispositions": "discharge_dispositions.csv",
    "admission_sources": "admission_sources.csv",
    "encounters": "encounters.csv",
    "encounter_diagnoses": "encounter_diagnoses.csv",
    "encounter_medications": "encounter_medications.csv"
}

PRIMARY_KEYS = {
    "patients": ["patient_nbr"],
    "admission_types": ["admission_type_id"],
    "discharge_dispositions": ["discharge_disposition_id"],
    "admission_sources": ["admission_source_id"],
    "encounters": ["encounter_id"],
    "encounter_diagnoses": ["encounter_id", "diagnosis_position"],
    "encounter_medications": ["encounter_id", "medication"]
}

INTEGER_COLUMNS = {
    "time_in_hospital", "num_lab_procedures", "num_procedures",
    "num_medications", "number_outpatient", "number_emergency",
    "number_inpatient", "number_diagnoses", "diagnosis_position"
}

def sql_type(column):
    if column in {"encounter_id", "patient_nbr"} or column.endswith("_id"):
        return "BIGINT"
    if column in INTEGER_COLUMNS:
        return "INT"
    if column == "description":
        return "VARCHAR(500)"
    if column in {"diagnosis_code", "medication", "medication_status"}:
        return "VARCHAR(100)"
    return "VARCHAR(255)"

def create_table(cursor, table):
    path = DATA / FILES[table]
    if not path.exists():
        raise FileNotFoundError(f"Missing input file: {path}")

    with open(path, newline="", encoding="utf-8-sig") as f:
        columns = next(csv.reader(f))

    if not columns or any(not c.strip() for c in columns):
        raise ValueError(f"Invalid CSV header: {path}")

    
    required_columns = set(PRIMARY_KEYS[table])

    if table == "encounters":
        required_columns.update([
        "patient_nbr",
        "admission_type_id",
        "discharge_disposition_id",
        "admission_source_id"
    ])

    if table in {"encounter_diagnoses", "encounter_medications"}:
        required_columns.add("encounter_id")

    definitions = [
    f"`{col}` {sql_type(col)} "
    f"{'NOT NULL' if col in required_columns else 'NULL'}"
    for col in columns
]


    definitions.append(
        "PRIMARY KEY (" +
        ", ".join(f"`{col}`" for col in PRIMARY_KEYS[table]) +
        ")"
    )

    if table == "encounters":
        definitions.extend([
            "CONSTRAINT fk_encounter_patient "
            "FOREIGN KEY (`patient_nbr`) REFERENCES "
            "`patients` (`patient_nbr`)",
            "CONSTRAINT fk_admission_type "
            "FOREIGN KEY (`admission_type_id`) REFERENCES "
            "`admission_types` (`admission_type_id`)",
            "CONSTRAINT fk_discharge_disposition "
            "FOREIGN KEY (`discharge_disposition_id`) REFERENCES "
            "`discharge_dispositions` (`discharge_disposition_id`)",
            "CONSTRAINT fk_admission_source "
            "FOREIGN KEY (`admission_source_id`) REFERENCES "
            "`admission_sources` (`admission_source_id`)"
        ])

    if table in {"encounter_diagnoses", "encounter_medications"}:
        constraint = (
            "fk_diagnosis_encounter"
            if table == "encounter_diagnoses"
            else "fk_medication_encounter"
        )
        definitions.append(
            f"CONSTRAINT {constraint} FOREIGN KEY (`encounter_id`) "
            "REFERENCES `encounters` (`encounter_id`)"
        )

    cursor.execute(
        f"CREATE TABLE IF NOT EXISTS `{table}` ("
        + ", ".join(definitions)
        + ") ENGINE=InnoDB"
    )

def load_table(connection, cursor, table):
    path = DATA / FILES[table]

    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        columns = reader.fieldnames

        if not columns:
            raise ValueError(f"No CSV columns found: {path}")

        quoted_columns = ", ".join(f"`{c}`" for c in columns)
        placeholders = ", ".join(["%s"] * len(columns))
        updates = [
            c for c in columns if c not in PRIMARY_KEYS[table]
        ]

        if updates:
            update_sql = ", ".join(
                f"`{c}` = VALUES(`{c}`)" for c in updates
            )
        else:
            update_sql = (
                f"`{PRIMARY_KEYS[table][0]}` = "
                f"VALUES(`{PRIMARY_KEYS[table][0]}`)"
            )

        query = (
            f"INSERT INTO `{table}` ({quoted_columns}) "
            f"VALUES ({placeholders}) "
            f"ON DUPLICATE KEY UPDATE {update_sql}"
        )

        batch = []
        total = 0

        for row in reader:
            batch.append(tuple(
                None if row[col] is None or row[col] == ""
                else row[col]
                for col in columns
            ))

            if len(batch) >= BATCH_SIZE:
                cursor.executemany(query, batch)
                connection.commit()
                total += len(batch)
                batch.clear()

        if batch:
            cursor.executemany(query, batch)
            connection.commit()
            total += len(batch)

    print(f"Loaded {total:,} rows into {table}")

def main():
    connection = None
    cursor = None

    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()

        cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` "
            "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
        connection.commit()

        cursor.execute(f"USE `{DB_NAME}`")

        # Create tables in dependency order.
        for table in FILES:
            create_table(cursor, table)

        connection.commit()

        # Load parent tables before dependent tables.
        for table in FILES:
            load_table(connection, cursor, table)

        print("\nDatabase loading completed.")

    except Exception:
        if connection and connection.is_connected():
            connection.rollback()
        raise

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

if __name__ == "__main__":
    main()
