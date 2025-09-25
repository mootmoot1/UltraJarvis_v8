# UltraJarvis Coding Constitution

## General Principles
- Code must be clean, readable, and maintainable.
- Follow PEP 8 style guidelines for Python code.
- Use type hints for all function signatures.

## Documentation
- Every function must have a docstring explaining its purpose and usage.
- Public classes and modules should have a top-level docstring.

## Testing
- Write unit tests for all new features and bug fixes.
- Use pytest for testing; tests should be located in the `tests/` directory.
- Aim for at least 80% test coverage.

## Code Quality
- Use `ruff` for linting and `black` for code formatting.
- Ensure code passes all linting and formatting checks before merging.

## Dependencies
- Only use standard library modules unless absolutely necessary.
- External dependencies must be listed in `requirements.txt` and should be minimal.

## Version Control
- Commit messages should be clear and descriptive.
- Use branches for new features and bug fixes, merging into `main` only after review.

## Python Version
- Ensure compatibility with Python 3.10 or later. Avoid using syntax or features that are not supported in these versions.