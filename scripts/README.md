# Scripts Directory

This directory contains utility scripts for database seeding, manual testing, and maintenance tasks.

## 📁 Directory Structure

```
scripts/
├── seeds/              # Database seeding scripts
│   ├── seed_admin.py   # Interactive admin user creation
│   └── seed_admin.sql  # SQL-based admin seeding
│
└── manual_tests/       # Manual testing scripts
    ├── test_chat_feature.py       # Chat feature end-to-end test
    ├── test_gmail.py              # Gmail integration test
    ├── test_search.py             # Search functionality test
    └── verify_search_endpoints.py # Search endpoint verification
```

## 🌱 Seeds

### Admin User Seeding

Create admin users interactively:

```bash
python scripts/seeds/seed_admin.py
```

**Features:**
- Create new admin users
- Promote existing users to admin
- List all admin users
- Seed predefined admins

**Options:**
1. Create new admin user (interactive)
2. Promote existing user to admin
3. List all admin users
4. Seed predefined admins
5. Exit

### SQL Seeding

Alternatively, use SQL directly:

```bash
# PostgreSQL
psql -U your_user -d your_database -f scripts/seeds/seed_admin.sql

# SQLite
sqlite3 app.db < scripts/seeds/seed_admin.sql
```

## 🧪 Manual Tests

These scripts are for manual testing and verification of features. They are not part of the automated test suite.

### Chat Feature Test

Test the complete chat feature flow:

```bash
python scripts/manual_tests/test_chat_feature.py
```

**Tests:**
- User creation
- Direct chat creation
- Message sending
- Message replies
- Message editing
- Read receipts
- Group chat creation
- Room listing

### Gmail Integration Test

Test Gmail integration with Composio:

```bash
python scripts/manual_tests/test_gmail.py
```

**Requirements:**
- `COMPOSIO_API_KEY` in `.env`
- Gmail toolkit configured in Composio
- User authenticated with Gmail

### Search Test

Test web search functionality:

```bash
python scripts/manual_tests/test_search.py
```

**Requirements:**
- `COMPOSIO_API_KEY` in `.env`
- Search toolkit configured in Composio

### Search Endpoints Verification

Verify search API endpoints:

```bash
python scripts/manual_tests/verify_search_endpoints.py
```

**Tests:**
- Search endpoint availability
- Response format validation
- Error handling

## 📝 Notes

### Running Scripts

All scripts should be run from the project root:

```bash
# From project root
python scripts/seeds/seed_admin.py
python scripts/manual_tests/test_chat_feature.py
```

### Environment Variables

Ensure your `.env` file is properly configured:

```env
DATABASE_URL=postgresql://user:pass@localhost/dbname
COMPOSIO_API_KEY=your_composio_key
GROQ_API_KEY=your_groq_key
```

### Database Setup

Before running seed scripts, ensure migrations are up to date:

```bash
alembic upgrade head
```

## 🔧 Adding New Scripts

When adding new scripts:

1. **Seeds** → Place in `scripts/seeds/`
   - Database initialization
   - Data seeding
   - User creation

2. **Manual Tests** → Place in `scripts/manual_tests/`
   - Feature verification
   - Integration testing
   - Endpoint validation

3. **Update this README** with usage instructions

## ⚠️ Important

- **Seeds**: Use with caution in production
- **Manual Tests**: Not for CI/CD, use `pytest` for automated tests
- **Credentials**: Never commit API keys or passwords
- **Database**: Always backup before running seed scripts in production

## 🤝 Related Documentation

- [Admin Seeding Guide](../docs/operations/ADMIN_SEEDING_GUIDE.md)
- [Chat Setup Guide](../docs/guides/CHAT_SETUP_GUIDE.md)
- [Automated Tests](../tests/)
