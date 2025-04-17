-- Migration: Add is_featured and is_popular columns to roles table
ALTER TABLE roles ADD COLUMN is_featured INTEGER DEFAULT 0;
ALTER TABLE roles ADD COLUMN is_popular INTEGER DEFAULT 0;
