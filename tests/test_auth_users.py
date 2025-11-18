import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.db import Base, get_async_session
from app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture
async def client():
    test_engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async def override_get_async_session():
        async with TestingSessionLocal() as session:
            yield session

    app.dependency_overrides[get_async_session] = override_get_async_session

    from core import auth as auth_core
    from core import user_manager as user_manager_core

    original_auth_secret = auth_core.SECRET_KEY
    original_user_secret = user_manager_core.SECRET_KEY
    original_reset_secret = user_manager_core.UserManager.reset_password_token_secret
    original_verify_secret = user_manager_core.UserManager.verification_token_secret

    auth_core.SECRET_KEY = "test-secret"
    user_manager_core.SECRET_KEY = "test-secret"
    user_manager_core.UserManager.reset_password_token_secret = "test-secret"
    user_manager_core.UserManager.verification_token_secret = "test-secret"

    transport = ASGITransport(app=app)

    try:
        async with AsyncClient(transport=transport, base_url="http://test") as async_client:
            yield async_client
    finally:
        app.dependency_overrides.pop(get_async_session, None)
        auth_core.SECRET_KEY = original_auth_secret
        user_manager_core.SECRET_KEY = original_user_secret
        user_manager_core.UserManager.reset_password_token_secret = original_reset_secret
        user_manager_core.UserManager.verification_token_secret = original_verify_secret
        await test_engine.dispose()


@pytest.mark.anyio
async def test_auth_flow_register_login_update_and_logout(client):
    registration_payload = {
        "email": "test.user@example.com",
        "password": "Str0ngPass!",
        "is_active": True,
        "is_superuser": False,
        "is_verified": True,
    }

    register_response = await client.post("/api/auth/register", json=registration_payload)
    assert register_response.status_code == 201
    registered_user = register_response.json()
    assert registered_user["email"] == registration_payload["email"]

    login_response = await client.post(
        "/api/auth/jwt/login",
        data={
            "username": registration_payload["email"],
            "password": registration_payload["password"],
        },
    )
    assert login_response.status_code == 200
    tokens = login_response.json()
    assert tokens["token_type"] == "bearer"
    access_token = tokens["access_token"]

    auth_headers = {"Authorization": f"Bearer {access_token}"}
    me_response = await client.get("/api/users/me", headers=auth_headers)
    assert me_response.status_code == 200
    current_user = me_response.json()
    assert current_user["email"] == registration_payload["email"]

    update_payload = {"email": "updated.user@example.com"}
    update_response = await client.patch(
        "/api/users/me", json=update_payload, headers=auth_headers
    )
    assert update_response.status_code == 200
    updated_user = update_response.json()
    assert updated_user["email"] == update_payload["email"]

    relogin_response = await client.post(
        "/api/auth/jwt/login",
        data={"username": update_payload["email"], "password": registration_payload["password"]},
    )
    assert relogin_response.status_code == 200
    new_access_token = relogin_response.json()["access_token"]

    logout_response = await client.post(
        "/api/auth/jwt/logout",
        headers={"Authorization": f"Bearer {new_access_token}"},
    )
    assert logout_response.status_code == 204


@pytest.mark.anyio
async def test_users_me_requires_authentication(client):
    response = await client.get("/api/users/me")
    assert response.status_code == 401
