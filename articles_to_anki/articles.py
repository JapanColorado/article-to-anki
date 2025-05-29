import hashlib
import os
from typing import Optional, List, Dict, Any

import requests
from bs4 import BeautifulSoup
from readability import Document
import pymupdf
from articles_to_anki.config import MODEL, client, get_processed_articles, save_processed_articles


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
        self.content_hash: Optional[str] = None
        self.is_processed: bool = False
        self._identifier: Optional[str] = None

    @property
    def identifier(self) -> str:
        """
        Returns a unique identifier for the article (URL or file path).
        """
        if self._identifier is not None:
            return self._identifier
        if self.url:
            self._identifier = self.url
        elif self.file_path:
            self._identifier = os.path.basename(self.file_path)
        else:
            raise ValueError("Either url or file_path must be provided.")
        return self._identifier

    def fetch_content(self, use_cache: bool = False, skip_if_processed: bool = False, model: Optional[str] = None):
        """
        Fetches and sets the article's content and title from either a file or a URL.

        Args:
            use_cache (bool): Whether to cache URL content to avoid repeated fetching.
            skip_if_processed (bool): Whether to skip fetching if the article has already been processed.
            model (Optional[str]): OpenAI model to use for fallback text extraction. If None, uses default from config.
        """
        # Check if the article has already been processed
        if skip_if_processed and self._check_if_processed():
            self.is_processed = True
            return

        if self.file_path:
            self._fetch_from_file()
        elif self.url:
            self._fetch_from_url_or_cache(use_cache, model)
        else:
            raise ValueError("Either url or file_path must be provided.")

        # Generate a hash of the content
        if self.text:
            self._generate_content_hash()

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

    def _fetch_from_url_or_cache(self, use_cache: bool = False, model: Optional[str] = None):
        """
        Fetches the article content and title from a URL, optionally using caching.

        Args:
            use_cache (bool): Whether to use local caching of the article content.
            model (Optional[str]): OpenAI model to use for fallback text extraction. If None, uses default from config.
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
            if not client:
                raise RuntimeError(f"Failed to extract text from {self.url} and no OpenAI client available for fallback extraction.")
            selected_model = model or MODEL
            print(f"Failed to extract text from {self.url}. Using GPT extraction fallback with model {selected_model}.")
            response = client.chat.completions.create(
                model=selected_model,
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

    def _generate_content_hash(self) -> None:
        """
        Generates a hash of the article content for identifying duplicates.
        """
        if not self.text:
            return

        # Include title in hash calculation if available
        content_to_hash = (self.title or "") + "\n" + self.text
        self.content_hash = hashlib.sha256(content_to_hash.encode('utf-8')).hexdigest()

    def _check_if_processed(self) -> bool:
        """
        Checks if the article has already been processed by looking up its
        identifier in the processed articles file.

        Returns:
            bool: True if the article has been processed before, False otherwise.
        """
        processed_articles = get_processed_articles()
        return self.identifier in processed_articles

    def mark_as_processed(self, deck: str) -> None:
        """
        Marks the article as processed by adding its information to the processed articles file.

        Args:
            deck (str): The name of the deck where cards were added.
        """
        if not self.content_hash:
            self._generate_content_hash()

        processed_articles = get_processed_articles()
        processed_articles[self.identifier] = {
            "title": self.title,
            "hash": self.content_hash,
            "deck": deck
        }
        save_processed_articles(processed_articles)

    def generate_cards(self, custom_prompt: Optional[str] = None, model: Optional[str] = None) -> tuple[List[str], List[str]]:
        """
        Generates Anki flashcards from the article's text using GPT completions.
        For each key concept, the optimal card format (cloze or basic) is chosen
        to avoid redundancy and maximize learning effectiveness.

        Args:
            custom_prompt (Optional[str]): Additional instructions to modify the base prompt.
            model (Optional[str]): OpenAI model to use for generation. If None, uses default from config.

        Returns:
            tuple[List[str], List[str]]: A tuple with a list of cloze cards and a list of basic cards.
        """
        # If the article was already processed, return empty lists
        if self.is_processed:
            print(f"Skipping card generation for \"{self.title or self.identifier}\": already processed.")
            return [], []
        base_prompt = """
You are a spaced repetition tutor creating Anki flashcards from an article the user provides.

Your task is to extract key ideas and present each one using the optimal flashcard format. For each distinct concept, choose either cloze or basic format based on what works best for that specific type of information.

Card Format Selection Guidelines:

Use CLOZE format for:
- Main arguments and key supporting claims where the structure and context matter
- Conceptual relationships where seeing the full sentence helps understanding
- Complex ideas that benefit from partial context cues
- Statements where multiple related terms can be tested together ({{c1::term1}} and {{c2::term2}})

Use BASIC format for:
- Clear definitions where a simple question-answer works best
- Specific facts, statistics, or data points
- Direct cause-effect relationships that can be asked simply
- Terminology where the definition is the focus

Card Creation Rules:
- Extract approximately one card for every 150 words in the article
- Each card should test a unique, distinct concept—avoid redundancy between cloze and basic cards
- For cloze cards: Keep sentences concise and direct, cloze 1-5 words that are key terms or concepts
- For basic cards: Use simple, direct questions with clear, short answers
- Focus on the core reasoning and avoid examples, metaphors, quotes, or trivia
- If an idea could work as either format, choose the one that makes the concept clearest and most memorable

Content Guidelines:
- Identify the main argument (central thesis) and key supporting claims
- Extract meaningful definitions, distinctions, or relationships the author establishes
- If the argument is implicit, infer the author's main points
- Focus only on intentional, substantial content

Output Format:
- Begin with the line CLOZE, then list all cloze cards
- Then write BASIC, and list all basic cards
- Format each card using semicolons:
  - Cloze: {{c1::clozed phrase}}
  - Basic: Question ; Answer
- Use ONLY the separators shown above - no extra semicolons or spaces
- IMPORTANT: Replace any semicolons (;) in the original text content with commas (,) to avoid confusion with card format separators
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

        if not client:
            raise RuntimeError("OpenAI client not available. Please set OPENAI_API_KEY environment variable.")

        # Use provided model or fall back to default
        selected_model = model or MODEL
        print(f"Generating cards for \"{self.title}\" using model {selected_model}...")

        response = client.chat.completions.create(
            model=selected_model,
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
