"""
FastAPI Enterprise Application Entrypoint
"""

import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.database import init_database_schema, get_db_connection
from src.api.routes import auth, users, patients, encounters, analytics, reports, reference_data

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("HealthcareAPI")

app = FastAPI(
    title="Healthcare Patient Management System API",
    version="2.0.0",
    description="Enterprise REST APIs for Patient Administration, Clinical Encounters, Readmission Analytics, and Audit Logs."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    logger.info("Initializing relational database schema and security structures...")
    init_database_schema()
    logger.info("Healthcare Patient Management API initialized successfully.")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error occurred. Please contact system administrator."}
    )


# Register API Routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(patients.router)
app.include_router(encounters.router)
app.include_router(analytics.router)
app.include_router(reports.router)
app.include_router(reference_data.router)


@app.get("/", tags=["System"])
def root():
    return {
        "system": "Healthcare Patient Management System",
        "status": "online",
        "version": "2.0.0",
        "documentation": "/docs"
    }


@app.get("/health", tags=["System"])
def health_check():
    conn = get_db_connection()
    try:
        cur = conn.cursor(dictionary=False)
        cur.execute("SELECT 1")
        cur.close()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database_error": str(e)}
    finally:
        conn.close()
