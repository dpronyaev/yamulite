# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Setup
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Run
python -m yamulite

# Install as CLI tool
pip install -e .
yamulite
```

No test framework or linter is configured.

## Architecture

YAMULITE is a single-window PyQt6 desktop client for Yandex Music (Russian streaming service). Python ≥3.10 required.

**Entry flow:** `__main__.py` loads token from storage → shows `LoginWindow` if missing → creates `MainWindow` on success.

**Core layers:**

- `auth.py` — OAuth device flow (`https://ya.ru/device`), token stored in keyring or `~/.yamulite/token.json`
- `api.py` — Thin sync wrapper over `yandex_music.Client`; exposes search, liked tracks, playlists, album/artist pages, like/unlike, and `stream_url(track)`
- `player.py` — VLC-based (`python-vlc`, `--no-video`) with queue management and Qt signals (`track_changed`, `state_changed`, `position_changed`); auto-advances on end, retries on stream failure
- `workers.py` — `Task(QRunnable)` with result/error signals; two pools: global (interactive API calls) and `cover_pool` (4-thread I/O for cover downloads); `_live_tasks` set prevents GC
- `covers.py` — Downloads covers from Yandex CDN, caches to `~/.yamulite/covers/` by SHA1 hash

**UI (`ui/`):**

- `main_window.py` — Creates `Api` and `Player`, owns `QStackedWidget` for pages and a persistent `_liked_ids` set shared across all track lists
- `search.py`, `library.py`, `detail.py` — Pages never destroyed (attached to stacked widget); detail pages are `AlbumPage`, `ArtistPage`, `PlaylistPage`
- `player_bar.py` — Transport controls wired to `Player`
- `widgets.py` — `TrackRow`, `TrackList` (QListWidget), `SimpleList`; reused across all pages

**Threading rule:** Qt main thread handles UI only; all API calls and cover downloads go through worker pools.
