from flask import Blueprint, request, jsonify
import os
from dotenv import load_dotenv
import groq
from tavily import TavilyClient
import json

# Load environment variables
load_dotenv()

# Initialize Blueprint
educational_bp = Blueprint('educational', __name__)

# Initialize Groq and Tavily clients
groq_client = groq.Groq(api_key=os.getenv("GROQ_API_KEY"))
tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

@educational_bp.route("/api/agents/education", methods=["GET"])
def get_educational_agent():
    """Return the educational agent information"""
    agent_info = {
        "id": "education",
        "name": "Educational Resources",
        "description": "AI-powered learning companion that provides curated educational resources, tutorials, and study materials.",
        "supported_types": ["txt", "pdf", "csv"]
    }
    return jsonify(agent_info)

@educational_bp.route("/api/search_resources", methods=["POST"])
def search_resources():
    """Search for educational resources"""
    try:
        data = request.get_json()
        if not data or 'topic' not in data:
            return jsonify({'error': 'Topic is required'}), 400
        
        topic = data['topic']
        
        # Search for resources using Tavily
        search_query = f"{topic} academic resources tutorials courses papers"
        response = tavily_client.search(
            query=search_query,
            search_depth="advanced",
            include_answer=True,
            include_domains=[
                "github.com", "arxiv.org", "youtube.com", "coursera.org", 
                "reddit.com", "stackoverflow.com", "medium.com", 
                "towardsdatascience.com", "kaggle.com", "udemy.com",
                "edx.org", "pluralsight.com", "freecodecamp.org",
                "w3schools.com", "geeksforgeeks.org", "tutorialspoint.com"
            ]
        )
        
        # Prepare context for Groq
        context = f"Topic: {topic}\n\nSearch Results:\n"
        for result in response.get("results", [])[:10]:
            context += f"- {result.get('title', '')}: {result.get('url', '')}\n"
        
        # Create prompt for Groq
        prompt = f"""Analyze these search results for the topic '{topic}' and categorize them into the following categories:
        1. Blogs & Articles
        2. Tutorials
        3. YouTube Videos
        4. Online Courses
        5. Research Papers
        6. Books & PDFs
        7. Communities & Forums
        8. Practice & Projects

        For each category, provide a list of relevant resources with their titles and URLs.
        Format the response as a JSON object with these categories as keys.
        Only include categories that have relevant resources.
        Ensure all URLs are valid and accessible.

        Search Results:
        {context}"""

        # Get response from Groq
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that categorizes academic resources."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )

        try:
            # Parse the response as JSON
            response_text = completion.choices[0].message.content
            # Extract JSON from the response (in case there's additional text)
            json_str = response_text[response_text.find("{"):response_text.rfind("}")+1]
            return jsonify(json.loads(json_str))
        except Exception as e:
            print(f"Error parsing Groq response: {e}")
            return jsonify({})
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@educational_bp.route("/api/answer_question", methods=["POST"])
def answer_question():
    """Answer questions about a topic"""
    try:
        data = request.get_json()
        if not data or 'topic' not in data or 'question' not in data:
            return jsonify({'error': 'Topic and question are required'}), 400
        
        topic = data['topic']
        question = data['question']
        
        # Search for relevant information
        search_query = f"{topic} {question}"
        response = tavily_client.search(
            query=search_query,
            search_depth="advanced",
            include_answer=True,
            include_domains=[
                "github.com", "arxiv.org", "youtube.com", "coursera.org", 
                "reddit.com", "stackoverflow.com", "medium.com", 
                "towardsdatascience.com", "kaggle.com", "udemy.com",
                "edx.org", "pluralsight.com", "freecodecamp.org",
                "w3schools.com", "geeksforgeeks.org", "tutorialspoint.com"
            ]
        )
        
        # Prepare context from search results
        context = f"Topic: {topic}\nQuestion: {question}\n\nRelevant Information:\n"
        for result in response.get("results", [])[:5]:
            context += f"- {result.get('title', '')}: {result.get('url', '')}\n"
        
        # Create prompt for Groq
        prompt = f"""Based on the following information about {topic}, please answer this question: {question}

        Provide a clear, concise, and informative answer. Include relevant details and examples when possible.
        If you're not sure about something, please say so.
        Structure your answer with:
        1. A direct answer to the question
        2. Key points or steps
        3. Examples or use cases
        4. Additional resources for learning more

        Context:
        {context}"""

        # Get response from Groq
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a helpful educational assistant that provides clear and accurate answers."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )

        return jsonify({'answer': completion.choices[0].message.content})
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500 