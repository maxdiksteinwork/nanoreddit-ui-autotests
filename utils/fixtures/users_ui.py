import pytest
import pytest_asyncio

from models.auth_dto import LoginUserDTO, RegisterUserDTO
from utils.clients.api_client import ApiClient


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
