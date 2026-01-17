from tools.paths import ProjectPaths

def test_speech_marks_path():
    paths = ProjectPaths()
    assert hasattr(paths, "speech_marks_path")
    assert paths.speech_marks_path.name == "speech_marks.json"
    assert "tools" in str(paths.speech_marks_path.parent)
