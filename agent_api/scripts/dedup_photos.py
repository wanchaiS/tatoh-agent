#!/usr/bin/env python3
"""
Remove RoomPhoto DB records whose file no longer exists on disk,
then renumber sort_order starting from 0 per room.

Usage (from agent_api/):
    uv run python scripts/dedup_photos.py
"""

import asyncio
import sys
from pathlib import Path

# Ensure agent_api package is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from core.config import STATIC_DIR, settings
from db.models import RoomPhoto

ROOMS_DIR = STATIC_DIR / "photos" / "rooms"


async def main():
    url = settings.database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    engine = create_async_engine(url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        result = await db.execute(select(RoomPhoto).order_by(RoomPhoto.room_id, RoomPhoto.id))
        all_photos = result.scalars().all()

        stale_ids = []
        for photo in all_photos:
            path = ROOMS_DIR / str(photo.room_id) / photo.filename
            if not path.exists():
                stale_ids.append(photo.id)

        if stale_ids:
            await db.execute(delete(RoomPhoto).where(RoomPhoto.id.in_(stale_ids)))
            print(f"Deleted {len(stale_ids)} stale records.")
        else:
            print("No stale records found.")

        # Renumber sort_order per room
        result = await db.execute(select(RoomPhoto).order_by(RoomPhoto.room_id, RoomPhoto.id))
        remaining = result.scalars().all()

        current_room = None
        counter = 0
        for photo in remaining:
            if photo.room_id != current_room:
                current_room = photo.room_id
                counter = 0
            await db.execute(
                update(RoomPhoto).where(RoomPhoto.id == photo.id).values(sort_order=counter)
            )
            counter += 1

        await db.commit()
        print(f"Renumbered sort_order for {len(remaining)} remaining records.")

    await engine.dispose()
    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
