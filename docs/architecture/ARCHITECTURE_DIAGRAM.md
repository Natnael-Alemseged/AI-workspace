# System Architecture Diagram

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                             │
├─────────────────────────────────────────────────────────────────┤
│  Web Browser / Mobile App                                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   REST API   │  │  Socket.IO   │  │     Auth     │          │
│  │   Calls      │  │  Connection  │  │   (JWT)      │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
└─────────┼──────────────────┼──────────────────┼──────────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API GATEWAY LAYER                           │
├─────────────────────────────────────────────────────────────────┤
│  FastAPI Application (main.py)                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  CORS Middleware │ Auth Middleware │ Error Handlers      │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Channels   │  │     Chat     │  │     Auth     │          │
│  │   Router     │  │   Router     │  │   Router     │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
└─────────┼──────────────────┼──────────────────┼──────────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                     SERVICE LAYER                                │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Channel    │  │    Topic     │  │   Socket.IO  │          │
│  │   Service    │  │   Service    │  │   Service    │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                  │                  │                  │
│         │  ┌──────────────┐│                  │                  │
│         └─►│ Permissions  ││                  │                  │
│            │   Service    ││                  │                  │
│            └──────────────┘│                  │                  │
└─────────────────────────────┼──────────────────┼──────────────────┘
                              │                  │
                              ▼                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                     DATA ACCESS LAYER                            │
├─────────────────────────────────────────────────────────────────┤
│  SQLAlchemy ORM (Async)                                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Models: User, Channel, Topic, TopicMessage, etc.        │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     DATABASE LAYER                               │
├─────────────────────────────────────────────────────────────────┤
│  PostgreSQL Database                                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │  users   │ │ channels │ │  topics  │ │ messages │          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

## Data Model Relationships

```
┌──────────────┐
│     User     │
│ ─────────────│
│ id           │
│ email        │
│ full_name    │
│ role ◄───────┼──── ADMIN or USER
└──────┬───────┘
       │
       │ creates
       ▼
┌──────────────┐
│   Channel    │
│ ─────────────│
│ id           │
│ name         │
│ description  │
│ icon         │
│ color        │
│ created_by   │
└──────┬───────┘
       │
       │ contains
       ▼
┌──────────────┐
│    Topic     │
│ ─────────────│
│ id           │
│ channel_id   │
│ name         │
│ description  │
│ is_pinned    │
│ created_by   │
└──────┬───────┘
       │
       ├─────────────┐
       │             │
       │ has         │ has
       ▼             ▼
┌──────────────┐  ┌──────────────┐
│ TopicMember  │  │TopicMessage  │
│ ─────────────│  │ ─────────────│
│ id           │  │ id           │
│ topic_id     │  │ topic_id     │
│ user_id      │  │ sender_id    │
│ joined_at    │  │ content      │
│ last_read_at │  │ reply_to_id  │
└──────────────┘  └──────┬───────┘
                         │
                         ├─────────────┐
                         │             │
                         │ has         │ has
                         ▼             ▼
                  ┌──────────────┐  ┌──────────────┐
                  │MessageMention│  │MessageReaction│
                  │ ─────────────│  │ ─────────────│
                  │ id           │  │ id           │
                  │ message_id   │  │ message_id   │
                  │ mentioned_   │  │ user_id      │
                  │   user_id    │  │ emoji        │
                  │ is_read      │  └──────────────┘
                  └──────────────┘
```

## Request Flow: Send Message with Mention

```
┌─────────┐
│ Client  │
└────┬────┘
     │
     │ 1. POST /api/channels/topics/messages
     │    { content: "Hey @john, check this" }
     ▼
┌─────────────────┐
│ Channels Router │
└────┬────────────┘
     │
     │ 2. Validate JWT & Extract User
     ▼
┌─────────────────┐
│  Topic Service  │
└────┬────────────┘
     │
     │ 3. Verify user is topic member
     │ 4. Extract mentions from content
     │ 5. Validate mentioned users
     ▼
┌─────────────────┐
│    Database     │
└────┬────────────┘
     │
     │ 6. Create TopicMessage
     │ 7. Create MessageMention records
     │ 8. Update topic.updated_at
     ▼
┌─────────────────┐
│ Socket.IO Svc   │
└────┬────────────┘
     │
     │ 9. Broadcast to topic room
     │    - new_topic_message
     │ 10. Notify mentioned users
     │    - mentioned
     ▼
┌─────────┐
│ Clients │ ◄── All topic members receive update
└─────────┘
```

