# Healthcare Patient Management API

FastAPI + MySQL backend for a healthcare dataset capstone. Includes patient/encounter/diagnosis/medication CRUD, aggregate analytics, JWT login, password hashing, role-based authorization, and admin user management.

## 1. Setup

Run these commands from `Backend_API` in PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Create `.env` from `.env.example` and enter your existing MySQL credentials. Generate a JWT secret in PowerShell:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Copy the generated value into `JWT_SECRET_KEY`. Do not commit `.env`.

## 2. Create security tables and first admin

In MySQL:

```sql
SOURCE D:/Hospital Management System/Backend_API/sql/security_schema.sql;
```

If MySQL's `SOURCE` command rejects the path because of spaces, use the full path in quotes in the MySQL CLI or open the SQL file and execute its statements.

Then from PowerShell:

```powershell
python create_admin.py
```

The script prompts for an admin username and a password of at least 12 characters. Passwords are stored as Argon2 hashes.

## 3. Run

```powershell
python -m uvicorn app.main:app --reload
```

- Swagger: http://127.0.0.1:8000/docs
- Health: http://127.0.0.1:8000/health/db

Authenticate in Swagger using `POST /auth/login` with form fields `username` and `password`, then click **Authorize** and enter the returned bearer token. Swagger uses OAuth2 password form login.

## 4. Roles

- `Admin`: user administration and all modules.
- `Healthcare Staff`: patient and encounter-related CRUD.
- `Analyst`: aggregate analytics and reference data; no direct patient-identifiable records.

Role checks are enforced in FastAPI, not only in the UI.

## 5. Important API routes

- Auth: `POST /auth/login`, `GET /auth/me`
- Users (Admin): `GET /users`, `POST /users`, `PATCH /users/{user_id}`
- Patients: `GET/POST /patients`, `GET/PUT/PATCH /patients/{patient_nbr}`
- Encounters: `GET/POST /encounters`, `GET/PUT/PATCH /encounters/{encounter_id}`
- Diagnoses: `GET/POST /diagnoses`, `GET /diagnoses/{encounter_id}`, `PUT/PATCH/DELETE /diagnoses/{encounter_id}/{diagnosis_position}`
- Medications: `GET/POST /medications`, `GET /medications/{encounter_id}`, `PUT/PATCH/DELETE /medications/{encounter_id}/{medication}`
- Reference data: `GET /reference-data/admission-types`, `/discharge-dispositions`, `/admission-sources`
- Analytics: `GET /analytics/overview`, `/admissions`, `/readmissions`, `/length-of-stay`, `/diagnoses`, `/medications`

## 6. Data integrity and scope

The original patient table has only `patient_nbr`, `race`, and `gender`. This dataset is retrospective and is not a live electronic health record. New or edited rows are for capstone demonstration unless connected to a validated clinical source. The API intentionally does not expose DELETE for patients or encounters because they are parent records referenced by other tables. Diagnose/medication deletion is available for authorized staff and admins.

The `/analytics/readmissions` result is a dataset-label-based encounter-level measure, not a clinically validated patient-level readmission rate. Validate analytics against your existing baseline before final presentation.

## 7. Security notes

Use HTTPS outside localhost, protect `.env`, rotate secrets, back up the database, restrict database privileges, and add rate limiting/lockout and formal audit events before production. This capstone implementation is not certified for real patient data or production healthcare deployment.
