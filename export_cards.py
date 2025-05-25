import os
import requests
from datetime import datetime
from typing import List
from config import ANKICONNECT_URL

class ExportCards:
    """
    Handles the export of Anki cards to either AnkiConnect or a file.
    
    Attributes:
        cloze_cards (List[str]): List of cloze cards to export.
        basic_cards (List[str]): List of basic cards to export.
        title (str): Title of the article.
        deck (str): Name of the Anki deck.
        to_file (bool): Flag indicating whether to export to a file or AnkiConnect.
    """
    
    def __init__(self, cloze_cards: List[str], basic_cards: List[str], title: str, deck: str, to_file: bool = False):
        self.cloze_cards = cloze_cards
        self.basic_cards = basic_cards
        self.title = title
        self.deck = deck
        self.to_file = to_file

    def export(self):
        """
        Export the cards to Anki or a file based on the configuration.
        """
        if self.to_file:
            self._export_to_file(self.cloze_cards, self.title, True)
            self._export_to_file(self.basic_cards, self.title, False)
        
        else:
            for card in self.cloze_cards:
                front, back = card.split(" ; ")
                self._export_to_anki(front, back, True)
            for card in self.basic_cards:
                self._export_to_anki(card, self.title, False)
        print(f"Exported {len(self.cloze_cards)} cloze cards and {len(self.basic_cards)} basic cards.")
    
    def _export_to_anki(self, front: str, back: str, is_cloze: bool) -> None:
        note = {
            "deckName": self.deck,
            "modelName": "Basic" if not is_cloze else "Cloze",
            "fields": {"Front": front, "Back": back},
            "tags": ["article->anki", f"{self.title}"],
        }
        if is_cloze:
            note["fields"]["Text"] = front
        payload = {"action": "addNote", "version": 6, "note": note}
        try:
            response = requests.post(ANKICONNECT_URL, json=payload, timeout=15)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Failed to add card: {e}. Check if Anki is running and AnkiConnect is enabled.")
        
        print(f"Added {'cloze' if is_cloze else 'basic'} card: {front} -> {back} to deck '{self.deck}'.")
    
    def _export_to_file(self, cards: List[str], title: str, is_cloze: bool) -> None:
        """Exports cards to a file in the 'exported_cards' directory."""
        os.makedirs("exported_cards", exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d-%H")
        file_path = f"exported_cards/{timestamp}_{'cloze' if is_cloze else 'basic'}_cards.txt"
        with open(file_path, "a", encoding="utf-8") as f:
            for card in cards:
                f.write(f"{card} {title} ;\n")
        print(f"Exported {len(cards)} {'cloze' if is_cloze else 'basic'} cards to {file_path}.")