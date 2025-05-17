import openai
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import time
import os
import re

# === CONFIGURATION ===
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or "sk-..."
MODEL = "gpt-4o"
ARTICLES_FILE = "articles.txt"
OUTPUT_CLOZE_FILE = "anki_cloze_cards.txt"
OUTPUT_BASIC_FILE = "anki_basic_cards.txt"
CARDS_PER_ARTICLE = 20

from openai import OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

def fetch_article_text(url):
    print(f"Fetching: {url}")
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # Strip scripts and styles
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        text = ' '.join(soup.stripped_strings)
        return text[:12000], soup.title.string.strip() if soup.title else url
    except Exception as e:
        print(f"Error fetching article: {e}")
        return "", url

def generate_anki_cards(article_text, url, title):
    prompt = f"""
You're a spaced repetition tutor. Given the following article content from {url}, extract up to {CARDS_PER_ARTICLE} high-quality Anki flashcards.
Focus on the most important concepts, definitions, and facts. Don't include any extraneous information or examples.

1. Generate many cloze deletions per sentence such that there is one around every 7-10 words. Use the format: {{c(cloze number)::text}}
2. Also generate a small number of normal front-back cards.
3. Separate the two types clearly in your response: label one section "CLOZE" and the other "BASIC"
4. Use semicolons (`;`) to separate fields in each card.
5. Include the article title as the third field for every card.

Only output formatted cards in plain text:
- Cloze: `[text with cloze deletions] ; [leave blank] ; [title]`
- Basic: `Front ; Back ; [title]`

Article Content:
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You generate high-quality Anki cards from articles."},
            {"role": "user", "content": prompt + article_text}
        ],
        temperature=0.7,
    )

    return response.choices[0].message.content.strip()

def split_cards(generated_text):
    cloze_cards = []
    basic_cards = []
    current_section = None

    for line in generated_text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.upper().startswith("CLOZE"):
            current_section = "cloze"
            continue
        elif line.upper().startswith("BASIC"):
            current_section = "basic"
            continue

        if current_section == "cloze":
            cloze_cards.append(line)
        elif current_section == "basic":
            basic_cards.append(line)

    return cloze_cards, basic_cards

def main():
    if not OPENAI_API_KEY or OPENAI_API_KEY.startswith("sk-..."):
        raise ValueError("Set your OpenAI API key in the OPENAI_API_KEY variable or as an environment variable.")

    with open(ARTICLES_FILE) as f:
        urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    all_cloze = []
    all_basic = []

    for url in urls:
        article_text, title = fetch_article_text(url)
        if not article_text:
            continue
        raw_output = generate_anki_cards(article_text, url, title)
        cloze_cards, basic_cards = split_cards(raw_output)
        all_cloze.extend(cloze_cards)
        all_basic.extend(basic_cards)
        time.sleep(1)  # polite rate limit

    with open(OUTPUT_CLOZE_FILE, "w") as f:
        f.write("\n".join(all_cloze))

    with open(OUTPUT_BASIC_FILE, "w") as f:
        f.write("\n".join(all_basic))

    print(f"\nDone. {len(all_cloze)} cloze cards and {len(all_basic)} basic cards saved to {OUTPUT_CLOZE_FILE} and {OUTPUT_BASIC_FILE}.")

if __name__ == "__main__":
    main()
