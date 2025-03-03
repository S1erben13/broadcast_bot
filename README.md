# Key Features
## Master Bot:
Allows a single user to send anonymous messages to all subscribed users.

## Servant Bot:
Users can subscribe to receive messages from the Master Bot.

## Message Broadcasting:
Messages sent through the Master Bot are instantly delivered to all subscribed users via the Servant Bot.

## Database Storage:
All messages are stored in a PostgreSQL database for logging and future reference.

## Dockerized:
The entire system is containerized using Docker Compose, making it easy to deploy and scale.

# How It Works
Users subscribe to the Servant Bot to receive messages.

The Master Bot allows an authorized user to send a message.

The message is broadcasted to all subscribed users via the Servant Bot.

The message is also saved in the PostgreSQL database for logging.

# Technologies Used
## Telegram Bots:
Built using aiogram (Python framework for Telegram Bot API).

## Backend:
FastAPI for handling API requests.

## Database:
PostgreSQL for storing messages and user subscriptions.

## Containerization:
Docker and Docker Compose for easy deployment.

## Environment Management:
.env files for configuration.
