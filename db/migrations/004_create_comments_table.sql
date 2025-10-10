-- Migration: Create comments table with threading support
-- Phase 2: Reddit-like comment system

CREATE TABLE alter_earth.comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Comment content
    content TEXT NOT NULL,

    -- Who created this comment
    user_id UUID NOT NULL REFERENCES alter_earth.users(id) ON DELETE SET NULL,

    -- Which post this comment belongs to
    post_id UUID NOT NULL REFERENCES alter_earth.posts(id) ON DELETE CASCADE,

    -- Parent comment for threading (NULL for top-level comments)
    parent_id UUID REFERENCES alter_earth.comments(id) ON DELETE CASCADE,

    -- Denormalized vote counts for performance
    upvotes INTEGER NOT NULL DEFAULT 0,
    downvotes INTEGER NOT NULL DEFAULT 0,
    score INTEGER NOT NULL DEFAULT 0,  -- upvotes - downvotes

    -- Soft delete flag (preserves thread structure)
    is_deleted BOOLEAN NOT NULL DEFAULT false,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_comments_post_id ON alter_earth.comments(post_id);
CREATE INDEX idx_comments_user_id ON alter_earth.comments(user_id);
CREATE INDEX idx_comments_parent_id ON alter_earth.comments(parent_id) WHERE parent_id IS NOT NULL;
CREATE INDEX idx_comments_score ON alter_earth.comments(score DESC);
CREATE INDEX idx_comments_created_at ON alter_earth.comments(created_at);

-- Composite index for fetching post comments sorted by score
CREATE INDEX idx_comments_post_score ON alter_earth.comments(post_id, score DESC) WHERE is_deleted = false;

-- Composite index for fetching post comments sorted by time
CREATE INDEX idx_comments_post_created ON alter_earth.comments(post_id, created_at DESC) WHERE is_deleted = false;

-- Comments
COMMENT ON TABLE alter_earth.comments IS 'User comments on posts with threading support';
COMMENT ON COLUMN alter_earth.comments.parent_id IS 'Parent comment ID for nested replies (NULL for top-level)';
COMMENT ON COLUMN alter_earth.comments.is_deleted IS 'Soft delete flag - preserves thread structure when comment deleted';
COMMENT ON COLUMN alter_earth.comments.score IS 'Simple score (upvotes - downvotes) for sorting';
