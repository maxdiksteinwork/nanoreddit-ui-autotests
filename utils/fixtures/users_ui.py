import pytest
from playwright.async_api import BrowserContext

from models.auth_dto import RegisterUserDTO
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
