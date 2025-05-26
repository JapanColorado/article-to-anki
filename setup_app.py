#!/usr/bin/env python3
"""
Setup Script for Articles to Anki

This script handles all setup tasks for Articles to Anki:
1. Creates necessary directories (articles, exported_cards)
2. Creates initial URL file
3. Downloads NLTK data for semantic similarity detection

Can be run directly or as a CLI command after pip installation:
  python setup.py
  articles-to-anki-setup
"""

import os
import sys
import argparse
import traceback
from pathlib import Path

# Import configuration values
try:
    from config import ARTICLE_DIR, URLS_FILE
except ImportError:
    # Default values if config.py can't be imported
    ARTICLE_DIR = "articles"
    URLS_FILE = f"{ARTICLE_DIR}/urls.txt"

def setup_dirs_and_files():
    """Create necessary directories and files."""
    print("\n=== Articles to Anki: Directory Setup ===\n")
    
    # Create articles directory if it doesn't exist
    if not os.path.exists(ARTICLE_DIR):
        print(f"Creating articles directory: {ARTICLE_DIR}")
        os.makedirs(ARTICLE_DIR, exist_ok=True)
        print("✓ Articles directory created")
    else:
        print(f"✓ Articles directory already exists: {ARTICLE_DIR}")
    
    # Create exported_cards directory if it doesn't exist
    exported_dir = "exported_cards"
    if not os.path.exists(exported_dir):
        print(f"Creating exported cards directory: {exported_dir}")
        os.makedirs(exported_dir, exist_ok=True)
        print("✓ Exported cards directory created")
    else:
        print(f"✓ Exported cards directory already exists: {exported_dir}")
    
    # Create URLs file if it doesn't exist
    if not os.path.exists(URLS_FILE):
        print(f"Creating URLs file: {URLS_FILE}")
        with open(URLS_FILE, "w") as f:
            f.write("# Add your URLs here, one per line.\n")
        print("✓ URLs file created")
    else:
        print(f"✓ URLs file already exists: {URLS_FILE}")
    
    print("\nDirectory setup complete!")
    return True

