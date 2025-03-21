import os
from typing import List, Dict, Any
from datetime import datetime
import requests
import pandas as pd
from bs4 import BeautifulSoup
from groq import Groq
from serpapi import GoogleSearch
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Groq and SerpAPI
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
serpapi_key = os.getenv("SERPAPI_API_KEY")

# Check for missing API keys
if not os.getenv("GROQ_API_KEY") or not os.getenv("SERPAPI_API_KEY"):
    raise ValueError("Missing GROQ_API_KEY or SERPAPI_API_KEY in environment variables")

class MarketingAgencyAutomation:
    def __init__(self):
        self.groq = groq_client
        self.serpapi_key = serpapi_key
        
    def _get_completion(self, prompt: str) -> str:
        """Get completion from Groq API."""
        try:
            completion = self.groq.chat.completions.create(
                model="mistral-saba-24b",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=1000
            )
            return completion.choices[0].message.content
        except Exception as e:
            print(f"Error getting completion: {e}")
            return None

    def _search_serp(self, query: str, **params) -> Dict:
        """Helper method for SerpAPI searches"""
        search = GoogleSearch({
            "q": query,
            "api_key": self.serpapi_key,
            "location": "United States",  # Added for precision
            **params
        })
        return search.get_dict()

    def seo_optimizer(self, url: str, keywords: List[str]) -> Dict[str, Any]:
        """Analyzes website SEO and provides optimization recommendations"""
        try:
            # Fetch webpage content with user-agent
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract key SEO elements
            title = soup.title.string if soup.title else ""
            meta_desc = soup.find("meta", {"name": "description"})
            meta_desc = meta_desc["content"] if meta_desc else ""
            h1_tags = [h1.text.strip() for h1 in soup.find_all("h1")]  # Added H1 analysis
            
            # Analyze content with AI
            analysis_prompt = f"""
            Analyze this webpage SEO for the following elements:
            URL: {url}
            Title: {title}
            Meta Description: {meta_desc}
            H1 Tags: {', '.join(h1_tags)}
            Target Keywords: {', '.join(keywords)}
            
            Provide specific recommendations for:
            1. Title optimization
            2. Meta description improvements
            3. Content structure
            4. Keyword placement
            5. Technical SEO improvements
            """
            
            seo_analysis = self._get_completion(analysis_prompt)
            
            return {
                "url": url,
                "current_title": title,
                "current_meta": meta_desc,
                "current_h1": h1_tags,
                "recommendations": seo_analysis
            }
        except Exception as e:
            return {"error": str(e)}

    def competitor_watchdog(self, competitors: List[str], keywords: List[str]) -> Dict[str, Any]:
        """Monitors competitor activities and rankings"""
        competitor_data = {}
        
        for competitor in competitors:
            # Search competitor rankings with slight delay to avoid rate limits
            search_results = self._search_serp(competitor, num=10)  # Reduced num for testing
            time.sleep(1)  # Avoid hitting API limits
            
            # Analyze competitor content
            competitor_analysis = self._get_completion(f"""
            Analyze the market position and strategy for {competitor} based on:
            1. Search rankings
            2. Content strategy
            3. Keywords they're ranking for: {', '.join(keywords)}
            4. Recent changes or updates
            """)
            
            competitor_data[competitor] = {
                "rankings": search_results,
                "analysis": competitor_analysis
            }
        
        return competitor_data

    def product_recommendation_ai(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generates personalized product recommendations"""
        recommendation_prompt = f"""
        Based on the following customer data:
        {customer_data}
        
        Generate personalized product recommendations considering:
        1. Past purchase history
        2. Browsing behavior
        3. Demographics
        4. Market trends
        """
        
        recommendations = self._get_completion(recommendation_prompt)
        
        return {
            "customer_id": customer_data.get("customer_id"),
            "recommendations": recommendations
        }

    def post_creator(self, topic: str, platform: str, tone: str = "professional") -> Dict[str, Any]:
        """Creates engaging social media posts and content"""
        content_prompt = f"""
        Create a {platform} post about {topic} with a {tone} tone.
        Include:
        1. Main post content
        2. Relevant hashtags
        3. Call to action
        4. Best posting time recommendation
        """
        
        content = self._get_completion(content_prompt)
        
        return {
            "platform": platform,
            "content": content,
            "topic": topic,
            "created_at": datetime.now().isoformat()
        }

    def smart_email_manager(self, campaign_type: str, audience: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Manages email campaigns with AI-driven optimization"""
        email_templates = {}
        
        for segment in audience:
            email_prompt = f"""
            Create an email campaign for:
            Campaign Type: {campaign_type}
            Audience Segment: {segment}
            
            Include:
            1. Subject line options
            2. Email body
            3. Call to action
            4. Personalization elements
            """
            
            email_content = self._get_completion(email_prompt)
            
            email_templates[segment["segment_name"]] = {
                "content": email_content,
                "subject_lines": self.generate_subject_lines(campaign_type, segment),
                "send_time": self.optimize_send_time(segment)
            }
        
        return email_templates

    def generate_subject_lines(self, campaign_type: str, segment: Dict[str, Any]) -> List[str]:
        """Helper method to generate email subject lines"""
        prompt = f"Generate 5 engaging subject lines for {campaign_type} campaign targeting {segment['segment_name']}"
        return self._get_completion(prompt).split("\n")

    def optimize_send_time(self, segment: Dict[str, Any]) -> str:
        """Helper method to determine optimal send time"""
        if segment.get("characteristics") == "first_time_buyers":
            return "14:00 PM"  # Afternoon for newbies
        elif segment.get("characteristics") == "repeat_buyers":
            return "09:00 AM"  # Morning for loyal customers
        return "10:00 AM"  # Default

    def sentiment_analyzer(self, brand_name: str, timeframe: str = "past_month") -> Dict[str, Any]:
        """
        Analyzes brand sentiment and perception across social media and news.
        Returns sentiment scores, key mentions, and trend analysis.
        """
        # Search for brand mentions
        search_results = self._search_serp(
            f"{brand_name} reviews OR mentions OR feedback site:twitter.com OR site:linkedin.com",
            time=timeframe,
            num=20
        )
        
        # Analyze sentiment using AI
        sentiment_prompt = f"""
        Analyze the sentiment and brand perception for {brand_name} based on these mentions:
        {search_results.get('organic_results', [])}
        
        Provide:
        1. Overall sentiment score (positive/negative/neutral)
        2. Key positive mentions
        3. Key concerns or negative feedback
        4. Trend analysis
        5. Recommendations for improvement
        """
        
        sentiment_analysis = self._get_completion(sentiment_prompt)
        
        return {
            "brand": brand_name,
            "timeframe": timeframe,
            "analysis": sentiment_analysis,
            "raw_data": search_results
        }

    def content_performance_predictor(self, content: str, platform: str) -> Dict[str, Any]:
        """
        Predicts content performance using AI analysis.
        Suggests improvements for better engagement.
        """
        prediction_prompt = f"""
        Analyze this content for {platform} and predict its performance:
        {content}
        
        Consider:
        1. Engagement potential (likes, shares, comments)
        2. Viral potential
        3. SEO impact
        4. Target audience resonance
        5. Best posting time and frequency
        6. Potential improvements
        """
        
        prediction = self._get_completion(prediction_prompt)
        
        return {
            "platform": platform,
            "content_preview": content[:100] + "...",
            "prediction": prediction
        }

    def price_monitor(self, product_url: str, competitors: List[str]) -> Dict[str, Any]:
        """
        Monitors product prices across competitors.
        Provides price analysis and recommendations.
        """
        prices = {}
        
        # Get main product price
        try:
            response = requests.get(product_url, headers={"User-Agent": "Mozilla/5.0"})
            soup = BeautifulSoup(response.text, 'html.parser')
            # This is a simplified price extraction - would need customization per site
            price = soup.find("span", {"class": "price"})
            prices["main_product"] = price.text if price else "Price not found"
        except Exception as e:
            prices["main_product"] = f"Error: {str(e)}"
        
        # Get competitor prices
        for competitor in competitors:
            try:
                response = requests.get(competitor, headers={"User-Agent": "Mozilla/5.0"})
                soup = BeautifulSoup(response.text, 'html.parser')
                price = soup.find("span", {"class": "price"})
                prices[competitor] = price.text if price else "Price not found"
            except Exception as e:
                prices[competitor] = f"Error: {str(e)}"
        
        # Analyze pricing strategy
        analysis_prompt = f"""
        Analyze these prices and provide recommendations:
        Main product: {prices['main_product']}
        Competitor prices: {prices}
        
        Consider:
        1. Price positioning
        2. Competitive advantage
        3. Pricing strategy recommendations
        4. Market opportunity
        """
        
        price_analysis = self._get_completion(analysis_prompt)
        
        return {
            "product_url": product_url,
            "prices": prices,
            "analysis": price_analysis
        }

    def customer_journey_mapper(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Maps and analyzes customer journey touchpoints.
        Provides optimization recommendations.
        """
        journey_prompt = f"""
        Analyze this customer's journey based on their data:
        {customer_data}
        
        Map out:
        1. Key touchpoints
        2. Pain points
        3. Conversion opportunities
        4. Personalization recommendations
        5. Next best actions
        6. Retention strategies
        """
        
        journey_analysis = self._get_completion(journey_prompt)
        
        return {
            "customer_id": customer_data.get("customer_id"),
            "journey_map": journey_analysis
        }

def main():
    # Initialize the marketing automation system
    print("\n✨ Marketing Automation System Initialized ✨\n")
    
    marketing_system = MarketingAgencyAutomation()
    
    # Real-world competitor test data
    competitor_url = "https://www.hubspot.com"
    keywords = ["crm software", "marketing automation", "inbound marketing"]
    competitors = ["https://www.hubspot.com", "https://www.salesforce.com"]
    
    # Test SEO Optimizer
    print("\n🔍 SEO Analysis Results for HubSpot")
    print("=" * 50)
    seo_results = marketing_system.seo_optimizer(competitor_url, keywords)
    print(f"Website: {seo_results['url']}")
    print(f"Current Title: {seo_results['current_title']}")
    print(f"Current Meta Description: {seo_results['current_meta']}")
    print(f"Current H1 Tags: {', '.join(seo_results['current_h1'])}")
    print("\nRecommendations:")
    print(seo_results['recommendations'])
    
    # Test Competitor Watchdog
    print("\n📊 Competitor Analysis")
    print("=" * 50)
    competitor_insights = marketing_system.competitor_watchdog(competitors, keywords)
    for competitor, insights in competitor_insights.items():
        print(f"\n{competitor.upper()} Analysis:")
        print("-" * 30)
        print(insights.get('analysis', 'No analysis available'))
    
    # Test Product Recommendations
    print("\n🎯 Product Recommendations")
    print("=" * 50)
    customer_data = {
        "customer_id": "12345",
        "purchase_history": ["Product A", "Product B"],
        "demographics": {"age": 30, "location": "US"}
    }
    recommendations = marketing_system.product_recommendation_ai(customer_data)
    print(f"Customer ID: {recommendations['customer_id']}")
    print("\nPersonalized Recommendations:")
    print(recommendations['recommendations'])
    
    # Test Social Media Post Creator
    print("\n📱 Social Media Content")
    print("=" * 50)
    post = marketing_system.post_creator("Digital Marketing Trends 2024", "LinkedIn")
    print(f"Platform: {post['platform']}")
    print(f"Topic: {post['topic']}")
    print(f"Created: {post['created_at']}")
    print("\nContent:")
    print(post['content'])
    
    # Test Email Campaign Manager
    print("\n📧 Email Campaign Details")
    print("=" * 50)
    audience = [
        {"segment_name": "new_customers", "characteristics": "first_time_buyers"},
        {"segment_name": "loyal_customers", "characteristics": "repeat_buyers"}
    ]
    email_campaign = marketing_system.smart_email_manager("welcome_series", audience)
    for segment, details in email_campaign.items():
        print(f"\n📋 Segment: {segment}")
        print("-" * 30)
        print("Content Preview:")
        content_preview = details['content'].split('\n')[0] if details['content'] else "No content"
        print(f"{content_preview}...")
        print("\nSubject Line Options:")
        for i, subject in enumerate(details['subject_lines'][:3], 1):
            print(f"{i}. {subject}")
        print(f"Optimal Send Time: {details['send_time']}")
    
    # Test new features
    print("\n🎭 Brand Sentiment Analysis")
    print("=" * 50)
    sentiment_results = marketing_system.sentiment_analyzer("HubSpot")
    print("\nBrand Sentiment Analysis:")
    print(sentiment_results['analysis'])
    
    # Test content performance prediction
    print("\n📈 Content Performance Prediction")
    print("=" * 50)
    sample_content = "Excited to announce our new AI-powered marketing features! #MarTech #Innovation"
    prediction_results = marketing_system.content_performance_predictor(sample_content, "LinkedIn")
    print("\nContent Performance Prediction:")
    print(prediction_results['prediction'])
    
    # Test price monitoring
    print("\n💰 Price Monitoring")
    print("=" * 50)
    price_results = marketing_system.price_monitor(
        "https://www.hubspot.com/products/marketing",
        ["https://www.salesforce.com/products/marketing-cloud/overview/"]
    )
    print("\nPrice Analysis:")
    print(price_results['analysis'])
    
    # Test customer journey mapping
    print("\n🗺️ Customer Journey Analysis")
    print("=" * 50)
    customer_journey = marketing_system.customer_journey_mapper({
        "customer_id": "12345",
        "touchpoints": ["website_visit", "email_open", "product_demo", "purchase"],
        "engagement_score": 8.5,
        "lifetime_value": 1500
    })
    print("\nCustomer Journey Analysis:")
    print(customer_journey['journey_map'])

if __name__ == "__main__":
    main()