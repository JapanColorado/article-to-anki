import argparse
from datetime import datetime
import hashlib
import os
import time
from typing import Tuple, Optional, List

from bs4 import BeautifulSoup
from openai import OpenAI
from readability import Document
import requests

# === CONFIGURATION ===
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANKI_CONNECT_URL = "http://localhost:8765"
MODEL = "gpt-4.1-mini"
ARTICLES_FILE = "articles.txt"

client = OpenAI(api_key=OPENAI_API_KEY)

def fetch_article_text(url: str, use_cache: bool = False) -> Tuple[Optional[str], Optional[str]]:
    """Fetches the article text and title from the given URL using BeautifulSoup.
    Caches the result in a hidden file to avoid redownloading if caching is enabled."""
    if use_cache:
        # Create a cache directory
        cache_dir = ".article_cache"
        os.makedirs(cache_dir, exist_ok=True)
        # Use a hash of the URL as the filename
        url_hash = hashlib.sha256(url.encode("utf-8")).hexdigest()
        cache_path = os.path.join(cache_dir, f"{url_hash}.txt")

        # Check if cached file exists
        if os.path.exists(cache_path):
            with open(cache_path, "r", encoding="utf-8") as f:
                title = f.readline().rstrip("\n")
                text = f.read()
            print(f"Loaded from cache: {url}")
            return text, title

    print(f"Fetching: {url}")
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/113.0.0.0 Safari/537.36"
        )
    }
    try:
        resp = requests.get(
            url,
            headers=headers,
            timeout=15
        )
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch {url}: {e}")
        return None, None

    doc = Document(resp.text)
    title = doc.short_title() or url
    main_html = doc.summary()
    soup = BeautifulSoup(main_html, "html.parser")

    # Remove sections whose id or class contains "comment"
    for c in soup.find_all(
        lambda t: (
            (t.has_attr("id") and "comment" in t["id"].lower())
            or (t.has_attr("class") and any("comment" in x.lower() for x in t["class"]))
        )
    ):
        c.decompose()

    text = soup.get_text(separator="\n", strip=True)
    text = "\n".join(line for line in text.splitlines() if line.strip())

    if use_cache:
        # Save to cache
        with open(cache_path, "w", encoding="utf-8") as f: # type: ignore
            f.write(title + "\n")
            f.write(text)

    return text, title

def generate_anki_cards(
    article_text: str, custom_instructions: Optional[str] = None
) -> str:
    """Generates Anki cards using OpenAI's API."""
    base_prompt = """
You are a spaced repetition tutor creating Anki flashcards from an article the user provides.

Your task is to extract two types of flashcards:

Cloze Cards
- Identify the main argument (central thesis) and key supporting claims (major justifications, logical steps, or contrasts).
- Summarize each claim in a clear, concise sentence. Keep sentences short and direct—no extra clauses or fluff.
- Create cloze deletions targeting key terms, distinctions, or causal claims.
- Use multiple clozes per sentence if helpful (e.g., {{c1::term}} and {{c2::contrast}}).
- Each cloze should be 1–5 words and stand on its own—do not cloze whole phrases or compound ideas.
- Avoid orphaning sentences; ensure each cloze deletion is meaningful and complete.
- Avoid examples, metaphors, quotes, or trivia—focus only on the core reasoning.
- Each cloze deletion should be a complete thought that can stand alone. Try and combine clozes into a single sentence if they are closely related.
- Aim for 2–10 cloze cards. Include more only if necessary for clarity and understanding.
- Avoid vague rephrasings, filler, or incidental facts.
Basic Cards
- Extract definitions, statistics, distinctions, or cause-effect relationships the author defines or builds on.
- Use a simple front–back format: one question, one answer.
- Keep both the question and answer short and direct.
- Avoid vague rephrasings, filler, or incidental facts.
- Aim for 2–10 basic cards. Include more only if the content is clear and important.

Ambiguity Handling
- If the argument is implicit, infer it: Why was this written? What is the author trying to convey?
- If the structure is loose, extract only what is meaningful and intentional.

Output Format
- Begin with the line CLOZE, then list all cloze cards.
- Then write BASIC, and list all basic cards.
- Format each card using semicolons:
  - Cloze: {{c1::clozed phrase}} ; ;
  - Basic: Question ; Answer ;
- Output only the formatted cards. No explanations, preambles, or summaries.
"""
    if custom_instructions:
        prompt = (
            base_prompt
            + "\nThe user provided these additional instructions:\n"
            + custom_instructions.strip()
            + "\n\nArticle Content:\n"
        )
    else:
        prompt = base_prompt + "\nArticle Content:\n"
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
    content = response.choices[0].message.content
    return content.strip() if content else ""


