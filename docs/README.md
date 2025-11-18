# Armada Den Documentation

Welcome to the Armada Den backend documentation. This directory contains all guides, feature documentation, operational references, and architecture diagrams.

## 📚 Documentation Structure

### 🚀 [Guides](./guides/)
Step-by-step setup and usage guides:
- **[CHAT_SETUP_GUIDE.md](./guides/CHAT_SETUP_GUIDE.md)** - Setting up the chat feature
- **[QUICK_START_CHANNELS.md](./guides/QUICK_START_CHANNELS.md)** - Quick start guide for channels
- **[SOCKETIO_CLIENT_GUIDE.md](./guides/SOCKETIO_CLIENT_GUIDE.md)** - Socket.IO client integration guide

### ✨ [Features](./features/)
Detailed feature documentation:
- **[AI_AGENT_MENTIONS.md](./AI_AGENT_MENTIONS.md)** - Using @emailAi and @searchAi agents
- **[CHANNELS_TOPICS_FEATURE.md](./features/CHANNELS_TOPICS_FEATURE.md)** - Channels and topics feature overview
- **[CHAT_FEATURE_README.md](./features/CHAT_FEATURE_README.md)** - Chat feature documentation
- **[EMOJI_REACTIONS_GUIDE.md](./features/EMOJI_REACTIONS_GUIDE.md)** - Emoji reactions implementation
- **[MENTIONS_GUIDE.md](./features/MENTIONS_GUIDE.md)** - User mentions in messages

### ⚙️ [Operations](./operations/)
Operational guides and references:
- **[ADMIN_SEEDING_GUIDE.md](./operations/ADMIN_SEEDING_GUIDE.md)** - Creating admin users
- **[IMPLEMENTATION_SUMMARY.md](./operations/IMPLEMENTATION_SUMMARY.md)** - Implementation summary
- **[TOPIC_MEMBER_MANAGEMENT_GUIDE.md](./operations/TOPIC_MEMBER_MANAGEMENT_GUIDE.md)** - Managing topic members

### 🏗️ [Architecture](./architecture/)
System architecture and design:
- **[ARCHITECTURE_DIAGRAM.md](./architecture/ARCHITECTURE_DIAGRAM.md)** - System architecture overview
- **[Product Specification PDF](./architecture/)** - Product specification document

## 🔧 Scripts & Tools

### Seeds
Database seeding scripts are located in `scripts/seeds/`:
- **seed_admin.py** - Interactive admin user creation
- **seed_admin.sql** - SQL-based admin seeding

Usage:
```bash
python scripts/seeds/seed_admin.py
```

### Manual Tests
Manual testing scripts are in `scripts/manual_tests/`:
- **test_chat_feature.py** - End-to-end chat feature test
- **test_gmail.py** - Gmail integration test
- **test_search.py** - Search functionality test
- **verify_search_endpoints.py** - Search endpoint verification

Usage:
```bash
python scripts/manual_tests/test_chat_feature.py
```

## 🧪 Automated Tests

Unit and integration tests are in the `tests/` directory:
```bash
pytest tests/ -v
```

## 📖 Quick Links

### Getting Started
1. [Quick Start Guide](./guides/QUICK_START_CHANNELS.md)
2. [Chat Setup](./guides/CHAT_SETUP_GUIDE.md)
3. [Admin Seeding](./operations/ADMIN_SEEDING_GUIDE.md)

### Feature Documentation
- [AI Agent Mentions](./AI_AGENT_MENTIONS.md) - Use specialized AI agents
- [Channels & Topics](./features/CHANNELS_TOPICS_FEATURE.md)
- [Chat Feature](./features/CHAT_FEATURE_README.md)

### Integration Guides
- [Socket.IO Client](./guides/SOCKETIO_CLIENT_GUIDE.md)
- [User Mentions](./features/MENTIONS_GUIDE.md)
- [Emoji Reactions](./features/EMOJI_REACTIONS_GUIDE.md)

## 🤝 Contributing

When adding new documentation:
1. Place guides in `docs/guides/`
2. Place feature docs in `docs/features/`
3. Place operational docs in `docs/operations/`
4. Place architecture docs in `docs/architecture/`
5. Update this README with links

## 📝 Notes

- All documentation is in Markdown format
- Code examples should be syntax-highlighted
- Include usage examples where applicable
- Keep documentation up-to-date with code changes
