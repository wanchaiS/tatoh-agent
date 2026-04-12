#!/usr/bin/env python3
"""
Migrate room photos to regenerate multi-size thumbnails.

Steps:
  1. Rename  static/photos/rooms  →  static/photos/legacy_rooms
  2. For each room directory in legacy_rooms, re-upload every original
     photo file (skips 'thumbnails' sub-dirs) via POST /api/rooms/{id}/photos
  3. Prints a summary of successes / failures

Usage (from repo root or agent_api/):
    python scripts/reupload_photos.py [--base-url http://127.0.0.1:8000]
"""

import argparse
import mimetypes
import shutil
import sys
from pathlib import Path

import requests

STATIC_DIR = Path(__file__).parent.parent / "static"
ROOMS_DIR = STATIC_DIR / "photos" / "rooms"
LEGACY_DIR = STATIC_DIR / "photos" / "legacy_rooms"


def move_to_legacy():
    if not ROOMS_DIR.exists():
        print(f"[skip] {ROOMS_DIR} does not exist — nothing to migrate.")
        return False
    if LEGACY_DIR.exists():
        print(f"[skip] {LEGACY_DIR} already exists — skipping rename.")
        return True
    shutil.move(str(ROOMS_DIR), str(LEGACY_DIR))
    print(f"[move] {ROOMS_DIR} → {LEGACY_DIR}")
    return True


def iter_original_photos(room_dir: Path):
    """Yield original photo files, skipping the thumbnails sub-directory."""
    for f in sorted(room_dir.iterdir()):
        if f.name == "thumbnails" or f.name.startswith("."):
            continue
        if f.is_file():
            yield f


def upload_photo(base_url: str, room_id: int, photo_path: Path) -> bool:
    url = f"{base_url}/api/rooms/{room_id}/photos"
    mime = mimetypes.guess_type(photo_path.name)[0] or "image/jpeg"
    try:
        with photo_path.open("rb") as fh:
            resp = requests.post(url, files={"file": (photo_path.name, fh, mime)}, timeout=30)
        if resp.status_code == 201:
            return True
        print(f"  [error] {photo_path.name} → HTTP {resp.status_code}: {resp.text[:120]}")
        return False
    except Exception as exc:
        print(f"  [error] {photo_path.name} → {exc}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Re-upload room photos via API.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="API base URL")
    args = parser.parse_args()

    if not move_to_legacy():
        sys.exit(1)

    room_dirs = sorted(
        (d for d in LEGACY_DIR.iterdir() if d.is_dir() and d.name.isdigit()),
        key=lambda d: int(d.name),
    )

    if not room_dirs:
        print("[warn] No room directories found in legacy_rooms.")
        sys.exit(0)

    total_ok = total_fail = 0

    for room_dir in room_dirs:
        room_id = int(room_dir.name)
        photos = list(iter_original_photos(room_dir))
        if not photos:
            print(f"[room {room_id}] no photos — skipping")
            continue

        print(f"[room {room_id}] uploading {len(photos)} photo(s)…")
        ok = fail = 0
        for photo in photos:
            if upload_photo(args.base_url, room_id, photo):
                print(f"  [ok] {photo.name}")
                ok += 1
            else:
                fail += 1

        total_ok += ok
        total_fail += fail
        print(f"  → {ok} ok, {fail} failed")

    print(f"\nDone. Total: {total_ok} uploaded, {total_fail} failed.")
    if total_fail:
        sys.exit(1)


if __name__ == "__main__":
    main()
