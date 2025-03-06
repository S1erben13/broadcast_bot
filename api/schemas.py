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

class Master(BaseModel):
    model_config = ConfigDict(strict=True)

    role : str | None = None
    user_id: str
    password: bytes
    active: bool = True

class Token(BaseModel):
    access_token: str
    token_type: str