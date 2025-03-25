import logging
from fastapi import FastAPI, HTTPException, Depends, Header, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
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
    """Yields an async database session."""
    async with async_session_factory() as session:
        yield session


@app.on_event("startup")
async def startup():
    """Initialize database tables on startup."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logging.info("Database tables created.")
    # for hand test
    try:
        from init_test_bots import create_test_projects
        await create_test_projects()
        logging.info("Test bots initialized.")
    except Exception:
        logging.info("Test bots exists.")

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

# Unified CRUD operations
async def create_entity(
        session: AsyncSession,
        model: type,
        data: BaseModel,
        error_map: dict = None
):
    """
    Creates a new entity in database.

    Args:
        session: Async database session
        model: SQLAlchemy model class
        data: Pydantic schema for creation
        error_map: Custom error messages for IntegrityError

    Returns:
        Created entity instance

    Raises:
        HTTPException: On creation error
    """
    try:
        entity = model(**data.dict())
        session.add(entity)
        await session.commit()
        await session.refresh(entity)
        return entity
    except IntegrityError as e:
        await session.rollback()
        if error_map:
            for key, msg in error_map.items():
                if key in str(e):
                    raise HTTPException(400, detail=msg)
        raise HTTPException(500, detail="Database integrity error")
    except Exception as e:
        await session.rollback()
        raise HTTPException(500, detail=str(e))


async def get_entity(
        session: AsyncSession,
        model: type,
        identifier: str | int,
        id_field: str = "id",
        extra_filters: dict = None
):
    """
    Retrieves entity with optional filters.

    Args:
        session: Async database session
        model: SQLAlchemy model class
        identifier: Value to match against id_field
        id_field: Field name to filter by
        extra_filters: Additional {field: value} filters

    Returns:
        Entity instance if found

    Raises:
        HTTPException: If not found or DB error
    """
    try:
        query = select(model).where(getattr(model, id_field) == identifier)
        if extra_filters:
            for field, value in extra_filters.items():
                query = query.where(getattr(model, field) == value)

        result = await session.execute(query)
        entity = result.scalars().first()
        if not entity:
            raise HTTPException(404, detail=f"{model.__name__} not found")
        return entity
    except Exception as e:
        raise HTTPException(500, detail=str(e))


async def update_entity(
        session: AsyncSession,
        model: type,
        identifier: str | int,
        update_data: BaseModel,
        id_field: str = "id",
        extra_filters: dict = None
):
    """
    Updates entity in database.

    Args:
        session: Async database session
        model: SQLAlchemy model class
        identifier: Value to match against id_field
        update_data: Pydantic schema with update fields
        id_field: Field name to filter by
        extra_filters: Additional {field: value} filters

    Returns:
        dict: Status message

    Raises:
        HTTPException: On update error
    """
    try:
        query = update(model).where(getattr(model, id_field) == identifier)
        if extra_filters:
            for field, value in extra_filters.items():
                query = query.where(getattr(model, field) == value)

        await session.execute(query.values(**update_data.dict(exclude_unset=True)))
        await session.commit()
        return {"status": f"{model.__name__} updated"}
    except Exception as e:
        await session.rollback()
        raise HTTPException(500, detail=str(e))


async def get_entities(
        session: AsyncSession,
        model: type,
        base_filters: dict = None,
        extra_filters: dict = None
):
    """
    Retrieves multiple entities with optional filters.

    Args:
        session: Async database session
        model: SQLAlchemy model class
        base_filters: Required filters (e.g., is_active=True)
        extra_filters: Optional additional filters

    Returns:
        List of entity instances
    """
    try:
        query = select(model)
        if base_filters:
            for field, value in base_filters.items():
                query = query.where(getattr(model, field) == value)
        if extra_filters:
            for field, value in extra_filters.items():
                query = query.where(getattr(model, field) == value)

        result = await session.execute(query)
        return result.scalars().all()
    except Exception as e:
        raise HTTPException(500, detail=str(e))


# Message endpoints
@app.post("/messages")
async def create_message(
        message: MessageCreate,
        session: AsyncSession = Depends(get_async_session)
):
    """Creates new message."""
    db_message = await create_entity(session, Message, message, ERROR_MESSAGES)
    return {
        "id": db_message.id,
        "telegram_user_id": db_message.telegram_user_id,
        "project_id": db_message.project_id,
        "text": db_message.text,
    }


@app.get("/messages")
async def get_messages(
    last_message_id: int = 0,
    project_id: int = None,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Get messages with ID > last_message_id, optionally filtered by project.
    Returns empty list if no new messages.
    """
    try:
        query = select(Message).where(Message.id > last_message_id)
        if project_id is not None:
            query = query.where(Message.project_id == project_id)

        messages = (await session.execute(query)).scalars().all()

        return {
            "messages": [{
                "id": m.id,
                "telegram_user_id": m.telegram_user_id,
                "project_id": m.project_id,
                "text": m.text
            } for m in messages]
        }
    except Exception as e:
        raise HTTPException(500, detail=str(e))


# User endpoints

