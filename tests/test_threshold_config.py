import json
from pathlib import Path

import pytest
from fixtures import sample_transactions
from main import parse_args
from service import DEFAULT_REPEAT_THRESHOLD, flag_repeat_transactions, repeat_threshold_from_config

DATA = json.loads((Path(__file__).resolve().parent.parent / "data" / "records.json").read_text())


def test_threshold_read_from_config():
    assert repeat_threshold_from_config({"repeat_alert_threshold": 5}) == 5


@pytest.mark.parametrize("config", [None, {}, {"repeat_alert_threshold": 0}, {"repeat_alert_threshold": -3},
                                    {"repeat_alert_threshold": "3"}, {"repeat_alert_threshold": True}, []])
def test_missing_or_invalid_config_falls_back_to_default(config):
    assert repeat_threshold_from_config(config) == DEFAULT_REPEAT_THRESHOLD


def test_dataset_threshold_matches_default_result():
    threshold = repeat_threshold_from_config(DATA)
    assert threshold == 2
    assert flag_repeat_transactions(DATA["transactions"], threshold) == flag_repeat_transactions(DATA["transactions"])


def test_raising_threshold_reduces_alerts():
    # dataset groups have 3 rows each
    assert len(flag_repeat_transactions(DATA["transactions"], 2)) == 48
    assert flag_repeat_transactions(DATA["transactions"], 3) == []


def test_cli_threshold_default_and_override():
    assert parse_args([]).threshold == DEFAULT_REPEAT_THRESHOLD
    assert parse_args(["--threshold", "1"]).threshold == 1


def test_cli_threshold_one_flags_sample_pair():
    # fixtures have one matching pair
    assert flag_repeat_transactions(sample_transactions(), parse_args([]).threshold) == []
    alerts = flag_repeat_transactions(sample_transactions(), parse_args(["--threshold", "1"]).threshold)
    assert [a["transaction_ids"] for a in alerts] == [["TX-1", "TX-2"]]


@pytest.mark.parametrize("value", ["0", "-1", "abc"])
def test_cli_rejects_invalid_threshold(value):
    with pytest.raises(SystemExit):
        parse_args(["--threshold", value])
