"""Explicit-system detection is registry based and requires no trained model."""

from pathlib import Path

import pytest
import yaml

from ml.src import systems
from ml.src.systems import Registry, find_systems, load_registry, normalize_with_map


ML = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def registry():
    # The public registry cases should not depend on the caller's environment.
    return load_registry(ML / "configs/systems.yaml")


def _check_spans(text, result):
    mentions = [mention for system in result["systems"] for mention in system["mentions"]]
    for mention in [*mentions, *result["possible_mentions"], *result["generic_references"]]:
        assert 0 <= mention["start"] < mention["end"] <= len(text)
        assert text[mention["start"]:mention["end"]] == mention["text"]


@pytest.mark.parametrize(
    "text, status, ids, possible_ids, generic_texts",
    [
        pytest.param("تطبيق أبشر ما يفتح", "identified", ["absher"], [], [], id="context-cue"),
        pytest.param("ابشر يا أخوي", "ambiguous", [], ["absher"], [], id="ordinary-word"),
        pytest.param("توكلنا على الله", "unknown", [], [], [], id="excluded-phrase"),
        pytest.param("the Absher app", "identified", ["absher"], [], [], id="latin-alias"),
        pytest.param("«توكلنا»", "identified", ["tawakkalna"], [], [], id="quoted-name"),
        pytest.param("النفاذ الوطني الموحد", "identified", ["nafath"], [], [], id="longest-alias"),
        pytest.param("منصة ناجز ... النفاذ الوطني الموحد", "identified", ["najiz", "nafath"], [], [], id="appearance-order"),
        pytest.param("وبأبشر أفراد", "identified", ["absher"], [], [], id="attached-proclitics"),
        pytest.param("تطبيق أبـشـر ما يفتح", "identified", ["absher"], [], [], id="tatweel"),
        pytest.param("تَطْبِيق أَبْشَر ما يفتح", "identified", ["absher"], [], [], id="diacritics"),
        pytest.param("تطبيق إِبشر ما يفتح", "identified", ["absher"], [], [], id="alef-variant"),
        pytest.param("التطبيق بطيء", "unknown", [], [], ["التطبيق"], id="generic-reference"),
        pytest.param("تطبيق سهل للمواصلات", "unknown", [], [], [], id="unregistered-system"),
        pytest.param("", "unknown", [], [], [], id="empty"),
        pytest.param("ابشر يا أخوي، التطبيق بطيء في منصة ناجز", "identified", ["najiz"], ["absher"], ["التطبيق"], id="all-span-types"),
    ],
)
def test_system_cases(text, status, ids, possible_ids, generic_texts, registry):
    result = find_systems(text, registry=registry)
    assert result["status"] == status
    assert [system["system_id"] for system in result["systems"]] == ids
    assert [mention["system_id"] for mention in result["possible_mentions"]] == possible_ids
    assert [mention["text"] for mention in result["generic_references"]] == generic_texts
    _check_spans(text, result)


def test_ambiguous_name_is_confirmed_by_context(registry):
    mention = find_systems("تطبيق أبشر ما يفتح", registry=registry)["systems"][0]["mentions"][0]
    assert mention["text"] == "أبشر"
    assert mention["basis"].startswith("ambiguous_name+context_cue:")


def test_long_alias_is_registered_and_not_double_counted(registry):
    text = "النفاذ الوطني الموحد"
    result = find_systems(text, registry=registry)
    assert len(result["systems"]) == 1
    assert result["systems"][0]["system_id"] == "nafath"
    assert result["systems"][0]["mentions"] == [
        {"text": text, "start": 0, "end": len(text), "basis": "registered_alias"},
    ]
    assert result["possible_mentions"] == []
    _check_spans(text, result)


def test_none_is_rejected():
    with pytest.raises(TypeError, match="text must be str"):
        find_systems(None)


def test_normalization_preserves_original_character_map():
    text = "أَبـشَر ١۲"
    normalized, indexes = normalize_with_map(text)
    assert normalized == "ابشر 12"
    assert indexes == [0, 2, 4, 6, 7, 8, 9]
    assert len(normalized) == len(indexes)
    assert indexes == sorted(indexes)
    # One presentation-form character expands to two normalized characters.
    assert normalize_with_map("ﻻ") == ("لا", [0, 0])


@pytest.fixture
def custom_config():
    return {
        "version": "p1-test-registry",
        "context_cues": {"ar": ["تطبيق"], "en": ["app"]},
        "generic_references": {"ar": ["التطبيق"], "en": ["the app"]},
        "systems": [
            {"id": "sawt", "name_ar": "صوت", "name_en": "Sawt", "aliases": ["Sawt App"], "ambiguous": ["صوت"]},
        ],
    }


@pytest.mark.parametrize(
    "text, expected_status",
    [("Sawt App is slow", "identified"), ("تطبيق صوت بطيء", "identified"), ("صوت", "ambiguous")],
)
def test_registry_extensibility_without_retraining(custom_config, text, expected_status):
    result = find_systems(text, registry=Registry(custom_config))
    assert result["status"] == expected_status
    assert result["registry_version"] == "p1-test-registry"
    if expected_status == "identified":
        assert [system["system_id"] for system in result["systems"]] == ["sawt"]
    else:
        assert result["systems"] == []
        assert [mention["system_id"] for mention in result["possible_mentions"]] == ["sawt"]
    _check_spans(text, result)


def test_duplicate_system_id_raises(custom_config):
    custom_config["systems"].append({"id": "sawt", "aliases": ["Another App"]})
    with pytest.raises(ValueError, match="duplicate system id"):
        Registry(custom_config)


@pytest.mark.parametrize("alias", ["Sawt App", "SAWT APP", "صَوْت"])
def test_duplicate_normalized_alias_across_systems_raises(custom_config, alias):
    custom_config["systems"].append({"id": "another", "aliases": [alias]})
    with pytest.raises(ValueError, match="used by both"):
        Registry(custom_config)


def test_load_registry_explicit_path_and_environment(custom_config, tmp_path, monkeypatch):
    path = tmp_path / "custom-systems.yaml"
    path.write_text(yaml.safe_dump(custom_config, allow_unicode=True), encoding="utf-8")
    explicit = load_registry(path)
    assert explicit.source == str(path)
    assert explicit.version == "p1-test-registry"
    assert list(explicit.systems) == ["sawt"]

    monkeypatch.setenv("ML_SYSTEMS_REGISTRY", str(path))
    monkeypatch.setattr(systems, "_registry", None)
    from_environment = load_registry()
    assert from_environment.source == str(path)
    assert from_environment.version == explicit.version
    text = "تطبيق صوت بطيء"
    result = find_systems(text)
    assert result["status"] == "identified"
    assert [system["system_id"] for system in result["systems"]] == ["sawt"]
    _check_spans(text, result)
    # An explicit path overrides the environment-selected default.
    assert "absher" in load_registry(ML / "configs/systems.yaml").systems
