import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, Time, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from db.database import Base

SCHEMA = "tatoh"


class GuestThread(Base):
    __tablename__ = "guest_threads"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[int] = mapped_column(primary_key=True)
    guest_id: Mapped[str] = mapped_column(String(36), index=True)
    thread_id: Mapped[str] = mapped_column(String(36), unique=True)
    title: Mapped[str | None] = mapped_column(String(200), default=None)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Room(Base):
    __tablename__ = "rooms"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[int] = mapped_column(primary_key=True)
    room_name: Mapped[str] = mapped_column(String(10), unique=True)
    room_type: Mapped[str] = mapped_column(String(50))
    summary: Mapped[str] = mapped_column(Text)
    bed_queen: Mapped[int]
    bed_single: Mapped[int]
    baths: Mapped[int]
    size: Mapped[float]
    price_weekdays: Mapped[float]
    price_weekends_holidays: Mapped[float]
    price_ny_songkran: Mapped[float]
    max_guests: Mapped[int]
    steps_to_beach: Mapped[int]
    sea_view: Mapped[int]
    privacy: Mapped[int]
    steps_to_restaurant: Mapped[int]
    room_design: Mapped[int]
    room_newness: Mapped[int]
    tags: Mapped[str | None] = mapped_column(Text, default=None)


class RoomPhoto(Base):
    __tablename__ = "room_photos"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[int] = mapped_column(primary_key=True)
    room_id: Mapped[int] = mapped_column(
        ForeignKey(f"{SCHEMA}.rooms.id", ondelete="CASCADE")
    )
    filename: Mapped[str] = mapped_column(String(255))
    sort_order: Mapped[int] = mapped_column(default=0)


class BoatSchedule(Base):
    __tablename__ = "boat_schedules"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[int] = mapped_column(primary_key=True)
    origin: Mapped[str] = mapped_column(String(100))
    destination: Mapped[str] = mapped_column(String(100))
    departure: Mapped[datetime.time] = mapped_column(Time)
    arrival: Mapped[datetime.time] = mapped_column(Time)
    type: Mapped[str] = mapped_column(String(50))
    price: Mapped[int]
    infant_price: Mapped[int]
    young_children_price: Mapped[int]
    is_vip: Mapped[bool]
    is_direct: Mapped[bool]


class BusSchedule(Base):
    __tablename__ = "bus_schedules"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[int] = mapped_column(primary_key=True)
    origin: Mapped[str] = mapped_column(String(100))
    destination: Mapped[str] = mapped_column(String(100))
    departure: Mapped[datetime.time] = mapped_column(Time)
    arrival: Mapped[datetime.time] = mapped_column(Time)
    price: Mapped[int]


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(100), unique=True)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    image_urls: Mapped[list[str] | None] = mapped_column(ARRAY(Text), default=None)
