# Articles to Anki

**Articles to Anki** is a Python tool that automates the creation of high-quality Anki flashcards from articles, whether sourced from URLs or local files. Leveraging GPT-4, it intelligently selects the optimal card format (cloze or basic) for each concept to maximize learning effectiveness and avoid redundancy.

## Features

- **Fetch Articles**: Download and parse articles from URLs or supported local file formats (PDF, EPUB, DOCX, TXT, and more)
- **Multiple URL Sources**: Process URLs from multiple organized files using `--url-files`
- **Smart Parsing**: Uses readability and GPT-4 to extract clean article text and titles, even from messy web pages
- **Intelligent Card Generation**: Automatically selects the optimal format (cloze or basic) for each concept, focusing on core arguments, definitions, and key facts while avoiding redundancy
- **Flexible Export**: Send cards directly to Anki via AnkiConnect, or export them as text files for later use
- **Smart Duplicate Detection**: Identifies semantically similar cards even with different wording, preventing redundant flashcards
- **Custom Prompts**: Optionally provide your own prompt to customize card generation
- **Caching**: Optionally cache downloaded articles to speed up repeated runs
- **Process Control**: Fine-grained control over which articles to process and whether to allow duplicates

## Quick Start

### Installation

```bash
# Install with basic features
pip install articles-to-anki

# Install with advanced similarity detection (recommended)
pip install articles-to-anki[advanced_similarity]
```

### Setup

```bash
# Create directories and download required resources
articles-to-anki-setup

# Set your OpenAI API key
export OPENAI_API_KEY='your_openai_api_key'
```

### Usage

```bash
# Add URLs to articles/urls.txt, then run:
articles-to-anki

# Or process URLs from specific files:
articles-to-anki --url-files tech_articles.txt science_articles.txt

# Export to a specific deck with caching:
articles-to-anki --deck "Learning" --use_cache
```

## Multiple URL Files

Organize your articles by topic, priority, or source using multiple URL files:

```bash
# Process URLs from multiple organized files
articles-to-anki --url-files technology.txt science.txt history.txt

# Combine with other options
articles-to-anki --url-files priority_articles.txt --deck "High Priority" --use_cache
```

### File Organization Examples

```
urls/
├── technology.txt      # AI, programming, tech news
├── science.txt         # Research papers, discoveries
├── high_priority.txt   # Must-read articles
└── daily_reading.txt   # Regular reading list
```

Each file follows the same format as `articles/urls.txt`:
```
# Technology Articles
https://example.com/ai-breakthrough
https://example.com/programming-tutorial

# Comments start with #
https://example.com/machine-learning-guide
```

## Requirements

