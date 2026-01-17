import json
import pytest
from tools.speech_marks import SpeechMarkManager
from tools.paths import ProjectPaths

def test_speech_mark_manager_init(tmp_path):
    # Mock paths to use tmp_path
    paths = ProjectPaths(base_dir=tmp_path)
    
    # 1. Test initialization with no files
    manager = SpeechMarkManager(paths=paths)
    assert manager.get_speech_marks() == {}
    
    # 2. Test initialization with old hyphenations.json
    old_hyphenations = {"testword": "test-word"}
    paths.hyphenations_dict_path.parent.mkdir(parents=True, exist_ok=True)
    paths.hyphenations_dict_path.write_text(json.dumps(old_hyphenations))
    
    manager = SpeechMarkManager(paths=paths)
    assert manager.get_variants("testword") == ["test-word"]
    
    # 3. Test initialization with unified speech_marks.json (takes precedence)
    unified_data = {"testword": ["test'word"]}
    paths.speech_marks_path.write_text(json.dumps(unified_data))
    
    manager = SpeechMarkManager(paths=paths)
    # Should only have unified data, or if merging, should have both.
    # Spec says: "Load from tools/speech_marks_path if exists... Load old hyphenations if tools/hyphenations.json exists"
    # Merging seems more robust for the migration.
    variants = manager.get_variants("testword")
    assert "test'word" in variants
    assert "test-word" in variants

def test_speech_mark_manager_update_and_save(tmp_path):
    paths = ProjectPaths(base_dir=tmp_path)
    paths.speech_marks_path.parent.mkdir(parents=True, exist_ok=True)
    manager = SpeechMarkManager(paths=paths)
    
    # Test update
    manager.update_variants("clean", "cl'ean")
    assert manager.get_variants("clean") == ["cl'ean"]
    
    manager.update_variants("clean", "cle-an")
    assert "cl'ean" in manager.get_variants("clean")
    assert "cle-an" in manager.get_variants("clean")
    
    # Test duplicate update
    manager.update_variants("clean", "cl'ean")
    assert len(manager.get_variants("clean")) == 2
    
    # Test save
    manager.save()
    assert paths.speech_marks_path.exists()
    
    with open(paths.speech_marks_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        assert data["clean"] == ["cl'ean", "cle-an"]

def test_speech_mark_manager_regeneration(tmp_path):
    # This test will mock the DB part or just test the logic if we separate it.
    # For now, let's test _should_regenerate logic.
    paths = ProjectPaths(base_dir=tmp_path)
    paths.speech_marks_path.parent.mkdir(parents=True, exist_ok=True)
    manager = SpeechMarkManager(paths=paths)
    
    # No file exists
    assert manager._should_regenerate() is True
    
    # File exists and is new
    paths.speech_marks_path.write_text("{}")
    assert manager._should_regenerate() is False
    
    # File exists and is old (mocking time is hard without freezegun, 
    # but we can manually set mtime)
    import os
    import time
    old_time = time.time() - (25 * 3600) # 25 hours ago
    os.utime(paths.speech_marks_path, (old_time, old_time))
    assert manager._should_regenerate() is True

def test_speech_mark_manager_loads_merged_data():
    # Real test with the actual generated file
    manager = SpeechMarkManager() 
    # Check a known hyphenation (pick one from source or just check count > 0)
    assert len(manager.get_speech_marks()) > 0
    
    # Check if we can find a likely candidate (optional, but good for sanity)
    # Just checking the dictionary is populated is enough for this phase step.
