import pytest
import pytest_asyncio
from playwright.async_api import BrowserContext

from models.auth_dto import LoginUserDTO, RegisterUserDTO
from ui.pages.home_page import HomePage
from utils.clients.api_client import ApiClient
from utils.fixtures.base_ui import _setup_console_logging


@pytest.fixture
def user_api_created(session_api_client: ApiClient) -> RegisterUserDTO:
    user = RegisterUserDTO.random()
    session_api_client.register_user(
        email=user.email,
        username=user.username,
        password=user.password,
    )
    return user


@pytest_asyncio.fixture
async def user_api_created_ui_authorized(user_api_created, login_page):
    await login_page.open()
    await login_page.login_user_model(LoginUserDTO.from_register(user_api_created))
    return user_api_created


@pytest.fixture
def make_user_api_created_ui_authorized(session_api_client, login_page):
    async def _create_and_login() -> RegisterUserDTO:
        user = RegisterUserDTO.random()
        session_api_client.register_user(
            email=user.email,
            username=user.username,
            password=user.password,
        )
        await login_page.open()
        await login_page.login_user_model(LoginUserDTO.from_register(user))
        return user

    return _create_and_login


@pytest.fixture
def make_authenticated_user_with_home_page(
    session_api_client: ApiClient,
    make_authenticated_context,
):
    """фабрика для создания авторизованного пользователя с его home_page"""

    async def _create_user_with_pages() -> tuple[RegisterUserDTO, HomePage, BrowserContext]:
        user = RegisterUserDTO.random()
        session_api_client.register_user(
            email=user.email,
            username=user.username,
            password=user.password,
        )
        context = await make_authenticated_context(user)
        page = await context.new_page()
        _setup_console_logging(page)
        home_page = HomePage(page)
        return user, home_page, context

    return _create_user_with_pages
