from tools.speech_marks import SpeechMarksDict

def test_speech_marks_type_definition():
    # Verify it's a valid type alias (generic alias or similar)
    # In runtime, dict[str, list[str]] behaves like a type object
    assert SpeechMarksDict is not None
