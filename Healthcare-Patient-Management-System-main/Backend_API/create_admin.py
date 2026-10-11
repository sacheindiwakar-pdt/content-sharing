from getpass import getpass
from app.database import get_db_connection
from app.security import hash_password

username=input("Admin username: ").strip()
if len(username)<3:
    raise SystemExit("Username must contain at least 3 characters.")
password=getpass("Admin password (minimum 12 characters): ")
confirm=getpass("Confirm password: ")
if password != confirm:
    raise SystemExit("Passwords do not match.")
if len(password)<12:
    raise SystemExit("Password must contain at least 12 characters.")
connection=get_db_connection(); cursor=connection.cursor()
try:
    cursor.execute("INSERT INTO users (username,password_hash,role,is_active) VALUES (%s,%s,'Admin',TRUE)",(username,hash_password(password)))
    connection.commit()
    print("Admin user created successfully.")
except Exception:
    connection.rollback()
    raise
finally:
    cursor.close(); connection.close()