@app.get("/users")
async def get_users(
        project_id: int = None,
        session: AsyncSession = Depends(get_async_session)
):
    """Retrieves active users, optionally filtered by project."""
    users = await get_entities(
        session,
        User,
        {"is_active": True},
        {"project_id": project_id} if project_id else None
    )

    return {
        "users": [{
            "id": u.id,
            "telegram_user_id": u.telegram_user_id,
            "telegram_chat_id": u.telegram_chat_id,
            "project_id": u.project_id,
            "last_message_id": u.last_message_id
        } for u in users]
    }
@app.post("/users")
async def create_user(
        user: UserCreate,
        session: AsyncSession = Depends(get_async_session)
):
    """Creates new user."""
    db_user = await create_entity(session, User, user, ERROR_MESSAGES)
    return {
        "id": db_user.id,
        "telegram_user_id": db_user.telegram_user_id,
        "telegram_chat_id": db_user.telegram_chat_id,
        "project_id": db_user.project_id,
    }


@app.get("/users/{telegram_chat_id}")
async def get_user(
    telegram_chat_id: str,
    project_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    """Retrieves user by telegram_chat_id and project_id."""
    return await get_entity(
        session,
        User,
        telegram_chat_id,
        "telegram_chat_id",
        {"project_id": project_id}
    )

@app.patch("/users/{telegram_chat_id}")
async def update_user(
            telegram_chat_id: str,
            project_id: int,
            update_data: UserUpdate,
            session: AsyncSession = Depends(get_async_session)
    ):
        """Updates user data."""
        return await update_entity(
            session,
            User,
            telegram_chat_id,
            update_data,
            "telegram_chat_id",
            {"project_id": project_id})


# Masters endpoints
@app.post("/masters")
async def create_master(
    master: MasterCreate,
    session: AsyncSession = Depends(get_async_session)
):
    """Creates new master."""
    db_master = await create_entity(session, Master, master, ERROR_MESSAGES)
    return {
        "id": db_master.id,
        "telegram_user_id": db_master.telegram_user_id,
        "telegram_chat_id": db_master.telegram_chat_id,
        "project_id": db_master.project_id,
    }
@app.get("/masters/{telegram_user_id}")
async def get_master(
        telegram_user_id: str,
        session: AsyncSession = Depends(get_async_session)
):
    """Retrieves master by telegram_user_id."""
    master = await get_entity(
        session,
        Master,
        telegram_user_id,
        "telegram_user_id"
    )
    return {
        "id": master.id,
        "telegram_user_id": master.telegram_user_id,
        "telegram_chat_id": master.telegram_chat_id,
        "project_id": master.project_id
    }


@app.patch("/masters/{telegram_user_id}")
async def update_master(
        telegram_user_id: str,
        update_data: MasterUpdate,
        session: AsyncSession = Depends(get_async_session)
):
    """Updates master's data."""
    return await update_entity(
        session,
        Master,
        telegram_user_id,
        update_data,
        "telegram_user_id"
    )


@app.get("/masters")
async def get_masters(
        project_id: int = None,
        session: AsyncSession = Depends(get_async_session)
):
    """Retrieves active masters, optionally filtered by project."""
    masters = await get_entities(
        session,
        Master,
        {"is_active": True},
        {"project_id": project_id} if project_id else None
    )

    return {
        "masters": [{
            "id": m.id,
            "telegram_user_id": m.telegram_user_id,
            "telegram_chat_id": m.telegram_chat_id,
            "project_id": m.project_id
        } for m in masters]
    }


# Projects endpoints
@app.get("/projects")
async def get_projects(
        _=Depends(verify_secret_key),
        session: AsyncSession = Depends(get_async_session)
):
    """
    Retrieve all projects (requires secret key)

    Returns:
        List of projects with their tokens and status
    """
    try:
        projects = await session.execute(select(Project))
        return {
            "projects": [{
                "id": p.id,
                "master_token": p.master_token,
                "servant_token": p.servant_token,
                "master_reg_token": p.master_reg_token,
                "servant_reg_token": p.servant_reg_token,
                "is_active": p.is_active
            } for p in projects.scalars()]
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )

@app.post("/projects")
async def create_project(
        project: ProjectCreate,
        _=Depends(verify_secret_key),
        session: AsyncSession = Depends(get_async_session)
):
    """Creates new project (requires secret key)."""
    db_project = await create_entity(session, Project, project, ERROR_MESSAGES)
    return {"id": db_project.id}


@app.patch("/projects/{project_id}")
async def update_project(
        project_id: int,
        update_data: ProjectUpdate,
        _=Depends(verify_secret_key),
        session: AsyncSession = Depends(get_async_session)
):
    """Updates project data (requires secret key)."""
    return await update_entity(
        session,
        Project,
        project_id,
        update_data
    )


@app.delete("/projects/{project_id}")
async def delete_project(
        project_id: int,
        _=Depends(verify_secret_key),
        session: AsyncSession = Depends(get_async_session)
):
    """Marks project as inactive (requires secret key)."""
    project = await get_entity(session, Project, project_id)
    project.is_active = False
    await session.commit()
    return {"status": "project deactivated"}

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
