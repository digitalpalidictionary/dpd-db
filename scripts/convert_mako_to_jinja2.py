#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mako to Jinja2 template converter.

This script converts Mako template files to Jinja2 syntax using the following rules:
- ${var} -> {{ var }}
- % if condition: -> {% if condition %}
- % elif condition: -> {% elif condition %}
- % else: -> {% else %}
- % endif -> {% endif %}
- % for item in items: -> {% for item in items %}
- % endfor -> {% endfor %}
- ## comment -> {# comment #}
"""

import argparse
import re
import sys
from pathlib import Path


def convert_variable_expression(content: str) -> str:
    """Convert Mako variable expressions ${...} to Jinja2 {{ ... }}.

    Args:
        content: The template content containing Mako variable expressions.

    Returns:
        The content with Mako variable expressions converted to Jinja2.
    """
    # Match ${...} but not $ followed by non-brace characters
    # Handle nested braces for method calls with arguments
    pattern = r"\$\{([^}]+(?:\{[^}]*\}[^}]*)*)\}"

    def replace_var(match: re.Match) -> str:
        var_content = match.group(1)
        return f"{{{{ {var_content} }}}}"

    return re.sub(pattern, replace_var, content)


def convert_control_structure(content: str) -> str:
    """Convert Mako control structures to Jinja2.

    Args:
        content: The template content containing Mako control structures.

    Returns:
        The content with Mako control structures converted to Jinja2.
    """
    # Convert % if condition: -> {% if condition %}
    content = re.sub(
        r"^([ \t]*)%\s*if\s+(.+?):$", r"\1{% if \2 %}", content, flags=re.MULTILINE
    )

    # Convert % elif condition: -> {% elif condition %}
    content = re.sub(
        r"^([ \t]*)%\s*elif\s+(.+?):$", r"\1{% elif \2 %}", content, flags=re.MULTILINE
    )

    # Convert % else: -> {% else %}
    content = re.sub(
        r"^([ \t]*)%\s*else:\s*$", r"\1{% else %}", content, flags=re.MULTILINE
    )

    # Convert % endif -> {% endif %}
    content = re.sub(
        r"^([ \t]*)%\s*endif\s*$", r"\1{% endif %}", content, flags=re.MULTILINE
    )

    # Convert % for item in items: -> {% for item in items %}
    content = re.sub(
        r"^([ \t]*)%\s*for\s+(.+?):$", r"\1{% for \2 %}", content, flags=re.MULTILINE
    )

    # Convert % endfor -> {% endfor %}
    content = re.sub(
        r"^([ \t]*)%\s*endfor\s*$", r"\1{% endfor %}", content, flags=re.MULTILINE
    )

    return content


def convert_comment(content: str) -> str:
    """Convert Mako comments to Jinja2 comments.

    Args:
        content: The template content containing Mako comments.

    Returns:
        The content with Mako comments converted to Jinja2.
    """
    # Convert ## comment -> {# comment #}
    # Match ## at the start of a line or after whitespace, followed by the comment text
    content = re.sub(
        r"(^|[ \t])##\s*(.*?)$", r"\1{# \2 #}", content, flags=re.MULTILINE
    )

    return content


def convert_mako_to_jinja2(content: str) -> str:
    """Convert Mako template syntax to Jinja2.

    Args:
        content: The Mako template content.

    Returns:
        The content converted to Jinja2 syntax.
    """
    # Apply conversions in order
    content = convert_comment(content)
    content = convert_control_structure(content)
    content = convert_variable_expression(content)

    return content


def process_file(input_path: Path, output_path: Path, dry_run: bool = False) -> bool:
    """Process a single Mako template file and convert it to Jinja2.

    Args:
        input_path: Path to the input Mako template file.
        output_path: Path where the converted Jinja2 template will be written.
        dry_run: If True, don't write any files, just show what would be done.

    Returns:
        True if the file was processed successfully, False otherwise.
    """
    try:
        content = input_path.read_text(encoding="utf-8")
        converted = convert_mako_to_jinja2(content)

        if dry_run:
            print(f"[DRY-RUN] Would convert: {input_path} -> {output_path}")
            return True

        # Create output directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)

        output_path.write_text(converted, encoding="utf-8")
        print(f"Converted: {input_path} -> {output_path}")
        return True

    except Exception as e:
        print(f"Error processing {input_path}: {e}", file=sys.stderr)
        return False


def process_directory(
    input_dir: Path, output_dir: Path, dry_run: bool = False
) -> tuple[int, int]:
    """Process all HTML template files in a directory.

    Args:
        input_dir: Path to the input directory containing Mako templates.
        output_dir: Path where the converted Jinja2 templates will be written.
        dry_run: If True, don't write any files, just show what would be done.

    Returns:
        A tuple of (success_count, total_count).
    """
    success_count = 0
    total_count = 0

    for input_path in input_dir.rglob("*.html"):
        # Calculate relative path and corresponding output path
        rel_path = input_path.relative_to(input_dir)
        output_path = output_dir / rel_path

        total_count += 1
        if process_file(input_path, output_path, dry_run):
            success_count += 1

    return success_count, total_count


def main() -> int:
    """Main entry point for the converter script.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    parser = argparse.ArgumentParser(
        description="Convert Mako template files to Jinja2 syntax.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s -i template.html -o converted.html
  %(prog)s -i templates/ -o converted_templates/
  %(prog)s -i templates/ -o converted_templates/ --dry-run
        """,
    )

    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        required=True,
        help="Input file or directory containing Mako templates",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        required=True,
        help="Output file or directory for converted Jinja2 templates",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be converted without writing files",
    )

    args = parser.parse_args()

    if not args.input.exists():
        print(f"Error: Input path does not exist: {args.input}", file=sys.stderr)
        return 1

    if args.input.is_file():
        success = process_file(args.input, args.output, args.dry_run)
        return 0 if success else 1
    elif args.input.is_dir():
        success_count, total_count = process_directory(
            args.input, args.output, args.dry_run
        )
        print(f"\nProcessed {success_count}/{total_count} files successfully")
        return 0 if success_count == total_count else 1
    else:
        print(
            f"Error: Input path is neither a file nor a directory: {args.input}",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
