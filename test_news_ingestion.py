"""
Test script for news ingestion service.
"""

import asyncio
import asyncpg
from app.core.config import settings
from app.services.news_ingestion import run_news_ingestion


async def create_news_tables():
    """Create news tables manually to avoid SQLAlchemy prepared statement issues."""
    print("🔧 Creating news tables...")
    
    try:
        conn = await asyncpg.connect(
            settings.database_url,
            statement_cache_size=0
        )
        
        # Create news_sources table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS alter_earth.news_sources (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR(200) NOT NULL,
                description TEXT,
                url VARCHAR(500) NOT NULL,
                rss_url VARCHAR(500),
                api_endpoint VARCHAR(500),
                source_type VARCHAR(50) NOT NULL,
                category_focus VARCHAR(100),
                language VARCHAR(10) NOT NULL DEFAULT 'en',
                country VARCHAR(10),
                typical_access_type VARCHAR(20) NOT NULL DEFAULT 'free',
                paywall_frequency FLOAT,
                access_reliability FLOAT NOT NULL DEFAULT 1.0,
                fetch_frequency_hours INTEGER NOT NULL DEFAULT 6,
                max_articles_per_fetch INTEGER NOT NULL DEFAULT 20,
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                last_fetch_at TIMESTAMP WITH TIME ZONE,
                last_fetch_success BOOLEAN NOT NULL DEFAULT TRUE,
                last_error_message TEXT,
                total_articles_fetched INTEGER NOT NULL DEFAULT 0,
                average_relevance_score FLOAT,
                free_content_percentage FLOAT,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
            )
        """)
        
        # Create news_articles table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS alter_earth.news_articles (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                title VARCHAR(500) NOT NULL,
                description TEXT,
                content TEXT,
                url VARCHAR(1000) NOT NULL UNIQUE,
                source_name VARCHAR(200) NOT NULL,
                source_url VARCHAR(500),
                author VARCHAR(200),
                access_type VARCHAR(20) NOT NULL DEFAULT 'free',
                paywall_detected_at TIMESTAMP WITH TIME ZONE,
                is_full_content BOOLEAN NOT NULL DEFAULT TRUE,
                access_notes TEXT,
                category VARCHAR(100),
                tags TEXT,
                published_at TIMESTAMP WITH TIME ZONE NOT NULL,
                scraped_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                relevance_score FLOAT,
                quality_score FLOAT,
                accessibility_score FLOAT,
                ai_summary TEXT,
                is_featured BOOLEAN NOT NULL DEFAULT FALSE,
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                view_count INTEGER NOT NULL DEFAULT 0,
                share_count INTEGER NOT NULL DEFAULT 0,
                word_count INTEGER,
                reading_time_minutes INTEGER,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
            )
        """)
        
        # Create indexes
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_news_articles_title ON alter_earth.news_articles(title)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_news_articles_url ON alter_earth.news_articles(url)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_news_articles_source_name ON alter_earth.news_articles(source_name)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_news_articles_category ON alter_earth.news_articles(category)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_news_articles_published_at ON alter_earth.news_articles(published_at)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_news_articles_access_type ON alter_earth.news_articles(access_type)")
        
        print("✅ News tables created successfully!")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        raise


async def test_news_ingestion():
    """Test the news ingestion service."""
    print("🌱 Testing Alter Earth news ingestion service...")
    
    try:
        # Create tables first
        await create_news_tables()
        
        # Run news ingestion
        print("📰 Starting news ingestion...")
        total_articles = await run_news_ingestion()
        
        print(f"🎉 News ingestion completed! Total articles ingested: {total_articles}")
        
        # Query some results
        conn = await asyncpg.connect(
            settings.database_url,
            statement_cache_size=0
        )
        
        # Get article count by category
        categories = await conn.fetch("""
            SELECT category, COUNT(*) as count
            FROM alter_earth.news_articles 
            GROUP BY category 
            ORDER BY count DESC
        """)
        
        print("\n📊 Articles by category:")
        for row in categories:
            print(f"   {row['category']}: {row['count']} articles")
        
        # Get recent articles
        recent_articles = await conn.fetch("""
            SELECT title, source_name, category, relevance_score, access_type, published_at
            FROM alter_earth.news_articles 
            ORDER BY published_at DESC 
            LIMIT 5
        """)
        
        print("\n📋 Recent articles:")
        for article in recent_articles:
            print(f"   • {article['title'][:60]}...")
            print(f"     Source: {article['source_name']} | Category: {article['category']}")
            print(f"     Relevance: {article['relevance_score']:.2f} | Access: {article['access_type']}")
            print()
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ Error in news ingestion test: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(test_news_ingestion())