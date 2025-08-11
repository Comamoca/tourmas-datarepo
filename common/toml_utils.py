import tomllib
from pathlib import Path
from typing import Any, Dict, List


def read_card_data_from_toml(file_path: Path) -> List[Dict[str, Any]]:
    """TOML ファイルから [[card]] 形式のカードデータを読み込む。

    Args:
        file_path: 読み込むTOMLファイルのパス

    Returns:
        カードデータのリスト

    Raises:
        FileNotFoundError: ファイルが存在しない場合
        tomllib.TOMLDecodeError: TOML形式が不正な場合
        ValueError: [[card]]形式でない場合
    """
    with open(file_path, "rb") as f:
        data = tomllib.load(f)

    if not isinstance(data, dict):
        raise ValueError(
            f"TOML root must be a table (dictionary) in {file_path.name}"
        )

    if "card" not in data:
        raise ValueError(
            f"Missing '[[card]]' array definition in {file_path.name}"
        )

    card_list = data["card"]
    if not isinstance(card_list, list):
        raise ValueError(
            f"Expected a list under the 'card' key in {file_path.name}"
        )

    return card_list


def find_toml_files(directory: Path) -> List[Path]:
    """指定されたディレクトリからTOMLファイルを検索する。

    Args:
        directory: 検索するディレクトリ

    Returns:
        見つかったTOMLファイルのソートされたリスト

    Raises:
        FileNotFoundError: ディレクトリが存在しない場合
    """
    if not directory.is_dir():
        raise FileNotFoundError(f"ディレクトリが見つかりません: {directory}")

    return sorted(list(directory.glob("*.toml")))


def collect_all_card_data(toml_dir: Path) -> List[Dict[str, Any]]:
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
    toml_files = find_toml_files(toml_dir)

    for file_path in toml_files:
        try:
            card_data = read_card_data_from_toml(file_path)
            all_card_data.extend(card_data)
        except (tomllib.TOMLDecodeError, ValueError, FileNotFoundError) as e:
            raise RuntimeError(f"Failed to read {file_path.name}: {e}")

    return all_card_data
