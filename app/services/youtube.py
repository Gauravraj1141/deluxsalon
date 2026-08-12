import yt_dlp


class PlaylistFetchError(Exception):
    """Raised when a YouTube/YouTube Music playlist URL cannot be resolved to a track list."""


def fetch_playlist_songs(url: str) -> list[dict]:
    """Resolve a YouTube or YouTube Music playlist URL into song dicts.

    Uses yt-dlp's flat-playlist extraction, which reads the playlist's own listing
    data (title/duration/channel per entry) without downloading or fully resolving
    each video, so it stays fast even for large playlists.
    """
    ydl_opts = {
        "extract_flat": "in_playlist",
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except yt_dlp.utils.DownloadError as exc:
        raise PlaylistFetchError(str(exc)) from exc

    if not info:
        raise PlaylistFetchError("Could not read playlist data from that URL.")

    entries = info.get("entries")
    if entries is None:
        raise PlaylistFetchError("That URL doesn't look like a playlist.")

    songs = []
    for index, entry in enumerate(entries, start=1):
        if not entry:
            continue
        video_id = entry.get("id")
        title = entry.get("title")
        if not video_id or not title:
            continue
        duration = entry.get("duration")
        songs.append(
            {
                "title": title,
                "artist": entry.get("channel") or entry.get("uploader") or "Unknown",
                "video_id": video_id,
                "duration": int(duration) if duration else 0,
                "sort_order": index,
            }
        )

    if not songs:
        raise PlaylistFetchError("No playable tracks were found in that playlist.")

    return songs
