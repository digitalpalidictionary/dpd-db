#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Template validation utilities for Jinja2 templates.

This module provides tools for validating template functionality, including:
- Validating Jinja2 template functionality
- Detecting common template issues
- Command-line interface for validation
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from jinja2 import Environment, StrictUndefined
from jinja2.exceptions import TemplateError, UndefinedError

try:
    from exporter.jinja2_env import create_jinja2_env
except ImportError:
    from jinja2_env import create_jinja2_env


@dataclass
class ValidationResult:
    """Result of template validation.

    Attributes:
        is_valid: Whether the validation passed
        errors: List of error messages
        warnings: List of warning messages
        jinja2_output: Rendered output from Jinja2 template (if applicable)
        differences: List of differences between outputs
    """

    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    jinja2_output: str | None = None
    differences: list[str] = field(default_factory=list)


class TemplateValidator:
    """Validator for Jinja2 templates.

    This class provides methods to validate templates by:
    - Rendering templates with test data
    - Checking for common issues
    """

    def __init__(self) -> None:
        """Initialize the validator with Jinja2 environments."""
        # Standard environment for validation
        self.jinja2_env = create_jinja2_env(
            ".",  # Will be overridden when loading templates
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Strict environment for detecting undefined variables
        self.strict_jinja2_env = Environment(
            undefined=StrictUndefined,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def load_test_data(
        self, data_source: Path | dict[str, Any] | str
    ) -> dict[str, Any]:
        """Load test data from various sources.

        Args:
            data_source: Path to JSON file, dictionary, or JSON string

        Returns:
            Dictionary of test data

        Raises:
            FileNotFoundError: If JSON file doesn't exist
            json.JSONDecodeError: If JSON is invalid
        """
        if isinstance(data_source, dict):
            return data_source

        if isinstance(data_source, str):
            # Try to parse as JSON first
            try:
                return json.loads(data_source)
            except json.JSONDecodeError:
                # Treat as file path
                data_source = Path(data_source)

        if isinstance(data_source, Path):
            if not data_source.exists():
                raise FileNotFoundError(f"Test data file not found: {data_source}")

            content = data_source.read_text(encoding="utf-8")
            return json.loads(content)

        raise ValueError(f"Unsupported data source type: {type(data_source)}")

    def normalize_html(self, html: str) -> str:
        """Normalize HTML for comparison.

        Normalizes whitespace and formatting to allow for meaningful
        comparison between template outputs.

        Args:
            html: HTML content to normalize

        Returns:
            Normalized HTML string
        """
        # Replace multiple whitespace with single space
        normalized = re.sub(r"\s+", " ", html)
        # Remove whitespace between tags
        normalized = re.sub(r">\s+<", "><", normalized)
        # Strip leading/trailing whitespace
        return normalized.strip()

    def render_jinja2_template(
        self, template_path: Path, data: dict[str, Any], strict: bool = False
    ) -> str:
        """Render a Jinja2 template with the given data.

        Args:
            template_path: Path to the Jinja2 template file
            data: Dictionary of variables to pass to the template
            strict: Whether to use strict undefined handling

        Returns:
            Rendered template output

        Raises:
            TemplateError: If template rendering fails
            UndefinedError: If strict mode and undefined variables are used
        """
        content = template_path.read_text(encoding="utf-8")

        if strict:
            template = self.strict_jinja2_env.from_string(content)
        else:
            template = self.jinja2_env.from_string(content)

        return str(template.render(**data))

    def check_template_issues(self, jinja2_content: str) -> list[str]:
        """Check for common template issues.

        Args:
            jinja2_content: Content of the Jinja2 template

        Returns:
            List of detected issues
        """
        issues: list[str] = []

        # Check for remaining Mako variable syntax
        if re.search(r"\$\{[^}]+\}", jinja2_content):
            issues.append("Found remaining Mako variable syntax (${...})")

        # Check for remaining Mako control structures
        mako_control_patterns = [
            (r"^\s*%\s*if\s+", "Mako if statement"),
            (r"^\s*%\s*elif\s+", "Mako elif statement"),
            (r"^\s*%\s*else\s*:", "Mako else statement"),
            (r"^\s*%\s*endif", "Mako endif statement"),
            (r"^\s*%\s*for\s+", "Mako for loop"),
            (r"^\s*%\s*endfor", "Mako endfor statement"),
        ]

        for pattern, description in mako_control_patterns:
            if re.search(pattern, jinja2_content, re.MULTILINE):
                issues.append(f"Found remaining {description}")

        # Check for remaining Mako comments
        if re.search(r"##\s*\S", jinja2_content):
            issues.append("Found remaining Mako comment syntax (##)")

        # Check for Jinja2 syntax issues
        # Unclosed if statements
        if_count = len(re.findall(r"{%\s*if\s+", jinja2_content))
        endif_count = len(re.findall(r"{%\s*endif\s*%}", jinja2_content))
        if if_count != endif_count:
            issues.append(f"Mismatched if/endif: {if_count} if, {endif_count} endif")

        # Unclosed for loops
        for_count = len(re.findall(r"{%\s*for\s+", jinja2_content))
        endfor_count = len(re.findall(r"{%\s*endfor\s*%}", jinja2_content))
        if for_count != endfor_count:
            issues.append(
                f"Mismatched for/endfor: {for_count} for, {endfor_count} endfor"
            )

        return issues


def validate_jinja2_template(
    template_content: str,
    test_data: dict[str, Any],
    strict: bool = True,
) -> ValidationResult:
    """Validate a Jinja2 template by rendering it with test data.

    Args:
        template_content: The Jinja2 template content
        test_data: Dictionary of variables to pass to the template
        strict: Whether to use strict undefined variable handling

    Returns:
        ValidationResult with validation results
    """
    errors: list[str] = []
    warnings: list[str] = []
    output: str | None = None

    # Check for conversion issues first
    validator = TemplateValidator()
    conversion_issues = validator.check_template_issues(template_content)
    if conversion_issues:
        warnings.extend(conversion_issues)

    # Try to render the template
    try:
        if strict:
            env = Environment(
                undefined=StrictUndefined,
                trim_blocks=True,
                lstrip_blocks=True,
            )
        else:
            env = Environment(trim_blocks=True, lstrip_blocks=True)

        template = env.from_string(template_content)
        output = str(template.render(**test_data))
    except UndefinedError as e:
        errors.append(f"Undefined variable: {e}")
    except TemplateError as e:
        errors.append(f"Template syntax error: {e}")
    except Exception as e:
        errors.append(f"Unexpected error: {e}")

    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        jinja2_output=output,
    )


def main() -> int:
    """Main entry point for the CLI.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    parser = argparse.ArgumentParser(
        description="Validate Jinja2 templates.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --jinja-template template.html --test-data data.json
        """,
    )

    parser.add_argument(
        "--jinja-template",
        type=Path,
        required=True,
        help="Path to Jinja2 template",
    )

    parser.add_argument(
        "--test-data",
        type=Path,
        help="JSON file with test data for rendering",
    )

    parser.add_argument(
        "--strict",
        action="store_true",
        help="Use strict undefined variable handling",
    )

    args = parser.parse_args()

    # Check template file exists
    if not args.jinja_template.exists():
        print(
            f"Error: Jinja2 template not found: {args.jinja_template}", file=sys.stderr
        )
        return 1

    # Load test data
    test_data: dict[str, Any] = {}
    if args.test_data:
        if not args.test_data.exists():
            print(f"Error: Test data file not found: {args.test_data}", file=sys.stderr)
            return 1
        try:
            validator = TemplateValidator()
            test_data = validator.load_test_data(args.test_data)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in test data: {e}", file=sys.stderr)
            return 1

    # Perform validation
    template_content = args.jinja_template.read_text(encoding="utf-8")
    result = validate_jinja2_template(template_content, test_data, strict=args.strict)

    # Print results
    print("=" * 60)
    print("Template Validation Results")
    print("=" * 60)

    if result.is_valid:
        print("\n✓ Validation PASSED")
    else:
        print("\n✗ Validation FAILED")

    if result.errors:
        print(f"\nErrors ({len(result.errors)}):")
        for error in result.errors:
            print(f"  - {error}")

    if result.warnings:
        print(f"\nWarnings ({len(result.warnings)}):")
        for warning in result.warnings:
            print(f"  - {warning}")

    if result.jinja2_output is not None:
        print(f"\nJinja2 output length: {len(result.jinja2_output)} chars")

    print("=" * 60)

    return 0 if result.is_valid else 1


if __name__ == "__main__":
    sys.exit(main())
