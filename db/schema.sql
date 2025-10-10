-- Alter Earth Database Schema
-- Run this to set up a fresh database for development

-- Create schema
CREATE SCHEMA IF NOT EXISTS alter_earth;

-- Users table with Cognito authentication integration
CREATE TABLE IF NOT EXISTS alter_earth.users (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Cognito integration
    cognito_id VARCHAR(255) UNIQUE NOT NULL,
    
    -- Basic profile information
    email VARCHAR(255) UNIQUE NOT NULL,
    nickname VARCHAR(50) UNIQUE NOT NULL,
    bio TEXT,
    
    -- Optional real name (user choice to share)
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    show_real_name BOOLEAN DEFAULT FALSE NOT NULL,
    
    -- User role and permissions
    role VARCHAR(20) NOT NULL DEFAULT 'member', -- member, expert, moderator, admin
    is_expert BOOLEAN DEFAULT FALSE NOT NULL,
    
    -- Expert-specific fields
    expertise_areas TEXT, -- JSON string of expertise areas
    institution VARCHAR(200),
    website_url VARCHAR(500),
    
    -- Account status
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    is_verified BOOLEAN DEFAULT FALSE NOT NULL,
    
    -- Engagement metrics (for platform insights)
    post_count INTEGER DEFAULT 0 NOT NULL,
    comment_count INTEGER DEFAULT 0 NOT NULL,
    vote_count INTEGER DEFAULT 0 NOT NULL,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    last_active_at TIMESTAMPTZ
);

-- News articles table (for AI-powered content curation)
CREATE TABLE IF NOT EXISTS alter_earth.news_articles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    content TEXT,
    url VARCHAR(1000),
    source VARCHAR(200),
    published_at TIMESTAMPTZ,
    relevance_score FLOAT,
    category VARCHAR(100),
    tags TEXT[], -- Array of tags
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_cognito_id ON alter_earth.users(cognito_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON alter_earth.users(email);
CREATE INDEX IF NOT EXISTS idx_users_nickname ON alter_earth.users(nickname);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON alter_earth.users(created_at);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON alter_earth.users(is_active);

CREATE INDEX IF NOT EXISTS idx_news_published_at ON alter_earth.news_articles(published_at);
CREATE INDEX IF NOT EXISTS idx_news_category ON alter_earth.news_articles(category);
CREATE INDEX IF NOT EXISTS idx_news_relevance_score ON alter_earth.news_articles(relevance_score);

-- Update trigger for updated_at timestamps
CREATE OR REPLACE FUNCTION alter_earth.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE OR REPLACE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON alter_earth.users 
    FOR EACH ROW EXECUTE FUNCTION alter_earth.update_updated_at_column();

CREATE OR REPLACE TRIGGER update_news_articles_updated_at 
    BEFORE UPDATE ON alter_earth.news_articles 
    FOR EACH ROW EXECUTE FUNCTION alter_earth.update_updated_at_column();

-- Sample data (optional - remove for production)
-- INSERT INTO alter_earth.news_articles (title, content, url, source, category, tags) VALUES
-- ('Sample Environmental News', 'This is a sample article about sustainability...', 'https://example.com/article1', 'Sample Source', 'environment', ARRAY['sustainability', 'climate']);

-- Grant permissions (adjust as needed for your setup)
-- GRANT USAGE ON SCHEMA alter_earth TO your_app_user;
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA alter_earth TO your_app_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA alter_earth TO your_app_user;