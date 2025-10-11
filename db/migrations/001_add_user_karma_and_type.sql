-- Migration: Add user_type, post_karma, and comment_karma to users table
-- Phase 2: Reddit-like post system with voting and karma

-- Create user_type enum
CREATE TYPE alter_earth.user_type AS ENUM ('human', 'ai_agent');

-- Add new columns to users table
ALTER TABLE alter_earth.users
ADD COLUMN IF NOT EXISTS user_type alter_earth.user_type NOT NULL DEFAULT 'human',
ADD COLUMN IF NOT EXISTS post_karma INTEGER NOT NULL DEFAULT 0,
ADD COLUMN IF NOT EXISTS comment_karma INTEGER NOT NULL DEFAULT 0;

-- Add index on user_type for filtering
CREATE INDEX IF NOT EXISTS idx_users_user_type ON alter_earth.users(user_type);

-- Add indexes on karma fields for sorting/leaderboards
CREATE INDEX IF NOT EXISTS idx_users_post_karma ON alter_earth.users(post_karma DESC);
CREATE INDEX IF NOT EXISTS idx_users_comment_karma ON alter_earth.users(comment_karma DESC);

COMMENT ON COLUMN alter_earth.users.user_type IS 'Distinguishes human users from AI agents/bots';
COMMENT ON COLUMN alter_earth.users.post_karma IS 'Cumulative karma from post upvotes (used for vote weighting)';
COMMENT ON COLUMN alter_earth.users.comment_karma IS 'Cumulative karma from comment upvotes (used for vote weighting)';
