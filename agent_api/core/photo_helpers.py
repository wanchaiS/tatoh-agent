from typing import TypedDict

from core.config import STATIC_URL_PREFIX

THUMBNAIL_WIDTHS = (240, 480, 960)

class EmbeddedPhoto(TypedDict):
    url: str
    thumbnails: dict[int, str]

def build_photo_urls(room_id: int, filename: str) -> EmbeddedPhoto:
    """Build url + thumbnails dict for a photo. Pure helper — no DB, no I/O."""
    return {
        "url": f"{STATIC_URL_PREFIX}/photos/rooms/{room_id}/{filename}",
        "thumbnails": {
            w: f"{STATIC_URL_PREFIX}/photos/rooms/{room_id}/thumbnails/{w}/{filename}"
            for w in THUMBNAIL_WIDTHS
        },
    }
