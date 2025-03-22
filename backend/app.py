from flask import Flask, request, jsonify
import os
import tempfile
from pathlib import Path
import sys
from flask_cors import CORS  # Add this import

# Add parent directory to path to import text_analyzer
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from text_analyzer.agent import DocumentProcessor

# Import finance agent
from agents.finance.agent import FinanceAnalyzer  # Fixed import path

# Import marketing agent
from agents.marketing.agent import MarketingAgencyAutomation  # Fixed import path

# Import healthcare agent
from agents.healthcare.agent import HealthcareAgent

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize processor
processor = DocumentProcessor()

# Initialize LLM
llm = ChatGroq(model="llama-3.3-70b-versatile")
parser = StrOutputParser()

# Storage for processed documents
processed_docs = {}

# Create a registry of agents
agent_registry = {
    "summarizer": {
        "name": "Document Summarizer",
        "processor": processor,
        "description": "Summarize documents and videos",
        "supported_types": ["txt", "pdf", "csv", "mp4", "mov"],
        "mime_types": {
            "txt": "text/plain",
            "pdf": "application/pdf",
            "csv": "text/csv",
            "mp4": "video/mp4",
            "mov": "video/quicktime",
        },
    },
    "finance": {
        "name": "Finance Analyzer",
        "processor": FinanceAnalyzer(),
        "description": "Analyze stocks and financial data",
        "supported_types": ["txt", "csv"],
        "mime_types": {
            "txt": "text/plain",
            "csv": "text/csv",
        },
    },
    "marketing": {
        "name": "Marketing Assistant",
        "processor": MarketingAgencyAutomation(),
        "description": "Marketing automation and analysis tools",
        "supported_types": ["txt", "csv", "json"],
        "mime_types": {
            "txt": "text/plain",
            "csv": "text/csv",
            "json": "application/json",
        },
    },
    "healthcare": {
        "name": "Healthcare Assistant",
        "processor": HealthcareAgent(),
        "description": "Healthcare advice and wellness tips",
        "supported_types": ["txt"],
        "mime_types": {
            "txt": "text/plain",
        },
    },
}


@app.route("/api/agents", methods=["GET"])
def get_agents():
    """Return a list of available agents"""
    agents_list = []
    for agent_id, agent_data in agent_registry.items():
        agents_list.append(
            {
                "id": agent_id,
                "name": agent_data["name"],
                "description": agent_data["description"],
                "supported_types": agent_data["supported_types"],
            }
        )
    return jsonify(agents_list)


@app.route("/api/analyze_tickers", methods=["POST"])
def analyze_tickers():
    """Analyze stock tickers directly"""
    data = request.json
    tickers = data.get("tickers", [])

    if not tickers:
        return jsonify({"error": "No tickers provided"}), 400

    try:
        # Get the finance agent
        finance_processor = agent_registry["finance"]["processor"]

        # Analyze tickers with better error handling
        try:
            analysis_data = finance_processor.process_tickers(tickers)
            return jsonify(analysis_data)
        except Exception as e:
            app.logger.error(f"Error processing tickers: {str(e)}")
            return (
                jsonify(
                    {
                        "results": [
                            {"ticker": t, "status": "Processing error"} for t in tickers
                        ],
                        "charts": [],
                        "error": str(e),
                    }
                ),
                500,
            )

    except Exception as e:
        app.logger.error(f"Error in analyze_tickers endpoint: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/process_document", methods=["POST"])
def process_document():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    # Get the agent type from the request
    agent_type = request.form.get("agent_type", "summarizer")

    # Check if agent exists
    if agent_type not in agent_registry:
        return jsonify({"error": f"Unknown agent type: {agent_type}"}), 400

    # Get the agent data
    agent_data = agent_registry[agent_type]
    processor = agent_data["processor"]
    mime_types = agent_data["mime_types"]

    file = request.files["file"]
    file_ext = Path(file.filename).suffix[1:].lower()

    # Check if file type is supported
    if file_ext not in mime_types:
        return (
            jsonify(
                {"error": f"Unsupported file type for {agent_data['name']}: {file_ext}"}
            ),
            400,
        )

    file_type = mime_types[file_ext]

    # Create temp file with proper extension
    with tempfile.NamedTemporaryFile(suffix=f".{file_ext}", delete=False) as tmp_file:
        file.save(tmp_file.name)
        file_path = tmp_file.name

    try:
        # Handle agent-specific processing
        if agent_type == "finance":
            # Finance agent has its own processing method
            analysis_data = processor.process_file(file_path, file_type)
            return jsonify(analysis_data)

        elif agent_type == "summarizer":
            # Process document with file_type parameter
            chunks = processor.process_file(file_path, file_type)

            # Store processed chunks for later summarization
            processed_docs[file.filename] = chunks

            # Generate summary immediately
            chunk_summaries = []
            prompt_template = ChatPromptTemplate.from_template(
                "Summarize this chunk concisely:\n{document}"
            )

            for chunk in chunks:
                chain = prompt_template | llm | parser
                summary = chain.invoke({"document": chunk.page_content})
                chunk_summaries.append(summary)

            # Generate final summary
            combined = "\n".join(chunk_summaries)
            final_prompt = ChatPromptTemplate.from_template(
                "Combine these summaries into one coherent summary:\n{document}"
            )
            final_chain = final_prompt | llm | parser
            final_summary = final_chain.invoke({"document": combined})

            return jsonify({"summary": final_summary})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        # Clean up temp file
        Path(file_path).unlink(missing_ok=True)


