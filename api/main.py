import logging
from fastapi import FastAPI, HTTPException, Depends, Header, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from config import ERROR_MESSAGES, SECRET_KEY
from models import Message, User, Master, Project
from schemas import MessageCreate, UserCreate, UserUpdate, MasterCreate, MasterUpdate, ProjectCreate, ProjectUpdate
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


async def create_entity(session, entity, entity_create, error_messages):
    """
    Helper function to create a new entity in the database.

    Args:
        session (AsyncSession): Database session.
        entity: The SQLAlchemy model class.
        entity_create: The Pydantic schema for entity creation.
        error_messages (dict): Custom error messages.

    Returns:
        dict: The created entity data.

    Raises:
        HTTPException: If an error occurs during entity creation.
    """
    try:
        db_entity = entity(**entity_create.dict())
        session.add(db_entity)
        await session.commit()
        await session.refresh(db_entity)
        return db_entity
    except IntegrityError as e:
        await session.rollback()
        if "chat_id" in str(e):
            raise HTTPException(status_code=400, detail=error_messages["chat_id_exists"])
        elif "user_id" in str(e):
            raise HTTPException(status_code=400, detail=error_messages["user_id_exists"])
        else:
            raise HTTPException(status_code=500, detail=error_messages["database_integrity_error"])
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=error_messages["internal_server_error"])


async def update_entity(session, entity, identifier, update_data, identifier_name="id"):
    """
    Helper function to update an entity in the database.

    Args:
        session (AsyncSession): Database session.
        entity: The SQLAlchemy model class.
        identifier: The identifier value (e.g., chat_id, user_id).
        update_data: The Pydantic schema for entity update.
        identifier_name (str): The name of the identifier field.

    Returns:
        dict: A status message.

    Raises:
        HTTPException: If an error occurs during the update.
    """
    try:
        await session.execute(
            update(entity)
            .where(getattr(entity, identifier_name) == identifier)
            .values(**update_data.dict(exclude_unset=True))
        )
        await session.commit()
        return {"status": f"{entity.__name__} updated"}
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))


async def get_entity(session, entity, identifier, identifier_name="id"):
    """
    Helper function to retrieve an entity from the database.

    Args:
        session (AsyncSession): Database session.
        entity: The SQLAlchemy model class.
        identifier: The identifier value (e.g., chat_id, user_id).
        identifier_name (str): The name of the identifier field.

    Returns:
        dict: The entity's data.

    Raises:
        HTTPException: If the entity is not found or an error occurs.
    """
    try:
        result = await session.execute(select(entity).where(getattr(entity, identifier_name) == identifier))
        db_entity = result.scalars().first()
        if not db_entity:
            raise HTTPException(status_code=404, detail=f"{entity.__name__} not found")
        return db_entity
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/messages")
async def create_message(
        message: MessageCreate,
        session: AsyncSession = Depends(get_async_session),
):
    """
    Creates a new message.

    Args:
        message (MessageCreate): The message data.
        session (AsyncSession): Database session.

    Returns:
        dict: The created message data.

    Raises:
        HTTPException: If an error occurs during message creation.
    """
    db_message = await create_entity(session, Message, message, ERROR_MESSAGES)
    return {
        "id": db_message.id,
        "author_id": db_message.author_id,
        "text": db_message.text,
    }


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
    db_user = await create_entity(session, User, user, ERROR_MESSAGES)
    return {
        "id": db_user.id,
        "user_id": db_user.user_id,
        "chat_id": db_user.chat_id,
    }


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
    return await update_entity(session, User, chat_id, update_data, "chat_id")


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
    user = await get_entity(session, User, chat_id, "chat_id")
    return {
        "id": user.id,
        "user_id": user.user_id,
        "chat_id": user.chat_id,
        "is_active": user.is_active,
    }


@app.get("/messages")
async def get_messages(
        last_message_id: int = 0,
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
                {"id": message.id, "author_id": message.author_id, "project_id": message.project_id, "text": message.text}
                for message in messages
            ]
            return {"messages": messages_list}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching messages: {str(e)}")


