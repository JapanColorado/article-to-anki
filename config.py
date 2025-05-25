import os
from openai import OpenAI

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANKICONNECT_URL = "http://localhost:8765"
MODEL = "gpt-4.1-mini"
ARTICLE_DIR = "articles"
URLS_FILE = f"{ARTICLE_DIR}/urls.txt"
ALLOWED_EXTENSIONS = {".pdf", ".xps", ".epub", ".mobi", ".fb2", ".cbz", ".svg", ".txt", ".md", ".docx", ".doc", ".pptx", ".ppt"}

client = OpenAI(api_key=OPENAI_API_KEY)
