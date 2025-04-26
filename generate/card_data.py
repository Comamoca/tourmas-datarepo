import json
import os
from pathlib import Path

import toml


def convert_toml_to_json(toml_dir: str, json_file_path: str):
    """
    Converts multiple TOML files in a directory to a single JSON file with
    the structure {"data": [all card information]}.

    Args:
        toml_dir (str): The directory containing the TOML files.
        json_file_path (str): The output JSON file path.
    """
    all_card_data = []
    for filename in os.listdir(toml_dir):
        if filename.endswith(".toml"):
            file_path = os.path.join(toml_dir, filename)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    toml_data = toml.load(f)
                    if isinstance(toml_data, dict):
                        all_card_data.extend(toml_data.values())
                    elif isinstance(toml_data, list):
                        all_card_data.extend(toml_data)
                    else:
                        print(f"Unexpected data structure in {filename}")
            except Exception as e:
                print(f"Error reading {filename}: {e}")
                continue

    output_data = {"data": all_card_data}

    try:
        with open(json_file_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=4, ensure_ascii=False)
        print(f"Successfully converted TOML files to {json_file_path}")
    except Exception as e:
        print(f"Error writing to {json_file_path}: {e}")


if __name__ == "__main__":
    toml_directory = "./card_data"
    output_json_file = "card_data.json"
    convert_toml_to_json(toml_directory, output_json_file)
