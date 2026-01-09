from sqlalchemy import text
from app.db import get_session

def add_columns():
    session = get_session()
    print("Manually adding columns if they don't exist...")
    try:
        # Check if column exists by trying to select it
        try:
            session.execute(text("SELECT sentiment_score FROM scores LIMIT 1"))
            print("Message: Columns already exist.")
        except Exception:
            print("Adding sentiment_score and reflection_text columns...")
            session.execute(text("ALTER TABLE scores ADD COLUMN sentiment_score FLOAT DEFAULT 0.0"))
            session.execute(text("ALTER TABLE scores ADD COLUMN reflection_text TEXT"))
            session.commit()
            print("✅ Columns added successfully.")
            
    except Exception as e:
        print(f"❌ Error adding columns: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    add_columns()
