from fastapi import APIRouter, Depends
from app.database import get_db_connection
from app.dependencies import require_roles

router=APIRouter(prefix="/reference-data",tags=["Reference Data"])
access=require_roles("Admin","Healthcare Staff","Analyst")

@router.get("/admission-types")
def admission_types(_:dict=Depends(access)):
    return _read("admission_types","admission_type_id")
@router.get("/discharge-dispositions")
def discharge_dispositions(_:dict=Depends(access)):
    return _read("discharge_dispositions","discharge_disposition_id")
@router.get("/admission-sources")
def admission_sources(_:dict=Depends(access)):
    return _read("admission_sources","admission_source_id")

def _read(table, id_column):
    connection=get_db_connection(); cursor=connection.cursor(dictionary=True)
    try:
        cursor.execute(f"SELECT {id_column} AS id, description FROM {table} ORDER BY {id_column}")
        return cursor.fetchall()
    finally: cursor.close(); connection.close()
