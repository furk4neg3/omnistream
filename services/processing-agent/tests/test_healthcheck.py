import json
from datetime import datetime, timedelta, timezone

import pytest

from app.healthcheck import check_metrics_snapshot


NOW = datetime(2026, 6, 6, 12, 0, 0, tzinfo=timezone.utc)


def iso_seconds_ago(seconds: int) -> str:
    return (NOW - timedelta(seconds=seconds)).isoformat().replace("+00:00", "Z")


def write_metrics(path, payload):
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_healthcheck_accepts_fresh_running_snapshot(tmp_path):
    metrics_file = tmp_path / "processing-agent-metrics.json"
    write_metrics(
        metrics_file,
        {
            "service": "processing-agent",
            "status": "running",
            "updated_at": iso_seconds_ago(5),
        },
    )

    healthy, message = check_metrics_snapshot(str(metrics_file), 30, now=NOW)

    assert healthy is True
    assert "healthy" in message


def test_healthcheck_reports_missing_metrics_file(tmp_path):
    healthy, message = check_metrics_snapshot(
        str(tmp_path / "missing-metrics.json"),
        30,
        now=NOW,
    )

    assert healthy is False
    assert "not found" in message


def test_healthcheck_reports_invalid_json(tmp_path):
    metrics_file = tmp_path / "processing-agent-metrics.json"
    metrics_file.write_text("{not-valid-json", encoding="utf-8")

    healthy, message = check_metrics_snapshot(str(metrics_file), 30, now=NOW)

    assert healthy is False
    assert "invalid JSON" in message


def test_healthcheck_reports_non_object_json(tmp_path):
    metrics_file = tmp_path / "processing-agent-metrics.json"
    metrics_file.write_text(json.dumps(["not", "an", "object"]), encoding="utf-8")

    healthy, message = check_metrics_snapshot(str(metrics_file), 30, now=NOW)

    assert healthy is False
    assert "JSON object" in message


@pytest.mark.parametrize("status", ["stopping", "stopped", "error"])
def test_healthcheck_reports_non_running_status(tmp_path, status):
    metrics_file = tmp_path / "processing-agent-metrics.json"
    write_metrics(
        metrics_file,
        {
            "service": "processing-agent",
            "status": status,
            "updated_at": iso_seconds_ago(1),
        },
    )

    healthy, message = check_metrics_snapshot(str(metrics_file), 30, now=NOW)

    assert healthy is False
    assert "not running" in message
    assert status in message


def test_healthcheck_reports_missing_updated_at(tmp_path):
    metrics_file = tmp_path / "processing-agent-metrics.json"
    write_metrics(
        metrics_file,
        {
            "service": "processing-agent",
            "status": "running",
        },
    )

    healthy, message = check_metrics_snapshot(str(metrics_file), 30, now=NOW)

    assert healthy is False
    assert "updated_at" in message


def test_healthcheck_reports_invalid_updated_at(tmp_path):
    metrics_file = tmp_path / "processing-agent-metrics.json"
    write_metrics(
        metrics_file,
        {
            "service": "processing-agent",
            "status": "running",
            "updated_at": "not-a-timestamp",
        },
    )

    healthy, message = check_metrics_snapshot(str(metrics_file), 30, now=NOW)

    assert healthy is False
    assert "updated_at" in message


def test_healthcheck_reports_stale_running_snapshot(tmp_path):
    metrics_file = tmp_path / "processing-agent-metrics.json"
    write_metrics(
        metrics_file,
        {
            "service": "processing-agent",
            "status": "running",
            "updated_at": iso_seconds_ago(120),
        },
    )

    healthy, message = check_metrics_snapshot(str(metrics_file), 30, now=NOW)

    assert healthy is False
    assert "stale" in message
    assert "exceeding 30 seconds" in message
