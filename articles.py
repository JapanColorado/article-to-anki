import hashlib
import os
from typing import Tuple, Optional, List

import requests
from bs4 import BeautifulSoup
from readability import Document
import pymupdf
from config import MODEL, client


class Article:
    """
    Represents an article obtained from a URL or a file, and provides methods
    to fetch its content and generate Anki flashcards.
    """

    def __init__(self, url: Optional[str] = None, file_path: Optional[str] = None):
        """
        Initialize an Article with either a URL or a local file path.

        Args:
            url (Optional[str]): The URL of the article.
            file_path (Optional[str]): The local file path of the article.
        """
        self.url = url
        self.file_path = file_path
        self.title: Optional[str] = None
        self.text: Optional[str] = None

    def fetch_content(self, use_cache: bool = False):
        """
        Fetches and sets the article's content and title from either a file or a URL.

        Args:
            use_cache (bool): Whether to cache URL content to avoid repeated fetching.
        """
        if self.file_path:
            self._fetch_from_file()
        elif self.url:
            self._fetch_from_url_or_cache(use_cache)
        else:
            raise ValueError("Either url or file_path must be provided.")

    def _fetch_from_file(self):
        """
        Extracts the article content and title from a file using pymupdf.
        """
        doc = pymupdf.open(self.file_path)
        title = (doc.metadata or {}).get("title") or os.path.basename(self.file_path or "")
        text = ""
        for page in doc:
            text += page.get_text("text") # type: ignore
        self.title = title
        self.text = text

    def _fetch_from_url_or_cache(self, use_cache: bool = False):
        """
        Fetches the article content and title from a URL, optionally using caching.

        Args:
            use_cache (bool): Whether to use local caching of the article content.
        """
        cache_path = None
        if use_cache:
            cache_dir = ".article_cache"
            os.makedirs(cache_dir, exist_ok=True)
            url_hash = hashlib.sha256((self.url or "").encode("utf-8")).hexdigest()
            cache_path = os.path.join(cache_dir, f"{url_hash}.txt")
            if os.path.exists(cache_path):
                with open(cache_path, "r", encoding="utf-8") as f:
                    self.file_path = cache_path
                    lines = f.readlines()
                    if lines:
                        self.title = lines[0].strip()
                        self.text = "".join(lines[1:]).strip()
                        return

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/113.0.0.0 Safari/537.36"
            )
        }
        try:
            response = requests.get(self.url or "", headers=headers, timeout=15)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to fetch {self.url}: {e}")

        doc = Document(response.text)
        title = doc.short_title() or (self.url or "")
        main_html = doc.summary()
        soup = BeautifulSoup(main_html, "html.parser")

        # Remove sections with id or class containing "comment"
        for tag in soup.find_all(
            lambda t: (
                (t.has_attr("id") and any("comment" in x.lower() for x in t["id"]))
                or (t.has_attr("class") and any("comment" in x.lower() for x in t["class"]))
            )
        ):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)
        text = "\n".join(line for line in text.splitlines() if line.strip())

        # Fallback to GPT parsing if text extraction failed.
        if not text:
            print(f"Failed to extract text from {self.url}. Using GPT extraction fallback.")
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a web scraper that extracts the main text and title from an article.",
                    },
                    {
                        "role": "user",
                        "content": f"Extract the main text and title from this HTML:\n{response.text}",
                    },
                ],
                temperature=0.1,
            )
            content = response.choices[0].message.content if response.choices else ""
            if content:
                lines = content.splitlines()
                title = lines[0].strip().replace("Title: ", "")
                text = "\n".join(line.strip() for line in lines[1:] if line.strip())
            else:
                raise RuntimeError(f"Failed to extract text with GPT fallback for {self.title or 'Unknown'} - {self.url}.")

        self.title = title
        self.text = text
        if use_cache and cache_path is not None:
            with open(cache_path, "w", encoding="utf-8") as f:
                f.write(title + "\n")
                f.write(text)

    def generate_cards(self, custom_prompt: Optional[str] = None) -> Tuple[List[str], List[str]]:
        """
        Generates Anki flashcards from the article's text using GPT completions.
        Two types of cards are created: Cloze cards and Basic cards.

        Args:
            custom_prompt (Optional[str]): Additional instructions to modify the base prompt.

        Returns:
            Tuple[List[str], List[str]]: A tuple with a list of cloze cards and a list of basic cards.
        """
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
        if custom_prompt:
            prompt = (
                base_prompt
                + "\nThe user provided these additional instructions:\n"
                + custom_prompt.strip()
                + "\n\nArticle Content:\n"
            )
        else:
            prompt = base_prompt + "\nArticle Content:\n"

        full_prompt = prompt + (self.text or "")

        print(f"Generating cards for \"{self.title}\"...")

        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You generate high-quality Anki cards from articles."},
                {"role": "user", "content": full_prompt},
            ],
            temperature=0.7,
        )
        generated_text = (
            response.choices[0].message.content.strip() if response.choices and response.choices[0].message.content else ""
        )

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
