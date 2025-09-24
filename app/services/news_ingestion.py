"""
News ingestion service for environmental and sustainability content.
Handles RSS feed parsing, content processing, and database storage.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional, Tuple
from urllib.parse import urlparse
import re

import feedparser
import aiohttp
from bs4 import BeautifulSoup
from dateutil import parser as date_parser
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.database import get_async_session
from app.models.news import NewsArticle, NewsSource
from app.core.news_config import (
    ENVIRONMENTAL_RSS_SOURCES, 
    QUALITY_INDICATORS,
    PRIMARY_SEARCH_TERMS,
    CATEGORY_MAPPING
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NewsIngestionService:
    """Service for ingesting environmental news from various sources."""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.db_session: Optional[AsyncSession] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'Alter-Earth-Bot/1.0 (+https://alterearth.example.com)'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def fetch_rss_feed(self, url: str) -> Optional[feedparser.FeedParserDict]:
        """Fetch and parse RSS feed from URL."""
        try:
            logger.info(f"Fetching RSS feed: {url}")
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    content = await response.text()
                    feed = feedparser.parse(content)
                    
                    if feed.bozo:
                        logger.warning(f"RSS feed has issues: {url} - {feed.bozo_exception}")
                    
                    logger.info(f"Successfully parsed {len(feed.entries)} entries from {url}")
                    return feed
                else:
                    logger.error(f"Failed to fetch RSS feed {url}: HTTP {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error fetching RSS feed {url}: {e}")
            return None
    
    def extract_article_content(self, entry: feedparser.FeedParserDict) -> Dict:
        """Extract and clean article content from RSS entry."""
        # Get title
        title = entry.get('title', '').strip()
        
        # Get description/summary
        description = entry.get('description') or entry.get('summary', '')
        if description:
            # Clean HTML from description
            soup = BeautifulSoup(description, 'html.parser')
            description = soup.get_text().strip()
        
        # Get content
        content = ''
        if hasattr(entry, 'content') and entry.content:
            content = entry.content[0].value if entry.content else ''
        elif description:
            content = description
        
        # Clean HTML from content
        if content:
            soup = BeautifulSoup(content, 'html.parser')
            content = soup.get_text().strip()
        
        # Get URL
        url = entry.get('link', '')
        
        # Get author
        author = entry.get('author', '')
        
        # Get publication date
        pub_date = None
        if 'published_parsed' in entry and entry.published_parsed:
            pub_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
        elif 'published' in entry:
            try:
                pub_date = date_parser.parse(entry.published)
                if pub_date.tzinfo is None:
                    pub_date = pub_date.replace(tzinfo=timezone.utc)
            except Exception as e:
                logger.warning(f"Could not parse date '{entry.published}': {e}")
        
        if not pub_date:
            pub_date = datetime.now(timezone.utc)
        
        # Calculate reading time (rough estimate: 200 words per minute)
        word_count = len(content.split()) if content else 0
        reading_time = max(1, word_count // 200) if word_count > 0 else 1
        
        return {
            'title': title,
            'description': description,
            'content': content,
            'url': url,
            'author': author,
            'published_at': pub_date,
            'word_count': word_count,
            'reading_time_minutes': reading_time
        }
    
    def detect_paywall(self, content: str, url: str) -> Tuple[str, Optional[datetime], bool, str]:
        """
        Detect if content is behind a paywall.
        Returns: (access_type, paywall_detected_at, is_full_content, access_notes)
        """
        content_lower = content.lower()
        url_lower = url.lower()
        
        # Check for paywall indicators
        paywall_indicators = QUALITY_INDICATORS['paywall_indicators']
        free_indicators = QUALITY_INDICATORS['free_indicators']
        
        paywall_found = any(indicator in content_lower for indicator in paywall_indicators)
        free_found = any(indicator in content_lower for indicator in free_indicators)
        
        # Check URL for paywall patterns
        paywall_domains = ['wsj.com', 'nytimes.com', 'ft.com', 'economist.com']
        is_paywall_domain = any(domain in url_lower for domain in paywall_domains)
        
        # Detect truncated content (common with paywalls)
        is_truncated = (
            content.endswith('...') or 
            'continue reading' in content_lower or
            'read more' in content_lower or
            len(content) < 100
        )
        
        if paywall_found or is_paywall_domain:
            return 'paywall', datetime.now(timezone.utc), not is_truncated, 'Paywall detected'
        elif free_found:
            return 'free', None, True, 'Free access confirmed'
        elif is_truncated:
            return 'registration', None, False, 'Content appears truncated'
        else:
            return 'free', None, True, 'Appears to be free access'
    
    def calculate_relevance_score(self, title: str, description: str, content: str) -> float:
        """Calculate relevance score for environmental content."""
        text = f"{title} {description} {content}".lower()
        
        # Count matches with our search terms
        primary_matches = sum(1 for term in PRIMARY_SEARCH_TERMS if term.lower() in text)
        
        # Additional environmental keywords - expanded for better coverage
        environmental_keywords = [
            'carbon', 'emission', 'pollution', 'conservation', 'ecosystem',
            'renewable', 'sustainable', 'green', 'climate', 'environment',
            'biodiversity', 'habitat', 'species', 'energy', 'solar', 'wind',
            'electric', 'ev', 'vehicle', 'plastic', 'waste', 'recycling',
            'nature', 'wildlife', 'forest', 'ocean', 'water', 'air',
            'ecology', 'organic', 'trees', 'earth', 'planet', 'eco',
            'natural', 'clean', 'environmental', 'sustainability'
        ]
        
        keyword_matches = sum(1 for keyword in environmental_keywords if keyword in text)
        
        # Calculate score (0.0 to 1.0)
        primary_score = min(1.0, primary_matches * 0.3)
        keyword_score = min(0.7, keyword_matches * 0.05)
        
        return min(1.0, primary_score + keyword_score)
    
    def categorize_article(self, title: str, description: str, content: str) -> Optional[str]:
        """Categorize article based on content."""
        text = f"{title} {description} {content}".lower()
        
        # Score each category
        category_scores = {}
        for category, keywords in CATEGORY_MAPPING.items():
            score = sum(1 for keyword in keywords if keyword.lower() in text)
            if score > 0:
                category_scores[category] = score
        
        # Return category with highest score
        if category_scores:
            return max(category_scores.items(), key=lambda x: x[1])[0]
        
        return 'environmental-news'  # Default category
    
    async def save_article(self, article_data: Dict, source: NewsSource, db_session: AsyncSession) -> Optional[NewsArticle]:
        """Save article to database."""
        try:
            # Check if article already exists
            existing = await db_session.execute(
                select(NewsArticle).where(NewsArticle.url == article_data['url'])
            )
            if existing.scalars().first():
                logger.debug(f"Article already exists: {article_data['url']}")
                return None
            
            # Detect paywall and calculate scores
            access_type, paywall_at, is_full, access_notes = self.detect_paywall(
                article_data['content'], article_data['url']
            )
            
            relevance_score = self.calculate_relevance_score(
                article_data['title'], 
                article_data['description'], 
                article_data['content']
            )
            
            category = self.categorize_article(
                article_data['title'],
                article_data['description'], 
                article_data['content']
            )
            
            # Create new article
            article = NewsArticle(
                title=article_data['title'][:500],  # Truncate to fit column
                description=article_data['description'],
                content=article_data['content'],
                url=article_data['url'],
                source_name=source.name,
                source_url=source.url,
                author=article_data['author'],
                category=category,
                published_at=article_data['published_at'],
                access_type=access_type,
                paywall_detected_at=paywall_at,
                is_full_content=is_full,
                access_notes=access_notes,
                relevance_score=relevance_score,
                word_count=article_data['word_count'],
                reading_time_minutes=article_data['reading_time_minutes']
            )
            
            db_session.add(article)
            await db_session.commit()
            await db_session.refresh(article)
            
            logger.info(f"Saved article: {article.title[:50]}... (relevance: {relevance_score:.2f})")
            return article
            
        except IntegrityError:
            await db_session.rollback()
            logger.debug(f"Duplicate article skipped: {article_data['url']}")
            return None
        except Exception as e:
            await db_session.rollback()
            logger.error(f"Error saving article {article_data['url']}: {e}")
            return None
    
    async def process_feed_source(self, source_config: Dict, db_session: AsyncSession) -> int:
        """Process a single RSS feed source."""
        logger.info(f"Processing RSS source: {source_config['name']}")
        
        # Get or create news source in database
        existing_source = await db_session.execute(
            select(NewsSource).where(NewsSource.rss_url == source_config['rss_url'])
        )
        source = existing_source.scalars().first()
        
        if not source:
            source = NewsSource(
                name=source_config['name'],
                description=source_config['description'],
                url=source_config.get('url', source_config['rss_url']),
                rss_url=source_config['rss_url'],
                source_type='rss',
                category_focus=source_config['category_focus'],
                typical_access_type=source_config['typical_access_type']
            )
            db_session.add(source)
            await db_session.commit()
            await db_session.refresh(source)
        
        # Fetch RSS feed
        feed = await self.fetch_rss_feed(source_config['rss_url'])
        if not feed:
            return 0
        
        articles_saved = 0
        
        # Process each entry
        for entry in feed.entries[:source.max_articles_per_fetch]:
            try:
                article_data = self.extract_article_content(entry)
                
                if not article_data['title'] or not article_data['url']:
                    continue
                
                # Only save articles with reasonable relevance
                relevance = self.calculate_relevance_score(
                    article_data['title'],
                    article_data['description'],
                    article_data['content']
                )
                
                if relevance >= 0.1:  # Minimum relevance threshold - more inclusive
                    saved_article = await self.save_article(article_data, source, db_session)
                    if saved_article:
                        articles_saved += 1
                
            except Exception as e:
                logger.error(f"Error processing entry: {e}")
                continue
        
        # Update source metadata
        source.last_fetch_at = datetime.now(timezone.utc)
        source.last_fetch_success = True
        source.total_articles_fetched += articles_saved
        await db_session.commit()
        
        logger.info(f"Processed {source_config['name']}: {articles_saved} articles saved")
        return articles_saved
    
    async def ingest_all_sources(self) -> int:
        """Ingest news from all configured RSS sources."""
        total_articles = 0
        
        async for db_session in get_async_session():
            for source_config in ENVIRONMENTAL_RSS_SOURCES:
                try:
                    articles_count = await self.process_feed_source(source_config, db_session)
                    total_articles += articles_count
                except Exception as e:
                    logger.error(f"Error processing source {source_config['name']}: {e}")
                    continue
            
            break  # Only need one session iteration
        
        logger.info(f"News ingestion complete. Total articles saved: {total_articles}")
        return total_articles


async def run_news_ingestion():
    """Standalone function to run news ingestion."""
    async with NewsIngestionService() as service:
        return await service.ingest_all_sources()