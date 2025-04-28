#!/usr/bin/env python3
"""
run_pipeline.py

Generic CLI for PPT → PDF → images → OCR text → LLM summary.
Supports two providers:
  - openai      (requires OPENAI_API_KEY)
  - gemini      (requires GEMINI_API_KEY, defaults to Gemini 2.5 Flash Preview)

Usage:
    python run_pipeline.py <deck.pptx> <work_dir> [provider]

Examples:
    python run_pipeline.py slides.pptx output openai
    python run_pipeline.py slides.pptx output gemini

Environment variables:
    OPENAI_API_KEY     -- API key for OpenAI (GPT-3.5-turbo)
    GEMINI_API_KEY     -- API key for Google Gemini
    GEMINI_MODEL       -- Gemini model (default: models/gemini-2.5-flash-preview-04-17)
"""
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

# Load environment variables
def load_keys():
    load_dotenv()
    openai.api_key = os.getenv("OPENAI_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")
    gemini_model = os.getenv("GEMINI_MODEL", "models/gemini-2.5-flash-preview-04-17")
    return gemini_key, gemini_model

# Conversion functions

def pptx_to_pdf(pptx_path: Path, out_dir: Path) -> Path:
    """Convert PPTX to PDF using LibreOffice headless."""
    out_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        "soffice","--headless","--convert-to","pdf",
        "--outdir", str(out_dir), str(pptx_path)
    ], check=True)
    return out_dir / pptx_path.with_suffix('.pdf').name


def pdf_to_images(pdf_path: Path, out_dir: Path) -> list[Path]:
    """Rasterize each PDF page to a PNG image."""
    out_dir.mkdir(parents=True, exist_ok=True)
    pil_images = convert_from_path(
        str(pdf_path), dpi=200, output_folder=str(out_dir), fmt="png"
    )
    return [Path(img.filename) for img in pil_images]

# OCR extraction
def extract_text(image_path: Path) -> str:
    """Use Tesseract OCR to extract text from a slide image."""
    img = Image.open(image_path)
    return pytesseract.image_to_string(img).strip()

# Summarization providers
def summarize_openai(raw_text: str) -> str:
    """Summarize extracted text via OpenAI GPT-3.5-Turbo."""
    if not raw_text:
        return "[No text detected]"
    prompt = (
        "Below is OCR-extracted text from a slide. "
        "Provide a concise 2-3 sentence summary focusing on key points:\n\n" + raw_text
    )
    resp = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role":"user","content":prompt}]
    )
    return resp.choices[0].message.content.strip()


def summarize_gemini(raw_text: str, api_key: str, model: str) -> str:
    """Summarize extracted text via Google Gemini API."""
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set")
    
    # Configure the Gemini API with the provided key
    genai.configure(api_key=api_key)
    
    if not raw_text:
        return "[No text detected]"
    
    # Create the model
    model_instance = genai.GenerativeModel(model)
    
    prompt = (
        "Below is OCR-extracted text from a slide. "
        "Provide a concise 2-3 sentence summary focusing on key points:\n\n" + raw_text
    )
    
    # Generate the response using the proper method
    response = model_instance.generate_content(prompt)
    
    # Extract the text from the response
    return response.text.strip()

# Main pipeline

def process_deck(deck_path: str, work_dir: str, provider: str):
    base = Path(work_dir)
    # 1) PPTX → PDF
    pdf_dir = base / 'pdf'
    pdf_file = pptx_to_pdf(Path(deck_path), pdf_dir)
    
    # 2) PDF → images
    img_dir = base / 'images'
    slides = pdf_to_images(pdf_file, img_dir)

    # 3) OCR & summarization
    gemini_key, gemini_model = load_keys()
    for idx, slide_img in enumerate(sorted(slides), start=1):
        text = extract_text(slide_img)
        try:
            if provider.lower() == 'gemini':
                summary = summarize_gemini(text, gemini_key, gemini_model)
            else:
                summary = summarize_openai(text)
        except RateLimitError:
            time.sleep(5)
            summary = summarize_openai(text) if provider!='gemini' else summarize_gemini(text, gemini_key, gemini_model)
        except Exception as e:
            print(f"Error processing slide {idx}: {e}")
            summary = "[Error processing slide]"

        print(f"--- Slide {idx} ---\n{summary}\n")
        time.sleep(1)

# CLI entry-point

if __name__ == '__main__':
    if len(sys.argv) < 3 or len(sys.argv) > 4:
        print("Usage: python run_pipeline.py <deck.pptx> <work_dir> [openai|gemini]")
        sys.exit(1)
    deck_file = sys.argv[1]
    out_dir = sys.argv[2]
    prov = sys.argv[3] if len(sys.argv)==4 else 'openai'
    process_deck(deck_file, out_dir, prov)