"""Roku ECP URL-to-Playback conversion.

Generated from the ``roku-deeplink`` spec-library, version **1.2.0**, via speclib.
The canonical behavior lives in that library's ``SPEC.md`` / ``PROMPT.md`` /
``test_fixtures.json``; regenerate with ``speclib sync`` rather than editing the
behavior here by hand.

This consumer supports the four public-streaming channels the spec addresses by
URL (Netflix, Disney+, HBO Max, Prime Video). The spec's Emby channel (``44191``)
is descriptor-only / self-hosted and is intentionally *not* implemented here.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from typing import Literal

MediaType = Literal["movie", "series"]
PostLaunchKey = Literal["Play", "Select"]


@dataclass(frozen=True)
class ExtractionResult:
    """A content descriptor extracted from a streaming URL (output of Function 1)."""

    channel_id: str
    channel_name: str
    content_id: str
    media_type: MediaType
    post_launch_key: PostLaunchKey


@dataclass(frozen=True)
class Channel:
    """A streaming service channel configuration."""

    channel_id: str
    channel_name: str
    url_pattern: re.Pattern[str]
    post_launch_key: PostLaunchKey
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
    url_pattern=re.compile(r"disneyplus\.com/(?:(?:play|video)/|browse/entity-)([a-f0-9-]+)"),
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
    url_pattern=re.compile(r"(?:amazon\.com|primevideo\.com)/.*?/([B][A-Z0-9]{9})"),
    post_launch_key="Select",
)

CHANNEL_CATALOG: tuple[Channel, ...] = (NETFLIX, DISNEY_PLUS, HBO_MAX, PRIME_VIDEO)


def _determine_media_type(url: str, channel: Channel) -> MediaType:
    """Netflix distinguishes movie vs series by URL path; all others are movies."""
    if channel.media_type_from_url and "/title/" in url:
        return "series"
    return "movie"


def convert_url_to_ecp_command(url: str) -> ExtractionResult | None:
    """Convert a streaming URL to an extraction result (Function 1).

    Uses regex ``search`` semantics (pattern may appear anywhere in the URL).
    Returns an :class:`ExtractionResult`, or ``None`` if the URL matches no
    supported URL channel.
    """
    for channel in CHANNEL_CATALOG:
        match = channel.url_pattern.search(url)
        if match:
            return ExtractionResult(
                channel_id=channel.channel_id,
                channel_name=channel.channel_name,
                content_id=match.group(1),
                media_type=_determine_media_type(url, channel),
                post_launch_key=channel.post_launch_key,
            )
    return None


@dataclass(frozen=True)
class LaunchAction:
    """Launch a channel with deep-link params — always the first action."""

    channel_id: str
    params: str
    type: Literal["launch"] = "launch"


@dataclass(frozen=True)
class WaitAction:
    """Delay before the next action, in milliseconds."""

    milliseconds: int
    type: Literal["wait"] = "wait"


@dataclass(frozen=True)
class KeypressAction:
    """Press a remote key ``count`` times (``count`` >= 1)."""

    key: str
    count: int
    type: Literal["keypress"] = "keypress"


Action = LaunchAction | WaitAction | KeypressAction


@dataclass(frozen=True)
class PlaybackCommand:
    """An action sequence to execute against a Roku device (output of Function 2)."""

    actions: tuple[Action, ...]
    type: Literal["action_sequence"] = "action_sequence"

    def to_dict(self) -> dict[str, object]:
        """Render to the spec's JSON shape (``actions`` as a list of action dicts)."""
        return {"type": self.type, "actions": [asdict(action) for action in self.actions]}


def _launch_params(descriptor: Mapping[str, object]) -> str:
    """Build channel-launch params. The URL channels all use ``contentId``/``mediaType``."""
    content_id = descriptor["content_id"]
    media_type = descriptor.get("media_type", "movie")
    return f"contentId={content_id}&mediaType={media_type}"


def build_playback_command(descriptor: ExtractionResult | Mapping[str, object]) -> PlaybackCommand:
    """Build a Roku ECP playback command from a content descriptor (Function 2).

    Accepts an :class:`ExtractionResult` or an equivalent mapping. Produces a
    ``launch`` action, then — when the descriptor carries a ``post_launch_key`` —
    a ``wait`` (2000ms) and a ``keypress``. A descriptor with no
    ``post_launch_key`` yields a launch-only command.
    """
    data: Mapping[str, object] = asdict(descriptor) if isinstance(descriptor, ExtractionResult) else descriptor
    actions: list[Action] = [
        LaunchAction(channel_id=str(data["channel_id"]), params=_launch_params(data)),
    ]
    post_launch_key = data.get("post_launch_key")
    if post_launch_key:
        actions.append(WaitAction(milliseconds=2000))
        actions.append(KeypressAction(key=str(post_launch_key), count=1))
    return PlaybackCommand(actions=tuple(actions))
