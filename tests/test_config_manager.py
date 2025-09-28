import json

from step_by_step.core.config_manager import ConfigManager, UserPreferences
from step_by_step.core.defaults import DEFAULT_SETTINGS


def test_load_preferences_creates_defaults(tmp_path):
    config_path = tmp_path / "settings.json"
    manager = ConfigManager(file_path=config_path)
    prefs = manager.load_preferences()

    assert config_path.exists()
    assert isinstance(prefs, UserPreferences)
    assert prefs.theme == DEFAULT_SETTINGS["theme"]


def test_load_preferences_repairs_invalid_json(tmp_path):
    config_path = tmp_path / "settings.json"
    config_path.write_text("{defekt", encoding="utf-8")
    manager = ConfigManager(file_path=config_path)

    prefs = manager.load_preferences()

    assert prefs.autosave_interval_minutes == DEFAULT_SETTINGS["autosave_interval_minutes"]
    stored = json.loads(config_path.read_text(encoding="utf-8"))
    assert stored["font_scale"] == DEFAULT_SETTINGS["font_scale"]


def test_save_preferences_persists_updates(tmp_path):
    config_path = tmp_path / "settings.json"
    manager = ConfigManager(file_path=config_path)
    prefs = manager.load_preferences()
    prefs.audio_volume = 0.42
    prefs.extra["custom"] = "value"

    manager.save_preferences(prefs)

    stored = json.loads(config_path.read_text(encoding="utf-8"))
    assert stored["audio_volume"] == 0.42
    assert stored["custom"] == "value"
