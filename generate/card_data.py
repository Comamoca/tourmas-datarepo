import json
import os
from pathlib import Path

import toml


def convert_toml_to_json(toml_dir: str, json_file_path: str) -> None:
    """Converts TOML files in a directory to a single JSON file.

    The output JSON file has the structure {"data": [all card information]}.

    Args:
        toml_dir: The directory containing the TOML files.
        json_file_path: The output JSON file path.
    """
    all_card_data = []
    try:
        for filename in os.listdir(toml_dir):
            if filename.endswith(".toml"):
                file_path = os.path.join(toml_dir, filename)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
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
                            print(
                                f"Unexpected data structure in {filename}"
                            )  # Enhanced logging
                except Exception as e:
                    print(f"Error reading {filename}: {e}")
                    continue
    except FileNotFoundError as e:
        print(f"Error: TOML directory not found: {toml_dir}")
        print(f"Exception details: {e}")
        return

    output_data = {"data": all_card_data}

    # `./dist`が存在しなかったら作成する
    dist_dir = Path(json_file_path).parent
    if not dist_dir.exists():
        dist_dir.mkdir()

    try:
        with open(json_file_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=4, ensure_ascii=False)
        print(f"Successfully converted TOML files to {json_file_path}")
        print(f"JSON file created at: {os.path.abspath(json_file_path)}")
    except Exception as e:
        print(f"Error writing to {json_file_path}: {e}")  # Enhanced logging
        print(f"Exception details: {e}")


if __name__ == "__main__":
    toml_directory = "./card_data"
    output_json_file = "./dist/card_data.json"
    convert_toml_to_json(toml_directory, output_json_file)
