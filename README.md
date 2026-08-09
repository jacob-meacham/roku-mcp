# roku-mcp

An MCP server that lets LLM clients control Roku devices over the [External Control Protocol (ECP)](https://developer.roku.com/docs/developer-program/dev-tools/external-control-api.md) — query device state, press remote keys, launch channels, and deep-link straight into streaming content from a plain URL.

```
LLM client ──MCP (Streamable HTTP)──▶ roku-mcp ──ECP (HTTP :8060)──▶ Roku device(s)
```

## Quick start

### Docker

```bash
docker run -d --name roku-mcp -p 9191:8080 \
  -e DEVICES='[{"name":"Living Room Roku","ip":"192.168.1.252"}]' \
  jemonjam/roku-mcp:latest
```

The container is stateless and env-configured; it must be on a network that can reach your Roku's port 8060 (i.e. the same LAN).

### From source

```bash
uv sync
cp config.yml.example config.yml   # or create config.yml, see Configuration
uv run roku-mcp
```

### Connect a client

The MCP endpoint is `http://<host>:<port>/mcp` (Streamable HTTP). For Claude Code:

```bash
claude mcp add --transport http roku http://localhost:9191/mcp
```

Or in any client's MCP config:

```json
{
  "mcpServers": {
    "roku": { "type": "http", "url": "http://localhost:9191/mcp" }
  }
}
```

## Configuration

YAML file (`config.yml`, path overridable via `ROKU_MCP_CONFIG`) with env-var overrides (`__` nesting). Every key is optional; defaults shown:

```yaml
server:
  host: 0.0.0.0
  port: 8080
devices:
  - name: Roku
    ip: 192.168.1.100
```

| Env var | Meaning |
|---|---|
| `DEVICES` | JSON list of devices: `[{"name":"...","ip":"..."}]` — handy for containers |
| `SERVER__HOST` / `SERVER__PORT` | Listen address / port |
| `ROKU_MCP_CONFIG` | Path to the YAML config file |

Multiple devices are supported; every tool takes an optional `device` (name) argument and defaults to the first configured device.

Don't know your Roku's IP? On the device: Settings → Network → About. Or SSDP-discover it: Rokus answer an M-SEARCH for `roku:ecp` on the LAN.

## Tools

**Query (read-only)**

| Tool | Returns |
|---|---|
| `list_devices` | Configured devices (name + IP) |
| `get_device_info` | Model, software version, MACs, network type |
| `list_apps` | Installed channels with their channel IDs |
| `get_active_app` | Currently foregrounded app |
| `get_media_player_status` | Playback state, position, duration |

**Control**

| Tool | Does |
|---|---|
| `send_keypress` | One remote key press |
| `send_keypresses` | A key sequence with a configurable delay |
| `type_text` | Types a string into a focused text field |
| `launch_app` | Launch a channel by ID, optionally with deep-link params |
| `play_url` | Paste a streaming URL, get playback (see below) |
| `search_roku` | Open Roku's search UI pre-filled with a keyword |

Valid key names: `Home`, `Up`, `Down`, `Left`, `Right`, `Select`, `Back`, `Play`, `Rev`, `Fwd`, `InstantReplay`, `Info`, `Backspace`, `Search`, `Enter`, `VolumeUp`, `VolumeDown`, `VolumeMute`, `PowerOff`, `InputTuner`, `InputHDMI1`–`InputHDMI4`, `InputAV1`.

## Deep linking with `play_url`

`play_url` converts a share/browser URL into a Roku deep-link launch, then presses the right key to get past the channel's landing screen:

| Service | Example URL | After launch |
|---|---|---|
| Netflix | `netflix.com/watch/81444554`, `/title/…`, locale prefixes OK | Plays automatically |
| Disney+ | `disneyplus.com/play/<uuid>` | `Select` pressed for the profile picker — verify with `get_media_player_status` |
| HBO Max | `play.max.com/video/watch/<uuid>` | same |
| Prime Video | `amazon.com/gp/video/detail/<id>` | same |
| Hulu | `hulu.com/watch/<id>` | same |
| Apple TV+ | `tv.apple.com/movie|show/…` | same |
| YouTube | `youtube.com/watch?v=…`, `youtu.be/…` | Auto-plays — launch-only, no key pressed |

Netflix `/watch/` URLs are treated as movies and `/title/` as series. Unsupported services (Spotify, Twitch, …) return a "could not detect" message — fall back to `launch_app` with an ID from `list_apps`, or `search_roku`.

The URL-to-ECP behavior is generated from the [roku-deeplink spec](https://github.com/jacob-meacham/roku-deeplink-spec) via speclib — fix behavior there, then `speclib sync`, rather than editing `deeplink.py`.

## Agent skill

The repo ships a Claude skill at [`.claude/skills/using-roku-mcp/`](.claude/skills/using-roku-mcp/SKILL.md) that teaches an agent the non-obvious parts of driving these tools (post-launch profile pickers, keyboard focus, pause semantics, off-catalog apps). It activates automatically for agents working in this repo; to use it elsewhere, copy the directory into your own skills folder (e.g. `~/.claude/skills/`).

## Security

The server is **unauthenticated**, as is Roku ECP itself — anything that can reach it can control your TV. Keep it on a trusted LAN/VPN; don't expose it to the internet.

## Development

```bash
uv sync --dev
uv run pytest          # tests
uv run ruff check .    # lint
uv run pyright .       # strict type checking
```

CI publishes `jemonjam/roku-mcp:latest` (and a `:sha` tag) to Docker Hub on every push to `main`.
