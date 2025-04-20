import argparse
import re
import sys
import tomllib
from pathlib import Path
from typing import List, Literal, Optional

from pydantic import BaseModel, ValidationError, field_validator

# --- 定数定義 ---
CARD_ID_PATTERN = re.compile(r"^IMT-\d{2}-\d{3}$")
IDOL_NAME_PATTERN = re.compile(r"^[^\s]+ [^\s]+$")
VALID_RARITIES = Literal["N", "R", "SR", "SSR"]
VALID_TYPES = Literal["costume", "accessory", "sp_appeal", "support"]


# --- Pydantic モデル定義 ---
class AppealValue(BaseModel):
    """アピール値モデル"""

    vocal: int
    dance: int
    visual: int


class BaseCard(BaseModel):
    """全カード共通の基本モデル"""

    card_name: str
    idol_name: str
    text: str
    subject: str  # TODO: subjectの取りうる値をLiteralで定義するべきか検討
    rarity: VALID_RARITIES
    type: VALID_TYPES

    @field_validator("idol_name")
    @classmethod
    def validate_idol_name_format(cls, v: str) -> str:
        """idol_nameが '名字 名前' の形式（半角スペース区切り）になっているか検証"""
        if not IDOL_NAME_PATTERN.match(v):
            raise ValueError(
                "idol_name must be in the format 'FirstName LastName' with a single space."
            )
        return v


class CostumeCard(BaseCard):
    """衣装カードモデル"""

    type: Literal["costume"]
    appeal_value: AppealValue


class AccessoryCard(BaseCard):
    """アクセサリーカードモデル"""

    type: Literal["accessory"]
    appeal_value: AppealValue # アクセサリーにもアピール値はある想定
    body_part: Optional[str] = None # data_rule.mdに基づきOptional


class SpAppealCard(BaseCard):
    """SPアピールカードモデル"""
    # TODO: sp_appeal.toml固有のフィールドがあれば追加
    type: Literal["sp_appeal"]


class SupportCard(BaseCard):
    """サポートカードモデル"""
    # TODO: support.toml固有のフィールドがあれば追加
    type: Literal["support"]


# カードタイプ名と対応するPydanticモデルのマッピング
CARD_TYPE_MAP = {
    "costume": CostumeCard,
    "accessory": AccessoryCard,
    "sp_appeal": SpAppealCard,
    "support": SupportCard,
}

# --- バリデーション関数 ---

def validate_card_id(card_id: str) -> List[str]:
    """カードIDのフォーマットと大文字ルールを検証"""
    errors = []
    if not CARD_ID_PATTERN.match(card_id):
        errors.append(f"Invalid card ID format: '{card_id}'. Expected 'IMT-XX-XXX'.")
    if not card_id.isupper():
        errors.append(f"Card ID must be uppercase: '{card_id}'.")
    return errors


def validate_toml_file(file_path: Path) -> List[str]:
    """単一のTOMLファイルをバリデーションする"""
    errors = []
    try:
        with open(file_path, "rb") as f:
            data = tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        errors.append(f"Error decoding TOML file '{file_path}': {e}")
        return errors
    except IOError as e:
        errors.append(f"Error reading file '{file_path}': {e}")
        return errors

    # data_rule.md の [[IMT-XX-XXX]] 形式 (テーブル配列) を想定
    # Pythonでは {'IMT-XX-XXX': [ {card_data1}, {card_data2}, ... ]} のような辞書になる
    for card_id, card_list in data.items():
        id_errors = validate_card_id(card_id)
        if id_errors:
            errors.extend([f"File '{file_path}', Card ID '{card_id}': {err}" for err in id_errors])
            # IDが不正な場合、そのIDに紐づくカードデータの検証はスキップする方が安全かもしれない
            continue

        if not isinstance(card_list, list):
            errors.append(f"File '{file_path}', Card ID '{card_id}': Expected a list of cards, but got {type(card_list)}.")
            continue

        for i, card_data in enumerate(card_list):
            if not isinstance(card_data, dict):
                errors.append(f"File '{file_path}', Card ID '{card_id}', Entry {i+1}: Expected a dictionary for card data, but got {type(card_data)}.")
                continue

            card_type = card_data.get("type")
            if card_type not in CARD_TYPE_MAP:
                errors.append(
                    f"File '{file_path}', Card ID '{card_id}', Entry {i+1}: Invalid or missing 'type' field: '{card_type}'."
                )
                continue

            model = CARD_TYPE_MAP[card_type]
            try:
                model.model_validate(card_data)
            except ValidationError as e:
                for error in e.errors():
                    loc = " -> ".join(map(str, error["loc"]))
                    msg = error["msg"]
                    errors.append(
                        f"File '{file_path}', Card ID '{card_id}', Entry {i+1}, Field '{loc}': {msg}"
                    )

    return errors


# --- メイン処理 ---
def main():
    parser = argparse.ArgumentParser(description="Validate card data TOML files.")
    parser.add_argument(
        "toml_files",
        nargs="+",
        type=Path,
        help="Path(s) to the TOML file(s) to validate.",
    )
    args = parser.parse_args()

    all_errors: List[str] = []
    for file_path in args.toml_files:
        if not file_path.is_file():
            all_errors.append(f"Error: File not found or not a file: {file_path}")
            continue
        print(f"Validating {file_path}...")
        errors = validate_toml_file(file_path)
        all_errors.extend(errors)

    if all_errors:
        print("\nValidation failed with the following errors:", file=sys.stderr)
        for error in all_errors:
            print(f"- {error}", file=sys.stderr)
        sys.exit(1)
    else:
        print("\nValidation successful. All files conform to the defined rules.")
        sys.exit(0)


if __name__ == "__main__":
    main()
