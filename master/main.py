import logging
import httpx
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.client.bot import DefaultBotProperties
from config import TOKEN, API_URL, MESSAGES, HTTP_TIMEOUT, API_RESPONSE_FORMAT

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()


async def send_message_to_api(author_id: str, text: str) -> dict | None:
    """
    Sends a message to the API.

    Args:
        author_id (str): The ID of the message author.
        text (str): The text of the message.

    Returns:
        dict | None: The API response as a dictionary, or None if an error occurs.
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                API_URL,
                json={"author_id": author_id, "text": text},
                timeout=HTTP_TIMEOUT
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logging.error(f"Error sending request to API: {e}")
            return None


@dp.message()
async def handle_message(message: types.Message):
    """
    Handles incoming messages from users.

    Args:
        message (types.Message): The incoming message object.
    """
    author_id = str(message.from_user.id)
    text = message.text

    # Send the message to the API
    api_response = await send_message_to_api(author_id, text)

    if api_response:
        # Format the success message with the API response
        response_message = MESSAGES["message_sent"].format(
            api_response=API_RESPONSE_FORMAT.format(api_response=api_response)
        )
    else:
        # Use the error message if the API request failed
        response_message = MESSAGES["message_send_error"]

    # Send the response back to the user
    await message.answer(response_message)


async def main():
    """
    Starts the bot and begins polling for updates.
    """
    await dp.start_polling(bot)


if __name__ == '__main__':
    import asyncio

    # Run the bot
    asyncio.run(main())