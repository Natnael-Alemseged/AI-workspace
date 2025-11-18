# Alembic Database Migrations

This directory contains database migration scripts managed by Alembic.

## 📋 Current Status

✅ **Database:** Neon PostgreSQL  
✅ **Current Revision:** `ad5888aad145` (merge point)  
✅ **Migration Branches:** Merged

## 🔧 Common Commands

### Check Current Version
```bash
alembic current
```

### View Migration History
```bash
alembic history
```

### View All Heads
```bash
alembic heads
```

### Upgrade to Latest
```bash
alembic upgrade head
```

### Downgrade One Revision
```bash
alembic downgrade -1
```

### Create New Migration
```bash
# Auto-generate from model changes
alembic revision --autogenerate -m "description of changes"

# Empty migration (for data migrations)
alembic revision -m "description"
```

## 📚 Migration History

1. **4166023639f2** - Initial schema with all tables
2. **d949d1629252** - Make hashed_password nullable for OAuth
3. **add_channels_topics** - Add channels and topics system
4. **chat_tables_001** - Add chat tables (branched from d949d1629252)
5. **seed_initial_admin** - Seed initial admin user (branched from add_channels_topics)
6. **ad5888aad145** - **Merge migration** (merged chat and admin branches)

## ⚠️ Important Notes

### Multiple Heads Issue (RESOLVED)

Previously, there were two migration heads:
- `chat_tables_001` (chat feature branch)
- `seed_initial_admin` (admin seeding branch)

**Resolution:** Created merge migration `ad5888aad145` to unify the branches.

### Fresh Database Setup

For a fresh Neon PostgreSQL database:

```bash
# Upgrade to latest
alembic upgrade head
```

### Existing Database with Data

If your database already has tables but no alembic version:

```bash
# Stamp at current revision (marks as migrated without running migrations)
alembic stamp head
```

### Creating New Migrations

Always check for multiple heads before creating new migrations:

```bash
# Check heads
alembic heads

# If multiple heads exist, merge them first
alembic merge -m "merge branches" head1_id head2_id

# Then create your migration
alembic revision --autogenerate -m "your changes"
```

## 🗂️ Migration Files

Located in `alembic/versions/`:

- `4166023639f2_*.py` - Initial schema
- `d949d1629252_*.py` - OAuth password changes
- `add_channels_topics_system.py` - Channels/topics feature
- `add_chat_tables.py` - Chat feature
- `seed_initial_admin.py` - Admin user seeding
- `ad5888aad145_*.py` - Merge migration

## 🔍 Troubleshooting

### "Multiple head revisions" Error

```bash
# List all heads
alembic heads

# Merge them
alembic merge -m "merge description" head1 head2

# Upgrade
alembic upgrade head
```

### "Type already exists" Error

This means the database has existing objects. Either:

1. **Drop and recreate** (development only):
   ```sql
   DROP SCHEMA public CASCADE;
   CREATE SCHEMA public;
   ```

2. **Stamp at current revision**:
   ```bash
   alembic stamp head
   ```

### Check What Will Be Applied

```bash
# Show SQL without executing
alembic upgrade head --sql
```

## 📝 Best Practices

1. **Always check current state** before creating migrations
2. **Review auto-generated migrations** - they may need manual adjustments
3. **Test migrations** on development database first
4. **Backup production** before running migrations
5. **Never edit applied migrations** - create new ones instead
6. **Keep migrations small** and focused on single changes

## 🔗 Related Documentation

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [Database Configuration](../docs/operations/)
- [Admin Seeding Guide](../docs/operations/ADMIN_SEEDING_GUIDE.md)
