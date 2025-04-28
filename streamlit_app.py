import streamlit as st
import tempfile
import time
from pathlib import Path
import base64
from PIL import Image
import io

# Import pipeline functions
from run_pipeline import (
    pptx_to_pdf,
    pdf_to_images,
    extract_text,
    summarize_openai,
    summarize_gemini,
    load_keys,
)

# Page configuration with favicon and custom theme
st.set_page_config(
    page_title="Slide Summarizer",
    page_icon="📑",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for better styling
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
    .provider-radio {
        background-color: #f0f2f6;
        padding: 0.1rem;
        border-radius: 5px;
        margin-bottom: 20px;
    }
    .stProgress > div > div > div > div {
        background-color: #4CAF50;
    }
    .upload-section {
        background-color: #f0f7ff;
        
        padding: 0.1rem;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .api-section {
        background-color: #fff8f0;
        padding: 0.1rem;
        border-radius: 10px;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='main-header'>📑 Slide Summarizer</div>", unsafe_allow_html=True)
st.markdown("<div class='subheader'>Transform your presentations into concise summaries</div>", unsafe_allow_html=True)

# Create two columns for the main layout
left_col, right_col = st.columns([3, 2])

with right_col:
    st.markdown("### Settings")
    
    # API Provider selection with nice radio buttons and icons
    st.markdown("<div class='provider-radio'>", unsafe_allow_html=True)
    provider = st.radio(
        "Select AI Provider",
        options=["openai", "gemini"],
        format_func=lambda x: "OpenAI GPT" if x == "openai" else "Google Gemini",
        horizontal=True,
        index=0
    )
    st.markdown("</div>", unsafe_allow_html=True)
    
    # API Keys with collapsible sections
    with st.expander("🔑 API Keys (Required)"):
        st.markdown("<div class='api-section'>", unsafe_allow_html=True)
        openai_key_input = st.text_input(
            "OpenAI API Key", 
            type="password", 
            help="Overrides OPENAI_API_KEY env var",
            disabled=provider != "openai"
        )
        gemini_key_input = st.text_input(
            "Gemini API Key", 
            type="password", 
            help="Overrides GEMINI_API_KEY env var",
            disabled=provider != "gemini"
        )
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Advanced options
    with st.expander("⚙️ Advanced Options"):
        st.slider("Slide Processing Delay (seconds)", 0.0, 5.0, 1.0, 0.1, key="delay")
        
        if provider == "gemini":
            gemini_default = "models/gemini-2.5-flash-preview-04-17"
            gemini_model_input = st.text_input(
                "Gemini Model", 
                value=gemini_default,
                help="Model identifier for Gemini API"
            )
        
        # Summary style options
        summary_style = st.selectbox(
            "Summary Style",
            ["Concise", "Detailed", "Bullet Points"],
            index=0
        )

with left_col:
    # File upload section with visual styling
    st.markdown("<div class='upload-section'>", unsafe_allow_html=True)
    st.markdown("### Upload Presentation")
    uploaded_file = st.file_uploader(
        "Choose a PowerPoint file (.ppt or .pptx)",
        type=["ppt", "pptx"],
        help="Your file will be processed securely and not stored permanently"
    )
    
    # Show file details when uploaded
    if uploaded_file:
        file_details = {
            "Filename": uploaded_file.name,
            "File size": f"{uploaded_file.size / 1024:.1f} KB"
        }
        
        st.write("File Information:")
        for key, value in file_details.items():
            st.write(f"- {key}: {value}")
            
        valid_api_key = False
        if provider == "openai" and openai_key_input:
            valid_api_key = True
        elif provider == "gemini" and gemini_key_input:
            valid_api_key = True

        if valid_api_key:
            process_button = st.button("🚀 Summarize Slides", type="primary", use_container_width=True)
        else:
            st.warning(f"Please provide a {'OpenAI' if provider == 'openai' else 'Gemini'} API key in the Settings panel.")
            process_button = st.button("🚀 Summarize Slides", type="primary", use_container_width=True, disabled=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Results area - will be populated after processing
    if uploaded_file and 'results' not in st.session_state:
        st.markdown("### Results will appear here")
    
    # Main processing logic
    if uploaded_file and 'process_button' in locals() and process_button:
        # Initialize progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Create temp working directory
        with tempfile.TemporaryDirectory() as tmpdir:
            work_dir = Path(tmpdir)
            ppt_path = work_dir / uploaded_file.name
            
            # Save uploaded PPTX
            status_text.text("Saving uploaded file...")
            with open(ppt_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            progress_bar.progress(10)
            
            # Load keys (possibly overridden)
            status_text.text("Loading API credentials...")
            # Only use user-provided keys, not environment variables
            if provider == "openai":
                import openai
                openai.api_key = openai_key_input
                gemini_key = None
                gemini_model = "models/gemini-2.5-flash-preview-04-17"
            else:  # provider == "gemini"
                import google.generativeai as genai
                genai.configure(api_key=gemini_key_input)
                gemini_key = gemini_key_input
                gemini_model = gemini_model_input if 'gemini_model_input' in locals() else "models/gemini-2.5-flash-preview-04-17"
            progress_bar.progress(20)
            
            # Convert to PDF
            status_text.text("Converting PowerPoint to PDF...")
            pdf_dir = work_dir / "pdf"
            pdf_file = pptx_to_pdf(ppt_path, pdf_dir)
            progress_bar.progress(30)
            
            # Convert PDF to images
            status_text.text("Extracting slide images...")
            img_dir = work_dir / "images"
            slides = pdf_to_images(pdf_file, img_dir)
            progress_bar.progress(40)
            
            # Setting up for processing
            total_slides = len(slides)
            status_text.text(f"Processing {total_slides} slides...")
            
            # Store results in session state
            st.session_state.results = []
            st.session_state.images = []
            
            # Process each slide
            for idx, slide_img in enumerate(sorted(slides), start=1):
                current_progress = 40 + (idx / total_slides * 50)
                progress_bar.progress(int(current_progress))
                status_text.text(f"Processing slide {idx}/{total_slides}...")
                
                # Extract text and image
                raw_text = extract_text(slide_img)
                
                # Get summary based on provider and style
                try:
                    # Adjust prompt based on style
                    summary_prompt = raw_text
                    if summary_style == "Concise":
                        summary_instruction = "Provide a concise 2-3 sentence summary focusing on key points"
                    elif summary_style == "Detailed":
                        summary_instruction = "Provide a detailed paragraph summarizing all important information"
                    else:  # Bullet Points
                        summary_instruction = "Provide a summary as 3-5 bullet points of the key takeaways"
                    
                    # Get summary
                    if provider == "gemini":
                        if 'gemini_model_input' in locals():
                            gemini_model = gemini_model_input
                        summary = summarize_gemini(raw_text, gemini_key, gemini_model)
                    else:
                        summary = summarize_openai(raw_text)
                    
                    # Save thumbnail of the slide
                    img = Image.open(slide_img)
                    img_thumb = img.copy()
                    img_thumb.thumbnail((800, 600))
                    buffered = io.BytesIO()
                    img_thumb.save(buffered, format="PNG")
                    img_str = base64.b64encode(buffered.getvalue()).decode()
                    
                    # Store results
                    st.session_state.results.append({
                        "slide_num": idx,
                        "summary": summary,
                        "raw_text": raw_text
                    })
                    st.session_state.images.append(img_str)
                    
                except Exception as e:
                    st.error(f"Error processing slide {idx}: {str(e)}")
                    st.session_state.results.append({
                        "slide_num": idx,
                        "summary": f"Error: {str(e)}",
                        "raw_text": raw_text if 'raw_text' in locals() else "Text extraction failed"
                    })
                    st.session_state.images.append(None)
                
                # Add delay between API calls
                time.sleep(st.session_state.delay)
            
            # Complete progress
            progress_bar.progress(100)
            status_text.text("Processing complete!")
            time.sleep(0.5)
            status_text.empty()
            progress_bar.empty()
            
            # Trigger page refresh to show results
            st.rerun()

# Display results if available
if 'results' in st.session_state and len(st.session_state.results) > 0:
    st.markdown("## Slide Summaries")
    
    # Add download button for all summaries
    all_summaries = "\n\n".join([
        f"# Slide {r['slide_num']}\n{r['summary']}" 
        for r in st.session_state.results
    ])
    
    st.download_button(
        label="📥 Download All Summaries",
        data=all_summaries,
        file_name=f"slide_summaries_{time.strftime('%Y%m%d-%H%M%S')}.md",
        mime="text/markdown",
    )
    
    # Display each slide with its summary
    for i, result in enumerate(st.session_state.results):
        st.markdown(f"<div class='slide-container'>", unsafe_allow_html=True)
        
        # Create columns for image and text
        img_col, text_col = st.columns([1, 2])
        
        with img_col:
            if st.session_state.images[i]:
                st.markdown(f"<img src='data:image/png;base64,{st.session_state.images[i]}' width='100%'>", unsafe_allow_html=True)
            else:
                st.markdown("*Image not available*")
        
        with text_col:
            st.markdown(f"<div class='slide-header'>Slide {result['slide_num']}</div>", unsafe_allow_html=True)
            st.markdown(result['summary'])
            
            # Expandable raw text
            with st.expander("Show extracted text"):
                st.text(result['raw_text'])
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Add option to clear results and start over
    if st.button("Clear Results & Start Over"):
        del st.session_state.results
        del st.session_state.images
        st.rerun()

# Footer
st.markdown("---")
st.markdown(
    "Built with Streamlit • Processing powered by " + 
    ("OpenAI GPT" if provider == "openai" else "Google Gemini")
)