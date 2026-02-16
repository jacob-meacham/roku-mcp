"""Integration tests for MCP server tools."""

from __future__ import annotations

from unittest.mock import MagicMock

import httpx
import pytest
from mcp.server.fastmcp import Context
from mcp.shared.context import RequestContext

from roku_mcp.config import DeviceConfig, Settings
from roku_mcp.server import (
    AppContext,
    RokuContext,
    get_active_app,
    get_device_info,
    get_media_player_status,
    launch_app,
    list_apps,
    list_devices,
    play_url,
    search_roku,
    send_keypress,
    send_keypresses,
    type_text,
)

from .conftest import ACTIVE_APP_XML, APPS_XML, DEVICE_INFO_XML, MEDIA_PLAYER_XML


def _make_mock_transport() -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if request.method == "GET":
            if path == "/query/device-info":
                return httpx.Response(200, text=DEVICE_INFO_XML)
            if path == "/query/apps":
                return httpx.Response(200, text=APPS_XML)
            if path == "/query/active-app":
                return httpx.Response(200, text=ACTIVE_APP_XML)
            if path == "/query/media-player":
                return httpx.Response(200, text=MEDIA_PLAYER_XML)
        if request.method == "POST":
            if path.startswith(("/keypress/", "/launch/", "/search/")):
                return httpx.Response(200)
        return httpx.Response(404)

    return httpx.MockTransport(handler)


def _make_ctx() -> RokuContext:
    """Create a mock MCP Context with our AppContext as lifespan context."""
    settings = Settings(devices=[DeviceConfig(name="Test Roku", ip="192.168.1.100")])
    http_client = httpx.AsyncClient(transport=_make_mock_transport())
    app_ctx = AppContext(settings=settings, http_client=http_client)

    mock_request_context = MagicMock(spec=RequestContext)
    mock_request_context.lifespan_context = app_ctx
    mock_request_context.meta = None

    return Context(request_context=mock_request_context, fastmcp=None)


@pytest.fixture()
def ctx() -> RokuContext:
    return _make_ctx()


@pytest.mark.asyncio
class TestListDevices:
    async def test_returns_devices(self, ctx: RokuContext) -> None:
        result = await list_devices(ctx)
        assert len(result) == 1
        assert result[0]["name"] == "Test Roku"


@pytest.mark.asyncio
class TestGetDeviceInfo:
    async def test_returns_info(self, ctx: RokuContext) -> None:
        result = await get_device_info(ctx)
        assert result["model_name"] == "Roku Ultra"


@pytest.mark.asyncio
class TestListApps:
    async def test_returns_apps(self, ctx: RokuContext) -> None:
        result = await list_apps(ctx)
        assert len(result) == 3
        assert result[0]["name"] == "Netflix"


@pytest.mark.asyncio
class TestGetActiveApp:
    async def test_returns_active_app(self, ctx: RokuContext) -> None:
        result = await get_active_app(ctx)
        assert result["id"] == "12"
        assert result["name"] == "Netflix"


@pytest.mark.asyncio
class TestGetMediaPlayerStatus:
    async def test_returns_status(self, ctx: RokuContext) -> None:
        result = await get_media_player_status(ctx)
        assert result["state"] == "play"
        assert result["position"] == "01:23:45"


@pytest.mark.asyncio
class TestSendKeypress:
    async def test_sends_key(self, ctx: RokuContext) -> None:
        result = await send_keypress(ctx, "Home")
        assert "Home" in result


@pytest.mark.asyncio
class TestSendKeypresses:
    async def test_sends_keys(self, ctx: RokuContext) -> None:
        result = await send_keypresses(ctx, ["Up", "Down", "Select"], delay_ms=0)
        assert "3 keypresses" in result


@pytest.mark.asyncio
class TestTypeText:
    async def test_types_text(self, ctx: RokuContext) -> None:
        result = await type_text(ctx, "hi")
        assert "hi" in result


@pytest.mark.asyncio
class TestLaunchApp:
    async def test_launches_channel(self, ctx: RokuContext) -> None:
        result = await launch_app(ctx, "12")
        assert "12" in result


@pytest.mark.asyncio
class TestPlayUrl:
    async def test_plays_netflix_url(self, ctx: RokuContext) -> None:
        result = await play_url(ctx, "https://www.netflix.com/watch/81444554")
        assert "Netflix" in result

    async def test_unsupported_url(self, ctx: RokuContext) -> None:
        result = await play_url(ctx, "https://www.youtube.com/watch?v=abc")
        assert "Could not detect" in result


@pytest.mark.asyncio
class TestSearchRoku:
    async def test_searches(self, ctx: RokuContext) -> None:
        result = await search_roku(ctx, "breaking bad")
        assert "breaking bad" in result
