# Suggested Commands

## Python Environment
- `uv run python <script>` - Run Python scripts using uv
- `uv sync` - Sync dependencies after modifying pyproject.toml
- `uv add <package>` - Add new Python packages

## Development Environment
- `nix develop` - Enter the Nix development environment
- `nix fmt` - Format Nix files with treefmt

## Linting and Formatting
- `ruff check` - Run linter (use instead of flake8)
- `ruff format` - Format code

## Data Validation and Testing
- `uv run python ./validators/card_data.py` - Validate all card data TOML files
- Pre-commit hooks automatically validate card data when committing changes to `card_data/`

## Data Generation
- `uv run python ./generate/card_data.py` - Convert TOML files to JSON output in `./dist/card_data.json`

## Git and Version Control
- `git add .` - Stage all changes
- `git commit -m "message"` - Commit changes (triggers pre-commit hooks)
- `git push` - Push changes to remote

## System Utilities (Linux)
- `ls` - List directory contents
- `cd` - Change directory
- `grep` - Search text patterns
- `find` - Find files and directories
- `cat` - Display file contents
- `head/tail` - Display file beginning/end