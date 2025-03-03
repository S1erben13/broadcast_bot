import logging

import httpx
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from sqlalchemy import select, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from models import Message, User
from schemas import MessageCreate, UserCreate
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


async def send_follower_to_api(user_id: int | str, chat_id: int | str) -> None:
    """
    Функция для отправки пользователя на api:8000/users.
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "http://api:8000/users",
                json={"user_id": str(user_id), "chat_id": str(chat_id)}
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 400:
                logging.warning(f"Chat ID already exists: {e}")
            else:
                logging.error(f"Ошибка при отправке пользователя в api: {e}")
        except httpx.HTTPError as e:
            logging.error(f"Ошибка при отправке пользователя в api: {e}")


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
        background_tasks.add_task(send_follower_to_api, message.text, message.chat_id)

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
        if "user_chat_id_key" in str(e):  # Проверяем, что ошибка связана с уникальностью chat_id
            raise HTTPException(status_code=400, detail="Chat ID already exists")
        else:
            raise HTTPException(status_code=500, detail="Database integrity error")
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/users/{chat_id}")
async def delete_user(
    chat_id: str,
    session: AsyncSession = Depends(get_async_session),
):
    try:
        result = await session.execute(
            delete(User).where(User.chat_id == chat_id)
        )
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="User not found")
        await session.commit()
        return {"status": "User deleted"}
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ping")
async def ping():
    return {"message": "pong!"}


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