## Permission Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    Permission Check Flow                     │
└─────────────────────────────────────────────────────────────┘

User makes request
       │
       ▼
┌──────────────┐
│ Extract JWT  │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Get User     │
│ from DB      │
└──────┬───────┘
       │
       ▼
┌──────────────────┐
│ Check user.role  │
└──────┬───────────┘
       │
       ├─────────────┐
       │             │
       ▼             ▼
   ADMIN          USER
       │             │
       │             │
       ▼             ▼
┌──────────────┐  ┌──────────────┐
│ Can:         │  │ Can:         │
│ - Create     │  │ - View       │
│   channels   │  │   channels   │
│ - Create     │  │ - Send       │
│   topics     │  │   messages   │
│ - Add/remove │  │ - Edit own   │
│   members    │  │   messages   │
│ - Delete any │  │ - Add        │
│   message    │  │   reactions  │
│ - Pin topics │  │ - Mention    │
└──────────────┘  │   members    │
                  └──────────────┘
```

## Socket.IO Event Flow

```
┌─────────────────────────────────────────────────────────────┐
│                  Socket.IO Real-time Flow                    │
└─────────────────────────────────────────────────────────────┘

Client 1                Server                  Client 2
   │                       │                       │
   │ connect(auth: token)  │                       │
   ├──────────────────────►│                       │
   │                       │                       │
   │      connected        │                       │
   │◄──────────────────────┤                       │
   │                       │                       │
   │ join_topic(topic_id)  │                       │
   ├──────────────────────►│                       │
   │                       │                       │
   │    topic_joined       │                       │
   │◄──────────────────────┤                       │
   │                       │                       │
   │                       │  user_joined_topic    │
   │                       ├──────────────────────►│
   │                       │                       │
   │ topic_typing          │                       │
   ├──────────────────────►│                       │
   │                       │                       │
   │                       │  user_typing_topic    │
   │                       ├──────────────────────►│
   │                       │                       │
   │ (REST) POST message   │                       │
   ├──────────────────────►│                       │
   │                       │                       │
   │  new_topic_message    │  new_topic_message    │
   │◄──────────────────────┼──────────────────────►│
   │                       │                       │
   │                       │      mentioned        │
   │                       ├──────────────────────►│
   │                       │   (if @mentioned)     │
   │                       │                       │
```

## Component Interaction: Create Topic

```
┌─────────────────────────────────────────────────────────────┐
│              Admin Creates Topic Flow                        │
└─────────────────────────────────────────────────────────────┘

Admin                                              Users
  │                                                  │
  │ 1. POST /api/channels/topics                    │
  │    { name, channel_id, member_ids }             │
  ▼                                                  │
┌──────────────────┐                                │
│ Channels Router  │                                │
└────┬─────────────┘                                │
     │                                               │
     │ 2. Verify admin role                         │
     ▼                                               │
┌──────────────────┐                                │
│  Topic Service   │                                │
└────┬─────────────┘                                │
     │                                               │
     │ 3. Create topic                              │
     │ 4. Add members                               │
     ▼                                               │
┌──────────────────┐                                │
│    Database      │                                │
└────┬─────────────┘                                │
     │                                               │
     │ 5. Return topic                              │
     ▼                                               │
┌──────────────────┐                                │
│ Socket.IO Svc    │                                │
└────┬─────────────┘                                │
     │                                               │
     │ 6. Emit topic_created                        │
     │    to all members                            │
     └───────────────────────────────────────────►  │
                                                     ▼
                                            ┌──────────────┐
                                            │ Notification │
                                            │ "Added to    │
                                            │  new topic"  │
                                            └──────────────┘
