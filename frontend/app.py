import streamlit as st
import requests
import os
from pathlib import Path
import base64
from io import BytesIO
from PIL import Image
import datetime

# Update this to the correct backend URL
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:9000")

st.set_page_config(page_title="Agent Marketplace", layout="wide")
st.title("Agent Marketplace")


# Fetch available agents from backend
@st.cache_data(ttl=300)
def get_available_agents():
    try:
        response = requests.get(f"{BACKEND_URL}/api/agents")
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to fetch agents: {response.status_code}")
            return []
    except Exception as e:
        st.error(f"Connection error: {str(e)}")
        return []


# Get agents
agents = get_available_agents()

# Create tabs for agents
if agents:
    tab_names = ["📋 All Agents"] + [
        f"{'📄' if agent['id'] == 'summarizer' else '📈' if agent['id'] == 'finance' else '🤖'} {agent['name']}"
        for agent in agents
    ]
    tabs = st.tabs(tab_names)

    # First tab shows all available agents
    with tabs[0]:
        st.header("Available Agents")
        st.write("Click on an agent's tab to use it.")

        for i, agent in enumerate(agents):
            st.markdown(f"### {i+1}. {agent['name']}")
            st.markdown(f"_{agent['description']}_")
            st.markdown(
                f"Supported file types: `{', '.join(agent['supported_types'])}`"
            )
            st.markdown("---")

    # Create a tab for each agent
    for i, agent in enumerate(agents, 1):
        with tabs[i]:
            st.header(agent["name"])
            st.write(agent["description"])

            if agent["id"] == "finance":
                # Add ticker input option
                st.markdown("### Enter stock tickers to analyze")
                st.markdown(
                    "Enter up to 5 ticker symbols, separated by commas (e.g., AAPL, MSFT, GOOG)"
                )

                # Text input for tickers
                ticker_input = st.text_input("Ticker symbols", key="ticker_input")

                if ticker_input:
                    # Parse tickers
                    tickers = [t.strip() for t in ticker_input.split(",")]

                    # Process button
                    if st.button(
                        "▶️ Analyze Stocks",
                        key=f"analyze_btn_{agent['id']}",
                        use_container_width=True,
                    ):
                        with st.spinner("Analyzing stocks..."):
                            try:
                                response = requests.post(
                                    f"{BACKEND_URL}/api/analyze_tickers",
                                    json={"tickers": tickers},
                                )

                                if response.status_code == 200:
                                    st.success("✅ Analysis complete!")
                                    result = response.json()

                                    # Display finance results
                                    st.markdown("## Stock Analysis Results")

                                    # Display charts and analysis for each stock
                                    for stock_result in result["results"]:
                                        st.markdown("---")

                                        # Check if there was an error for this stock
                                        if "status" in stock_result:
                                            st.warning(
                                                f"**{stock_result['ticker']}**: {stock_result['status']}"
                                            )
                                            continue

                                        # Display stock analysis
                                        st.markdown(
                                            f"### {stock_result['company_name']} ({stock_result['ticker']})"
                                        )

                                        # Create columns for chart and metrics
                                        col1, col2 = st.columns([3, 2])

                                        # Find matching chart
                                        chart_data = next(
                                            (
                                                c["chart"]
                                                for c in result["charts"]
                                                if c["ticker"] == stock_result["ticker"]
                                            ),
                                            None,
                                        )

                                        if chart_data:
                                            # Display chart
                                            with col1:
                                                img = Image.open(
                                                    BytesIO(
                                                        base64.b64decode(chart_data)
                                                    )
                                                )
                                                st.image(
                                                    img,
                                                    caption=f"{stock_result['ticker']} - 1 Year Price Chart",
                                                )

                                        # Display metrics and recommendation
                                        with col2:
                                            metrics = stock_result["metrics"]
                                            st.metric(
                                                "Current Price",
                                                f"${metrics['current_price']:.2f}",
                                            )
                                            st.metric(
                                                "Annual Return",
                                                f"{metrics['annual_return']:.2f}%",
                                            )
                                            st.metric(
                                                "Annual Volatility",
                                                f"{metrics['annual_volatility']:.2f}%",
                                            )
                                            st.metric(
                                                "Sharpe Ratio",
                                                f"{metrics['sharpe_ratio']:.2f}",
                                            )

                                        # Display full analysis with markdown
                                        st.markdown(stock_result["analysis"])

                                        # Download button for individual stock analysis
                                        st.download_button(
                                            f"⬇️ Download {stock_result['ticker']} Analysis",
                                            stock_result["analysis"],
                                            f"{stock_result['ticker']}_analysis.md",
                                            mime="text/markdown",
                                        )

                                    # Create a combined analysis for all stocks
                                    combined_analysis = "# Stock Analysis Report\n\n"
                                    combined_analysis += f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d')}\n\n"

                                    for stock_result in result["results"]:
                                        if "analysis" in stock_result:
                                            combined_analysis += (
                                                f"## {stock_result['ticker']}\n\n"
                                            )
                                            combined_analysis += (
                                                stock_result["analysis"] + "\n\n"
                                            )

                                    # Download button for combined analysis
                                    st.download_button(
                                        "⬇️ Download Complete Analysis",
                                        combined_analysis,
                                        f"stock_analysis_report.md",
                                        mime="text/markdown",
                                    )
                                else:
                                    st.error(f"❌ Error: {response.status_code}")
                                    try:
                                        st.error(
                                            f"Details: {response.json().get('error', 'Unknown error')}"
                                        )
                                    except:
                                        st.error(f"Raw response: {response.text}")

                            except Exception as e:
                                st.error(f"❌ Connection error: {str(e)}")
                                st.info(
                                    f"Make sure backend is running at {BACKEND_URL}"
                                )

                # Add popular stock suggestions
                st.markdown(
                    """
                ### Popular stocks to analyze:
                - Tech: AAPL, MSFT, GOOG, META, NVDA
                - Retail: AMZN, WMT, TGT, COST
                - Financial: JPM, BAC, GS, V, MA
                - Healthcare: JNJ, PFE, MRK, UNH
                - Energy: XOM, CVX, BP, COP
                """
                )

                # Divider
                st.markdown("---")

                # Option to still upload file
                st.markdown("### Or upload a file with tickers")

            if agent["id"] == "marketing":
                # Marketing Agent UI
                st.markdown("### Marketing Tools")
                
                # Create tabs for different marketing features
                marketing_tabs = st.tabs([
                    "🔍 SEO Analysis",
                    "👥 Competitor Analysis",
                    "📝 Content Creation",
                    "📧 Email Campaigns",
                    "📊 Sentiment Analysis",
                    "📈 Performance Prediction",
                    "💰 Price Monitoring",
                    "🗺️ Customer Journey"
                ])
                
                # SEO Analysis Tab
                with marketing_tabs[0]:
                    st.markdown("#### Website SEO Analysis")
                    url = st.text_input("Enter website URL", key="seo_url_input")
                    keywords = st.text_input("Enter keywords (comma-separated)", key="seo_keywords_input")
                    
                    if st.button("Analyze SEO", key="seo_btn"):
                        if url:
                            with st.spinner("Analyzing SEO..."):
                                try:
                                    response = requests.post(
                                        f"{BACKEND_URL}/api/analyze_seo",
                                        json={"url": url, "keywords": [k.strip() for k in keywords.split(",")] if keywords else []}
                                    )
                                    if response.status_code == 200:
                                        result = response.json()
                                        st.success("SEO Analysis Complete!")
                                        st.markdown("### Current SEO Status")
                                        st.markdown(f"**Title:** {result['current_title']}")
                                        st.markdown(f"**Meta Description:** {result['current_meta']}")
                                        st.markdown("### Recommendations")
                                        st.markdown(result['recommendations'])
                                    else:
                                        st.error(f"Error: {response.json().get('error', 'Unknown error')}")
                                except Exception as e:
                                    st.error(f"Connection error: {str(e)}")
                
                # Competitor Analysis Tab
                with marketing_tabs[1]:
                    st.markdown("#### Competitor Analysis")
                    competitors = st.text_input("Enter competitor URLs (comma-separated)", key="competitor_urls_input")
                    keywords = st.text_input("Enter keywords to track (comma-separated)", key="competitor_keywords_input")
                    
                    if st.button("Analyze Competitors", key="competitor_btn"):
                        if competitors:
                            with st.spinner("Analyzing competitors..."):
                                try:
                                    response = requests.post(
                                        f"{BACKEND_URL}/api/analyze_competitors",
                                        json={
                                            "competitors": [c.strip() for c in competitors.split(",")],
                                            "keywords": [k.strip() for k in keywords.split(",")] if keywords else []
                                        }
                                    )
                                    if response.status_code == 200:
                                        result = response.json()
                                        st.success("Competitor Analysis Complete!")
                                        for competitor, data in result.items():
                                            st.markdown(f"### {competitor}")
                                            st.markdown(data['analysis'])
                                    else:
                                        st.error(f"Error: {response.json().get('error', 'Unknown error')}")
                                except Exception as e:
                                    st.error(f"Connection error: {str(e)}")
                
                # Content Creation Tab
                with marketing_tabs[2]:
                    st.markdown("#### Content Creation")
                    topic = st.text_input("Enter content topic", key="content_topic_input")
                    platform = st.selectbox("Select platform", ["Twitter", "LinkedIn", "Facebook", "Instagram"], key="content_platform_select")
                    tone = st.selectbox("Select tone", ["professional", "casual", "friendly", "formal"], key="content_tone_select")
                    
                    if st.button("Create Content", key="content_btn"):
                        if topic and platform:
                            with st.spinner("Creating content..."):
                                try:
                                    response = requests.post(
                                        f"{BACKEND_URL}/api/create_content",
                                        json={"topic": topic, "platform": platform, "tone": tone}
                                    )
                                    if response.status_code == 200:
                                        result = response.json()
                                        st.success("Content Created!")
                                        st.markdown("### Generated Content")
                                        st.markdown(result['content'])
                                    else:
                                        st.error(f"Error: {response.json().get('error', 'Unknown error')}")
                                except Exception as e:
                                    st.error(f"Connection error: {str(e)}")
                
                # Email Campaigns Tab
                with marketing_tabs[3]:
                    st.markdown("#### Email Campaign Creation")
                    campaign_type = st.selectbox("Select campaign type", ["newsletter", "promotional", "welcome", "abandoned_cart"], key="email_campaign_type_select")
                    audience = st.text_area("Enter audience segments (JSON format)", 
                                          value='[{"segment_name": "new_customers", "characteristics": "first_time_buyers"}]',
                                          key="email_audience_input")
                    
                    if st.button("Create Campaign", key="email_btn"):
                        if campaign_type and audience:
                            with st.spinner("Creating email campaign..."):
                                try:
                                    response = requests.post(
                                        f"{BACKEND_URL}/api/create_email_campaign",
                                        json={"campaign_type": campaign_type, "audience": eval(audience)}
                                    )
                                    if response.status_code == 200:
                                        result = response.json()
                                        st.success("Email Campaign Created!")
                                        for segment, data in result.items():
                                            st.markdown(f"### {segment}")
                                            st.markdown(data['content'])
                                            st.markdown(f"**Subject Lines:**")
                                            for line in data['subject_lines']:
                                                st.markdown(f"- {line}")
                                            st.markdown(f"**Best Send Time:** {data['send_time']}")
                                    else:
                                        st.error(f"Error: {response.json().get('error', 'Unknown error')}")
                                except Exception as e:
                                    st.error(f"Connection error: {str(e)}")
                
                # Sentiment Analysis Tab
                with marketing_tabs[4]:
                    st.markdown("#### Brand Sentiment Analysis")
                    brand_name = st.text_input("Enter brand name", key="sentiment_brand_input")
                    timeframe = st.selectbox("Select timeframe", ["past_week", "past_month", "past_year"], key="sentiment_timeframe_select")
                    
                    if st.button("Analyze Sentiment", key="sentiment_btn"):
                        if brand_name:
                            with st.spinner("Analyzing sentiment..."):
                                try:
                                    response = requests.post(
                                        f"{BACKEND_URL}/api/analyze_sentiment",
                                        json={"brand_name": brand_name, "timeframe": timeframe}
                                    )
                                    if response.status_code == 200:
                                        result = response.json()
                                        st.success("Sentiment Analysis Complete!")
                                        st.markdown(result['analysis'])
                                    else:
                                        st.error(f"Error: {response.json().get('error', 'Unknown error')}")
                                except Exception as e:
                                    st.error(f"Connection error: {str(e)}")
                
                # Performance Prediction Tab
                with marketing_tabs[5]:
                    st.markdown("#### Content Performance Prediction")
                    content = st.text_area("Enter content to analyze", key="performance_content_input")
                    platform = st.selectbox("Select platform for prediction", ["Twitter", "LinkedIn", "Facebook", "Instagram"], key="performance_platform_select")
                    
                    if st.button("Predict Performance", key="performance_btn"):
                        if content and platform:
                            with st.spinner("Predicting performance..."):
                                try:
                                    response = requests.post(
                                        f"{BACKEND_URL}/api/predict_content_performance",
                                        json={"content": content, "platform": platform}
                                    )
                                    if response.status_code == 200:
                                        result = response.json()
                                        st.success("Performance Prediction Complete!")
                                        st.markdown(result['prediction'])
                                    else:
                                        st.error(f"Error: {response.json().get('error', 'Unknown error')}")
                                except Exception as e:
                                    st.error(f"Connection error: {str(e)}")
                
                # Price Monitoring Tab
                with marketing_tabs[6]:
                    st.markdown("#### Product Price Monitoring")
                    product_url = st.text_input("Enter product URL", key="price_product_url_input")
                    competitors = st.text_input("Enter competitor URLs (comma-separated)", key="price_competitors_input")
                    
                    if st.button("Monitor Prices", key="price_btn"):
                        if product_url:
                            with st.spinner("Monitoring prices..."):
                                try:
                                    response = requests.post(
                                        f"{BACKEND_URL}/api/monitor_prices",
                                        json={
                                            "product_url": product_url,
                                            "competitors": [c.strip() for c in competitors.split(",")] if competitors else []
                                        }
                                    )
                                    if response.status_code == 200:
                                        result = response.json()
                                        st.success("Price Monitoring Complete!")
                                        st.markdown("### Current Prices")
                                        for url, price in result['prices'].items():
                                            st.markdown(f"**{url}:** {price}")
                                        st.markdown("### Analysis")
                                        st.markdown(result['analysis'])
                                    else:
                                        st.error(f"Error: {response.json().get('error', 'Unknown error')}")
                                except Exception as e:
                                    st.error(f"Connection error: {str(e)}")
                
                # Customer Journey Tab
                with marketing_tabs[7]:
                    st.markdown("#### Customer Journey Mapping")
                    customer_data = st.text_area("Enter customer data (JSON format)",
                                               value='{"customer_id": "123", "purchase_history": [], "interactions": []}',
                                               key="journey_customer_data_input")
                    
                    if st.button("Map Journey", key="journey_btn"):
                        if customer_data:
                            with st.spinner("Mapping customer journey..."):
                                try:
                                    response = requests.post(
                                        f"{BACKEND_URL}/api/map_customer_journey",
                                        json={"customer_data": eval(customer_data)}
                                    )
                                    if response.status_code == 200:
                                        result = response.json()
                                        st.success("Customer Journey Mapping Complete!")
                                        st.markdown(result['journey_map'])
                                    else:
                                        st.error(f"Error: {response.json().get('error', 'Unknown error')}")
                                except Exception as e:
                                    st.error(f"Connection error: {str(e)}")

                # Divider
                st.markdown("---")

            if agent["id"] == "healthcare":
                # Healthcare Agent UI
                st.markdown("### Healthcare Assistant")
                
                # Create tabs for different healthcare features
                healthcare_tabs = st.tabs([
                    "💬 Symptom Chat",
                    "✨ Wellness Tips",
                    "🤔 Custom Questions"
                ])
                
                # Symptom Chat Tab
                with healthcare_tabs[0]:
                    st.markdown("#### How are you feeling today?")
                    st.markdown("""
                        Please describe your symptoms in detail, including:
                        - What symptoms you're experiencing
                        - When they started
                        - How severe they are (mild, moderate, severe)
                        - Any triggers you've noticed
                        - How long they last
                        - Any medications you're currently taking
                        - Any other relevant information
                    """)
                    symptoms = st.text_area("Describe your symptoms:", height=150, key="healthcare_symptoms_input")
                    
                    if st.button("Get Friendly Advice", key="healthcare_symptom_btn"):
                        if symptoms:
                            with st.spinner("Analyzing your symptoms and preparing personalized advice..."):
                                try:
                                    response = requests.post(
                                        f"{BACKEND_URL}/api/analyze_symptoms",
                                        json={"symptoms": symptoms}
                                    )
                                    if response.status_code == 200:
                                        result = response.json()
                                        if result["status"] == "success":
                                            st.success("Analysis Complete!")
                                            st.markdown("### Here's what I think:")
                                            st.markdown(result["response"])
                                        else:
                                            st.error(f"Error: {result['message']}")
                                    else:
                                        st.error(f"Error: {response.json().get('error', 'Unknown error')}")
                                except Exception as e:
                                    st.error(f"Connection error: {str(e)}")
                        else:
                            st.warning("Please describe your symptoms first!")
                
                # Wellness Tips Tab
                with healthcare_tabs[1]:
                    st.markdown("#### Get a Daily Wellness Tip")
                    st.markdown("""
                        Click below to receive a personalized wellness tip that includes:
                        - The main tip
                        - Why it's beneficial
                        - How to implement it
                        - Additional related tips
                    """)
                    if st.button("Get Today's Tip", key="healthcare_tip_btn"):
                        with st.spinner("Finding a helpful tip for you..."):
                            try:
                                response = requests.get(f"{BACKEND_URL}/api/get_wellness_tip")
                                if response.status_code == 200:
                                    result = response.json()
                                    if result["status"] == "success":
                                        st.success("Here's your wellness tip!")
                                        st.markdown(result["response"])
                                    else:
                                        st.error(f"Error: {result['message']}")
                                else:
                                    st.error(f"Error: {response.json().get('error', 'Unknown error')}")
                            except Exception as e:
                                st.error(f"Connection error: {str(e)}")
                
                # Custom Questions Tab
                with healthcare_tabs[2]:
                    st.markdown("#### Ask Any Health-Related Question")
                    st.markdown("""
                        Feel free to ask any health-related question! For example:
                        - "What are some good exercises for stress relief?"
                        - "How can I improve my sleep quality?"
                        - "What foods are good for boosting immunity?"
                        - "What are the common causes of headaches?"
                        - "How can I maintain good posture while working?"
                    """)
                    
                    custom_query = st.text_area("Your question:", height=150, key="healthcare_question_input")
                    
                    if st.button("Get Answer", key="healthcare_question_btn"):
                        if custom_query:
                            with st.spinner("Preparing a comprehensive response..."):
                                try:
                                    response = requests.post(
                                        f"{BACKEND_URL}/api/answer_health_question",
                                        json={"query": custom_query}
                                    )
                                    if response.status_code == 200:
                                        result = response.json()
                                        if result["status"] == "success":
                                            st.success("Here's my response:")
                                            st.markdown(result["response"])
                                        else:
                                            st.error(f"Error: {result['message']}")
                                    else:
                                        st.error(f"Error: {response.json().get('error', 'Unknown error')}")
                                except Exception as e:
                                    st.error(f"Connection error: {str(e)}")
                        else:
                            st.warning("Please enter your question first!")
                
                # Footer with Medical Disclaimers
                st.markdown("---")
                st.markdown("""
                    <div style='text-align: center; color: #666;'>
                        <p>Important Medical Disclaimers:</p>
                        <ul style='list-style: none; padding: 0;'>
                            <li>• I'm an AI assistant providing general information only</li>
                            <li>• Always consult healthcare professionals for medical advice</li>
                            <li>• Read all medication and supplement labels carefully</li>
                            <li>• Consult your doctor or pharmacist before starting any medications</li>
                            <li>• Be aware of potential side effects and interactions</li>
                            <li>• Individual responses to medications may vary</li>
                        </ul>
                    </div>
                """, unsafe_allow_html=True)

                # Divider
                st.markdown("---")

            # File uploader - only show for summarizer and finance agents
            if agent["id"] in ["summarizer", "finance"]:
                uploaded_file = st.file_uploader(
                    f"Upload a {', '.join(agent['supported_types'])} file",
                    type=agent["supported_types"],
                    key=f"file_uploader_{agent['id']}",
                )

                if uploaded_file:
                    st.write(f"Selected file: **{uploaded_file.name}**")

                    # Process button
                    if st.button(
                        "▶️ Process Document",
                        key=f"process_btn_{agent['id']}",
                        use_container_width=True,
                    ):
                        with st.spinner("Processing document..."):
                            files = {"file": uploaded_file}
                            try:
                                response = requests.post(
                                    f"{BACKEND_URL}/api/process_document",
                                    files=files,
                                    data={"agent_type": agent["id"]},
                                )

                                if response.status_code == 200:
                                    st.success("✅ Processing complete!")
                                    result = response.json()

                                    # Handle different agent output formats
                                    if agent["id"] == "summarizer" and "summary" in result:
                                        st.markdown("## Summary Results")
                                        st.write(result["summary"])

                                        # Download button
                                        st.download_button(
                                            "⬇️ Download Summary",
                                            result["summary"],
                                            f"{Path(uploaded_file.name).stem}_summary.txt",
                                            mime="text/plain",
                                        )

                                    elif agent["id"] == "finance" and "results" in result:
                                        # Display finance results
                                        st.markdown("## Stock Analysis Results")

                                        # Display charts and analysis for each stock
                                        for stock_result in result["results"]:
                                            st.markdown("---")

                                            # Check if there was an error for this stock
                                            if "status" in stock_result:
                                                st.warning(
                                                    f"**{stock_result['ticker']}**: {stock_result['status']}"
                                                )
                                                continue

                                            # Display stock analysis
                                            st.markdown(
                                                f"### {stock_result['company_name']} ({stock_result['ticker']})"
                                            )

                                            # Create columns for chart and metrics
                                            col1, col2 = st.columns([3, 2])

                                            # Find matching chart
                                            chart_data = next(
                                                (
                                                    c["chart"]
                                                    for c in result["charts"]
                                                    if c["ticker"] == stock_result["ticker"]
                                                ),
                                                None,
                                            )

                                            if chart_data:
                                                # Display chart
                                                with col1:
                                                    img = Image.open(
                                                        BytesIO(
                                                            base64.b64decode(chart_data)
                                                        )
                                                    )
                                                    st.image(
                                                        img,
                                                        caption=f"{stock_result['ticker']} - 1 Year Price Chart",
                                                    )

                                            # Display metrics and recommendation
                                            with col2:
                                                metrics = stock_result["metrics"]
                                                st.metric(
                                                    "Current Price",
                                                    f"${metrics['current_price']:.2f}",
                                                )
                                                st.metric(
                                                    "Annual Return",
                                                    f"{metrics['annual_return']:.2f}%",
                                                )
                                                st.metric(
                                                    "Annual Volatility",
                                                    f"{metrics['annual_volatility']:.2f}%",
                                                )
                                                st.metric(
                                                    "Sharpe Ratio",
                                                    f"{metrics['sharpe_ratio']:.2f}",
                                                )

                                            # Display full analysis with markdown
                                            st.markdown(stock_result["analysis"])

                                            # Download button for individual stock analysis
                                            st.download_button(
                                                f"⬇️ Download {stock_result['ticker']} Analysis",
                                                stock_result["analysis"],
                                                f"{stock_result['ticker']}_analysis.md",
                                                mime="text/markdown",
                                            )

                                        # Create a combined analysis for all stocks
                                        combined_analysis = "# Stock Analysis Report\n\n"
                                        combined_analysis += f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d')}\n\n"

                                        for stock_result in result["results"]:
                                            if "analysis" in stock_result:
                                                combined_analysis += (
                                                    f"## {stock_result['ticker']}\n\n"
                                                )
                                                combined_analysis += (
                                                    stock_result["analysis"] + "\n\n"
                                                )

                                        # Download button for combined analysis
                                        st.download_button(
                                            "⬇️ Download Complete Analysis",
                                            combined_analysis,
                                            f"stock_analysis_report.md",
                                            mime="text/markdown",
                                        )

                                    else:
                                        st.error(f"❌ Error: {response.status_code}")
                                    try:
                                        st.error(
                                            f"Details: {response.json().get('error', 'Unknown error')}"
                                        )
                                    except:
                                        st.error(f"Raw response: {response.text}")

                            except Exception as e:
                                st.error(f"❌ Connection error: {str(e)}")
                                st.info(f"Make sure backend is running at {BACKEND_URL}")
                else:
                    st.info(
                        f"Please upload a {', '.join(agent['supported_types'])} file to get started."
                    )

                    if agent["id"] == "finance":
                        st.markdown(
                            """
                        ### Sample CSV Format
                        
                        You can upload a CSV file with stock tickers like this:
                        
                        ```csv
                        ticker
                        AAPL
                        MSFT
                        GOOG
                        AMZN
                        TSLA
                        ```
                        
                        The first 5 tickers will be analyzed.
                        """
                        )
else:
    st.error("No agents available. Please check that the backend is running correctly.")
    st.markdown(f"Backend URL: {BACKEND_URL}")

    # Allow user to retry connection
    # if st.button("Retry Connection"):
    #     st.rerun()

# Footer
st.markdown("---")
st.markdown("Agent Marketplace | Made with ❤️")
