from pydantic import BaseModel

class MessageCreate(BaseModel):
    author_id: str
    text: str

class UserCreate(BaseModel):
    user_id: str
    chat_id: str

class UserUpdate(BaseModel):
    is_deleted: bool | None = None
    last_message_id: int | None = None