```

## Database Schema Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Database Tables                           │
└─────────────────────────────────────────────────────────────┘

users (existing + role column)
├── id (PK)
├── email (UNIQUE)
├── full_name
├── role (NEW: ADMIN/USER)
└── ...

channels
├── id (PK)
├── name (UNIQUE)
├── description
├── icon
├── color
├── created_by (FK → users.id)
└── timestamps

topics
├── id (PK)
├── channel_id (FK → channels.id)
├── name
├── description
├── is_pinned
├── created_by (FK → users.id)
└── timestamps

topic_members
├── id (PK)
├── topic_id (FK → topics.id)
├── user_id (FK → users.id)
├── joined_at
├── last_read_at
└── is_active

topic_messages
├── id (PK)
├── topic_id (FK → topics.id)
├── sender_id (FK → users.id)
├── content
├── reply_to_id (FK → topic_messages.id)
├── is_edited / edited_at
├── is_deleted / deleted_at
└── created_at

message_mentions
├── id (PK)
├── message_id (FK → topic_messages.id)
├── mentioned_user_id (FK → users.id)
├── is_read
└── created_at

message_reactions
├── id (PK)
├── message_id (FK → topic_messages.id)
├── user_id (FK → users.id)
├── emoji
├── created_at
└── UNIQUE(message_id, user_id, emoji)
```

## API Endpoint Organization

```
/api
├── /channels
│   ├── POST    /                     Create channel (admin)
│   ├── GET     /                     List channels
│   ├── GET     /{id}                 Get channel
│   ├── PATCH   /{id}                 Update channel (admin)
│   ├── DELETE  /{id}                 Delete channel (admin)
│   │
│   ├── GET     /{id}/topics          List channel topics
│   │
│   └── /topics
│       ├── POST    /                 Create topic (admin)
│       ├── GET     /my               List user's topics
│       ├── GET     /{id}             Get topic
│       ├── PATCH   /{id}             Update topic (admin)
│       │
│       ├── POST    /{id}/members/{user_id}    Add member (admin)
│       ├── DELETE  /{id}/members/{user_id}    Remove member (admin)
│       │
│       └── /messages
│           ├── POST    /                      Create message
│           ├── GET     /{topic_id}/messages   List messages
│           ├── PATCH   /{id}                  Edit message
│           ├── DELETE  /{id}                  Delete message
│           │
│           └── /{id}/reactions
│               ├── POST    /                  Add reaction
│               └── DELETE  /{emoji}           Remove reaction
```

## Technology Stack

```
┌─────────────────────────────────────────────────────────────┐
│                    Technology Stack                          │
└─────────────────────────────────────────────────────────────┘

Backend Framework
├── FastAPI (async web framework)
├── Uvicorn (ASGI server)
└── Python 3.9+

Database
├── PostgreSQL (relational database)
├── SQLAlchemy (ORM)
└── Alembic (migrations)

Real-time Communication
├── Socket.IO (WebSocket library)
└── python-socketio (server implementation)

Authentication
├── JWT (JSON Web Tokens)
├── fastapi-users (user management)
└── python-jose (JWT handling)

Data Validation
└── Pydantic (schemas & validation)

Utilities
├── python-dotenv (environment variables)
└── logging (application logging)
```

## Deployment Architecture (Recommended)

```
┌─────────────────────────────────────────────────────────────┐
│                  Production Deployment                       │
└─────────────────────────────────────────────────────────────┘

Internet
   │
   ▼
┌──────────────┐
│   Nginx      │  ◄── SSL/TLS termination
│ (Reverse     │  ◄── Load balancing
│  Proxy)      │  ◄── Static file serving
└──────┬───────┘
       │
       ├─────────────┐
       │             │
       ▼             ▼
┌──────────┐   ┌──────────┐
│ FastAPI  │   │ FastAPI  │  ◄── Multiple instances
│ Instance │   │ Instance │  ◄── for scaling
└────┬─────┘   └────┬─────┘
     │              │
     └──────┬───────┘
            │
            ▼
┌──────────────────┐
│   PostgreSQL     │  ◄── Primary database
│   (Primary)      │
└────┬─────────────┘
     │
     ▼
┌──────────────────┐
│   PostgreSQL     │  ◄── Read replica
│   (Replica)      │      (optional)
└──────────────────┘

Optional:
┌──────────────────┐
│      Redis       │  ◄── Caching
│                  │  ◄── Session storage
└──────────────────┘
```

This architecture provides a comprehensive view of how all components interact in the role-based channels and topics system.
