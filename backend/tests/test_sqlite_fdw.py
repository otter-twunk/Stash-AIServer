import logging

from stash_ai_server.db.sqlite_fdw import setup_sqlite_fdw


class _UnexpectedConnectionEngine:
    def begin(self):
        raise AssertionError("sqlite_fdw should not open a database connection when disabled")


def test_setup_sqlite_fdw_skips_when_disabled(monkeypatch, caplog):
    monkeypatch.setenv("AI_ENABLE_SQLITE_FDW", "0")

    with caplog.at_level(logging.INFO, logger="stash_ai_server.db.sqlite_fdw"):
        setup_sqlite_fdw(_UnexpectedConnectionEngine())

    assert "sqlite_fdw setup skipped (AI_ENABLE_SQLITE_FDW disabled)" in caplog.text
