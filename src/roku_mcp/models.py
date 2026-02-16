"""Frozen dataclasses for Roku ECP response data."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DeviceInfo:
    """Roku device information from /query/device-info."""

    model_name: str
    model_number: str
    serial_number: str
    software_version: str
    software_build: str
    device_name: str
    network_type: str
    wifi_mac: str
    ethernet_mac: str


@dataclass(frozen=True)
class App:
    """An installed Roku channel from /query/apps."""

    id: str
    name: str
    version: str
    app_type: str


@dataclass(frozen=True)
class ActiveApp:
    """The currently running app from /query/active-app."""

    id: str
    name: str


@dataclass(frozen=True)
class MediaPlayerStatus:
    """Playback status from /query/media-player."""

    state: str
    position: str
    duration: str
    is_live: bool
