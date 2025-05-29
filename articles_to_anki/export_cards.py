import os
import requests
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Tuple
from articles_to_anki.config import ANKICONNECT_URL, BASIC_MODEL_NAME, CLOZE_MODEL_NAME, SIMILARITY_THRESHOLD, get_card_database, save_card_database
from articles_to_anki.text_utils import are_cards_similar

class ExportCards:
    """
    Handles the export of Anki cards to either AnkiConnect or a file.

    Attributes:
        cloze_cards (List[str]): List of cloze cards to export.
        basic_cards (List[str]): List of basic cards to export.
        title (str): Title of the article.
        deck (str): Name of the Anki deck.
        to_file (bool): Flag indicating whether to export to a file or AnkiConnect.
        skip_duplicates (bool): Whether to skip duplicate cards.
        auto_overwrite (bool): Whether to automatically overwrite existing export files without prompting.
        duplicate_file (str): Path to the file storing card hashes.
    """

    def __init__(self, cloze_cards: List[str], basic_cards: List[str], title: str, deck: str, to_file: bool = False,
                 skip_duplicates: bool = True, similarity_threshold: float = SIMILARITY_THRESHOLD, auto_overwrite: bool = False):
        self.cloze_cards = cloze_cards
        self.basic_cards = basic_cards
        self.title = title
        self.deck = deck
        self.to_file = to_file
        self.skip_duplicates = skip_duplicates
        self.similarity_threshold = similarity_threshold
        self.auto_overwrite = auto_overwrite
        self.cards_exported = 0
        self.cards_skipped = 0
        # Load the card database
        self.card_database = get_card_database()
        # Process existing cards for comparison
        self.existing_cards = []  # List of tuples (card_content, is_cloze)

    def _preload_existing_cards(self):
        """
        Preloads existing cards from the database for similarity comparison.
        """
        self.existing_cards = []

        if "cards" not in self.card_database:
            return

        for card in self.card_database["cards"]:
            card_type = card.get("type", "basic")
            is_cloze = (card_type == "cloze")

            if is_cloze:
                front = card.get("front", "")
                self.existing_cards.append(((front, ""), True))
            else:  # basic
                front = card.get("front", "")
                back = card.get("back", "")
                self.existing_cards.append(((front, back), False))



    def _is_duplicate(self, card_content: Tuple[str, str], is_cloze: bool) -> bool:
        """
        Checks if a card is semantically similar to any existing card.

        Args:
            card_content (Tuple[str, str]): For cloze cards, (text, ""). For basic, (front, back).
            is_cloze (bool): Whether this is a cloze card.

        Returns:
            bool: True if a similar card exists, False otherwise.
        """
        if not self.skip_duplicates:
            return False

        # Safety check for empty content
        if not card_content or not card_content[0]:
            return False

        # Preload cards if not already done
        if not self.existing_cards:
            self._preload_existing_cards()

        try:
            # Check for semantic similarity with existing cards
            for existing_content, existing_is_cloze in self.existing_cards:
                # Only compare cards of the same type (cloze to cloze, basic to basic)
                if is_cloze == existing_is_cloze:
                    try:
                        if are_cards_similar(card_content, existing_content, is_cloze, self.similarity_threshold):
                            return True
                    except Exception as e:
                        # Don't let similarity errors fail the whole process
                        print(f"Error comparing cards: {e}")
                        continue
        except Exception as e:
            print(f"Error during duplicate detection: {e}")
            print("Continuing without duplicate detection for this card.")
            return False

        return False

    def export(self):
        """
        Export the cards to Anki or a file based on the configuration.
        """
        self.cards_exported = 0
        self.cards_skipped = 0

        try:
            # Preload existing cards for similarity comparison
            if self.skip_duplicates:
                self._preload_existing_cards()

            if self.to_file:
                self._handle_file_export()
            else:
                for card in self.cloze_cards:
                    try:
                        # Clean up malformed cloze cards - extract only the cloze part
                        front = self._clean_cloze_card(card)
                        if front:
                            self._export_to_anki(front, "", True)
                    except Exception as e:
                        print(f"Error exporting cloze card: {e}")
                        continue

                for card in self.basic_cards:
                    try:
                        # Clean up basic cards and extract front/back
                        front, back = self._clean_basic_card(card)
                        if front:
                            self._export_to_anki(front, back, False)
                    except Exception as e:
                        print(f"Error exporting basic card: {e}")
                        continue

            # Save updated card database
            try:
                save_card_database(self.card_database)
            except Exception as e:
                print(f"Warning: Could not save card database: {e}")

            print(f"Exported {self.cards_exported} cards ({self.cards_skipped} duplicates skipped).")
        except Exception as e:
            print(f"Error during export: {e}")
            print(f"Successfully exported {self.cards_exported} cards before the error.")

    def _export_to_anki(self, front: str, back: str, is_cloze: bool) -> None:
        """
        Exports a single card to Anki via AnkiConnect.
        """
        # Skip empty cards
        if not front.strip():
            print("Skipping empty card")
            return

        # Check for duplicates if needed
        card_content = (front, back) if not is_cloze else (front, "")

        try:
            if self.skip_duplicates and self._is_duplicate(card_content, is_cloze):
                self.cards_skipped += 1
                return
        except Exception as e:
            print(f"Error checking for duplicates: {e}")
            print("Continuing with export")

        # Validate cloze cards have proper cloze markers
        if is_cloze and "{{c" not in front:
            # Try to fix common issues with cloze formatting
            if "{{" in front and "}}" in front:
                # Missing 'c1::' format, try to fix
                front = front.replace("{{", "{{c1::")
                print("Fixed missing cloze numbering in card")
            else:
                print(f"Warning: Cloze card doesn't have proper cloze markers: {front[:50]}...")
                # Check if this might be a PDF-formatted card that lost its markers
                if self.title.endswith('.pdf'):
                    # Try to recover by finding keywords to cloze
                    words = front.split()
                    for i, word in enumerate(words):
                        if len(word) > 4 and word.lower() not in ["this", "that", "these", "those"]:
                            words[i] = f"{{{{c1::{word}}}}}"
                            front = " ".join(words)
                            print(f"Attempted to fix PDF cloze formatting: {front[:50]}...")
                            break
                    if "{{c" not in front:
                        print("Error: Cloze card is missing cloze markers ({{c1::...}})")
                        return
                else:
                    print("Error: Cloze card is missing cloze markers ({{c1::...}})")
                    return

        model_name = CLOZE_MODEL_NAME if is_cloze else BASIC_MODEL_NAME
        # Sanitize tags to avoid AnkiConnect errors
        safe_tag = self.title.replace(" ", "_").replace("/", "_")
        # Remove any characters that might cause issues in tags
        safe_tag = ''.join(c for c in safe_tag if c.isalnum() or c in '_-')
        if not safe_tag:
            safe_tag = "imported_card"

        # Prepare the note
        note = {
            "deckName": self.deck,
            "modelName": model_name,
            "fields": {},  # Will be set below
            "options": {
                "allowDuplicate": False
            },
            "tags": [safe_tag]
        }

        # Set appropriate fields based on card type
        if is_cloze:
            # Cloze model usually only needs 'Text' field
            note["fields"] = {"Text": front}
            # Add Extra field if available in the model
            if back:
                note["fields"]["Extra"] = back
        else:
            # Basic model expects 'Front' and 'Back'
            note["fields"] = {"Front": front, "Back": back}
        payload = {
            "action": "addNote",
            "version": 6,
            "params": {
                "note": note
            }
        }
        try:
            response = requests.post(ANKICONNECT_URL, json=payload, timeout=30)
            response.raise_for_status()
            result = response.json()
            if result.get("error") is not None:
                error_msg = result['error']
                # Handle specific error cases
                if "duplicate" in error_msg.lower():
                    print(f"Skipping duplicate card: {front[:50]}...")
                    self.cards_skipped += 1
                    return
                elif "empty" in error_msg.lower():
                    print(f"Card has empty fields: {front[:50]}...")
                    return
                else:
                    # Log detailed information for debugging
                    print(f"AnkiConnect error: {error_msg}")
                    print(f"Card content: {front[:100]}{'...' if len(front) > 100 else ''}")

                    # Check for missing cloze markers in cloze cards
                    if is_cloze and "{{c" not in front:
                        print("Error: Cloze card is missing cloze markers ({{c1::...}})")
                        return

                    # Try to diagnose other common issues
                    if len(front) > 1000:
                        print("Warning: Card front text is very long (over 1000 chars)")
            else:
                # Successfully added note, store the card in our database
                card_data = {
                    "id": str(uuid.uuid4()),
                    "type": "cloze" if is_cloze else "basic",
                    "front": front,
                    "back": back if not is_cloze else "",
                    "deck": self.deck,
                    "title": self.title
                }
                # Add to existing cards list for duplicate detection
                self.existing_cards.append((card_content, is_cloze))
                # Add to database
                if "cards" not in self.card_database:
                    self.card_database["cards"] = []
                self.card_database["cards"].append(card_data)
                self.cards_exported += 1
        except requests.exceptions.Timeout:
            print("AnkiConnect request timed out. Check if Anki is running.")
        except requests.exceptions.ConnectionError:
            print("Connection error. Make sure Anki is running with AnkiConnect addon.")
        except Exception as e:
            print(f"Failed to export card to Anki: {e}")
            # Print some debugging information
            print(f"Card type: {'Cloze' if is_cloze else 'Basic'}")
            print(f"Card front length: {len(front)} characters")

    def _handle_file_export(self) -> None:
        """Handles file export with user prompts for existing files."""
        os.makedirs("exported_cards", exist_ok=True)
        
        # Check if we have any cards to export
        has_cloze = self.cloze_cards and any(card.strip() for card in self.cloze_cards)
        has_basic = self.basic_cards and any(card.strip() for card in self.basic_cards)
        
        if not has_cloze and not has_basic:
            print("No cards to export.")
            return
        
        # Check for existing files only for card types we're actually exporting
        cloze_file = "exported_cards/cloze_cards.txt"
        basic_file = "exported_cards/basic_cards.txt"
        
        files_exist = []
        if has_cloze and os.path.exists(cloze_file):
            files_exist.append(("cloze", cloze_file))
        if has_basic and os.path.exists(basic_file):
            files_exist.append(("basic", basic_file))
        
        if files_exist:
            if self.auto_overwrite:
                choice = '1'  # Auto-overwrite mode
                print(f"\nExisting export files found - automatically overwriting:")
                for file_type, file_path in files_exist:
                    print(f"  - {file_path}")
            else:
                print(f"\nExisting export files found:")
                for file_type, file_path in files_exist:
                    print(f"  - {file_path}")
                
                while True:
                    choice = input("\nChoose an option:\n1. Overwrite existing files\n2. Create new files with timestamp\n3. Append to existing files\nEnter choice (1/2/3): ").strip()
                    
                    if choice in ['1', '2', '3']:
                        break
                    print("Invalid choice. Please enter 1, 2, or 3.")
            
            if choice == '1':
                # Overwrite mode
                if has_cloze:
                    self._export_to_file(self.cloze_cards, self.title, True, cloze_file, 'w')
                if has_basic:
                    self._export_to_file(self.basic_cards, self.title, False, basic_file, 'w')
            elif choice == '2':
                # New files with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                if has_cloze:
                    new_cloze_file = f"exported_cards/cloze_cards_{timestamp}.txt"
                    self._export_to_file(self.cloze_cards, self.title, True, new_cloze_file, 'w')
                if has_basic:
                    new_basic_file = f"exported_cards/basic_cards_{timestamp}.txt"
                    self._export_to_file(self.basic_cards, self.title, False, new_basic_file, 'w')
            else:  # choice == '3'
                # Append mode
                if has_cloze:
                    self._export_to_file(self.cloze_cards, self.title, True, cloze_file, 'a')
                if has_basic:
                    self._export_to_file(self.basic_cards, self.title, False, basic_file, 'a')
        else:
            # No existing files, create new ones
            if has_cloze:
                self._export_to_file(self.cloze_cards, self.title, True, cloze_file, 'w')
            if has_basic:
                self._export_to_file(self.basic_cards, self.title, False, basic_file, 'w')

    def _export_to_file(self, cards: List[str], title: str, is_cloze: bool, file_path: str, mode: str = 'a') -> None:
        """Exports cards to a file in the 'exported_cards' directory."""
        try:
            # Filter out empty cards before processing
            non_empty_cards = [card for card in cards if card.strip()]
            if not non_empty_cards:
                print(f"No non-empty {'cloze' if is_cloze else 'basic'} cards to export.")
                return
                
            exported_count = 0

            with open(file_path, mode, encoding="utf-8") as f:
                f.write(f"# {title}\n")
                for card in non_empty_cards:
                    try:

                        # For processing, parse the card content
                        if is_cloze:
                            front = self._clean_cloze_card(card)
                            card_content = (front, "")
                        else:
                            front, back = self._clean_basic_card(card)
                            card_content = (front, back)

                        # Check for semantic duplicates
                        try:
                            if self.skip_duplicates and self._is_duplicate(card_content, is_cloze):
                                self.cards_skipped += 1
                                continue
                        except Exception as e:
                            print(f"Error checking for duplicates: {e}")
                            print("Continuing with export")

                        # Write the cleaned card content to file
                        # Replace spaces with underscores in title for tags
                        title_tag = title.replace(" ", "_")
                        if is_cloze:
                            # Use the cleaned cloze card front with extra empty field and title tag
                            f.write(f"{front} ; ; {title_tag}\n")
                        else:
                            # Use the cleaned basic card front and back with title tag
                            if back:
                                f.write(f"{front} ; {back} ; {title_tag}\n")
                            else:
                                f.write(f"{front} ;  ; {title_tag}\n")

                        # Store the card in our database
                        front, back = card_content
                        if front:  # Only store non-empty cards
                            card_data = {
                                "id": str(uuid.uuid4()),
                                "type": "cloze" if is_cloze else "basic",
                                "front": front,
                                "back": back,
                                "title": title
                            }

                            # Add to existing cards list for duplicate detection
                            self.existing_cards.append((card_content, is_cloze))

                            # Add to database
                            if "cards" not in self.card_database:
                                self.card_database["cards"] = []
                            self.card_database["cards"].append(card_data)

                            exported_count += 1
                            self.cards_exported += 1
                    except Exception as e:
                        print(f"Error processing card: {e}")
                        continue

            print(f"Exported {exported_count} {'cloze' if is_cloze else 'basic'} cards to {file_path}.")
        except Exception as e:
            print(f"Error exporting cards to file: {e}")

    def _clean_cloze_card(self, card: str) -> str:
        """Clean up malformed cloze cards and extract the cloze content."""
        card = card.strip()
        if not card:
            return ""
        
        # Remove title suffix if present (new format: front ; ; title)
        if " ; ; " in card:
            card = card.split(" ; ; ")[0].strip()
        elif " ; ; ; " in card:
            # Handle old format with triple separator
            card = card.split(" ; ; ; ")[0].strip()
        
        # Remove any remaining trailing semicolons and spaces
        card = card.rstrip(" ;")
        
        # Extract only the cloze part before any remaining semicolon
        if " ; " in card:
            card = card.split(" ; ")[0].strip()
        
        # Validate it's actually a cloze card
        if "{{c" not in card or "}}" not in card:
            return ""
        
        return card

    def _clean_basic_card(self, card: str) -> tuple[str, str]:
        """Clean up basic cards and extract front and back."""
        card = card.strip()
        if not card:
            return "", ""
        
        # Handle new format: front ; back ; title
        parts = card.split(" ; ")
        if len(parts) >= 3:
            # New format with title tag - take first two parts
            front = parts[0].strip()
            back = parts[1].strip()
            # Handle case where back field is empty (front ; ; title)
            # In this case, parts[1] will be empty string
            return front, back
        elif " ; ; ; " in card:
            # Old format with multiple separators
            parts = card.split(" ; ; ; ")
            card = parts[0].strip()
        
        # Split on the first " ; " to get front and back
        if " ; " in card:
            parts = card.split(" ; ", 1)
            front = parts[0].strip()
            back = parts[1].strip() if len(parts) > 1 else ""
            
            # Remove any trailing semicolons from back
            back = back.rstrip(" ;")
            
            return front, back
        else:
            # No separator found, treat whole thing as front
            return card.rstrip(" ;"), ""
