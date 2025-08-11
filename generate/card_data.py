import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Union


def _setup_logging() -> None:
    """ログ設定を初期化する。"""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def _read_toml_file(file_path: Path) -> List[Dict[str, Any]]:
    """単一のTOMLファイルから[[card]]形式のカードデータを読み込む。

    Args:
        file_path: 読み込むTOMLファイルのパス

    Returns:
        カードデータのリスト

    Raises:
        FileNotFoundError: ファイルが存在しない場合
        RuntimeError: TOML読み込みに失敗した場合
    """
    import sys

    sys.path.append(str(Path(__file__).parent.parent))
    from common.toml_utils import read_card_data_from_toml

    logging.info(f"Reading {file_path.name}")

    try:
        return read_card_data_from_toml(file_path)
    except (FileNotFoundError, ValueError) as e:
        raise RuntimeError(f"Failed to read {file_path.name}: {e}")


def _collect_card_data(toml_dir: Path) -> List[Dict[str, Any]]:
    """指定されたディレクトリからすべてのTOMLファイルを読み込み、カードデータを収集する。

    Args:
        toml_dir: TOMLファイルが格納されているディレクトリ

    Returns:
        収集されたカードデータのリスト

    Raises:
        FileNotFoundError: ディレクトリが存在しない場合
    """
    import sys

    sys.path.append(str(Path(__file__).parent.parent))
    from common.toml_utils import collect_all_card_data

    try:
        return collect_all_card_data(toml_dir)
    except RuntimeError as e:
        logging.error(str(e))
        return []


def _write_json_file(
    json_file_path: Path, card_data: List[Dict[str, Any]]
) -> None:
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


def convert_toml_to_json(
    toml_dir: Union[str, Path], json_file_path: Union[str, Path]
) -> None:
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
