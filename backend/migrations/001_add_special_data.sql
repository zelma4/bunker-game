-- Migration: Add special_data column to players table
-- Date: 2025-12-02
-- Description: Add JSON column for storing special condition state data

-- Add special_data column if it doesn't exist
ALTER TABLE players 
ADD COLUMN IF NOT EXISTS special_data JSONB;

-- Create index for faster JSON queries
CREATE INDEX IF NOT EXISTS idx_players_special_data 
ON players USING GIN (special_data);

-- Update/commit
COMMIT;
