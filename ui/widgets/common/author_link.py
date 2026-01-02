from __future__ import annotations

from playwright.async_api import expect

from ui.page_factory.link import Link


class AuthorLink(Link):
    """clickable author email that opens profile modal"""

    async def should_contain_text(self, text: str) -> None:
        with self._action_step(f'assert link contains "{text}"'):
            locator = self.get_locator()
            await expect(locator).to_contain_text(text)

    async def open_profile(self) -> None:
        await self.click()
