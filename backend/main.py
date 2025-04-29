from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import tempfile
import os
from pathlib import Path
import json
from typing import List, Dict
import uvicorn

from pipeline import process_deck

app = FastAPI(title="Slide Summarizer API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your Vercel frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/summarize")
async def summarize_slides(
    file: UploadFile = File(...),
    provider: str = Form(...),
    style: str = Form(...),
    openai_key: str = Form(None),
    gemini_key: str = Form(None)
):
    try:
        # Validate API keys based on provider
        if provider == "openai" and not openai_key:
            raise HTTPException(status_code=400, detail="OpenAI API key is required")
        if provider == "gemini" and not gemini_key:
            raise HTTPException(status_code=400, detail="Gemini API key is required")

        # Create a temporary directory for processing
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Save uploaded file
            file_path = temp_path / file.filename
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            
            # Process the deck with user-provided API keys
            results = process_deck(
                deck_path=str(file_path),
                work_dir=str(temp_path),
                provider=provider,
                style=style,
                openai_key=openai_key,
                gemini_key=gemini_key
            )
            
            return JSONResponse(content=results)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 