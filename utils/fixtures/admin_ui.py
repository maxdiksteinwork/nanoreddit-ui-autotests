from __future__ import annotations

import pytest

from models.auth_dto import LoginUserDTO, RegisterUserDTO
from ui.pages.post_page import PostPage
from ui.widgets.profile.admin_user_modal import AdminUserModal


@pytest.fixture
def make_admin_api_created(session_api_client, session_sql_client):
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
def banned_user_api_created(session_api_client, admin_api_created) -> LoginUserDTO:
    user = RegisterUserDTO.random()
    session_api_client.register_user(
        email=user.email,
        username=user.username,
        password=user.password,
    )
    login_response = session_api_client.login_user(
        email=admin_api_created.email, password=admin_api_created.password
    )
    token = login_response["responseData"]["jwt"]
    session_api_client.ban_user(email=user.email, seconds=3600, token=token)
    return LoginUserDTO.from_register(user)


@pytest.fixture
async def admin_api_created_ui_authorized(login_page, home_page, admin_api_created):
    await login_page.open()
    await login_page.login_user_model(LoginUserDTO.from_register(admin_api_created))
    await home_page.navbar.should_be_user_nav(email=admin_api_created.email)
    return admin_api_created


@pytest.fixture
def make_post_via_api_and_open_author_modal(
    make_post_api_created, home_page, open_author_modal
):
    async def _create_and_open(target):
        created_post = await make_post_api_created(
            email=target.email, password=target.password
        )
        await home_page.open()
        post_page = await home_page.open_post(title=created_post.title)
        modal = await open_author_modal(post_page)
        return post_page, modal

    return _create_and_open


@pytest.fixture
def open_author_modal():
    async def _open(post_page: PostPage) -> AdminUserModal:
        await post_page.post.author.open_profile()
        modal = AdminUserModal(post_page.page)
        await modal.should_be_visible()
        return modal

    return _open
