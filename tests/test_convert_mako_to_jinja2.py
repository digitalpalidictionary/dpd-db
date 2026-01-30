# -*- coding: utf-8 -*-
"""Tests for the Mako to Jinja2 template converter."""

import tempfile
from pathlib import Path


from scripts.convert_mako_to_jinja2 import (
    convert_comment,
    convert_control_structure,
    convert_variable_expression,
    convert_mako_to_jinja2,
    process_file,
    process_directory,
)


class TestConvertVariableExpression:
    """Tests for converting Mako variable expressions to Jinja2."""

    def test_simple_variable(self) -> None:
        """Test converting simple variable expression."""
        mako = "${var}"
        expected = "{{ var }}"
        assert convert_variable_expression(mako) == expected

    def test_object_attribute(self) -> None:
        """Test converting object attribute access."""
        mako = "${i.lemma_1}"
        expected = "{{ i.lemma_1 }}"
        assert convert_variable_expression(mako) == expected

    def test_dictionary_access(self) -> None:
        """Test converting dictionary key access."""
        mako = "${i['abbrev']}"
        expected = "{{ i['abbrev'] }}"
        assert convert_variable_expression(mako) == expected

    def test_dictionary_access_double_quotes(self) -> None:
        """Test converting dictionary key access with double quotes."""
        mako = '${i["key"]}'
        expected = '{{ i["key"] }}'
        assert convert_variable_expression(mako) == expected

    def test_nested_attribute_access(self) -> None:
        """Test converting nested attribute access."""
        mako = "${i.rt.root_has_verb}"
        expected = "{{ i.rt.root_has_verb }}"
        assert convert_variable_expression(mako) == expected

    def test_method_call(self) -> None:
        """Test converting method call."""
        mako = "${text.strip()}"
        expected = "{{ text.strip() }}"
        assert convert_variable_expression(mako) == expected

    def test_method_call_with_args(self) -> None:
        """Test converting method call with arguments."""
        mako = "${text.replace('latn', 'deva')}"
        expected = "{{ text.replace('latn', 'deva') }}"
        assert convert_variable_expression(mako) == expected

    def test_multiple_variables_in_line(self) -> None:
        """Test converting multiple variables in a single line."""
        mako = "<p>${i.pos}. ${i.meaning_combo_html}</p>"
        expected = "<p>{{ i.pos }}. {{ i.meaning_combo_html }}</p>"
        assert convert_variable_expression(mako) == expected

    def test_variable_in_html_attribute(self) -> None:
        """Test converting variable in HTML attribute."""
        mako = '<div id="examples_${i.lemma_1_}" class="dpd">'
        expected = '<div id="examples_{{ i.lemma_1_ }}" class="dpd">'
        assert convert_variable_expression(mako) == expected

    def test_variable_in_url_parameter(self) -> None:
        """Test converting variable in URL parameter."""
        mako = '<a href="?entry=${i.id}">Link</a>'
        expected = '<a href="?entry={{ i.id }}">Link</a>'
        assert convert_variable_expression(mako) == expected


class TestConvertControlStructure:
    """Tests for converting Mako control structures to Jinja2."""

    def test_if_statement(self) -> None:
        """Test converting if statement."""
        mako = "% if condition:"
        expected = "{% if condition %}"
        assert convert_control_structure(mako) == expected

    def test_elif_statement(self) -> None:
        """Test converting elif statement."""
        mako = "% elif condition:"
        expected = "{% elif condition %}"
        assert convert_control_structure(mako) == expected

    def test_else_statement(self) -> None:
        """Test converting else statement."""
        mako = "% else:"
        expected = "{% else %}"
        assert convert_control_structure(mako) == expected

    def test_endif_statement(self) -> None:
        """Test converting endif statement."""
        mako = "% endif"
        expected = "{% endif %}"
        assert convert_control_structure(mako) == expected

    def test_for_loop(self) -> None:
        """Test converting for loop."""
        mako = "% for item in items:"
        expected = "{% for item in items %}"
        assert convert_control_structure(mako) == expected

    def test_endfor_statement(self) -> None:
        """Test converting endfor statement."""
        mako = "% endfor"
        expected = "{% endfor %}"
        assert convert_control_structure(mako) == expected

    def test_complex_condition(self) -> None:
        """Test converting if with complex condition."""
        mako = "% if i.meaning_1 and i.meaning_1 != '_':"
        expected = "{% if i.meaning_1 and i.meaning_1 != '_' %}"
        assert convert_control_structure(mako) == expected

    def test_if_with_not(self) -> None:
        """Test converting if with not operator."""
        mako = "% if not i.example_2:"
        expected = "{% if not i.example_2 %}"
        assert convert_control_structure(mako) == expected


