"""
Debug RSS feeds to understand why only Clean Technica is working.
"""

import asyncio
import aiohttp
import feedparser
from app.core.news_config import ENVIRONMENTAL_RSS_SOURCES

async def test_single_feed(session, source):
    """Test a single RSS feed and report results."""
    print(f"\n🔍 Testing: {source['name']}")
    print(f"   URL: {source['rss_url']}")
    
    try:
        async with session.get(source['rss_url'], timeout=aiohttp.ClientTimeout(total=10)) as response:
            print(f"   HTTP Status: {response.status}")
            
            if response.status == 200:
                content = await response.text()
                print(f"   Content Length: {len(content)} bytes")
                
                # Parse with feedparser
                feed = feedparser.parse(content)
                print(f"   Feed Title: {feed.feed.get('title', 'N/A')}")
                print(f"   Entries Found: {len(feed.entries)}")
                
                if feed.bozo:
                    print(f"   ⚠️  Feed Issues: {feed.bozo_exception}")
                
                # Show first few entries
                for i, entry in enumerate(feed.entries[:3]):
                    title = entry.get('title', 'No title')[:60]
                    print(f"   Entry {i+1}: {title}...")
                
                return len(feed.entries)
            else:
                print(f"   ❌ HTTP Error: {response.status}")
                return 0
                
    except asyncio.TimeoutError:
        print(f"   ⏰ Timeout after 10 seconds")
        return 0
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return 0

async def debug_all_feeds():
    """Test all RSS feeds and report results."""
    print("🔍 DEBUG: Testing all RSS feeds individually")
    print("=" * 60)
    
    async with aiohttp.ClientSession(
        headers={'User-Agent': 'Alter-Earth-Bot/1.0 (+https://alterearth.example.com)'}
    ) as session:
        
        total_working = 0
        total_entries = 0
        
        for source in ENVIRONMENTAL_RSS_SOURCES:
            entries = await test_single_feed(session, source)
            if entries > 0:
                total_working += 1
                total_entries += entries
        
        print(f"\n" + "=" * 60)
        print(f"📊 SUMMARY:")
        print(f"   Working feeds: {total_working}/{len(ENVIRONMENTAL_RSS_SOURCES)}")
        print(f"   Total entries available: {total_entries}")
        
        if total_working < len(ENVIRONMENTAL_RSS_SOURCES):
            print(f"\n⚠️  {len(ENVIRONMENTAL_RSS_SOURCES) - total_working} feeds are not working!")

if __name__ == "__main__":
    asyncio.run(debug_all_feeds())