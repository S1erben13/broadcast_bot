import logging
import httpx
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.client.bot import DefaultBotProperties
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from config import TOKEN, API_BASE_URL, BUTTONS, MESSAGES
from models import Message

logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

async def get_new_messages(last_message_id: int):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{API_BASE_URL}/messages")
            response.raise_for_status()
            messages = response.json().get("messages", [])
            return [msg for msg in messages if msg["id"] > last_message_id]
        except httpx.HTTPError as e:
            logging.error(f"Ошибка при получении сообщений с сервера: {e}")
            return []

async def update_last_message_got(chat_id: str, last_message_id: int):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.patch(
                f"{API_BASE_URL}/users/{chat_id}",
                json={"last_message_got": last_message_id}
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            logging.error(f"Ошибка при обновлении last_message_got: {e}")

async def check_for_new_messages():
    while True:
        try:
            followers = await get_followers_from_api()
            for user in followers:
                if user.get("is_deleted", False):
                    continue

                messages = await get_new_messages(user.get("last_message_got", 0))
                for message in messages:
                    try:
                        await bot.send_message(user["chat_id"], message["text"])
                        await update_last_message_got(user["chat_id"], message["id"])
                    except Exception as e:
                        logging.error(f"Ошибка при отправке сообщения пользователю {user['chat_id']}: {e}")

            await asyncio.sleep(60)  # Интервал проверки
        except Exception as e:
            logging.error(f"Ошибка в check_for_new_messages: {e}")
            await asyncio.sleep(60)

async def follow_user(user_id: int | str, chat_id: int | str) -> None:
    """
    Отправляет запрос на подписку пользователя.
    Если пользователь уже существует, но был отписан, обновляет его статус.
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{API_BASE_URL}/users/{chat_id}")
            if response.status_code == 200:
                user = response.json()
                if user.get("is_deleted", True):
                    await client.patch(
                        f"{API_BASE_URL}/users/{chat_id}",
                        json={"is_deleted": False}
                    )
                    logging.info(f"Пользователь {chat_id} снова подписан.")
                    return  # Возвращаемся, чтобы не вызывать повторную подписку
                else:
                    logging.warning(f"Пользователь {chat_id} уже подписан.")
                    raise Exception("Chat ID already exists")

            # Если пользователь не существует, создаем нового
            response = await client.post(
                f"{API_BASE_URL}/users",
                json={"user_id": str(user_id), "chat_id": str(chat_id)}
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            error_detail = e.response.json().get("detail", "")
            if "Chat ID already exists" in error_detail:
                logging.warning(f"Chat ID already exists: {error_detail}")
            else:
                logging.error(f"Ошибка при отправке пользователя в api: {error_detail}")
            raise
        except httpx.HTTPError as e:
            logging.error(f"Ошибка при отправке пользователя в api: {e}")
            raise

async def unfollow_user(chat_id: str) -> None:
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{API_BASE_URL}/users/{chat_id}")
            if response.status_code == 200:
                user = response.json()
                if user.get("is_deleted", True):
                    logging.warning(f"Пользователь {chat_id} уже отписан.")
                    raise Exception("User already unfollowed")
                else:
                    try:
                        response = await client.patch(
                            f"{API_BASE_URL}/users/{chat_id}",
                            json={"is_deleted": True}
                        )
                        response.raise_for_status()
                    except httpx.HTTPError as e:
                        logging.error(f"Ошибка при отписке: {e}")
                        raise
        except httpx.HTTPStatusError as e:
            error_detail = e.response.json().get("detail", "")
            logging.error(f"Ошибка при отписке: {error_detail}")
            raise
        except httpx.HTTPError as e:
            logging.error(f"Ошибка при отписке: {e}")
            raise

async def get_followers_from_api():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{API_BASE_URL}/users")  
            response.raise_for_status()
            followers = response.json()['users']
            return followers
        except httpx.HTTPError as e:
            logging.error(f"Ошибка при получении пользователей с api: {e}")

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BUTTONS["follow"]), KeyboardButton(text=BUTTONS["unfollow"])]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    await message.answer(
        MESSAGES["welcome"],
        reply_markup=keyboard,
    )

@dp.message(Command("follow"))
async def cmd_follow(message: types.Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    try:
        await follow_user(chat_id, user_id)
        await message.answer(MESSAGES["subscribed"])  # Уведомление о подписке
    except Exception as e:
        if "Chat ID already exists" in str(e):
            await message.answer(MESSAGES["already_subscribed"])  # Уже подписан
        else:
            await message.answer(MESSAGES["subscription_error"])

@dp.message(Command("unfollow"))
async def cmd_unfollow(message: types.Message):
    chat_id = str(message.chat.id)
    try:
        await unfollow_user(chat_id)
        await message.answer(MESSAGES["unsubscribed"])
    except httpx.HTTPStatusError as e:
        error_detail = e.response.json().get("detail", "")
        if "User not found" in error_detail:
            await message.answer(MESSAGES["not_subscribed"])  
        else:
            await message.answer(MESSAGES["unsubscription_error"])  
    except httpx.HTTPError as e:
        await message.answer(MESSAGES["unsubscription_error"])
    except Exception as e:
        if "User already unfollowed" in str(e):
            await message.answer(MESSAGES["already_unsubscribed"])

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
    asyncio.create_task(check_for_new_messages())
    await dp.start_polling(bot)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())