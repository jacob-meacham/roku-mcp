"""Tests for URL-to-ECP conversion, using test fixtures from roku-deeplink-spec."""

import json
from pathlib import Path

import pytest

from roku_mcp.deeplink import convert_url_to_ecp_command

FIXTURES_PATH = Path(__file__).parent / "deeplink_fixtures.json"


def _load_fixtures() -> dict[str, list[dict[str, object]]]:
    with FIXTURES_PATH.open() as f:
        return json.load(f)


class TestValidUrls:
    @pytest.fixture()
    def fixtures(self) -> dict[str, list[dict[str, object]]]:
        return _load_fixtures()

    def test_all_valid_urls(self, fixtures: dict[str, list[dict[str, object]]]) -> None:
        for case in fixtures["valid_urls"]:
            url = str(case["url"])
            expected = case["expected"]
            assert isinstance(expected, dict)
            result = convert_url_to_ecp_command(url)
            assert result is not None, f"Expected match for {url}"
            assert result.channel_id == expected["channel_id"], f"channel_id mismatch for {url}"
            assert result.channel_name == expected["channel_name"], f"channel_name mismatch for {url}"
            assert result.content_id == expected["content_id"], f"content_id mismatch for {url}"
            assert result.media_type == expected["media_type"], f"media_type mismatch for {url}"
            assert result.post_launch_key == expected["post_launch_key"], f"post_launch_key mismatch for {url}"


class TestInvalidUrls:
    @pytest.fixture()
    def fixtures(self) -> dict[str, list[dict[str, object]]]:
        return _load_fixtures()

    def test_all_invalid_urls(self, fixtures: dict[str, list[dict[str, object]]]) -> None:
        for case in fixtures["invalid_urls"]:
            url = str(case["url"])
            result = convert_url_to_ecp_command(url)
            assert result is None, f"Expected no match for {url}: {case.get('description')}"


class TestSpecificUrls:
    def test_netflix_watch(self) -> None:
        result = convert_url_to_ecp_command("https://www.netflix.com/watch/81444554")
        assert result is not None
        assert result.channel_id == "12"
        assert result.content_id == "81444554"
        assert result.media_type == "movie"
        assert result.post_launch_key == "Play"

    def test_netflix_title_is_series(self) -> None:
        result = convert_url_to_ecp_command("https://www.netflix.com/title/80179766")
        assert result is not None
        assert result.media_type == "series"

    def test_disney_plus(self) -> None:
        result = convert_url_to_ecp_command("https://www.disneyplus.com/play/f63db666-b097-4c61-99c1-b778de2d4ae1")
        assert result is not None
        assert result.channel_id == "291097"
        assert result.post_launch_key == "Select"

    def test_unsupported_url(self) -> None:
        result = convert_url_to_ecp_command("https://www.youtube.com/watch?v=abc123")
        assert result is None
