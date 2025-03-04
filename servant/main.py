import asyncio
import logging
from typing import List, Dict, Any

import httpx
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.client.bot import DefaultBotProperties
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from config import TOKEN, API_BASE_URL, BUTTONS, MESSAGES, CHECK_MSGS_RATE

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize bot and dispatcher
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()


async def fetch_data(url: str, method: str = "GET", json: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    A generic function to fetch data from the API.

    Args:
        url (str): The API endpoint URL.
        method (str, optional): The HTTP method (GET, POST, PATCH, etc.). Defaults to "GET".
        json (Dict[str, Any], optional): The JSON data to send in the request body. Defaults to None.

    Returns:
        Dict[str, Any]: The JSON response from the API or an error dictionary.
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(method, url, json=json)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"API error ({url}): {e}")
            return {"error": str(e)}

async def get_new_messages(last_message_id: int) -> List[Dict[str, Any]]:
    """
    Retrieves new messages from the API since the last message ID.

    Args:
        last_message_id (int): The ID of the last processed message.

    Returns:
        List[Dict[str, Any]]: A list of new messages.
    """
    data = await fetch_data(f"{API_BASE_URL}/messages?last_message_id={last_message_id}")
    if "error" in data:
        logger.error(f"Failed to fetch new messages: {data['error']}")
        return []
    if not isinstance(data.get("messages"), list):
        logger.error("Invalid response format: 'messages' key is missing or not a list")
        return []
    return data["messages"]


async def update_user(chat_id: str, last_message_id: int) -> bool:
    """
    Updates the last message ID for a user in the database.

    Args:
        chat_id (str): The user's chat ID.
        last_message_id (int): The ID of the last message sent to the user.

    Returns:
        bool: True if the update was successful, False otherwise.
    """
    response = await fetch_data(f"{API_BASE_URL}/users/{chat_id}", method="PATCH", json={"last_message_id": last_message_id})
    return bool(response.get('success', False))


async def get_followers() -> List[Dict[str, Any]]:
    """
    Retrieves a list of followers from the API.

    Returns:
        List[Dict[str, Any]]: A list of follower data.  Returns an empty list if there's an API error.
    """
    data = await fetch_data(f"{API_BASE_URL}/users")
    return data.get("users", [])


async def check_for_new_messages():
    """
    Continuously checks for new messages and sends them to followers.
    Handles potential errors gracefully and includes a sleep timer for rate limiting.
    """
    while True:
        try:
            followers = await get_followers()
            for user in followers:
                if user.get("followed", True):
                    continue
                messages = await get_new_messages(user.get("last_message_id", 0))
                for message in messages:
                    try:
                        await bot.send_message(user["chat_id"], message["text"])
                        # Обновляем last_message_id
                        await update_user(user["chat_id"], message["id"])
                    except Exception as e:
                        logger.error(f"Error sending message to {user['chat_id']}: {e}")
            await asyncio.sleep(CHECK_MSGS_RATE)
        except Exception as e:
            logger.exception(f"Error in check_for_new_messages: {e}")  # Log the full traceback
            await asyncio.sleep(CHECK_MSGS_RATE)


async def handle_user(chat_id: str, user_id: str, action: str) -> str:
    """
    Handles user follow/unfollow requests.

    Args:
        chat_id (str): The user's chat ID.
        user_id (str): The user's ID.
        action (str): Either "follow" or "unfollow".

    Returns:
        str: The appropriate message from MESSAGES based on the action and user status.
    """
    data = await fetch_data(f"{API_BASE_URL}/users/{chat_id}", method="GET")
    if data.get("error"):
        # User not found, create a new entry
        # Получаем ID последнего сообщения
        messages_data = await fetch_data(f"{API_BASE_URL}/messages/last_message_id?last_message_id=0")
        last_message_id = messages_data["messages"][-1]["id"] if messages_data.get("messages") else 0
        # Создаем пользователя с last_message_id
        await fetch_data(f"{API_BASE_URL}/users", method="POST", json={"user_id": user_id, "chat_id": chat_id, "last_message_id": last_message_id})
        return MESSAGES["subscribed"] if action == "follow" else MESSAGES["unsubscribed"]
    elif action == "follow":
        if data.get("followed", False):
            await fetch_data(f"{API_BASE_URL}/users/{chat_id}", method="PATCH", json={"followed": True})
            return MESSAGES["subscribed"]
        else:
            return MESSAGES["already_subscribed"]
    elif action == "unfollow":
        if not data.get("followed", False):
            await fetch_data(f"{API_BASE_URL}/users/{chat_id}", method="PATCH", json={"followed": False})
            return MESSAGES["unsubscribed"]
        else:
            return MESSAGES["already_unsubscribed"]
    return MESSAGES["subscription_error"]


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Handles the /start command."""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=BUTTONS["follow"]), KeyboardButton(text=BUTTONS["unfollow"])]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    await message.answer(MESSAGES["welcome"], reply_markup=keyboard)


@dp.message(Command("follow"))
async def cmd_follow(message: types.Message):
    """Handles the /follow command."""
    await message.answer(await handle_user(str(message.chat.id), str(message.from_user.id), "follow"))


@dp.message(Command("unfollow"))
async def cmd_unfollow(message: types.Message):
    """Handles the /unfollow command."""
    await message.answer(await handle_user(str(message.chat.id), str(message.from_user.id), "unfollow"))


async def main():
    """Starts the bot and runs the message checker in the background."""
    asyncio.create_task(check_for_new_messages())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
