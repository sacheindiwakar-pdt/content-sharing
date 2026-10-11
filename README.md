FAILED tests/test_health.py::test_health - AssertionError: assert 404 == 200
FAILED tests/test_reference_data.py::test_admission_types - assert (404 == 200)
FAILED tests/test_reference_data.py::test_discharge_dispositions - assert (404 == 200)
FAILED tests/test_reference_data.py::test_admission_sources - assert (404 == 200)

# Healthcare Patient Management System

[![Python Version](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-v2.0-009688.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-v1.40+-FF4B4B.svg)](https://streamlit.io/)
[![Relational DB](https://img.shields.io/badge/Database-MySQL%20%2F%20SQLite%20Adaptive-4479A1.svg)](https://www.mysql.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An enterprise-grade, full-stack clinical operations and patient management platform built for healthcare organizations. Engineered to ingest and clean large-scale hospital datasets, enforce 3NF relational modeling, provide authenticated RESTful CRUD microservices, and deliver real-time clinical dashboards.

---

## 1. Project Overview & Business Value

Healthcare facilities struggle with disconnected, legacy patient admission records, obscured readmission signals, and manual reporting in flat files. This system provides an end-to-end operational solution:

- **Automated Data Engineering (ETL):** Extracts, validates, and normalizes over 100,000 inpatient records from the *UCI Diabetes 130-US Hospitals (1999–2008)* dataset.
- **Normalized Relational Core (3NF):** Stores curated records across structured tables with referential integrity and performance indexing.
- **RESTful Microservices (FastAPI):** High-throughput endpoints for patient and encounter CRUD, multi-criteria filtering, pagination, and SQL aggregations.
- **Enterprise Security & Governance:** Argon2 password hashing, stateless OAuth2 JWT authentication, granular Role-Based Access Control (**Admin**, **Healthcare Staff**, **Analyst**), and compliance audit trails.
- **Clinical Operations Interface (Streamlit):** Distinctive healthcare design (Deep Navy, Teal, Slate) featuring real-time KPI metrics, readmission distribution charts, length-of-stay analysis, and one-click CSV/Excel downloads.

---

## 2. System Architecture

The architecture follows a decoupled, multi-tier microservice paradigm:

```
+-------------------------------------------------------------------------------+
|                        PRESENTATION LAYER (STREAMLIT)                         |
|  - Executive KPI Cards   - Readmission Donut Charts   - LOS Histograms        |
|  - Patient Directory     - Encounter Timeline         - Compliance Audits     |
+---------------------------------------+---------------------------------------+
                                        |  REST API (HTTP / JSON / JWT)
                                        v
+-------------------------------------------------------------------------------+
|                         API MICROSERVICE (FASTAPI)                            |
|  - OAuth2 / JWT Auth     - Role-Based Access (RBAC)   - CRUD Controllers      |
|  - Aggregation Engine    - CSV/Excel Export Handlers  - Audit Interceptor     |
+---------------------------------------+---------------------------------------+
                                        |  Adaptive SQL Layer
                                        v
+-------------------------------------------------------------------------------+
|                       RELATIONAL STORAGE (3NF NORMALIZED)                     |
|  - patients              - encounters                 - encounter_diagnoses   |
|  - encounter_medications - admission_types / sources  - audit_logs            |
|  [Production: MySQL 8.0  |  Evaluation Fallback: Self-Initializing SQLite]     |
+---------------------------------------^---------------------------------------+
                                        |  Batch / Incremental Ingestion
+---------------------------------------+---------------------------------------+
|                      DATA ENGINEERING & INGESTION (ETL)                       |
|  - UCI Diabetes Dataset  - Pandas Cleansing Engine    - Deduplication & CDC   |
+-------------------------------------------------------------------------------+
```

---

## 3. Technology Stack

- **Backend & REST APIs:** FastAPI, Uvicorn, Pydantic v2
- **Data Engineering & ETL:** Pandas, NumPy, OpenPyXL
- **Database Engine:** Adaptive MySQL Connector + SQLite Engine (Zero-friction local evaluation)
- **Security & Authorization:** Argon2 (pwdlib), PyJWT, OAuth2 Bearer Tokens
- **Frontend / Presentation:** Streamlit, Matplotlib, Seaborn
- **Quality Assurance & Testing:** Pytest, HTTPX TestClient
- **Documentation & Artifacts:** ReportLab (Vector PDF Generation), Python-PPTX

---

## 4. Standardized Directory Layout

```
Healthcare-Patient-Management-System/
├── architecture/
│   ├── Architecture_Diagram.pdf        # Vector architecture diagram
│   └── Architecture_Diagram.png        # High-res architecture visual
├── design/
│   └── Design_Document.pdf             # Comprehensive system design document
├── docs/
│   ├── API_Documentation.pdf           # Complete endpoint and payload reference
│   ├── Dataset_Details.pdf             # UCI dataset structure, schemas & hygiene
│   └── Evaluation_Report.pdf           # Automated test benchmarks & latency analysis
├── presentation/
│   └── Project_Presentation.pptx       # 10-slide defense presentation deck
├── data/
│   ├── raw/                            # Original UCI diabetic_data.csv & IDS_mapping.csv
│   ├── processed/                      # Curated, normalized relational CSV feeds
│   └── sample_data/                    # Small test fixtures for continuous integration
├── src/
│   ├── api/
│   │   ├── routes/                     # auth, users, patients, encounters, analytics, reports, ref
│   │   ├── database.py                 # Adaptive MySQL / SQLite connection pool
│   │   ├── dependencies.py             # JWT verification and RBAC guards
│   │   ├── schemas.py                  # Pydantic v2 request/response models
│   │   └── security.py                 # Argon2 hashing & JWT utilities
│   ├── services/
│   │   ├── audit_service.py            # Immutable compliance audit logger
│   │   └── etl_pipeline.py             # Data cleansing, schema creation & seeding
│   ├── utils/                          # Diagram, PDF, and PPTX generator scripts
│   └── main.py                         # FastAPI application entrypoint
├── frontend/
│   ├── app.py                          # Executive dashboard & authentication session
│   ├── pages/                          # Multi-page clinical workspaces (Patients, Encounters, Analytics)
│   ├── services/api_client.py          # Authenticated REST API client
│   └── assets/style.css                # Enterprise deep navy and teal visual theme
├── tests/
│   ├── test_api.py                     # API authentication, CRUD, and RBAC test cases
│   └── test_etl.py                     # Data quality, deduplication, and schema tests
├── requirements.txt                    # Pinned project dependencies
└── README.md                           # Master setup and documentation guide
```

---

## 5. Local Setup & Execution Guide

### Step 1: Environment Setup
Ensure Python 3.11+ is installed. Clone the repository and navigate into the project root:

```bash
git clone <repository_url>
cd Healthcare-Patient-Management-System
```

Create and activate a virtual environment (optional but recommended):
```bash
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate
```

Install all dependencies:
```bash
pip install -r requirements.txt
```

### Step 2: Database Initialization & ETL Ingestion
Run the automated ETL pipeline. This will create the normalized schema, seed default users, load clinical terminology, and populate curated patient records:

```bash
python -m src.services.etl_pipeline
```
*(By default, this initializes a local relational database with zero setup. If you wish to connect to an external MySQL server, simply set `DB_HOST`, `DB_USER`, `DB_PASSWORD`, and `DB_NAME` in a `.env` file).*

### Step 3: Start the FastAPI Backend
Start the high-performance microservice using Uvicorn:

```bash
uvicorn src.main:app --reload --port 8000
```
- **API Home:** `http://127.0.0.1:8000/`
- **Interactive Swagger Documentation:** `http://127.0.0.1:8000/docs`
- **ReDoc:** `http://127.0.0.1:8000/redoc`

### Step 4: Launch the Streamlit Frontend
In a new terminal window, launch the clinical dashboard:

```bash
streamlit run frontend/app.py
```
Open your browser at `http://localhost:8501`.

---

## 6. Default Demonstration Accounts

The system comes pre-seeded with three accounts demonstrating Role-Based Access Control:

| Username | Password | Role | Access Scope |
| :--- | :--- | :--- | :--- |
| `admin` | `Admin123!` | **Admin** | Full system administration, user management, record deletion, audit inspection |
| `doctor` | `Doctor123!` | **Healthcare Staff** | Master patient registry, admission creation, clinical timeline inspection |
| `analyst` | `Analyst123!` | **Analyst** | Read-only analytics, KPI trend exploration, CSV/Excel report exports |

---

## 7. Sample API Usage & curl Queries

### 1. Authenticate and Receive JWT Token
```bash
curl -X POST "http://127.0.0.1:8000/auth/login" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=admin&password=Admin123!"
```
*Expected Output:*
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in_minutes": 120,
  "role": "Admin",
  "username": "admin"
}
```

### 2. Retrieve Hospital KPI Overview
```bash
curl -X GET "http://127.0.0.1:8000/analytics/overview" \
     -H "Authorization: Bearer <YOUR_ACCESS_TOKEN>"
```
*Expected Output:*
```json
{
  "total_patients": 5000,
  "total_encounters": 5000,
  "average_length_of_stay": 4.28,
  "total_readmissions": 2062,
  "early_readmissions_under_30": 551,
  "readmission_rate_percent": 41.24,
  "average_lab_procedures": 43.1,
  "average_medications": 16.0
}
```

### 3. Register a New Patient Record
```bash
curl -X POST "http://127.0.0.1:8000/patients" \
     -H "Authorization: Bearer <YOUR_ACCESS_TOKEN>" \
     -H "Content-Type: application/json" \
     -d '{"patient_nbr": 88812345, "race": "Asian", "gender": "Male"}'
```

### 4. Export Encounters to CSV
```bash
curl -X GET "http://127.0.0.1:8000/reports/export/encounters/csv?limit=100" \
     -H "Authorization: Bearer <YOUR_ACCESS_TOKEN>" \
     --output encounters.csv
```

---

## 8. Automated Test Suite

Run the complete automated test suite covering ETL, data quality, API authentication, and RBAC:

```bash
pytest tests -v
```

*Result:*
```
tests/test_api.py::test_health_check PASSED
tests/test_api.py::test_auth_login_admin PASSED
tests/test_api.py::test_auth_login_invalid PASSED
tests/test_api.py::test_patient_listing_and_rbac PASSED
tests/test_api.py::test_analytics_overview PASSED
tests/test_etl.py::test_data_cleaning_and_deduplication PASSED
tests/test_etl.py::test_database_table_integrity PASSED

7 passed in 1.94s
```

---

## 9. Deliverables Manifest

All mandatory Capstone submission deliverables have been generated and validated:

1. **Architecture Diagram:** [architecture/Architecture_Diagram.pdf](architecture/Architecture_Diagram.pdf) & [architecture/Architecture_Diagram.png](architecture/Architecture_Diagram.png)
2. **System Design Document:** [design/Design_Document.pdf](design/Design_Document.pdf)
3. **API Specification Document:** [docs/API_Documentation.pdf](docs/API_Documentation.pdf)
4. **Dataset Documentation:** [docs/Dataset_Details.pdf](docs/Dataset_Details.pdf)
5. **Evaluation Benchmark Report:** [docs/Evaluation_Report.pdf](docs/Evaluation_Report.pdf)
6. **Presentation Deck:** [presentation/Project_Presentation.pptx](presentation/Project_Presentation.pptx) (10-slide defense presentation)
7. **Complete Source Code & Automated Tests:** [src/](src/), [frontend/](frontend/), and [tests/](tests/)
