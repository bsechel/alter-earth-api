-- Migration: Create posts table (central content hub)
-- Phase 2: Reddit-like post system

-- Create entity_type enum
CREATE TYPE alter_earth.entity_type AS ENUM ('automated_article', 'user_submission');

-- Create posts table
CREATE TABLE alter_earth.posts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    entity_type alter_earth.entity_type NOT NULL,

    -- Link to user (NOT NULL - all posts must have a user, use bot for automated)
    user_id UUID NOT NULL REFERENCES alter_earth.users(id) ON DELETE SET NULL,

    -- Community support (nullable for now, Phase 3 feature)
    community_id UUID NULL,

    -- Denormalized vote counts for performance
    upvotes INTEGER NOT NULL DEFAULT 0,
    downvotes INTEGER NOT NULL DEFAULT 0,
    score INTEGER NOT NULL DEFAULT 0,  -- upvotes - downvotes
    hot_score DOUBLE PRECISION NOT NULL DEFAULT 0.0,

    -- Engagement metrics
    view_count INTEGER NOT NULL DEFAULT 0,
    comment_count INTEGER NOT NULL DEFAULT 0,

    -- Status
    is_active BOOLEAN NOT NULL DEFAULT true,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_posts_entity_type ON alter_earth.posts(entity_type);
CREATE INDEX idx_posts_user_id ON alter_earth.posts(user_id);
CREATE INDEX idx_posts_hot_score ON alter_earth.posts(hot_score DESC);
CREATE INDEX idx_posts_score ON alter_earth.posts(score DESC);
CREATE INDEX idx_posts_created_at ON alter_earth.posts(created_at DESC);
CREATE INDEX idx_posts_is_active ON alter_earth.posts(is_active);

-- Composite indexes for common queries
CREATE INDEX idx_posts_active_hot ON alter_earth.posts(is_active, hot_score DESC) WHERE is_active = true;
CREATE INDEX idx_posts_active_score ON alter_earth.posts(is_active, score DESC) WHERE is_active = true;
CREATE INDEX idx_posts_active_created ON alter_earth.posts(is_active, created_at DESC) WHERE is_active = true;

-- Add comments
COMMENT ON TABLE alter_earth.posts IS 'Central table for all content types (automated articles, user submissions)';
COMMENT ON COLUMN alter_earth.posts.entity_type IS 'Discriminator for content type (determines which detail table to join)';
COMMENT ON COLUMN alter_earth.posts.hot_score IS 'Reddit-style hot score for time-decayed ranking';
COMMENT ON COLUMN alter_earth.posts.score IS 'Simple score (upvotes - downvotes) for top ranking';
