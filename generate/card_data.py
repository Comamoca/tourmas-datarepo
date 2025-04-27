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
        file_path = card_data_dir / filename
        if filename.endswith(".toml") and os.path.isfile(file_path):
            try:
                with open(file_path, encoding="utf-8") as f:
                    data = toml.load(f)
                    if "card" in data:
                        cards = data["card"]
                        print(f"Loaded {len(cards)} cards from {file_path}")
                        all_cards.extend(cards)
            except FileNotFoundError:
                print(f"Error: File not found: {file_path}")
            except toml.TomlDecodeError:
                print(f"Error: Could not decode TOML in file: {file_path}")
def write_card_data(card_data: list[dict], output_file: Path):
    """Writes the combined card data to a JSON file."""
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({"card": card_data}, f, indent=2, ensure_ascii=False, sort_keys=True, indent=2)


def find_missing_ids(card_ids: list[str]) -> list[str]:
    """Finds missing card IDs in the range IMT-01-001 to IMT-01-094."""
    all_ids = [f"IMT-01-{i:03}" for i in range(1, 95)]
    existing_ids = set(card_ids)
    missing_ids = sorted(list(set(all_ids) - existing_ids))
    return missing_ids


def main():
    """Main function to load and combine card data."""
    all_cards = load_card_data(CARD_DATA_DIR)

    if all_cards is None:
        print("Error: Failed to load card data - load_card_data returned None.")
        return

    if not all_cards:
        print("Error: No cards loaded from TOML files.")
        return

    print(f"Loaded {len(all_cards)} cards.")

    card_ids = [card["id"] for card in all_cards]
    missing_ids = find_missing_ids(card_ids)

    if missing_ids:
        print("Missing card IDs:")
        for card_id in missing_ids:
            print(card_id)
    else:
        print("No missing card IDs found.")

    # Sort the cards by ID before writing to the output file
    all_cards.sort(key=lambda card: card["id"])

    write_card_data(all_cards, OUTPUT_FILE)
    print(f"Card data written to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
