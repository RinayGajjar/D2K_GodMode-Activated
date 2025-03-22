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
import streamlit as st
from urllib.parse import urlparse

# Load environment variables
load_dotenv()

# Initialize Groq and SerpAPI
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
serpapi_key = os.getenv("SERPAPI_API_KEY")

# Check for missing API keys
if not os.getenv("GROQ_API_KEY") or not os.getenv("SERPAPI_API_KEY"):
    raise ValueError("Missing GROQ_API_KEY or SERPAPI_API_KEY in environment variables")

def init_streamlit():
    st.set_page_config(
        page_title="Marketing Automation Suite",
        page_icon="🚀",
        layout="wide"
    )
    st.title("🚀 Marketing Automation Suite")

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
    init_streamlit()
    
    try:
        marketing_system = MarketingAgencyAutomation()
    except ValueError as e:
        st.error(f"⚠️ {str(e)}")
        st.info("Please set up your API keys in the .env file:")
        st.code("""
        GROQ_API_KEY=your_groq_api_key_here
        SERPAPI_API_KEY=your_serpapi_api_key_here
        """)
        return

    # Available functions with their descriptions
    available_functions = {
        "Market Analysis": {
            "icon": "🎯",
            "description": "Analyze your website and competitors",
            "id": "market"
        },
        "SEO Optimization": {
            "icon": "🔍",
            "description": "Optimize your website's SEO",
            "id": "seo"
        },
        "Content Creation": {
            "icon": "📝",
            "description": "Generate social media and marketing content",
            "id": "content"
        },
        "Email Campaigns": {
            "icon": "📧",
            "description": "Create targeted email campaigns",
            "id": "email"
        },
        "Competitor Analysis": {
            "icon": "📊",
            "description": "Analyze competitor strategies",
            "id": "competitor"
        }
    }

    # Function selection
    st.sidebar.title("🚀 Marketing Suite")
    st.sidebar.write("Select the functions you want to use:")
    
    # Multi-select for functions
    selected_functions = st.sidebar.multiselect(
        "Choose functions:",
        options=list(available_functions.keys()),
        format_func=lambda x: f"{available_functions[x]['icon']} {x}",
        help="Select one or more functions to use"
    )

    if not selected_functions:
        st.info("👈 Please select at least one function from the sidebar to get started.")
        return

    # Main content area
    for function in selected_functions:
        st.markdown(f"## {available_functions[function]['icon']} {function}")
        st.write(available_functions[function]['description'])
        
        # Market Analysis Function
        if function == "Market Analysis":
            col1, col2 = st.columns(2)
            with col1:
                main_url = st.text_input(
                    "Your website URL:",
                    placeholder="https://example.com",
                    key="market_url"
                )
            with col2:
                keywords = st.text_input(
                    "Target keywords:",
                    placeholder="marketing automation, digital marketing",
                    key="market_keywords"
                )

            if st.button("Run Market Analysis", key="market_button"):
                if not main_url:
                    st.error("Please enter your website URL")
                    return
                if not keywords:
                    st.error("Please enter target keywords")
                    return
                    
                with st.spinner("Analyzing market position..."):
                    try:
                        # Extract domain from URL
                        domain = urlparse(main_url).netloc
                        
                        # Find top competitors using SerpAPI
                        st.info("🔍 Finding top competitors...")
                        search_query = f"{keywords} top companies -site:{domain}"
                        competitor_search = marketing_system._search_serp(
                            search_query,
                            num=5,  # Get top 5 to filter best 3
                            type="organic"
                        )
                        
                        # Extract and validate competitor URLs
                        competitors = []
                        if 'organic_results' in competitor_search:
                            for result in competitor_search['organic_results']:
                                if len(competitors) >= 3:  # Limit to 3 competitors
                                    break
                                comp_url = result.get('link', '')
                                comp_domain = urlparse(comp_url).netloc
                                if comp_domain and comp_domain != domain:
                                    competitors.append({
                                        'url': comp_url,
                                        'title': result.get('title', ''),
                                        'snippet': result.get('snippet', ''),
                                        'position': result.get('position', 0)
                                    })

                        if not competitors:
                            st.error("Could not find relevant competitors. Please try a different keyword.")
                            return

                        # Analyze main website
                        keywords_list = [k.strip() for k in keywords.split(',')]
                        main_site_analysis = marketing_system.seo_optimizer(main_url, keywords_list)
                        
                        # Analyze competitors
                        competitor_analyses = {}
                        for comp_url in competitors:
                            comp_analysis = marketing_system.seo_optimizer(comp_url['url'], keywords_list)
                            competitor_analyses[comp_url['url']] = comp_analysis
                        
                        # Display results in tabs
                        tab1, tab2, tab3 = st.tabs(["Your Website", "Competitors", "Comparison"])
                        
                        with tab1:
                            st.subheader("🌐 Your Website Analysis")
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write(f"**Title:** {main_site_analysis['current_title']}")
                                st.write(f"**Meta Description:** {main_site_analysis['current_meta']}")
                            with col2:
                                st.write(f"**H1 Tags:** {', '.join(main_site_analysis['current_h1'])}")
                            st.write("**SEO Recommendations:**")
                            st.write(main_site_analysis['recommendations'])

                        with tab2:
                            st.subheader("🔍 Competitor Analysis")
                            for url, analysis in competitor_analyses.items():
                                with st.expander(f"Competitor: {url}"):
                                    st.write(f"**Title:** {analysis['current_title']}")
                                    st.write(f"**Meta Description:** {analysis['current_meta']}")
                                    st.write(f"**H1 Tags:** {', '.join(analysis['current_h1'])}")
                                    st.write("**Analysis:**")
                                    st.write(analysis['recommendations'])

                        with tab3:
                            st.subheader("📊 Comparative Analysis")
                            
                            # Create comparison table
                            comparison_data = {
                                'Website': [main_url] + [comp['url'] for comp in competitors],
                                'Title Length': [len(main_site_analysis['current_title'])] + 
                                             [len(analysis['current_title']) for analysis in competitor_analyses.values()],
                                'Meta Description': ['Yes' if main_site_analysis['current_meta'] else 'No'] +
                                                 ['Yes' if analysis['current_meta'] else 'No' for analysis in competitor_analyses.values()],
                                'H1 Tags Count': [len(main_site_analysis['current_h1'])] +
                                              [len(analysis['current_h1']) for analysis in competitor_analyses.values()]
                            }
                            
                            df = pd.DataFrame(comparison_data)
                            st.dataframe(df)
                            
                            # Generate market insights
                            market_prompt = f"""
                            Compare these websites based on their SEO analysis:
                            
                            Main Website ({main_url}):
                            - Title: {main_site_analysis['current_title']}
                            - Meta: {main_site_analysis['current_meta']}
                            
                            Competitors:
                            {', '.join([f"{comp['url']}: {analysis['current_title']}" for comp, analysis in zip(competitors, competitor_analyses.values())])}
                            
                            Keywords: {keywords}
                            
                            Provide:
                            1. Market positioning analysis
                            2. Key competitive advantages/disadvantages
                            3. Improvement opportunities
                            4. Market trends
                            """
                            
                            market_insights = marketing_system._get_completion(market_prompt)
                            st.write("**Market Insights:**")
                            st.write(market_insights)
                            
                            # Add download button for report
                            report = f"""
                            Market Analysis Report
                            Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                            
                            Your Website: {main_url}
                            Keywords: {keywords}
                            
                            Main Website Analysis:
                            {main_site_analysis['recommendations']}
                            
                            Competitor Analyses:
                            {chr(10).join([f"{comp['url']}:{chr(10)}{analysis['recommendations']}" for comp, analysis in zip(competitors, competitor_analyses.values())])}
                            
                            Market Insights:
                            {market_insights}
                            """
                            
                            st.download_button(
                                label="📥 Download Full Report",
                                data=report,
                                file_name="market_analysis_report.txt",
                                mime="text/plain"
                            )
                            
                    except Exception as e:
                        st.error(f"Analysis failed: {str(e)}")

        # SEO Optimization Function
        elif function == "SEO Optimization":
            url = st.text_input(
                "Website URL:",
                placeholder="https://example.com",
                key="seo_url"
            )
            keywords = st.text_input(
                "Target keywords:",
                placeholder="keyword1, keyword2, keyword3",
                key="seo_keywords"
            )

            if st.button("Analyze SEO", key="seo_button"):
                if url and keywords:
                    with st.spinner("Analyzing SEO..."):
                        keywords_list = [k.strip() for k in keywords.split(',')]
                        results = marketing_system.seo_optimizer(url, keywords_list)
                        
                        st.subheader("SEO Analysis Results")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Title:** {results['current_title']}")
                            st.write(f"**Meta Description:** {results['current_meta']}")
                        with col2:
                            st.write(f"**H1 Tags:** {', '.join(results['current_h1'])}")
                        
                        st.write("**Recommendations:**")
                        st.write(results['recommendations'])

        # Content Creation Function
        elif function == "Content Creation":
            content_type = st.selectbox(
                "Content Type:",
                ["Social Media Post", "Blog Post", "Marketing Copy"],
                key="content_type"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                topic = st.text_input("Topic:", key="content_topic")
                if content_type == "Social Media Post":
                    platform = st.selectbox(
                        "Platform:",
                        ["LinkedIn", "Twitter", "Facebook", "Instagram"],
                        key="content_platform"
                    )
            with col2:
                tone = st.selectbox(
                    "Tone:",
                    ["Professional", "Casual", "Friendly", "Formal"],
                    key="content_tone"
                )

            if st.button("Generate Content", key="content_button"):
                if topic:
                    with st.spinner("Generating content..."):
                        post = marketing_system.post_creator(topic, platform, tone.lower())
                        st.subheader("Generated Content")
                        st.write(post['content'])

        # Email Campaigns Function
        elif function == "Email Campaigns":
            st.subheader("📧 Email Campaign Generator")
            
            # Campaign settings in a clean card-like interface
            with st.container():
                st.markdown("### Campaign Basics")
                col1, col2, col3 = st.columns(3)
                with col1:
                    brand_name = st.text_input(
                        "Brand Name:",
                        key="brand_name",
                        help="Your company or brand name"
                    )
                with col2:
                    industry = st.text_input(
                        "Industry:",
                        key="industry",
                        help="Your business industry"
                    )
                with col3:
                    campaign_type = st.selectbox(
                        "Campaign Type:",
                        ["Welcome Series", "Promotional", "Newsletter", "Re-engagement", "Product Launch"],
                        key="email_type",
                        help="Select the type of email campaign"
                    )

            # Campaign goals and tone
            with st.expander("Campaign Settings & Tone", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    primary_goal = st.selectbox(
                        "Primary Goal:",
                        ["Drive Sales", "Increase Engagement", "Share Information", "Get Feedback", "Build Relationships"],
                        key="goal"
                    )
                    tone = st.selectbox(
                        "Email Tone:",
                        ["Professional", "Friendly", "Casual", "Formal", "Enthusiastic"],
                        key="email_tone"
                    )
                with col2:
                    st.markdown("##### Campaign Tips:")
                    st.markdown("""
                    - Welcome Series: Focus on building trust
                    - Promotional: Clear value proposition
                    - Newsletter: Consistent formatting
                    - Re-engagement: Compelling subject lines
                    - Product Launch: Create excitement
                    """)

            st.markdown("### 📊 Audience Segments")
            num_segments = st.number_input(
                "Number of segments:",
                min_value=1,
                max_value=3,
                value=1,
                key="email_segments"
            )

            segments = []
            for i in range(int(num_segments)):
                with st.container():
                    st.markdown(f"#### Segment {i+1}")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        name = st.text_input(
                            "Segment name:",
                            key=f"email_seg_name_{i}",
                            placeholder="e.g., New Customers"
                        )
                    with col2:
                        characteristics = st.selectbox(
                            "Characteristics:",
                            ["First-time Buyers", "Repeat Customers", "VIP Members", "Inactive Users"],
                            key=f"email_seg_char_{i}"
                        )
                    with col3:
                        previous_engagement = st.select_slider(
                            "Engagement Level:",
                            options=["Very Low", "Low", "Medium", "High", "Very High"],
                            key=f"engagement_{i}"
                        )
                    
                    interests = st.text_input(
                        "Interests & Preferences (comma-separated):",
                        key=f"interests_{i}",
                        placeholder="e.g., technology, sustainability, premium products"
                    )
                    
                    if name:  # Only append if name is not empty
                        segments.append({
                            "segment_name": name.strip(),
                            "characteristics": characteristics,
                            "interests": interests,
                            "engagement": previous_engagement
                        })

            if st.button("Generate Campaign", key="email_button", use_container_width=True):
                if not brand_name.strip():
                    st.error("⚠️ Please enter your Brand Name")
                    return
                
                if not segments:
                    st.error("⚠️ Please enter at least one Segment Name")
                    return
                
                if any(not seg["segment_name"].strip() for seg in segments):
                    st.error("⚠️ Please fill in all Segment Names")
                    return
                
                with st.spinner("✨ Crafting your email campaign..."):
                    try:
                        generated_emails = []  # Store generated emails
                        
                        for segment in segments:
                            email_prompt = f"""
                            Create a professional {campaign_type.lower()} email campaign with these details:
                            Brand: {brand_name}
                            Industry: {industry}
                            Goal: {primary_goal}
                            Tone: {tone}
                            
                            Audience:
                            - Segment: {segment['segment_name']}
                            - Type: {segment['characteristics']}
                            - Interests: {segment['interests']}
                            - Engagement: {segment['engagement']}
                            
                            Generate:
                            1. Three attention-grabbing subject lines (under 50 characters)
                            2. Preview text (under 100 characters)
                            3. Personalized greeting
                            4. Main email body with:
                               - Clear value proposition
                               - Engaging content
                               - Specific benefits
                            5. Strong call-to-action
                            6. Professional signature
                            7. P.S. section (if relevant)
                            
                            Format as clean text with:
                            - Professional spacing
                            - Clear section breaks
                            - Easy readability
                            - No HTML
                            """
                            
                            email_content = marketing_system._get_completion(email_prompt)
                            generated_emails.append((segment['segment_name'], email_content))
                            
                            # Display results in an organized way
                            st.markdown(f"### 📧 Campaign for {segment['segment_name']}")
                            
                            # Create tabs for different versions
                            email_tab, preview_tab, settings_tab = st.tabs(["Email Content", "Preview", "Segment Details"])
                            
                            with email_tab:
                                st.text_area(
                                    "Generated Email:",
                                    value=email_content,
                                    height=400,
                                    key=f"email_content_{segment['segment_name']}",
                                    help="Your generated email content"
                                )
                                
                                col1, col2 = st.columns([1, 4])
                                with col1:
                                    if st.button("📋 Copy", key=f"copy_{segment['segment_name']}"):
                                        st.code(email_content)
                                        st.success("✅ Copied to clipboard!")
                            with preview_tab:
                                st.markdown("##### 📱 Mobile Preview")
                                st.markdown("""```
                                """ + email_content[:500] + "...\n```")
                            
                            with settings_tab:
                                st.markdown("#### Segment Details")
                                st.markdown(f"""
                                - **Audience Type:** {segment['characteristics']}
                                - **Interests:** {segment['interests']}
                                - **Engagement Level:** {segment['engagement']}
                                - **Recommended Send Time:** {marketing_system.optimize_send_time(segment)}
                                """)
                        
                        # Create combined email document with better formatting
                        all_emails = "\n\n" + "="*50 + "\n\n".join([
                            f"Campaign for: {name}\n" +
                            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n" +
                            f"{'='*30}\n\n" +
                            content +
                            f"\n\n{'='*30}\n"
                            for name, content in generated_emails
                        ])
                        
                        # Add download button with improved styling
                        st.markdown("### 📥 Download Campaign")
                        st.download_button(
                            label="Download Complete Campaign",
                            data=all_emails,
                            file_name=f"{campaign_type.lower()}_campaign_{datetime.now().strftime('%Y%m%d')}.txt",
                            mime="text/plain",
                            use_container_width=True
                        )
                        
                    except Exception as e:
                        st.error(f"⚠️ Campaign generation failed: {str(e)}")

        # Competitor Analysis Function
        elif function == "Competitor Analysis":
            num_competitors = st.number_input(
                "Number of competitors:",
                min_value=1,
                max_value=5,
                value=1,
                key="comp_num"
            )
            
            keywords = st.text_input(
                "Keywords to track:",
                placeholder="keyword1, keyword2, keyword3",
                key="comp_keywords"
            )

            competitors = []
            cols = st.columns(2)
            for i in range(int(num_competitors)):
                with cols[i % 2]:
                    comp_url = st.text_input(f"Competitor {i+1} URL:", key=f"comp_url_{i}")
                    competitors.append(comp_url)

            if st.button("Analyze Competitors", key="comp_button"):
                if all(competitors) and keywords:
                    with st.spinner("Analyzing competitors..."):
                        keywords_list = [k.strip() for k in keywords.split(',')]
                        results = marketing_system.competitor_watchdog(competitors, keywords_list)
                        
                        for competitor, insights in results.items():
                            st.subheader(f"Analysis for {competitor}")
                            st.write(insights['analysis'])

        st.markdown("---")  # Separator between functions

    # Tips in sidebar
    with st.sidebar.expander("💡 Tips"):
        st.write("""
        - Select multiple functions to use them together
        - Each function can be used independently
        - Results can be combined for comprehensive analysis
        - Use the same keywords across functions for consistency
        """)

if __name__ == "__main__":
    main()