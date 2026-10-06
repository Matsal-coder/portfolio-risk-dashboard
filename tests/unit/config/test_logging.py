import json
import logging

from portfolio_risk.config.logging import JsonFormatter


def test_json_formatter_returns_structured_log() -> None:
    formatter = JsonFormatter()

    record = logging.LogRecord(
        name="portfolio_risk.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="test_message",
        args=(),
        exc_info=None,
    )

    payload = json.loads(formatter.format(record))

    assert payload["level"] == "INFO"
    assert payload["logger"] == "portfolio_risk.test"
    assert payload["message"] == "test_message"
    assert "timestamp" in payload
