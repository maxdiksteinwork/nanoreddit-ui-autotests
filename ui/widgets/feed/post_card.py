from __future__ import annotations

import allure
from playwright.async_api import Locator, Page

from ui.page_factory.link import Link
from ui.page_factory.list_item import ListItem
from ui.page_factory.text import Text


class PostCard:
    SECTION = "Post card"
    LINK_TEST_ID = "home-post-link"
    TITLE_TEST_ID = "home-post-title"
    CONTENT_TEST_ID = "home-post-content"
    META_TEST_ID = "home-post-meta"
    AUTHOR_TEST_ID = "home-post-author"
    DATE_TEST_ID = "home-post-date"

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
            locator=locator.get_by_test_id(self.LINK_TEST_ID),
            name="Post link",
            section=section,
        )
        self.title = Text(
            page,
            locator=locator.get_by_test_id(self.TITLE_TEST_ID),
            name="Title",
            section=section,
        )
        self.content = Text(
            page,
            locator=locator.get_by_test_id(self.CONTENT_TEST_ID),
            name="Content preview",
            section=section,
        )
        self.meta = Text(
            page,
            locator=locator.get_by_test_id(self.META_TEST_ID),
            name="Meta block",
            section=section,
        )
        self.author = Text(
            page,
            locator=locator.get_by_test_id(self.AUTHOR_TEST_ID),
            name="Author",
            section=section,
        )
        self.date = Text(
            page,
            locator=locator.get_by_test_id(self.DATE_TEST_ID),
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
