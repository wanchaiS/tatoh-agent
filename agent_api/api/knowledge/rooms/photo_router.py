"""Photo management router for rooms."""

import logging
import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from PIL import Image as PILImage
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_db, require_auth
from api.knowledge.rooms.photo_schemas import PhotoReorderItem, PhotoResponse
from api.schemas import OkResponse
from core.config import STATIC_DIR, STATIC_URL_PREFIX
from core.photo_helpers import THUMBNAIL_WIDTHS, build_photo_urls
from db.models import Room as RoomModel
from db.models import RoomPhoto

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/rooms", tags=["room_photos"])

PHOTOS_DIR = STATIC_DIR / "photos" / "rooms"


def _create_thumbnails(
    source_path: Path,
    room_photos_dir: Path,
    filename: str,
) -> None:
    """Generate three JPEG thumbnails at 240w, 480w, 960w with aspect-preserving resize."""
    try:
        with PILImage.open(source_path) as opened:
            img: PILImage.Image = (
                opened.convert("RGB") if opened.mode in ("RGBA", "P") else opened
            )
            for width in THUMBNAIL_WIDTHS:
                dest_dir = room_photos_dir / "thumbnails" / str(width)
                dest_dir.mkdir(parents=True, exist_ok=True)
                resized = img.copy()
                resized.thumbnail((width, 10000))
                resized.save(dest_dir / filename, "JPEG", quality=85)
    except Exception as e:
        logger.error("Error creating thumbnails: %s", e)


@router.get("/{room_id}/photos", response_model=list[PhotoResponse])
async def list_photos(
    room_id: int,
    _: str = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
) -> list[PhotoResponse]:
    """List all photos for a room, ordered by sort_order."""
    # Verify room exists
    room_check = await db.execute(select(RoomModel).where(RoomModel.id == room_id))
    if room_check.scalars().first() is None:
        raise HTTPException(status_code=404, detail=f"Room {room_id} not found")

    # Get photos
    photos_result = await db.execute(
        select(RoomPhoto)
        .where(RoomPhoto.room_id == room_id)
        .order_by(RoomPhoto.sort_order)
    )
    photos = photos_result.scalars().all()

    return [
        PhotoResponse(
            id=photo.id,
            filename=photo.filename,
            sort_order=photo.sort_order,
            **build_photo_urls(room_id, photo.filename),
        )
        for photo in photos
    ]


@router.post(
    "/{room_id}/photos",
    response_model=PhotoResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_photo(
    room_id: int,
    file: UploadFile = File(...),
    _: str = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
) -> PhotoResponse:
    """Upload a photo for a room."""
    # Verify room exists
    room_check = await db.execute(select(RoomModel).where(RoomModel.id == room_id))
    if room_check.scalars().first() is None:
        raise HTTPException(status_code=404, detail=f"Room {room_id} not found")

    # Create directory if it doesn't exist
    room_photos_dir = PHOTOS_DIR / str(room_id)
    room_photos_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename: uuid_original_name
    file_ext = os.path.splitext(file.filename or "image")[1]
    filename = f"{room_id}_{uuid.uuid4().hex}{file_ext}"
    filepath = room_photos_dir / filename

    # Read and validate file size
    content = await file.read()
    MAX_SIZE = 5 * 1024 * 1024  # 5 MB
    if len(content) > MAX_SIZE:
        raise HTTPException(status_code=413, detail="File too large. Max 5 MB.")

    with open(filepath, "wb") as f:
        f.write(content)

    # Create thumbnails (240w, 480w, 960w)
    _create_thumbnails(filepath, room_photos_dir, filename)

    # Get max sort_order for this room
    sort_result = await db.execute(
        select(RoomPhoto.sort_order)
        .where(RoomPhoto.room_id == room_id)
        .order_by(RoomPhoto.sort_order.desc())
    )
    max_order = sort_result.scalars().first() or -1
    new_sort_order = max_order + 1

    # Save to database
    photo = RoomPhoto(
        room_id=room_id,
        filename=filename,
        sort_order=new_sort_order,
    )
    db.add(photo)
    await db.commit()
    await db.refresh(photo)

    return PhotoResponse(
        id=photo.id,
        filename=photo.filename,
        sort_order=photo.sort_order,
        url=f"{STATIC_URL_PREFIX}/photos/rooms/{room_id}/{filename}",
        thumbnails={
            w: f"{STATIC_URL_PREFIX}/photos/rooms/{room_id}/thumbnails/{w}/{filename}"
            for w in THUMBNAIL_WIDTHS
        },
    )


@router.delete("/{room_id}/photos/{photo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_photo(
    room_id: int,
    photo_id: int,
    _: str = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a photo."""
    photo_result = await db.execute(
        select(RoomPhoto)
        .where(RoomPhoto.id == photo_id)
        .where(RoomPhoto.room_id == room_id)
    )
    photo = photo_result.scalars().first()

    if not photo:
        raise HTTPException(status_code=404, detail=f"Photo {photo_id} not found")

    # Delete file from disk
    filepath = PHOTOS_DIR / str(room_id) / photo.filename
    if filepath.exists():
        filepath.unlink()

    # Delete all thumbnail sizes
    for w in THUMBNAIL_WIDTHS:
        thumbnail_path = (
            PHOTOS_DIR / str(room_id) / "thumbnails" / str(w) / photo.filename
        )
        if thumbnail_path.exists():
            thumbnail_path.unlink()

    # Delete from database
    await db.execute(delete(RoomPhoto).where(RoomPhoto.id == photo_id))
    await db.commit()


@router.patch("/{room_id}/photos/reorder", response_model=OkResponse)
async def reorder_photos(
    room_id: int,
    items: list[PhotoReorderItem],
    _: str = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
) -> OkResponse:
    """Reorder photos by updating sort_order."""
    # Verify room exists
    room_check = await db.execute(select(RoomModel).where(RoomModel.id == room_id))
    if room_check.scalars().first() is None:
        raise HTTPException(status_code=404, detail=f"Room {room_id} not found")

    # Update sort_order for each photo
    for item in items:
        await db.execute(
            update(RoomPhoto)
            .where(RoomPhoto.id == item.id)
            .where(RoomPhoto.room_id == room_id)
            .values(sort_order=item.sort_order)
        )

    await db.commit()
    return OkResponse()
