from __future__ import annotations

from typing import List

import allure
from playwright.async_api import Locator, Page, expect

from ui.page_factory.button import Button
from ui.page_factory.text import Text
from ui.page_factory.textarea import Textarea
from ui.widgets.common.author_link import AuthorLink


class CommentsSection:
    SECTION = "Post comments"
    CARD_TEST_ID = "post-comments-card"
    LIST_TEST_ID = "post-comments-list"
    ITEM_TEST_ID = "post-comment-item"

    def __init__(self, page: Page) -> None:
        self.page = page
        self.container = self.page.get_by_test_id(self.CARD_TEST_ID)
        self.list = self.container.get_by_test_id(self.LIST_TEST_ID)
        self.items = self.list.get_by_test_id(self.ITEM_TEST_ID)
        self.form = CommentForm(page)

    async def should_be_visible(self) -> None:
        with allure.step("Ensure comments section is visible"):
            await expect(self.container).to_be_visible()

    async def should_have_at_least(self, count: int = 1) -> None:
        with allure.step(f"Ensure there are at least {count} comments"):
            actual = await self.items.count()
            assert actual >= count, f"Expected at least {count} comments, found {actual}"

    async def get_comment_by_index(self, index: int = 0) -> CommentItem:
        total = await self.items.count()
        if total == 0:
            raise AssertionError("No comments present")
        if index < 0 or index >= total:
            raise IndexError(f"Comment index {index} is out of range (total {total})")
        locator = self.items.nth(index)
        with allure.step(f"Get comment by index {index}"):
            await expect(locator).to_be_visible()
            return CommentItem(self.page, locator=locator, label=f"#{index + 1}")

    async def should_have_comment_with_text(self, text: str) -> None:
        with allure.step(f"Ensure a comment contains text '{text}'"):
            await expect(self.items.filter(has_text=text)).to_have_count(1)


class CommentForm:
    SECTION = "Post comments | Form"
    CONTAINER_TEST_ID = "post-comment-form"
    TEXTAREA_TEST_ID = "post-comment-input"
    SUBMIT_BUTTON_TEST_ID = "post-comment-submit-btn"

    def __init__(self, page: Page) -> None:
        self.page = page
        self.container = page.get_by_test_id(self.CONTAINER_TEST_ID)
        self.textarea = Textarea(
            page,
            locator=self.container.get_by_test_id(self.TEXTAREA_TEST_ID).locator("textarea"),
            name="Comment textarea",
            section=self.SECTION,
        )
        self.submit_button = Button(
            page,
            locator=self.container.get_by_test_id(self.SUBMIT_BUTTON_TEST_ID),
            name="Submit comment",
            section=self.SECTION,
        )

    async def fill(self, text: str) -> None:
        await self.textarea.fill(text, validate_value=True)

    async def submit(self) -> None:
        await self.submit_button.click()

    async def add_comment(self, text: str) -> None:
        with allure.step(f"Submit comment: {text[:50]}{'...' if len(text) > 50 else ''}"):
            await self.fill(text)
            await self.submit_button.should_be_enabled()
            await self.submit()


class CommentItem:
    SECTION = "Post comments | Comment"
    AUTHOR_TEST_ID = "comment-author"
    TEXT_TEST_ID = "comment-text"
    REPLY_BUTTON_TEST_ID = "comment-reply-btn"
    REPLY_INPUT_TEST_ID = "comment-reply-input"
    REPLY_SUBMIT_BUTTON_TEST_ID = "comment-reply-submit-btn"
    REPLIES_LIST_TEST_ID = "comment-replies-list"
    REPLY_CARD_TEST_ID = "comment-card"

    def __init__(self, page: Page, *, locator: Locator, label: str) -> None:
        self.page = page
        section = f"{self.SECTION} ({label})"
        self.author = AuthorLink(
            page,
            locator=locator.get_by_test_id(self.AUTHOR_TEST_ID),
            name="Comment author",
            section=section,
        )
        self.text = Text(
            page,
            locator=locator.get_by_test_id(self.TEXT_TEST_ID),
            name="Comment text",
            section=section,
        )
        self.reply_button = Button(
            page,
            locator=locator.get_by_test_id(self.REPLY_BUTTON_TEST_ID),
            name="Reply button",
            section=section,
        )
        self.reply_textarea = Textarea(
            page,
            locator=locator.get_by_test_id(self.REPLY_INPUT_TEST_ID).locator("textarea"),
            name="Reply textarea",
            section=section,
        )
        self.reply_submit = Button(
            page,
            locator=locator.get_by_test_id(self.REPLY_SUBMIT_BUTTON_TEST_ID),
            name="Reply submit button",
            section=section,
        )
        self.replies_container = locator.get_by_test_id(self.REPLIES_LIST_TEST_ID)

    async def should_contain_text(self, expected: str) -> None:
        await self.text.should_contain_text(expected)

    async def should_show_author(self, expected: str) -> None:
        await self.author.should_contain_text(expected)

    async def click_reply(self) -> None:
        await self.reply_button.click()

    async def reply(self, text: str) -> None:
        with allure.step(f"Reply to comment: {text[:50]}{'...' if len(text) > 50 else ''}"):
            await self.click_reply()
            await self.reply_textarea.fill(text, validate_value=True)
            await self.reply_submit.click()

    async def replies(self) -> List["CommentItem"]:
        reply_cards = self.replies_container.get_by_test_id(self.REPLY_CARD_TEST_ID)
        count = await reply_cards.count()
        items: List[CommentItem] = []
        for idx in range(count):
            items.append(
                CommentItem(
                    self.page,
                    locator=reply_cards.nth(idx),
                    label=f"reply #{idx + 1}",
                )
            )
        return items

    async def wait_for_reply_with_text(self, expected: str, timeout: int = 5000) -> "CommentItem":
        with allure.step(
            f"Check reply with text '{expected[:50]}{'...' if len(expected) > 50 else ''}'"
        ):
            reply_cards = self.replies_container.get_by_test_id(self.REPLY_CARD_TEST_ID)
            await expect(reply_cards).to_have_count(1, timeout=timeout)
            replies = await self.replies()
            for reply in replies:
                try:
                    await reply.should_contain_text(expected)
                    return reply
                except AssertionError:
                    continue
            raise AssertionError(f"Reply with text '{expected}' not found")
