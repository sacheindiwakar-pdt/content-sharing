
from pathlib import Path
import csv
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"

SOURCE = RAW / "diabetic_data.csv"
MAPPING = RAW / "IDS_mapping.csv"
CLEANED = PROCESSED / "cleaned_encounters.csv"
REPORT = PROCESSED / "transformation_report.json"

EXCLUDED = ["weight", "max_glu_serum", "A1Cresult"]
DIAGNOSES = ["diag_1", "diag_2", "diag_3"]
DEMOGRAPHICS = ["race", "gender"]

MEDICATIONS = [
    "metformin", "repaglinide", "nateglinide", "chlorpropamide",
    "glimepiride", "acetohexamide", "glipizide", "glyburide",
    "tolbutamide", "pioglitazone", "rosiglitazone", "acarbose",
    "miglitol", "troglitazone", "tolazamide", "examide",
    "citoglipton", "insulin", "glyburide-metformin",
    "glipizide-metformin", "glimepiride-pioglitazone",
    "metformin-rosiglitazone", "metformin-pioglitazone"
]

MAPPING_SECTIONS = {
    "admission_type_id": "admission_types",
    "discharge_disposition_id": "discharge_dispositions",
    "admission_source_id": "admission_sources"
}


def parse_mappings():
    mappings = {key: [] for key in MAPPING_SECTIONS}
    current = None

    with open(MAPPING, encoding="utf-8-sig", newline="") as file:
        for row in csv.reader(file):
            row = [value.strip() for value in row]

            if not row or not any(row):
                continue

            header = row[0].lower()
            if header in MAPPING_SECTIONS and len(row) > 1:
                current = header
                continue

            if current is None or len(row) < 2 or not row[0]:
                continue

            try:
                mapping_id = int(row[0])
            except ValueError:
                continue

            description = ",".join(row[1:]).strip()

            mappings[current].append({
                current: mapping_id,
                "description": description
            })

    result = {}
    for key, table_name in MAPPING_SECTIONS.items():
        table = pd.DataFrame(mappings[key], columns=[key, "description"])

        if table.empty:
            raise ValueError(f"No mappings found for {key}")

        if table[key].duplicated().any():
            raise ValueError(f"Duplicate mapping IDs found for {key}")

        result[table_name] = table

    return result


def transform():
    PROCESSED.mkdir(parents=True, exist_ok=True)

    if not SOURCE.exists() or not CLEANED.exists() or not MAPPING.exists():
        raise FileNotFoundError(
            "Required files: diabetic_data.csv, cleaned_encounters.csv, "
            "and IDS_mapping.csv must exist in their expected folders."
        )

    # Load cleaned encounters and restore clinically useful columns.
    encounters = pd.read_csv(CLEANED, dtype={"payer_code": "string"})
    raw = pd.read_csv(
        SOURCE,
        na_values=["?"],
        dtype={"payer_code": "string"}
    )

    if encounters["encounter_id"].duplicated().any():
        raise ValueError("Duplicate encounter IDs in cleaned data.")

    if raw["encounter_id"].duplicated().any():
        raise ValueError("Duplicate encounter IDs in raw data.")

    for col in EXCLUDED:
        if col in raw.columns:
            encounters = encounters.merge(
                raw[["encounter_id", col]],
                on="encounter_id",
                how="left",
                validate="one_to_one"
            )

    # Create one patient record per patient.
    patient_columns = ["patient_nbr"] + DEMOGRAPHICS
    patients = encounters[patient_columns].copy()

    conflicts = {}
    for col in DEMOGRAPHICS:
        counts = patients.groupby("patient_nbr")[col].nunique(
            dropna=True
        )
        conflicts[col] = int((counts > 1).sum())

    patients = patients.drop_duplicates(
        subset=["patient_nbr"], keep="first"
    )

    # Create encounter-level records.
    medication_columns = [
        col for col in MEDICATIONS if col in encounters.columns
    ]
    diagnosis_columns = [
        col for col in DIAGNOSES if col in encounters.columns
    ]

    encounter_columns = [
    col for col in encounters.columns
    if col not in (
        DEMOGRAPHICS + medication_columns + diagnosis_columns
    )
]
    encounter_table = encounters[encounter_columns].copy()

    # Convert diagnosis columns into one row per diagnosis position.
    diagnosis_table = encounters[
        ["encounter_id"] + diagnosis_columns
    ].melt(
        id_vars=["encounter_id"],
        value_vars=diagnosis_columns,
        var_name="diagnosis_position",
        value_name="diagnosis_code"
    )

    diagnosis_table["diagnosis_position"] = (
        diagnosis_table["diagnosis_position"]
        .map({"diag_1": 1, "diag_2": 2, "diag_3": 3})
    )
    diagnosis_table["diagnosis_code"] = (
        diagnosis_table["diagnosis_code"].replace("Unknown", pd.NA)
    )

    # Convert medication columns into one row per encounter/medication.
    medication_table = encounters[
        ["encounter_id"] + medication_columns
    ].melt(
        id_vars=["encounter_id"],
        value_vars=medication_columns,
        var_name="medication",
        value_name="medication_status"
    )

    medication_table["medication_status"] = (
        medication_table["medication_status"].replace("", pd.NA)
    )

    # Parse the three sections in IDS_mapping.csv.
    reference_tables = parse_mappings()

    # Validate IDs before creating reference relationships.
    mapping_checks = {}
    for key, table_name in MAPPING_SECTIONS.items():
        if key not in encounter_table.columns:
            continue

        known_ids = set(reference_tables[table_name][key])
        source_ids = set(encounter_table[key].dropna().unique())
        unmapped = sorted(source_ids - known_ids)

        mapping_checks[key] = {
            "distinct_source_ids": len(source_ids),
            "unmapped_ids": unmapped
        }

    # Save transformed datasets.
    outputs = {
        "patients.csv": patients,
        "encounters.csv": encounter_table,
        "encounter_diagnoses.csv": diagnosis_table,
        "encounter_medications.csv": medication_table
    }

    for filename, table in outputs.items():
        table.to_csv(PROCESSED / filename, index=False)

    for table_name, table in reference_tables.items():
        table.to_csv(PROCESSED / f"{table_name}.csv", index=False)

    report = {
        "source_encounters": len(raw),
        "transformed_encounters": len(encounter_table),
        "unique_patients": len(patients),
        "diagnosis_rows": len(diagnosis_table),
        "medication_rows": len(medication_table),
        "restored_columns": [
            col for col in EXCLUDED if col in encounters.columns
        ],
        "patient_attribute_conflicts": conflicts,
        "reference_mapping_checks": mapping_checks,
        "reference_row_counts": {
            name: len(table)
            for name, table in reference_tables.items()
        }
    }

    with open(REPORT, "w", encoding="utf-8") as file:
        json.dump(report, file, indent=4)

    print("\n--- TRANSFORMATION REPORT ---")
    print(f"Source encounters: {len(raw):,}")
    print(f"Transformed encounters: {len(encounter_table):,}")
    print(f"Unique patients: {len(patients):,}")
    print(f"Diagnosis rows: {len(diagnosis_table):,}")
    print(f"Medication rows: {len(medication_table):,}")
    print(f"Reference mapping checks: {mapping_checks}")
    print(f"\nSaved transformed files to: {PROCESSED}")


if __name__ == "__main__":
    transform()
