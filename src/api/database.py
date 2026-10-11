"""
Adaptive Database Connection & Execution Layer
Supports MySQL (production / configured) and local SQLite (fallback).
Ensures zero-friction local execution while maintaining full relational integrity.
"""

import os
import sqlite3
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

ROOT_DIR = Path(__file__).resolve().parents[2]
SQLITE_DB_PATH = ROOT_DIR / "data" / "healthcare.db"

DB_TYPE = os.getenv("DB_TYPE", "").lower()
DB_HOST = os.getenv("DB_HOST", "")
DB_USER = os.getenv("DB_USER", "")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "healthcare_management")
DB_PORT = os.getenv("DB_PORT", "3306")


class DBConnectionWrapper:
    """Wrapper that provides a uniform cursor interface for both SQLite and MySQL."""
    def __init__(self, raw_conn, is_sqlite=False):
        self.raw_conn = raw_conn
        self.is_sqlite = is_sqlite

    def cursor(self, dictionary=True):
        if self.is_sqlite:
            cur = self.raw_conn.cursor()
            return SQLiteDictCursor(cur) if dictionary else cur
        else:
            return self.raw_conn.cursor(dictionary=dictionary)

    def commit(self):
        self.raw_conn.commit()

    def rollback(self):
        self.raw_conn.rollback()

    def close(self):
        self.raw_conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.rollback()
        self.close()


class SQLiteDictCursor:
    """Dictionary-returning cursor wrapper for SQLite."""
    def __init__(self, cursor):
        self.cursor = cursor
        self.description = None

    def execute(self, sql, params=()):
        # Convert MySQL %s placeholders to SQLite ? placeholders
        sql_converted = sql.replace("%s", "?")
        res = self.cursor.execute(sql_converted, params)
        self.description = self.cursor.description
        return res

    def executemany(self, sql, params_seq):
        sql_converted = sql.replace("%s", "?")
        return self.cursor.executemany(sql_converted, params_seq)

    def fetchone(self):
        row = self.cursor.fetchone()
        if row is None:
            return None
        cols = [d[0] for d in self.cursor.description]
        return dict(zip(cols, row))

    def fetchall(self):
        rows = self.cursor.fetchall()
        if not rows:
            return []
        cols = [d[0] for d in self.cursor.description]
        return [dict(zip(cols, row)) for row in rows]

    @property
    def rowcount(self):
        return self.cursor.rowcount

    def close(self):
        self.cursor.close()


def get_db_connection():
    """
    Returns an active database connection.
    Attempts MySQL first if DB_HOST is provided, otherwise connects to local SQLite.
    """
    if DB_HOST and DB_USER and DB_TYPE != "sqlite":
        try:
            import mysql.connector
            port = int(DB_PORT)
            conn = mysql.connector.connect(
                host=DB_HOST,
                port=port,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                connection_timeout=5,
                autocommit=False,
            )
            return DBConnectionWrapper(conn, is_sqlite=False)
        except Exception:
            # Fall back to SQLite if MySQL fails to connect
            pass

    # SQLite fallback
    SQLITE_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(SQLITE_DB_PATH), check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON;")
    return DBConnectionWrapper(conn, is_sqlite=True)


def init_database_schema():
    """Initializes tables, indexes, and default administrative security roles."""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=False)

    try:
        # Schema creation DDL compatible with SQLite & MySQL
        cur.execute("""
        CREATE TABLE IF NOT EXISTS roles (
            role_name VARCHAR(50) PRIMARY KEY,
            description VARCHAR(255)
        );
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(100) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            role VARCHAR(50) NOT NULL,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (role) REFERENCES roles(role_name)
        );
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            patient_nbr BIGINT PRIMARY KEY,
            race VARCHAR(100),
            gender VARCHAR(50)
        );
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS admission_types (
            admission_type_id BIGINT PRIMARY KEY,
            description VARCHAR(500)
        );
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS discharge_dispositions (
            discharge_disposition_id BIGINT PRIMARY KEY,
            description VARCHAR(500)
        );
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS admission_sources (
            admission_source_id BIGINT PRIMARY KEY,
            description VARCHAR(500)
        );
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS encounters (
            encounter_id BIGINT PRIMARY KEY,
            patient_nbr BIGINT NOT NULL,
            age VARCHAR(50),
            admission_type_id BIGINT,
            discharge_disposition_id BIGINT,
            admission_source_id BIGINT,
            time_in_hospital INT,
            payer_code VARCHAR(50),
            medical_specialty VARCHAR(100),
            num_lab_procedures INT,
            num_procedures INT,
            num_medications INT,
            number_outpatient INT,
            number_emergency INT,
            number_inpatient INT,
            number_diagnoses INT,
            change VARCHAR(50),
            diabetesMed VARCHAR(50),
            readmitted VARCHAR(50),
            weight VARCHAR(50),
            max_glu_serum VARCHAR(50),
            A1Cresult VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_nbr) REFERENCES patients(patient_nbr),
            FOREIGN KEY (admission_type_id) REFERENCES admission_types(admission_type_id),
            FOREIGN KEY (discharge_disposition_id) REFERENCES discharge_dispositions(discharge_disposition_id),
            FOREIGN KEY (admission_source_id) REFERENCES admission_sources(admission_source_id)
        );
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS encounter_diagnoses (
            encounter_id BIGINT NOT NULL,
            diagnosis_position INT NOT NULL,
            diagnosis_code VARCHAR(100),
            PRIMARY KEY (encounter_id, diagnosis_position),
            FOREIGN KEY (encounter_id) REFERENCES encounters(encounter_id)
        );
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS encounter_medications (
            encounter_id BIGINT NOT NULL,
            medication VARCHAR(100) NOT NULL,
            medication_status VARCHAR(100),
            PRIMARY KEY (encounter_id, medication),
            FOREIGN KEY (encounter_id) REFERENCES encounters(encounter_id)
        );
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id BIGINT,
            username VARCHAR(100) NOT NULL,
            action VARCHAR(100) NOT NULL,
            resource_type VARCHAR(100) NOT NULL,
            resource_id VARCHAR(255),
            outcome VARCHAR(30) NOT NULL,
            detail VARCHAR(500),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # Indexes for query optimization
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_encounters_patient ON encounters(patient_nbr);",
            "CREATE INDEX IF NOT EXISTS idx_encounters_readmitted ON encounters(readmitted);",
            "CREATE INDEX IF NOT EXISTS idx_encounters_time_hospital ON encounters(time_in_hospital);",
            "CREATE INDEX IF NOT EXISTS idx_encounters_admission_type ON encounters(admission_type_id);",
            "CREATE INDEX IF NOT EXISTS idx_diagnoses_code ON encounter_diagnoses(diagnosis_code);",
            "CREATE INDEX IF NOT EXISTS idx_medications_med ON encounter_medications(medication);",
            "CREATE INDEX IF NOT EXISTS idx_audit_time ON audit_logs(created_at);",
            "CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_logs(username);"
        ]
        for idx in indexes:
            try:
                cur.execute(idx)
            except Exception:
                pass

        # Seed roles
        roles = [
            ("Admin", "Full administrative control and user management"),
            ("Healthcare Staff", "Clinical operations and patient/encounter updates"),
            ("Analyst", "View reports, trends, and analytical dashboards")
        ]
        for role, desc in roles:
            cur.execute("INSERT OR IGNORE INTO roles (role_name, description) VALUES (?, ?)", (role, desc))

        conn.commit()
    finally:
        cur.close()
        conn.close()
