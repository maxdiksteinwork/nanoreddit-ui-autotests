from __future__ import annotations

import pytest

from ui.pages.create_post_page import CreatePostPage
from ui.pages.home_page import HomePage
from ui.pages.login_page import LoginPage
from ui.pages.post_page import PostPage
from ui.pages.register_page import RegisterPage


@pytest.fixture
def register_page(page) -> RegisterPage:
    return RegisterPage(page)


@pytest.fixture
def login_page(page) -> LoginPage:
    return LoginPage(page)


@pytest.fixture
def authenticated_home_page(authenticated_page) -> HomePage:
    return HomePage(authenticated_page)


@pytest.fixture
def authenticated_create_post_page(authenticated_page) -> CreatePostPage:
    return CreatePostPage(authenticated_page)


@pytest.fixture
def authenticated_post_page(authenticated_page) -> PostPage:
    return PostPage(authenticated_page)


@pytest.fixture
def admin_authenticated_home_page(admin_authenticated_page) -> HomePage:
    return HomePage(admin_authenticated_page)


@pytest.fixture
def admin_authenticated_create_post_page(admin_authenticated_page) -> CreatePostPage:
    return CreatePostPage(admin_authenticated_page)


@pytest.fixture
def admin_authenticated_post_page(admin_authenticated_page) -> PostPage:
    return PostPage(admin_authenticated_page)


@pytest.fixture
def banned_authenticated_home_page(banned_authenticated_page) -> HomePage:
    return HomePage(banned_authenticated_page)


@pytest.fixture
def banned_authenticated_create_post_page(banned_authenticated_page) -> CreatePostPage:
    return CreatePostPage(banned_authenticated_page)


@pytest.fixture
def banned_authenticated_post_page(banned_authenticated_page) -> PostPage:
    return PostPage(banned_authenticated_page)
