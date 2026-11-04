import json
from unittest.mock import MagicMock, patch

import pytest
import requests

import setup_check


def _get(payload):
    response = MagicMock()
    response.json.return_value = payload
    return patch("setup_check.requests.get", return_value=response)


def _stream(*chunks):
    response = MagicMock()
    response.__enter__.return_value = response
    response.iter_lines.return_value = [json.dumps(c).encode() for c in chunks]
    return patch("setup_check.requests.post", return_value=response)


class TestChecks:
    def test_version_needs_0_40(self):
        assert setup_check.version_ok("0.40.13")
        assert setup_check.version_ok("1.2.0")
        assert not setup_check.version_ok("0.12.6")

    def test_ollama_down_means_no_version(self):
        with patch("setup_check.requests.get", side_effect=requests.ConnectionError):
            assert setup_check.ollama_version() is None

    def test_missing_models(self):
        with _get({"models": [{"name": "test-model-casual"}]}):
            assert "test-model-casual" not in setup_check.missing_models()
            assert "test-model-pro" in setup_check.missing_models()


class TestPull:
    def test_progress_adds_up_layers_and_ends_on_success(self):
        seen = []
        with patch("setup_check.free_space_gb", return_value=100), _stream(
            {"status": "pulling manifest"},
            {"status": "pulling a", "digest": "a", "total": 300, "completed": 100},
            {"status": "pulling b", "digest": "b", "total": 100, "completed": 100},
            {"status": "pulling a", "digest": "a", "total": 300, "completed": 300},
            {"status": "success"},
        ):
            setup_check.pull("m", lambda p: seen.append((p.done, p.total, p.status)))
        assert seen[-2][:2] == (400, 400)
        assert seen[-1][2] == "success"

    def test_error_from_ollama_is_raised(self):
        with patch("setup_check.free_space_gb", return_value=100), \
                _stream({"error": "pull model manifest: file does not exist"}):
            with pytest.raises(setup_check.PullError, match="does not exist"):
                setup_check.pull("m", lambda p: None)

    def test_not_enough_space_stops_before_downloading(self):
        with patch("setup_check.free_space_gb", return_value=1.0), \
                patch("setup_check.requests.post") as post:
            with pytest.raises(setup_check.PullError, match="disk space"):
                setup_check.pull("m", lambda p: None)
            post.assert_not_called()

    def test_stream_cut_short_asks_to_retry(self):
        with patch("setup_check.free_space_gb", return_value=100), \
                _stream({"status": "pulling a", "digest": "a", "total": 300, "completed": 10}):
            with pytest.raises(setup_check.PullError, match="Try again"):
                setup_check.pull("m", lambda p: None)
