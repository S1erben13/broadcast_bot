import logging
import httpx
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.client.bot import DefaultBotProperties
from config import TOKEN
from models import Message

logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

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
            # Извлекаем текст ошибки из тела ответа
            error_detail = e.response.json().get("detail", "")
            if "Chat ID already exists" in error_detail:
                logging.warning(f"Chat ID already exists: {error_detail}")
            else:
                logging.error(f"Ошибка при отправке пользователя в api: {error_detail}")
            raise  # Пробрасываем исключение дальше
        except httpx.HTTPError as e:
            logging.error(f"Ошибка при отправке пользователя в api: {e}")
            raise  # Пробрасываем исключение дальше

async def unfollow_user(chat_id: str) -> None:
    """
    Функция для отправки запроса на удаление пользователя.
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.delete(
                f"http://api:8000/users/{chat_id}"
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            error_detail = e.response.json().get("detail", "")
            logging.error(f"Ошибка при отписке: {error_detail}")
            raise
        except httpx.HTTPError as e:
            logging.error(f"Ошибка при отписке: {e}")
            raise

async def get_followers_from_api():
    """
    Функция для получения пользователей с api:8000/users.
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://api:8000/users")
            response.raise_for_status()
            followers = response.json()['users']
            return followers
        except httpx.HTTPError as e:
            logging.error(f"Ошибка при получении пользователей с api: {e}")

@dp.message(Command("follow"))
async def cmd_follow(message: types.Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    try:
        await send_follower_to_api(chat_id, user_id)
        await message.answer("Вы подписались на рассылку!")
    except httpx.HTTPStatusError as e:
        error_detail = e.response.json().get("detail", "")
        if "Chat ID already exists" in error_detail:
            await message.answer("Вы уже подписаны на рассылку!")
        else:
            await message.answer("Произошла ошибка при попытке подписки.")
    except httpx.HTTPError as e:
        await message.answer("Произошла ошибка при попытке подписки.")

@dp.message(Command("unfollow"))
async def cmd_unfollow(message: types.Message):
    chat_id = str(message.chat.id)
    try:
        await unfollow_user(chat_id)
        await message.answer("Вы отписались от рассылки.")
    except httpx.HTTPStatusError as e:
        error_detail = e.response.json().get("detail", "")
        if "User not found" in error_detail:
            await message.answer("Вы не были подписаны на рассылку.")
        else:
            await message.answer("Произошла ошибка при отписке.")
    except httpx.HTTPError as e:
        await message.answer("Произошла ошибка при отписке.")

# Функция для рассылки сообщений подписанным пользователям
async def broadcast_message(message: Message):
    followers = await get_followers_from_api()
    for user in followers:
        try:
            await bot.send_message(user['chat_id'], message.text)
        except Exception as e:
            logging.error(f"Ошибка при отправке сообщения пользователю {user['user_id']}: {e}")
    return {"status": "ok"}

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())