from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import allure
from playwright.async_api import Locator, Page, expect


class Component(ABC):
    def __init__(
        self,
        page: Page,
        *,
        locator: str | Locator,
        name: str,
        section: str | None = None,
    ) -> None:
        self.page = page
        self._raw_locator = locator
        self.name = name
        self.section = section

    @property
    @abstractmethod
    def type_of(self) -> str:
        """human-readable component type for Allure steps."""

    @property
    def _display_name(self) -> str:
        if self.section:
            return f"[{self.section}] {self.name}"
        return self.name

    def _action_step(self, action: str):
        title = f"{self.type_of.title()} | {self._display_name} → {action}"
        return allure.step(title)

    def get_locator(self, **kwargs: Any) -> Locator:
        if isinstance(self._raw_locator, Locator):
            if kwargs:
                raise ValueError(
                    "Formatted locators are not supported when locator is a Locator instance"
                )
            return self._raw_locator

        resolved_locator = self._raw_locator.format(**kwargs) if kwargs else self._raw_locator
        return self.page.locator(resolved_locator)

    async def click(self, **kwargs: Any) -> None:
        with self._action_step("click"):
            locator = self.get_locator(**kwargs)
            await locator.click()

    async def should_be_visible(self, **kwargs: Any) -> None:
        with self._action_step("assert visible"):
            locator = self.get_locator(**kwargs)
            await expect(locator).to_be_visible()

    async def should_have_text(self, text: str, **kwargs: Any) -> None:
        with self._action_step(f'assert text is "{text}"'):
            locator = self.get_locator(**kwargs)
            await expect(locator).to_have_text(text)

    async def should_be_enabled(self, **kwargs: Any) -> None:
        with self._action_step("assert enabled"):
            locator = self.get_locator(**kwargs)
            await expect(locator).to_be_enabled()

    async def should_be_disabled(self, **kwargs: Any) -> None:
        with self._action_step("assert disabled"):
            locator = self.get_locator(**kwargs)
            await expect(locator).to_be_disabled()
