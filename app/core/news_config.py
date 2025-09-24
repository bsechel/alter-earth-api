"""
News curation configuration and search strategy for environmental content.
"""

# Environmental News Search Term Strategy
# =====================================
# Comprehensive terms for environmental conservation, sustainability, and ecological topics

PRIMARY_SEARCH_TERMS = [
    "environmental conservation",
    "climate change",
    "renewable energy", 
    "biodiversity",
    "ecosystem restoration",
    "green technology",
    "carbon capture",
    "sustainable development"
]

SECONDARY_SEARCH_TERMS = [
    "wildlife protection",
    "habitat preservation", 
    "pollution prevention",
    "clean energy",
    "solar power",
    "wind energy",
    "electric vehicles",
    "sustainable agriculture",
    "ocean conservation",
    "forest conservation",
    "circular economy",
    "environmental policy",
    "climate solutions",
    "conservation biology",
    "green innovation",
    "sustainability",
    "environmental science",
    "ecology"
]

CATEGORY_MAPPING = {
    # Climate & Energy
    "climate-change": ["climate change", "global warming", "carbon emissions", "greenhouse gas"],
    "renewable-energy": ["solar power", "wind energy", "renewable energy", "clean energy", "green energy"],
    "energy-efficiency": ["energy efficiency", "smart grid", "energy storage", "electric vehicles"],
    
    # Conservation & Biodiversity  
    "wildlife-conservation": ["wildlife protection", "endangered species", "biodiversity", "conservation biology"],
    "ecosystem-restoration": ["ecosystem restoration", "habitat restoration", "rewilding", "forest restoration"],
    "ocean-conservation": ["ocean conservation", "marine conservation", "coral reef", "overfishing"],
    
    # Technology & Innovation
    "green-technology": ["green technology", "cleantech", "environmental technology", "green innovation"],
    "carbon-capture": ["carbon capture", "carbon sequestration", "direct air capture", "CCUS"],
    "sustainable-transport": ["electric vehicles", "sustainable transport", "green mobility", "EV"],
    
    # Agriculture & Food
    "sustainable-agriculture": ["sustainable agriculture", "regenerative farming", "organic farming", "food security"],
    "alternative-protein": ["lab-grown meat", "plant-based protein", "sustainable food", "food innovation"],
    
    # Policy & Economics
    "environmental-policy": ["environmental policy", "climate policy", "green legislation", "carbon pricing"],
    "green-finance": ["green finance", "sustainable investing", "ESG", "climate finance"],
    "circular-economy": ["circular economy", "waste reduction", "recycling", "zero waste"]
}

# RSS Feed Sources (Free, High-Quality Environmental News) - Updated 2025
ENVIRONMENTAL_RSS_SOURCES = [
    # Climate & Earth Science Focus
    {
        "name": "Climate Central",
        "rss_url": "http://feeds.feedburner.com/climatecentral/djOO",
        "category_focus": "climate-change",
        "typical_access_type": "free", 
        "description": "Climate science and solutions"
    },
    {
        "name": "Yale Environment 360",
        "rss_url": "https://e360.yale.edu/feed.xml",
        "category_focus": "environmental-policy",
        "typical_access_type": "free",
        "description": "Yale's environmental magazine"
    },
    {
        "name": "EcoWatch",
        "rss_url": "https://www.ecowatch.com/feed",
        "category_focus": "environmental-news",
        "typical_access_type": "free",
        "description": "Environmental news and sustainability"
    },
    # Sustainability & Green Living
    {
        "name": "Grist Environmental News", 
        "rss_url": "https://grist.org/feed/",
        "category_focus": "environmental-policy",
        "typical_access_type": "free",
        "description": "Environmental news and climate solutions"
    },
    {
        "name": "Mongabay",
        "rss_url": "https://news.mongabay.com/feed/",
        "category_focus": "wildlife-conservation",
        "typical_access_type": "free",
        "description": "Environmental science and conservation news"
    },
    # Conservation & Biodiversity
    {
        "name": "Inside Climate News",
        "rss_url": "https://insideclimatenews.org/feed/",
        "category_focus": "climate-change",
        "typical_access_type": "free",
        "description": "Pulitzer Prize-winning climate journalism"
    },
    {
        "name": "World Wildlife Fund",
        "rss_url": "http://feeds.feedburner.com/WWFStories",
        "category_focus": "wildlife-conservation", 
        "typical_access_type": "free",
        "description": "Wildlife and habitat conservation"
    },
    # Earth & Environmental Science
    {
        "name": "ScienceDaily Environment",
        "rss_url": "https://www.sciencedaily.com/rss/earth_climate/environmental_issues.xml",
        "category_focus": "earth-science",
        "typical_access_type": "free",
        "description": "Environmental science research and studies"
    },
    # Clean Technology & Renewable Energy
    {
        "name": "Clean Technica",
        "rss_url": "https://cleantechnica.com/feed/",
        "category_focus": "renewable-energy",
        "typical_access_type": "free",
        "description": "Clean technology and renewable energy news"
    }
]

# Content Quality Indicators
QUALITY_INDICATORS = {
    "high_quality_sources": [
        "yale.edu", "stanford.edu", "mit.edu", "nature.com", "science.org",
        "epa.gov", "noaa.gov", "nasa.gov", "ipcc.ch", "unep.org"
    ],
    "reliable_news_sources": [
        "reuters.com", "apnews.com", "bbc.co.uk", "theguardian.com",
        "climatecentral.org", "e360.yale.edu", "greenbiz.com"
    ],
    "paywall_indicators": [
        "premium", "subscribe", "paywall", "members only", "subscription required"
    ],
    "free_indicators": [
        "open access", "free", "public", "creative commons"
    ]
}

# AI Content Enhancement Prompts (for future Claude API integration)
AI_ENHANCEMENT_PROMPTS = {
    "relevance_scoring": "Rate the relevance of this article to environmental conservation and sustainability on a scale of 0.0 to 1.0.",
    "summary_generation": "Create a concise 2-3 sentence summary of this environmental news article, focusing on key impacts and solutions.",
    "category_classification": "Classify this environmental article into one of these categories: {categories}",
    "accessibility_scoring": "Rate how accessible this content is to the general public (avoiding excessive scientific jargon) on a scale of 0.0 to 1.0."
}