@app.get("/users")
async def get_users():
    """
    Retrieves all users.

    Returns:
        dict: A list of users.

    Raises:
        HTTPException: If an error occurs while fetching users.
    """
    async with async_session_factory() as session:
        try:
            query = select(User)
            result = await session.execute(query)
            users = result.scalars().all()

            user_list = [
                {"id": user.id, "user_id": user.user_id, "chat_id": user.chat_id, "is_active": user.is_active,
                 "last_message_id": user.last_message_id}
                for user in users
            ]
            return {"users": user_list}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching users: {str(e)}")


@app.get("/masters")
async def get_masters():
    """
    Retrieves all active masters.

    Returns:
        dict: A list of masters.

    Raises:
        HTTPException: If an error occurs while fetching masters.
    """
    async with async_session_factory() as session:
        try:
            query = select(Master).where(Master.is_active == True)
            result = await session.execute(query)
            masters = result.scalars().all()

            masters_list = [
                {"id": master.id, "user_id": master.user_id, "chat_id": master.chat_id}
                for master in masters
            ]
            return {"masters": masters_list}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching masters: {str(e)}")


@app.post("/masters")
async def create_master(
        master: MasterCreate,
        session: AsyncSession = Depends(get_async_session),
):
    """
    Creates a new master.

    Args:
        master (MasterCreate): The master data.
        session (AsyncSession): Database session.

    Returns:
        dict: The created master data.

    Raises:
        HTTPException: If a master with the same user_id or chat_id already exists or another error occurs.
    """
    db_master = await create_entity(session, Master, master, ERROR_MESSAGES)
    return {
        "id": db_master.id,
        "user_id": db_master.user_id,
        "chat_id": db_master.chat_id,
    }


@app.get("/masters/{user_id}")
async def get_master(
        user_id: str,
        session: AsyncSession = Depends(get_async_session),
):
    """
    Retrieves a master by their user ID.

    Args:
        user_id (str): The master's user ID.
        session (AsyncSession): Database session.

    Returns:
        dict: The master's data.

    Raises:
        HTTPException: If the master is not found or an error occurs.
    """
    master = await get_entity(session, Master, user_id, "user_id")
    return {
        "id": master.id,
        "user_id": master.user_id,
        "chat_id": master.chat_id,
    }


@app.patch("/masters/{user_id}")
async def update_master(
        user_id: str,
        update_data: MasterUpdate,
        session: AsyncSession = Depends(get_async_session),
):
    """
    Updates a master's data.

    Args:
        user_id (str): The master's user ID.
        update_data (MasterUpdate): The data to update.
        session (AsyncSession): Database session.

    Returns:
        dict: A status message.

    Raises:
        HTTPException: If an error occurs during the update.
    """
    return await update_entity(session, Master, user_id, update_data, "user_id")

@app.exception_handler(RequestValidationError)
async def hide_header_error(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": "Invalid request data"},  # Общее сообщение без деталей
    )

async def verify_secret_key(secret_key: str = Header(..., alias="X-Secret-Key")):
    if secret_key != SECRET_KEY:
        raise HTTPException(status_code=403, detail="Forbidden")
    return True

@app.get("/projects")
async def get_users(
        _ = Depends(verify_secret_key)
):
    async with async_session_factory() as session:
        try:
            query = select(Project)
            result = await session.execute(query)
            projects = result.scalars().all()

            project_list = [
                {"id": project.id, "master_token": project.master_token, "servant_token": project.servant_token, "master_reg_token": project.master_reg_token, "servant_reg_token": project.servant_reg_token, "is_active" : project.is_active}
                for project in projects
            ]
            return {"projects": project_list}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching projects: {str(e)}")

@app.post("/projects")
async def create_project(
        project: ProjectCreate,
        _ = Depends(verify_secret_key),
        session: AsyncSession = Depends(get_async_session),
):
    db_project = await create_entity(session, Project, project, ERROR_MESSAGES)
    return {"id": db_project.id}


@app.patch("/projects/{project_id}")
async def update_project(
        project_id: int,
        update_data: ProjectUpdate,
        _ = Depends(verify_secret_key),
        session: AsyncSession = Depends(get_async_session),
):
    return await update_entity(session, Project, project_id, update_data, "project_id")


@app.delete("/projects/{project_id}")
async def delete_project(
        project_id: int,
        _ = Depends(verify_secret_key),
        session: AsyncSession = Depends(get_async_session),
):
    result = await session.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project.is_active = False
    await session.commit()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
