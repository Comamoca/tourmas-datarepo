import re
import sys
import tomllib
from pathlib import Path
from typing import Dict, List, Literal, Optional, Type

from pydantic import BaseModel, Field, ValidationError, field_validator


# --- Pydantic Models ---

class BaseCard(BaseModel):
    """全カードタイプの基底モデル、共通フィールドを含む。"""
    id: str
    name: str
    idol: str
    rarity: Literal["N", "R", "SR", "SSR"]
    text: str
    type: Literal["costume", "accessory", "support", "sp_appeal"]
    subject: Optional[Literal["everyone", "female", "male", "unique"] | str] = None

    @field_validator("idol")
    @classmethod
    def validate_idol_name(cls, value: str) -> str:
        """アイドル名が適切な形式かを検証する。"""
        if " " not in value.strip() and len(value.strip().split()) > 1:
            raise ValueError("アイドル名は姓名の間にスペースが必要です")
        return value

    @field_validator("id")
    @classmethod
    def validate_card_id(cls, value: str) -> str:
        """カードIDがIMT-XX-XXX形式に従うかを検証する。"""
        if not re.match(r"^IMT-\d{2}-\d{3}$", value):
            raise ValueError("カードIDはIMT-XX-XXX形式である必要があります")
        return value


class AppealValue(BaseModel):
    """アピール値（ボーカル、ダンス、ビジュアル）のモデル。"""
    vocal: int = Field(ge=0, description="ボーカル値")
    dance: int = Field(ge=0, description="ダンス値")
    visual: int = Field(ge=0, description="ビジュアル値")


class Skill(BaseModel):
    """スキル名と説明のモデル（コスチューム用）。"""
    name: str
    description: str


class SupportSkill(BaseModel):
    """サポートスキルのタイプと説明のモデル（サポート用）。"""
    live_type: List[Literal["rhythm", "create"]]
    description: List[str]


class SpAppeal(BaseModel):
    """SPアピール名と効果のモデル（SPアピール用）。"""
    effect: List[str]


class CostumeCard(BaseCard):
    """コスチュームタイプカードのモデル。"""
    type: Literal["costume"]
    appeal: AppealValue
    skill: Optional[Skill] = Field(None, exclude=True)
    support_skill: Optional[SupportSkill] = Field(None, exclude=True)
    sp_appeal: Optional[SpAppeal] = Field(None, exclude=True)
    body_part: Optional[str] = Field(None, exclude=True)


class AccessoryCard(BaseCard):
    """アクセサリータイプカードのモデル。"""
    type: Literal["accessory"]
    body_part: Literal["head", "face", "hand", "body", "waist", "leg"]
    appeal: Optional[AppealValue] = Field(None, exclude=True)
    skill: Optional[Skill] = Field(None, exclude=True)
    support_skill: Optional[SupportSkill] = Field(None, exclude=True)
    sp_appeal: Optional[SpAppeal] = Field(None, exclude=True)


class SupportCard(BaseCard):
    """サポートタイプカードのモデル。"""
    type: Literal["support"]
    support_skill: SupportSkill
    appeal: Optional[AppealValue] = Field(None, exclude=True)
    skill: Optional[Skill] = Field(None, exclude=True)
    body_part: Optional[str] = Field(None, exclude=True)
    sp_appeal: Optional[SpAppeal] = Field(None, exclude=True)


class SpAppealCard(BaseCard):
    """SPアピールタイプカードのモデル。"""
    type: Literal["sp_appeal"]
    sp_appeal: SpAppeal
    appeal: Optional[AppealValue] = Field(None, exclude=True)
    skill: Optional[Skill] = Field(None, exclude=True)
    body_part: Optional[str] = Field(None, exclude=True)
    support_skill: Optional[SupportSkill] = Field(None, exclude=True)


CARD_MODELS: Dict[str, Type[BaseCard]] = {
    "costume": CostumeCard,
    "accessory": AccessoryCard,
    "support": SupportCard,
    "sp_appeal": SpAppealCard,
}

CARD_ARRAY_KEY = "card"
SEPARATOR_LINE = "-" * 20


