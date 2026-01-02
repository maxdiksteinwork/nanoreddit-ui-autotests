from __future__ import annotations

import pytest

from ui.pages.create_post_page import CreatePostPage
from ui.pages.home_page import HomePage
from ui.pages.login_page import LoginPage
from ui.pages.post_page import PostPage
from ui.pages.register_page import RegisterPage


@pytest.fixture
def home_page(page) -> HomePage:
    return HomePage(page)


@pytest.fixture
def register_page(page) -> RegisterPage:
    return RegisterPage(page)


@pytest.fixture
def login_page(page) -> LoginPage:
    return LoginPage(page)


@pytest.fixture
def create_post_page(page) -> CreatePostPage:
    return CreatePostPage(page)


@pytest.fixture
def post_page(page) -> PostPage:
    return PostPage(page)
