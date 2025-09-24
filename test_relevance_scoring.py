"""
Test relevance scoring to understand why we're only getting one article.
"""

from app.services.news_ingestion import NewsIngestionService

def test_relevance_scoring():
    service = NewsIngestionService()
    
    # Test some example titles
    test_cases = [
        ('Solar Energy Project Wins Environmental Award', 'Solar power development in California'),
        ('New Climate Change Study Released', 'Scientists report on global warming trends'),
        ('Tech Company Announces Carbon Neutral Goal', 'Microsoft pledges net zero emissions by 2030'),
        ('Local Wildlife Conservation Effort', 'Community works to protect endangered species'),
        ('Electric Vehicle Sales Surge', 'Tesla and other EVs see record growth'),
        ('Renewable Energy Costs Drop', 'Wind and solar now cheaper than coal'),
        ('Plastic Pollution in Oceans', 'New study shows microplastics in marine life'),
        ('Green Technology Startup Funding', 'Cleantech companies raise $2B in investments'),
        ('Biden Signs Climate Bill', 'New legislation targets carbon emissions'),
        ('Unrelated Business News', 'Stock market gains as tech sector rises')
    ]
    
    print("🔍 Testing relevance scoring:")
    print("=" * 60)
    
    for title, description in test_cases:
        score = service.calculate_relevance_score(title, description, '')
        status = "✅ PASS" if score >= 0.1 else "❌ FAIL"
        print(f"{status} {score:.2f} | {title}")
    
    print("\n" + "=" * 60)
    print(f"Threshold: 0.1 (articles with score >= 0.1 are saved)")

if __name__ == "__main__":
    test_relevance_scoring()