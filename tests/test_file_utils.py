import json
import logging

from step_by_step.core.file_utils import atomic_write_json


def test_atomic_write_json_creates_file(tmp_path):
    target = tmp_path / "settings.json"
    payload = {"hello": "world"}
    assert atomic_write_json(target, payload)
    saved = json.loads(target.read_text(encoding="utf-8"))
    assert saved == payload


def test_atomic_write_json_handles_serialisation_error(tmp_path, caplog):
    target = tmp_path / "broken.json"

    class Unserialisable:
        pass

    logger = logging.getLogger("test.atomic_write")
    with caplog.at_level(logging.ERROR):
        result = atomic_write_json(target, {"value": Unserialisable()}, logger=logger)
    assert result is False
    assert not target.exists()
    assert any("JSON konnte nicht serialisiert" in message for message in caplog.text.splitlines())
