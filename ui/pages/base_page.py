import re

import allure
from playwright.async_api import Locator, Page, Response, expect

from settings import get_settings
from ui.widgets.navigation.navbar import Navbar


class BasePage:
    path: str | None = None
    TOAST_SELECTOR = ".n-message__content"

    def __init__(self, page: Page) -> None:
        self.page = page
        self.settings = get_settings()
        self.navbar = Navbar(page)

    @property
    def url(self) -> str:
        base = self.settings.base_url.rstrip("/")
        if not self.path:
            return base
        return f"{base}/{self.path.lstrip('/')}"

    async def visit(self) -> Response | None:
        with allure.step(f'Opening page "{self.url}"'):
            return await self.page.goto(
                self.url,
                wait_until="load",
                timeout=15000,
            )

    async def reload(self) -> Response | None:
        with allure.step(f'Reloading page "{self.page.url}"'):
            return await self.page.reload(wait_until="load")

    async def should_have_url(self, expected_fragment: str) -> None:
        with allure.step(f'Ensure current URL contains "{expected_fragment}"'):
            pattern = re.compile(f".*{re.escape(expected_fragment)}.*")
            await expect(self.page).to_have_url(pattern)

    def get_last_toast(self) -> Locator:
        return self.page.locator(self.TOAST_SELECTOR).last
