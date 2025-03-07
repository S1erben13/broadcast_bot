import logging
import httpx
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from config import ERROR_MESSAGES
from models import Message, User, Master
from schemas import MessageCreate, UserCreate, UserUpdate, MasterCreate
from database import async_session_factory, Base, async_engine

app = FastAPI()

logging.basicConfig(level=logging.INFO)

async def get_async_session() -> AsyncSession:
    """
    Provides an asynchronous database session.

    Yields:
        AsyncSession: An asynchronous SQLAlchemy session.
    """
    async with async_session_factory() as session:
        yield session


@app.on_event("startup")
async def startup():
    """
    Initializes the database tables on application startup.
    """
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logging.info("Database tables created successfully.")


@app.post("/messages")
async def create_message(
    message: MessageCreate,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Creates a new message and sends it to the servant in the background.

    Args:
        message (MessageCreate): The message data.
        background_tasks (BackgroundTasks): FastAPI's background tasks utility.
        session (AsyncSession): Database session.

    Returns:
        dict: The created message data.

    Raises:
        HTTPException: If an error occurs during message creation.
    """
    try:
        db_message = Message(author_id=message.author_id, text=message.text)
        session.add(db_message)
        await session.commit()
        await session.refresh(db_message)

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
    """
    Creates a new user.

    Args:
        user (UserCreate): The user data.
        session (AsyncSession): Database session.

    Returns:
        dict: The created user data.

    Raises:
        HTTPException: If a user with the same chat_id already exists or another error occurs.
    """
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
    """
    Updates a user's data.

    Args:
        chat_id (str): The user's chat ID.
        update_data (UserUpdate): The data to update.
        session (AsyncSession): Database session.

    Returns:
        dict: A status message.

    Raises:
        HTTPException: If an error occurs during the update.
    """
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
    """
    Retrieves a user by their chat ID.

    Args:
        chat_id (str): The user's chat ID.
        session (AsyncSession): Database session.

    Returns:
        dict: The user's data.

    Raises:
        HTTPException: If the user is not found or an error occurs.
    """
    try:
        result = await session.execute(select(User).where(User.chat_id == chat_id))
        user = result.scalars().first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {
            "id": user.id,
            "user_id": user.user_id,
            "chat_id": user.chat_id,
            "followed": user.followed,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/messages")
async def get_messages(
    last_message_id: int,
):
    """
    Retrieves messages created after a specific message ID.

    Args:
        last_message_id (int): The ID of the last message the user has seen.

    Returns:
        dict: A list of new messages.

    Raises:
        HTTPException: If an error occurs while fetching messages.
    """
    async with async_session_factory() as session:
        try:
            query = select(Message).where(Message.id > last_message_id)
            result = await session.execute(query)
            messages = result.scalars().all()

            messages_list = [
                {"id": message.id, "author_id": message.author_id, "text": message.text}
                for message in messages
            ]
            return {"messages": messages_list}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching messages: {str(e)}")

@app.get("/users")
async def get_users():
    async with async_session_factory() as session:
        try:
            query = select(User)
            result = await session.execute(query)
            users = result.scalars().all()

            user_list = [
                {"id": user.id, "user_id": user.user_id, "chat_id": user.chat_id, "followed": user.followed, "last_message_id": user.last_message_id}
                for user in users
            ]
            return {"users": user_list}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Ошибка при получении пользователей: {str(e)}")

@app.post("/masters")
async def create_master(
    user: MasterCreate,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Creates a new Master.

    Args:
        user (MasterCreate): The user data.
        session (AsyncSession): Database session.

    Returns:
        dict: The created master data.

    Raises:
        HTTPException: If a user with the same chat_id already exists or another error occurs.
    """
    try:
        db_master = Master(user_id=user.user_id)
        session.add(db_master)
        await session.commit()
        await session.refresh(db_master)

        return {
            "id": db_master.id,
            "user_id": db_master.user_id,
            "chat_id": db_master.user_id,
        }
    except IntegrityError as e:
        await session.rollback()
        if "master_user_id_key" in str(e):
            raise HTTPException(status_code=400, detail=ERROR_MESSAGES["user_id_exists"])
        elif "master_chat_id_key" in str(e):
            raise HTTPException(status_code=400, detail=ERROR_MESSAGES["chat_id_exists"])
        else:
            raise HTTPException(status_code=500, detail=ERROR_MESSAGES["database_integrity_error"])
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=ERROR_MESSAGES["internal_server_error"])

async def is_followed(chat_id):
    response = await get_users()
    for user in response["users"]:
        if user["chat_id"] == chat_id:
            return True
    return False


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