class TestConvertComment:
    """Tests for converting Mako comments to Jinja2."""

    def test_single_line_comment(self) -> None:
        """Test converting single-line comment."""
        mako = "## This is a comment"
        expected = "{# This is a comment #}"
        assert convert_comment(mako) == expected

    def test_comment_with_leading_whitespace(self) -> None:
        """Test converting comment with leading whitespace."""
        mako = "    ## This is a comment"
        expected = "    {# This is a comment #}"
        assert convert_comment(mako) == expected

    def test_inline_comment(self) -> None:
        """Test converting inline comment."""
        mako = "<p>Content</p> ## End of content"
        expected = "<p>Content</p> {# End of content #}"
        assert convert_comment(mako) == expected


class TestConvertMakoToJinja2:
    """Tests for full Mako to Jinja2 conversion."""

    def test_simple_template(self) -> None:
        """Test converting a simple template."""
        mako = """<h1>${title}</h1>
<p>${content}</p>"""
        expected = """<h1>{{ title }}</h1>
<p>{{ content }}</p>"""
        assert convert_mako_to_jinja2(mako) == expected

    def test_template_with_if_statement(self) -> None:
        """Test converting template with if statement."""
        mako = """% if i.plus_case:
    <span>(${i.plus_case})</span>
% endif"""
        expected = """{% if i.plus_case %}
    <span>({{ i.plus_case }})</span>
{% endif %}"""
        assert convert_mako_to_jinja2(mako) == expected

    def test_template_with_if_else(self) -> None:
        """Test converting template with if/else."""
        mako = """% if active:
    <span>Active</span>
% else:
    <span>Inactive</span>
% endif"""
        expected = """{% if active %}
    <span>Active</span>
{% else %}
    <span>Inactive</span>
{% endif %}"""
        assert convert_mako_to_jinja2(mako) == expected

    def test_template_with_for_loop(self) -> None:
        """Test converting template with for loop."""
        mako = """% for d in deconstructions:
    <p>${d}</p>
% endfor"""
        expected = """{% for d in deconstructions %}
    <p>{{ d }}</p>
{% endfor %}"""
        assert convert_mako_to_jinja2(mako) == expected

    def test_template_with_comments(self) -> None:
        """Test converting template with comments."""
        mako = """## Header section
<h1>${title}</h1>
## Content section
<p>${content}</p>"""
        expected = """{# Header section #}
<h1>{{ title }}</h1>
{# Content section #}
<p>{{ content }}</p>"""
        assert convert_mako_to_jinja2(mako) == expected

    def test_complex_template(self) -> None:
        """Test converting a complex template with multiple constructs."""
        mako = """% if i.example_1 and i.example_2:
    <div id="examples_${i.lemma_1_}" class="dpd content hidden">
% elif i.example_1 and not i.example_2:
    <div id="example_${i.lemma_1_}" class="dpd content hidden">
% else:
    <div class="dpd content">
% endif
    <p>${i.meaning_1}</p>
</div>

% for item in items:
    <span>${item}</span>
% endfor"""
        expected = """{% if i.example_1 and i.example_2 %}
    <div id="examples_{{ i.lemma_1_ }}" class="dpd content hidden">
{% elif i.example_1 and not i.example_2 %}
    <div id="example_{{ i.lemma_1_ }}" class="dpd content hidden">
{% else %}
    <div class="dpd content">
{% endif %}
    <p>{{ i.meaning_1 }}</p>
</div>

{% for item in items %}
    <span>{{ item }}</span>
{% endfor %}"""
        assert convert_mako_to_jinja2(mako) == expected

    def test_nested_control_structures(self) -> None:
        """Test converting nested control structures."""
        mako = """% if i.family_set:
    <div class="family_set">
    % for f in i.family_set_list:
        % if f:
            <p>${f}</p>
        % endif
    % endfor
    </div>
% endif"""
        expected = """{% if i.family_set %}
    <div class="family_set">
    {% for f in i.family_set_list %}
        {% if f %}
            <p>{{ f }}</p>
        {% endif %}
    {% endfor %}
    </div>
{% endif %}"""
        assert convert_mako_to_jinja2(mako) == expected

    def test_dictionary_access_in_template(self) -> None:
        """Test converting template with dictionary access."""
        mako = """${i.freq_data_unpack["FreqHeading"]}
${i['abbrev']}"""
        expected = """{{ i.freq_data_unpack["FreqHeading"] }}
{{ i['abbrev'] }}"""
        assert convert_mako_to_jinja2(mako) == expected

    def test_method_calls_in_template(self) -> None:
        """Test converting template with method calls."""
        mako = """${text.strip().upper()}
${url.replace('latn', 'deva')}"""
        expected = """{{ text.strip().upper() }}
{{ url.replace('latn', 'deva') }}"""
        assert convert_mako_to_jinja2(mako) == expected


