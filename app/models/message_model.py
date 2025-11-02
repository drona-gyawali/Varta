import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import BASE

Base = BASE


class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    text = Column(String, nullable=False)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    room_id = Column(String, ForeignKey("rooms.id"), nullable=False)

    user = relationship("User", back_populates="messages")
    room = relationship("Room", back_populates="messages")

    def __repr__(self):
        return (
            f"<Message(id={self.id}, user_id={self.user_id}, room_id={self.room_id})>"
        )


class Room(Base):
    __tablename__ = "rooms"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    is_private = Column(Boolean, default=False)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    owner = Column(String, nullable=False)
    messages = relationship("Message", back_populates="room", cascade="all, delete")
    members = relationship("RoomMember", back_populates="room", cascade="all, delete")

    def __repr__(self):
        return f"<Room(id={self.id}, name='{self.name}')>"


class RoomMember(Base):
    __tablename__ = "room_members"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    room_id = Column(String, ForeignKey("rooms.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    joined_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    room = relationship("Room", back_populates="members")
    user = relationship("User", back_populates="rooms")

    def __repr__(self):
        return f"<RoomMember(room_id={self.room_id}, user_id={self.user_id})>"


class RoomInvite(Base):
    __tablename__ = "room_invites"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    room_id = Column(String, ForeignKey("rooms.id"), nullable=False)
    invite_token = Column(String, nullable=False, unique=True)
    expires_at = Column(DateTime(timezone=True))
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    room = relationship("Room")


# IGNORE THIS PLEASE
# # usaage
# # create user
# u1 = User(email="a@example.com", password="123")

# # create room
# r1 = Room(name="General")

# # add user to room
# rm = RoomMember(room=r1, user=u1)

# # send message
# m1 = Message(text="Hello world", user=u1, room=r1)

# session.add_all([u1, r1, rm, m1])
# session.commit()