@app.route("/api/summarize", methods=["POST"])
def summarize():
    data = request.json
    file_id = data.get("file_id")

    if not file_id or file_id not in processed_docs:
        return jsonify({"error": "Document not found or not processed"}), 400

    try:
        chunks = processed_docs[file_id]

        # Process chunk summaries
        chunk_summaries = []
        prompt_template = ChatPromptTemplate.from_template(
            "Summarize this chunk concisely:\n{document}"
        )

        for chunk in chunks:
            chain = prompt_template | llm | parser
            summary = chain.invoke({"document": chunk.page_content})
            chunk_summaries.append(summary)

        # Generate final summary
        combined = "\n".join(chunk_summaries)
        final_prompt = ChatPromptTemplate.from_template(
            "Combine these summaries into one coherent summary:\n{document}"
        )
        final_chain = final_prompt | llm | parser
        final_summary = final_chain.invoke({"document": combined})

        return jsonify({"summary": final_summary})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/analyze_seo", methods=["POST"])
def analyze_seo():
    """Analyze website SEO"""
    data = request.json
    url = data.get("url")
    keywords = data.get("keywords", [])

    if not url:
        return jsonify({"error": "URL is required"}), 400

    try:
        marketing_processor = agent_registry["marketing"]["processor"]
        results = marketing_processor.seo_optimizer(url, keywords)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/analyze_competitors", methods=["POST"])
def analyze_competitors():
    """Analyze competitor websites"""
    data = request.json
    competitors = data.get("competitors", [])
    keywords = data.get("keywords", [])

    if not competitors:
        return jsonify({"error": "At least one competitor is required"}), 400

    try:
        marketing_processor = agent_registry["marketing"]["processor"]
        results = marketing_processor.competitor_watchdog(competitors, keywords)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/create_content", methods=["POST"])
def create_content():
    """Create marketing content"""
    data = request.json
    topic = data.get("topic")
    platform = data.get("platform")
    tone = data.get("tone", "professional")

    if not topic or not platform:
        return jsonify({"error": "Topic and platform are required"}), 400

    try:
        marketing_processor = agent_registry["marketing"]["processor"]
        results = marketing_processor.post_creator(topic, platform, tone)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/create_email_campaign", methods=["POST"])
def create_email_campaign():
    """Create email campaign"""
    data = request.json
    campaign_type = data.get("campaign_type")
    audience = data.get("audience", [])

    if not campaign_type or not audience:
        return jsonify({"error": "Campaign type and audience are required"}), 400

    try:
        marketing_processor = agent_registry["marketing"]["processor"]
        results = marketing_processor.smart_email_manager(campaign_type, audience)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/analyze_sentiment", methods=["POST"])
def analyze_sentiment():
    """Analyze brand sentiment"""
    data = request.json
    brand_name = data.get("brand_name")
    timeframe = data.get("timeframe", "past_month")

    if not brand_name:
        return jsonify({"error": "Brand name is required"}), 400

    try:
        marketing_processor = agent_registry["marketing"]["processor"]
        results = marketing_processor.sentiment_analyzer(brand_name, timeframe)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/predict_content_performance", methods=["POST"])
def predict_content_performance():
    """Predict content performance"""
    data = request.json
    content = data.get("content")
    platform = data.get("platform")

    if not content or not platform:
        return jsonify({"error": "Content and platform are required"}), 400

    try:
        marketing_processor = agent_registry["marketing"]["processor"]
        results = marketing_processor.content_performance_predictor(content, platform)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/monitor_prices", methods=["POST"])
def monitor_prices():
    """Monitor product prices"""
    data = request.json
    product_url = data.get("product_url")
    competitors = data.get("competitors", [])

    if not product_url:
        return jsonify({"error": "Product URL is required"}), 400

    try:
        marketing_processor = agent_registry["marketing"]["processor"]
        results = marketing_processor.price_monitor(product_url, competitors)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/map_customer_journey", methods=["POST"])
def map_customer_journey():
    """Map customer journey"""
    data = request.json
    customer_data = data.get("customer_data")

    if not customer_data:
        return jsonify({"error": "Customer data is required"}), 400

    try:
        marketing_processor = agent_registry["marketing"]["processor"]
        results = marketing_processor.customer_journey_mapper(customer_data)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/analyze_symptoms", methods=["POST"])
def analyze_symptoms():
    """Analyze user symptoms and provide advice"""
    data = request.json
    symptoms = data.get("symptoms")

    if not symptoms:
        return jsonify({"error": "Symptoms are required"}), 400

    try:
        healthcare_processor = agent_registry["healthcare"]["processor"]
        result = healthcare_processor.analyze_symptoms(symptoms)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/get_wellness_tip", methods=["GET"])
def get_wellness_tip():
    """Get a daily wellness tip"""
    try:
        healthcare_processor = agent_registry["healthcare"]["processor"]
        result = healthcare_processor.get_wellness_tip()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/answer_health_question", methods=["POST"])
def answer_health_question():
    """Answer a custom health-related question"""
    data = request.json
    query = data.get("query")

    if not query:
        return jsonify({"error": "Question is required"}), 400

    try:
        healthcare_processor = agent_registry["healthcare"]["processor"]
        result = healthcare_processor.answer_health_question(query)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Add a health check endpoint
@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy", "agents": list(agent_registry.keys())}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 9000))
    print(f"Starting backend server on port {port}")
    app.run(debug=True, host="0.0.0.0", port=port)
