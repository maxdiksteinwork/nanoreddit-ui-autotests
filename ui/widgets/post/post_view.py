from __future__ import annotations

import allure
from playwright.async_api import Page, expect

from ui.page_factory.button import Button
from ui.page_factory.text import Text
from ui.widgets.common.author_link import AuthorLink


class PostView:
    SECTION = "Post view"
    CARD_LOCATOR = "[qa-data='post-card']"
    TITLE_LOCATOR = ".n-card-header__main"
    CONTENT_LOCATOR = "[qa-data='post-content']"
    META_LOCATOR = "[qa-data='post-meta']"
    AUTHOR_LOCATOR = "[qa-data='post-author']"
    DATE_LOCATOR = "[qa-data='post-date']"
    VOTE_BLOCK_LOCATOR = "[qa-data='post-vote-block']"
    VOTE_UP_LOCATOR = "[qa-data='post-vote-up']"
    VOTE_DOWN_LOCATOR = "[qa-data='post-vote-down']"
    VOTE_SCORE_LOCATOR = "[qa-data='post-vote-score']"

    def __init__(self, page: Page) -> None:
        self.container = page.locator(self.CARD_LOCATOR)
        self.title = Text(
            page,
            locator=self.container.locator(self.TITLE_LOCATOR),
            name="Post title",
            section=self.SECTION,
        )
        self.content = Text(
            page,
            locator=self.container.locator(self.CONTENT_LOCATOR),
            name="Post content",
            section=self.SECTION,
        )
        self.meta = self.container.locator(self.META_LOCATOR)
        self.author = AuthorLink(
            page,
            locator=self.meta.locator(self.AUTHOR_LOCATOR),
            name="Post author",
            section=self.SECTION,
        )
        self.date = Text(
            page,
            locator=self.meta.locator(self.DATE_LOCATOR),
            name="Post date",
            section=self.SECTION,
        )
        vote_block = self.container.locator(self.VOTE_BLOCK_LOCATOR)
        self.vote_up_button = Button(
            page,
            locator=vote_block.locator(self.VOTE_UP_LOCATOR),
            name="Vote up",
            section=self.SECTION,
        )
        self.vote_down_button = Button(
            page,
            locator=vote_block.locator(self.VOTE_DOWN_LOCATOR),
            name="Vote down",
            section=self.SECTION,
        )
        self.vote_score = Text(
            page,
            locator=vote_block.locator(self.VOTE_SCORE_LOCATOR),
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
