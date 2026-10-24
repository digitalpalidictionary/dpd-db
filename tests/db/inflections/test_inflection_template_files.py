"""Tests for db/inflections/inflection_template_files.py

Round trip of template data through the TSV files, every loader check,
and rename / remove updating both the index and the grid files.
The real committed files are tested separately (real-data tests below).
"""

import pytest
from db.inflections.inflection_template_files import (
    TemplateFile,
    load_templates,
    remove_template,
    rename_template,
    write_template,
)
from tools.paths import ProjectPaths


def make_template() -> TemplateFile:
    """A 3-row template with a multi-form cell and an empty cell."""
    return TemplateFile(
        pattern="test pr",
        like="kāraka",
        data=[
            [[""], ["sg"], [""], ["pl"], [""]],
            [["pr 3rd"], ["ati"], ["pr 3rd sg"], ["anti"], ["pr 3rd pl"]],
            [["pr 2nd"], ["asi", "ase"], ["pr 2nd sg"], [""], ["pr 2nd pl"]],
            [["pr 1st"], ["āmi"], ["pr 1st sg"], ["āma"], ["pr 1st pl"]],
        ],
    )


def write_grid_raw(lines: list[list[str]], templates_dir, name: str) -> None:
    """Hand-write a grid file, bypassing write_template's checks."""
    templates_dir.mkdir(parents=True, exist_ok=True)
    path = templates_dir / f"{name}.tsv"
    text = "\n".join("\t".join(line) for line in lines) + "\n"
    path.write_text(text, encoding="utf-8")


@pytest.fixture
def files(tmp_path):
    """A temp index and templates dir holding one valid template."""
    index_path = tmp_path / "templates_index.tsv"
    templates_dir = tmp_path / "templates"
    write_template(make_template(), index_path, templates_dir)
    return index_path, templates_dir


def test_round_trip(files):
    """Write then load gives back the same TemplateFile."""
    index_path, templates_dir = files
    loaded = load_templates(index_path, templates_dir)
    assert len(loaded) == 1
    assert loaded[0] == make_template()


def test_grid_file_content(files):
    """The grid file holds the pattern name, ', '-joined forms, full width."""
    _, templates_dir = files
    text = (templates_dir / "test pr.tsv").read_text(encoding="utf-8")
    lines = text.splitlines()
    assert len(lines) == 4
    assert lines[0].split("\t")[0] == "test pr"
    # the multi-form cell is joined with ", "
    assert "asi, ase" in lines[2]
    # the empty cell is an empty string, rows are full width
    assert lines[2].split("\t") == [
        "pr 2nd",
        "asi, ase",
        "pr 2nd sg",
        "",
        "pr 2nd pl",
    ]


def test_index_file_content(files):
    """The index file has a header and one sorted row."""
    index_path, _ = files
    lines = index_path.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "pattern\tlike"
    assert lines[1] == "test pr\tkāraka"


def test_missing_table_file(files):
    """An index row without a table file raises."""
    index_path, templates_dir = files
    write_template(
        TemplateFile(
            pattern="ghost pr",
            like="x",
            data=[[[""], ["sg"]]],
        ),
        index_path,
        templates_dir,
    )
    (templates_dir / "ghost pr.tsv").unlink()
    with pytest.raises(ValueError, match="table file not found.*ghost pr"):
        load_templates(index_path, templates_dir)


def test_file_without_index_row(files):
    """A table file without an index row raises."""
    index_path, templates_dir = files
    write_grid_raw(
        [["orphan pr", "sg"], ["pr 3rd", "ati"]],
        templates_dir,
        "orphan pr",
    )
    with pytest.raises(ValueError, match="table file without index row.*orphan pr"):
        load_templates(index_path, templates_dir)


def test_wrong_top_left(files):
    """A grid whose top-left cell differs from its name raises."""
    index_path, templates_dir = files
    write_grid_raw(
        [["wrong pr", "sg"], ["pr 3rd", "ati"]],
        templates_dir,
        "test pr",
    )
    with pytest.raises(ValueError, match="top-left cell.*test pr"):
        load_templates(index_path, templates_dir)


