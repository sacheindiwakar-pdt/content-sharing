"""
Audit Logging Service for Enterprise Compliance
Captures create, update, delete, and critical read activities.
"""

from src.api.database import get_db_connection


def record_audit(username: str, action: str, resource_type: str, resource_id: str = None, outcome: str = "SUCCESS", detail: str = None, user_id: int = None):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO audit_logs (user_id, username, action, resource_type, resource_id, outcome, detail)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (user_id, username, action, resource_type, str(resource_id) if resource_id is not None else None, outcome, detail)
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Failed to record audit log: {e}")
