"""Shared test fixtures."""

from pathlib import Path

import pytest

import roku_mcp.config


@pytest.fixture(autouse=True)
def _isolate_config(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:  # pyright: ignore[reportUnusedFunction]
    """Keep tests hermetic: never load a developer's local config.yml."""
    monkeypatch.setattr(roku_mcp.config, "CONFIG_FILE", tmp_path / "config.yml")


DEVICE_INFO_XML = """\
<device-info>
  <serial-number>YH00AA000000</serial-number>
  <device-id>S0A00000000</device-id>
  <vendor-name>Roku</vendor-name>
  <model-name>Roku Ultra</model-name>
  <model-number>4800X</model-number>
  <wifi-mac>AA:BB:CC:DD:EE:FF</wifi-mac>
  <ethernet-mac>11:22:33:44:55:66</ethernet-mac>
  <network-type>wifi</network-type>
  <user-device-name>Living Room</user-device-name>
  <software-version>11.5.0</software-version>
  <software-build>4210</software-build>
</device-info>
"""

APPS_XML = """\
<apps>
  <app id="12" type="appl" version="5.2.130079005">Netflix</app>
  <app id="13" type="appl" version="15.4.2025110415">Prime Video</app>
  <app id="291097" type="appl" version="1.57.2026010600">Disney+</app>
</apps>
"""

ACTIVE_APP_XML = """\
<active-app>
  <app id="12" type="appl">Netflix</app>
</active-app>
"""

MEDIA_PLAYER_XML = """\
<player state="play" live="false">
  <position>01:23:45</position>
  <duration>02:00:00</duration>
</player>
"""

MEDIA_PLAYER_CLOSE_XML = """\
<player state="close" />
"""
