"""Tests for XML parsing."""

from roku_mcp.xml_parser import parse_active_app, parse_apps, parse_device_info, parse_media_player

from .conftest import ACTIVE_APP_XML, APPS_XML, DEVICE_INFO_XML, MEDIA_PLAYER_CLOSE_XML, MEDIA_PLAYER_XML


class TestParseDeviceInfo:
    def test_parses_all_fields(self) -> None:
        info = parse_device_info(DEVICE_INFO_XML)
        assert info.model_name == "Roku Ultra"
        assert info.model_number == "4800X"
        assert info.serial_number == "YH00AA000000"
        assert info.software_version == "11.5.0"
        assert info.software_build == "4210"
        assert info.device_name == "Living Room"
        assert info.network_type == "wifi"
        assert info.wifi_mac == "AA:BB:CC:DD:EE:FF"
        assert info.ethernet_mac == "11:22:33:44:55:66"


class TestParseApps:
    def test_parses_multiple_apps(self) -> None:
        apps = parse_apps(APPS_XML)
        assert len(apps) == 3
        assert apps[0].id == "12"
        assert apps[0].name == "Netflix"
        assert apps[0].version == "5.2.130079005"
        assert apps[0].app_type == "appl"

    def test_parses_all_app_ids(self) -> None:
        apps = parse_apps(APPS_XML)
        ids = [a.id for a in apps]
        assert ids == ["12", "13", "291097"]


class TestParseActiveApp:
    def test_parses_active_app(self) -> None:
        app = parse_active_app(ACTIVE_APP_XML)
        assert app.id == "12"
        assert app.name == "Netflix"

    def test_parses_empty_active_app(self) -> None:
        app = parse_active_app("<active-app></active-app>")
        assert app.id == ""
        assert app.name == ""


class TestParseMediaPlayer:
    def test_parses_playing_state(self) -> None:
        status = parse_media_player(MEDIA_PLAYER_XML)
        assert status.state == "play"
        assert status.position == "01:23:45"
        assert status.duration == "02:00:00"
        assert status.is_live is False

    def test_parses_close_state(self) -> None:
        status = parse_media_player(MEDIA_PLAYER_CLOSE_XML)
        assert status.state == "close"
        assert status.is_live is False
