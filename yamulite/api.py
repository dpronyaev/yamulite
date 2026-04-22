"""Thin wrapper over yandex_music.Client. All methods are synchronous and
meant to be called from background workers, not the UI thread."""
from __future__ import annotations

from typing import List, Optional

from yandex_music import Album, Artist, Client, Playlist, Track


class Api:
    def __init__(self, token: str):
        self.client = Client(token).init()

    # --- search -----------------------------------------------------------
    def search(self, text: str, type_: str = "all", page: int = 0):
        """type_: 'track' | 'artist' | 'album' | 'playlist' | 'all'."""
        return self.client.search(text, type_=type_, page=page)

    # --- library ----------------------------------------------------------
    def liked_tracks(self) -> List[Track]:
        likes = self.client.users_likes_tracks()
        if not likes:
            return []
        ids = [t.track_id for t in likes.tracks]
        if not ids:
            return []
        return self.client.tracks(ids)

    def user_playlists(self) -> List[Playlist]:
        return self.client.users_playlists_list() or []

    def playlist_tracks(self, playlist: Playlist) -> List[Track]:
        full = self.client.users_playlists(playlist.kind, playlist.owner.uid)
        if not full:
            return []
        if isinstance(full, list):
            full = full[0]
        short = full.tracks or []
        ids = [t.track_id or (t.track.id if t.track else None) for t in short]
        ids = [i for i in ids if i]
        if not ids:
            return []
        return self.client.tracks(ids)

    def album_tracks(self, album_id: int) -> List[Track]:
        album = self.client.albums_with_tracks(album_id)
        if not album or not album.volumes:
            return []
        out: List[Track] = []
        for volume in album.volumes:
            out.extend(volume)
        return out

    def artist_tracks_page(self, artist_id: int, page: int = 0, page_size: int = 50):
        """Returns (tracks, has_more)."""
        res = self.client.artists_tracks(artist_id, page=page, page_size=page_size)
        if not res:
            return [], False
        tracks = list(res.tracks or [])
        pager = res.pager
        has_more = False
        if pager is not None:
            shown = (page + 1) * page_size
            has_more = shown < (pager.total or 0)
        return tracks, has_more

    def artist_albums(self, artist_id: int) -> List[Album]:
        res = self.client.artists_direct_albums(artist_id)
        return res or []

    # --- actions ----------------------------------------------------------
    def like(self, track_id) -> None:
        self.client.users_likes_tracks_add(track_id)

    def unlike(self, track_id) -> None:
        self.client.users_likes_tracks_remove(track_id)

    def is_liked(self, track_id) -> bool:
        likes = self.client.users_likes_tracks()
        if not likes:
            return False
        tid = str(track_id)
        return any(str(t.track_id) == tid or str(t.id) == tid for t in likes.tracks)

    def stream_url(self, track: Track) -> Optional[str]:
        infos = track.get_download_info(get_direct_links=True)
        if not infos:
            return None
        # pick best mp3 bitrate
        mp3 = [i for i in infos if i.codec == "mp3"]
        chosen = max(mp3 or infos, key=lambda i: i.bitrate_in_kbps or 0)
        return chosen.direct_link

    # --- user -------------------------------------------------------------
    def account_name(self) -> str:
        status = self.client.me
        if status and status.account:
            return status.account.display_name or status.account.login or "you"
        return "you"
