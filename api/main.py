import logging

import httpx
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from sqlalchemy import select, delete, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from config import SERVANT_BASE_URL, SUCCESS_MESSAGES, ERROR_MESSAGES
from models import Message, User
from schemas import MessageCreate, UserCreate, UserUpdate
from database import async_session_factory, Base, async_engine

app = FastAPI()

logging.basicConfig(level=logging.INFO)

async def get_async_session() -> AsyncSession:
    async with async_session_factory() as session:
        yield session


@app.on_event("startup")
async def startup():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # logging.INFO("Таблицы успешно созданы")


async def send_message_to_servant(message_text: str):
    """
    Функция для отправки сообщения на servant.
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{SERVANT_BASE_URL}/send_message",  # Используем переменную
                json={"text": message_text}
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            logging.error(f"Ошибка при отправке сообщения на servant: {e}")


@app.post("/messages")
async def create_message(
        message: MessageCreate,
        background_tasks: BackgroundTasks,
        session: AsyncSession = Depends(get_async_session),
):
    try:
        # Сохраняем сообщение в базу данных
        db_message = Message(author_id=message.author_id, text=message.text)
        session.add(db_message)
        await session.commit()
        await session.refresh(db_message)

        # Добавляем задачу на отправку сообщения в servant
        background_tasks.add_task(send_message_to_servant, message.text)

        # Возвращаем результат
        return {
            "id": db_message.id,
            "author_id": db_message.author_id,
            "text": db_message.text,
        }
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/users")
async def create_user(
        user: UserCreate,
        session: AsyncSession = Depends(get_async_session),
):
    try:
        db_user = User(user_id=user.user_id, chat_id=user.chat_id)
        session.add(db_user)
        await session.commit()
        await session.refresh(db_user)

        return {
            "id": db_user.id,
            "user_id": db_user.user_id,
            "chat_id": db_user.chat_id,
        }
    except IntegrityError as e:
        await session.rollback()
        if "user_chat_id_key" in str(e):
            raise HTTPException(status_code=400, detail=ERROR_MESSAGES["chat_id_exists"])
        else:
            raise HTTPException(status_code=500, detail=ERROR_MESSAGES["database_integrity_error"])
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=ERROR_MESSAGES["internal_server_error"])

@app.patch("/users/{chat_id}")
async def update_user(
    chat_id: str,
    update_data: UserUpdate,
    session: AsyncSession = Depends(get_async_session),
):
    try:
        await session.execute(
            update(User)
            .where(User.chat_id == chat_id)
            .values(**update_data.dict(exclude_unset=True))
        )
        await session.commit()
        return {"status": "User updated"}
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/users/{chat_id}")
async def get_user(
    chat_id: str,
    session: AsyncSession = Depends(get_async_session),
):
    try:
        result = await session.execute(select(User).where(User.chat_id == chat_id))
        user = result.scalars().first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {
            "id": user.id,
            "user_id": user.user_id,
            "chat_id": user.chat_id,
            "is_deleted": user.is_deleted,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ping")
async def ping():
    return {"message": SUCCESS_MESSAGES["pong"]}


@app.get("/messages")
async def get_messages():
    async with async_session_factory() as session:
        try:
            # Получаем все сообщения из базы данных
            query = select(Message)
            result = await session.execute(query)
            messages = result.scalars().all()

            # Преобразуем сообщения в список словарей
            messages_list = [
                {"id": message.id, "author_id": message.author_id, "text": message.text}
                for message in messages
            ]
            return {"messages": messages_list}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Ошибка при получении сообщений: {str(e)}")

@app.get("/users")
async def get_users():
    async with async_session_factory() as session:
        try:
            query = select(User)
            result = await session.execute(query)
            users = result.scalars().all()

            user_list = [
                {"id": user.id, "user_id": user.user_id, "chat_id": user.chat_id}
                for user in users
            ]
            return {"users": user_list}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Ошибка при получении пользователей: {str(e)}")

async def is_followed(chat_id):
    response = await get_users()
    for user in response["users"]:
        if user["chat_id"] == chat_id:
            return True
    return False


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
