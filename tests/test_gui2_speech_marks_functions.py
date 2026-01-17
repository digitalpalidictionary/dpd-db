import json
import pytest
from gui2.dpd_fields_functions import clean_speech_marks, clean_commentary, clean_example
from tools.speech_marks import SpeechMarkManager
from tools.paths import ProjectPaths

def test_gui2_functions_with_speech_marks(tmp_path):
    # Setup mock data
    paths = ProjectPaths(base_dir=tmp_path)
    paths.speech_marks_path.parent.mkdir(parents=True, exist_ok=True)
    
    data = {
        "sandhipada": ["sandhi'pada"],
        "hyphenpada": ["hyphen-pada"]
    }
    paths.speech_marks_path.write_text(json.dumps(data))
    
    manager = SpeechMarkManager(paths=paths)
    
    # Test clean_speech_marks
    assert clean_speech_marks("sandhipada", manager) == "sandhi'pada"
    assert clean_speech_marks("hyphenpada", manager) == "hyphen-pada"
    
    # Test clean_commentary (includes speech marks + general cleaning)
    # clean_text replaces ṁ with ṃ
    assert clean_commentary("sandhipada ṁ", manager) == "sandhi'pada ṃ"
    
    # Test clean_example
    assert clean_example("hyphenpada ṁ", manager) == "hyphen-pada ṃ"
