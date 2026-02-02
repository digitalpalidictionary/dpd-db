from tools.speech_marks import SpeechMarkManager
from tools.speech_marks_replacement import replace_speech_marks
from tools.paths import ProjectPaths
import json


def test_replace_speech_marks(tmp_path):
    # Setup mock data
    paths = ProjectPaths(base_dir=tmp_path)
    paths.speech_marks_path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "sandhipada": ["sandhi'pada"],
        "hyphenpada": ["hyphen-pada"],
        "missakapada": ["missaka-pada", "missaka'pada"],
    }
    paths.speech_marks_path.write_text(json.dumps(data))

    manager = SpeechMarkManager(paths=paths)

    # Test 1: Replace sandhi
    text = "ayaṃ sandhipada."
    result = replace_speech_marks(text, manager)
    assert result == "ayaṃ sandhi'pada."

    # Test 2: Replace hyphen
    text = "ayaṃ hyphenpada."
    result = replace_speech_marks(text, manager)
    assert result == "ayaṃ hyphen-pada."

    # Test 3: Replace multiple variants
    text = "ayaṃ missakapada."
    result = replace_speech_marks(text, manager)
    # Order depends on list order in JSON, which is preserved
    assert result == "ayaṃ missaka-pada//missaka'pada."

    # Test 4: No replacement
    text = "ayaṃ padas."
    result = replace_speech_marks(text, manager)
    assert result == "ayaṃ padas."

    # Test 5: Punctuation handling
    text = "sandhipada, hyphenpada!"
    result = replace_speech_marks(text, manager)
    assert result == "sandhi'pada, hyphen-pada!"
