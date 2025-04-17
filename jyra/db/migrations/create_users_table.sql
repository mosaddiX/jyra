-- Create the users table for Jyra bot
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    current_role_id INTEGER,
    settings TEXT,
    FOREIGN KEY(current_role_id) REFERENCES roles(role_id)
);
