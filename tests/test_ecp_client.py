"""Tests for the ECP client."""

import httpx
import pytest

from roku_mcp.deeplink import ExtractionResult
from roku_mcp.ecp_client import ECPError, RokuECPClient

from .conftest import ACTIVE_APP_XML, APPS_XML, DEVICE_INFO_XML, MEDIA_PLAYER_XML


async def _noop_sleep(_seconds: float) -> None:
    """No-op sleep for tests."""


@pytest.fixture()
def mock_transport() -> httpx.MockTransport:
    """Transport that returns canned XML responses."""

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


@pytest.fixture()
def ecp_client(mock_transport: httpx.MockTransport) -> RokuECPClient:
    client = httpx.AsyncClient(transport=mock_transport)
    return RokuECPClient("192.168.1.100", client, sleep=_noop_sleep)


@pytest.mark.asyncio
class TestGetDeviceInfo:
    async def test_returns_device_info(self, ecp_client: RokuECPClient) -> None:
        info = await ecp_client.get_device_info()
        assert info.model_name == "Roku Ultra"
        assert info.device_name == "Living Room"


@pytest.mark.asyncio
class TestGetApps:
    async def test_returns_apps(self, ecp_client: RokuECPClient) -> None:
        apps = await ecp_client.get_apps()
        assert len(apps) == 3
        assert apps[0].name == "Netflix"


@pytest.mark.asyncio
class TestGetActiveApp:
    async def test_returns_active_app(self, ecp_client: RokuECPClient) -> None:
        app = await ecp_client.get_active_app()
        assert app.id == "12"
        assert app.name == "Netflix"


@pytest.mark.asyncio
class TestGetMediaPlayer:
    async def test_returns_status(self, ecp_client: RokuECPClient) -> None:
        status = await ecp_client.get_media_player()
        assert status.state == "play"
        assert status.position == "01:23:45"


@pytest.mark.asyncio
class TestKeypress:
    async def test_valid_key(self, ecp_client: RokuECPClient) -> None:
        await ecp_client.keypress("Home")

    async def test_invalid_key_raises(self, ecp_client: RokuECPClient) -> None:
        with pytest.raises(ECPError, match="Invalid key"):
            await ecp_client.keypress("InvalidKey")


@pytest.mark.asyncio
class TestTypeText:
    async def test_types_characters(self, ecp_client: RokuECPClient) -> None:
        await ecp_client.type_text("hi")


@pytest.mark.asyncio
class TestLaunch:
    async def test_launch_channel(self, ecp_client: RokuECPClient) -> None:
        await ecp_client.launch("12")

    async def test_launch_with_deep_link(self, ecp_client: RokuECPClient) -> None:
        await ecp_client.launch("12", content_id="81444554", media_type="movie")


@pytest.mark.asyncio
class TestLaunchWithDeeplink:
    """The live playback path builds a Function 2 action sequence and executes it."""

    async def test_executes_launch_wait_keypress(self) -> None:
        requests: list[httpx.Request] = []
        sleeps: list[float] = []

        def handler(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            return httpx.Response(200)

        async def _recording_sleep(seconds: float) -> None:
            sleeps.append(seconds)

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        ecp_client = RokuECPClient("192.168.1.100", client, sleep=_recording_sleep)

        extraction = ExtractionResult(
            channel_id="12",
            channel_name="Netflix",
            content_id="81444554",
            media_type="movie",
            post_launch_key="Play",
        )
        await ecp_client.launch_with_deeplink(extraction)

        # launch (with deep-link params) → wait 2000ms → keypress, in order.
        assert [(r.method, r.url.path) for r in requests] == [
            ("POST", "/launch/12"),
            ("POST", "/keypress/Play"),
        ]
        launch = requests[0]
        assert launch.url.params["contentId"] == "81444554"
        assert launch.url.params["mediaType"] == "movie"
        assert sleeps == [2.0]


@pytest.mark.asyncio
class TestSearch:
    async def test_search(self, ecp_client: RokuECPClient) -> None:
        await ecp_client.search("breaking bad")
