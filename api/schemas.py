from pydantic import BaseModel, ConfigDict


class MessageCreate(BaseModel):
    author_id: str
    text: str

class UserCreate(BaseModel):
    user_id: str
    chat_id: str

class UserUpdate(BaseModel):
    followed: bool | None = None
    last_message_id: int | None = None

class MasterCreate(BaseModel):
    user_id: str
    chat_id: str

class MasterUpdate(BaseModel):
    active: bool | None = None