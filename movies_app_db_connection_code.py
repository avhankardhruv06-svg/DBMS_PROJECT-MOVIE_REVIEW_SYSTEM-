# db.py
import os
import oracledb
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_DSN  = os.getenv("DB_DSN")  # Format: host:port/service_name

# Optional: Use thin mode (pure Python, no Instant Client needed)
oracledb.init_oracle_client(lib_dir=None)  # Comment out if you have Instant Client installed

def get_connection():
    """Create and return a new Oracle DB connection"""
    try:
        conn = oracledb.connect(
            user=DB_USER,
            password=DB_PASS,
            dsn=DB_DSN
        )
        return conn
    except oracledb.Error as e:
        print("❌ Database connection failed:", e)
        return None

def fetch_cursor(query, params=None):
    """Execute a SELECT query and return results"""
    conn = get_connection()
    if conn is None:
        return "Connection failed"
    try:
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        rows = cursor.fetchall()
        return rows
    except oracledb.Error as e:
        return str(e)
    finally:
        cursor.close()
        conn.close()

def call_procedure(proc_name, params=None):
    """Call a stored procedure with parameters"""
    conn = get_connection()
    if conn is None:
        return False, "Connection failed"
    try:
        cursor = conn.cursor()
        if params:
            cursor.callproc(proc_name, params)
        else:
            cursor.callproc(proc_name)
        conn.commit()
        return True, "Success"
    except oracledb.Error as e:
        return False, str(e)
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    # Quick test
    conn = get_connection()
    if conn:
        print("✅ Connected successfully to Oracle")
        conn.close()
    else:
        print("❌ Connection failed")