def validate_toml_file(file_path: Path) -> List[str]:
    """Validates a single TOML file against the appropriate Pydantic model."""
    errors: List[str] = []
    print(f"Validating {file_path}...")
    card_ids: set[str] = set()  # カードIDを格納するセット

    try:
        with open(file_path, "rb") as f:
            data = tomllib.load(f)
    except FileNotFoundError:
        errors.append(f"Error: File not found at {file_path}")
        return errors
    except tomllib.TOMLDecodeError as e:
        # Add line number information if possible, though tomllib doesn't easily provide it
        errors.append(f"Error decoding TOML in {file_path.name}: {e}")
        # If TOML decoding fails, further validation is likely impossible or misleading.
        return errors
    # FileNotFoundError is handled by the text pre-validation part now.
    except Exception as e:
        errors.append(f"Unexpected error during TOML parsing of {file_path.name}: {e}")
        return errors

    # --- Data Structure Validation ---
    if not isinstance(data, dict):
        errors.append(f"Error in {file_path.name}: TOML root must be a table (dictionary).")
        return errors

    # Check for [[card]] format (This is the only supported format now)
    if "card" not in data:
        errors.append(f"Error in {file_path.name}: Missing '[[card]]' array definition. Data must be defined as an array of tables under the 'card' key.")
        # If 'card' key doesn't exist, but the file is not empty, it's an error.
        if data:
            errors.append(f"Info: Found top-level keys {list(data.keys())} instead of '[[card]]'.")
        return errors  # Cannot proceed without [[card]]

    card_list = data["card"]
    if not isinstance(card_list, list):
        errors.append(f"Error in {file_path.name}: Expected a list under the 'card' key, found {type(card_list).__name__}.")
        return errors
    if not card_list:
        print(f"Info: {file_path.name} contains 'card = []' but no card entries.")
        return errors  # No cards to validate, but not an error state itself.

    # --- Validate each card in [[card]] list ---
    for index, card_data in enumerate(card_list):
        item_description = f"[[card]] item {index + 1}"
        if not isinstance(card_data, dict):
            errors.append(f"Error in {file_path.name}, {item_description}: Expected a table, found {type(card_data).__name__}.")
            continue  # Skip this item, check others

        # 'id' must exist within the table for [[card]] format
        if "id" not in card_data:
            errors.append(f"Error in {file_path.name}, {item_description}: Missing 'id' field.")
            continue  # Cannot proceed validation for this item without id

        card_id = card_data.get("id", "UNKNOWN_ID")  # Get id for error reporting, use placeholder if missing

        if card_id in card_ids:
            errors.append(f"Error in {file_path.name}, {item_description}: Duplicate card ID '{card_id}'")
        else:
            card_ids.add(card_id)

        _validate_single_card(file_path.name, item_description, card_id, card_data, errors)

    return errors


def _validate_single_card(filename: str, item_desc: str, card_id: str, card_data: dict, errors: list):
    """Helper function to validate a single card's data using Pydantic."""
    card_type = card_data.get("type")
    if not card_type:
        errors.append(
            f"Error in {filename}, {item_desc}: Missing 'type' field."
        )
        return # Skip this card item

    model = CARD_MODELS.get(card_type)
    if not model:
        errors.append(
            f"Error in {filename}, {item_desc}: Unknown card type '{card_type}'."
        )
        return # Skip item with unknown type

    try:
        # Validate the card data (including card_id added for [[IMT...]] format)
        model.model_validate(card_data)

        # Explicit checks for disallowed fields are handled by `exclude=True` in models

    except ValidationError as e:
        for error in e.errors():
            # Use '.' for nested fields as is common practice
            field_path = ".".join(map(str, error["loc"]))
            message = error["msg"]
            input_value = error.get("input", "N/A")
            errors.append(
                f"Error in {filename}, {item_desc} (ID: {card_id}), field '{field_path}': {message} [Input: {input_value}]"
            )
    except Exception as e:
        errors.append(
            f"Unexpected error during Pydantic validation in {filename}, {item_desc} (ID: {card_id}): {e}"
        )


def _find_toml_files(card_data_dir: Path) -> List[Path]:
    """指定されたディレクトリからTOMLファイルを検索する。
    
    Args:
        card_data_dir: 検索するディレクトリ
        
    Returns:
        見つかったTOMLファイルのリスト
        
    Raises:
        FileNotFoundError: ディレクトリが存在しない場合
    """
    if not card_data_dir.is_dir():
        raise FileNotFoundError(f"ディレクトリが見つかりません: {card_data_dir}")
    
    return sorted(list(card_data_dir.glob("*.toml")))


def _validate_all_files(toml_files: List[Path], project_root: Path) -> List[str]:
    """すべてのTOMLファイルを検証する。
    
    Args:
        toml_files: 検証するTOMLファイルのリスト
        project_root: プロジェクトルートディレクトリ
        
    Returns:
        すべての検証エラーのリスト
    """
    all_errors = []
    
    for file_path in toml_files:
        if not file_path.is_file():
            print(f"Warning: ファイルでないアイテムをスキップします: {file_path}", file=sys.stderr)
            continue
        
        file_errors = validate_toml_file(file_path)
        if file_errors:
            all_errors.extend(file_errors)
        else:
            print(f"検証成功: {file_path.relative_to(project_root)}")
    
    return all_errors


def main() -> None:
    """./card_dataディレクトリ内のすべてのTOMLファイルを検索し、検証する。"""
    project_root = Path(__file__).parent.parent
    card_data_dir = project_root / "card_data"
    
    try:
        toml_files = _find_toml_files(card_data_dir)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    
    if not toml_files:
        print(f"TOMLファイルが見つかりません: {card_data_dir}", file=sys.stderr)
        sys.exit(0)
    
    print(f"{card_data_dir}で検証する{len(toml_files)}個のTOMLファイルを発見:")
    print(SEPARATOR_LINE)
    
    all_errors = _validate_all_files(toml_files, project_root)
    
    print(SEPARATOR_LINE)
    
    if all_errors:
        print(f"\n検証失敗: {len(all_errors)}個のエラー:", file=sys.stderr)
        for error in all_errors:
            print(f"- {error}", file=sys.stderr)
        sys.exit(1)
    else:
        print("\n検証成功: すべてのファイルが定義されたルールに適合しています")
        sys.exit(0)


if __name__ == "__main__":
    main()
