import streamlit as st
import requests
import tempfile
import json
from pathlib import Path
import base64
from PIL import Image
import io

# Page configuration
st.set_page_config(
    page_title="Slide Summarizer",
    page_icon="📑",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }
    .subheader {
        color: #888888;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }
    .slide-container {
        border: 1px solid #e6e6e6;
        border-radius: 10px;
        padding: 0.1rem;
        margin-bottom: 1rem;
        background-color: #f9f9f9;
    }
    .slide-header {
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .api-key-warning {
        color: #ff4b4b;
        font-size: 0.9rem;
        margin-top: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Constants
BACKEND_URL = st.secrets.get("BACKEND_URL", "http://localhost:8000")  # Will be set in Vercel environment

def main():
    st.title("📑 Slide Summarizer")
    st.markdown("""
    Upload your PowerPoint presentation and get AI-powered summaries for each slide.
    Choose between OpenAI's GPT-3.5-Turbo or Google's Gemini for summarization.
    """)

    # Sidebar configuration
    with st.sidebar:
        st.header("Configuration")
        provider = st.radio(
            "AI Provider",
            ["openai", "gemini"],
            format_func=lambda x: "OpenAI GPT" if x == "openai" else "Google Gemini"
        )
        style = st.selectbox(
            "Summary Style",
            ["concise", "detailed", "bullet-points"],
            format_func=lambda x: x.title().replace("-", " ")
        )
        
        # API Key inputs
        st.subheader("API Keys")
        st.markdown('<p class="api-key-warning">⚠️ Your API keys are only used for this session and are not stored.</p>', unsafe_allow_html=True)
        
        if provider == "openai":
            openai_key = st.text_input("OpenAI API Key", type="password", help="Get your key from https://platform.openai.com/api-keys")
            gemini_key = None
        else:
            gemini_key = st.text_input("Google Gemini API Key", type="password", help="Get your key from https://makersuite.google.com/app/apikey")
            openai_key = None

    # File upload
    uploaded_file = st.file_uploader(
        "Upload PowerPoint File",
        type=["ppt", "pptx"],
        help="Upload a PowerPoint file to summarize"
    )

    if uploaded_file is not None:
        # Validate API key is provided
        if (provider == "openai" and not openai_key) or (provider == "gemini" and not gemini_key):
            st.error("Please provide your API key in the sidebar to continue.")
            return

        if st.button("🚀 Summarize Slides"):
            with st.spinner("Processing your presentation..."):
                try:
                    # Prepare the file for upload
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
                    data = {
                        "provider": provider,
                        "style": style,
                        "openai_key": openai_key,
                        "gemini_key": gemini_key
                    }

                    # Make API request to backend
                    response = requests.post(
                        f"{BACKEND_URL}/summarize",
                        files=files,
                        data=data
                    )
                    
                    if response.status_code == 200:
                        results = response.json()
                        
                        # Display results
                        for slide in results:
                            with st.container():
                                st.markdown(f"### Slide {slide['slide_number']}")
                                col1, col2 = st.columns([1, 2])
                                
                                with col1:
                                    # Display slide thumbnail
                                    if slide.get('thumbnail'):
                                        st.image(slide['thumbnail'])
                                
                                with col2:
                                    # Display summary
                                    st.markdown(slide['summary'])
                                    
                        # Download button
                        st.download_button(
                            label="📥 Download All Summaries",
                            data=json.dumps(results, indent=2),
                            file_name="slide_summaries.json",
                            mime="application/json"
                        )
                    else:
                        st.error(f"Error: {response.text}")
                        
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main() 