from fastapi import FastAPI, Request, Form, File, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import requests
import os
from pathlib import Path

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