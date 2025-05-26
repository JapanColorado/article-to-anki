import os
import json
from openai import OpenAI

ANKICONNECT_URL = "http://localhost:8765"
CLOZE_MODEL_NAME = "Cloze-Articles-to-Anki"
BASIC_MODEL_NAME = "Basic-Articles-to-Anki"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = "gpt-4.1-mini"

ARTICLE_DIR = "articles"
URLS_FILE = f"{ARTICLE_DIR}/urls.txt"
ALLOWED_EXTENSIONS = {".pdf", ".xps", ".epub", ".mobi", ".fb2", ".cbz", ".svg", ".txt", ".md", ".docx", ".doc", ".pptx", ".ppt"}
PROCESSED_ARTICLES_FILE = ".processed_articles.json"
CARD_DATABASE_FILE = ".card_database.json"

# Default similarity threshold for considering cards as duplicates (0.0 to 1.0)
# Higher values = stricter duplicate detection (require more similarity)
# Lower values = more lenient duplicate detection (accept more variations as duplicates)
SIMILARITY_THRESHOLD = 0.85

client = OpenAI(api_key=OPENAI_API_KEY)

def get_processed_articles():
    """
    Returns a dictionary of processed articles with their timestamps and hashes.
    
    Returns:
        dict: A dictionary with article identifiers (URLs or filenames) as keys,
              and dictionaries containing 'timestamp', 'title', and 'hash' as values.
    """
    if os.path.exists(PROCESSED_ARTICLES_FILE):
        try:
            with open(PROCESSED_ARTICLES_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            print(f"Error reading {PROCESSED_ARTICLES_FILE}, creating a new one.")
    return {}

def get_card_database():
    """
    Returns the database of previously created cards with their content and metadata.
    
    Returns:
        dict: A dictionary with card IDs as keys and card data as values.
    """
    if os.path.exists(CARD_DATABASE_FILE):
        try:
            with open(CARD_DATABASE_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            print(f"Error reading {CARD_DATABASE_FILE}, creating a new one.")
    return {"cards": [], "metadata": {"version": 1, "last_updated": ""}}

def save_processed_articles(processed_articles):
    """
    Saves the processed articles dictionary to the PROCESSED_ARTICLES_FILE.
    
    Args:
        processed_articles (dict): Dictionary of processed articles.
    """
    try:
        with open(PROCESSED_ARTICLES_FILE, 'w') as f:
            json.dump(processed_articles, f, indent=2)
    except IOError as e:
        print(f"Error saving {PROCESSED_ARTICLES_FILE}: {e}")
        
def save_card_database(card_database):
    """
    Saves the card database to the CARD_DATABASE_FILE.
    
    Args:
        card_database (dict): Dictionary containing cards and metadata.
    """
    # Update last_updated timestamp
    from datetime import datetime
    card_database["metadata"]["last_updated"] = datetime.now().isoformat()
    
    try:
        with open(CARD_DATABASE_FILE, 'w') as f:
            json.dump(card_database, f, indent=2)
    except IOError as e:
        print(f"Error saving {CARD_DATABASE_FILE}: {e}")
