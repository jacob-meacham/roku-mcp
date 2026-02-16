# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Project Overview

Roku MCP Server — a Python MCP server that enables LLMs to control Roku devices via the External Control Protocol (ECP). Exposes tools for device queries, remote control, channel launching, deep linking, and streaming URL playback. Supports multiple Roku devices via configuration and uses the Streamable HTTP transport.

## Development Commands

All commands run from the repo root using `uv`:

```bash
# Install dependencies
uv sync --dev

# Run the MCP server
uv run roku-mcp

# Run all tests
uv run pytest

# Lint and format
uv run ruff check .
uv run ruff format .

# Type checking (strict mode)
uv run pyright .
```

## Architecture

```
User (LLM Client) → MCP Streamable HTTP → FastMCP Server → ECP HTTP → Roku Device
```

**Source** (`src/roku_mcp/`):
- `server.py` — FastMCP instance, lifespan, all 11 MCP tools, entry point
- `config.py` — Pydantic Settings: multi-device config, YAML + env vars
- `ecp_client.py` — RokuECPClient: async HTTP wrapper for all ECP endpoints
- `models.py` — Frozen dataclasses: DeviceInfo, App, MediaPlayerStatus, etc.
- `deeplink.py` — URL-to-ECP conversion for streaming services
- `xml_parser.py` — Parse Roku XML responses into typed models

## Code Quality

- **Ruff**: Line length 120, target Python 3.13, rules: E, F, I, N, W, B, C4, UP, RUF
- **Pyright**: Strict mode, Python 3.13
- **pytest**: Strict markers/config, coverage on `roku_mcp` package

## Key Patterns

- **Configuration**: YAML config file (`config.yml`) with env var overrides via `__` nesting. Config path overridable via `ROKU_MCP_CONFIG` env var.
- **Multi-device**: Multiple Roku devices configured in YAML. Tools accept optional `device` param, defaulting to first device.
- **Async throughout**: All I/O is async/await. Tests use `pytest-asyncio`.
- **ECP base URL**: `http://{roku-ip}:8060` for all Roku commands.
