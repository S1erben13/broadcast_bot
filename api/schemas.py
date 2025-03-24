from pydantic import BaseModel


class MessageCreate(BaseModel):
    author_id: str
    text: str

class UserCreate(BaseModel):
    user_id: str
    chat_id: str

class UserUpdate(BaseModel):
    is_active: bool | None = None
    last_message_id: int | None = None

class MasterCreate(BaseModel):
    user_id: str
    chat_id: str

class MasterUpdate(BaseModel):
    is_active: bool | None = None

class ProjectCreate(BaseModel):
    master_token: str
    servant_token: str
    master_reg_token: str
    servant_reg_token: str

class ProjectUpdate(BaseModel):
    master_reg_token: str
    servant_reg_token: str