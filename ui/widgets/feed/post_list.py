from __future__ import annotations

import allure
from playwright.async_api import Page, expect

from ui.widgets.feed.post_card import PostCard


class PostList:
    LIST_LOCATOR = "[qa-data='home-post-list']"
    CARD_LOCATOR = "[qa-data='home-post-item']"
    EMPTY_FEED_LOCATOR = "[qa-data='home-empty-posts']"
    EMPTY_FEED_TEXT_LOCATOR = f"{EMPTY_FEED_LOCATOR} .n-empty__description"
    FEED_CARD_WRAPPER = "[qa-data='home-posts-card']"

    def __init__(self, page: Page) -> None:
        self.page = page
        self._cards_list = page.locator(self.LIST_LOCATOR)
        self._cards = page.locator(self.CARD_LOCATOR)

    async def should_be_visible(self) -> None:
        with allure.step("Ensure feed list container is visible"):
            if await self._cards_list.count() > 0:
                await expect(self._cards_list).to_be_visible()
            else:
                await expect(self._cards.first).to_be_visible()

    async def should_have_at_least(self, count: int = 1) -> None:
        await self.should_be_visible()
        with allure.step(f"Ensure feed has at least {count} posts"):
            actual = await self._cards.count()
            assert actual >= count, (
                f"Feed list contains {actual} posts, expected at least {count}"
            )

    async def get_card_by_index(self, index: int = 0) -> PostCard:
        await self.should_be_visible()
        total = await self._cards.count()
        if total == 0:
            raise AssertionError("Feed list is empty, cannot fetch a card")
        if index < 0 or index >= total:
            raise IndexError(
                f"Feed card index {index} is out of range (total: {total})"
            )

        locator = self._cards.nth(index)
        with allure.step(f"Get post card by index {index}"):
            await expect(locator).to_be_visible()
            return PostCard(self.page, locator=locator, label=f"#{index + 1}")

    async def get_card_by_title(self, title: str) -> PostCard:
        await self.should_be_visible()
        locator = self._cards.filter(has_text=title).first
        with allure.step(f"Find post card with title '{title}'"):
            await expect(locator).to_be_visible()
        return PostCard(self.page, locator=locator, label=title)

    async def should_show_empty_state(
        self, *, expected_message: str = "Пока нет постов"
    ) -> None:
        with allure.step("Ensure empty feed state is shown"):
            await expect(self.page.locator(self.FEED_CARD_WRAPPER)).to_be_visible()
            await expect(self._cards).to_have_count(0)
            await expect(
                self.page.locator(self.EMPTY_FEED_TEXT_LOCATOR)
            ).to_contain_text(expected_message)
