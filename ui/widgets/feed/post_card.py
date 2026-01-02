from __future__ import annotations

import allure
from playwright.async_api import Locator, Page

from ui.page_factory.link import Link
from ui.page_factory.list_item import ListItem
from ui.page_factory.text import Text


class PostCard:
    SECTION = "Post card"
    LINK_LOCATOR = "[qa-data='home-post-link']"
    TITLE_LOCATOR = "[qa-data='home-post-title']"
    CONTENT_LOCATOR = "[qa-data='home-post-content']"
    META_LOCATOR = "[qa-data='home-post-meta']"
    AUTHOR_LOCATOR = "[qa-data='home-post-author']"
    DATE_LOCATOR = "[qa-data='home-post-date']"

    def __init__(self, page: Page, *, locator: Locator, label: str) -> None:
        self.label = label
        section = f"{self.SECTION} ({label})"
        self._container = ListItem(
            page,
            locator=locator,
            name=f"Post card {label}",
            section=section,
        )
        self.link = Link(
            page,
            locator=locator.locator(self.LINK_LOCATOR),
            name="Post link",
            section=section,
        )
        self.title = Text(
            page,
            locator=locator.locator(self.TITLE_LOCATOR),
            name="Title",
            section=section,
        )
        self.content = Text(
            page,
            locator=locator.locator(self.CONTENT_LOCATOR),
            name="Content preview",
            section=section,
        )
        self.meta = Text(
            page,
            locator=locator.locator(self.META_LOCATOR),
            name="Meta block",
            section=section,
        )
        self.author = Text(
            page,
            locator=locator.locator(self.AUTHOR_LOCATOR),
            name="Author",
            section=section,
        )
        self.date = Text(
            page,
            locator=locator.locator(self.DATE_LOCATOR),
            name="Publish date",
            section=section,
        )

    async def should_be_visible(self) -> None:
        await self._container.should_be_visible()

    async def should_have_title(self, title: str) -> None:
        await self.title.should_have_text(title)

    async def should_contain_content(self, text_fragment: str) -> None:
        await self.content.should_contain_text(text_fragment)

    async def should_display_author(self, author: str) -> None:
        await self.author.should_contain_text(author)

    async def should_display_date(self, date_fragment: str) -> None:
        await self.date.should_contain_text(date_fragment)

    async def open(self) -> None:
        with allure.step(f"Open post card {self.label}"):
            await self.link.click()
