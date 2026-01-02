from __future__ import annotations

import allure
from playwright.async_api import Page, expect

from ui.page_factory.button import Button
from ui.page_factory.input import Input
from ui.widgets.profile.user_profile_modal import UserProfileModal


class AdminUserModal(UserProfileModal):
    SECTION = "User profile modal | Admin"
    ADMIN_CONTROLS_LOCATOR = ".admin-controls"
    BAN_DURATION_INPUT_LOCATOR = ".n-input-number input"
    BAN_BUTTON_LOCATOR = "button:has-text('Забанить')"
    UNBAN_BUTTON_LOCATOR = "button:has-text('Разбанить')"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        admin_controls = self.dialog.locator(self.ADMIN_CONTROLS_LOCATOR)
        self.ban_duration_input = Input(
            page,
            locator=admin_controls.locator(self.BAN_DURATION_INPUT_LOCATOR),
            name="Ban duration (seconds)",
            section=self.SECTION,
        )
        self.ban_button = Button(
            page,
            locator=admin_controls.locator(self.BAN_BUTTON_LOCATOR),
            name="Ban user",
            section=self.SECTION,
        )
        self.unban_button = Button(
            page,
            locator=admin_controls.locator(self.UNBAN_BUTTON_LOCATOR),
            name="Unban user",
            section=self.SECTION,
        )

    async def set_ban_duration(self, seconds: int) -> None:
        await self.ban_duration_input.fill(str(seconds), validate_value=True)

    async def ban_user(
        self, seconds: int | None = None, raw_input: str | None = None
    ) -> None:
        if raw_input is not None:
            await self.ban_duration_input.fill(raw_input, validate_value=True)
        elif seconds is not None:
            await self.set_ban_duration(seconds)
        with allure.step("Ban user via admin modal"):
            await expect(self.ban_button.get_locator()).to_be_enabled()
            await self.ban_button.click()

    async def unban_user(self) -> None:
        with allure.step("Unban user via admin modal"):
            await self.unban_button.click()
