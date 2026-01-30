"""Test to verify Jinja2 is properly installed and functional."""

import jinja2


def test_jinja2_import():
    """Verify jinja2 can be imported."""
    assert jinja2 is not None


def test_jinja2_version():
    """Verify jinja2 version is available."""
    version = jinja2.__version__
    assert version is not None
    assert isinstance(version, str)
    assert len(version) > 0


def test_basic_template_rendering():
    """Test basic template rendering functionality."""
    template_string = "Hello, {{ name }}!"
    template = jinja2.Template(template_string)
    result = template.render(name="World")
    assert result == "Hello, World!"


def test_template_with_conditionals():
    """Test template rendering with conditionals."""
    template_string = "{% if active %}Active{% else %}Inactive{% endif %}"
    template = jinja2.Template(template_string)
    assert template.render(active=True) == "Active"
    assert template.render(active=False) == "Inactive"


def test_template_with_loops():
    """Test template rendering with loops."""
    template_string = "{% for item in items %}{{ item }}{% endfor %}"
    template = jinja2.Template(template_string)
    result = template.render(items=["a", "b", "c"])
    assert result == "abc"
