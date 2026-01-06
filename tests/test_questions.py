from app.questions import load_questions
from app.db import get_connection
from app.models import ensure_question_bank_schema

def test_load_questions_from_db(temp_db):
    conn = get_connection(temp_db)
    cursor = conn.cursor()

    ensure_question_bank_schema(cursor)

    cursor.execute(
        "INSERT INTO question_bank (question_text, is_active) VALUES (?, 1)",
        ("Test question?",)
    )
    conn.commit()
    conn.close()

    questions = load_questions(temp_db)

    assert len(questions) == 1
    assert questions[0][1] == "Test question?"

