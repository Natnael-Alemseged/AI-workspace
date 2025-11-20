"""Unit test for reaction service logic."""
import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.db import Base
from app.models.channel import MessageReaction, TopicMessage, Topic, TopicMember, Channel
from app.models.user import User
from app.services.topic.topic_reaction_service import TopicReactionService
from uuid import uuid4


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture
async def session():
    """Create a test database session."""
    # Use JSON instead of JSONB for SQLite compatibility
    # We'll exclude tables that use JSONB
    test_engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)

    async with test_engine.begin() as conn:
        # Only create the tables we need for this test
        await conn.run_sync(lambda sync_conn: Base.metadata.create_all(
            sync_conn,
            tables=[
                User.__table__,
                Channel.__table__,
                Topic.__table__,
                TopicMember.__table__,
                TopicMessage.__table__,
                MessageReaction.__table__,
            ]
        ))

    async with TestingSessionLocal() as test_session:
        yield test_session

    await test_engine.dispose()


@pytest.mark.anyio
async def test_single_reaction_per_user_per_message(session):
    """Test that a user can only have one reaction per message."""
    
    # Create test user
    user = User(
        id=uuid4(),
        email="test@example.com",
        hashed_password="hashed",
        is_active=True,
        is_superuser=False,
        is_verified=True
    )
    session.add(user)
    
    # Create channel
    channel = Channel(
        id=uuid4(),
        name="Test Channel",
        description="Test",
        created_by=user.id
    )
    session.add(channel)
    
    # Create topic
    topic = Topic(
        id=uuid4(),
        channel_id=channel.id,
        name="Test Topic",
        description="Test",
        created_by=user.id
    )
    session.add(topic)
    
    # Create topic member
    member = TopicMember(
        topic_id=topic.id,
        user_id=user.id
    )
    session.add(member)
    
    # Create message
    message = TopicMessage(
        id=uuid4(),
        topic_id=topic.id,
        sender_id=user.id,
        content="Test message"
    )
    session.add(message)
    
    await session.commit()
    
    # Add first reaction
    reaction1 = await TopicReactionService.add_reaction(
        session, message.id, user.id, "👍"
    )
    assert reaction1.emoji == "👍"
    
    # Verify only one reaction exists
    query = select(MessageReaction).where(
        MessageReaction.message_id == message.id,
        MessageReaction.user_id == user.id
    )
    result = await session.execute(query)
    reactions = result.scalars().all()
    assert len(reactions) == 1
    assert reactions[0].emoji == "👍"
    
    # Add second reaction (different emoji, same user, same message)
    reaction2 = await TopicReactionService.add_reaction(
        session, message.id, user.id, "👎"
    )
    assert reaction2.emoji == "👎"
    
    # Verify still only one reaction exists and it's the new one
    result = await session.execute(query)
    reactions = result.scalars().all()
    assert len(reactions) == 1, f"Expected 1 reaction, found {len(reactions)}"
    assert reactions[0].emoji == "👎", f"Expected 👎, found {reactions[0].emoji}"
    
    # Verify the reaction IDs are the same (updated, not created new)
    assert reaction1.id == reaction2.id, "Reaction should be updated, not created new"


@pytest.mark.anyio
async def test_same_reaction_twice_returns_existing(session):
    """Test that adding the same reaction twice returns the existing one."""
    
    # Create test user
    user = User(
        id=uuid4(),
        email="test2@example.com",
        hashed_password="hashed",
        is_active=True,
        is_superuser=False,
        is_verified=True
    )
    session.add(user)
    
    # Create channel
    channel = Channel(
        id=uuid4(),
        name="Test Channel",
        description="Test",
        created_by=user.id
    )
    session.add(channel)
    
    # Create topic
    topic = Topic(
        id=uuid4(),
        channel_id=channel.id,
        name="Test Topic",
        description="Test",
        created_by=user.id
    )
    session.add(topic)
    
    # Create topic member
    member = TopicMember(
        topic_id=topic.id,
        user_id=user.id
    )
    session.add(member)
    
    # Create message
    message = TopicMessage(
        id=uuid4(),
        topic_id=topic.id,
        sender_id=user.id,
        content="Test message"
    )
    session.add(message)
    
    await session.commit()
    
    # Add reaction
    reaction1 = await TopicReactionService.add_reaction(
        session, message.id, user.id, "❤️"
    )
    
    # Add same reaction again
    reaction2 = await TopicReactionService.add_reaction(
        session, message.id, user.id, "❤️"
    )
    
    # Should return the same reaction
    assert reaction1.id == reaction2.id
    assert reaction2.emoji == "❤️"
    
    # Verify only one reaction exists
    query = select(MessageReaction).where(
        MessageReaction.message_id == message.id,
        MessageReaction.user_id == user.id
    )
    result = await session.execute(query)
    reactions = result.scalars().all()
    assert len(reactions) == 1
