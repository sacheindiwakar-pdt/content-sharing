
from pathlib import Path
import pandas as pd

DATA_PATH = Path("../data/raw/diabetic_data.csv")

REQUIRED_COLUMNS = {
    "encounter_id", "patient_nbr", "race", "gender", "age",
    "admission_type_id", "time_in_hospital",
    "num_lab_procedures", "num_medications",
    "number_outpatient", "number_inpatient",
    "number_emergency", "diag_1", "diag_2", "diag_3",
    "insulin", "readmitted"
}

def extract_data(path=DATA_PATH):
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path.resolve()}")

    df = pd.read_csv(path, na_values=["?"], low_memory=False)

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    print(f"Extracted {len(df):,} rows and {len(df.columns)} columns")
    return df

if __name__ == "__main__":
    df = extract_data()
    print(df.head())
    print(df.shape)
