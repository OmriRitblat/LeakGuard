
"""Tests for POC dataset loading utilities."""

from dataset_loader import EVAL_DIR, TRAIN_DIR, load_json


def test_load_train_dataset():
    data = load_json(TRAIN_DIR / "ss001_train.json")

    assert isinstance(data, dict)
    assert "secret" in data
    assert data["secret"]["code"] == "SS-001"


def test_load_eval_dataset():
    data = load_json(EVAL_DIR / "ss001_eval.json")

    assert isinstance(data, dict)
    assert "cases" in data
    assert len(data["cases"]) > 0


def test_train_data_fixture(train_data):
    expected_files = {
        "ss001_train",
        "ss002_train",
        "ss003_train",
    }

    assert expected_files.issubset(train_data.keys())

    for dataset in train_data.values():
        assert "secret" in dataset
        assert isinstance(dataset["secret"], dict)


def test_eval_data_fixture(eval_data):
    expected_files = {
        "ss001_eval",
        "ss002_eval",
        "ss003_eval",
        "multi_secret_eval",
        "pii_eval",
    }

    assert expected_files.issubset(eval_data.keys())

    for dataset in eval_data.values():
        assert "cases" in dataset
        assert isinstance(dataset["cases"], list)
        assert len(dataset["cases"]) > 0
