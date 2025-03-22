from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from educational_agent.educational_agent import educational_bp

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Register blueprints
app.register_blueprint(educational_bp)

@app.route("/api/agents", methods=["GET"])
def get_all_agents():
    """Return a list of all available agents"""
    agents_list = [
        {
            "id": "summarizer",
            "name": "Document Summarizer",
            "description": "AI-powered document summarization tool that creates concise summaries of long documents.",
            "supported_types": ["txt", "pdf"]
        },
        {
            "id": "marketing",
            "name": "Marketing Analysis",
            "description": "Comprehensive marketing analysis including competitor research, market trends, and campaign optimization.",
            "supported_types": ["txt", "pdf", "csv"]
        },
        {
            "id": "healthcare",
            "name": "Healthcare Analysis",
            "description": "Comprehensive health analysis including symptom analysis, medication review, health metrics, and more.",
            "supported_types": ["txt", "pdf", "csv"]
        },
        {
            "id": "finance",
            "name": "Financial Analysis",
            "description": "Comprehensive financial analysis including market trends, investment opportunities, and risk assessment.",
            "supported_types": ["txt", "pdf", "csv"]
        },
        {
            "id": "education",
            "name": "Educational Resources",
            "description": "AI-powered learning companion that provides curated educational resources, tutorials, and study materials.",
            "supported_types": ["txt", "pdf", "csv"]
        }
    ]
    return jsonify(agents_list)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 9000))
    print(f"Starting backend server on port {port}")
    app.run(debug=True, host="0.0.0.0", port=port)
