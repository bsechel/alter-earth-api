"""
Test script for news ingestion service (Phase 2 - Posts structure).
"""

import asyncio
import asyncpg
from app.core.config import settings
from app.services.news_ingestion import run_news_ingestion


async def test_news_ingestion():
    """Test the news ingestion service with Phase 2 schema."""
    print("🌱 Testing Alter Earth news ingestion service (Phase 2)...")

    try:
        # Run news ingestion
        print("📰 Starting news ingestion...")
        total_posts = await run_news_ingestion()

        print(f"🎉 News ingestion completed! Total posts created: {total_posts}")

        # Query some results
        conn = await asyncpg.connect(
            settings.database_url,
            statement_cache_size=0
        )

        # Get post count by category
        categories = await conn.fetch("""
            SELECT aa.category, COUNT(*) as count
            FROM alter_earth.posts p
            JOIN alter_earth.automated_articles aa ON p.id = aa.post_id
            GROUP BY aa.category
            ORDER BY count DESC
        """)

        print("\n📊 Posts by category:")
        for row in categories:
            print(f"   {row['category']}: {row['count']} posts")

        # Get recent posts
        recent_posts = await conn.fetch("""
            SELECT
                p.title,
                p.score,
                p.hot_score,
                aa.source_name,
                aa.category,
                aa.relevance_score,
                aa.access_type,
                aa.published_at,
                u.nickname as author
            FROM alter_earth.posts p
            JOIN alter_earth.automated_articles aa ON p.id = aa.post_id
            JOIN alter_earth.users u ON p.user_id = u.id
            ORDER BY aa.published_at DESC
            LIMIT 5
        """)

        print("\n📋 Recent posts:")
        for post in recent_posts:
            print(f"   • {post['title'][:60]}...")
            print(f"     Author: {post['author']} | Source: {post['source_name']}")
            print(f"     Category: {post['category']} | Relevance: {post['relevance_score']:.2f}")
            print(f"     Score: {post['score']} | Hot Score: {post['hot_score']:.2f}")
            print(f"     Access: {post['access_type']}")
            print()

        # Get total posts count
        total_count = await conn.fetchval("""
            SELECT COUNT(*) FROM alter_earth.posts
            WHERE entity_type = 'automated_article'
        """)

        print(f"\n📈 Total automated article posts in database: {total_count}")

        await conn.close()

    except Exception as e:
        print(f"❌ Error in news ingestion test: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    asyncio.run(test_news_ingestion())