class TestProcessFile:
    """Tests for file processing functionality."""

    def test_process_single_file(self) -> None:
        """Test processing a single file."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_file = Path(tmp_dir) / "test.html"
            output_file = Path(tmp_dir) / "output.html"
            input_file.write_text("<h1>${title}</h1>")

            process_file(input_file, output_file)

            result = output_file.read_text()
            assert result == "<h1>{{ title }}</h1>"

    def test_process_file_dry_run(self) -> None:
        """Test dry-run mode doesn't write files."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_file = Path(tmp_dir) / "test.html"
            output_file = Path(tmp_dir) / "output.html"
            input_file.write_text("<h1>${title}</h1>")

            process_file(input_file, output_file, dry_run=True)

            assert not output_file.exists()

    def test_process_file_creates_directories(self) -> None:
        """Test that output directories are created if needed."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_file = Path(tmp_dir) / "test.html"
            output_file = Path(tmp_dir) / "nested" / "dir" / "output.html"
            input_file.write_text("<h1>${title}</h1>")

            process_file(input_file, output_file)

            assert output_file.exists()


class TestProcessDirectory:
    """Tests for directory processing functionality."""

    def test_process_directory(self) -> None:
        """Test processing all files in a directory."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_dir = Path(tmp_dir) / "input"
            output_dir = Path(tmp_dir) / "output"
            input_dir.mkdir()

            (input_dir / "file1.html").write_text("<h1>${title}</h1>")
            (input_dir / "file2.html").write_text("<p>${content}</p>")

            process_directory(input_dir, output_dir)

            assert (output_dir / "file1.html").exists()
            assert (output_dir / "file2.html").exists()
            assert (output_dir / "file1.html").read_text() == "<h1>{{ title }}</h1>"
            assert (output_dir / "file2.html").read_text() == "<p>{{ content }}</p>"

    def test_process_directory_nested(self) -> None:
        """Test processing nested directories."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_dir = Path(tmp_dir) / "input"
            output_dir = Path(tmp_dir) / "output"
            nested_dir = input_dir / "nested"
            nested_dir.mkdir(parents=True)

            (input_dir / "root.html").write_text("${root_var}")
            (nested_dir / "nested.html").write_text("${nested_var}")

            process_directory(input_dir, output_dir)

            assert (output_dir / "root.html").exists()
            assert (output_dir / "nested" / "nested.html").exists()
            assert (
                output_dir / "nested" / "nested.html"
            ).read_text() == "{{ nested_var }}"

    def test_process_directory_dry_run(self) -> None:
        """Test dry-run mode for directories."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_dir = Path(tmp_dir) / "input"
            output_dir = Path(tmp_dir) / "output"
            input_dir.mkdir()

            (input_dir / "file.html").write_text("<h1>${title}</h1>")

            process_directory(input_dir, output_dir, dry_run=True)

            assert not output_dir.exists()


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_empty_template(self) -> None:
        """Test converting empty template."""
        mako = ""
        expected = ""
        assert convert_mako_to_jinja2(mako) == expected

    def test_no_mako_syntax(self) -> None:
        """Test converting template without Mako syntax."""
        mako = "<h1>Plain HTML</h1>"
        expected = "<h1>Plain HTML</h1>"
        assert convert_mako_to_jinja2(mako) == expected

    def test_dollar_sign_not_variable(self) -> None:
        """Test that dollar signs not followed by brace are preserved."""
        mako = "Price: $50.00"
        expected = "Price: $50.00"
        assert convert_mako_to_jinja2(mako) == expected

    def test_variable_at_line_start(self) -> None:
        """Test variable at the start of a line."""
        mako = "${var}\nMore text"
        expected = "{{ var }}\nMore text"
        assert convert_mako_to_jinja2(mako) == expected

    def test_control_structure_with_leading_whitespace(self) -> None:
        """Test control structure with leading whitespace."""
        mako = "    % if condition:"
        expected = "    {% if condition %}"
        assert convert_control_structure(mako) == expected

    def test_multiple_consecutive_variables(self) -> None:
        """Test multiple consecutive variables."""
        mako = "${a}${b}${c}"
        expected = "{{ a }}{{ b }}{{ c }}"
        assert convert_mako_to_jinja2(mako) == expected

    def test_variable_in_javascript(self) -> None:
        """Test variable in JavaScript context."""
        mako = """<script>
var data_${i.lemma_1_} = {
    "id": ${i.id},
    "lemma": "${i.lemma_1}"
};
</script>"""
        expected = """<script>
var data_{{ i.lemma_1_ }} = {
    "id": {{ i.id }},
    "lemma": "{{ i.lemma_1 }}"
};
</script>"""
        assert convert_mako_to_jinja2(mako) == expected
