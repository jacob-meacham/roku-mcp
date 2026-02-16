"""Tests for configuration loading."""

import pytest

from roku_mcp.config import DeviceConfig, Settings


class TestSettings:
    def test_default_settings(self) -> None:
        settings = Settings(devices=[DeviceConfig(name="Test", ip="10.0.0.1")])
        assert settings.server.host == "0.0.0.0"
        assert settings.server.port == 8080
        assert len(settings.devices) == 1

    def test_get_device_default(self) -> None:
        settings = Settings(devices=[DeviceConfig(name="First", ip="10.0.0.1")])
        device = settings.get_device()
        assert device.name == "First"
        assert device.ip == "10.0.0.1"

    def test_get_device_by_name(self) -> None:
        settings = Settings(
            devices=[
                DeviceConfig(name="Living Room", ip="10.0.0.1"),
                DeviceConfig(name="Bedroom", ip="10.0.0.2"),
            ]
        )
        device = settings.get_device("Bedroom")
        assert device.ip == "10.0.0.2"

    def test_get_device_not_found(self) -> None:
        settings = Settings(devices=[DeviceConfig(name="Test", ip="10.0.0.1")])
        with pytest.raises(ValueError, match="Nonexistent"):
            settings.get_device("Nonexistent")
