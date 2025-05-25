import os
import argparse
from config import OPENAI_API_KEY, URLS_FILE, ARTICLE_DIR, ALLOWED_EXTENSIONS
from articles import Article
from export_cards import ExportCards

def check_config() -> None:
    """
    Checks if the necessary configuration is set up correctly.
    Raises an error if the OPENAI_API_KEY is not set, or if the ARTICLE_DIR or URLS_FILE does not exist.

    Raises:
        ValueError: If OPENAI_API_KEY is not set.
        FileNotFoundError: If ARTICLE_DIR or URLS_FILE does not exist.
    """
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY must be set in the environment variables(or in config.py). Use the following command:\nexport OPENAI_API_KEY='your_api_key'")
    if not os.path.exists(ARTICLE_DIR):
        print(f"Directory {ARTICLE_DIR} does not exist. If you want to use a different directory, please set the ARTICLE_DIR variable in config.py.")
        make_directory = input(f"Do you want to create the directory {ARTICLE_DIR}? (y/n): ").strip().lower()
        if make_directory != 'y':
            raise FileNotFoundError(f"Directory {ARTICLE_DIR} does not exist. Please create it or set a different directory in config.py.")
        print(f"Creating directory {ARTICLE_DIR}...")
        os.makedirs(ARTICLE_DIR)
        print(f"Please add your article files to {ARTICLE_DIR} and run the script again.")
        return
    if not os.path.exists(URLS_FILE):
        print(f"File {URLS_FILE} does not exist. If you want to use a different file, please set the URLS_FILE variable in config.py.")
        make_file = input(f"Do you want to create the file {URLS_FILE}? (y/n): ").strip().lower()
        if make_file != 'y':
            raise FileNotFoundError(f"File {URLS_FILE} does not exist. Please create it or set a different file in config.py.")
        print(f"Creating file {URLS_FILE}...")
        with open(URLS_FILE, "w") as f:
            f.write("# Add your URLs here, one per line.\n")
        print(f"Created file for URLs at {URLS_FILE}. Please add your URLs and run the script again.")
        return

def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch articles and export Anki cards.")
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

    args = parser.parse_args()

    check_config()

    with open(URLS_FILE, "r") as f:
        urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    local_files = [f for f in os.listdir(ARTICLE_DIR) if f.endswith(tuple(ALLOWED_EXTENSIONS)) and not f.startswith(".") and not f == URLS_FILE.split("/")[-1]]

    if not urls and not local_files:
        print(f"No URLs or local files found in {URLS_FILE} or {ARTICLE_DIR}. Please add URLs or local files or check config.py, and then run the script again.")
        return
    
    articles = [Article(url=url) for url in urls if url.strip()]
    articles += [Article(file_path=os.path.join(ARTICLE_DIR, file)) for file in local_files if file.strip()]
    
    for article in articles:
        article.fetch_content(use_cache=args.use_cache)
    
        cloze_cards, basic_cards = [], []
        if article.text:
            cloze_cards, basic_cards = article.generate_cards(custom_prompt=args.custom_prompt)
        
        if not cloze_cards and not basic_cards:
            print(f"No cards generated for \"{article.title}\". Please check the article content or your custom prompt.")
            continue

        print(f"Exporting {len(cloze_cards)} cloze cards and {len(basic_cards)} basic cards for {article.title}.")
        
        exporter = ExportCards(
            cloze_cards=cloze_cards,
            basic_cards=basic_cards,
            title=article.title or "Untitled",
            deck=args.deck,
            to_file=args.to_file,
        )
        exporter.export()

        print(f"Finished processing \"{article.title}\".")
        print("-" * 40)
        
    print("All articles processed. Check the output for any errors or warnings.")

if __name__ == "__main__":
    main()
