from __future__ import annotations

import allure
from playwright.async_api import Page

from models.auth_dto import RegisterUserDTO
from ui.pages.base_page import BasePage
from ui.widgets.auth.register_form import RegisterForm


class RegisterPage(BasePage):
    path = "register"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.form = RegisterForm(page)

    async def open(self) -> None:
        await self.visit()

    async def register_user(
        self,
        *,
        email: str,
        username: str,
        password: str,
        password_confirmation: str | None = None,
    ) -> None:
        with allure.step("Submit registration form"):
            await self.form.register(
                email=email,
                username=username,
                password=password,
                password_confirmation=password_confirmation,
            )

    async def register_user_model(self, user: RegisterUserDTO) -> None:
        await self.register_user(
            email=user.email,
            username=user.username,
            password=user.password,
            password_confirmation=user.passwordConfirmation,
        )
