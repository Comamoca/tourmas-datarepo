import re
import sys
import tomllib
from pathlib import Path
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, ValidationError, field_validator


# --- Pydantic Models ---

class BaseCard(BaseModel):
    """Base model for all card types, containing common fields."""
    id: str # Changed from card_id
    name: str # Changed from card_name
    idol: str # Changed from idol_name
    rarity: Literal["N", "R", "SR", "SSR"]
    text: str
    type: Literal["costume", "accessory", "support", "sp_appeal"]
    subject: Optional[Literal["everyone", "female", "male", "unique"] | str] = None # Common but handled in subtypes for specific rules if needed

    @field_validator("idol")
    @classmethod
    def check_idol_name_format(cls, value: str) -> str:
        """Ensure idol has a space between first and last name."""
        if " " not in value.strip():
            # Allow single names (like 'P') for now, adjust if needed
            if len(value.strip().split()) == 1:
                 return value
            raise ValueError("idol must contain a space between first and last name.")
        return value

    @field_validator("id")
    @classmethod
    def check_card_id_format(cls, value: str) -> str:
        """Ensure id follows the IMT-XX-XXX format."""
        if not re.match(r"^IMT-\d{2}-\d{3}$", value):
            raise ValueError("id must be in the format IMT-XX-XXX")
        return value


class AppealValue(BaseModel):
    """Model for appeal values (Vocal, Dance, Visual)."""
    vocal: int = Field(..., ge=0)
    dance: int = Field(..., ge=0)
    visual: int = Field(..., ge=0)


class Skill(BaseModel):
    """Model for skill name and description (used by Costume)."""
    name: str
    description: str


class SupportSkill(BaseModel):
    """Model for support skill type and description (used by Support)."""
    # name: str # Removed as it's not present in the updated support.toml example
    live_type: List[Literal["rhythm", "create"]] # Changed from Literal to List[Literal] based on updated support.toml
    description: List[str] # Changed from str to List[str] based on updated support.toml


class SpAppeal(BaseModel):
    """Model for SP appeal name and description (used by SpAppeal)."""
    name: str
    description: str


class CostumeCard(BaseCard):
    """Model for 'costume' type cards."""
    type: Literal["costume"]
    appeal: AppealValue # Renamed from appeal_value
    # skill: Skill # Removed as costume cards don't have skills according to user feedback
    # subject is inherited from BaseCard
    # Ensure other type-specific fields are not present
    skill: Optional[Skill] = Field(None, exclude=True)
    support_skill: Optional[SupportSkill] = Field(None, exclude=True)
    sp_appeal: Optional[SpAppeal] = Field(None, exclude=True)
    body_part: Optional[str] = Field(None, exclude=True)


class AccessoryCard(BaseCard):
    """Model for 'accessory' type cards."""
    type: Literal["accessory"]
    body_part: Literal["head", "face", "hand", "body", "waist", "leg"]
    # subject is inherited from BaseCard
    appeal: Optional[AppealValue] = Field(None, exclude=True) # Ensure appeal is NOT present
    skill: Optional[Skill] = Field(None, exclude=True) # Ensure skill is NOT present
    support_skill: Optional[SupportSkill] = Field(None, exclude=True) # Ensure support_skill is NOT present
    sp_appeal: Optional[SpAppeal] = Field(None, exclude=True) # Ensure sp_appeal is NOT present


class SupportCard(BaseCard):
    """Model for 'support' type cards."""
    type: Literal["support"]
    support_skill: SupportSkill # Renamed from support_effects, now a structured model
    # subject is inherited from BaseCard
    appeal: Optional[AppealValue] = Field(None, exclude=True) # Ensure appeal is NOT present
    skill: Optional[Skill] = Field(None, exclude=True) # Ensure skill is NOT present
    body_part: Optional[str] = Field(None, exclude=True) # Ensure body_part is NOT present
    sp_appeal: Optional[SpAppeal] = Field(None, exclude=True) # Ensure sp_appeal is NOT present


