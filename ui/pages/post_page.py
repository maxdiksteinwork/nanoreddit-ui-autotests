from __future__ import annotations

from playwright.async_api import Page

from ui.pages.base_page import BasePage
from ui.widgets.post.comments_section import CommentsSection
from ui.widgets.post.post_view import PostView


class PostPage(BasePage):
    path = None

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.post = PostView(page)
        self.comments = CommentsSection(page)

    def set_post_id(self, post_id: str) -> None:
        self.path = f"post/{post_id}"

    async def open_by_id(self, post_id: str) -> None:
        self.set_post_id(post_id)
        await self.visit()
        await self.comments.should_be_visible()

    async def should_display_post(
        self,
        *,
        title: str | None = None,
        content_fragment: str | None = None,
        author_fragment: str | None = None,
        date_fragment: str | None = None,
    ) -> None:
        await self.post.should_be_visible()
        if title:
            await self.post.should_have_title(title)
        if content_fragment:
            await self.post.should_have_content(content_fragment)
        if author_fragment:
            await self.post.should_show_author(author_fragment)
        if date_fragment:
            await self.post.should_show_date(date_fragment)

    async def vote_up(self) -> None:
        await self.post.vote_up()

    async def vote_down(self) -> None:
        await self.post.vote_down()

    async def add_comment(self, text: str) -> None:
        await self.comments.form.add_comment(text)

    async def should_have_comment(self, text: str) -> None:
        await self.comments.should_have_comment_with_text(text)
