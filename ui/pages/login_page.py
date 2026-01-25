from __future__ import annotations

import allure
from playwright.async_api import Page

from models.auth_dto import LoginUserDTO
from ui.pages.base_page import BasePage
from ui.widgets.auth.login_form import LoginForm


class LoginPage(BasePage):
    path = "login"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.form = LoginForm(page)

    async def open(self) -> None:
        await self.visit()

    async def login(self, user: LoginUserDTO) -> None:
        with allure.step(f"Attempting to log in as {user.email}"):
            await self.form.login(email=user.email, password=user.password)
            await self.wait_for_path("/")
