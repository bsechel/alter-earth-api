-- Migration: Add performance indexes for Phase 2
-- Created: 2025-10-10
-- Description: Add indexes to optimize common query patterns

-- Posts table indexes
CREATE INDEX IF NOT EXISTS idx_posts_hot_score ON alter_earth.posts(hot_score DESC);
CREATE INDEX IF NOT EXISTS idx_posts_score ON alter_earth.posts(score DESC);
CREATE INDEX IF NOT EXISTS idx_posts_created_at ON alter_earth.posts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_posts_entity_type ON alter_earth.posts(entity_type);
CREATE INDEX IF NOT EXISTS idx_posts_user_id ON alter_earth.posts(user_id);
CREATE INDEX IF NOT EXISTS idx_posts_community_id ON alter_earth.posts(community_id) WHERE community_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_posts_is_active ON alter_earth.posts(is_active);

-- Composite index for common query: active posts sorted by hot score
CREATE INDEX IF NOT EXISTS idx_posts_active_hot ON alter_earth.posts(is_active, hot_score DESC) WHERE is_active = true;

-- Composite index for top posts in time period
CREATE INDEX IF NOT EXISTS idx_posts_active_created_score ON alter_earth.posts(is_active, created_at DESC, score DESC) WHERE is_active = true;

-- Comments table indexes
CREATE INDEX IF NOT EXISTS idx_comments_post_id ON alter_earth.comments(post_id);
CREATE INDEX IF NOT EXISTS idx_comments_parent_id ON alter_earth.comments(parent_id) WHERE parent_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_comments_user_id ON alter_earth.comments(user_id);
CREATE INDEX IF NOT EXISTS idx_comments_created_at ON alter_earth.comments(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_comments_is_deleted ON alter_earth.comments(is_deleted);

-- Composite index for getting post's top-level comments
CREATE INDEX IF NOT EXISTS idx_comments_post_toplevel ON alter_earth.comments(post_id, created_at DESC) WHERE parent_id IS NULL AND is_deleted = false;

-- Votes table indexes (composite primary key already indexes user_id)
CREATE INDEX IF NOT EXISTS idx_votes_post_id ON alter_earth.votes(post_id) WHERE post_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_votes_comment_id ON alter_earth.votes(comment_id) WHERE comment_id IS NOT NULL;

-- Automated articles indexes
CREATE INDEX IF NOT EXISTS idx_automated_articles_category ON alter_earth.automated_articles(category);
CREATE INDEX IF NOT EXISTS idx_automated_articles_published_at ON alter_earth.automated_articles(published_at DESC);
CREATE INDEX IF NOT EXISTS idx_automated_articles_source_name ON alter_earth.automated_articles(source_name);
CREATE INDEX IF NOT EXISTS idx_automated_articles_relevance_score ON alter_earth.automated_articles(relevance_score DESC);

-- User submissions indexes
CREATE INDEX IF NOT EXISTS idx_user_submissions_submission_type ON alter_earth.user_submissions(submission_type);
