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
            agents = response.json()
            # Add healthcare and education agents if not present in backend response
            additional_agents = [
                {
                    "id": "healthcare",
                    "name": "Healthcare Analysis",
                    "description": "Comprehensive health analysis including symptom analysis, medication review, health metrics, and more.",
                    "supported_types": ["txt", "pdf", "csv"]
                },
                {
                    "id": "education",
                    "name": "Educational Resources",
                    "description": "AI-powered learning companion that provides curated educational resources, tutorials, and study materials.",
                    "supported_types": ["txt", "pdf", "csv"]
                }
            ]
            for agent in additional_agents:
                if not any(a["id"] == agent["id"] for a in agents):
                    agents.append(agent)
            return agents
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
                                    combined_analysis += f"Generated on: {datetime.now().strftime('%Y-%m-%d')}\n\n"

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
                st.markdown("### Healthcare Analysis Suite")
                
                # Analysis mode selection
                analysis_mode = st.radio(
                    "Select Analysis Mode",
                    ["Individual Analysis", "Comprehensive Analysis"],
                    help="Choose between individual analysis or comprehensive analysis with chaining"
                )
                
                if analysis_mode == "Individual Analysis":
                    # Create tabs for different healthcare features
                    healthcare_tabs = st.tabs([
                        "🔍 Symptom Analysis",
                        "💊 Medication Review",
                        "📊 Health Metrics",
                        "🥗 Nutrition Analysis",
                        "💪 Fitness Planning",
                        "😴 Sleep Analysis",
                        "🧠 Mental Health",
                        "📈 Health Trends"
                    ])
                    
                    # Symptom Analysis Tab
                    with healthcare_tabs[0]:
                        st.markdown("#### Symptom Analysis")
                        symptoms = st.text_input("Describe your symptoms", key="symptoms_input")
                        duration = st.text_input("Duration of symptoms", key="duration_input")
                        severity = st.slider("Severity (1-10)", 1, 10, 5, key="severity_slider")
                        
                        if st.button("Analyze Symptoms", key="symptoms_btn"):
                            if symptoms:
                                with st.spinner("Analyzing symptoms..."):
                                    try:
                                        # For now, generate a mock response since the API endpoint doesn't exist
                                        mock_result = {
                                            'analysis': f"""
### Symptom Analysis Results
- **Symptoms Reported:** {symptoms}
- **Duration:** {duration}
- **Severity Level:** {severity}/10

Based on the symptoms reported, here are some potential considerations:
1. Monitor the severity level closely
2. Keep track of any changes in symptoms
3. Consider consulting a healthcare professional if symptoms persist
""",
                                            'recommendations': f"""
### Recommendations
1. **Immediate Actions:**
   - Rest and stay hydrated
   - Monitor symptoms for any changes
   - Keep a symptom diary

2. **When to Seek Medical Attention:**
   - If severity increases
   - If new symptoms develop
   - If symptoms persist beyond {duration}

3. **General Advice:**
   - Maintain good hygiene
   - Get adequate rest
   - Stay hydrated
"""
                                        }
                                        st.success("Analysis Complete!")
                                        st.markdown("### Analysis Results")
                                        st.markdown(mock_result['analysis'])
                                        st.markdown("### Recommendations")
                                        st.markdown(mock_result['recommendations'])
                                    except Exception as e:
                                        st.error(f"Error during analysis: {str(e)}")
                    
                    # Medication Review Tab
                    with healthcare_tabs[1]:
                        st.markdown("#### Medication Review")
                        medications = st.text_input("List your current medications", key="medications_input")
                        conditions = st.text_input("List your medical conditions", key="conditions_input")
                        
                        if st.button("Review Medications", key="medications_btn"):
                            if medications:
                                with st.spinner("Reviewing medications..."):
                                    try:
                                        # Mock response for medication review
                                        mock_result = {
                                            'analysis': f"""
### Medication Review Results
- **Current Medications:** {medications}
- **Medical Conditions:** {conditions}

Analysis of current medication regimen:
1. Reviewing potential interactions
2. Assessing medication effectiveness
3. Identifying any gaps in treatment
""",
                                            'interactions': f"""
### Potential Interactions and Considerations
1. **Medication Interactions:**
   - Review with your healthcare provider
   - Monitor for any side effects
   - Keep track of medication timing

2. **General Recommendations:**
   - Take medications as prescribed
   - Keep a medication schedule
   - Report any side effects to your doctor
"""
                                        }
                                        st.success("Review Complete!")
                                        st.markdown("### Medication Analysis")
                                        st.markdown(mock_result['analysis'])
                                        st.markdown("### Potential Interactions")
                                        st.markdown(mock_result['interactions'])
                                    except Exception as e:
                                        st.error(f"Error during review: {str(e)}")
                    
                    # Health Metrics Tab
                    with healthcare_tabs[2]:
                        st.markdown("#### Health Metrics Analysis")
                        weight = st.number_input("Weight (kg)", key="weight_input")
                        height = st.number_input("Height (cm)", key="height_input")
                        blood_pressure = st.text_input("Blood Pressure (e.g., 120/80)", key="bp_input")
                        heart_rate = st.number_input("Heart Rate (bpm)", key="hr_input")
                        
                        if st.button("Analyze Metrics", key="metrics_btn"):
                            with st.spinner("Analyzing health metrics..."):
                                try:
                                    # Mock response for health metrics
                                    mock_result = {
                                        'status': f"""
### Health Status Overview
- **Weight:** {weight} kg
- **Height:** {height} cm
- **Blood Pressure:** {blood_pressure}
- **Heart Rate:** {heart_rate} bpm

Analysis of current health metrics:
1. Calculating BMI and body composition
2. Assessing cardiovascular health
3. Evaluating overall fitness level
""",
                                        'recommendations': f"""
### Health Recommendations
1. **Weight Management:**
   - Maintain a balanced diet
   - Regular physical activity
   - Monitor weight changes

2. **Cardiovascular Health:**
   - Regular blood pressure monitoring
   - Heart rate tracking during exercise
   - Stress management techniques

3. **General Wellness:**
   - Regular check-ups
   - Balanced nutrition
   - Adequate sleep
"""
                                    }
                                    st.success("Analysis Complete!")
                                    st.markdown("### Health Status")
                                    st.markdown(mock_result['status'])
                                    st.markdown("### Recommendations")
                                    st.markdown(mock_result['recommendations'])
                                except Exception as e:
                                    st.error(f"Error during analysis: {str(e)}")
                    
                else:  # Comprehensive Analysis
                    st.markdown("### Comprehensive Health Analysis")
                    st.markdown("This mode will perform a complete health analysis by chaining multiple analyses together.")
                    
                    # Progress tracking
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # Initialize session state for results
                    if 'health_analysis_results' not in st.session_state:
                        st.session_state.health_analysis_results = {}
                    
                    # Input collection
                    st.markdown("#### Health Information")
                    col1, col2 = st.columns(2)
                    with col1:
                        symptoms = st.text_input("Describe your symptoms", key="comp_symptoms_input")
                        medications = st.text_input("List your current medications", key="comp_medications_input")
                        conditions = st.text_input("List your medical conditions", key="comp_conditions_input")
                    
                    with col2:
                        weight = st.number_input("Weight (kg)", key="comp_weight_input")
                        height = st.number_input("Height (cm)", key="comp_height_input")
                        blood_pressure = st.text_input("Blood Pressure (e.g., 120/80)", key="comp_bp_input")
                        heart_rate = st.number_input("Heart Rate (bpm)", key="comp_hr_input")
                    
                    if st.button("Run Comprehensive Analysis", key="comp_analysis_btn"):
                        with st.spinner("Running comprehensive analysis..."):
                            try:
                                # Generate mock results for each analysis
                                mock_symptoms_result = {
                                    'analysis': f"### Symptom Analysis\n- Symptoms: {symptoms}\n- Duration: ongoing\n- Severity: moderate",
                                    'recommendations': "Monitor symptoms and consult healthcare provider if needed."
                                }
                                
                                mock_medications_result = {
                                    'analysis': f"### Medication Review\n- Medications: {medications}\n- Conditions: {conditions}",
                                    'interactions': "Review medication interactions with healthcare provider."
                                }
                                
                                mock_metrics_result = {
                                    'status': f"### Health Metrics\n- Weight: {weight}kg\n- Height: {height}cm\n- BP: {blood_pressure}\n- HR: {heart_rate}bpm",
                                    'recommendations': "Maintain regular monitoring of health metrics."
                                }
                                
                                # Store results in session state
                                st.session_state.health_analysis_results['symptoms'] = mock_symptoms_result
                                st.session_state.health_analysis_results['medications'] = mock_medications_result
                                st.session_state.health_analysis_results['metrics'] = mock_metrics_result
                                
                                # Generate comprehensive report
                                report = "# Comprehensive Health Analysis Report\n\n"
                                report += f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d')}\n\n"
                                
                                # Generate Executive Summary
                                executive_summary = "## Executive Summary\n\n"
                                executive_summary += "### Key Findings\n"
                                
                                # Add symptom summary
                                if symptoms:
                                    executive_summary += f"- **Symptoms:** {symptoms}\n"
                                
                                # Add medication summary
                                if medications:
                                    executive_summary += f"- **Current Medications:** {medications}\n"
                                
                                # Add health metrics summary
                                if weight and height:
                                    bmi = weight / ((height/100) ** 2)
                                    executive_summary += f"- **BMI:** {bmi:.1f}\n"
                                if blood_pressure:
                                    executive_summary += f"- **Blood Pressure:** {blood_pressure}\n"
                                if heart_rate:
                                    executive_summary += f"- **Heart Rate:** {heart_rate} bpm\n"
                                
                                executive_summary += "\n### Overall Health Status\n"
                                executive_summary += "Based on the provided information:\n"
                                
                                # Add health status assessment
                                if symptoms:
                                    executive_summary += "- Currently experiencing symptoms that require monitoring\n"
                                if medications:
                                    executive_summary += "- On medication regimen requiring regular review\n"
                                if weight and height:
                                    if bmi < 18.5:
                                        executive_summary += "- BMI indicates underweight status\n"
                                    elif bmi < 25:
                                        executive_summary += "- BMI indicates healthy weight range\n"
                                    elif bmi < 30:
                                        executive_summary += "- BMI indicates overweight status\n"
                                    else:
                                        executive_summary += "- BMI indicates obesity\n"
                                
                                executive_summary += "\n### Priority Actions\n"
                                executive_summary += "1. Regular monitoring of reported symptoms\n"
                                executive_summary += "2. Medication adherence and side effect monitoring\n"
                                executive_summary += "3. Regular health metrics tracking\n"
                                executive_summary += "4. Follow-up with healthcare provider as needed\n"
                                
                                # Add executive summary to report
                                report += executive_summary + "\n"
                                
                                # Add sections from each analysis
                                report += "## Detailed Analysis\n"
                                report += mock_symptoms_result['analysis'] + "\n\n"
                                
                                report += "## Medication Review\n"
                                report += mock_medications_result['analysis'] + "\n\n"
                                
                                report += "## Health Metrics Analysis\n"
                                report += mock_metrics_result['status'] + "\n\n"
                                
                                # Add recommendations
                                report += "## Overall Recommendations\n"
                                report += mock_symptoms_result['recommendations'] + "\n"
                                report += mock_medications_result['interactions'] + "\n"
                                report += mock_metrics_result['recommendations'] + "\n"
                                
                                # Display report in tabs
                                progress_bar.progress(100)
                                status_text.text("Analysis complete!")
                                
                                report_tabs = st.tabs([
                                    "📊 Executive Summary",
                                    "📝 Recommendations"
                                ])
                                
                                with report_tabs[0]:
                                    st.markdown("### Executive Summary")
                                    st.markdown(executive_summary)
                                
                                with report_tabs[1]:
                                    st.markdown("### Recommendations")
                                    st.markdown(mock_symptoms_result['recommendations'])
                                    st.markdown(mock_medications_result['interactions'])
                                    st.markdown(mock_metrics_result['recommendations'])

                                # Download button for comprehensive report
                                st.download_button(
                                    "⬇️ Download Comprehensive Report",
                                    report,
                                    "comprehensive_health_analysis.md",
                                    mime="text/markdown"
                                )
                                
                            except Exception as e:
                                st.error(f"Error during comprehensive analysis: {str(e)}")
                                progress_bar.progress(0)
                                status_text.text("Analysis failed. Please try again.")
                
                # Skip file uploader for healthcare agent
                continue

            if agent["id"] == "education":
                # Educational Agent UI
                st.markdown("### 🎓 Educational Resource Hub")
                
                # Analysis mode selection
                analysis_mode = st.radio(
                    "Select Analysis Mode",
                    ["Resource Search", "Question Answering"],
                    help="Choose between searching for learning resources or asking questions about a topic"
                )
                
                if analysis_mode == "Resource Search":
                    # Resource Search Mode
                    st.markdown("#### Find Learning Resources")
                    topic = st.text_input(
                        "What would you like to learn about?",
                        placeholder="e.g., Machine Learning, Quantum Physics, etc.",
                        key="education_topic_input"
                    )
                    
                    if st.button("🔍 Search Resources", key="education_search_btn"):
                        if topic:
                            with st.spinner("Searching for the best learning resources..."):
                                try:
                                    response = requests.post(
                                        f"{BACKEND_URL}/api/search_resources",
                                        json={"topic": topic}
                                    )
                                    
                                    if response.status_code == 200:
                                        result = response.json()
                                        st.success("Resources found!")
                                        
                                        # Display resources by category
                                        for category, resources in result.items():
                                            st.markdown(f"### 📌 {category}")
                                            if isinstance(resources, list):
                                                for resource in resources:
                                                    if isinstance(resource, dict):
                                                        title = resource.get('title', '')
                                                        url = resource.get('url', '')
                                                        if title and url:
                                                            st.markdown(f"- [{title}]({url})")
                                            else:
                                                st.markdown(f"- {resources}")
                                        
                                        # Download button for resource list
                                        resource_report = f"# Learning Resources for {topic}\n\n"
                                        for category, resources in result.items():
                                            resource_report += f"## {category}\n"
                                            if isinstance(resources, list):
                                                for resource in resources:
                                                    if isinstance(resource, dict):
                                                        title = resource.get('title', '')
                                                        url = resource.get('url', '')
                                                        if title and url:
                                                            resource_report += f"- [{title}]({url})\n"
                                            else:
                                                resource_report += f"- {resources}\n"
                                            resource_report += "\n"
                                        
                                        st.download_button(
                                            "⬇️ Download Resource List",
                                            resource_report,
                                            f"learning_resources_{topic.lower().replace(' ', '_')}.md",
                                            mime="text/markdown"
                                        )
                                    else:
                                        st.error(f"Error: {response.json().get('error', 'Unknown error')}")
                                except Exception as e:
                                    st.error(f"Connection error: {str(e)}")
                        else:
                            st.warning("Please enter a topic to search for resources.")
                    
                    # Popular topics section
                    st.markdown("### 📚 Popular Topics")
                    popular_topics = [
                        "Machine Learning",
                        "Web Development",
                        "Data Science",
                        "Artificial Intelligence",
                        "Python Programming",
                        "Cloud Computing",
                        "Cybersecurity",
                        "Mobile Development"
                    ]
                    
                    cols = st.columns(4)
                    for i, topic in enumerate(popular_topics):
                        with cols[i % 4]:
                            if st.button(topic, key=f"popular_topic_{i}"):
                                st.session_state.education_topic_input = topic
                                st.rerun()
                
                else:  # Question Answering Mode
                    st.markdown("#### Ask Questions About Your Topic")
                    topic = st.text_input(
                        "Enter your topic",
                        placeholder="e.g., Machine Learning, Quantum Physics, etc.",
                        key="qa_topic_input"
                    )
                    question = st.text_area(
                        "What would you like to know?",
                        placeholder="Ask your question here...",
                        key="qa_question_input"
                    )
                    
                    if st.button("❓ Get Answer", key="qa_btn"):
                        if topic and question:
                            with st.spinner("Finding the answer..."):
                                try:
                                    response = requests.post(
                                        f"{BACKEND_URL}/api/answer_question",
                                        json={
                                            "topic": topic,
                                            "question": question
                                        }
                                    )
                                    
                                    if response.status_code == 200:
                                        result = response.json()
                                        st.success("Answer found!")
                                        st.markdown("### Answer")
                                        st.markdown(result['answer'])
                                        
                                        # Download button for Q&A
                                        qa_report = f"# Q&A for {topic}\n\n"
                                        qa_report += f"## Question\n{question}\n\n"
                                        qa_report += f"## Answer\n{result['answer']}\n"
                                        
                                        st.download_button(
                                            "⬇️ Download Q&A",
                                            qa_report,
                                            f"qa_{topic.lower().replace(' ', '_')}.md",
                                            mime="text/markdown"
                                        )
                                    else:
                                        st.error(f"Error: {response.json().get('error', 'Unknown error')}")
                                except Exception as e:
                                    st.error(f"Connection error: {str(e)}")
                        else:
                            st.warning("Please enter both a topic and a question.")
                
                # Skip file uploader for education agent
                continue

            # File uploader
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
                                    combined_analysis += f"Generated on: {st.session_state.get('run_date', 'today')}\n\n"

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
                                    # Generic display for other agent types
                                    st.json(result)
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
