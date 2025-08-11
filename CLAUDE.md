# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a data repository for The Idolmaster Tours (ツアマス) card information. The project uses Python with uv for dependency management and contains:

- TOML files with structured card data in `card_data/`
- Python scripts to validate and convert TOML data to JSON
- Pre-commit hooks for data validation
- Nix flake for development environment

## Common Commands

### Python Environment
- `uv run python <script>` - Run Python scripts using uv
- `uv sync` - Sync dependencies after modifying pyproject.toml
- `uv add <package>` - Add new Python packages

### Linting and Formatting
- `ruff check` - Run linter (use instead of flake8)
- `ruff format` - Format code
- `nix fmt` - Format Nix files with treefmt

### Data Validation and Testing
- `uv run pytest` - Run all tests using pytest framework
- `uv run pytest tests/test_card_validation.py` - Run card data validation tests specifically
- `uv run python ./validators/card_data.py` - Run standalone validation script (legacy)
- Pre-commit hooks automatically validate card data when committing changes to `card_data/`

### Data Generation
- `uv run python ./generate/card_data.py` - Convert TOML files to JSON output in `./dist/card_data.json`

## Architecture

### Card Data Model Architecture
The project uses a sophisticated Pydantic-based validation system with inheritance:

- **BaseCard**: Core model with shared fields (`id`, `name`, `idol`, `rarity`, `text`, `type`, `subject`)
- **Type-specific models**: CostumeCard, AccessoryCard, SupportCard, SpAppealCard
- **Field-specific models**: AppealValue (vocal/dance/visual), Skill, SupportSkill, SpAppeal
- **Type mapping**: CARD_MODELS dict in `validators/card_data.py:103-108` maps types to validation models

### Data Storage Format
Card data is stored in TOML files using the `[[card]]` array-of-tables format:
- Each card entry is a table within the `card` array
- Base fields: `id` (IMT-XX-XXX format), `name`, `idol`, `rarity`, `text`, `type`
- Type-specific fields with validation exclusions (costume cards have `appeal` + optional `skill`, accessories have `body_part`, etc.)

### Validation Pipeline
The `validators/card_data.py` implements a multi-stage validation process:
1. TOML parsing and structure validation
2. Card array format validation (`[[card]]` structure)
3. Per-card Pydantic model validation with type-specific rules
4. Duplicate ID detection across all cards in a file
5. Cross-field validation (e.g., idol name format, card ID pattern)

### Data Generation Pipeline
The `generate/card_data.py` converts TOML to JSON:
1. Reads all `.toml` files from `card_data/`
2. Collects card data from `[[card]]` arrays
3. Sorts by card ID and outputs to `dist/card_data.json` with `{"data": [...]}` structure

## Development Guidelines

### Data Contribution Workflow
- **Strict one-card-per-PR policy**: Each PR must modify exactly one card (enforced rejection of multi-card PRs)
- Card data changes can be made directly via PR without prior issue discussion
- Program/script changes require issue discussion before implementation
- Pre-commit hooks automatically validate card data on TOML file changes

### Development Environment
- **Nix-based development**: Use `nix develop` for consistent environment
- **Python 3.13** with uv package management
- **Pre-commit hooks** configured via Nix flake for automatic validation
- **Code formatting**: treefmt for Nix files, ruff for Python

### Language Requirements
According to `.aiderrules`, all aider responses should be in Japanese.

### Pre-commit Hook Configuration
The Nix flake (`flake.nix:62-94`) configures comprehensive pre-commit hooks:
- **treefmt**: Code formatting for Nix files
- **ripsecrets & git-secrets**: Secret detection
- **validate-card-data**: Custom hook that runs `validators/card_data.py` on TOML changes
  - Triggers only for `card_data/*.toml` files
  - Uses devenv shell environment for proper uv execution

### Card Data Rules
Cards must follow strict validation rules enforced by Pydantic models:
- **ID format**: Must match `IMT-XX-XXX` pattern (regex: `^IMT-\d{2}-\d{3}$`)
- **Idol names**: Must contain space between surname and given name
- **Type-specific fields**: Each card type has exclusive field requirements with `exclude=True` validation
- **No duplicate IDs**: Within each TOML file, card IDs must be unique