# -*- coding: utf-8 -*-
"""Tests for the template validation utilities.

This module provides comprehensive tests for validating Jinja2
template functionality.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from jinja2 import Environment

from exporter.template_validator import (
    TemplateValidator,
    ValidationResult,
    validate_jinja2_template,
    main,
)


class TestValidationResult:
    """Tests for the ValidationResult dataclass."""

    def test_validation_result_creation(self) -> None:
        """Test creating a ValidationResult."""
        result = ValidationResult(
            is_valid=True,
            errors=[],
            warnings=["Minor issue"],
            jinja2_output="<p>Test</p>",
            differences=[],
        )
        assert result.is_valid is True
        assert result.errors == []
        assert result.warnings == ["Minor issue"]
        assert result.jinja2_output == "<p>Test</p>"
        assert result.differences == []

    def test_validation_result_with_errors(self) -> None:
        """Test ValidationResult with errors."""
        result = ValidationResult(
            is_valid=False,
            errors=["Template syntax error"],
            warnings=[],
            jinja2_output=None,
            differences=[],
        )
        assert result.is_valid is False
        assert len(result.errors) == 1


class TestTemplateValidator:
    """Tests for the TemplateValidator class."""

    def test_validator_initialization(self) -> None:
        """Test that validator initializes correctly."""
        validator = TemplateValidator()
        assert validator is not None
        assert isinstance(validator.jinja2_env, Environment)
        assert isinstance(validator.strict_jinja2_env, Environment)

    def test_load_test_data_from_json(self) -> None:
        """Test loading test data from JSON file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"name": "Test", "items": ["a", "b", "c"]}, f)
            temp_path = f.name

        try:
            validator = TemplateValidator()
            data = validator.load_test_data(Path(temp_path))
            assert data["name"] == "Test"
            assert data["items"] == ["a", "b", "c"]
        finally:
            Path(temp_path).unlink()

    def test_load_test_data_from_dict(self) -> None:
        """Test loading test data from dictionary."""
        validator = TemplateValidator()
        data = {"key": "value", "number": 42}
        result = validator.load_test_data(data)
        assert result == data

    def test_normalize_html_whitespace(self) -> None:
        """Test HTML whitespace normalization."""
        validator = TemplateValidator()
        html = "<p>  Multiple   spaces   </p>\n\n<p>New line</p>"
        normalized = validator.normalize_html(html)
        assert normalized == "<p> Multiple spaces </p><p>New line</p>"

    def test_normalize_html_preserves_structure(self) -> None:
        """Test that normalization preserves HTML structure."""
        validator = TemplateValidator()
        html = "<div><p>Content</p></div>"
        normalized = validator.normalize_html(html)
        assert normalized == html


class TestValidateJinja2Template:
    """Tests for validating Jinja2 templates."""

    def test_valid_template(self) -> None:
        """Test validation of a valid Jinja2 template."""
        template_content = "<h1>{{ title }}</h1><p>{{ content }}</p>"
        test_data = {"title": "Test", "content": "Content"}

        result = validate_jinja2_template(template_content, test_data)

        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_template_syntax_error(self) -> None:
        """Test detection of syntax errors."""
        template_content = "<h1>{{ title</h1>"  # Missing closing braces
        test_data = {"title": "Test"}

        result = validate_jinja2_template(template_content, test_data)

        assert result.is_valid is False
        assert len(result.errors) > 0

    def test_missing_variables(self) -> None:
        """Test detection of missing variables."""
        template_content = "<h1>{{ title }}</h1><p>{{ missing_var }}</p>"
        test_data = {"title": "Test"}

        result = validate_jinja2_template(template_content, test_data)

        assert result.is_valid is False
        assert any("missing_var" in str(error) for error in result.errors)

    def test_undefined_variable_strictness(self) -> None:
        """Test strict undefined variable handling."""
        template_content = "<p>{{ undefined_var }}</p>"
        test_data = {}

        result = validate_jinja2_template(template_content, test_data, strict=True)

        assert result.is_valid is False

    def test_complex_template_validation(self) -> None:
        """Test validation of complex template with multiple features."""
        template_content = """
<!DOCTYPE html>
<html>
<head><title>{{ title }}</title></head>
<body>
    {% if user.is_admin %}
        <div class="admin">Admin Panel</div>
    {% endif %}
    {% for item in items %}
        <p>{{ item.name }}: {{ item.value }}</p>
    {% endfor %}
</body>
</html>
"""
        test_data = {
            "title": "Test Page",
            "user": {"is_admin": True},
            "items": [
                {"name": "Item 1", "value": 100},
                {"name": "Item 2", "value": 200},
            ],
        }

        result = validate_jinja2_template(template_content, test_data)

        assert result.is_valid is True


