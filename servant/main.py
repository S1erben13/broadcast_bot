import asyncio
import logging
from typing import List, Dict, Any

import httpx
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.client.bot import DefaultBotProperties
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from config import TOKEN, API_BASE_URL, BUTTONS, MESSAGES, CHECK_MSGS_RATE, REG_SERVANT_TOKEN

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize bot and dispatcher
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()


async def fetch_data(url: str, method: str = "GET", json: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Sends a request to the API and returns the response.

    Args:
        url (str): The API endpoint URL.
        method (str): The HTTP method (GET, POST, PATCH, etc.).
        json (Dict[str, Any]): The JSON payload for the request.

    Returns:
        Dict[str, Any]: The API response or an error dictionary.
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(method, url, json=json)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"API error ({url}): {e}")
            return {"error": str(e)}

async def get_new_messages(last_message_id: int | None) -> List[Dict[str, Any]]:
    """
    Fetches new messages from the API.

    Args:
        last_message_id (int | None): The ID of the last message the user has seen.

    Returns:
        List[Dict[str, Any]]: A list of new messages.
    """
    last_message_id = last_message_id if last_message_id is not None else 0
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
    return response.get("status") == "User updated"


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
                if not user.get("is_active", False):
                    continue
                # Передаем last_message_id, если он есть, иначе 0
                last_message_id = user.get("last_message_id", 0)
                messages = await get_new_messages(last_message_id)
                for message in messages:
                    try:
                        await bot.send_message(user["chat_id"], message["text"])
                        # Обновляем last_message_id только после успешной отправки сообщения
                        if await update_user(user["chat_id"], message["id"]):
                            logger.info(f"Updated last_message_id for user {user['chat_id']} to {message['id']}")
                        else:
                            logger.error(f"Failed to update last_message_id for user {user['chat_id']}")
                    except Exception as e:
                        logger.error(f"Error sending message to {user['chat_id']}: {e}")
            await asyncio.sleep(CHECK_MSGS_RATE)
        except Exception as e:
            logger.exception(f"Error in check_for_new_messages: {e}")  # Log the full traceback
            await asyncio.sleep(CHECK_MSGS_RATE)


async def handle_user(chat_id: str, user_id: str, action: str, token: str = None) -> str:
    """
    Handles user follow/unfollow requests.
    Validates the token only on the first interaction (subscription).

    Args:
        chat_id (str): The user's chat ID.
        user_id (str): The user's ID.
        action (str): Either "follow" or "unfollow".
        token (str): The registration token (required only for the first subscription).

    Returns:
        str: The appropriate message from MESSAGES based on the action and user status.
    """
    # Fetch user data from the API
    data = await fetch_data(f"{API_BASE_URL}/users/{chat_id}", method="GET")

    # If the user is not found, it's their first interaction
    if data.get("error"):
        # Validate the token for the first subscription
        if action == "follow" and token != REG_SERVANT_TOKEN:
            return MESSAGES["invalid_token"]

        # Create a new user entry
        messages_data = await fetch_data(f"{API_BASE_URL}/messages")
        last_message_id = messages_data["messages"][-1]["id"] if messages_data.get("messages") else 0
        await fetch_data(
            f"{API_BASE_URL}/users",
            method="POST",
            json={"user_id": user_id, "chat_id": chat_id, "last_message_id": last_message_id}
        )
        return MESSAGES["subscribed"] if action == "follow" else MESSAGES["unsubscribed"]

    # Handle follow/unfollow for existing users
    if action == "follow":
        if not data.get("is_active", False):
            await fetch_data(f"{API_BASE_URL}/users/{chat_id}", method="PATCH", json={"is_active": True})
            return MESSAGES["subscribed"]
        else:
            return MESSAGES["already_subscribed"]
    elif action == "unfollow":
        if data.get("is_active", False):
            await fetch_data(f"{API_BASE_URL}/users/{chat_id}", method="PATCH", json={"is_active": False})
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
    # Extract the token from the message (if provided)
    try:
        _, token = message.text.split()
    except ValueError:
        token = None

    # Pass the token to handle_user
    response = await handle_user(str(message.chat.id), str(message.from_user.id), "follow", token)
    await message.answer(response)


@dp.message(Command("unfollow"))
async def cmd_unfollow(message: types.Message):
    """Handles the /unfollow command."""
    # Unfollow does not require a token
    response = await handle_user(str(message.chat.id), str(message.from_user.id), "unfollow")
    await message.answer(response)


async def main():
    """Starts the bot and runs the message checker in the background."""
    asyncio.create_task(check_for_new_messages())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
