
from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_FILE = ROOT / "data" / "raw" / "diabetic_data.csv"
CLEAN_FILE = ROOT / "data" / "processed" / "cleaned_encounters.csv"
AUDIT_FILE = ROOT / "data" / "processed" / "cleaning_report.json"

EXCLUDED_COLUMNS = ["weight", "max_glu_serum", "A1Cresult"]
UNKNOWN_COLUMNS = [
    "race",
    "medical_specialty",
    "payer_code"
]
DIAGNOSIS_COLUMNS = ["diag_1", "diag_2", "diag_3"]

def clean_data(df):
    df = df.copy()
    original_rows = len(df)

    # Required identifiers must be present.
    required = ["encounter_id", "patient_nbr"]
    if df[required].isna().any().any():
        raise ValueError("Missing encounter_id or patient_nbr.")

    if df["encounter_id"].duplicated().any():
        raise ValueError("Duplicate encounter_id values detected.")

    # Remove columns excluded from the initial curated dataset.
    removed_columns = [c for c in EXCLUDED_COLUMNS if c in df.columns]
    df = df.drop(columns=removed_columns)

    # Normalize categorical text without changing its meaning.
    for col in df.select_dtypes(include=["object", "string"]).columns:
        df[col] = df[col].map(
            lambda value: value.strip() if isinstance(value, str) else value
        )
        df[col] = df[col].replace("", pd.NA)

    # Explicitly represent missing categories.
    for col in UNKNOWN_COLUMNS:
        if col in df.columns:
            df[col] = df[col].fillna("Unknown")

    # Preserve missing diagnoses with an explicit marker.
    for col in DIAGNOSIS_COLUMNS:
        if col in df.columns:
            df[col] = df[col].fillna("Unknown")

    # Normalize known binary categorical columns.
    binary_columns = [
        "gender", "diabetesMed",
        "change", "readmitted"
    ]
    for col in binary_columns:
        if col in df.columns:
            df[col] = df[col].str.strip()

    # Validate identifiers again after cleaning.
    if df["encounter_id"].isna().any():
        raise ValueError("Missing encounter_id after cleaning.")

    if df["patient_nbr"].isna().any():
        raise ValueError("Missing patient_nbr after cleaning.")

    report = {
        "source_rows": original_rows,
        "cleaned_rows": len(df),
        "source_columns": original_rows and len(
            pd.read_csv(RAW_FILE, nrows=0)
        ),
        "cleaned_columns": len(df.columns),
        "excluded_columns": removed_columns,
        "missing_values_remaining": {
            col: int(count)
            for col, count in df.isna().sum().items()
            if count > 0
        },
        "duplicate_encounter_ids": int(
            df["encounter_id"].duplicated().sum()
        ),
        "unique_patients": int(df["patient_nbr"].nunique())
    }

    return df, report

def main():
    if not RAW_FILE.exists():
        raise FileNotFoundError(f"Source dataset not found: {RAW_FILE}")

    df = pd.read_csv(
    RAW_FILE,
    na_values=["?"],
    dtype={"payer_code": "string"},
    low_memory=False
)
    cleaned_df, report = clean_data(df)

    CLEAN_FILE.parent.mkdir(parents=True, exist_ok=True)
    cleaned_df.to_csv(CLEAN_FILE, index=False)

    with open(AUDIT_FILE, "w", encoding="utf-8") as file:
        json.dump(report, file, indent=4)

    print("\n--- CLEANING REPORT ---")
    print(f"Source rows: {report['source_rows']:,}")
    print(f"Cleaned rows: {report['cleaned_rows']:,}")
    print(f"Cleaned columns: {report['cleaned_columns']}")
    print(f"Unique patients: {report['unique_patients']:,}")
    print(f"Excluded columns: {report['excluded_columns']}")
    print(f"Remaining missing values: {report['missing_values_remaining']}")
    print(f"\nSaved: {CLEAN_FILE}")
    print(f"Audit report: {AUDIT_FILE}")

if __name__ == "__main__":
    main()
