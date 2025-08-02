# DPD Database - Agent Guidelines

## Build/Lint/Test Commands
- **Lint**: `ruff check .`
- **Format**: `black .`
- **Type check**: `pyright`

## Code Style Guidelines
- **Imports**: Use absolute imports, group standard library, third-party, and local imports
- **Formatting**: Black formatter with 88-character line length
- **Types**: Use type hints consistently (Python 3.12+), `typing` module for complex types
- **Naming**: snake_case for variables/functions, PascalCase for classes, UPPER_CASE for constants
- **Error handling**: Use specific exceptions, avoid bare `except:`, log errors appropriately
- **Docstrings**: Use triple quotes for module/class/function documentation
- **SQLAlchemy**: Use modern 2.0 style with typed Mapped columns and declarative base