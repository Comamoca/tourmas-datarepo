import re # 正規表現モジュールをインポート
import sys
import tomllib
from pathlib import Path
from typing import List, Literal, Optional

from pydantic import BaseModel, ValidationError, field_validator, Field


# --- Pydantic Models ---

class BaseCard(BaseModel):
    """Base model for all card types, containing common fields."""
    card_name: str
    idol_name: str
    rarity: Literal["N", "R", "SR", "SSR"]
    text: str
    type: Literal["costume", "accessory", "support", "sp_appeal"]
    subject: Literal["everyone", "female", "male", "unique"] | str # Common but handled in subtypes for specific rules if needed

    @field_validator("idol_name")
    @classmethod
    def check_idol_name_format(cls, value: str) -> str:
        """Ensure idol_name has a space between first and last name."""
        if " " not in value.strip():
            # Allow single names (like 'P') for now, adjust if needed
            if len(value.strip().split()) == 1:
                 return value
            raise ValueError("idol_name must contain a space between first and last name.")
        return value


class AppealValue(BaseModel):
    """Model for appeal values (Vocal, Dance, Visual)."""
    vocal: int = Field(..., ge=0)
    dance: int = Field(..., ge=0)
    visual: int = Field(..., ge=0)


class CostumeCard(BaseCard):
    """Model for 'costume' type cards."""
    type: Literal["costume"]
    appeal_value: AppealValue
    # subject is inherited from BaseCard


class AccessoryCard(BaseCard):
    """Model for 'accessory' type cards."""
    type: Literal["accessory"]
    body_part: Literal["head", "face", "hand", "body", "waist", "leg"]
    # subject is inherited from BaseCard
    appeal_value: Optional[AppealValue] = Field(None, exclude=True) # Ensure appeal_value is NOT present


class SupportCard(BaseCard):
    """Model for 'support' type cards."""
    type: Literal["support"]
    support_effects: str # Keep as string for now, can be refined if structure is known
    # subject is inherited from BaseCard
    appeal_value: Optional[AppealValue] = Field(None, exclude=True) # Ensure appeal_value is NOT present
    body_part: Optional[str] = Field(None, exclude=True) # Ensure body_part is NOT present


class SpAppealCard(BaseCard):
    """Model for 'sp_appeal' type cards."""
    type: Literal["sp_appeal"]
    rhythm_live_effects: List[str]
    # subject is inherited from BaseCard
    appeal_value: Optional[AppealValue] = Field(None, exclude=True) # Ensure appeal_value is NOT present
    body_part: Optional[str] = Field(None, exclude=True) # Ensure body_part is NOT present


# --- Mapping and Validation Logic ---

CARD_MODELS = {
    "costume": CostumeCard,
    "accessory": AccessoryCard,
    "support": SupportCard,
    "sp_appeal": SpAppealCard,
}


