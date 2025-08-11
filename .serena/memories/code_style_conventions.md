# Code Style and Conventions

## Python Code Style
- **Line length**: 80 characters (configured in pyproject.toml)
- **Formatter**: Ruff with docstring code formatting enabled
- **Type hints**: Use throughout codebase (Python 3.13+)
- **Docstrings**: Include for all classes and functions

## Naming Conventions
- **Classes**: PascalCase (e.g., BaseCard, AppealValue)
- **Functions**: snake_case (e.g., validate_toml_file, _validate_single_card)
- **Variables**: snake_case (e.g., card_data, toml_directory)
- **Constants**: UPPER_SNAKE_CASE (e.g., CARD_MODELS, SEPARATOR_LINE)
- **Private functions**: Prefix with underscore (e.g., _setup_logging, _read_toml_file)

## Code Organization
- Use Pydantic models for data validation
- Implement inheritance hierarchy (BaseCard -> specific card types)
- Use type hints with Literal types for enums
- Include field validation with @field_validator decorators
- Use Optional and Union types appropriately

## Error Handling
- Use ValidationError for Pydantic validation failures
- Include descriptive error messages in Japanese
- Use logging for information and warnings
- Implement proper exception handling with try/except blocks

## Data Validation Patterns
- ID format validation with regex patterns
- Field-specific validation methods
- Type-specific model exclusions
- Duplicate detection across data sets

## Import Organization
- Standard library imports first
- Third-party imports second
- Local imports last
- Use specific imports rather than wildcard imports