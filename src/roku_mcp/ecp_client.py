"""Async HTTP client for the Roku External Control Protocol (ECP)."""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Coroutine
from typing import Any, Literal, get_args
from urllib.parse import parse_qsl, quote

import httpx

from roku_mcp.deeplink import (
    ExtractionResult,
    LaunchAction,
    PlaybackCommand,
    WaitAction,
    build_playback_command,
)
from roku_mcp.models import ActiveApp, App, DeviceInfo, MediaPlayerStatus
from roku_mcp.xml_parser import parse_active_app, parse_apps, parse_device_info, parse_media_player

RokuKey = Literal[
    "Home",
    "Rev",
    "Fwd",
    "Play",
    "Select",
    "Left",
    "Right",
    "Down",
    "Up",
    "Back",
    "InstantReplay",
    "Info",
    "Backspace",
    "Search",
    "Enter",
    "VolumeDown",
    "VolumeMute",
    "VolumeUp",
    "PowerOff",
    "InputTuner",
    "InputHDMI1",
    "InputHDMI2",
    "InputHDMI3",
    "InputHDMI4",
    "InputAV1",
]

VALID_KEYS: frozenset[str] = frozenset(get_args(RokuKey))

SleepFn = Callable[[float], Coroutine[Any, Any, None]]


class ECPError(Exception):
    """Error communicating with a Roku device via ECP."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class RokuECPClient:
    """Async client for a single Roku device's ECP interface."""

    def __init__(
        self,
        ip: str,
        client: httpx.AsyncClient,
        sleep: SleepFn = asyncio.sleep,
    ) -> None:
        self._base_url = f"http://{ip}:8060"
        self._client = client
        self._sleep = sleep

    async def _get(self, path: str) -> str:
        """Send GET request and return response text."""
        try:
            response = await self._client.get(f"{self._base_url}{path}")
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise ECPError(f"ECP request failed: {path}", status_code=e.response.status_code) from e
        except httpx.HTTPError as e:
            raise ECPError(f"ECP connection error: {path}") from e
        return response.text

    async def _post(self, path: str, params: dict[str, str] | None = None) -> None:
        """Send POST request."""
        try:
            response = await self._client.post(f"{self._base_url}{path}", params=params)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise ECPError(f"ECP request failed: {path}", status_code=e.response.status_code) from e
        except httpx.HTTPError as e:
            raise ECPError(f"ECP connection error: {path}") from e

    async def get_device_info(self) -> DeviceInfo:
        """Query device info."""
        xml = await self._get("/query/device-info")
        return parse_device_info(xml)

    async def get_apps(self) -> list[App]:
        """Query installed apps."""
        xml = await self._get("/query/apps")
        return parse_apps(xml)

    async def get_active_app(self) -> ActiveApp:
        """Query the currently active app."""
        xml = await self._get("/query/active-app")
        return parse_active_app(xml)

    async def get_media_player(self) -> MediaPlayerStatus:
        """Query media player status."""
        xml = await self._get("/query/media-player")
        return parse_media_player(xml)

    async def keypress(self, key: str) -> None:
        """Send a single keypress."""
        if key not in VALID_KEYS:
            msg = f"Invalid key: {key}. Valid keys: {', '.join(sorted(VALID_KEYS))}"
            raise ECPError(msg)
        await self._post(f"/keypress/{key}")

    async def keypress_sequence(self, keys: list[str], delay_ms: int = 100) -> None:
        """Send a sequence of keypresses with delay between each."""
        for key in keys:
            await self.keypress(key)
            if delay_ms > 0:
                await self._sleep(delay_ms / 1000.0)

    async def type_text(self, text: str) -> None:
        """Type text using Lit_ key events."""
        for char in text:
            encoded = quote(char)
            await self._post(f"/keypress/Lit_{encoded}")
            await self._sleep(0.05)

    async def launch(
        self,
        channel_id: str,
        content_id: str | None = None,
        media_type: str | None = None,
    ) -> None:
        """Launch a channel, optionally with deep link parameters."""
        params: dict[str, str] = {}
        if content_id:
            params["contentId"] = content_id
        if media_type:
            params["mediaType"] = media_type
        await self._post(f"/launch/{channel_id}", params=params or None)

    async def execute_playback_command(self, command: PlaybackCommand) -> None:
        """Execute a playback command's action sequence against the device.

        Iterates the ``launch`` / ``wait`` / ``keypress`` actions produced by
        the spec's ``build_playback_command`` (Function 2) and dispatches each
        through the ECP primitives.
        """
        for action in command.actions:
            if isinstance(action, LaunchAction):
                params = dict(parse_qsl(action.params))
                await self._post(f"/launch/{action.channel_id}", params=params or None)
            elif isinstance(action, WaitAction):
                await self._sleep(action.milliseconds / 1000.0)
            else:  # KeypressAction
                for _ in range(action.count):
                    await self.keypress(action.key)

    async def launch_with_deeplink(self, extraction: ExtractionResult) -> None:
        """Execute a full deep link playback: build the action sequence (Function 2), then run it."""
        await self.execute_playback_command(build_playback_command(extraction))

    async def search(self, keyword: str) -> None:
        """Open Roku search with a keyword."""
        await self._post("/search/browse", params={"keyword": keyword})
