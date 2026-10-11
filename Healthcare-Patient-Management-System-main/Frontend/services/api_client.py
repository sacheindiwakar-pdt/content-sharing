import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv(
    "API_BASE_URL",
    "http://127.0.0.1:8000"
)


def get_analytics_overview():
    response = requests.get(
        f"{API_URL}/analytics/overview",
        timeout=10
    )
    response.raise_for_status()
    return response.json()


def get_analytics(endpoint):
    response = requests.get(
        f"{API_URL}/analytics/{endpoint}",
        timeout=10
    )
    response.raise_for_status()
    return response.json()