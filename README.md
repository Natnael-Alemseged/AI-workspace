# Armada Den Backend

**Armada Den** is a powerful backend API built with **FastAPI**, designed to support real-time applications with features like chat, notifications, and AI bot integration.

## 🚀 Features

- **Authentication**: Secure user authentication and management.
- **Real-time Communication**: 
    - **Socket.IO** integration for live updates.
    - **Push Notifications** via Web Push and Firebase.
- **AI Integration**: 
    - Support for AI bots and chat services.
    - **Tool Calling**: Integration with [Composio](https://composio.ai/) for advanced tool calling capabilities.
    - **Memory**: [Supermemory](https://supermemory.ai/) integration for long-term context and knowledge retrieval.
- **Database**: Async SQLAlchemy with Alembic migrations.

## 🛠️ Tech Stack

- **Framework**: [FastAPI](https://fastapi.tiangolo.com/)
- **Language**: Python 3.12+
- **Database**: PostgreSQL (Async)
- **ORM**: SQLAlchemy
- **Real-time**: Socket.IO, PyWebPush
- **AI/ML**: LlamaIndex, Composio, Supermemory

## 📚 Documentation

Detailed documentation is available in the [`docs/`](docs/) directory:

- **[Quick Setup Guide](docs/QUICK_SETUP_GUIDE.md)**: Get started in 5 minutes.
- **[Frontend Implementation](docs/FRONTEND_IMPLEMENTATION_GUIDE.md)**: Guide for frontend developers.
- **[Direct Messaging](docs/DIRECT_MESSAGING_IMPLEMENTATION.md)**: Implementation details for DM features.
- **[Notifications](docs/NOTIFICATIONS_IMPLEMENTATION_SUMMARY.md)**: How the notification system works.

## 🏁 Quick Start

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd armada-den
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   # OR with Poetry
   poetry install
   ```

3. **Setup Environment**:
   Copy `.env.example` to `.env` and configure your variables.

4. **Run the server**:
   ```bash
   uvicorn app.main:app --reload
   ```

For more details, please refer to the [Quick Setup Guide](docs/QUICK_SETUP_GUIDE.md).

## 🤝 Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct, and the process for submitting pull requests to us.
 