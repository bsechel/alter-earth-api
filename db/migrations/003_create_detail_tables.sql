-- Migration: Create automated_articles and user_submissions detail tables
-- Phase 2: Reddit-like post system

-- ============================================
-- automated_articles table (for RSS/API news)
-- ============================================
CREATE TABLE alter_earth.automated_articles (
    -- Primary key is also foreign key to posts (one-to-one relationship)
    post_id UUID PRIMARY KEY REFERENCES alter_earth.posts(id) ON DELETE CASCADE,

    -- Article content (from RSS/API)
    description TEXT,
    content TEXT,  -- Will be truncated to snippet only (copyright compliance)
    url VARCHAR(1000) NOT NULL UNIQUE,  -- URL is unique identifier

    -- Source information
    source_name VARCHAR(200) NOT NULL,
    source_url VARCHAR(500),
    author VARCHAR(200),

    -- Categorization
    category VARCHAR(100),
    tags TEXT,  -- JSON array of tags

    -- Publication info
    published_at TIMESTAMPTZ NOT NULL,
    scraped_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- AI/Quality scoring (from existing news_articles)
    relevance_score DOUBLE PRECISION,
    quality_score DOUBLE PRECISION,
    accessibility_score DOUBLE PRECISION,
    ai_summary TEXT,

    -- Access information
    access_type VARCHAR(20) DEFAULT 'free' NOT NULL,  -- 'free', 'paywall', 'subscription', 'registration'
    paywall_detected_at TIMESTAMPTZ,
    is_full_content BOOLEAN DEFAULT false NOT NULL,
    access_notes TEXT,

    -- Content analysis
    word_count INTEGER,
    reading_time_minutes INTEGER,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_automated_articles_url ON alter_earth.automated_articles(url);
CREATE INDEX idx_automated_articles_source ON alter_earth.automated_articles(source_name);
CREATE INDEX idx_automated_articles_published ON alter_earth.automated_articles(published_at DESC);
CREATE INDEX idx_automated_articles_category ON alter_earth.automated_articles(category);
CREATE INDEX idx_automated_articles_access ON alter_earth.automated_articles(access_type);

-- Comments
COMMENT ON TABLE alter_earth.automated_articles IS 'Detail table for automated news articles from RSS/API sources';
COMMENT ON COLUMN alter_earth.automated_articles.content IS 'Truncated snippet only (max 500 chars) for copyright compliance';
COMMENT ON COLUMN alter_earth.automated_articles.url IS 'Original article URL - must be unique';


-- ============================================
-- user_submissions table (for user-created posts)
-- ============================================

-- Create submission_type enum
CREATE TYPE alter_earth.submission_type AS ENUM ('text', 'link');

CREATE TABLE alter_earth.user_submissions (
    -- Primary key is also foreign key to posts (one-to-one relationship)
    post_id UUID PRIMARY KEY REFERENCES alter_earth.posts(id) ON DELETE CASCADE,

    -- Submission type
    submission_type alter_earth.submission_type NOT NULL,

    -- Content (for text posts)
    content TEXT,

    -- URL (for link posts)
    url VARCHAR(1000),

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraint: Either content or URL must be present based on type
    CHECK (
        (submission_type = 'text' AND content IS NOT NULL) OR
        (submission_type = 'link' AND url IS NOT NULL)
    )
);

-- Create indexes
CREATE INDEX idx_user_submissions_type ON alter_earth.user_submissions(submission_type);
CREATE INDEX idx_user_submissions_url ON alter_earth.user_submissions(url) WHERE url IS NOT NULL;

-- Comments
COMMENT ON TABLE alter_earth.user_submissions IS 'Detail table for user-created posts (text or link)';
COMMENT ON COLUMN alter_earth.user_submissions.submission_type IS 'Type of submission: text (self-post) or link';
