import os
import time
import requests
import argparse
from bs4 import BeautifulSoup
from openai import OpenAI
from typing import Tuple, Optional, List

# === CONFIGURATION ===
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANKI_CONNECT_URL = "http://localhost:8765"
MODEL = "gpt-4.1-mini"
ARTICLES_FILE = "articles.txt"

client = OpenAI(api_key=OPENAI_API_KEY)


def fetch_article_text(url: str) -> Tuple[Optional[str], Optional[str]]:
    """Fetches the article text and title from the given URL using BeautifulSoup."""
    print(f"Fetching: {url}")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch {url}: {e}")
        return None, None

    soup = BeautifulSoup(resp.text, "html.parser")

    # Try to get the title
    title = soup.title.string.strip() if soup.title and soup.title.string else url

    # Try to extract main article text
    # Prefer <article> tag if present
    article = soup.find("article")
    if article:
        text = article.get_text(separator="\n", strip=True)
    else:
        # Fallback: get all <p> tags
        paragraphs = soup.find_all("p")
        text = "\n".join(p.get_text(strip=True) for p in paragraphs)

    # Remove excessive whitespace
    text = "\n".join(line for line in text.splitlines() if line.strip())

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
- Avoid examples, metaphors, quotes, or trivia—focus only on the core reasoning.
- Aim for 2–10 cloze cards. Include more only if the article presents many distinct, well-developed points.

Basic Cards
- Extract definitions, distinctions, or cause-effect relationships the author defines or builds on.
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
    """Exports cards to a file. Format is front; back; title;"""
    os.makedirs("exported_cards", exist_ok=True)  # Ensure the directory exists
    filename = f"exported_cards/{title.replace(' ', '_')}_{'cloze' if is_cloze else 'basic'}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        for card in cards:
            f.write(f"{card} {title}\n")


def main() -> None:
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
    args = parser.parse_args()

    if not OPENAI_API_KEY or OPENAI_API_KEY.startswith("sk-..."):
        raise ValueError(
            "Set your OpenAI API key in the OPENAI_API_KEY variable or as an environment variable."
        )
    with open(ARTICLES_FILE, encoding="utf-8") as f:
        urls: List[str] = [
            line.strip() for line in f if line.strip() and not line.startswith("#")
        ]
    for url in urls:
        article_text, title = fetch_article_text(url)
        if not article_text:
            print(f"Skipping {url}: could not fetch article text.")
            continue
        if not title:
            print(f"Skipping {url}: could not determine article title.")
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
        print(f"Finished processing {url}. Generated {len(cloze_cards)} cloze cards and {len(basic_cards)} basic cards.")
        time.sleep(1)  # To avoid hitting the API too fast

    print("All done!")


if __name__ == "__main__":
    main()
