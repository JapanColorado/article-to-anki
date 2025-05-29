"""Articles to Anki - Generate Anki flashcards from articles using GPT-4.

A Python tool that automates the creation of high-quality Anki flashcards from articles,
whether sourced from URLs or local files. Leveraging GPT-4, it intelligently selects
the optimal card format (cloze or basic) for each concept to maximize learning effectiveness
and avoid redundancy.

Features:
- Fetch articles from URLs or local files (PDF, EPUB, DOCX, TXT, etc.)
- Smart parsing with readability and GPT-4 extraction
- Intelligent card format selection for optimal learning
- Direct export to Anki via AnkiConnect or file export
- Smart duplicate detection with semantic similarity
- Custom prompts and flexible configuration
"""

__version__ = "0.4.0"
__author__ = "japancolorado"
__email__ = "japancolorado@duck.com"
__license__ = "MIT"
__url__ = "https://github.com/japancolorado/articles-to-anki"

from .articles import Article
from .export_cards import ExportCards

__all__ = [
    "Article",
    "ExportCards",
    "__version__",
    "__author__",
    "__email__",
    "__license__",
    "__url__",
]
