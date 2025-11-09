from datetime import datetime
from typing import List

from pydantic import BaseModel, EmailStr


class CreateLink(BaseModel):
    room_name: str
    is_private: bool


class JoinRoom(BaseModel):
    invite_token: str


class MessageCreation(BaseModel):
    text: str
    room_id: str


class Room(BaseModel):
    id: str
    is_private: bool
    owner: str
    name: str
    created_at: datetime


class MessageResponse(BaseModel):
    id: str
    text: str
    created_at: datetime
    user_id: str


class RoomResponseModel(BaseModel):
    id: str
    is_private: bool
    owner: str
    name: str


class PageMetadata(BaseModel):
    total_items: int
    limit: int
    offset: int
    total_pages: int


class PaginationResponse(BaseModel):
    message: List[Room]
    pagination: PageMetadata


class UserRoomResponse(BaseModel):
    room: RoomResponseModel
    messages: List[MessageResponse]
    pagination: PageMetadata


class RoomMemberModel(BaseModel):
    user_id: str
    joined_at: datetime


class RoomMemberResponse(BaseModel):
    members: List[RoomMemberModel]
    pagination: PageMetadata


class EmailSchema(BaseModel):
    subject: str
    recipients: EmailStr
    body: str
