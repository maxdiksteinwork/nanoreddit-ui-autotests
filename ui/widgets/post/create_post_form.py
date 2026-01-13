from __future__ import annotations

import allure
from playwright.async_api import Page, expect

from ui.page_factory.button import Button
from ui.page_factory.input import Input
from ui.page_factory.textarea import Textarea


class CreatePostForm:
    SECTION = "Create post form"
    FORM_TEST_ID = "create-post-form"
    TITLE_INPUT_TEST_ID = "create-post-title-input"
    CONTENT_INPUT_TEST_ID = "create-post-content-input"
    SUBMIT_BUTTON_TEST_ID = "create-post-submit-btn"

    def __init__(self, page: Page) -> None:
        self.page = page
        self.form = page.get_by_test_id(self.FORM_TEST_ID)
        self.title_input = Input(
            page,
            locator=self.form.get_by_test_id(self.TITLE_INPUT_TEST_ID).locator("input"),
            name="Post title",
            section=self.SECTION,
        )
        self.content_input = Textarea(
            page,
            locator=self.form.get_by_test_id(self.CONTENT_INPUT_TEST_ID).locator("textarea"),
            name="Post content",
            section=self.SECTION,
        )
        self.submit_button = Button(
            page,
            locator=self.form.get_by_test_id(self.SUBMIT_BUTTON_TEST_ID),
            name="Submit new post",
            section=self.SECTION,
        )

    async def should_be_visible(self) -> None:
        with allure.step("Ensure create post form is visible"):
            await expect(self.form).to_be_visible()

    async def fill_title(self, title: str) -> None:
        await self.title_input.fill(title, validate_value=True)

    async def fill_content(self, content: str) -> None:
        await self.content_input.fill(content, validate_value=True)

    async def submit(self) -> None:
        await self.submit_button.click()

    async def create_post(self, *, title: str, content: str) -> None:
        with allure.step(f"Create post with title '{title}'"):
            await self.should_be_visible()
            await self.fill_title(title)
            await self.fill_content(content)
            await self.submit()
