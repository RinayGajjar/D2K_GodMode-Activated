import streamlit as st
import requests
import os
from pathlib import Path

# Update this to the correct backend URL
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:9000")

st.set_page_config(page_title="Agent Marketplace", layout="wide")
st.title("Agent Marketplace")

# Use tabs instead of react_flow for simplicity and reliability
tab1, tab2 = st.tabs(["📋 Agents", "📄 Document Summarizer"])

with tab1:
    st.header("Available Agents")
    st.write("Click on the 'Document Summarizer' tab to process documents.")

    # Display a visualization of available agents
    st.markdown(
        """
    ### Available Agents
    
    - **Document Summarizer**: Summarize documents and videos
    
    *More agents coming soon...*
    """
    )

with tab2:
    st.header("Document Summarizer")
    st.write("Upload your document below to generate a summary")

    # File uploader
    uploaded_file = st.file_uploader(
        "Upload a document",
        type=["txt", "pdf", "csv", "mp4", "mov"],
    )

    if uploaded_file:
        st.write(f"Selected file: **{uploaded_file.name}**")
        file_extension = Path(uploaded_file.name).suffix[1:].lower()

        # Process button
        if st.button("▶️ Process Document", use_container_width=True):
            with st.spinner("Processing document..."):
                files = {"file": uploaded_file}
                try:
                    response = requests.post(
                        f"{BACKEND_URL}/api/process_document", files=files
                    )

                    # Debug info
                    st.write(f"Backend URL: {BACKEND_URL}")
                    st.write(f"Response status: {response.status_code}")

                    if response.status_code == 200:
                        st.success("✅ Processing complete!")
                        result = response.json()

                        if "summary" in result:
                            st.markdown("## Summary Results")
                            st.write(result["summary"])

                            # Download button
                            st.download_button(
                                "⬇️ Download Summary",
                                result["summary"],
                                f"{Path(uploaded_file.name).stem}_summary.txt",
                                mime="text/plain",
                            )
                        else:
                            st.success(
                                "Document processed! Click 'Generate Summary' to continue."
                            )

                            if st.button(
                                "🔄 Generate Summary", use_container_width=True
                            ):
                                with st.spinner("Creating summary..."):
                                    summary_response = requests.post(
                                        f"{BACKEND_URL}/api/summarize",
                                        json={"file_id": uploaded_file.name},
                                    )

                                    if summary_response.status_code == 200:
                                        summary = summary_response.json()["summary"]
                                        st.markdown("## Summary Results")
                                        st.write(summary)

                                        st.download_button(
                                            "⬇️ Download Summary",
                                            summary,
                                            f"{Path(uploaded_file.name).stem}_summary.txt",
                                            mime="text/plain",
                                        )
                                    else:
                                        st.error(
                                            f"❌ Error: {summary_response.json().get('error', 'Unknown error')}"
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
        st.info("Please upload a document to get started.")
