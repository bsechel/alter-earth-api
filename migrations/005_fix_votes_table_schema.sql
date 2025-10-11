-- Migration: Fix votes table schema
-- Changes the primary key from composite (user_id, post_id, comment_id) to a UUID id field
-- Adds unique constraints to prevent duplicate votes

BEGIN;

SET search_path TO alter_earth;

-- Drop the old primary key constraint
ALTER TABLE votes DROP CONSTRAINT votes_pkey;

-- Add the new id column as primary key
ALTER TABLE votes ADD COLUMN id UUID DEFAULT gen_random_uuid() PRIMARY KEY;

-- Make comment_id nullable (it already is in the model, but database might not be)
ALTER TABLE votes ALTER COLUMN comment_id DROP NOT NULL;

-- Add unique constraints to ensure a user can only vote once per post/comment
-- First, remove any duplicate votes (keep the most recent)
WITH duplicates AS (
    SELECT id,
           ROW_NUMBER() OVER (PARTITION BY user_id, post_id ORDER BY created_at DESC) as rn
    FROM votes
    WHERE post_id IS NOT NULL
)
DELETE FROM votes WHERE id IN (SELECT id FROM duplicates WHERE rn > 1);

WITH duplicates AS (
    SELECT id,
           ROW_NUMBER() OVER (PARTITION BY user_id, comment_id ORDER BY created_at DESC) as rn
    FROM votes
    WHERE comment_id IS NOT NULL
)
DELETE FROM votes WHERE id IN (SELECT id FROM duplicates WHERE rn > 1);

-- Now add the unique constraints
ALTER TABLE votes ADD CONSTRAINT unique_user_post_vote UNIQUE (user_id, post_id);
ALTER TABLE votes ADD CONSTRAINT unique_user_comment_vote UNIQUE (user_id, comment_id);

-- Add indexes on post_id and comment_id for better query performance
CREATE INDEX IF NOT EXISTS idx_votes_post_id ON votes(post_id);
CREATE INDEX IF NOT EXISTS idx_votes_comment_id ON votes(comment_id);

COMMIT;
