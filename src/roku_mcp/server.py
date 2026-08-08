"""Roku MCP Server — exposes Roku ECP control as MCP tools."""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from dataclasses import asdict, dataclass
from typing import Any

import httpx
from mcp.server.fastmcp import Context, FastMCP

from roku_mcp.config import Settings
from roku_mcp.deeplink import convert_url_to_ecp_command
from roku_mcp.ecp_client import RokuECPClient, RokuKey


@dataclass
class AppContext:
    """Application context holding shared resources."""

    settings: Settings
    http_client: httpx.AsyncClient


RokuContext = Context[Any, AppContext, Any]


def _make_lifespan(
    settings: Settings,
) -> Callable[[FastMCP[AppContext]], AbstractAsyncContextManager[AppContext]]:
    """Create a lifespan context manager that captures settings."""

    @asynccontextmanager
    async def app_lifespan(server: FastMCP[AppContext]) -> AsyncIterator[AppContext]:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
            yield AppContext(settings=settings, http_client=client)

    return app_lifespan


def _get_app_ctx(ctx: RokuContext) -> AppContext:
    """Extract AppContext from the MCP Context."""
    return ctx.request_context.lifespan_context


def _get_client(app_ctx: AppContext, device: str | None) -> RokuECPClient:
    """Resolve a device and return an ECP client for it."""
    device_config = app_ctx.settings.get_device(device)
    return RokuECPClient(device_config.ip, app_ctx.http_client)


def create_server(settings: Settings | None = None) -> FastMCP[AppContext]:
    """Create and configure the FastMCP server."""
    if settings is None:
        settings = Settings()
    return FastMCP(
        "roku-mcp",
        lifespan=_make_lifespan(settings),
        host=settings.server.host,
        port=settings.server.port,
    )


mcp = create_server()


@mcp.tool()
async def list_devices(ctx: RokuContext) -> list[dict[str, str]]:
    """List all configured Roku devices."""
    app_ctx = _get_app_ctx(ctx)
    return [{"name": d.name, "ip": d.ip} for d in app_ctx.settings.devices]


@mcp.tool()
async def get_device_info(
    ctx: RokuContext,
    device: str | None = None,
) -> dict[str, str]:
    """Get device model, software version, and network info.

    Args:
        device: Device name (optional, defaults to first configured device)
    """
    app_ctx = _get_app_ctx(ctx)
    client = _get_client(app_ctx, device)
    info = await client.get_device_info()
    return asdict(info)


@mcp.tool()
async def list_apps(
    ctx: RokuContext,
    device: str | None = None,
) -> list[dict[str, str]]:
    """List all installed channels with their IDs.

    Args:
        device: Device name (optional, defaults to first configured device)
    """
    app_ctx = _get_app_ctx(ctx)
    client = _get_client(app_ctx, device)
    apps = await client.get_apps()
    return [asdict(a) for a in apps]


@mcp.tool()
async def get_active_app(
    ctx: RokuContext,
    device: str | None = None,
) -> dict[str, str]:
    """Get the currently running app.

    Args:
        device: Device name (optional, defaults to first configured device)
    """
    app_ctx = _get_app_ctx(ctx)
    client = _get_client(app_ctx, device)
    app = await client.get_active_app()
    return asdict(app)


@mcp.tool()
async def get_media_player_status(
    ctx: RokuContext,
    device: str | None = None,
) -> dict[str, str | bool]:
    """Get current playback state, position, and duration.

    Args:
        device: Device name (optional, defaults to first configured device)
    """
    app_ctx = _get_app_ctx(ctx)
    client = _get_client(app_ctx, device)
    status = await client.get_media_player()
    return asdict(status)


@mcp.tool()
async def send_keypress(
    ctx: RokuContext,
    key: RokuKey,
    device: str | None = None,
) -> str:
    """Send a single remote control key press.

    Args:
        key: Remote key name
        device: Device name (optional, defaults to first configured device)
    """
    app_ctx = _get_app_ctx(ctx)
    client = _get_client(app_ctx, device)
    await client.keypress(key)
    return f"Sent keypress: {key}"


@mcp.tool()
async def send_keypresses(
    ctx: RokuContext,
    keys: list[RokuKey],
    delay_ms: int = 100,
    device: str | None = None,
) -> str:
    """Send a sequence of remote control key presses with delay between each.

    Args:
        keys: List of remote key names to send in order
        delay_ms: Delay between keypresses in milliseconds (default 100)
        device: Device name (optional, defaults to first configured device)
    """
    app_ctx = _get_app_ctx(ctx)
    client = _get_client(app_ctx, device)
    await client.keypress_sequence(list(keys), delay_ms)
    return f"Sent {len(keys)} keypresses: {', '.join(keys)}"


@mcp.tool()
async def type_text(
    ctx: RokuContext,
    text: str,
    device: str | None = None,
) -> str:
    """Type text into an input field using Lit_ key events.

    Args:
        text: Text string to type
        device: Device name (optional, defaults to first configured device)
    """
    app_ctx = _get_app_ctx(ctx)
    client = _get_client(app_ctx, device)
    await client.type_text(text)
    return f"Typed text: {text}"


@mcp.tool()
async def launch_app(
    ctx: RokuContext,
    channel_id: str,
    content_id: str | None = None,
    media_type: str | None = None,
    device: str | None = None,
) -> str:
    """Launch a channel by ID, optionally with deep link parameters.

    Args:
        channel_id: Roku channel ID (e.g. "12" for Netflix, "13" for Prime Video)
        content_id: Content ID for deep linking (optional)
        media_type: Media type for deep linking — movie, series, episode (optional)
        device: Device name (optional, defaults to first configured device)
    """
    app_ctx = _get_app_ctx(ctx)
    client = _get_client(app_ctx, device)
    await client.launch(channel_id, content_id, media_type)
    return f"Launched channel {channel_id}"


@mcp.tool()
async def play_url(
    ctx: RokuContext,
    url: str,
    device: str | None = None,
) -> str:
    """Auto-detect a streaming URL and deep link to play it on Roku.

    Supports Netflix, Disney+, HBO Max, Prime Video, Hulu, and Apple TV+ URLs.

    Args:
        url: Streaming service URL (e.g. https://www.netflix.com/watch/81444554)
        device: Device name (optional, defaults to first configured device)
    """
    extraction = convert_url_to_ecp_command(url)
    if extraction is None:
        return f"Could not detect streaming service from URL: {url}"
    app_ctx = _get_app_ctx(ctx)
    client = _get_client(app_ctx, device)
    await client.launch_with_deeplink(extraction)
    return f"Playing on {extraction.channel_name}: content {extraction.content_id} ({extraction.media_type})"


@mcp.tool()
async def search_roku(
    ctx: RokuContext,
    keyword: str,
    device: str | None = None,
) -> str:
    """Open Roku search with a keyword.

    Args:
        keyword: Search keyword
        device: Device name (optional, defaults to first configured device)
    """
    app_ctx = _get_app_ctx(ctx)
    client = _get_client(app_ctx, device)
    await client.search(keyword)
    return f"Searching Roku for: {keyword}"


def main() -> None:
    """Entry point for the roku-mcp server."""
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
