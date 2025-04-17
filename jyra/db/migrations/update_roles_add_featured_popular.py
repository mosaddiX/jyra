import sqlite3

DB_PATH = "../../jyra.db"

ALTERS = [
    "ALTER TABLE roles ADD COLUMN is_featured INTEGER DEFAULT 0;",
    "ALTER TABLE roles ADD COLUMN is_popular INTEGER DEFAULT 0;"
]

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    for stmt in ALTERS:
        try:
            cursor.execute(stmt)
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print(f"Column already exists: {e}")
            else:
                raise
    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
