import os
import requests
import json
from datetime import datetime
import uuid
from typing import List, Dict, Any, Tuple
from config import ANKICONNECT_URL, BASIC_MODEL_NAME, CLOZE_MODEL_NAME, SIMILARITY_THRESHOLD, get_card_database, save_card_database
from text_utils import are_cards_similar

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
        duplicate_file (str): Path to the file storing card hashes.
    """

    def __init__(self, cloze_cards: List[str], basic_cards: List[str], title: str, deck: str, to_file: bool = False,
                 skip_duplicates: bool = True, similarity_threshold: float = SIMILARITY_THRESHOLD):
        self.cloze_cards = cloze_cards
        self.basic_cards = basic_cards
        self.title = title
        self.deck = deck
        self.to_file = to_file
        self.skip_duplicates = skip_duplicates
        self.similarity_threshold = similarity_threshold
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
                self._export_to_file(self.cloze_cards, self.title, True)
                self._export_to_file(self.basic_cards, self.title, False)
            else:
                for card in self.cloze_cards:
                    try:
                        # For cloze, split either on "; " or ";;" to handle both formats
                        if ";;" in card:
                            front = card.split(";;", 1)[0].strip()
                        else:
                            front = card.split(";", 1)[0].strip()
                        self._export_to_anki(front, "", True)
                    except Exception as e:
                        print(f"Error exporting cloze card: {e}")
                        continue

                for card in self.basic_cards:
                    try:
                        # For basic, split on ' ; ' (with spaces)
                        if " ; " in card:
                            front, back = card.split(" ; ", 1)
                        else:
                            front, back = card, ""
                        self._export_to_anki(front.strip(), back.strip(), False)
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
                    "title": self.title,
                    "timestamp": datetime.now().isoformat()
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

    def _export_to_file(self, cards: List[str], title: str, is_cloze: bool) -> None:
        """Exports cards to a file in the 'exported_cards' directory."""
        try:
            os.makedirs("exported_cards", exist_ok=True)
            timestamp = datetime.now().strftime("%Y-%m-%d-%H")
            file_path = f"exported_cards/{timestamp}_{'cloze' if is_cloze else 'basic'}_cards.txt"
            exported_count = 0

            with open(file_path, "a", encoding="utf-8") as f:
                f.write(f"# {title}\n")
                for card in cards:
                    try:
                        # Skip empty cards
                        if not card.strip():
                            continue

                        # For processing, parse the card content
                        if is_cloze:
                            card_content = (card, "")
                        else:
                            if " ; " in card:
                                front, back = card.split(" ; ", 1)
                                card_content = (front.strip(), back.strip())
                            else:
                                card_content = (card, "")

                        # Check for semantic duplicates
                        try:
                            if self.skip_duplicates and self._is_duplicate(card_content, is_cloze):
                                self.cards_skipped += 1
                                continue
                        except Exception as e:
                            print(f"Error checking for duplicates: {e}")
                            print("Continuing with export")

                        # Write the card to file without appending the title
                        # Check if card already contains proper formatting
                        card_to_write = card

                        # For cloze cards, ensure they end with title
                        if is_cloze:
                            # If card doesn't have formatting or title information
                            if not card.endswith(f" {title} ;") and not card.endswith(f" ; {title} ;"):
                                # If card has proper " ; ;" ending
                                if card.strip().endswith(" ; ;"):
                                    card_to_write = f"{card} {title} ;"
                                # If card doesn't have proper ending at all
                                else:
                                    card_to_write = f"{card} ; ; {title} ;"
                        # For basic cards
                        else:
                            # Most basic cards should already have formatting
                            if not card.endswith(";"):
                                card_to_write = f"{card} ;"

                            # Add title if not already present
                            if title not in card:
                                card_to_write = f"{card_to_write} {title} ;"

                        f.write(f"{card_to_write}\n")

                        # Store the card in our database
                        front, back = card_content
                        card_data = {
                            "id": str(uuid.uuid4()),
                            "type": "cloze" if is_cloze else "basic",
                            "front": front,
                            "back": back,
                            "title": title,
                            "timestamp": datetime.now().isoformat()
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
