from app.db import get_connection

def test_db_connection(temp_db):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1")
    assert cursor.fetchone()[0] == 1
    conn.close()
