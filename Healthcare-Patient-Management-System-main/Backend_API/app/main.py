import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.logging_config import configure_logging
from app.database import get_db_connection
from app.routes import patients, encounters, diagnoses, medications, reference_data, analytics, auth, users

configure_logging()
logger=logging.getLogger(__name__)
app=FastAPI(title="Healthcare Patient Management API",version="1.0.0",description="Healthcare records, analytics, authentication and role-based access control.")

@app.exception_handler(Exception)
async def unexpected_error_handler(request:Request,exc:Exception):
    logger.exception("Unhandled API error on %s %s",request.method,request.url.path)
    return JSONResponse(status_code=500,content={"detail":"Internal server error"})

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(patients.router)
app.include_router(encounters.router)
app.include_router(diagnoses.router)
app.include_router(medications.router)
app.include_router(reference_data.router)
app.include_router(analytics.router)

@app.get("/",tags=["System"])
def home():
    return {"message":"Healthcare Patient Management API is running","docs":"/docs"}

@app.get("/health/db",tags=["System"])
def check_database():
    connection=get_db_connection()
    try:
        cursor=connection.cursor(); cursor.execute("SELECT DATABASE()"); name=cursor.fetchone()[0]; cursor.close()
        return {"status":"connected","database":name}
    finally: connection.close()
