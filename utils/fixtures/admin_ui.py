from __future__ import annotations

from typing import Awaitable, Callable

import pytest

from models.auth_dto import RegisterUserDTO
from ui.pages.home_page import HomePage
from ui.pages.post_page import PostPage
from ui.widgets.profile.admin_user_modal import AdminUserModal
from utils.clients.api_client import ApiClient
from utils.clients.sql_client import SQLClient


@pytest.fixture
def make_admin_api_created(
    session_api_client: ApiClient, session_sql_client: SQLClient
) -> Callable[[RegisterUserDTO | None], RegisterUserDTO]:
    def _create_admin(user: RegisterUserDTO | None = None) -> RegisterUserDTO:
        if user is None:
            admin = RegisterUserDTO.random()
            session_api_client.register_user(
                email=admin.email,
                username=admin.username,
                password=admin.password,
            )
        else:
            admin = user

        session_sql_client.execute(
            "UPDATE users SET role = 'ADMIN' WHERE email = %s",
            (admin.email,),
        )
        return admin

    return _create_admin


@pytest.fixture
def admin_api_created(make_admin_api_created) -> RegisterUserDTO:
    return make_admin_api_created()


@pytest.fixture
def banned_user_api_created(
    session_api_client: ApiClient, admin_api_created: RegisterUserDTO
) -> RegisterUserDTO:
    user = RegisterUserDTO.random()
    session_api_client.register_user(
        email=user.email,
        username=user.username,
        password=user.password,
    )
    token = session_api_client.login_and_get_token(
        email=admin_api_created.email, password=admin_api_created.password
    )
    session_api_client.ban_user(email=user.email, seconds=3600, token=token)
    return user


@pytest.fixture
def make_post_via_api_and_open_author_modal(
    make_post_api_created,
    admin_api_created: RegisterUserDTO,
    make_page,
    open_author_modal,
) -> Callable[[RegisterUserDTO], Awaitable[tuple[PostPage, AdminUserModal]]]:
    async def _create_and_open(target: RegisterUserDTO) -> tuple[PostPage, AdminUserModal]:
        created_post = await make_post_api_created(email=target.email, password=target.password)
        home_page: HomePage = await make_page("home", user=admin_api_created)
        await home_page.open()
        post_page = await home_page.open_post(title=created_post.title)
        modal = await open_author_modal(post_page)
        return post_page, modal

    return _create_and_open


@pytest.fixture
def open_author_modal() -> Callable[[PostPage], Awaitable[AdminUserModal]]:
    async def _open(post_page: PostPage) -> AdminUserModal:
        await post_page.post.author.open_profile()
        modal = AdminUserModal(post_page.page)
        return modal

    return _open
