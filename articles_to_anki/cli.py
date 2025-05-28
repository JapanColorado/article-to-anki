import os
import argparse
import requests
from articles_to_anki.config import OPENAI_API_KEY, URLS_FILE, ARTICLE_DIR, ALLOWED_EXTENSIONS, ANKICONNECT_URL, CLOZE_MODEL_NAME, BASIC_MODEL_NAME, SIMILARITY_THRESHOLD
from articles_to_anki.articles import Article
from articles_to_anki.export_cards import ExportCards

def check_config() -> None:
    """
    Checks if the necessary configuration is set up correctly.
    Raises an error if the OPENAI_API_KEY is not set, or if required directories/files don't exist.

    Raises:
        ValueError: If OPENAI_API_KEY is not set.
        FileNotFoundError: If ARTICLE_DIR or URLS_FILE does not exist.
    """
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY must be set in the environment variables(or in config.py). Use the following command:\nexport OPENAI_API_KEY='your_api_key'")

    # Check if required directories and files exist
    if not os.path.exists(ARTICLE_DIR) or not os.path.exists(URLS_FILE):
        raise FileNotFoundError(
            f"Required directories or files don't exist. Please run 'articles-to-anki-setup' "
            f"to create the necessary directories and files before using the main command."
        )

def check_anki_note_model() -> None:
    """Checks if the Anki note model exists and creates it if not."""
    payload = {
        "action": "modelNames",
        "version": 6
    }
    try:
        response = requests.post(ANKICONNECT_URL, json=payload, timeout=15)
        response.raise_for_status()
        models = response.json().get("result", [])
        if f"{CLOZE_MODEL_NAME}" not in models:
            create_model_payload = {
                "action": "createModel",
                "version": 6,
                "params": {
                    "modelName": CLOZE_MODEL_NAME,
                    "inOrderFields": [
                        "Text",
                        "Extra"
                    ],
                    "css": """
.card {
 font-family: arial;
 font-size: 20px;
 text-align: left;
 color: black;
 background-color: white;
}
.cloze {
 font-weight: bold;
 color: blue;
}
""",
                    "isCloze": True,
                    "cardTemplates": [
                        {
                            "Name": "Cloze",
                            "Front": "{{cloze:Text}}",
                            "Back": "{{cloze:Text}}<br>{{Extra}}"
                        }
                    ]
                }
            }
            create_response = requests.post(ANKICONNECT_URL, json=create_model_payload, timeout=15)
            create_response.raise_for_status()
            if create_response.json().get("error"):
                raise RuntimeError(f"Failed to create Cloze model: {create_response.json().get('error')}")
            print(f"Cloze model '{CLOZE_MODEL_NAME}' created in Anki.")
        if f"{BASIC_MODEL_NAME}" not in models:
            create_basic_model_payload = {
                "action": "createModel",
                "version": 6,
                "params": {
                    "modelName": BASIC_MODEL_NAME,
                    "inOrderFields": [
                        "Front",
                        "Back"
                    ],
                    "css": """
.card {
 font-family: arial;
 font-size: 20px;
 text-align: left;
 color: black;
 background-color: white;
}
""",
                    "isCloze": False,
                    "cardTemplates": [
                        {
                            "Name": "Basic",
                            "Front": "{{Front}}",
                            "Back": "{{Front}}<hr id=answer>{{Back}}"
                        }
                    ]
                }
            }
            create_basic_response = requests.post(ANKICONNECT_URL, json=create_basic_model_payload, timeout=15)
            create_basic_response.raise_for_status()
            if create_basic_response.json().get("error"):
                raise RuntimeError(f"Failed to create Basic model: {create_basic_response.json().get('error')}")
            print(f"Basic model '{BASIC_MODEL_NAME}' created in Anki.")
    except requests.exceptions.RequestException as e:
        print(f"Failed to check Anki note models: {e}. Check if Anki is running and AnkiConnect is enabled.")

def read_urls_from_files(url_files):
    """
    Read URLs from multiple files and combine them.
    
    Args:
        url_files (list): List of file paths containing URLs
        
    Returns:
        list: Combined list of URLs from all files
    """
    all_urls = []
    
    for file_path in url_files:
        try:
            with open(file_path, "r") as f:
                urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]
                all_urls.extend(urls)
                print(f"Loaded {len(urls)} URLs from {file_path}")
        except FileNotFoundError:
            print(f"Warning: URL file '{file_path}' not found. Skipping.")
        except Exception as e:
            print(f"Error reading URLs from '{file_path}': {e}. Skipping.")
    
    return all_urls