class TestCommandLineInterface:
    """Tests for the command-line interface."""

    @patch("argparse.ArgumentParser.parse_args")
    def test_cli_missing_jinja_template(self, mock_parse_args) -> None:
        """Test CLI with non-existent Jinja2 template."""
        mock_parse_args.return_value = MagicMock(
            jinja_template=Path("/nonexistent/jinja.html"),
            test_data=None,
            strict=False,
        )

        result = main()
        assert result == 1

    @patch("argparse.ArgumentParser.parse_args")
    def test_cli_missing_test_data(self, mock_parse_args) -> None:
        """Test CLI with missing test data file."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            jinja_template = Path(tmp_dir) / "jinja.html"

            jinja_template.write_text("<h1>{{ title }}</h1>")

            mock_parse_args.return_value = MagicMock(
                jinja_template=jinja_template,
                test_data=Path("/nonexistent/data.json"),
                strict=False,
            )

            result = main()
            assert result == 1


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_empty_template(self) -> None:
        """Test validation of empty template."""
        template_content = ""
        test_data = {}

        result = validate_jinja2_template(template_content, test_data)

        assert result.is_valid is True

    def test_template_with_only_html(self) -> None:
        """Test validation of template with only HTML."""
        template_content = "<h1>Static Content</h1>"
        test_data = {}

        result = validate_jinja2_template(template_content, test_data)

        assert result.is_valid is True

    def test_unicode_content(self) -> None:
        """Test validation with unicode content."""
        template_content = "<h1>{{ title }}</h1>"
        test_data = {"title": "Pāḷi Dictionary 中文"}

        result = validate_jinja2_template(template_content, test_data)

        assert result.is_valid is True
        assert result.jinja2_output is not None
        assert "Pāḷi Dictionary 中文" in result.jinja2_output

    def test_nested_objects(self) -> None:
        """Test validation with nested object access."""
        template_content = "<p>{{ user.profile.name }}</p>"
        test_data = {"user": {"profile": {"name": "John"}}}

        result = validate_jinja2_template(template_content, test_data)

        assert result.is_valid is True

    def test_method_calls(self) -> None:
        """Test validation with method calls."""
        template_content = "<p>{{ text.upper() }}</p>"
        test_data = {"text": "hello"}

        result = validate_jinja2_template(template_content, test_data)

        assert result.is_valid is True
        assert result.jinja2_output is not None
        assert "HELLO" in result.jinja2_output

    def test_filters(self) -> None:
        """Test validation with Jinja2 filters."""
        template_content = "<p>{{ items|length }}</p>"
        test_data = {"items": ["a", "b", "c"]}

        result = validate_jinja2_template(template_content, test_data)

        assert result.is_valid is True
        assert result.jinja2_output is not None
        assert "3" in result.jinja2_output


class TestCommonConversionIssues:
    """Tests for detecting common Mako to Jinja2 conversion issues."""

    def test_remaining_mako_syntax(self) -> None:
        """Test detection of remaining Mako syntax in Jinja2 template."""
        validator = TemplateValidator()

        # Template with remaining Mako syntax
        jinja_content = "<h1>${title}</h1>  ## This is a comment"

        issues = validator.check_template_issues(jinja_content)

        assert any("Mako variable syntax" in issue for issue in issues)
        assert any("Mako comment syntax" in issue for issue in issues)

    def test_remaining_mako_control_structures(self) -> None:
        """Test detection of remaining Mako control structures."""
        validator = TemplateValidator()

        jinja_content = """
% if condition:
    <p>Content</p>
% endif
"""

        issues = validator.check_template_issues(jinja_content)

        assert any("Mako if statement" in issue for issue in issues)
        assert any("Mako endif statement" in issue for issue in issues)

    def test_jinja2_syntax_errors(self) -> None:
        """Test detection of Jinja2 syntax errors."""
        validator = TemplateValidator()

        jinja_content = "{% if condition %}<p>Content</p>"  # Missing endif

        issues = validator.check_template_issues(jinja_content)

        assert len(issues) > 0

    def test_no_issues_in_valid_jinja2(self) -> None:
        """Test that valid Jinja2 has no issues."""
        validator = TemplateValidator()

        jinja_content = "<h1>{{ title }}</h1>{% if show %}<p>Content</p>{% endif %}"

        issues = validator.check_template_issues(jinja_content)

        assert len(issues) == 0
