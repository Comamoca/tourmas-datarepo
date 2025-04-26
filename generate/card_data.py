import toml
import json
import os
from pathlib import Path

def convert_toml_to_json(toml_dir: str, json_file: str):
    """
    Converts multiple TOML files in a directory to a single JSON file.

    Args:
        toml_dir (str): The directory containing the TOML files.
        json_file (str): The output JSON file.
    """
    data = {}
    for filename in os.listdir(toml_dir):
        if filename.endswith(".toml"):
            file_path = os.path.join(toml_dir, filename)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    toml_data = toml.load(f)
                    data[filename[:-5]] = toml_data  # Remove ".toml" extension
            except Exception as e:
                print(f"Error reading {filename}: {e}")
                continue

    try:
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"Successfully converted TOML files to {json_file}")
    except Exception as e:
        print(f"Error writing to {json_file}: {e}")

if __name__ == "__main__":
    toml_directory = "./card_data"
    output_json_file = "card_data.json"
    convert_toml_to_json(toml_directory, output_json_file)
