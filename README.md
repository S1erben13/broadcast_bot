Broadcasting System
This project is a system for broadcasting anonymous messages via Telegram bots. It consists of four main services: a PostgreSQL database, a FastAPI backend, and two Telegram bots (Master Bot and Servant Bot) built using the aiogram framework.

Key Features
Master Bot:
Allows an authorized user (Master) to send anonymous messages.

Messages are sent to the FastAPI backend, which stores them in the database.

Registration: Masters can register using the /register <token> command, where <token> is a predefined secret token.

Servant Bot:
Users can subscribe or unsubscribe using the /follow and /unfollow commands.

First-time Subscription: Users must provide a valid token when subscribing for the first time using /follow <token>.

Continuously monitors the database for new messages via the FastAPI backend.

Sends new messages to all subscribed users.

If a user resubscribes after unsubscribing, they will receive all messages that were sent during their absence.

Message Broadcasting:
Messages sent through the Master Bot are instantly delivered to all subscribed users via the Servant Bot.

Database Storage:
All messages and user subscriptions are stored in a PostgreSQL database for logging and future reference.

Dockerized:
The entire system is containerized using Docker Compose, making it easy to deploy and scale.

How It Works
Master Bot:
Registration:

A user becomes a Master by sending the /register <token> command to the Master Bot.

The token must match the predefined MASTER_TOKEN in the .env file.

Sending Messages:

Once registered, Masters can send messages, which are forwarded to the FastAPI backend and stored in the database.

Servant Bot:
User Subscription:

Users subscribe to the Servant Bot using the /follow <token> command (required only for the first subscription).

After the first subscription, users can use /follow and /unfollow without a token.

Message Broadcasting:

The Servant Bot continuously checks the database for new messages.

When a new message is found, it is broadcasted to all subscribed users.

Resubscription Handling:

If a user resubscribes after unsubscribing, they will receive all messages that were sent during their absence.

Technologies Used
Telegram Bots:
Built using aiogram (Python framework for Telegram Bot API).

Backend:
FastAPI for handling API requests.

Database:
PostgreSQL for storing messages and user subscriptions.

Containerization:
Docker and Docker Compose for easy deployment and isolation of services.

Environment Management:
.env files for configuration.

API Endpoints
Messages:
POST /messages: Create a new message.

GET /messages: Retrieve messages created after a specific message ID.

Users:
POST /users: Create a new user.

PATCH /users/{chat_id}: Update a user's data.

GET /users/{chat_id}: Retrieve a user by their chat ID.

GET /users: Retrieve all users.

Bot Commands
Master Bot:
/register <token>: Register as a Master. The token must match the MASTER_TOKEN in the .env file.

Servant Bot:
/start: Start the bot and display the subscription options.

/follow <token>: Subscribe to receive messages (token required only for the first subscription).

/follow: Subscribe to receive messages (for users who have already subscribed once).

/unfollow: Unsubscribe from receiving messages.

Docker Setup
The project is fully dockerized, with each service (except the database) based on the same Python environment image. Each service installs its own dependencies, ensuring isolation.

To start the project, run:

bash
Copy
docker-compose up --build
This will start all services, including the database, API, and both bots.

Environment Variables
Master Bot:
MASTER_TOKEN: The secret token required for registering as a Master.

Servant Bot:
SERVANT_REG_TOKEN: The secret token required for the first-time subscription.

Database:
POSTGRES_USER: PostgreSQL username.

POSTGRES_PASSWORD: PostgreSQL password.

POSTGRES_DB: PostgreSQL database name.

API:
API_BASE_URL: The base URL for the FastAPI backend.

Conclusion
This system provides a robust and scalable solution for broadcasting anonymous messages via Telegram. The use of Docker ensures easy deployment and scalability, while the modular design allows for future enhancements. The addition of token-based registration and subscription ensures secure access to the system.
