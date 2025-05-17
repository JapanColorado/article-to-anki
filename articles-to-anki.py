import openai
from openai import OpenAI
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


client = OpenAI(api_key=OPENAI_API_KEY)


def fetch_article_text(url):
    print(f"Fetching: {url}")
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # Strip scripts and styles
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        text = " ".join(soup.stripped_strings)
        return text[:12000], soup.title.string.strip() if soup.title else url
    except Exception as e:
        print(f"Error fetching article: {e}")
        return "", url


def generate_anki_cards(article_text, url, title):
    prompt = """
You're a spaced repetition tutor creating Anki flashcards from a rationalist article.

Your task is to extract two types of flashcards:

Cloze Cards
- Identify the **main argument** of the article and its **key supporting claims**.
- Rewrite or summarize these into clear, assertive sentences.
- Turn these into cloze deletions targeting key concepts, terms, causes, or distinctions.
- Use multiple clozes per sentence if needed (e.g., {{c1::term}} and {{c2::contrast}}).
- Do **not** include illustrative examples, metaphors, quotes, or trivia — only the core structure of the article's reasoning.
- Be concise and precise: each cloze should be 1–5 words and essential for understanding the idea.

Basic Cards
- Extract **definitions, key terms, distinctions, or clear cause-effect relationships**.
- Format as simple front–back cards.
- Prioritize concepts the author defines or builds on.
- Avoid filler, vague rephrasings, or trivia.

Output Format
- Begin with the line CLOZE, then list the cloze cards.
- Then write BASIC, and list the basic cards.
- Format each card with semicolons:
  - Cloze: `{{c1::clozed phrase}} ; ; [article title]`
  - Basic: `Question ; Answer ; [article title]`
- Only output formatted cards. No explanations or summaries.


Article Content:
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": "You generate high-quality Anki cards from articles.",
            },
            {"role": "user", "content": prompt + article_text},
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
        if line[0] == "-":
            line = line[1:].strip()
        if not line:
            continue
        if line.upper().startswith("CLOZE"):
            current_section = "cloze"
            continue
        if line.upper().startswith("BASIC"):
            current_section = "basic"
            continue

        if current_section == "cloze":
            if line[0] == "-":
                line = line[1:].strip()
            cloze_cards.append(line)
        elif current_section == "basic":
            basic_cards.append(line)

    return cloze_cards, basic_cards


def main():
    if not OPENAI_API_KEY or OPENAI_API_KEY.startswith("sk-..."):
        raise ValueError(
            "Set your OpenAI API key in the OPENAI_API_KEY variable or as an environment variable."
        )

    with open(ARTICLES_FILE, encoding="utf-8") as f:
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

    with open(OUTPUT_CLOZE_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(all_cloze))

    with open(OUTPUT_BASIC_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(all_basic))

    print(
        f"Done. {len(all_cloze)} cloze cards and {len(all_basic)} basic cards saved to {OUTPUT_CLOZE_FILE} and {OUTPUT_BASIC_FILE}."
    )


if __name__ == "__main__":
    main()
