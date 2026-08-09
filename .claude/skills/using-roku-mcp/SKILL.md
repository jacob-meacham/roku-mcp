---
name: using-roku-mcp
description: Use when controlling a Roku TV through the roku-mcp MCP server — playing streaming content, pressing remote keys, launching channels, typing into on-screen keyboards, or when playback stalls on a profile picker or a URL isn't recognized.
---

# Using roku-mcp

Drives Roku devices over ECP. Every tool takes an optional `device` (a name from `list_devices`, exact match); omitted = first configured device.

## Picking the right tool

| Goal | Tool |
|---|---|
| Play a Netflix / Disney+ / HBO Max / Prime Video / Hulu / Apple TV+ / YouTube URL | `play_url` — that list is exhaustive |
| Open any other app (Spotify, Twitch, …) | `list_apps` → `launch_app(channel_id)` — never guess channel IDs; only installed channels are launchable |
| Find content when you have no URL | `search_roku(keyword)` — opens Roku's cross-channel search UI |
| Enter text (search box, login) | `type_text` — only works while a text field has focus; follow with `Enter` or navigate to the on-screen submit button |

## Non-obvious behaviors

- **`play_url` already presses the post-launch key for you**: `Play` on Netflix (starts immediately), `Select` on the other services (dismisses the profile picker). YouTube needs no key at all — its deep link auto-plays. Don't send a key again blindly — a second press can pause playback or change profile.
- **Verify, then intervene**: after any launch, call `get_media_player_status`. `state: "play"` with advancing position = success. `state: "close"` or stuck = the app is on a UI screen; only then navigate with `send_keypress`.
- **There is no Pause key** — `Play` is the play/pause toggle.
- **Netflix URLs**: `/watch/<id>` = movie (plays directly), `/title/<id>` = series (may land on the episode list; press `Select` to play the highlighted episode).
- **Series deep links resume per watch history** — landing on a detail page instead of playback is normal; it is not an error.
- **Volume/power keys only work on Roku TVs**, not sticks driving an external TV (`get_device_info` shows the model). Meaningful volume change ≈ 5+ presses via `send_keypresses`.

## Valid key names

`Home` `Up` `Down` `Left` `Right` `Select` `Back` `Play` `Rev` `Fwd` `InstantReplay` `Info` `Backspace` `Search` `Enter` `VolumeUp` `VolumeDown` `VolumeMute` `PowerOff` `InputTuner` `InputHDMI1`–`InputHDMI4` `InputAV1` — anything else is rejected.

## Common mistakes

| Mistake | Instead |
|---|---|
| `play_url` with an unsupported URL (Spotify, Twitch, …) | `list_apps` → `launch_app`, or `search_roku` |
| Hardcoding channel IDs from memory | Read them from `list_apps` (IDs vary; only installed apps launch) |
| Pressing `Select`/`Play` right after `play_url` | Check `get_media_player_status` first — the server already sent the post-launch key |
| `type_text` with no field focused | Open the keyboard first (e.g. via `search_roku`), then type |
| Assuming a stalled series launch failed | Detail page is expected; `Select` plays the highlighted episode |
