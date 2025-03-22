from flask import Flask, request, jsonify
import os
import tempfile
from pathlib import Path
import sys

# Add parent directory to path to import text_analyzer
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from text_analyzer.agent import DocumentProcessor

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Initialize processor
processor = DocumentProcessor()

# Initialize LLM
llm = ChatGroq(model="llama-3.3-70b-versatile")
parser = StrOutputParser()

# Storage for processed documents
processed_docs = {}


@app.route("/api/process_document", methods=["POST"])
def process_document():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    file_ext = Path(file.filename).suffix[1:].lower()

    # Map file extensions to MIME types
    mime_types = {
        "txt": "text/plain",
        "pdf": "application/pdf",
        "csv": "text/csv",
        "mp4": "video/mp4",
        "mov": "video/quicktime",
    }

    # Check if file type is supported
    if file_ext not in mime_types:
        return jsonify({"error": f"Unsupported file type: {file_ext}"}), 400

    file_type = mime_types[file_ext]

    # Create temp file with proper extension
    with tempfile.NamedTemporaryFile(suffix=f".{file_ext}", delete=False) as tmp_file:
        file.save(tmp_file.name)
        file_path = tmp_file.name

    try:
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


# Add a health check endpoint
@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy"}), 200


if __name__ == "__main__":
    port = 9000
    print(f"Starting backend server on port {port}")
    app.run(debug=True, host="0.0.0.0", port=port)
