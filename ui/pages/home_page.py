from __future__ import annotations

import allure
from playwright.async_api import Page

from ui.pages.base_page import BasePage
from ui.pages.post_page import PostPage
from ui.widgets.feed.post_list import PostList


class HomePage(BasePage):
    path = "/"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.feed = PostList(page)

    async def open(self) -> None:
        await self.visit()

    async def should_show_feed(self, *, min_posts: int = 1) -> None:
        with allure.step("Validate feed section on Home page"):
            await self.feed.should_have_at_least(min_posts)

    async def open_post(self, *, title: str | None = None, index: int | None = None) -> PostPage:
        if title is not None:
            card = await self.feed.get_card_by_title(title)
        else:
            position = index or 0
            card = await self.feed.get_card_by_index(position)
        await card.open()

        post_page = PostPage(self.page)
        await post_page.comments.should_be_visible()
        return post_page

    async def navigate_to_post_by_id(self, post_id: str) -> PostPage:
        post_page = PostPage(self.page)
        await post_page.open_by_id(post_id)
        return post_page
