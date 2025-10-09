import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, String
from sqlalchemy.orm import relationship
from app.core.database import DbInstance

Base = DbInstance.get_base

class User(Base):
    __tablename__ = "users"

    id = Column(
        String,
        primary_key=True,
        index=True,
        unique=True,
        default=lambda: str(uuid.uuid4())
    )
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    profile_img = Column(String, default="profile/default.png")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    messages = relationship("Message", back_populates="user", cascade="all, delete")
    rooms = relationship("RoomMember", back_populates="user", cascade="all, delete")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"
