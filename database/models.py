"""
SQLAlchemy models for the Media Downloader Bot database.
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, BigInteger, DateTime, Boolean, Text,
    ForeignKey, Float, Enum as SAEnum,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    """Declarative base for all models."""
    pass


class User(Base):
    """Telegram user registered in the bot."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    settings = relationship("UserSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")
    downloads = relationship("Download", back_populates="user", cascade="all, delete-orphan")


class UserSettings(Base):
    """Per-user persistent settings."""
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    media_type = Column(String(20), default="video")          # video | audio
    video_quality = Column(String(20), default="720p")
    video_format = Column(String(10), default="mp4")
    audio_quality = Column(String(20), default="320")
    audio_format = Column(String(10), default="mp3")
    subtitle_enabled = Column(Boolean, default=False)
    subtitle_language = Column(String(10), default="ru")

    user = relationship("User", back_populates="settings")


class Download(Base):
    """Download task record."""
    __tablename__ = "downloads"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    url = Column(Text, nullable=False)
    title = Column(String(500), nullable=True)
    media_type = Column(String(20), nullable=True)     # video | audio | subtitles
    format = Column(String(10), nullable=True)
    quality = Column(String(20), nullable=True)
    status = Column(String(20), default="pending")     # pending | downloading | processing | sending | done | error | cancelled
    file_size = Column(BigInteger, nullable=True)
    file_path = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="downloads")
