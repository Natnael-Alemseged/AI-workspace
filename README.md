# AI Workspace — Intent-Driven Agent Backend

A production-ready FastAPI backend that turns natural language into action. Users connect their tools (Gmail, Google Drive, Docs, web search), then direct AI agents inline — inside channels, topics, and DMs — using `@mentions`. The system handles routing, tool execution, and response delivery automatically.

> **"Email every user in this Google Sheet saying X"** — that's the kind of task this backend is built for.

---

## What This Is

AI Workspace is the infrastructure layer for community-style collaboration powered by AI agents. It's not a chatbot. It's a full workspace backend where:

- Humans and AI agents coexist in the same channels and conversations
- Users invoke agents inline with `@emailAi`, `@searchAi`, or `@generalAi`
- Agents have access to the user's connected services and act on their behalf
- Every tool call, response, and action is logged, stored, and retrievable
- Real-time delivery is handled via Socket.IO — no polling

The design pattern: **intent in a message → agent detection → tool execution → response delivered back into the thread.**

---

## Core Capabilities

### Intent-Driven Agent Routing

Mention an agent anywhere in a message. The system extracts the intent and routes it:

```
@emailAi draft a follow-up to everyone who opened last week's campaign
@searchAi find the latest pricing data for enterprise SaaS tools
@generalAi summarize the attachments I shared in Drive and create a doc
```

The agent determines which tools to call, executes them, and posts the result back as a reply from the bot user — all asynchronously, without blocking the thread.

### Connected Toolkits (via Composio)

| Service | What Agents Can Do |
|---|---|
| **Gmail** | Send, search, fetch, draft, label emails |
| **Google Drive** | Upload, download, organize, share files |
| **Google Docs** | Create, read, update documents |
| **Web Search** | Live search results via SerpAPI |

When a user tries to invoke a service they haven't connected yet, the system triggers a permission/connection flow automatically.

### Three Specialized Agents

| Agent | Trigger | Toolset |
|---|---|---|
| Email AI | `@emailAi` | Gmail only |
| Search AI | `@searchAi` | Web search only |
| General AI | `@generalAi` or default | All connected tools |

Each agent is a first-class user in the system — with its own ID, avatar, and message history. Responses appear as messages from the bot within the same thread.

### Long-Term Memory (Supermemory)

Agents maintain persistent memory across sessions. Relevant context is retrieved at inference time, so agents remember user preferences, prior decisions, and ongoing work without needing to re-explain.

### Workspace Structure

```
Workspace
├── Channels          (e.g., Design, Engineering, Client Success)
│   └── Topics        (focused discussions within a channel)
│       └── Messages  (with @agent support, reactions, replies, attachments)
├── Group Chats       (with AI bots auto-added as members)
└── Direct Messages   (1-on-1, supports media and attachments)
```

---

## Architecture

```
Client (Web/Mobile)
        │
        ├── REST API (FastAPI)
        └── Socket.IO (real-time events)
                │
        ┌───────┴───────────────────────────────┐
        │          Service Layer                 │
        │  AgentService · ChatService            │
        │  TopicService · DirectMessageService   │
        │  ComposioService · SocketIOService     │
        └───────────────────────────────────────┘
                │
        ┌───────┴───────────────────────────────┐
        │         Data & Infrastructure         │
        │  PostgreSQL (async SQLAlchemy)         │
        │  Supabase S3 (media storage)           │
        │  Firebase (push notifications)         │
        │  Redis (optional caching)              │
        └───────────────────────────────────────┘
                │
        ┌───────┴───────────────────────────────┐
        │         External Integrations         │
        │  Composio · Supermemory               │
        │  Groq / OpenAI (LLM)                  │
        │  LlamaIndex (agent orchestration)      │
        └───────────────────────────────────────┘
```

### Agent Execution Flow