def test_ragged_row(files):
    """A row narrower than the header raises."""
    index_path, templates_dir = files
    write_grid_raw(
        [["test pr", "sg", "", "pl"], ["pr 3rd", "ati"]],
        templates_dir,
        "test pr",
    )
    with pytest.raises(ValueError, match="row 1 has 2 cells, expected 4"):
        load_templates(index_path, templates_dir)


def test_empty_like(files):
    """An index row with an empty like raises."""
    index_path, templates_dir = files
    lines = index_path.read_text(encoding="utf-8").splitlines()
    lines[1] = "test pr\t"
    index_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="empty like.*test pr"):
        load_templates(index_path, templates_dir)


def test_duplicate_patterns(files):
    """Two index rows with the same pattern raise."""
    index_path, templates_dir = files
    lines = index_path.read_text(encoding="utf-8").splitlines()
    lines.append("test pr\tkāraka")
    index_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate pattern.*test pr"):
        load_templates(index_path, templates_dir)


def test_rename_updates_both_files(files):
    """Rename moves the grid file, updates the top-left cell and the index."""
    index_path, templates_dir = files
    old_data = make_template().data
    rename_template("test pr", "test new", index_path, templates_dir)
    assert not (templates_dir / "test pr.tsv").exists()
    loaded = load_templates(index_path, templates_dir)
    assert len(loaded) == 1
    assert loaded[0].pattern == "test new"
    assert loaded[0].data == old_data
    assert loaded[0].like == "kāraka"


def test_rename_to_existing_file_is_refused(files):
    """Rename never overwrites another template's file."""
    index_path, templates_dir = files
    other = make_template()
    other.pattern = "other pr"
    write_template(other, index_path, templates_dir)
    with pytest.raises(ValueError, match="already exists"):
        rename_template("test pr", "other pr", index_path, templates_dir)
    assert (templates_dir / "test pr.tsv").exists()


def test_hand_edited_forms_are_cleaned_and_sorted(files):
    """Unsorted forms, a bare comma and stray spaces load as clean sorted forms."""
    index_path, templates_dir = files
    write_grid_raw(
        [
            ["test pr", "sg", ""],
            ["pr 3rd", "asi,  ase ", "pr 3rd sg"],
            ["pr 2nd", "ā, āse, a", "pr 2nd sg"],
            ["pr 1st", " , ", "pr 1st sg"],
        ],
        templates_dir,
        "test pr",
    )
    data = load_templates(index_path, templates_dir)[0].data
    assert data[1][1] == ["asi", "ase"]  # Pāḷi order: i before e
    assert data[2][1] == ["a", "ā", "āse"]
    assert data[3][1] == [""]


def test_remove_updates_both_files(files):
    """Remove deletes the grid file and the index row."""
    index_path, templates_dir = files
    remove_template("test pr", index_path, templates_dir)
    assert not (templates_dir / "test pr.tsv").exists()
    assert load_templates(index_path, templates_dir) == []


def test_write_replaces_index_row(files):
    """Writing a template with the same name replaces its index row."""
    index_path, templates_dir = files
    t = make_template()
    t.like = "changed"
    write_template(t, index_path, templates_dir)
    loaded = load_templates(index_path, templates_dir)
    assert len(loaded) == 1
    assert loaded[0].like == "changed"


# real-data tests on the committed files


@pytest.fixture(scope="module")
def real_templates() -> list[TemplateFile]:
    pth = ProjectPaths()
    return load_templates(
        pth.inflection_templates_index_path, pth.inflection_templates_dir
    )


def test_real_files_load(real_templates):
    """The committed files load: 154 templates, all names unique."""
    assert len(real_templates) == 154
    names = [t.pattern for t in real_templates]
    assert len(set(names)) == 154
    assert all(t.like for t in real_templates)


def test_real_ant_adj_split(real_templates):
    """The ant adj loc fem sg cell holds the four split forms."""
    ant_adj = next(t for t in real_templates if t.pattern == "ant adj")
    fem_sg_col = ant_adj.data[0].index(["fem sg"])
    loc_row = next(r for r in ant_adj.data if r[0] == ["loc"])
    assert loc_row[fem_sg_col] == ["atiyaṃ", "atiyā", "antiyaṃ", "antiyā"]
