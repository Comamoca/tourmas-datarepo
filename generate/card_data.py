import json
from pathlib import Path
from typing import Union

import toml


def convert_toml_to_json(toml_dir: Union[str, Path], json_file_path: Union[str, Path]) -> None:
    """Converts TOML files in a directory to a single JSON file.

    The output JSON file has the structure {"data": [all card information]}.

    Args:
        toml_dir: The directory containing the TOML files.
        json_file_path: The output JSON file path.
    """
    toml_dir = Path(toml_dir)
    json_file_path = Path(json_file_path)

    all_card_data = []

    if not toml_dir.exists():
        print(f"[ERROR] TOML directory not found: {toml_dir}")
        return

    for file_path in toml_dir.iterdir():
        if file_path.suffix != ".toml":
            continue

        print(f"[INFO] Reading {file_path.name}")

        try:
            with file_path.open("r", encoding="utf-8") as f:
                toml_data = toml.load(f)

            if isinstance(toml_data, dict):
                for value in toml_data.values():
                    if isinstance(value, list):
                        all_card_data.extend(value)
                    else:
                        all_card_data.append(value)
            elif isinstance(toml_data, list):
                all_card_data.extend(toml_data)
            else:
                print(f"[WARNING] Unexpected data structure in {file_path.name}")
        except (OSError, toml.TomlDecodeError) as e:
            print(f"[ERROR] Failed to read {file_path.name}: {e}")
            continue

    # Sort the cards by ID
    all_card_data.sort(key=lambda card: card["id"])

    output_data = {"data": all_card_data}

    dist_dir = json_file_path.parent
    dist_dir.mkdir(parents=True, exist_ok=True)

    try:
        with json_file_path.open("w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=4, ensure_ascii=False)
        print(f"[SUCCESS] JSON file created at: {json_file_path.resolve()}")
    except OSError as e:
        print(f"[ERROR] Failed to write JSON file: {e}")


if __name__ == "__main__":
    toml_directory = "./card_data"
    output_json_file = "./dist/card_data.json"
    convert_toml_to_json(toml_directory, output_json_file)
