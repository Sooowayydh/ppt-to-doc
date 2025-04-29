from fastapi import FastAPI, Request, Form, File, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import requests
import os
from pathlib import Path
import shutil
from typing import Optional

app = FastAPI(title="Slide Summarizer")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Get backend URL from environment variable
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/summarize")
async def summarize(
    request: Request,
    file: UploadFile = File(...),
    provider: str = Form(...),
    style: str = Form(...),
    openai_key: str = Form(None),
    gemini_key: str = Form(None)
):
    try:
        # Prepare the file for upload
        files = {"file": (file.filename, await file.read())}
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
            return templates.TemplateResponse(
                "results.html",
                {
                    "request": request,
                    "results": results
                }
            )
        else:
            return templates.TemplateResponse(
                "error.html",
                {
                    "request": request,
                    "error": response.text
                }
            )
            
    except Exception as e:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error": str(e)
            }
        )

@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    output_format: str = Form(...),
    custom_prompt: Optional[str] = Form(None)
):
    # Create uploads directory if it doesn't exist
    upload_dir = Path("uploads")
    upload_dir.mkdir(exist_ok=True)
    
    # Save the uploaded file
    file_path = upload_dir / file.filename
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Process the file (placeholder for actual processing)
    # TODO: Implement file processing logic
    
    return {"message": "File uploaded successfully", "filename": file.filename} 