import os
import sys
import time
import subprocess
from pathlib import Path
from dotenv import load_dotenv

from pdf2image import convert_from_path
from PIL import Image
import pytesseract

import openai
import google.generativeai as genai
from openai.error import RateLimitError

def process_deck(deck_path: str, work_dir: str, provider: str, style: str, openai_key: str = None, gemini_key: str = None):
    """Process a PowerPoint deck and return summaries."""
    work_path = Path(work_dir)
    deck_path = Path(deck_path)
    
    # Convert PPT to PDF
    pdf_path = pptx_to_pdf(deck_path, work_path)
    
    # Convert PDF to images
    image_paths = pdf_to_images(pdf_path, work_path)
    
    results = []
    for i, image_path in enumerate(image_paths, 1):
        # Extract text from image
        text = extract_text(image_path)
        
        # Generate summary based on provider
        if provider == "openai":
            summary = summarize_openai(text, openai_key, style)
        else:
            summary = summarize_gemini(text, gemini_key, style)
        
        # Add result
        results.append({
            "slide_number": i,
            "summary": summary,
            "thumbnail": str(image_path)
        })
    
    return results

def pptx_to_pdf(pptx_path: Path, out_dir: Path) -> Path:
    """Convert PPTX to PDF using LibreOffice headless."""
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = out_dir / f"{pptx_path.stem}.pdf"
    
    subprocess.run([
        "soffice",
        "--headless",
        "--convert-to", "pdf",
        "--outdir", str(out_dir),
        str(pptx_path)
    ], check=True)
    
    return pdf_path

def pdf_to_images(pdf_path: Path, out_dir: Path) -> list[Path]:
    """Convert PDF to images."""
    images = convert_from_path(pdf_path)
    image_paths = []
    
    for i, image in enumerate(images):
        image_path = out_dir / f"slide_{i+1}.png"
        image.save(image_path, "PNG")
        image_paths.append(image_path)
    
    return image_paths

def extract_text(image_path: Path) -> str:
    """Extract text from image using Tesseract OCR."""
    return pytesseract.image_to_string(Image.open(image_path))

def summarize_openai(raw_text: str, api_key: str, style: str) -> str:
    """Generate summary using OpenAI."""
    openai.api_key = api_key
    
    prompt = f"""
    Please summarize the following text in a {style} style:
    
    {raw_text}
    """
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes text."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except RateLimitError:
        time.sleep(1)  # Wait before retrying
        return summarize_openai(raw_text, api_key, style)

def summarize_gemini(raw_text: str, api_key: str, style: str) -> str:
    """Generate summary using Google Gemini."""
    genai.configure(api_key=api_key)
    
    prompt = f"""
    Please summarize the following text in a {style} style:
    
    {raw_text}
    """
    
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(prompt)
    return response.text 