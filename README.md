# AI Workspace Backend

🚀 **High-performance FastAPI backend for real-time AI agents.** Featuring Socket.IO, Web Push notifications, and advanced tool-calling via Composio & Supermemory.

**AI Workspace** is a production-ready, asynchronous backend engine built with **FastAPI**. It is engineered to power the next generation of real-time applications and AI-driven platforms. By combining the speed of Python’s modern async ecosystem with robust integrations for AI agentic workflows, AI Workspace provides a solid foundation for:

*   **⚡ Real-time Interactivity**: Full-duplex communication via Socket.IO for instant chat and state updates.
*   **🧠 Intelligent Agents**: State-of-the-art tool calling capabilities integrated through **Composio** and long-term context retention using **Supermemory**.
*   **🔔 Omnichannel Notifications**: Native support for **Web Push** and Firebase, ensuring users stay engaged across platforms.
*   **🛡️ Scalable Architecture**: Built with PostgreSQL (SQLAlchemy Async), Alembic migrations, and a modular service-oriented design.

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
 
