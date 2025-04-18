import asyncio
import logging
from typing import Dict, Any, List, Optional

import httpx
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.client.bot import DefaultBotProperties
from aiogram.filters import Command

from config import API_URL, MESSAGES, HTTP_TIMEOUT, TOKENS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def fetch_data(url: str, method: str = "GET", json: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Sends a request to the API and returns the response.

    Args:
        url (str): The API endpoint URL.
        method (str): The HTTP method (GET, POST, PATCH, etc.).
        json (Optional[Dict[str, Any]]): The JSON payload for the request.

    Returns:
        Dict[str, Any]: The API response or an error dictionary.
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(method, url, json=json, timeout=HTTP_TIMEOUT)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"API error ({url}): {e}")
            return {"error": str(e)}


async def get_masters() -> List[Dict[str, Any]]:
    """
    Retrieves a list of masters from the API.

    Returns:
        List[Dict[str, Any]]: A list of master data. Returns an empty list if there's an API error.
    """
    data = await fetch_data(f"{API_URL}masters")
    return data.get("masters", [])


async def is_master(telegram_user_id: int) -> bool:
    """
    Checks if a user is a master.

    Args:
        telegram_user_id (int): The ID of the user to check.

    Returns:
        bool: True if the user is a master, False otherwise.
    """
    masters = await get_masters()
    return any(int(telegram_user_id) == int(master.get("telegram_user_id")) for master in masters)


async def send_message_to_api(telegram_user_id: str, project_id: int, text: str) -> Optional[Dict[str, Any]]:
    """
    Sends a message to the API.

    Args:
        telegram_user_id (str): The ID of the message author.
        text (str): The text of the message.

    Returns:
        Optional[Dict[str, Any]]: The API response as a dictionary, or None if an error occurs.
    """
    return await fetch_data(f"{API_URL}messages", method="POST", json={"telegram_user_id": telegram_user_id, "project_id": project_id, "text": text})

async def start_bot(tokens: tuple):
    bot_id, bot_token, master_reg_token = tokens
    bot = Bot(token=bot_token)
    dp = Dispatcher()

    @dp.message(Command("register"))
    async def register_master(message: types.Message):
        """
        Handles the /register command to register a new master.
        """
        telegram_user_id = str(message.from_user.id)
        telegram_chat_id = str(message.chat.id)

        # Check if the token is provided
        try:
            _, token = message.text.split()
        except ValueError:
            await message.answer("Invalid format. Use /register <token>")
            return

        # Validate the token
        if token != master_reg_token:
            await message.answer("Invalid token.")
            return

        # Send a request to the API to create a new master
        api_response = await fetch_data(
            f"{API_URL}masters",
            method="POST",
            json={"telegram_user_id": telegram_user_id, "telegram_chat_id": telegram_chat_id, "project_id": bot_id}
        )

        # Handle API response
        if api_response and "error" in api_response:
            await message.answer(f"Error registering master: {api_response['error']}")
        else:
            await message.answer(MESSAGES["master_activated"])

    @dp.message()
    async def handle_message(message: types.Message):
        """
        Handles incoming messages from masters.
        """
        # Ignore commands (messages starting with '/')
        if message.text.startswith('/'):
            await message.answer(MESSAGES["command_error"])
            return

        telegram_user_id = str(message.from_user.id)
        text = message.text

        # Check if the user is a master
        if not await is_master(int(telegram_user_id)):
            await message.answer(MESSAGES["not_master"])
            return

        # Send the message to the API
        api_response = await send_message_to_api(telegram_user_id, bot_id, text)
        if api_response and "error" in api_response:
            response_message = MESSAGES["message_send_error"]
        else:
            response_message = MESSAGES["message_sent"]

        # Send the response back to the user
        await message.answer(response_message)

    await dp.start_polling(bot)


async def main():
    await asyncio.gather(*[start_bot(tokens) for tokens in TOKENS])

if __name__ == "__main__":
    asyncio.run(main())