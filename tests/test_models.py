from app.models import (
    ensure_scores_schema,
    ensure_responses_schema,
    ensure_question_bank_schema
)
from app.db import get_connection

def test_schema_creation(temp_db):
    conn = get_connection()
    cursor = conn.cursor()

    ensure_scores_schema(cursor)
    ensure_responses_schema(cursor)
    ensure_question_bank_schema(cursor)

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cursor.fetchall()}

    assert "responses" in tables
    assert "question_bank" in tables

    conn.close()
