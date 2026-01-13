from __future__ import annotations

import allure
from playwright.async_api import Page, expect

from ui.page_factory.button import Button
from ui.page_factory.text import Text


class UserProfileModal:
    SECTION = "User profile modal"
    TITLE = "Информация о пользователе"
    FIELD_LOCATOR = "p"

    def __init__(self, page: Page) -> None:
        self.dialog = page.get_by_role("dialog").filter(has_text=self.TITLE).first
        self.close_button = Button(
            page,
            locator=self.dialog.get_by_role("button").first,
            name="Close profile modal",
            section=self.SECTION,
        )
        self.id_field = Text(
            page,
            locator=self._field_locator("ID"),
            name="User ID",
            section=self.SECTION,
        )
        self.email_field = Text(
            page,
            locator=self._field_locator("Email"),
            name="User email",
            section=self.SECTION,
        )
        self.username_field = Text(
            page,
            locator=self._field_locator("Имя пользователя"),
            name="Username",
            section=self.SECTION,
        )
        self.role_field = Text(
            page,
            locator=self._field_locator("Роль"),
            name="User role",
            section=self.SECTION,
        )
        self.banned_until_field = Text(
            page,
            locator=self._field_locator("Заблокирован до"),
            name="Banned until",
            section=self.SECTION,
        )

    def _field_locator(self, label: str):
        return self.dialog.locator(self.FIELD_LOCATOR).filter(has_text=f"{label}:")

    async def should_be_visible(self) -> None:
        with allure.step("Ensure user profile modal is visible"):
            await expect(self.dialog).to_be_visible()

    async def close(self) -> None:
        await self.close_button.click()
        await expect(self.dialog).to_be_hidden()

    async def should_show_id(self, value: str | int) -> None:
        await self.id_field.should_contain_text(str(value))

    async def should_show_email(self, email: str) -> None:
        await self.email_field.should_contain_text(email)

    async def should_show_username(self, username: str) -> None:
        await self.username_field.should_contain_text(username)

    async def should_show_role(self, role: str) -> None:
        await self.role_field.should_contain_text(role)

    async def should_show_banned_until(self, value: str) -> None:
        await self.banned_until_field.should_contain_text(value)
