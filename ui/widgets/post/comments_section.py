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
    CARD_LOCATOR = "[qa-data='post-comments-card']"
    LIST_LOCATOR = "[qa-data='post-comments-list']"
    ITEM_LOCATOR = "[qa-data='post-comment-item']"

    def __init__(self, page: Page) -> None:
        self.page = page
        self.container = self.page.locator(self.CARD_LOCATOR)
        self.list = self.container.locator(self.LIST_LOCATOR)
        self.items = self.list.locator(self.ITEM_LOCATOR)
        self.form = CommentForm(page)

    async def should_be_visible(self) -> None:
        with allure.step("Ensure comments section is visible"):
            await expect(self.container).to_be_visible()

    async def should_have_at_least(self, count: int = 1) -> None:
        with allure.step(f"Ensure there are at least {count} comments"):
            actual = await self.items.count()
            assert actual >= count, (
                f"Expected at least {count} comments, found {actual}"
            )

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
    CONTAINER_LOCATOR = "[qa-data='post-comment-form']"
    TEXTAREA_LOCATOR = "[qa-data='post-comment-input'] textarea"
    SUBMIT_BUTTON_LOCATOR = "[qa-data='post-comment-submit-btn']"

    def __init__(self, page: Page) -> None:
        self.container = page.locator(self.CONTAINER_LOCATOR)
        self.textarea = Textarea(
            page,
            locator=self.container.locator(self.TEXTAREA_LOCATOR),
            name="Comment textarea",
            section=self.SECTION,
        )
        self.submit_button = Button(
            page,
            locator=self.container.locator(self.SUBMIT_BUTTON_LOCATOR),
            name="Submit comment",
            section=self.SECTION,
        )

    async def fill(self, text: str) -> None:
        await self.textarea.fill(text, validate_value=True)

    async def submit(self) -> None:
        await self.submit_button.click()

    async def add_comment(self, text: str) -> None:
        with allure.step(
            f"Submit comment: {text[:50]}{'...' if len(text) > 50 else ''}"
        ):
            await self.fill(text)
            await self.submit_button.should_be_enabled()
            await self.submit()


class CommentItem:
    SECTION = "Post comments | Comment"
    AUTHOR_LOCATOR = "[qa-data='comment-author']"
    TEXT_LOCATOR = "[qa-data='comment-text']"
    REPLY_BUTTON_LOCATOR = "[qa-data='comment-reply-btn']"
    REPLY_INPUT_LOCATOR = "[qa-data='comment-reply-input'] textarea"
    REPLY_SUBMIT_BUTTON_LOCATOR = "[qa-data='comment-reply-submit-btn']"
    REPLIES_LIST_LOCATOR = "[qa-data='comment-replies-list']"
    REPLY_CARD_LOCATOR = "[qa-data='comment-card']"

    def __init__(self, page: Page, *, locator: Locator, label: str) -> None:
        self.page = page
        section = f"{self.SECTION} ({label})"
        self.author = AuthorLink(
            page,
            locator=locator.locator(self.AUTHOR_LOCATOR),
            name="Comment author",
            section=section,
        )
        self.text = Text(
            page,
            locator=locator.locator(self.TEXT_LOCATOR),
            name="Comment text",
            section=section,
        )
        self.reply_button = Button(
            page,
            locator=locator.locator(self.REPLY_BUTTON_LOCATOR),
            name="Reply button",
            section=section,
        )
        self.reply_textarea = Textarea(
            page,
            locator=locator.locator(self.REPLY_INPUT_LOCATOR),
            name="Reply textarea",
            section=section,
        )
        self.reply_submit = Button(
            page,
            locator=locator.locator(self.REPLY_SUBMIT_BUTTON_LOCATOR),
            name="Reply submit button",
            section=section,
        )
        self.replies_container = locator.locator(self.REPLIES_LIST_LOCATOR)

    async def should_contain_text(self, expected: str) -> None:
        await self.text.should_contain_text(expected)

    async def should_show_author(self, expected: str) -> None:
        await self.author.should_contain_text(expected)

    async def click_reply(self) -> None:
        await self.reply_button.click()

    async def reply(self, text: str) -> None:
        with allure.step(
            f"Reply to comment: {text[:50]}{'...' if len(text) > 50 else ''}"
        ):
            await self.click_reply()
            await self.reply_textarea.fill(text, validate_value=True)
            await self.reply_submit.click()

    async def replies(self) -> List["CommentItem"]:
        reply_cards = self.replies_container.locator(self.REPLY_CARD_LOCATOR)
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

    async def wait_for_reply_with_text(
        self, expected: str, timeout: int = 5000
    ) -> "CommentItem":
        with allure.step(
            f"Check reply with text '{expected[:50]}{'...' if len(expected) > 50 else ''}'"
        ):
            reply_cards = self.replies_container.locator(self.REPLY_CARD_LOCATOR)
            await expect(reply_cards).to_have_count(1, timeout=timeout)
            replies = await self.replies()
            for reply in replies:
                try:
                    await reply.should_contain_text(expected)
                    return reply
                except AssertionError:
                    continue
            raise AssertionError(f"Reply with text '{expected}' not found")
