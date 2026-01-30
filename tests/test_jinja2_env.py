# -*- coding: utf-8 -*-
"""Tests for the Jinja2 environment setup utility."""

import tempfile
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from exporter.jinja2_env import create_jinja2_env, get_webapp_jinja2_env


class TestCreateJinja2Env:
    """Tests for the create_jinja2_env function."""

    def test_environment_initialization_with_correct_loader(self) -> None:
        """Test that the environment is initialized with a FileSystemLoader."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            env = create_jinja2_env(tmp_dir)

            assert isinstance(env, Environment)
            assert isinstance(env.loader, FileSystemLoader)

    def test_templates_can_be_loaded_from_directory(self) -> None:
        """Test that templates can be loaded from the specified directory."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            template_path = Path(tmp_dir) / "test_template.html"
            template_path.write_text("<h1>Hello {{ name }}</h1>")

            env = create_jinja2_env(tmp_dir)
            template = env.get_template("test_template.html")
            result = template.render(name="World")

            assert "<h1>Hello World</h1>" in result

    def test_autoescaping_is_enabled_by_default(self) -> None:
        """Test that auto-escaping is enabled by default for HTML."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            template_path = Path(tmp_dir) / "test_template.html"
            template_path.write_text("<p>{{ content }}</p>")

            env = create_jinja2_env(tmp_dir)
            template = env.get_template("test_template.html")
            result = template.render(content="<script>alert('xss')</script>")

            # Script tag should be escaped
            assert "<script>" not in result
            assert "&lt;script&gt;" in result

    def test_autoescaping_can_be_disabled(self) -> None:
        """Test that auto-escaping can be disabled."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            template_path = Path(tmp_dir) / "test_template.html"
            template_path.write_text("<p>{{ content }}</p>")

            env = create_jinja2_env(tmp_dir, autoescape=False)
            template = env.get_template("test_template.html")
            result = template.render(content="<b>Bold</b>")

            assert "<b>Bold</b>" in result

    def test_environment_renders_templates_correctly(self) -> None:
        """Test that the environment correctly renders templates with variables."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            template_path = Path(tmp_dir) / "test_template.html"
            template_path.write_text("""
<!DOCTYPE html>
<html>
<head><title>{{ title }}</title></head>
<body>
    <h1>{{ heading }}</h1>
    <p>Count: {{ count }}</p>
    {% if items %}
    <ul>
        {% for item in items %}
        <li>{{ item }}</li>
        {% endfor %}
    </ul>
    {% endif %}
</body>
</html>
""")

            env = create_jinja2_env(tmp_dir)
            template = env.get_template("test_template.html")
            result = template.render(
                title="Test Page",
                heading="Welcome",
                count=42,
                items=["one", "two", "three"],
            )

            assert "<title>Test Page</title>" in result
            assert "<h1>Welcome</h1>" in result
            assert "<p>Count: 42</p>" in result
            assert "<li>one</li>" in result
            assert "<li>two</li>" in result
            assert "<li>three</li>" in result

    def test_trim_blocks_is_enabled(self) -> None:
        """Test that trim_blocks is enabled by default."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            template_path = Path(tmp_dir) / "test_template.html"
            template_path.write_text("""{% if True %}
content
{% endif %}""")

            env = create_jinja2_env(tmp_dir)
            template = env.get_template("test_template.html")
            result = template.render()

            # trim_blocks removes the first newline after a block
            assert "content" in result

    def test_lstrip_blocks_is_enabled(self) -> None:
        """Test that lstrip_blocks is enabled by default."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            template_path = Path(tmp_dir) / "test_template.html"
            template_path.write_text("""    {% if True %}
    content
    {% endif %}""")

            env = create_jinja2_env(tmp_dir)
            template = env.get_template("test_template.html")
            result = template.render()

            assert "    content" in result

    def test_additional_options_can_be_passed(self) -> None:
        """Test that additional Jinja2 options can be passed."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            env = create_jinja2_env(
                tmp_dir,
                cache_size=100,
                auto_reload=False,
            )

            assert env.cache is not None


class TestGetWebappJinja2Env:
    """Tests for the get_webapp_jinja2_env function."""

    def test_returns_configured_environment(self) -> None:
        """Test that get_webapp_jinja2_env returns a properly configured environment."""
        env = get_webapp_jinja2_env()

        assert isinstance(env, Environment)
        assert isinstance(env.loader, FileSystemLoader)

    def test_can_load_webapp_templates(self) -> None:
        """Test that the environment can load actual webapp templates."""
        env = get_webapp_jinja2_env()

        template_names = [
            "home.html",
            "dpd_headword.html",
            "header.html",
        ]

        for template_name in template_names:
            template = env.get_template(template_name)
            assert template is not None


class TestIntegration:
    """Integration tests for the Jinja2 environment."""

    def test_complex_template_rendering(self) -> None:
        """Test rendering of a complex template with various Jinja2 features."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            template_path = Path(tmp_dir) / "complex.html"
            template_path.write_text("""<!DOCTYPE html>
<html>
<head><title>{{ title }}</title></head>
<body>
    {% set greeting = "Hello" %}
    <h1>{{ greeting }}, {{ user.name }}!</h1>

    {% if user.is_admin %}
    <div class="admin">Admin Panel</div>
    {% endif %}

    {% for section in sections %}
    <section id="{{ section.id }}">
        <h2>{{ section.title }}</h2>
        <p>{{ section.content|safe }}</p>
    </section>
    {% endfor %}

    {% macro render_button(text, type='button') %}
    <button type="{{ type }}">{{ text }}</button>
    {% endmacro %}

    {{ render_button('Click me', 'submit') }}
</body>
</html>""")

            env = create_jinja2_env(tmp_dir)
            template = env.get_template("complex.html")

            result = template.render(
                title="Test Page",
                user={"name": "John", "is_admin": True},
                sections=[
                    {
                        "id": "sec1",
                        "title": "Section 1",
                        "content": "<em>Content 1</em>",
                    },
                    {
                        "id": "sec2",
                        "title": "Section 2",
                        "content": "<strong>Content 2</strong>",
                    },
                ],
            )

            assert "<title>Test Page</title>" in result
            assert "<h1>Hello, John!</h1>" in result
            assert '<div class="admin">Admin Panel</div>' in result
            assert '<section id="sec1">' in result
            assert "<h2>Section 1</h2>" in result
            assert "<em>Content 1</em>" in result
            assert '<button type="submit">Click me</button>' in result

    def test_html_escaping_with_safe_filter(self) -> None:
        """Test that HTML is properly escaped except when using |safe filter."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            template_path = Path(tmp_dir) / "escape_test.html"
            template_path.write_text("""
<p>Escaped: {{ user_input }}</p>
<p>Safe: {{ trusted_html|safe }}</p>
""")

            env = create_jinja2_env(tmp_dir)
            template = env.get_template("escape_test.html")

            result = template.render(
                user_input="<script>alert('xss')</script>",
                trusted_html="<b>Bold Text</b>",
            )

            # User input should be escaped
            assert "&lt;script&gt;" in result
            # Trusted HTML with |safe filter should not be escaped
            assert "<b>Bold Text</b>" in result