def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch articles and export Anki cards. Run 'articles-to-anki-setup' first if this is your first time.")
    parser.add_argument(
        "--deck",
        type=str,
        default="Default",
        help="Name of the Anki deck to export cards to.",
    )
    parser.add_argument(
        "--use_cache",
        action="store_true",
        help="Use cached content for URLs to avoid repeated fetching.",
    )
    parser.add_argument(
        "--to_file",
        action="store_true",
        help="Export cards to a file instead of AnkiConnect.",
    )
    parser.add_argument(
        "--custom_prompt",
        type=str,
        default="",
        help="Custom prompt to use for generating cards. If not provided, the default prompt will be used.",
    )
    parser.add_argument(
        "--allow_duplicates",
        action="store_true",
        help="Allow duplicate cards to be created even if they already exist.",
    )
    parser.add_argument(
        "--process_all",
        action="store_true",
        help="Process all articles even if they have been processed before.",
    )
    parser.add_argument(
        "--similarity_threshold",
        type=float,
        default=SIMILARITY_THRESHOLD,
        help=f"Threshold for semantic similarity when detecting duplicate cards (0.0-1.0, default: {SIMILARITY_THRESHOLD}).",
    )
    parser.add_argument(
        "--url-files",
        nargs="+",
        metavar="FILE",
        help="Additional text files containing URLs to process (one URL per line, # for comments). Can specify multiple files.",
    )
    args = parser.parse_args()
    if not args.to_file:
        check_anki_note_model()
    check_config()

    # Read URLs from the default file
    urls = []
    try:
        with open(URLS_FILE, "r") as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]
            print(f"Loaded {len(urls)} URLs from {URLS_FILE}")
    except FileNotFoundError:
        print(f"Default URL file '{URLS_FILE}' not found.")
    except Exception as e:
        print(f"Error reading default URL file '{URLS_FILE}': {e}")
    
    # Read URLs from additional files if specified
    if args.url_files:
        additional_urls = read_urls_from_files(args.url_files)
        urls.extend(additional_urls)
        print(f"Total URLs loaded: {len(urls)}")
    
    local_files = [f for f in os.listdir(ARTICLE_DIR) if f.endswith(tuple(ALLOWED_EXTENSIONS)) and not f.startswith(".") and not f == URLS_FILE.split("/")[-1]]

    if not urls and not local_files:
        print(f"No URLs or local files found in {URLS_FILE} or {ARTICLE_DIR}.")
        print(f"Please add URLs to {URLS_FILE}, specify additional URL files with --url-files, or add article files to {ARTICLE_DIR}, then run the script again.")
        return

    articles = [Article(url=url) for url in urls if url.strip()]
    articles += [Article(file_path=os.path.join(ARTICLE_DIR, file)) for file in local_files if file.strip()]

    for article in articles:
        article.fetch_content(use_cache=args.use_cache, skip_if_processed=(not args.process_all))

        # Skip already processed articles unless explicitly told to process all
        if article.is_processed and not args.process_all:
            print(f"Skipping \"{article.title or article.identifier}\": already processed. Use --process_all to override.")
            continue

        cloze_cards, basic_cards = [], []
        if article.text:
            cloze_cards, basic_cards = article.generate_cards(custom_prompt=args.custom_prompt)

        if not cloze_cards and not basic_cards:
            print(f"No cards generated for \"{article.title or article.identifier}\". Please check the article content or your custom prompt.")
            continue

        print(f"Exporting cards for \"{article.title or article.identifier}\"...")

        exporter = ExportCards(
            cloze_cards=cloze_cards,
            basic_cards=basic_cards,
            title=article.title or "Untitled",
            deck=args.deck,
            to_file=args.to_file,
            skip_duplicates=(not args.allow_duplicates),
            similarity_threshold=args.similarity_threshold,
        )
        exporter.export()

        # Mark the article as processed
        article.mark_as_processed(args.deck)

        print(f"Finished processing \"{article.title or article.identifier}\".")
        print("-" * 40)

    print("All articles processed. Check the output for any errors or warnings.")

if __name__ == "__main__":
    main()
