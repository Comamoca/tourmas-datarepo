import json
import os
from pathlib import Path

import toml

CARD_DATA_DIR = Path("card_data")
OUTPUT_FILE = Path("dist/card_data.json")


def load_card_data(card_data_dir: Path) -> list[dict]:
    """Loads card data from all TOML files in the given directory."""
    all_cards: list[dict] = []
    for filename in os.listdir(card_data_dir):
        if filename.endswith(".toml"):
            file_path = card_data_dir / filename
            try:
                with open(file_path, encoding="utf-8") as f:
                    data = toml.load(f)
                    if "card" in data:
                        all_cards.extend(data["card"])
            except FileNotFoundError:
                print(f"Error: File not found: {file_path}")
    return all_cards


def write_card_data(card_data: list[dict], output_file: Path):
    """Writes the combined card data to a JSON file."""
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({"card": card_data}, f, indent=2, ensure_ascii=False)


def main():
    """Main function to load and combine card data."""
    all_cards = load_card_data(CARD_DATA_DIR)

    print(f"Loaded {len(all_cards)} cards.")
    write_card_data(all_cards, OUTPUT_FILE)
    print(f"Card data written to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
