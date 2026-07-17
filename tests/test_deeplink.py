"""Tests for URL-to-ECP conversion and playback-command building.

Validated against the canonical ``test_fixtures.json`` shipped by the
``roku-deeplink`` spec-library (v1.2.0). Emby playback fixtures (channel
``44191``) are skipped: roku-mcp is public-streaming only and does not
implement Emby.
"""

import json
from pathlib import Path
from typing import Any

import pytest

from roku_mcp.deeplink import build_playback_command, convert_url_to_ecp_command

FIXTURES_PATH = Path(__file__).parent / "deeplink_fixtures.json"

# Emby: descriptor-only channel the spec includes but this consumer does not implement.
EMBY_CHANNEL_ID = "44191"


def _load_fixtures() -> dict[str, list[dict[str, Any]]]:
    with FIXTURES_PATH.open() as f:
        return json.load(f)


FIXTURES = _load_fixtures()


class TestValidUrls:
    @pytest.mark.parametrize("case", FIXTURES["valid_urls"])
    def test_valid_url(self, case: dict[str, Any]) -> None:
        url = str(case["url"])
        expected = case["expected"]
        result = convert_url_to_ecp_command(url)
        assert result is not None, f"Expected match for {url}"
        assert result.channel_id == expected["channel_id"], f"channel_id mismatch for {url}"
        assert result.channel_name == expected["channel_name"], f"channel_name mismatch for {url}"
        assert result.content_id == expected["content_id"], f"content_id mismatch for {url}"
        assert result.media_type == expected["media_type"], f"media_type mismatch for {url}"
        assert result.post_launch_key == expected["post_launch_key"], f"post_launch_key mismatch for {url}"


class TestInvalidUrls:
    @pytest.mark.parametrize("case", FIXTURES["invalid_urls"])
    def test_invalid_url(self, case: dict[str, Any]) -> None:
        url = str(case["url"])
        result = convert_url_to_ecp_command(url)
        assert result is None, f"Expected no match for {url}: {case.get('description')}"


class TestPlaybackCommands:
    @pytest.mark.parametrize("case", FIXTURES["playback_commands"])
    def test_playback_command(self, case: dict[str, Any]) -> None:
        descriptor = case["input"]
        if descriptor["channel_id"] == EMBY_CHANNEL_ID:
            pytest.skip("Emby (channel 44191) is not implemented by roku-mcp")
        command = build_playback_command(descriptor)
        assert command.to_dict() == case["expected"]


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

    def test_disney_browse_entity_reconciled(self) -> None:
        # Canonical spec regex captures /browse/entity-{id}; the pre-reconciliation
        # (drifted) Disney+ regex lacked this branch and would return None here.
        result = convert_url_to_ecp_command("https://www.disneyplus.com/browse/entity-abc123def")
        assert result is not None
        assert result.channel_id == "291097"
        assert result.content_id == "abc123def"
        assert result.media_type == "movie"

    def test_prime_broad_path_reconciled(self) -> None:
        # Canonical spec regex is broad (`.*?/` before the ASIN); the pre-reconciliation
        # (drifted) narrow regex required a `dp/` or `detail/` segment and would
        # return None for this `/gp/video/` path.
        result = convert_url_to_ecp_command("https://www.amazon.com/gp/video/B0DKTFF815")
        assert result is not None
        assert result.channel_id == "13"
        assert result.content_id == "B0DKTFF815"

    def test_unsupported_url(self) -> None:
        result = convert_url_to_ecp_command("https://www.youtube.com/watch?v=abc123")
        assert result is None


class TestBuildPlaybackCommand:
    def test_accepts_extraction_result(self) -> None:
        extraction = convert_url_to_ecp_command("https://www.netflix.com/watch/81444554")
        assert extraction is not None
        command = build_playback_command(extraction)
        assert command.type == "action_sequence"
        assert command.actions[0].type == "launch"
        assert command.actions[0].params == "contentId=81444554&mediaType=movie"
        assert command.actions[-1].type == "keypress"
        assert command.actions[-1].key == "Play"
