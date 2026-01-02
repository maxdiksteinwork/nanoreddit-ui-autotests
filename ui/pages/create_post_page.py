from __future__ import annotations

from playwright.async_api import Page

from models.posts_dto import PublishPostDTO
from ui.pages.base_page import BasePage
from ui.widgets.post.create_post_form import CreatePostForm


class CreatePostPage(BasePage):
    path = "create-post"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.form = CreatePostForm(page)

    async def open(self) -> None:
        await self.visit()

    async def create_post(self, *, title: str, content: str) -> None:
        await self.form.create_post(title=title, content=content)

    async def create_post_model(self, payload: PublishPostDTO) -> None:
        await self.create_post(title=payload.title, content=payload.content)
