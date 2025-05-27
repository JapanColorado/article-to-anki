# Articles to Anki

**Articles to Anki** is a Python tool that automates the creation of high-quality Anki flashcards from articles, whether sourced from URLs or local files. Leveraging GPT-4, it generates both cloze and basic cards, and can export them directly to Anki (via AnkiConnect) or to text files for manual import.

---

## Features

- **Fetch Articles**: Download and parse articles from URLs or supported local file formats (PDF, EPUB, DOCX, TXT, and more).
- **Smart Parsing**: Uses readability and GPT-4 to extract clean article text and titles, even from messy web pages.
- **Flashcard Generation**: Automatically generates both cloze and basic Anki cards, focusing on core arguments, definitions, and key facts.
- **Flexible Export**: Send cards directly to Anki via AnkiConnect, or export them as text files for later use.
- **Custom Prompts**: Optionally provide your own prompt to customize card generation.
- **Caching**: Optionally cache downloaded articles to speed up repeated runs.
- **Smart Duplicate Detection**: Identifies semantically similar cards even with different wording, preventing GPT-generated variations of the same concept from becoming redundant flashcards.
- **Process Control**: Fine-grained control over which articles to process and whether to allow duplicates.

---

## Requirements

- Python 3.8+
- Anki with [AnkiConnect](https://foosoft.net/projects/anki-connect/) (if exporting directly to Anki)
- OpenAI API key

---

## Installation and Setup

You can install **Articles to Anki** in two ways:

### 1. Install via pip (recommended)

If you just want to use the tool, you can install it directly from PyPI (if available) or from the GitHub repository:

```bash
# Basic installation
pip install articles-to-anki

# With advanced similarity detection (recommended)
pip install articles-to-anki[advanced_similarity]
```

Or, to install the latest version directly from GitHub:

```bash
# Basic installation
pip install git+https://github.com/yourusername/articles-to-anki.git

# With advanced similarity detection (recommended)
pip install git+https://github.com/yourusername/articles-to-anki.git#egg=articles-to-anki[advanced_similarity]
```

After installation, run the setup command to create directories and download NLTK data:

```bash
articles-to-anki-setup
```

### 2. Use from the downloaded GitHub repo

Clone the repository:

```bash
git clone https://github.com/yourusername/articles-to-anki.git
cd articles-to-anki
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

Then run the setup script:

```bash
python articles-to-anki/setup_app.py
```

### Advanced Similarity Detection

The setup command automatically configures the advanced similarity detection if you've installed the required dependencies. If you want to set up only specific components:

```bash
# Set up only directories and files
articles-to-anki-setup --dirs-only

# Set up only NLTK resources (use this if you're having NLTK issues)
articles-to-anki-setup --nltk-only

# Fix specific NLTK issues like "punkt_tab not found" errors
articles-to-anki-fix-nltk
```

These packages enable more sophisticated semantic matching between cards. If you encounter issues with NLTK (particularly "punkt_tab not found" errors), the system will automatically fall back to basic similarity detection, which still provides effective duplicate card detection.

**Note about punkt_tab errors**: Some newer versions of NLTK look for a resource called `punkt_tab` that isn't part of the standard distribution. Our troubleshooting tools create workarounds for this issue.

---

## Configuration

1. **Set your OpenAI API key**
   Export your key as an environment variable:
   ```
   export OPENAI_API_KEY='your_openai_api_key'
   ```
   Or add it to `config.py` directly.

2. **Add your content**
   - Place local files (PDF, EPUB, DOCX, TXT, etc.) in the `articles/` directory.
   - Add URLs (one per line) to `articles/urls.txt`.

3. **(Optional) Advanced configuration**
   Edit `config.py` to change the article directory, GPT model, or note types.

---

## Usage

Before first use, make sure you've run the setup command (`articles-to-anki-setup`).

### If installed via pip

After installing with pip, run:

```
articles-to-anki [options]
```

### If running from a local GitHub clone

From the project root directory, run:

```
python articles-to-anki/cli.py [options]
```

**Options:**
- `--deck DECKNAME` — Specify the Anki deck to export to (default: "Default")
- `--use_cache` — Use cached article content if available (avoids re-downloading articles)
- `--to_file` — Export cards to text files instead of Anki
- `--custom_prompt "..."` — Provide additional custom prompting for card generation
- `--allow_duplicates` — Allow duplicate cards to be created even if they already exist
- `--process_all` — Process all articles even if they have been processed before
- `--similarity_threshold 0.85` — Set the threshold for detecting semantically similar cards (0.0-1.0, higher values require more similarity to consider cards as duplicates)

---

## How It Works

1. **Setup**: The setup command creates necessary directories and downloads required resources.
2. **Configuration Check**: Ensures your API key and required files exist.
3. **Article Loading**: Reads URLs and local files, extracting clean text and titles.
4. **Duplicate Detection**: Checks if articles have been processed before and skips them unless `--process_all` is used.
5. **Card Generation**: Uses GPT-4.1 mini to create cloze and basic cards.
   - If a custom prompt is provided, it uses that; otherwise, it defaults to a predefined prompt.
   - Cards are generated based on the article content, focusing on key concepts and definitions.
6. **Smart Duplicate Detection**: Each card is semantically compared with previously generated cards to identify conceptual duplicates, even when phrased differently by GPT (unless `--allow_duplicates` is used).
7. **Export**: Sends cards to Anki (via AnkiConnect) or writes them to `exported_cards/`.
8. **Record Keeping**: Records processed articles to avoid re-processing them in future runs.

---

## Supported File Types

- `.pdf`, `.xps`, `.epub`, `.mobi`, `.fb2`, `.cbz`, `.svg`, `.txt`, `.md`, `.docx`, `.doc`, `.pptx`, `.ppt`

---

## Troubleshooting

- **First-time setup**: If you haven't run the setup command, run `articles-to-anki-setup` before using the tool.
- **AnkiConnect errors**: Make sure Anki is running and the AnkiConnect add-on is installed and enabled.
- **No cards generated**: Check your article content and custom prompt for clarity.
- **API errors**: Ensure your OpenAI API key is valid and you have quota.
- **Directory or file missing**: Run `articles-to-anki-setup` to create the necessary directories and files.
- **Skipped articles**: If articles are being skipped because they were previously processed, use the `--process_all` flag to override this behavior.
- **Duplicate cards**: The tool automatically detects and skips semantically similar cards (cards expressing the same concept in different words). To allow all duplicates, use the `--allow_duplicates` flag. To fine-tune duplicate sensitivity, adjust the `--similarity_threshold` option (default: 0.85, higher = stricter matching).
- **AnkiConnect errors**: If you see "cannot create note" or connection errors:
  1. Make sure Anki is running with AnkiConnect add-on installed
  2. Check for proper cloze formatting (cloze cards must include `{{c1::text}}` markers)
  3. Restart Anki and make sure AnkiConnect is enabled
- **NLTK errors**: If you see errors related to NLTK data not being found:
  1. Use our dedicated troubleshooting tool (specifically handles punkt_tab issues):
     `articles-to-anki-fix-nltk`
  2. If that doesn't work, try setting the NLTK_DATA environment variable:
     `export NLTK_DATA=~/nltk_data`
  3. Still having issues? No problem - the system will automatically fall back to basic similarity detection which still works well for finding duplicate cards.

  The system is designed to work even without the advanced NLP features. The basic similarity detection will automatically be used as a fallback.

---

## License

MIT License

---

## Troubleshooting

### AnkiConnect Issues

If you're experiencing problems with AnkiConnect or card creation:

1. **Common AnkiConnect problems**:
   - **"cannot create note" errors**:
     - Check if your cloze cards have proper cloze formatting (`{{c1::text}}`)
     - Verify the deck exists in Anki
     - Make sure Anki is running when you export cards
   - **Connection issues**: Check that AnkiConnect add-on is installed and enabled in Anki
   - **Empty fields**: Make sure cards have content in required fields

2. **Debugging steps**:
   - Restart Anki and make sure AnkiConnect is enabled
   - Try exporting to file instead with `--to_file` option
   - Test with a simple Anki card creation using the AnkiConnect API directly

### NLTK Issues

If you experience problems with the semantic similarity features related to NLTK:

1. **Run the dedicated troubleshooter** (recommended first step):
   ```bash
   articles-to-anki-fix-nltk
   ```
   This tool diagnoses common NLTK issues and applies fixes automatically.

2. **Common NLTK problems**:
   - **`punkt_tab not found` errors**: This is a common issue with newer versions of NLTK
     - The troubleshooter will create a workaround that doesn't need punkt_tab
     - This might use a simpler tokenization method but will work for card generation
   - **Permission problems**: Try running the commands with admin/sudo privileges
   - **Path issues**: Set the `NLTK_DATA` environment variable:
     ```bash
     export NLTK_DATA=~/nltk_data
     ```
     Add this to your shell profile (e.g., .bashrc, .zshrc) to make it permanent

3. **If the troubleshooter doesn't work**:
   - Run setup with just NLTK: `articles-to-anki-setup --nltk-only`
   - Try manually downloading NLTK data:
     ```python
     import nltk
     nltk.download('punkt')
     nltk.download('stopwords')
     ```

4. **Don't worry if fixes don't work**:
   - The tool automatically falls back to basic similarity detection
   - You can still use all features of Articles to Anki
   - Basic similarity detection is still effective for finding duplicate cards

## TODO

- Add more usage examples and screenshots
- Finetune similarity_threshold
- Add tests and CI/CD pipeline
- Support more file formats and advanced parsing options
- Add better error reporting with colored output
- Optimize semantic similarity algorithm for special terminology
- Improve handling of PDF formatting inconsistencies
- Create a web interface
- Publish package to PyPI
