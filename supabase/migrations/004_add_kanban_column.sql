-- Migration 004: Add kanban_column override field for drag-and-drop Kanban positioning
ALTER TABLE leads ADD COLUMN IF NOT EXISTS kanban_column TEXT DEFAULT NULL;
