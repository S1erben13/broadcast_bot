# Broadcasting System

This project is a system for broadcasting anonymous messages via Telegram bots. It consists of four main services: a PostgreSQL database, a FastAPI backend, and two Telegram bots (Master Bot and Servant Bot) built using the `aiogram` framework.

## Key Features

### Master Bot:
- Allows an authorized user to send anonymous messages.
- Messages are sent to the FastAPI backend, which stores them in the database.

### Servant Bot:
- Users can subscribe or unsubscribe using the `/follow` and `/unfollow` commands.
- Continuously monitors the database for new messages via the FastAPI backend.
- Sends new messages to all subscribed users.
- If a user resubscribes after unsubscribing, they will receive all messages that were sent during their absence.

### Message Broadcasting:
- Messages sent through the Master Bot are instantly delivered to all subscribed users via the Servant Bot.

### Database Storage:
- All messages and user subscriptions are stored in a PostgreSQL database for logging and future reference.

### Dockerized:
- The entire system is containerized using Docker Compose, making it easy to deploy and scale.

## How It Works

1. **User Subscription:**
   - Users subscribe to the Servant Bot using the `/follow` command.
   - Users can unsubscribe using the `/unfollow` command.

2. **Message Sending:**
   - The Master Bot allows an authorized user to send a message.
   - The message is sent to the FastAPI backend, which stores it in the database.

3. **Message Broadcasting:**
   - The Servant Bot continuously checks the database for new messages.
   - When a new message is found, it is broadcasted to all subscribed users.
   - The message is also saved in the PostgreSQL database for logging.

4. **Resubscription Handling:**
   - If a user resubscribes after unsubscribing, they will receive all messages that were sent during their absence.

## Technologies Used

### Telegram Bots:
- Built using `aiogram` (Python framework for Telegram Bot API).

### Backend:
- FastAPI for handling API requests.

### Database:
- PostgreSQL for storing messages and user subscriptions.

### Containerization:
- Docker and Docker Compose for easy deployment and isolation of services.

### Environment Management:
- `.env` files for configuration.

## API Endpoints

### Messages:
- **POST /messages**: Create a new message.
- **GET /messages**: Retrieve messages created after a specific message ID.

### Users:
- **POST /users**: Create a new user.
- **PATCH /users/{chat_id}**: Update a user's data.
- **GET /users/{chat_id}**: Retrieve a user by their chat ID.
- **GET /users**: Retrieve all users.

## Bot Commands

### Servant Bot:
- **/start**: Start the bot and display the subscription options.
- **/follow**: Subscribe to receive messages.
- **/unfollow**: Unsubscribe from receiving messages.

## Docker Setup

The project is fully dockerized, with each service (except the database) based on the same Python environment image. Each service installs its own dependencies, ensuring isolation.

To start the project, run:

```bash
docker-compose up --build
This will start all services, including the database, API, and both bots.

Conclusion
This system provides a robust and scalable solution for broadcasting anonymous messages via Telegram. The use of Docker ensures easy deployment and scalability, while the modular design allows for future enhancements.
