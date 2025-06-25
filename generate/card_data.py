import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Union

import toml


def _setup_logging() -> None:
    """ログ設定を初期化する。"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s"
    )


def _read_toml_file(file_path: Path) -> List[Dict[str, Any]]:
    """単一のTOMLファイルを読み込み、カードデータのリストを返す。
    
    Args:
        file_path: 読み込むTOMLファイルのパス
        
    Returns:
        カードデータのリスト
        
    Raises:
        FileNotFoundError: ファイルが存在しない場合
        toml.TomlDecodeError: TOML形式が不正な場合
    """
    logging.info(f"Reading {file_path.name}")
    
    with file_path.open("r", encoding="utf-8") as f:
        toml_data = toml.load(f)
    
    card_data = []
    if isinstance(toml_data, dict):
        for value in toml_data.values():
            if isinstance(value, list):
                card_data.extend(value)
            else:
                card_data.append(value)
    elif isinstance(toml_data, list):
        card_data.extend(toml_data)
    else:
        logging.warning(f"Unexpected data structure in {file_path.name}")
        
    return card_data


def _collect_card_data(toml_dir: Path) -> List[Dict[str, Any]]:
    """指定されたディレクトリからすべてのTOMLファイルを読み込み、カードデータを収集する。
    
    Args:
        toml_dir: TOMLファイルが格納されているディレクトリ
        
    Returns:
        収集されたカードデータのリスト
        
    Raises:
        FileNotFoundError: ディレクトリが存在しない場合
    """
    if not toml_dir.exists():
        raise FileNotFoundError(f"TOML directory not found: {toml_dir}")
    
    all_card_data = []
    
    for file_path in toml_dir.iterdir():
        if file_path.suffix != ".toml":
            continue
            
        try:
            card_data = _read_toml_file(file_path)
            all_card_data.extend(card_data)
        except (OSError, toml.TomlDecodeError) as e:
            logging.error(f"Failed to read {file_path.name}: {e}")
            continue
    
    return all_card_data


def _write_json_file(json_file_path: Path, card_data: List[Dict[str, Any]]) -> None:
    """カードデータをJSONファイルに書き込む。
    
    Args:
        json_file_path: 出力するJSONファイルのパス
        card_data: 書き込むカードデータのリスト
        
    Raises:
        OSError: ファイル書き込みに失敗した場合
    """
    sorted_data = sorted(card_data, key=lambda card: card["id"])
    output_data = {"data": sorted_data}
    
    json_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    with json_file_path.open("w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=4, ensure_ascii=False)
    
    logging.info(f"JSON file created at: {json_file_path.resolve()}")


def convert_toml_to_json(toml_dir: Union[str, Path], json_file_path: Union[str, Path]) -> None:
    """TOMLファイルを含むディレクトリを単一のJSONファイルに変換する。

    出力されるJSONファイルは {"data": [すべてのカード情報]} の構造を持つ。

    Args:
        toml_dir: TOMLファイルが格納されているディレクトリ
        json_file_path: 出力するJSONファイルのパス
    """
    _setup_logging()
    
    toml_dir = Path(toml_dir)
    json_file_path = Path(json_file_path)
    
    try:
        card_data = _collect_card_data(toml_dir)
        _write_json_file(json_file_path, card_data)
    except FileNotFoundError as e:
        logging.error(str(e))
    except OSError as e:
        logging.error(f"Failed to write JSON file: {e}")


if __name__ == "__main__":
    toml_directory = "./card_data"
    output_json_file = "./dist/card_data.json"
    convert_toml_to_json(toml_directory, output_json_file)
