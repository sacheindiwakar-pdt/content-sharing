"""
REST API Client for Streamlit Frontend
Handles authenticated calls, JWT tokens, session states, and error handling.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")


class APIClient:
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url.rstrip("/")

    def _headers(self, token: str = None) -> dict:
        headers = {"Accept": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def login(self, username: str, password: str) -> dict:
        url = f"{self.base_url}/auth/login"
        resp = requests.post(url, data={"username": username, "password": password}, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def get_profile(self, token: str) -> dict:
        url = f"{self.base_url}/auth/me"
        resp = requests.get(url, headers=self._headers(token), timeout=10)
        resp.raise_for_status()
        return resp.json()

    def get_analytics_overview(self, token: str) -> dict:
        url = f"{self.base_url}/analytics/overview"
        resp = requests.get(url, headers=self._headers(token), timeout=10)
        resp.raise_for_status()
        return resp.json()

    def get_admission_trends(self, token: str) -> dict:
        url = f"{self.base_url}/analytics/admissions"
        resp = requests.get(url, headers=self._headers(token), timeout=10)
        resp.raise_for_status()
        return resp.json()

    def get_readmission_insights(self, token: str) -> dict:
        url = f"{self.base_url}/analytics/readmissions"
        resp = requests.get(url, headers=self._headers(token), timeout=10)
        resp.raise_for_status()
        return resp.json()

    def get_length_of_stay(self, token: str) -> dict:
        url = f"{self.base_url}/analytics/length-of-stay"
        resp = requests.get(url, headers=self._headers(token), timeout=10)
        resp.raise_for_status()
        return resp.json()

    def get_demographics(self, token: str) -> dict:
        url = f"{self.base_url}/analytics/demographics"
        resp = requests.get(url, headers=self._headers(token), timeout=10)
        resp.raise_for_status()
        return resp.json()

    def list_patients(self, token: str, limit: int = 50, offset: int = 0, gender: str = None, race: str = None, search: str = None) -> list:
        url = f"{self.base_url}/patients"
        params = {"limit": limit, "offset": offset}
        if gender:
            params["gender"] = gender
        if race:
            params["race"] = race
        if search:
            params["search"] = search
        resp = requests.get(url, headers=self._headers(token), params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def get_patient(self, token: str, patient_nbr: int) -> dict:
        url = f"{self.base_url}/patients/{patient_nbr}"
        resp = requests.get(url, headers=self._headers(token), timeout=10)
        resp.raise_for_status()
        return resp.json()

    def get_patient_encounters(self, token: str, patient_nbr: int) -> list:
        url = f"{self.base_url}/patients/{patient_nbr}/encounters"
        resp = requests.get(url, headers=self._headers(token), timeout=10)
        resp.raise_for_status()
        return resp.json()

    def create_patient(self, token: str, data: dict) -> dict:
        url = f"{self.base_url}/patients"
        resp = requests.post(url, headers=self._headers(token), json=data, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def update_patient(self, token: str, patient_nbr: int, data: dict) -> dict:
        url = f"{self.base_url}/patients/{patient_nbr}"
        resp = requests.patch(url, headers=self._headers(token), json=data, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def delete_patient(self, token: str, patient_nbr: int) -> dict:
        url = f"{self.base_url}/patients/{patient_nbr}"
        resp = requests.delete(url, headers=self._headers(token), timeout=10)
        resp.raise_for_status()
        return resp.json()

    def list_encounters(self, token: str, limit: int = 50, offset: int = 0, patient_nbr: int = None, readmitted: str = None, age: str = None) -> list:
        url = f"{self.base_url}/encounters"
        params = {"limit": limit, "offset": offset}
        if patient_nbr:
            params["patient_nbr"] = patient_nbr
        if readmitted:
            params["readmitted"] = readmitted
        if age:
            params["age"] = age
        resp = requests.get(url, headers=self._headers(token), params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def get_encounter(self, token: str, encounter_id: int) -> dict:
        url = f"{self.base_url}/encounters/{encounter_id}"
        resp = requests.get(url, headers=self._headers(token), timeout=10)
        resp.raise_for_status()
        return resp.json()

    def create_encounter(self, token: str, data: dict) -> dict:
        url = f"{self.base_url}/encounters"
        resp = requests.post(url, headers=self._headers(token), json=data, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def update_encounter(self, token: str, encounter_id: int, data: dict) -> dict:
        url = f"{self.base_url}/encounters/{encounter_id}"
        resp = requests.patch(url, headers=self._headers(token), json=data, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def delete_encounter(self, token: str, encounter_id: int) -> dict:
        url = f"{self.base_url}/encounters/{encounter_id}"
        resp = requests.delete(url, headers=self._headers(token), timeout=10)
        resp.raise_for_status()
        return resp.json()

    def get_audit_logs(self, token: str, limit: int = 50) -> list:
        url = f"{self.base_url}/reports/audit-logs"
        resp = requests.get(url, headers=self._headers(token), params={"limit": limit}, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def export_encounters_csv_url(self) -> str:
        return f"{self.base_url}/reports/export/encounters/csv"

    def export_encounters_excel_url(self) -> str:
        return f"{self.base_url}/reports/export/encounters/excel"
