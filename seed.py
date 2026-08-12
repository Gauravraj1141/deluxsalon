"""Insert example seed data (one playlist with 8 songs).

Usage:
    python seed.py
    docker compose exec backend python seed.py
"""

from app.db.database import SessionLocal
from app.db.models import Playlist, Song

SEED_PLAYLIST_TITLE = "Punjabi Hits"

SEED_SONGS = [
    {"title": "36", "artist": "Unknown", "video_id": "GmytqWwPazE", "duration": 239},
    {"title": "Batti", "artist": "Unknown", "video_id": "l7jf_VwYu94", "duration": 189},
    {"title": "Shokeen", "artist": "Rabb Da Radio 2", "video_id": "SHqkcFNTJ4w", "duration": 201},
    {"title": "BHANG BHAROSA", "artist": "DeeVoy Singh", "video_id": "QrM8BiBvnVM", "duration": 184},
    {"title": "Bawa Bajte Hain", "artist": "Unknown", "video_id": "n5BHXaLvNfM", "duration": 143},
    {"title": "Saza-E-Maut", "artist": "feat. Raftaar", "video_id": "49_iB_n7SOo", "duration": 180},
    {"title": "Roll Up", "artist": "feat. Badshah", "video_id": "wo1IA3TyR6o", "duration": 196},
    {"title": "Villain", "artist": "feat. Karma, Ikka", "video_id": "HrC8-heR1Xc", "duration": 219},
]


def run() -> None:
    db = SessionLocal()
    try:
        existing = db.query(Playlist).filter(Playlist.title == SEED_PLAYLIST_TITLE).first()
        if existing:
            print(f"Seed playlist '{SEED_PLAYLIST_TITLE}' already exists, skipping.")
            return

        playlist = Playlist(
            title=SEED_PLAYLIST_TITLE,
            writer="Admin",
            description="Example seed playlist.",
        )
        db.add(playlist)
        db.flush()

        for order, song_data in enumerate(SEED_SONGS, start=1):
            db.add(Song(playlist_id=playlist.id, sort_order=order, **song_data))

        db.commit()
        print(f"Seeded playlist '{playlist.title}' (id={playlist.id}) with {len(SEED_SONGS)} songs.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
