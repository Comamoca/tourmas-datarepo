# Project Overview

## Purpose
This is a data repository for The Idolmaster Tours (ツアマス) card information. It's designed to collect and manage card data in structured TOML format and generate JSON data for public consumption via Cloudflare Pages.

## Tech Stack
- **Python 3.13** with uv for dependency management
- **Pydantic** for data validation and modeling
- **TOML** format for data storage
- **JSON** for data output
- **Nix flake** for development environment
- **Pre-commit hooks** for validation
- **Ruff** for code formatting and linting

## Project Structure
- `card_data/` - TOML files with structured card data (costume.toml, accessory.toml, support.toml, sp_appeal.toml)
- `validators/` - Python scripts for data validation 
- `generate/` - Python scripts for converting TOML to JSON
- `dist/` - Generated JSON output directory
- `docs/` - Documentation including contribution guidelines
- `pages/` - Web interface files
- `flake.nix` - Nix development environment configuration

## Key Features
- Sophisticated Pydantic-based validation system with inheritance
- Type-specific card models (CostumeCard, AccessoryCard, SupportCard, SpAppealCard)
- Automated pre-commit validation hooks
- JSON generation from TOML data
- Strict card ID format validation (IMT-XX-XXX pattern)