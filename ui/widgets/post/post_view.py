from __future__ import annotations

import allure
from playwright.async_api import Page, expect

from ui.page_factory.button import Button
from ui.page_factory.text import Text
from ui.widgets.common.author_link import AuthorLink


class PostView:
    SECTION = "Post view"
    CARD_TEST_ID = "post-card"
    CONTENT_TEST_ID = "post-content"
    META_TEST_ID = "post-meta"
    AUTHOR_TEST_ID = "post-author"
    DATE_TEST_ID = "post-date"
    VOTE_BLOCK_TEST_ID = "post-vote-block"
    VOTE_UP_TEST_ID = "post-vote-up"
    VOTE_DOWN_TEST_ID = "post-vote-down"
    VOTE_SCORE_TEST_ID = "post-vote-score"

    def __init__(self, page: Page) -> None:
        self.page = page
        self.container = page.get_by_test_id(self.CARD_TEST_ID)
        self.title = Text(
            page,
            locator=self.container.get_by_role("heading").first,
            name="Post title",
            section=self.SECTION,
        )
        self.content = Text(
            page,
            locator=self.container.get_by_test_id(self.CONTENT_TEST_ID),
            name="Post content",
            section=self.SECTION,
        )
        self.meta = self.container.get_by_test_id(self.META_TEST_ID)
        self.author = AuthorLink(
            page,
            locator=self.meta.get_by_test_id(self.AUTHOR_TEST_ID),
            name="Post author",
            section=self.SECTION,
        )
        self.date = Text(
            page,
            locator=self.meta.get_by_test_id(self.DATE_TEST_ID),
            name="Post date",
            section=self.SECTION,
        )
        vote_block = self.container.get_by_test_id(self.VOTE_BLOCK_TEST_ID)
        self.vote_up_button = Button(
            page,
            locator=vote_block.get_by_test_id(self.VOTE_UP_TEST_ID),
            name="Vote up",
            section=self.SECTION,
        )
        self.vote_down_button = Button(
            page,
            locator=vote_block.get_by_test_id(self.VOTE_DOWN_TEST_ID),
            name="Vote down",
            section=self.SECTION,
        )
        self.vote_score = Text(
            page,
            locator=vote_block.get_by_test_id(self.VOTE_SCORE_TEST_ID),
            name="Vote score",
            section=self.SECTION,
        )

    async def should_be_visible(self) -> None:
        with allure.step("Ensure post card is visible"):
            await expect(self.container).to_be_visible()

    async def should_have_title(self, title: str) -> None:
        await self.title.should_have_text(title)

    async def should_have_content(self, text_fragment: str) -> None:
        await self.content.should_contain_text(text_fragment)

    async def should_show_author(self, author_fragment: str) -> None:
        await self.author.should_contain_text(author_fragment)

    async def should_show_date(self, date_fragment: str) -> None:
        await self.date.should_contain_text(date_fragment)

    async def vote_up(self) -> None:
        await self.vote_up_button.click()

    async def vote_down(self) -> None:
        await self.vote_down_button.click()

    async def should_have_score(self, value: str | int) -> None:
        await self.vote_score.should_have_text(str(value))
