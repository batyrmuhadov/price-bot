import pytest
from unittest.mock import Mock, patch

from fetcher import fetch_with_retry, create_session


class TestCreateSession:
    def test_session_has_headers(self):
        session = create_session()
        assert "User-Agent" in session.headers
        assert "Chrome/120" in session.headers["User-Agent"]


class TestFetchWithRetry:
    def test_successful_request(self):
        session = Mock()
        resp = Mock()
        resp.status_code = 200
        session.get.return_value = resp
        result = fetch_with_retry(session, "https://example.com", max_retries=3)
        assert result is resp
        session.get.assert_called_once_with("https://example.com", timeout=20)

    def test_retry_on_failure(self):
        session = Mock()
        fail_resp = Mock()
        fail_resp.status_code = 503
        success_resp = Mock()
        success_resp.status_code = 200
        session.get.side_effect = [fail_resp, success_resp]
        result = fetch_with_retry(session, "https://example.com", max_retries=3)
        assert result is success_resp
        assert session.get.call_count == 2

    def test_all_retries_fail(self):
        session = Mock()
        resp = Mock()
        resp.status_code = 503
        session.get.return_value = resp
        result = fetch_with_retry(session, "https://example.com", max_retries=3)
        assert result is None
        assert session.get.call_count == 3