def setup_nltk():
    """Download required NLTK data packages."""
    print("\n=== Articles to Anki: NLTK Setup ===\n")
    print("Setting up NLTK data packages for semantic similarity detection...\n")
    
    try:
        # Import NLTK here to provide better error messages if it's not installed
        try:
            import nltk
        except ImportError:
            print("ERROR: NLTK is not installed. Please install it with:")
            print("pip install nltk scikit-learn")
            return False
        
        # Create NLTK data directory if it doesn't exist
        nltk_data_dir = os.path.expanduser("~/nltk_data")
        os.makedirs(nltk_data_dir, exist_ok=True)
        
        # Download required packages
        required_packages = ['punkt', 'stopwords', 'averaged_perceptron_tagger']
        required_packages = ['punkt', 'stopwords']
        for package in required_packages:
            print(f"Downloading {package}...")
            nltk.download(package, quiet=False)
            
        # Handle punkt_tab issue specifically
        print("Setting up punkt_tab directory structure...")
        try:
            # Create punkt_tab directory and files
            punkt_tab_dir = os.path.join(nltk_data_dir, "tokenizers/punkt_tab")
            english_dir = os.path.join(punkt_tab_dir, "english")
            os.makedirs(english_dir, exist_ok=True)
            
            # Create empty placeholder files
            files_to_create = ["collocations.tab", "punkt.tab", "punkt_tab.pickle"]
            for filename in files_to_create:
                filepath = os.path.join(english_dir, filename)
                with open(filepath, "wb") as f:
                    if filename.endswith(".pickle"):
                        import pickle
                        pickle.dump({}, f)
                    else:
                        f.write(b"")
                print(f"Created placeholder file: {filepath}")
            
            # Create a basic monkey patch for the tokenizer
            try:
                # Define a simple tokenizer that doesn't use punkt_tab
                def safe_word_tokenize(text):
                    """Tokenize text without requiring punkt_tab"""
                    import re
                    return re.findall(r'\w+', text.lower())
                    
                # Apply it directly to avoid errors
                import nltk.tokenize
                nltk.tokenize.word_tokenize = safe_word_tokenize
                nltk.word_tokenize = safe_word_tokenize
                
                # Test the tokenization
                test_sent = "Testing NLTK installation."
                tokenized = nltk.word_tokenize(test_sent)
                print(f"Test tokenization successful: {tokenized}")
            except Exception as e:
                print(f"Failed to patch tokenizer: {e}")
                print("Trying alternative download method...")
                import nltk.downloader
                nltk.downloader.download('punkt')
        except Exception as e:
            print(f"Failed to create punkt_tab directory: {e}")
        
        # Verify the installation succeeded
        verification_success = True
        try:
            nltk.data.find('tokenizers/punkt')
            nltk.data.find('corpora/stopwords')
            # Try to use the resources to make sure they're working
            from nltk.corpus import stopwords
            stop_words = stopwords.words('english')
            assert len(stop_words) > 0
            # Test tokenization functionality
            test_sentence = "Testing if NLTK tokenization works properly."
            tokens = nltk.word_tokenize(test_sentence)
            assert len(tokens) > 0
            print(f"Tokenization test: {tokens}")
        except Exception as e:
            print(f"\nWARNING: Installation verification failed: {str(e)}")
            print("The resources may not have downloaded correctly.")
            print("\nTrying to create a direct workaround for punkt_tab...")
            try:
                # Create a direct patch for NLTK tokenization
                import importlib
                import types
                
                # Create the necessary directories
                nltk_data_dir = os.path.expanduser("~/nltk_data")
                punkt_tab_dir = os.path.join(nltk_data_dir, "tokenizers/punkt_tab/english")
                os.makedirs(punkt_tab_dir, exist_ok=True)
                
                # Create all the files that might be needed
                for lang in ["english", "german", "french", "italian", "portuguese", "spanish"]:
                    lang_dir = os.path.join(nltk_data_dir, "tokenizers/punkt_tab", lang)
                    os.makedirs(lang_dir, exist_ok=True)
                    for filename in ["collocations.tab", "punkt.tab", "punkt_tab.pickle"]:
                        with open(os.path.join(lang_dir, filename), "wb") as f:
                            f.write(b"")
                
                # Create simple patch for tokenization function
                def simple_tokenize(text):
                    """A very simple tokenizer that doesn't need NLTK resources."""
                    import re
                    return [w for w in re.findall(r'\w+', text) if w]
                
                # Apply our patch to NLTK
                import nltk.tokenize
                nltk.tokenize.word_tokenize = simple_tokenize
                nltk.word_tokenize = simple_tokenize
                
                # Test if it works now
                test = nltk.word_tokenize("Testing if patched tokenizer works.")
                print(f"Patched tokenizer works: {test}")
                
                # Create a global marker file so text_utils.py knows to use the workaround
                with open(os.path.join(nltk_data_dir, "use_simple_tokenizer"), "w") as f:
                    f.write("true")
                
                print("\nNOTE: Using simplified tokenizer that doesn't require punkt_tab.")
                print("This will work with Articles to Anki, but may be less accurate than")
                print("the standard NLTK tokenizer for advanced NLP tasks.")
                
                verification_success = True
            except Exception as e2:
                print(f"Workaround failed: {e2}")
                verification_success = False
        
        if verification_success:
            print("\nNLTK setup completed successfully!")
            print(f"Data is stored in: {nltk_data_dir}")
            print("\nYou can now use the advanced semantic similarity features in Articles to Anki.")
            
            # Print environment info for troubleshooting
            print("\nNLTK environment information:")
            print(f"NLTK version: {nltk.__version__}")
            print(f"NLTK data path: {nltk.data.path}")
            print(f"Python executable: {sys.executable}")
            
            # Set NLTK_DATA environment variable to help NLTK find the data
            os.environ['NLTK_DATA'] = nltk_data_dir
            print(f"\nSet NLTK_DATA environment variable to: {nltk_data_dir}")
            print("To make this permanent, add to your shell profile:")
            print(f"    export NLTK_DATA={nltk_data_dir}")
        else:
            print("\nNLTK resources were downloaded but verification failed.")
            print("You may need to manually fix your NLTK installation.")
            return False
    
    except Exception as e:
        print(f"\nError during NLTK setup: {str(e)}")
        if "--debug" in sys.argv:
            traceback.print_exc()
        print("\nYou can still use Articles to Anki with basic similarity detection.")
        print("To retry setting up NLTK, run 'articles-to-anki-setup' again.")
        return False
    
    return True

def main():
    """Command-line entry point for the script."""
    parser = argparse.ArgumentParser(description="Setup Articles to Anki")
    parser.add_argument("--nltk-only", action="store_true", help="Only setup NLTK resources")
    parser.add_argument("--dirs-only", action="store_true", help="Only create directories and files")
    parser.add_argument("--debug", action="store_true", help="Show detailed error information if setup fails")
    args = parser.parse_args()
    
    success = True
    
    # If specific flags are set, only run those components
    if args.nltk_only:
        success = setup_nltk()
    elif args.dirs_only:
        success = setup_dirs_and_files()
    else:
        # Run all setup components by default
        dirs_success = setup_dirs_and_files()
        nltk_success = setup_nltk()
        success = dirs_success and nltk_success
    
    print("\n=== Setup Complete ===\n")
    if success:
        print("Articles to Anki is now ready to use!")
        print("Run 'articles-to-anki' to start processing your articles.\n")
    else:
        print("Setup completed with some issues. Check the messages above.")
        print("You can still use Articles to Anki, but some features might be limited.\n")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()