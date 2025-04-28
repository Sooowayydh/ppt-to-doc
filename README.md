```markdown
# 📑 Slide Summarizer

A simple Streamlit app that transforms PowerPoint decks into concise, human-readable summaries slide by slide. You can choose between OpenAI’s GPT-3.5-Turbo or Google Gemini 2.5 Flash Preview as the summarization engine, and tweak summary style and processing delay to suit your needs.

---

## 🚀 Features

- **Drag-and-drop PPT/PPTX upload** in a polished UI  
- **Two LLM backends**:
  - **OpenAI** (GPT-3.5-Turbo)  
  - **Google Gemini** (2.5 Flash Preview)  
- **OCR extraction** via Tesseract to pull raw text from slide images  
- **Customizable summary style**: Concise, Detailed, or Bullet-points  
- **Adjustable processing delay** to respect provider rate limits  
- **Per-slide thumbnails** alongside your summaries  
- **Downloadable Markdown** of all slide summaries  
- **Theming & styling** with custom CSS for a modern look  

---

## 🔧 Prerequisites

1. **System tools**  
   - [LibreOffice](https://www.libreoffice.org/) (headless)
   - [Poppler](https://poppler.freedesktop.org/) (for `pdf2image`)
   - [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)

2. **Python >= 3.9**  
3. **Python packages** (install with `pip`):
   ```bash
   pip install --upgrade pip
   pip install \
     streamlit \
     pdf2image \
     pillow \
     pytesseract \
     openai==0.28.0 \
     google-generativeai \
     python-dotenv
   ```

---

## ⚙️ Environment Variables

Create a `.env` file at the project root with your keys:

```dotenv
OPENAI_API_KEY=sk-…your_openai_key…
GEMINI_API_KEY=ya29.…your_google_token…
# (optional) override the default Gemini model:
GEMINI_MODEL=models/gemini-2.5-flash-preview-04-17
```

> **Note**:  
> - OpenAI summarization uses GPT-3.5-Turbo.  
> - Gemini summarization uses Google Gemini 2.5 Flash Preview by default.

---

## 📂 Project Structure

```
.
├── run_pipeline.py       # Core PPT→PDF→OCR→LLM pipeline
├── streamlit_app.py      # Streamlit front-end
├── requirements.txt      # Python dependencies
├── .env                  # (gitignored) API keys
└── README.md             # You are here!
```

---

## 🎬 Usage

1. **Launch the app**  
   ```bash
   streamlit run streamlit_app.py
   ```
2. **In your browser**  
   - Upload a `.ppt` or `.pptx`  
   - Select “OpenAI GPT” or “Google Gemini”  
   - (Optional) Paste your API key overrides in the sidebar  
   - Choose your summary style & delay  
   - Click **“🚀 Summarize Slides”**

3. **View & download**  
   - Watch per-slide summaries appear with thumbnails  
   - Click “📥 Download All Summaries” to grab a Markdown file  

---

## 🖌️ Customization

- **Theme & CSS**:  
  Tweak the `<style>` block in `streamlit_app.py` for colors, fonts, and layout.  
- **Summary Prompts**:  
  Update the prompt templates in `run_pipeline.py` under `summarize_openai()` and `summarize_gemini()` to refine tone.  
- **Rate Limits**:  
  Adjust the `time.sleep()` delay or add retry logic in `run_pipeline.py` to suit your API plan.


## 📜 License

This project is released under the **MIT License**. See [LICENSE](LICENSE) for details.  
```