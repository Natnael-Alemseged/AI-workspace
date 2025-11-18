"""Seed AI bot users into the database."""
import asyncio
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import async_engine, AsyncSessionLocal
from app.models.user import User, UserRole


async def create_ai_bots():
    """Create AI bot users if they don't exist."""
    
    ai_bots = [
        {
            "id": "00000000-0000-0000-0000-000000000001",
            "email": "emailai@armada.bot",
            "full_name": "Email AI",
            "role": "user",
            "is_superuser": False,
            "is_active": True,
            "is_verified": True,
            "hashed_password": None  # Bots don't need passwords
        },
        {
            "id": "00000000-0000-0000-0000-000000000002",
            "email": "searchai@armada.bot",
            "full_name": "Search AI",
            "role": "user",
            "is_superuser": False,
            "is_active": True,
            "is_verified": True,
            "hashed_password": None
        },
        {
            "id": "00000000-0000-0000-0000-000000000003",
            "email": "generalai@armada.bot",
            "full_name": "General AI",
            "role": "user",
            "is_superuser": False,
            "is_active": True,
            "is_verified": True,
            "hashed_password": None
        }
    ]
    
    async with AsyncSessionLocal() as session:
        for bot_data in ai_bots:
            # Check if bot already exists
            query = select(User).where(User.email == bot_data["email"])
            result = await session.execute(query)
            existing_bot = result.scalar_one_or_none()
            
            if existing_bot:
                print(f"✓ Bot already exists: {bot_data['full_name']} ({bot_data['email']})")
                continue
            
            # Create bot user
            bot = User(
                id=uuid.UUID(bot_data["id"]),
                email=bot_data["email"],
                full_name=bot_data["full_name"],
                role=bot_data["role"],
                is_superuser=bot_data["is_superuser"],
                is_active=bot_data["is_active"],
                is_verified=bot_data["is_verified"],
                hashed_password=bot_data["hashed_password"]
            )
            session.add(bot)
            print(f"✓ Created bot: {bot_data['full_name']} ({bot_data['email']})")
        
        await session.commit()
        print("\n✅ All AI bots created successfully!")


if __name__ == "__main__":
    print("Creating AI bot users...\n")
    asyncio.run(create_ai_bots())
