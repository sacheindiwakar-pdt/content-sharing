
from pathlib import Path
import pandas as pd

DATA = Path(__file__).resolve().parents[1] / "data" / "processed"

def check(condition, message):
    if not condition:
        raise AssertionError(message)
    print(f"PASS: {message}")

patients = pd.read_csv(DATA / "patients.csv")
encounters = pd.read_csv(DATA / "encounters.csv")
diagnoses = pd.read_csv(DATA / "encounter_diagnoses.csv")
medications = pd.read_csv(DATA / "encounter_medications.csv")

check(len(encounters) == 101766, "Encounter count is correct")
check(encounters["encounter_id"].is_unique,
      "Encounter IDs are unique")
check(patients["patient_nbr"].is_unique,
      "Patient IDs are unique")
check(len(patients) == 71518, "Patient count is correct")
check(set(encounters["patient_nbr"].dropna()).issubset(
    set(patients["patient_nbr"])),
    "Every encounter belongs to a known patient")
check(set(diagnoses["encounter_id"]).issubset(
    set(encounters["encounter_id"])),
    "Diagnosis records reference valid encounters")
check(set(medications["encounter_id"]).issubset(
    set(encounters["encounter_id"])),
    "Medication records reference valid encounters")
check(len(diagnoses) == 305298, "Diagnosis row count is correct")
check(len(medications) == 2340618,
      "Medication row count is correct")

for filename, id_column in [
    ("admission_types.csv", "admission_type_id"),
    ("discharge_dispositions.csv", "discharge_disposition_id"),
    ("admission_sources.csv", "admission_source_id")
]:
    table = pd.read_csv(DATA / filename, keep_default_na=False)
    check(table[id_column].is_unique,
          f"{filename}: IDs are unique")
    check(table["description"].ne("").all(),
          f"{filename}: descriptions are not blank")

print("\nAll transformation tests passed.")
