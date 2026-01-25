import asyncio

import pytest
import pytest_asyncio
from playwright.async_api import BrowserContext

from models.auth_dto import RegisterUserDTO
from ui.pages.home_page import HomePage
from utils.clients.api_client import ApiClient
from utils.database.database_helpers import delete_user_by_email, fetch_single_user


@pytest.fixture
def user_api_created(session_api_client: ApiClient) -> RegisterUserDTO:
    user = RegisterUserDTO.random()
    session_api_client.register_user(
        email=user.email,
        username=user.username,
        password=user.password,
    )
    return user


@pytest.fixture
def make_authenticated_user_with_home_page(
    session_api_client: ApiClient,
    make_page,
):
    """фабрика для создания авторизованного пользователя с его home_page"""

    async def _create_user_with_pages() -> tuple[RegisterUserDTO, HomePage, BrowserContext]:
        user = RegisterUserDTO.random()
        session_api_client.register_user(
            email=user.email,
            username=user.username,
            password=user.password,
        )
        home_page = await make_page("home", user=user)
        return user, home_page, home_page.page.context

    return _create_user_with_pages


@pytest_asyncio.fixture
async def db_user_api_created(session_sql_client, user_api_created: RegisterUserDTO) -> dict:
    return await asyncio.to_thread(
        fetch_single_user,
        session_sql_client,
        user_api_created.email,
        columns="id::text, email, username, role",
    )


@pytest_asyncio.fixture
async def minimal_user_db_clean(session_sql_client) -> RegisterUserDTO:
    user = RegisterUserDTO.minimal()
    await delete_user_by_email(session_sql_client, user.email)
    yield user
    await delete_user_by_email(session_sql_client, user.email)


@pytest_asyncio.fixture
async def invalid_email_user_db_clean(session_sql_client, invalid_email: str) -> RegisterUserDTO:
    user = RegisterUserDTO.random()
    user.email = invalid_email
    yield user
    await delete_user_by_email(session_sql_client, user.email)
