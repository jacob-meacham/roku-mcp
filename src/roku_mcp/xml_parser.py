"""Parse Roku XML responses into typed models."""

from __future__ import annotations

from xml.etree.ElementTree import Element, fromstring

from roku_mcp.models import ActiveApp, App, DeviceInfo, MediaPlayerStatus


def _text(element: Element, tag: str) -> str:
    """Get text content of a child element, defaulting to empty string."""
    child = element.find(tag)
    if child is not None and child.text:
        return child.text
    return ""


def parse_device_info(xml: str) -> DeviceInfo:
    """Parse /query/device-info XML response."""
    root = fromstring(xml)
    return DeviceInfo(
        model_name=_text(root, "model-name"),
        model_number=_text(root, "model-number"),
        serial_number=_text(root, "serial-number"),
        software_version=_text(root, "software-version"),
        software_build=_text(root, "software-build"),
        device_name=_text(root, "user-device-name"),
        network_type=_text(root, "network-type"),
        wifi_mac=_text(root, "wifi-mac"),
        ethernet_mac=_text(root, "ethernet-mac"),
    )


def parse_apps(xml: str) -> list[App]:
    """Parse /query/apps XML response."""
    root = fromstring(xml)
    apps: list[App] = []
    for app_el in root.findall("app"):
        apps.append(
            App(
                id=app_el.get("id", ""),
                name=app_el.text or "",
                version=app_el.get("version", ""),
                app_type=app_el.get("type", ""),
            )
        )
    return apps


def parse_active_app(xml: str) -> ActiveApp:
    """Parse /query/active-app XML response."""
    root = fromstring(xml)
    app_el = root.find("app")
    if app_el is None:
        return ActiveApp(id="", name="")
    return ActiveApp(
        id=app_el.get("id", ""),
        name=app_el.text or "",
    )


def parse_media_player(xml: str) -> MediaPlayerStatus:
    """Parse /query/media-player XML response."""
    root = fromstring(xml)
    state = root.get("state", "close")
    is_live = root.get("live", "false") == "true"

    return MediaPlayerStatus(
        state=state,
        position=_text(root, "position"),
        duration=_text(root, "duration"),
        is_live=is_live,
    )
