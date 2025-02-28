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

async def send_follower_to_api(user_id : int | str, chat_id: int | str) -> None:
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
        except httpx.HTTPError as e:
            logging.error(f"Ошибка при отправке пользователя в api: {e}")

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
async def cmd_follow(message: types.Message,):
    chat_id = message.chat.id
    user_id = message.from_user.id
    # followers = await get_followers_from_api()
    # for user in followers:
    #     print(user)
    #     if chat_id == user['chat_id']:
    #         await message.answer("Вы уже подписаны!")
    #         return
    await send_follower_to_api(chat_id, user_id)
    await message.answer("Вы подписались на рассылку!")

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