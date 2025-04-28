# pipeline/process_with_openai.py
"""
Minimal PPTX → PDF → images → OCR-based text extraction + OpenAI summarization.

Prerequisites:
  - LibreOffice (headless)
  - Poppler (pdf2image)
  - Tesseract OCR (for text extraction)
  - Python packages: Pillow, pdf2image, pytesseract, openai, python-dotenv
"""

import os
import subprocess
import sys
import time
from pathlib import Path
from pdf2image import convert_from_path
from dotenv import load_dotenv
import openai
from PIL import Image
import pytesseract

# Load OpenAI API key
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Throttle settings to respect token limits
MIN_INTERVAL = 2  # seconds between API calls


def pptx_to_pdf(pptx_path: Path, out_dir: Path) -> Path:
    """Convert PPTX to PDF using LibreOffice headless."""
    out_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        "soffice",
        "--headless",
        "--convert-to", "pdf",
        "--outdir", str(out_dir),
        str(pptx_path)
    ], check=True)
    pdf_name = pptx_path.with_suffix(".pdf").name
    return out_dir / pdf_name


def pdf_to_images(pdf_path: Path, out_dir: Path) -> list[Path]:
    """Convert each PDF page to a PNG image."""
    out_dir.mkdir(parents=True, exist_ok=True)
    images = convert_from_path(
        str(pdf_path), dpi=200, output_folder=str(out_dir), fmt="png"
    )
    return [Path(img.filename) for img in images]


def extract_text(image_path: Path) -> str:
    """Use Tesseract OCR to extract raw text from an image."""
    img = Image.open(image_path)
    text = pytesseract.image_to_string(img)
    return text.strip()


def summarize_text(raw_text: str) -> str:
    """Send extracted text to OpenAI for a concise summary."""
    if not raw_text:
        return "[No extractable text found on this slide.]"

    prompt = (
        "Below is the raw text extracted from a presentation slide. "
        "Please provide a concise summary in 2-3 sentences, focusing on key points:\n\n" + raw_text
    )
    resp = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return resp.choices[0].message.content.strip()


def process_deck(pptx_file: str, work_dir: str):
    """Full pipeline: PPTX → PDF → images → OCR → summarization."""
    base = Path(work_dir)

    # 1. Convert PPTX to PDF
    pdf_dir = base / "pdf"
    pdf = pptx_to_pdf(Path(pptx_file), pdf_dir)

    # 2. Convert PDF to images
    img_dir = base / "images"
    images = pdf_to_images(pdf, img_dir)

    # 3. OCR and summarize
    for idx, img_path in enumerate(sorted(images), start=1):
        raw_text = extract_text(img_path)
        summary = summarize_text(raw_text)
        print(f"--- Slide {idx} ---\n{summary}\n")
        time.sleep(MIN_INTERVAL)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python process_with_openai.py <deck.pptx> <work_dir>")
        sys.exit(1)
    process_deck(sys.argv[1], sys.argv[2])
