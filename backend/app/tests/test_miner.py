import pytest
import pandas as pd
from app.TopicModeling.miner_v2 import Miner


def test_miner_performance():
    miner = Miner()
    test_data = pd.DataFrame(
        {
            "content": [
                "This is a test document in English.",
                "Ceci est un document test en français.",
                "Invalid £$% content",
                "http://example.com some text",
            ],
            "error": [None, None, None, None],
        }
    )

    result = miner.mine(test_data)

    assert not result.empty
    assert "language" in result.columns
    assert "stripped" in result.columns
    assert "lemmatized" in result.columns


def test_miner_preserves_columns():
    miner = Miner()
    test_data = pd.DataFrame(
        {
            "id": [1, 2, 3, 4],
            "title": ["Doc1", "Doc2", "Doc3", "Doc4"],
            "content": [
                "This is a test document in English.",
                "Ceci est un document test en français.",
                "Invalid £$% content",
                "http://example.com some text",
            ],
            "date": ["2024-01-01"] * 4,
            "error": [None, None, None, None],
        }
    )

    result = miner.mine(test_data)

    original_columns = ["id", "title", "content", "date", "error"]
    for col in original_columns:
        assert col in result.columns

    new_columns = ["language", "stripped", "lemmatized", "without_stop_words"]
    for col in new_columns:
        assert col in result.columns

    assert len(result) == len(test_data)
    assert (result["id"] == test_data["id"]).all()
    assert (result["title"] == test_data["title"]).all()
