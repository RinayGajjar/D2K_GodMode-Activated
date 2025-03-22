from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

class HealthcareAgent:
    def __init__(self):
        # Initialize Groq chat model
        self.chat = ChatGroq(
            groq_api_key=os.getenv("GROQ_API_KEY"),
            model_name="llama-3.3-70b-versatile",
            temperature=0.7
        )

        # Create prompt templates
        self.symptom_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a friendly and empathetic healthcare AI assistant. 
            When users describe their symptoms, provide a comprehensive response that includes:
            1. A brief understanding of their symptoms
            2. Potential causes (but emphasize that this is general information)
            3. General self-care tips that might help
            4. Common over-the-counter medications that might help (with clear disclaimers)
            5. When to seek professional medical help
            6. Lifestyle recommendations for prevention
            
            Important Medication Disclaimers:
            - Always mention that medication recommendations are general information only
            - Emphasize the importance of reading medication labels and warnings
            - Advise consulting a pharmacist or healthcare provider before taking any medication
            - Include common side effects and interactions to be aware of
            - Remind users that medication effectiveness varies by individual
            
            Always remind them that you're an AI and they should consult healthcare professionals for medical advice.
            Keep your responses concise, friendly, and easy to understand.
            Format your response in clear sections with bullet points where appropriate."""),
            ("user", "{symptoms}")
        ])

        self.care_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a friendly healthcare AI assistant providing comprehensive wellness tips.
            For each tip, include:
            1. The main wellness tip
            2. Why it's beneficial
            3. How to implement it
            4. Additional related tips
            5. Common supplements or vitamins that might support this wellness goal (with disclaimers)
            
            Important Supplement Disclaimers:
            - Always mention that supplement recommendations are general information only
            - Emphasize the importance of reading supplement labels
            - Advise consulting a healthcare provider before starting any supplements
            - Include potential interactions with medications
            - Remind users that supplement effectiveness varies by individual
            
            Keep your suggestions simple, practical, and encouraging.
            Focus on general wellness and lifestyle advice, not medical treatment.
            Format your response in clear sections with bullet points where appropriate."""),
            ("user", "Please provide a detailed wellness tip for today.")
        ])

        self.custom_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a friendly and knowledgeable healthcare AI assistant.
            For each health-related question, provide a comprehensive response that includes:
            1. Direct answer to the question
            2. Scientific explanation (in simple terms)
            3. Practical tips for implementation
            4. Related health benefits
            5. Common medications or supplements that might be relevant (with disclaimers)
            6. When to consult a healthcare professional
            
            Important Medication/Supplement Disclaimers:
            - Always mention that medication/supplement recommendations are general information only
            - Emphasize the importance of reading labels and warnings
            - Advise consulting healthcare providers before starting any medications or supplements
            - Include potential side effects and interactions
            - Remind users that effectiveness varies by individual
            
            Always maintain a supportive tone and remind users to consult healthcare professionals for medical advice.
            Keep responses clear, concise, and easy to understand.
            Format your response in clear sections with bullet points where appropriate."""),
            ("user", "{query}")
        ])

        # Create chains
        self.symptom_chain = self.symptom_prompt | self.chat | StrOutputParser()
        self.care_chain = self.care_prompt | self.chat | StrOutputParser()
        self.custom_chain = self.custom_prompt | self.chat | StrOutputParser()

    def analyze_symptoms(self, symptoms):
        """Analyze user symptoms and provide advice"""
        try:
            response = self.symptom_chain.invoke({"symptoms": symptoms})
            return {"status": "success", "response": response}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_wellness_tip(self):
        """Get a daily wellness tip"""
        try:
            response = self.care_chain.invoke({})
            return {"status": "success", "response": response}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def answer_health_question(self, query):
        """Answer a custom health-related question"""
        try:
            response = self.custom_chain.invoke({"query": query})
            return {"status": "success", "response": response}
        except Exception as e:
            return {"status": "error", "message": str(e)} 