def validate_toml_file(file_path: Path) -> List[str]:
    """Validates a single TOML file against the appropriate Pydantic model."""
    errors = []
    print(f"Validating {file_path}...")

    # --- Text-based pre-validation for nested key consistency ---
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        errors.append(f"Error: File not found at {file_path}")
        return errors
    except Exception as e:
        errors.append(f"Error reading file {file_path}: {e}")
        return errors

    current_top_level_key = None
    # Regex to capture top-level keys like [IMT-XX-XXX] or [[IMT-XX-XXX]]
    top_level_key_pattern = re.compile(r"^\[{1,2}(IMT-\d{2}-\d{3})\]{1,2}")
    # Regex to capture nested appeal_value keys like [IMT-XX-XXX.appeal_value]
    nested_appeal_key_pattern = re.compile(r"^\[(IMT-\d{2}-\d{3})\.appeal_value\]")

    for line_num, line in enumerate(lines):
        stripped_line = line.strip()
        if not stripped_line or stripped_line.startswith("#"): # Skip empty lines and comments
            continue

        top_level_match = top_level_key_pattern.match(stripped_line)
        if top_level_match:
            current_top_level_key = top_level_match.group(1)
            continue # Move to next line after finding a top-level key

        nested_appeal_match = nested_appeal_key_pattern.match(stripped_line)
        if nested_appeal_match:
            nested_key_prefix = nested_appeal_match.group(1)
            if current_top_level_key is None:
                # Error if a nested key appears before any top-level key
                errors.append(
                    f"Error in {file_path.name}, line {line_num + 1}: Nested key '{stripped_line}' found before any top-level key '[IMT-XX-XXX]' or '[[IMT-XX-XXX]]'."
                )
            elif nested_key_prefix != current_top_level_key:
                # Error if the prefix of the nested key does not match the current top-level key
                errors.append(
                    f"Error in {file_path.name}, line {line_num + 1}: Key mismatch for nested table. Expected prefix '{current_top_level_key}' but found '{nested_key_prefix}' in '{stripped_line}'."
                )

    # --- End of text-based pre-validation ---

    # Proceed with tomllib parsing and Pydantic validation only if pre-validation passed,
    # or if you want to collect all errors (Pydantic errors might be redundant if structure is wrong).
    # If pre-validation found errors, we could return early:
    # if errors:
    #     return errors

    try:
        with open(file_path, "rb") as f:
            data = tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        # Add line number information if possible, though tomllib doesn't easily provide it
        errors.append(f"Error decoding TOML in {file_path.name}: {e}")
        # If TOML decoding fails, further validation is likely impossible or misleading.
        return errors
    # FileNotFoundError is handled by the text pre-validation part now.
    except Exception as e:
        errors.append(f"Unexpected error during TOML parsing of {file_path.name}: {e}")
        return errors

    # Check if the root is a dictionary (table)
    if not isinstance(data, dict):
        errors.append(f"Error in {file_path.name}: TOML root must be a table (dictionary).")
        return errors

    # Card ID format check using the same pattern as pre-validation
    card_id_pattern = re.compile(r"^IMT-\d{2}-\d{3}$")

    for card_id, card_list in data.items():
        # Validate the format of the top-level key (card_id)
        if not card_id_pattern.match(card_id):
             errors.append(f"Error in {file_path.name}: Invalid top-level key format '{card_id}'. Must match 'IMT-XX-XXX'.")
             continue # Skip validation for this malformed key block

        # Check if the value associated with the card_id is a list
        if not isinstance(card_list, list):
            errors.append(
                f"Error in {file_path.name}, ID '{card_id}': Expected a list of cards (defined with [[{card_id}]]), found {type(card_list).__name__}."
            )
            continue # Skip this card_id block

        # Iterate through each card definition within the list
        for index, card_data in enumerate(card_list):
            # Ensure each item in the list is a dictionary (table)
            if not isinstance(card_data, dict):
                errors.append(
                    f"Error in {file_path.name}, ID '{card_id}', item {index + 1}: Expected a table (dictionary), found {type(card_data).__name__}."
                )
                continue # Skip this item

            # Get the card type to determine the correct Pydantic model
            card_type = card_data.get("type")
            if not card_type:
                errors.append(
                    f"Error in {file_path.name}, ID '{card_id}', item {index + 1}: Missing 'type' field."
                )
                continue # Skip this card item

            # Find the corresponding Pydantic model based on the type
            model = CARD_MODELS.get(card_type)
            if not model:
                errors.append(
                    f"Error in {file_path.name}, ID '{card_id}', item {index + 1}: Unknown card type '{card_type}'."
                )
                continue # Skip item with unknown type

            # Validate the card data against the selected Pydantic model
            try:
                # Add context for better error messages if needed later
                # card_data_with_context = {"card_id": card_id, "file": str(file_path), **card_data}
                model.model_validate(card_data)

                # Explicitly check for disallowed fields based on type using Pydantic's validation logic (already handled by exclude=True)
                # However, adding explicit checks here can provide slightly clearer error messages if needed.
                # Example (optional, as Pydantic should catch this):
                # if card_type in ["support", "sp_appeal", "accessory"] and "appeal_value" in card_data:
                #     errors.append(
                #         f"Error in {file_path.name}, ID '{card_id}', item {index + 1}: Field 'appeal_value' is not allowed for type '{card_type}'."
                #     )
                # if card_type in ["support", "sp_appeal", "costume"] and "body_part" in card_data:
                #     errors.append(
                #         f"Error in {file_path.name}, ID '{card_id}', item {index + 1}: Field 'body_part' is not allowed for type '{card_type}'."
                #     )


            except ValidationError as e:
                for error in e.errors():
                    # Format Pydantic validation errors for better readability
                    field_path = " -> ".join(map(str, error["loc"]))
                    message = error["msg"]
                    input_value = error.get("input", "N/A") # Get the input value that caused the error
                    errors.append(
                        f"Error in {file_path.name}, ID '{card_id}', item {index + 1}, field '{field_path}': {message} [Input: {input_value}]"
                    )
            except Exception as e:
                # Catch any other unexpected errors during Pydantic validation
                errors.append(
                    f"Unexpected error during Pydantic validation in {file_path.name}, ID '{card_id}', item {index + 1}: {e}"
                )

    return errors


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