class SpAppealCard(BaseCard):
    """Model for 'sp_appeal' type cards."""
    type: Literal["sp_appeal"]
    sp_appeal: SpAppeal # Renamed from rhythm_live_effects, now a structured model
    # subject is inherited from BaseCard
    appeal: Optional[AppealValue] = Field(None, exclude=True) # Ensure appeal is NOT present
    skill: Optional[Skill] = Field(None, exclude=True) # Ensure skill is NOT present
    body_part: Optional[str] = Field(None, exclude=True) # Ensure body_part is NOT present
    support_skill: Optional[SupportSkill] = Field(None, exclude=True) # Ensure support_skill is NOT present


# --- Mapping and Validation Logic ---

CARD_MODELS = {
    "costume": CostumeCard,
    "accessory": AccessoryCard,
    "support": SupportCard,
    "sp_appeal": SpAppealCard,
}


def validate_toml_file(file_path: Path) -> List[str]:
    """Validates a single TOML file against the appropriate Pydantic model."""
    errors: List[str] = []
    print(f"Validating {file_path}...")
    card_ids = set()  # カードIDを格納するセット

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
        return errors # Cannot proceed without [[card]]

    card_list = data["card"]
    if not isinstance(card_list, list):
        errors.append(f"Error in {file_path.name}: Expected a list under the 'card' key, found {type(card_list).__name__}.")
        return errors
    if not card_list:
        print(f"Info: {file_path.name} contains 'card = []' but no card entries.")
        return errors # No cards to validate, but not an error state itself.

    # --- Validate each card in [[card]] list ---
    for index, card_data in enumerate(card_list):
        item_description = f"[[card]] item {index + 1}"
        if not isinstance(card_data, dict):
            errors.append(f"Error in {file_path.name}, {item_description}: Expected a table, found {type(card_data).__name__}.")
            continue # Skip this item, check others

        # 'id' must exist within the table for [[card]] format
        if "id" not in card_data:
             errors.append(f"Error in {file_path.name}, {item_description}: Missing 'id' field.")
             continue # Cannot proceed validation for this item without id

        card_id = card_data.get("id", "UNKNOWN_ID") # Get id for error reporting, use placeholder if missing

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


def main():
    """Finds and validates all TOML files in the ./card_data directory."""
    project_root = Path(__file__).parent.parent # Assumes validators/ is one level down from root
    card_data_dir = project_root / "card_data"

    if not card_data_dir.is_dir():
        print(f"Error: Directory not found: {card_data_dir}", file=sys.stderr)
        sys.exit(1)

    toml_files = sorted(list(card_data_dir.glob("*.toml"))) # Sort for consistent order

    if not toml_files:
        print(f"No TOML files found in {card_data_dir}", file=sys.stderr)
        # Exit with 0 if no files found is acceptable, or 1 if it's an error
        sys.exit(0)

    print(f"Found {len(toml_files)} TOML files to validate in {card_data_dir}:")
    # for f in toml_files:
    #     print(f"- {f.relative_to(project_root)}") # Print relative path
    print("-" * 20)

    all_errors = []
    has_files_validated = False
    for file_path in toml_files:
         if file_path.is_file():
             has_files_validated = True
             file_errors = validate_toml_file(file_path)
             if file_errors:
                 all_errors.extend(file_errors)
             else:
                 print(f"Validation successful for {file_path.relative_to(project_root)}.")
         else:
             print(f"Warning: Skipping non-file item: {file_path}", file=sys.stderr)


    print("-" * 20)
    if not has_files_validated and toml_files:
         print("Warning: No actual files were validated.", file=sys.stderr)

    if all_errors:
        print(f"\nValidation failed with {len(all_errors)} errors:", file=sys.stderr)
        for error in all_errors:
            print(f"- {error}", file=sys.stderr)
        sys.exit(1)
    else:
        print("\nValidation successful. All checked files conform to the defined rules.")
        sys.exit(0)


if __name__ == "__main__":
    main()
