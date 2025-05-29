import re
import string
import os
import sys
from typing import List, Set, Optional
from collections import Counter

# Define simple English stopwords
SIMPLE_STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "if", "because", "as", "what",
    "when", "where", "how", "who", "which", "this", "that", "these", "those",
    "then", "just", "so", "than", "such", "both", "through", "about", "for",
    "is", "was", "are", "were", "be", "been", "being", "have", "has", "had",
    "having", "do", "does", "did", "doing", "to", "from", "of", "at", "in",
    "on", "by", "with", "about", "against", "between", "into", "during",
    "before", "after", "above", "below", "over", "under", "again", "further",
    "then", "once", "here", "there", "all", "any", "both", "each", "few",
    "more", "most", "other", "some", "such", "no", "nor", "not", "only",
    "own", "same", "so", "than", "too", "very", "s", "t", "will", "can"
}

# Try to import advanced NLP libraries for better similarity detection
# If not available, fall back to simple implementations
USE_ADVANCED_NLP = False
vectorizer = None
stemmer = None
stop_words = set()

# Define simple helper functions
def simple_word_tokenize(text):
    """Simple word tokenizer that doesn't depend on NLTK"""
    import re
    # More robust tokenization that preserves words with apostrophes
    tokens = []
    # First split on whitespace and punctuation except apostrophes
    for word in re.findall(r"[a-zA-Z0-9_\'\-]+", text.lower()):
        # Further clean up the word
        word = word.strip("'\".,;:!?()-")
        if word:
            tokens.append(word)
    return tokens

def simple_stem(word):
    """Simple stemmer that just returns the word"""
    return word

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    import nltk

    # Set a recursion limit for safe tokenization
    sys.setrecursionlimit(1000)  # Default is typically 1000
    
    # Initialize NLTK with required resources
    try:
        # Check if the required NLTK data is available
        try:
            nltk.data.find('tokenizers/punkt')
            nltk.data.find('corpora/stopwords')
            
            # Manually create punkt_tab directory if needed
            nltk_data_dir = os.path.expanduser("~/nltk_data")
            punkt_tab_dir = os.path.join(nltk_data_dir, "tokenizers/punkt_tab/english")
            if not os.path.exists(punkt_tab_dir):
                os.makedirs(punkt_tab_dir, exist_ok=True)
                # Create empty placeholder files
                with open(os.path.join(punkt_tab_dir, "collocations.tab"), "wb") as f:
                    f.write(b"")
            
            # Define our own simple tokenizer to avoid recursion issues
            nltk.tokenize.word_tokenize = simple_word_tokenize
            nltk.word_tokenize = simple_word_tokenize

            # Now import these resources
            from nltk.corpus import stopwords
            from nltk.stem import PorterStemmer

            # Initialize stemmer and stopwords
            stemmer = PorterStemmer()
            stop_words = set(stopwords.words('english'))

            # Vectorizer for similarity calculation
            vectorizer = TfidfVectorizer(min_df=1, stop_words='english')

            USE_ADVANCED_NLP = True
            print("Using advanced NLP libraries for similarity detection.")

        except (LookupError, ImportError) as e:
            print(f"\nNLTK resources error: {e}")
            print("To enable advanced similarity detection:")
            print("1. Run 'articles-to-anki-fix-nltk' in your terminal, or")
            print("2. Run 'articles-to-anki-setup --nltk-only'")
            print("\nFalling back to basic similarity detection for now.\n")
            USE_ADVANCED_NLP = False
    except ImportError as e:
        print(f"NLTK module error: {e}. Using basic text similarity detection instead.")
        USE_ADVANCED_NLP = False
except ImportError:
    print("Advanced NLP libraries not found. Using basic text similarity detection instead.")
    print("To enable advanced similarity detection, install the required packages:")
    print("pip install scikit-learn nltk")


def normalize_text(text: str) -> str:
    """
    Normalize text by removing punctuation, converting to lowercase,
    removing stop words, and stemming (if available).

    Args:
        text (str): The text to normalize.

    Returns:
        str: Normalized text.
    """
    # Safety check
    if not text:
        return ""
        
    try:
        # Convert to lowercase
        text = text.lower()

        # Remove punctuation and special characters (but preserve apostrophes)
        text = re.sub(r'[^\w\s\']', ' ', text)

        # Replace multiple spaces with a single space
        text = re.sub(r'\s+', ' ', text)
    except Exception:
        # Ultra-safe fallback if regex fails
        text = text.lower()

    global USE_ADVANCED_NLP, stemmer, stop_words
    
    try:
        if USE_ADVANCED_NLP and stemmer is not None:
            # Use advanced processing
            try:
                # Use simple tokenization
                tokens = simple_word_tokenize(text)

                # Apply stemming and stopword removal
                tokens = [stemmer.stem(token) for token in tokens if token not in stop_words]
            except Exception as e:
                print(f"Advanced text processing failed: {e}")
                USE_ADVANCED_NLP = False
                # Fall back to basic processing
                tokens = simple_word_tokenize(text)
                tokens = [token for token in tokens if token not in SIMPLE_STOPWORDS]
        else:
            # Use basic processing
            tokens = simple_word_tokenize(text)
            tokens = [token for token in tokens if token not in SIMPLE_STOPWORDS]
    except Exception:
        # Ultimate fallback if all tokenization fails
        tokens = text.split()
    
    # Join tokens back into a string (with safety check)
    if not tokens:
        return text.lower()
    return ' '.join(tokens)

