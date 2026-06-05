from sqlalchemy import create_engine, text
engine = create_engine("sqlite:///./chartlens.db")
with engine.connect() as conn:
    tables = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).fetchall()
    print("Tables:", [t[0] for t in tables])
    try:
        rows = conn.execute(text("SELECT email, subscription_status, trial_cases_used FROM users")).fetchall()
        print("Users:", rows)
    except Exception as e:
        print("Error querying users:", e)