```
1. User posts message with @mention
2. Parser extracts: agent_type + prompt
3. Background task queued (response is non-blocking)
4. Agent fetches user's connected tools from Composio
5. LlamaIndex FunctionAgent reasons and calls tools
6. Result stored as a reply from the bot user
7. Socket.IO broadcasts updated thread to all members
```

---

## API Surface

### Messaging

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/topics/{id}/messages` | Post message (agent detection included) |
| `GET` | `/api/topics/{id}/messages` | Paginated message history |
| `POST` | `/api/chat/messages` | Chat room message |
| `POST` | `/api/direct-messages/` | Send DM |

### AI

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/ai/` | Direct AI invocation with conversation history |

### Workspace Structure

| Method | Endpoint | Description |
|---|---|---|
| `POST/GET` | `/api/channels/` | Channels |
| `POST/GET` | `/api/topics/` | Topics within channels |
| `POST/GET` | `/api/chat/rooms` | Group chat rooms |

### Auth

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/auth/register` | Register |
| `POST` | `/api/auth/login` | Login (JWT) |
| `GET` | `/api/auth/google/login` | Google OAuth |

### Socket.IO Events

**Incoming:** `join_room`, `send_message`, `typing`, `mark_as_read`, `message_edited`, `message_deleted`

**Outgoing:** `new_message`, `user_typing`, `messages_read`, `message_edited`, `message_deleted`, `user_joined`, `user_left`

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI + Python 3.12+ |
| Real-time | Socket.IO |
| Database | PostgreSQL (async SQLAlchemy + asyncpg) |
| Migrations | Alembic |
| AI Orchestration | LlamaIndex FunctionAgent |
| LLM Providers | Groq, OpenAI |
| Tool Calling | Composio (Gmail, Drive, Docs, Search) |
| Memory | Supermemory |
| Storage | Supabase S3 (via boto3) |
| Auth | JWT + Google OAuth (fastapi-users) |
| Notifications | Firebase Cloud Messaging + Web Push |
| Caching | Redis (optional) |
| Deployment | Docker + docker-compose, Mangum (AWS Lambda) |

---

## Quick Start

### 1. Install

```bash
git clone <repository-url>
cd AI-workspace

# With Poetry (recommended)
poetry install

# Or pip
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
```

Key variables to set:

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/ai_workspace

# Auth
SECRET_KEY=your-secret-key
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...

# LLM
GROQ_API_KEY=...
OPENAI_API_KEY=...

# Tool Calling
COMPOSIO_API_KEY=...

# Memory
SUPERMEMORY_API_KEY=...

# Storage
SUPABASE_URL=...
SUPABASE_KEY=...
SUPABASE_S3_ACCESS_KEY_ID=...
SUPABASE_S3_SECRET_ACCESS_KEY=...
SUPABASE_S3_ENDPOINT_URL=...

# Notifications
FIREBASE_SERVICE_ACCOUNT_KEY_PATH=/path/to/firebase-key.json
```

### 3. Set Up Database

```bash
alembic upgrade head
```

### 4. Run

```bash
# Development
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or
make run
```

### 5. Docker

```bash
docker-compose up -d
```

---

## Permissions Model

- **JWT-based** auth for REST API and Socket.IO connections
- **Role-based**: `admin` and `user` roles
- **Message-level**: users can only edit/delete their own messages (admins can override)
- **Topic membership**: access gated by membership
- **Bot users**: AI agents are first-class users with fixed UUIDs, auto-added to group chats
- **User approval**: optional `is_approved` gate before access is granted

---

## Documentation

- [Quick Setup Guide](docs/QUICK_SETUP_GUIDE.md)
- [Frontend Implementation Guide](docs/FRONTEND_IMPLEMENTATION_GUIDE.md)
- [Direct Messaging](docs/DIRECT_MESSAGING_IMPLEMENTATION.md)
- [Notifications](docs/NOTIFICATIONS_IMPLEMENTATION_SUMMARY.md)