- Python 3.9+
- OpenAI API key
- Anki with [AnkiConnect](https://foosoft.net/projects/anki-connect/) (for direct export to Anki)

## Installation Options

### From PyPI (Recommended)

```bash
# Basic installation
pip install articles-to-anki

# With advanced similarity detection
pip install articles-to-anki[advanced_similarity]

# All features
pip install articles-to-anki[all]
```

### From GitHub

```bash
# Latest development version
pip install git+https://github.com/japancolorado/articles-to-anki.git

# With advanced features
pip install "git+https://github.com/japancolorado/articles-to-anki.git#egg=articles-to-anki[advanced_similarity]"
```

### Development Installation

```bash
git clone https://github.com/japancolorado/articles-to-anki.git
cd articles-to-anki
pip install -e .[dev]
```

## Configuration

### 1. Set OpenAI API Key

```bash
export OPENAI_API_KEY='your_openai_api_key'
```

Or add it to your shell profile for persistence.

### 2. Run Setup

```bash
articles-to-anki-setup
```

This creates necessary directories and downloads NLTK resources for advanced similarity detection.

### 3. Add Content

- **URLs**: Add to `articles/urls.txt` or create custom URL files
- **Local Files**: Place PDF, EPUB, DOCX, TXT, etc. in the `articles/` directory

## Usage

### Basic Usage

```bash
articles-to-anki
```

### Command Line Options

```bash
articles-to-anki [OPTIONS]
```

**Options:**
- `--deck DECKNAME` — Anki deck to export to (default: "Default")
- `--model MODEL` — OpenAI model to use (default: "gpt-4o-mini"). Examples: gpt-4o, gpt-4-turbo, gpt-4.1 mini, gpt-4.1
- `--url-files FILE [FILE ...]` — Additional URL files to process
- `--use_cache` — Cache downloaded articles to avoid re-fetching
- `--to_file` — Export to text files instead of Anki
- `--custom_prompt "..."` — Custom instructions for card generation
- `--allow_duplicates` — Allow duplicate cards to be created
- `--process_all` — Process all articles, even previously processed ones
- `--similarity_threshold 0.85` — Similarity threshold for duplicate detection (0.0-1.0)

### Examples

```bash
# Process multiple URL files with custom deck
articles-to-anki --url-files tech.txt science.txt --deck "Learning"

# Use a specific OpenAI model
articles-to-anki --model gpt-4o --deck "Research"

# Use caching and custom prompt with different model
articles-to-anki --model gpt-4-turbo --use_cache --custom_prompt "Focus on practical applications"

# Export to files instead of Anki
articles-to-anki --to_file --url-files priority.txt

# Use cheaper model for large batches
articles-to-anki --model gpt-3.5-turbo --url-files bulk.txt

# Allow duplicates and process all articles
articles-to-anki --allow_duplicates --process_all

# Adjust duplicate detection sensitivity
articles-to-anki --similarity_threshold 0.75
```

## Supported File Types

- **Documents**: PDF, DOCX, DOC, TXT, MD
- **E-books**: EPUB, MOBI, FB2
- **Presentations**: PPTX, PPT
- **Other**: XPS, CBZ, SVG

## How It Works

1. **Article Extraction**: Downloads URLs or reads local files, extracting clean text and titles
2. **Duplicate Prevention**: Checks if articles have been processed before (unless `--process_all`)
3. **Card Generation**: Uses GPT-4 to intelligently choose the best card format for each concept from article content
4. **Smart Filtering**: Detects semantically similar cards to prevent duplicates (unless `--allow_duplicates`)
5. **Export**: Sends cards to Anki via AnkiConnect or exports to text files
6. **Record Keeping**: Tracks processed articles to avoid reprocessing

## Troubleshooting

### Setup Issues

If you encounter setup problems:

```bash
# Fix NLTK issues specifically
articles-to-anki-fix-nltk

# Recreate directories only
articles-to-anki-setup --dirs-only

# Setup NLTK resources only
articles-to-anki-setup --nltk-only
```

### Common Problems

**AnkiConnect Issues:**
- Ensure Anki is running with AnkiConnect addon enabled
- Check that cloze cards have proper `{{c1::text}}` formatting
- Try exporting to files first: `--to_file`

**NLTK Errors:**
- Run `articles-to-anki-fix-nltk` for automated fixes
- Set `NLTK_DATA` environment variable: `export NLTK_DATA=~/nltk_data`
- The tool automatically falls back to basic similarity detection if advanced features fail

**API Errors:**
- Verify your OpenAI API key is valid and has quota
- Check network connectivity

**No Cards Generated:**
- Verify article content is substantial and readable
- Try adjusting your custom prompt
- Check that URLs are accessible

## Advanced Configuration

Edit `articles_to_anki/config.py` to customize:
- GPT model selection
- File paths and directories
- AnkiConnect settings
- Default similarity thresholds

## Getting Free OpenAI Credits

**Share input/outputs with OpenAI and get free credits!**

1. **Sign up for OpenAI API**: Visit [platform.openai.com](https://platform.openai.com)
2. **Enable data sharing**: In your account settings, opt-in to share your API usage data with OpenAI
3. **Generate project API key**: Use this key in your environment variable `OPENAI_API_KEY`
4. **Profit**: Enjoy free credits for your Anki card generation enjoyment!

## Development

### Running Tests

```bash
pip install -e .[dev]
pytest
```

### Code Formatting

```bash
black articles_to_anki/
flake8 articles_to_anki/
```

### Building for Distribution

```bash
python -m build
twine check dist/*
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## Support

- **Issues**: [GitHub Issues](https://github.com/japancolorado/articles-to-anki/issues)
- **Documentation**: This README and inline code documentation
- **Troubleshooting**: Use `articles-to-anki-fix-nltk` for NLTK issues
