-- Migration: Create votes table
-- Phase 2: Reddit-like voting system

CREATE TABLE alter_earth.votes (
    -- User who cast the vote
    user_id UUID NOT NULL REFERENCES alter_earth.users(id) ON DELETE CASCADE,

    -- Either post_id or comment_id must be set (not both)
    post_id UUID REFERENCES alter_earth.posts(id) ON DELETE CASCADE,
    comment_id UUID REFERENCES alter_earth.comments(id) ON DELETE CASCADE,

    -- Vote value: 1 for upvote, -1 for downvote
    vote_value SMALLINT NOT NULL CHECK (vote_value IN (1, -1)),

    -- Timestamps (track when votes change)
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraints: vote must be for either post OR comment, not both, not neither
    CHECK (
        (post_id IS NOT NULL AND comment_id IS NULL) OR
        (post_id IS NULL AND comment_id IS NOT NULL)
    ),

    -- Primary key: combination of user and target
    PRIMARY KEY (user_id, post_id, comment_id)
);

-- Create unique indexes to enforce one vote per user per item
-- Note: Postgres allows multiple NULL values in unique indexes, so we use partial indexes
CREATE UNIQUE INDEX idx_votes_user_post ON alter_earth.votes(user_id, post_id)
    WHERE post_id IS NOT NULL;

CREATE UNIQUE INDEX idx_votes_user_comment ON alter_earth.votes(user_id, comment_id)
    WHERE comment_id IS NOT NULL;

-- Create indexes for lookups
CREATE INDEX idx_votes_post_id ON alter_earth.votes(post_id) WHERE post_id IS NOT NULL;
CREATE INDEX idx_votes_comment_id ON alter_earth.votes(comment_id) WHERE comment_id IS NOT NULL;
CREATE INDEX idx_votes_user_id ON alter_earth.votes(user_id);

-- Comments
COMMENT ON TABLE alter_earth.votes IS 'User votes on posts and comments';
COMMENT ON COLUMN alter_earth.votes.vote_value IS '1 for upvote, -1 for downvote';
COMMENT ON COLUMN alter_earth.votes.post_id IS 'Post being voted on (NULL if voting on comment)';
COMMENT ON COLUMN alter_earth.votes.comment_id IS 'Comment being voted on (NULL if voting on post)';
