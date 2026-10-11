
import pandas as pd

REQUIRED_COLUMNS = {
    "encounter_id",
    "patient_nbr",
    "race",
    "gender",
    "age",
    "admission_type_id",
    "time_in_hospital",
    "num_lab_procedures",
    "num_medications",
    "number_outpatient",
    "number_inpatient",
    "number_emergency",
    "diag_1",
    "diag_2",
    "diag_3",
    "insulin",
    "readmitted",
}

NUMERIC_COLUMNS = [
    "encounter_id",
    "patient_nbr",
    "admission_type_id",
    "time_in_hospital",
    "num_lab_procedures",
    "num_medications",
    "number_outpatient",
    "number_inpatient",
    "number_emergency",
]

ALLOWED_VALUES = {
    "gender": {"Male", "Female", "Unknown/Invalid"},
    "readmitted": {"<30", ">30", "NO"},
    "insulin": {"No", "Down", "Steady", "Up"},
}


def validate_data(df):
    errors = []
    warnings = []

    # 1. Check whether the DataFrame is empty
    if df.empty:
        errors.append("Dataset is empty.")
        return errors, warnings

    # 2. Check required columns
    missing_columns = REQUIRED_COLUMNS - set(df.columns)

    if missing_columns:
        errors.append(
            f"Missing required columns: {sorted(missing_columns)}"
        )
        return errors, warnings

    # 3. Check missing critical identifiers
    for column in ["encounter_id", "patient_nbr"]:
        missing_count = int(df[column].isna().sum())

        if missing_count:
            errors.append(
                f"{column} contains {missing_count} missing values."
            )

    # 4. Check duplicate encounter IDs
    duplicate_count = int(
        df["encounter_id"].duplicated().sum()
    )

    if duplicate_count:
        errors.append(
            f"Found {duplicate_count} duplicate encounter IDs."
        )

    # 5. Check missing readmission labels
    missing_labels = int(df["readmitted"].isna().sum())

    if missing_labels:
        errors.append(
            f"Found {missing_labels} missing readmission labels."
        )

    # 6. Check numeric columns
    for column in NUMERIC_COLUMNS:
        values = pd.to_numeric(df[column], errors="coerce")

        invalid_count = int(
            (df[column].notna() & values.isna()).sum()
        )

        if invalid_count:
            errors.append(
                f"{column} contains {invalid_count} non-numeric values."
            )

    # 7. Check impossible numeric values
    numeric_checks = {
        "time_in_hospital": lambda s: s < 1,
        "num_lab_procedures": lambda s: s < 0,
        "num_medications": lambda s: s < 0,
        "number_outpatient": lambda s: s < 0,
        "number_inpatient": lambda s: s < 0,
        "number_emergency": lambda s: s < 0,
    }

    for column, condition in numeric_checks.items():
        values = pd.to_numeric(df[column], errors="coerce")
        invalid_count = int(condition(values).fillna(False).sum())

        if invalid_count:
            errors.append(
                f"{column} contains {invalid_count} invalid values."
            )

    # 8. Check unexpected categorical values
    for column, allowed in ALLOWED_VALUES.items():
        unexpected = set(
            df[column].dropna().astype(str).unique()
        ) - allowed

        if unexpected:
            warnings.append(
                f"{column} contains unexpected values: "
                f"{sorted(unexpected)}"
            )

    # 9. Report missing values
    missing_columns = df.columns[df.isna().any()].tolist()

    if missing_columns:
        warnings.append(
            f"{len(missing_columns)} columns contain missing values."
        )

    return errors, warnings


if __name__ == "__main__":
    from extract import extract_data

    df = extract_data()
    errors, warnings = validate_data(df)

    print("\n--- VALIDATION REPORT ---")
    print(f"Rows checked: {len(df):,}")
    print(f"Columns checked: {len(df.columns)}")
    print(f"Errors: {len(errors)}")
    print(f"Warnings: {len(warnings)}")

    for error in errors:
        print(f"ERROR: {error}")

    for warning in warnings:
        print(f"WARNING: {warning}")

    if errors:
        print("\nValidation FAILED.")
    else:
        print("\nValidation PASSED.")
