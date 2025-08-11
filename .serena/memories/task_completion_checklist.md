# Task Completion Checklist

## When a task is completed, run these commands in order:

### 1. Code Quality Checks
- `ruff check` - Check for linting errors
- `ruff format` - Format code according to project standards

### 2. Data Validation 
- `uv run python ./validators/card_data.py` - Validate all TOML card data files
  - This is critical for data integrity
  - Must pass before any commits involving card data

### 3. Generate Output Data
- `uv run python ./generate/card_data.py` - Generate JSON output from TOML files
  - Creates/updates `dist/card_data.json`
  - Necessary for data distribution

### 4. Test Environment Setup
- Ensure `uv sync` has been run if dependencies changed
- Check that all files are properly formatted

### 5. Git Operations (if committing)
- `git add .` - Stage changes
- `git commit -m "descriptive message"` - Commit (triggers pre-commit hooks)
  - Pre-commit hooks will automatically run validation
  - Commit will fail if validation does not pass

## Important Notes
- Pre-commit hooks automatically validate card data changes
- All validation must pass before commits are accepted
- Follow one-card-per-PR policy for card data changes
- Program changes require issue discussion first

## Emergency Commands
- If pre-commit hooks fail, fix validation errors first
- Use `git status` to check current state
- Use `git diff` to see what changed