from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String, Text, Time
from sqlalchemy.dialects.postgresql import ARRAY

from db.database import Base


SCHEMA = "tatoh"


class Room(Base):
    __tablename__ = "rooms"
    __table_args__ = {"schema": SCHEMA}

    id = Column(Integer, primary_key=True)
    room_name = Column(String(10), unique=True, nullable=False)
    room_type = Column(String(50), nullable=False)
    summary = Column(Text, nullable=False)
    bed_queen = Column(Integer, nullable=False)
    bed_single = Column(Integer, nullable=False)
    baths = Column(Integer, nullable=False)
    size = Column(Float, nullable=False)
    price_weekdays = Column(Float, nullable=False)
    price_weekends_holidays = Column(Float, nullable=False)
    price_ny_songkran = Column(Float, nullable=False)
    max_guests = Column(Integer, nullable=False)
    steps_to_beach = Column(Integer, nullable=False)
    sea_view = Column(Integer, nullable=False)
    privacy = Column(Integer, nullable=False)
    steps_to_restaurant = Column(Integer, nullable=False)
    room_design = Column(Integer, nullable=False)
    room_newness = Column(Integer, nullable=False)
    tags = Column(Text, nullable=True)


class RoomPhoto(Base):
    __tablename__ = "room_photos"
    __table_args__ = {"schema": SCHEMA}

    id = Column(Integer, primary_key=True)
    room_id = Column(Integer, ForeignKey(f"{SCHEMA}.rooms.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(255), nullable=False)
    sort_order = Column(Integer, nullable=False, default=0)


class BoatSchedule(Base):
    __tablename__ = "boat_schedules"
    __table_args__ = {"schema": SCHEMA}

    id = Column(Integer, primary_key=True)
    origin = Column(String(100), nullable=False)
    destination = Column(String(100), nullable=False)
    departure = Column(Time, nullable=False)
    arrival = Column(Time, nullable=False)
    type = Column(String(50), nullable=False)
    price = Column(Integer, nullable=False)
    infant_price = Column(Integer, nullable=False)
    young_children_price = Column(Integer, nullable=False)
    is_vip = Column(Boolean, nullable=False)
    is_direct = Column(Boolean, nullable=False)


class BusSchedule(Base):
    __tablename__ = "bus_schedules"
    __table_args__ = {"schema": SCHEMA}

    id = Column(Integer, primary_key=True)
    origin = Column(String(100), nullable=False)
    destination = Column(String(100), nullable=False)
    departure = Column(Time, nullable=False)
    arrival = Column(Time, nullable=False)
    price = Column(Integer, nullable=False)


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"
    __table_args__ = {"schema": SCHEMA}

    id = Column(Integer, primary_key=True)
    key = Column(String(100), unique=True, nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    image_urls = Column(ARRAY(Text), nullable=True)
