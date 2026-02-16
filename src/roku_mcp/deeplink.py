"""Roku ECP URL-to-Playback conversion per roku-deeplink-spec.

Converts streaming service URLs into Roku ECP playback commands.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class ExtractionResult:
    """Result of extracting channel info from a streaming URL."""

    channel_id: str
    channel_name: str
    content_id: str
    media_type: Literal["movie", "series"]
    post_launch_key: Literal["Play", "Select"]


@dataclass(frozen=True)
class Channel:
    """A streaming service channel configuration."""

    channel_id: str
    channel_name: str
    url_pattern: re.Pattern[str]
    post_launch_key: Literal["Play", "Select"]
    media_type_from_url: bool = False


NETFLIX = Channel(
    channel_id="12",
    channel_name="Netflix",
    url_pattern=re.compile(r"netflix\.com/(?:watch|title)/(\d+)"),
    post_launch_key="Play",
    media_type_from_url=True,
)

DISNEY_PLUS = Channel(
    channel_id="291097",
    channel_name="Disney+",
    url_pattern=re.compile(r"disneyplus\.com/(?:(?:play|video)/)([a-f0-9-]+)"),
    post_launch_key="Select",
)

HBO_MAX = Channel(
    channel_id="61322",
    channel_name="HBO Max",
    url_pattern=re.compile(r"(?:max\.com|hbomax\.com)/(?:(?:movies|series)/[^/]+/|(?:video/watch|play)/)([^/?]+)"),
    post_launch_key="Select",
)

PRIME_VIDEO = Channel(
    channel_id="13",
    channel_name="Prime Video",
    url_pattern=re.compile(r"(?:amazon\.com|primevideo\.com)/(?:.*?/)?(?:dp|detail)/([B][A-Z0-9]{9})"),
    post_launch_key="Select",
)

CHANNEL_CATALOG: tuple[Channel, ...] = (NETFLIX, DISNEY_PLUS, HBO_MAX, PRIME_VIDEO)


def _determine_media_type(url: str, channel: Channel) -> Literal["movie", "series"]:
    """Determine media type from URL for Netflix, else return 'movie'."""
    if channel.media_type_from_url and "/title/" in url:
        return "series"
    return "movie"


def convert_url_to_ecp_command(url: str) -> ExtractionResult | None:
    """Convert a streaming URL to an ECP extraction result.

    Returns ExtractionResult with channel info, or None if URL doesn't match.
    """
    for channel in CHANNEL_CATALOG:
        match = channel.url_pattern.search(url)
        if match:
            content_id = match.group(1)
            media_type = _determine_media_type(url, channel)
            return ExtractionResult(
                channel_id=channel.channel_id,
                channel_name=channel.channel_name,
                content_id=content_id,
                media_type=media_type,
                post_launch_key=channel.post_launch_key,
            )
    return None
