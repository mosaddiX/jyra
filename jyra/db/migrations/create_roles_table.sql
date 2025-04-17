-- Create the roles table for Jyra bot
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
);
