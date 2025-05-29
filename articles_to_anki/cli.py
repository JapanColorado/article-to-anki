import os
import argparse
import requests
from typing import Optional, List
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
    # Try to find them in current directory or parent directories
    article_dir = ARTICLE_DIR
    urls_file = URLS_FILE
    
    # If not found in current directory, check if we're in the articles directory
    if not os.path.exists(article_dir):
        if os.path.basename(os.getcwd()) == "articles" and os.path.exists("../articles"):
            article_dir = "../articles"
            urls_file = "../articles/urls.txt"
        elif os.path.exists("../articles"):
            article_dir = "../articles"
            urls_file = "../articles/urls.txt"
    
    if not os.path.exists(article_dir):
        raise FileNotFoundError(
            f"Required directories or files don't exist. Please run 'articles-to-anki-setup' "
            f"to create the necessary directories and files before using the main command."
        )
    
    # Create urls.txt if it doesn't exist
    if not os.path.exists(urls_file):
        os.makedirs(os.path.dirname(urls_file), exist_ok=True)
        with open(urls_file, "w") as f:
            f.write("# Add your URLs here, one per line.\n")
        print(f"Created {urls_file}")

def get_file_handling_choice(auto_overwrite: bool) -> str:
    """
    Get user's choice on how to handle export files.
    Returns the choice ('1', '2', '3').
    """
    os.makedirs("exported_cards", exist_ok=True)
    
    cloze_file = "exported_cards/cloze_cards.txt"
    basic_file = "exported_cards/basic_cards.txt"
    
    files_exist = []
    if os.path.exists(cloze_file):
        files_exist.append(cloze_file)
    if os.path.exists(basic_file):
        files_exist.append(basic_file)
    
    if auto_overwrite:
        if files_exist:
            print(f"\nExisting export files found - automatically overwriting:")
            for file_path in files_exist:
                print(f"  - {file_path}")
        return '1'  # Auto-overwrite mode
    
    if files_exist:
        print(f"\nExisting export files found:")
        for file_path in files_exist:
            print(f"  - {file_path}")
        
        while True:
            choice = input("\nChoose an option:\n1. Overwrite existing files\n2. Create new files with timestamp\n3. Append to existing files\nEnter choice (1/2/3): ").strip()
            
            if choice in ['1', '2', '3']:
                return choice
            print("Invalid choice. Please enter 1, 2, or 3.")
    else:
        # No existing files - default to creating new files
        return '1'


