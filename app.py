import os
import streamlit as st
import tempfile
import time
from pathlib import Path
from text_analyzer import DocumentProcessor
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai import upload_file, get_file
import datetime
load_dotenv()

# Initialize core components
processor = DocumentProcessor()
llm = ChatGroq(model="llama-3.3-70b-versatile")
parser = StrOutputParser()

# Configure Gemini
if os.getenv("GOOGLE_API_KEY"):
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

st.title("Multi-Modal Document Analyzer")
st.divider()

# Supported file types
SUPPORTED_TYPES = {
    "txt": "text/plain",
    "pdf": "application/pdf",
    "csv": "text/csv",
    "mp4": "video/mp4",
    "mov": "video/quicktime",
}

def process_video(video_path):
    try:
        processed_video = upload_file(video_path, mime_type="video/mp4")
        while processed_video.state.name == "PROCESSING":
            time.sleep(1)
            processed_video = get_file(processed_video.name)
        
        model = genai.GenerativeModel('models/gemini-1.5-flash-latest')
        response = model.generate_content([
            "Analyze this video and provide a comprehensive English summary.",
            processed_video
        ])
        return response.text
    except Exception as e:
        st.error(f"Video processing error: {str(e)}")
        return None

# File upload section
uploaded_file = st.file_uploader(
    "Upload document or video", 
    type=["txt", "pdf", "csv", "mp4", "mov"]
)

summary_container = st.container()

if uploaded_file:
    file_ext = Path(uploaded_file.name).suffix[1:].lower()
    
    # Create temp file with proper extension
    with tempfile.NamedTemporaryFile(suffix=f".{file_ext}", delete=False) as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_path = tmp_file.name
    
    try:
        if file_ext in ["mp4", "mov"]:
            st.video(tmp_path)
            with st.spinner("Analyzing video..."):
                video_summary = process_video(tmp_path)
                
                if video_summary:
                    summary_container.markdown("## Video Summary")
                    summary_container.write(video_summary)
                    st.download_button(
                        label="Download Video Summary",
                        data=video_summary,
                        file_name="video_summary.txt"
                    )
        else:
            with st.spinner("Processing document..."):
                chunks = processor.process_file(tmp_path, SUPPORTED_TYPES[file_ext])
                st.session_state.chunks = chunks
                st.success("Document processed and stored in ChromaDB!")

    except Exception as e:
        st.error(f"Processing error: {str(e)}")
        st.stop()
    finally:
        Path(tmp_path).unlink(missing_ok=True)

if 'chunks' in st.session_state and st.button("Generate Document Summary"):
    with st.spinner("Summarizing..."):
        try:
            chunk_summaries = []
            prompt_template = ChatPromptTemplate.from_template(
                "Summarize this chunk concisely:\n{document}"
            )
            
            for chunk in st.session_state.chunks:
                chain = prompt_template | llm | parser
                summary = chain.invoke({"document": chunk.page_content})
                chunk_summaries.append(summary)
            
            combined = "\n".join(chunk_summaries)
            final_prompt = ChatPromptTemplate.from_template(
                "Combine these summaries into one:\n{document}"
            )
            final_chain = final_prompt | llm | parser 
            final_summary = final_chain.invoke({"document": combined})
            
            summary_container.markdown("## Document Summary")
            summary_container.write(final_summary)
            
            st.download_button(
                label="Download Document Summary",
                data=final_summary,
                file_name="document_summary.txt"
            )
            
        except Exception as e:
            st.error(f"Summarization error: {str(e)}")

st.markdown("""
    <style>
    .stTextArea textarea {
        height: 100px;
    }
    .stVideo {
        border-radius: 10px;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)






# import os
# import streamlit as st
# import tempfile
# from text_analyzer import DocumentProcessor
# from langchain_groq import ChatGroq
# from langchain_core.prompts import ChatPromptTemplate
# from langchain_core.output_parsers import StrOutputParser
# from dotenv import load_dotenv

# load_dotenv()

# # Initialize core components
# processor = DocumentProcessor()
# llm = ChatGroq(model="llama-3.3-70b-versatile")
# parser = StrOutputParser()

# st.title("Document Analyzer")
# st.divider()

# # File upload section
# uploaded_file = st.file_uploader("Upload document", type=["txt", "pdf", "csv"])
# summary_container = st.container()

# if uploaded_file:
#     # Use temporary file with context manager
#     with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
#         tmp_file.write(uploaded_file.getvalue())
#         tmp_path = tmp_file.name
    
#     try:
#         with st.spinner("Processing document..."):
#             chunks = processor.process_file(
#                 tmp_path, 
#                 uploaded_file.type
#             )
#             st.session_state.chunks = chunks
#             st.success("Document processed and stored in ChromaDB!")
            
#     except Exception as e:
#         st.error(f"Error: {str(e)}")
#         st.stop()
#     finally:
#         os.unlink(tmp_path)  # Clean up temp file

# # Summarization section
# if 'chunks' in st.session_state and st.button("Generate Summary"):
#     with st.spinner("Summarizing..."):
#         try:
#             # Chunk summarization
#             chunk_summaries = []
#             prompt_template = ChatPromptTemplate.from_template(
#                 "Summarize this chunk concisely, focusing on key facts:\n{document}"
#             )
            
#             for chunk in st.session_state.chunks:
#                 chain = prompt_template | llm | parser
#                 summary = chain.invoke({"document": chunk.page_content})
#                 chunk_summaries.append(summary)
            
#             # Final summary
#             combined = "\n".join(chunk_summaries)
#             final_prompt = ChatPromptTemplate.from_template(
#                 """Combine these chunk summaries into a cohesive final summary:
#                 {document}
                
#                 Maintain:
#                 - Clear section headers
#                 - Bullet points for key items
#                 - Technical terminology preservation"""
#             )
#             final_chain = final_prompt | llm | parser
#             final_summary = final_chain.invoke({"document": combined})
            
#             summary_container.markdown("## Final Summary")
#             summary_container.write(final_summary)
            
#             # Download button
#             st.download_button(
#                 label="Download Summary",
#                 data=final_summary,
#                 file_name="document_summary.txt"
#             )
            
#         except Exception as e:
#             st.error(f"Summarization error: {str(e)}")