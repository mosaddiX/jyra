import sqlite3
import os

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../jyra.db'))

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create roles table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS roles (
        role_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        personality TEXT,
        speaking_style TEXT,
        knowledge_areas TEXT,
        behaviors TEXT,
        is_custom INTEGER DEFAULT 0,
        created_by INTEGER,
        is_featured INTEGER DEFAULT 0,
        is_popular INTEGER DEFAULT 0
    )
    ''')

    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        current_role_id INTEGER,
        settings TEXT,
        FOREIGN KEY(current_role_id) REFERENCES roles(role_id)
    )
    ''')

    # Create memories table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS memories (
        memory_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        content TEXT NOT NULL,
        category TEXT,
        importance INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(user_id)
    )
    ''')

    conn.commit()
    conn.close()
    print(f"Database initialized at {DB_PATH}")

if __name__ == "__main__":
    main()