def write_all_cards_to_files(all_cloze_cards: List[str], all_basic_cards: List[str], choice: str) -> None:
    """
    Write all collected cards to files based on the user's choice.
    """
    from datetime import datetime
    
    os.makedirs("exported_cards", exist_ok=True)
    
    if choice == '1':  # Overwrite
        cloze_file = "exported_cards/cloze_cards.txt"
        basic_file = "exported_cards/basic_cards.txt"
        
        # Delete old files if they exist
        if os.path.exists(cloze_file):
            os.remove(cloze_file)
        if os.path.exists(basic_file):
            os.remove(basic_file)
            
        mode = 'w'
        
    elif choice == '2':  # Timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        cloze_file = f"exported_cards/cloze_cards_{timestamp}.txt"
        basic_file = f"exported_cards/basic_cards_{timestamp}.txt"
        mode = 'w'
        
    else:  # choice == '3' - Append
        cloze_file = "exported_cards/cloze_cards.txt"
        basic_file = "exported_cards/basic_cards.txt"
        mode = 'a'
    
    # Write cloze cards
    if all_cloze_cards:
        with open(cloze_file, mode, encoding="utf-8") as f:
            if mode == 'a' and os.path.getsize(cloze_file) > 0:
                f.write("\n")  # Add separator if appending to non-empty file
            for card in all_cloze_cards:
                f.write(f"{card}\n")
        print(f"Exported {len(all_cloze_cards)} cloze cards to {cloze_file}")
    
    # Write basic cards
    if all_basic_cards:
        with open(basic_file, mode, encoding="utf-8") as f:
            if mode == 'a' and os.path.getsize(basic_file) > 0:
                f.write("\n")  # Add separator if appending to non-empty file
            for card in all_basic_cards:
                f.write(f"{card}\n")
        print(f"Exported {len(all_basic_cards)} basic cards to {basic_file}")


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
        # Try file path as-is first, then relative to current directory
        paths_to_try = [file_path]
        
        # If path is not absolute and doesn't exist, try some common locations
        if not os.path.isabs(file_path) and not os.path.exists(file_path):
            # Try in current directory
            paths_to_try.append(os.path.join(".", file_path))
            # Try in articles directory
            paths_to_try.append(os.path.join("articles", file_path))
            # Try in parent articles directory (if we're in articles/)
            if os.path.basename(os.getcwd()) == "articles":
                paths_to_try.append(os.path.join("..", file_path))
            else:
                paths_to_try.append(os.path.join("..", "articles", file_path))
        
        file_found = False
        for try_path in paths_to_try:
            try:
                if os.path.exists(try_path):
                    with open(try_path, "r") as f:
                        urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]
                        all_urls.extend(urls)
                        print(f"Loaded {len(urls)} URLs from {try_path}")
                    file_found = True
                    break
            except Exception as e:
                continue
        
        if not file_found:
            print(f"Warning: URL file '{file_path}' not found in any of the expected locations:")
            for path in paths_to_try:
                print(f"  - {path}")
            print("Skipping.")
    
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
        "--use-cache",
        action="store_true",
        help="Use cached content for URLs to avoid repeated fetching.",
    )
    parser.add_argument(
        "--to-file",
        action="store_true",
        help="Export cards to a file instead of AnkiConnect.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Automatically overwrite existing export files without prompting (only applies with --to-file).",
    )
    parser.add_argument(
        "--custom-prompt",
        type=str,
        default="",
        help="Custom prompt to use for generating cards. If not provided, the default prompt will be used.",
    )
    parser.add_argument(
        "--allow-duplicates",
        action="store_true",
        help="Allow duplicate cards to be created even if they already exist.",
    )
    parser.add_argument(
        "--process-all",
        action="store_true",
        help="Process all articles even if they have been processed before.",
    )
    parser.add_argument(
        "--similarity-threshold",
        type=float,
        default=SIMILARITY_THRESHOLD,
        help=f"Threshold for semantic similarity when detecting duplicate cards (0.0-1.0, default: {SIMILARITY_THRESHOLD}).",
    )
    parser.add_argument(
        "--url-files",
        nargs="+",
        metavar="FILE",
        help="Additional text files containing URLs to process (one URL per line, # for comments). Files are searched in current directory, articles/ subdirectory, and parent directories. Can specify multiple files.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gpt-4o-mini",
        help="OpenAI model to use for card generation (default: gpt-4o-mini). Examples: gpt-4o, gpt-4o-mini, gpt-4-turbo, gpt-3.5-turbo.",
    )
    args = parser.parse_args()
    if not args.to_file:
        check_anki_note_model()
    check_config()

    # Read URLs from the default file
    urls = []
    
    # Determine the correct path for the default URLs file
    urls_file_path = URLS_FILE
    article_dir_path = ARTICLE_DIR
    
    # Check if we need to adjust paths based on current directory
    if not os.path.exists(ARTICLE_DIR):
        if os.path.basename(os.getcwd()) == "articles" and os.path.exists("../articles"):
            article_dir_path = "../articles"
            urls_file_path = "../articles/urls.txt"
        elif os.path.exists("../articles"):
            article_dir_path = "../articles" 
            urls_file_path = "../articles/urls.txt"
    
    try:
        if os.path.exists(urls_file_path):
            with open(urls_file_path, "r") as f:
                urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]
                print(f"Loaded {len(urls)} URLs from {urls_file_path}")
        else:
            print(f"Default URL file '{urls_file_path}' not found.")
    except Exception as e:
        print(f"Error reading default URL file '{urls_file_path}': {e}")
    
    # Read URLs from additional files if specified
    if args.url_files:
        additional_urls = read_urls_from_files(args.url_files)
        urls.extend(additional_urls)
        print(f"Total URLs loaded: {len(urls)}")
    
    local_files = []
    if os.path.exists(article_dir_path):
        local_files = [f for f in os.listdir(article_dir_path) if f.endswith(tuple(ALLOWED_EXTENSIONS)) and not f.startswith(".") and not f == os.path.basename(urls_file_path)]

    if not urls and not local_files:
        print(f"No URLs or local files found in {urls_file_path} or {article_dir_path}.")
        print(f"Please add URLs to {urls_file_path}, specify additional URL files with --url-files, or add article files to {article_dir_path}, then run the script again.")
        return

    articles = [Article(url=url) for url in urls if url.strip()]
    articles += [Article(file_path=os.path.join(article_dir_path, file)) for file in local_files if file.strip()]

    # Get file handling choice once if exporting to file
    file_handling_choice = '1'  # Default value
    if args.to_file:
        file_handling_choice = get_file_handling_choice(args.overwrite)
    
    # Collect all cards from all articles
    all_cloze_cards = []
    all_basic_cards = []
    total_cards_generated = 0

    for article in articles:
        article.fetch_content(use_cache=args.use_cache, skip_if_processed=(not args.process_all), model=args.model)

        # Skip already processed articles unless explicitly told to process all
        if article.is_processed and not args.process_all:
            print(f"Skipping \"{article.title or article.identifier}\": already processed. Use --process-all to override.")
            continue

        cloze_cards, basic_cards = [], []
        if article.text:
            cloze_cards, basic_cards = article.generate_cards(custom_prompt=args.custom_prompt, model=args.model)

        if not cloze_cards and not basic_cards:
            print(f"No cards generated for \"{article.title or article.identifier}\". Please check the article content or your custom prompt.")
            continue

        # Add article title headers to cards
        title_header = f"# {article.title or 'Untitled'}"
        
        if args.to_file:
            # Collect cards for batch file writing
            if cloze_cards:
                all_cloze_cards.append(title_header)
                all_cloze_cards.extend(cloze_cards)
            if basic_cards:
                all_basic_cards.append(title_header)
                all_basic_cards.extend(basic_cards)
            
            total_cards_generated += len(cloze_cards) + len(basic_cards)
            print(f"Generated {len(cloze_cards)} cloze cards and {len(basic_cards)} basic cards for \"{article.title or article.identifier}\"")
        else:
            # Export directly to Anki
            print(f"Exporting cards for \"{article.title or article.identifier}\"...")
            exporter = ExportCards(
                cloze_cards=cloze_cards,
                basic_cards=basic_cards,
                title=article.title or "Untitled",
                deck=args.deck,
                to_file=False,
                skip_duplicates=(not args.allow_duplicates),
                similarity_threshold=args.similarity_threshold,
            )
            exporter.export()

        # Mark the article as processed
        article.mark_as_processed(args.deck)

        print(f"Finished processing \"{article.title or article.identifier}\".")
        print("-" * 40)

    # Write all collected cards to files if using --to-file
    if args.to_file and (all_cloze_cards or all_basic_cards):
        print(f"\nWriting all {total_cards_generated} cards to files...")
        write_all_cards_to_files(all_cloze_cards, all_basic_cards, file_handling_choice)
        print("File export completed.")
    elif args.to_file:
        print("No cards were generated to export to files.")

    print("All articles processed. Check the output for any errors or warnings.")

if __name__ == "__main__":
    main()
