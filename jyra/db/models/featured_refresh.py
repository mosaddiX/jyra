import sqlite3
import os
import random
from datetime import datetime

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../jyra.db'))

# Helper table to track last refresh
def ensure_featured_refresh_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS featured_refresh (
        id INTEGER PRIMARY KEY,
        last_refresh_date TEXT
    )''')
    conn.commit()
    conn.close()

def get_last_featured_refresh():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT last_refresh_date FROM featured_refresh WHERE id = 1')
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def set_last_featured_refresh(date_str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO featured_refresh (id, last_refresh_date) VALUES (1, ?)', (date_str,))
    conn.commit()
    conn.close()

def refresh_featured_roles(n=3):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE roles SET is_featured = 0')
    cursor.execute('SELECT role_id FROM roles')
    all_roles = [row[0] for row in cursor.fetchall()]
    if not all_roles:
        conn.close()
        return []
    featured_roles = random.sample(all_roles, min(n, len(all_roles)))
    for role_id in featured_roles:
        cursor.execute('UPDATE roles SET is_featured = 1 WHERE role_id = ?', (role_id,))
    conn.commit()
    conn.close()
    return featured_roles

def refresh_featured_if_needed():
    ensure_featured_refresh_table()
    today = datetime.now().strftime('%Y-%m-%d')
    last_refresh = get_last_featured_refresh()
    if last_refresh != today:
        refresh_featured_roles()
        set_last_featured_refresh(today)