def split_cards(generated_text: str) -> Tuple[List[str], List[str]]:
    """
    Splits the generated text into two lists of Anki cards: one for cloze cards and
        one for basic cards, based on their respective section headers in the text.
    """
    cloze_cards: List[str] = []
    basic_cards: List[str] = []
    current_section: Optional[str] = None
    for line in generated_text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.upper().startswith("CLOZE"):
            current_section = "cloze"
            continue
        if line.upper().startswith("BASIC"):
            current_section = "basic"
            continue
        if current_section == "cloze":
            cloze_cards.append(line)
        elif current_section == "basic":
            basic_cards.append(line)
    return cloze_cards, basic_cards


def add_to_anki(front: str, back: str, title: str, is_cloze: bool, deck: str) -> None:
    """Adds a card to Anki using AnkiConnect. Title gets added as a tag."""
    note = {
        "deckName": deck,
        "modelName": "Basic" if not is_cloze else "Cloze",
        "fields": {"Front": front, "Back": back},
        "tags": ["article->anki", f"{title}"],
    }
    if is_cloze:
        note["fields"]["Text"] = front
    payload = {
        "action": "addNote",
        "version": 6,
        "note": note,
    }
    try:
        response = requests.post(ANKI_CONNECT_URL, json=payload, timeout=15)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Failed to add card: {e}")


def export_to_file(cards: List[str], title: str, is_cloze: bool) -> None:
    """Exports cards to a single file exported_cards.txt, appending new cards at the end.
    Card format is front; back; title;"""
    os.makedirs("exported_cards", exist_ok=True)  # Ensure the directory exists
    timestamp = datetime.now().strftime("%Y%m%d_%H")
    file_path = f"exported_cards/{timestamp}_{'cloze' if is_cloze else 'basic'}_cards.txt"
    with open(file_path, "a", encoding="utf-8") as f:
        for card in cards:
            f.write(f"{card} {title} ;\n")


def main() -> None:
    """Main function to parse arguments and process articles."""
    parser = argparse.ArgumentParser(description="Generate Anki cards from articles.")
    parser.add_argument(
        "--deck", type=str, help="Name of the Anki deck to use", default="Default"
    )
    parser.add_argument(
        "--to-file",
        action="store_true",
        help="Export cards to files instead of AnkiConnect",
        default=False,
    )
    parser.add_argument(
        "--instructions",
        type=str,
        help="Custom instructions for the card generator",
        default=None,
    )
    parser.add_argument(
        "--cache",
        action="store_true",
        help="Enable caching of fetched articles",
        default=False,
    )
    args = parser.parse_args()

    if not OPENAI_API_KEY or OPENAI_API_KEY.startswith("sk-..."):
        raise ValueError(
            "Set your OpenAI API key in the OPENAI_API_KEY variable or as an environment variable."
        )
    with open(ARTICLES_FILE, encoding="utf-8") as f:
        urls: List[str] = [
            line.strip() for line in f if line.strip() and not line.startswith("#")
        ]

    skipped_articles: List[Tuple] = []
    
    for url in urls:
        article_text, title = fetch_article_text(url, use_cache=args.cache)
        if not article_text:
            print(f"Skipping {title}: could not fetch article text.")
            skipped_articles.append((url,title))
            continue
        if not title:
            print(f"Skipping {url}: could not determine article title.")
            skipped_articles.append((url,url))
            continue
        raw_output = generate_anki_cards(
            article_text, custom_instructions=args.instructions
        )
        cloze_cards, basic_cards = split_cards(raw_output)
        if args.to_file:
            export_to_file(cloze_cards, title, is_cloze=True)
            export_to_file(basic_cards, title, is_cloze=False)
        else:
            for card in cloze_cards:
                front, back = card.split(" ; ")
                add_to_anki(front, back, title, is_cloze=True, deck=args.deck)
            for card in basic_cards:
                front, back = card.split(" ; ")
                add_to_anki(front, back, title, is_cloze=False, deck=args.deck)
        print(f"Finished processing {title}. Generated {len(cloze_cards)} cloze cards and {len(basic_cards)} basic cards.")
        time.sleep(1)  # To avoid hitting the API too fast

    print("All done!")
    if skipped_articles:
        print("Skipped Articles:")
        for url, title in skipped_articles:
            print(f"{title} - {url}")

if __name__ == "__main__":
    main()