def extract_cloze_content(cloze_text: str) -> str:
    """
    Extract content from cloze text, removing the cloze markers.

    Args:
        cloze_text (str): Text with cloze markers like {{c1::text}}

    Returns:
        str: Text with cloze markers replaced by their content
    """
    # Replace cloze markers like {{c1::text}} with just 'text'
    return re.sub(r'\{\{c\d+::(.+?)\}\}', r'\1', cloze_text)

def calculate_similarity(text1: str, text2: str) -> float:
    """
    Calculate the similarity between two text strings.
    Uses TF-IDF cosine similarity if advanced libraries are available,
    or a simpler Jaccard similarity if not.

    Args:
        text1 (str): First text string.
        text2 (str): Second text string.

    Returns:
        float: Similarity score between 0.0 and 1.0.
    """
    global USE_ADVANCED_NLP, vectorizer
    
    # Safety check for empty inputs
    if not text1 or not text2:
        return 0.0

    # Try advanced similarity if enabled
    if USE_ADVANCED_NLP:
        try:
            # Check if vectorizer is available
            if vectorizer is None:
                USE_ADVANCED_NLP = False
                return _calculate_jaccard_similarity(text1, text2)
            
            # Try TF-IDF similarity
            from sklearn.metrics.pairwise import cosine_similarity
            tfidf_matrix = vectorizer.fit_transform([text1, text2])
            return cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        except Exception as e:
            # Handle any errors with vectorizer
            print(f"Error calculating advanced similarity: {e}")
            print("Using basic similarity detection instead.")
            USE_ADVANCED_NLP = False  # Disable for future calls
            return _calculate_jaccard_similarity(text1, text2)
    
    # Use basic similarity
    return _calculate_jaccard_similarity(text1, text2)

def _calculate_jaccard_similarity(text1: str, text2: str) -> float:
    """
    Calculate the Jaccard similarity between two text strings.

    Args:
        text1 (str): First text string.
        text2 (str): Second text string.

    Returns:
        float: Similarity score between 0.0 and 1.0.
    """
    # Use our safe tokenizer to get words
    try:
        words1 = set(simple_word_tokenize(text1))
        words2 = set(simple_word_tokenize(text2))
    except Exception:
        # Ultra-safe fallback if tokenization fails
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

    # Safety check for empty sets
    if not words1 or not words2:
        return 0.0

    # Calculate Jaccard similarity: intersection / union
    try:
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        if union == 0:
            return 0.0
            
        similarity = intersection / union
    except Exception:
        # Last resort similarity measure
        return 0.1 if any(w in text2.lower() for w in text1.lower().split()) else 0.0

    # Enhance with n-gram overlap for better accuracy
    try:
        if len(text1) > 3 and len(text2) > 3:
            # Consider 3-character sequences
            ngrams1 = set(text1[i:i+3] for i in range(len(text1) - 2))
            ngrams2 = set(text2[i:i+3] for i in range(len(text2) - 2))

            if ngrams1 and ngrams2:
                ngram_intersection = len(ngrams1.intersection(ngrams2))
                ngram_union = len(ngrams1.union(ngrams2))
                
                if ngram_union > 0:
                    ngram_similarity = ngram_intersection / ngram_union
                    # Weighted combination
                    similarity = (similarity * 0.7) + (ngram_similarity * 0.3)
    except Exception:
        # If n-gram calculation fails, just use the basic similarity
        pass

    return similarity

def normalize_cloze_card(cloze_text: str) -> str:
    """
    Normalize a cloze card by extracting content and normalizing text.

    Args:
        cloze_text (str): The cloze card text with cloze markers.

    Returns:
        str: Normalized text with cloze markers removed.
    """
    extracted = extract_cloze_content(cloze_text)
    return normalize_text(extracted)

def normalize_basic_card(front: str, back: str) -> tuple[str, str]:
    """
    Normalize a basic card's front and back.

    Args:
        front (str): The front (question) text.
        back (str): The back (answer) text.

    Returns:
        tuple[str, str]: Normalized front and back texts.
    """
    return normalize_text(front), normalize_text(back)

def are_cards_similar(card1: tuple[str, str], card2: tuple[str, str],
                     is_cloze: bool, threshold: float = 0.85) -> bool:
    """
    Determine if two cards are semantically similar.

    Args:
        card1 (tuple[str, str]): First card as (content, "") for cloze or (front, back) for basic.
        card2 (tuple[str, str]): Second card as (content, "") for cloze or (front, back) for basic.
        is_cloze (bool): Whether these are cloze cards.
        threshold (float): Similarity threshold to consider cards as duplicates.

    Returns:
        bool: True if cards are similar above the threshold, False otherwise.
    """
    if is_cloze:
        # For cloze cards, compare the normalized text (with cloze markers removed)
        text1 = normalize_cloze_card(card1[0])
        text2 = normalize_cloze_card(card2[0])
        return calculate_similarity(text1, text2) >= threshold
    else:
        # For basic cards, compare the normalized question (front)
        # and optionally the answer if front is very similar
        front1, back1 = normalize_basic_card(card1[0], card1[1])
        front2, back2 = normalize_basic_card(card2[0], card2[1])

        # Check front similarity first
        front_similarity = calculate_similarity(front1, front2)
        if front_similarity >= threshold:
            # If fronts are very similar, cards are considered similar
            return True

        # If fronts are moderately similar, also check the backs
        if front_similarity >= threshold * 0.7:
            back_similarity = calculate_similarity(back1, back2)
            # Calculate weighted average with more weight on front
            combined_similarity = (front_similarity * 0.7) + (back_similarity * 0.3)
            return combined_similarity >= threshold

        return False
