import asyncio

import allure

from models.posts_dto import PublishPostDTO
from utils.assertions.ui_expectations import expect_contains_text
from utils.database.database_helpers import fetch_single_post_by_title


class TestPostFeed:
    # ----------- позитивные тесты -----------

    @allure.feature("Post feed")
    @allure.story("Empty state")
    @allure.severity(allure.severity_level.NORMAL)
    async def test_feed_empty_state_shows_placeholder(
        self, empty_posts_db, user_api_created, make_page
    ):
        home_page = await make_page("home", user=user_api_created)
        await home_page.open()
        await home_page.feed.should_show_empty_state()

    @allure.feature("Post feed")
    @allure.story("Non-empty state")
    @allure.severity(allure.severity_level.CRITICAL)
    async def test_feed_shows_posts(self, user_api_created, make_post_api_created, make_page):
        created_post = await make_post_api_created(
            email=user_api_created.email, password=user_api_created.password
        )

        home_page = await make_page("home", user=user_api_created)
        await home_page.open()
        await home_page.should_show_feed(min_posts=1)
        card = await home_page.feed.get_card_by_index(0)
        await card.should_be_visible()

        await expect_contains_text(
            card.title.get_locator(),
            created_post.title,
            label="Ensure feed card shows the post title",
        )
        await expect_contains_text(
            card.content.get_locator(),
            created_post.content,
            label="Ensure feed card shows full post content",
        )

    @allure.feature("Post feed")
    @allure.story("Sorting")
    @allure.severity(allure.severity_level.NORMAL)
    async def test_feed_orders_posts_by_created_at(
        self, user_api_created, make_post_api_created, make_page
    ):
        user = user_api_created
        older_payload = PublishPostDTO.random()
        newer_payload = PublishPostDTO.random()
        await make_post_api_created(email=user.email, password=user.password, payload=older_payload)
        await make_post_api_created(email=user.email, password=user.password, payload=newer_payload)

        home_page = await make_page("home", user=user_api_created)
        await home_page.open()
        await home_page.should_show_feed(min_posts=2)

        newest_card = await home_page.feed.get_card_by_index(0)
        await expect_contains_text(
            newest_card.title.get_locator(),
            newer_payload.title,
            label="Ensure newest post is first in the feed",
        )

        older_card = await home_page.feed.get_card_by_index(1)
        await expect_contains_text(
            older_card.title.get_locator(),
            older_payload.title,
            label="Ensure older post is shown after the newest post",
        )

    @allure.feature("Post feed")
    @allure.story("Metadata")
    @allure.severity(allure.severity_level.NORMAL)
    async def test_feed_card_shows_author_and_date(
        self,
        make_authenticated_user_with_home_page,
        make_post_api_created,
        session_sql_client,
    ):
        # создаем автора через API и авторизуем через localStorage
        author, author_home_page, author_context = await make_authenticated_user_with_home_page()

        created_post = await make_post_api_created(email=author.email, password=author.password)

        db_post = await asyncio.to_thread(
            fetch_single_post_by_title,
            session_sql_client,
            created_post.title,
            columns="p.id::text, p.title, p.created_at, u.username, u.email",
        )

        await author_home_page.open()
        await author_home_page.should_show_feed(min_posts=1)

        card = await author_home_page.feed.get_card_by_index(0)
        await card.should_be_visible()

        await expect_contains_text(
            card.author.get_locator(),
            "я",
            label="Author sees their own post labeled as 'я'",
        )
        date_fragment = db_post["created_at"].strftime("%Y")
        await expect_contains_text(
            card.date.get_locator(),
            date_fragment,
            label="Ensure feed card shows publish date fragment",
        )

        # создаем читателя через API и авторизуем через localStorage
        reader, reader_home_page, reader_context = await make_authenticated_user_with_home_page()

        await reader_home_page.open()
        await reader_home_page.should_show_feed(min_posts=1)

        reader_card = await reader_home_page.feed.get_card_by_index(0)
        await reader_card.should_be_visible()
        await expect_contains_text(
            reader_card.author.get_locator(),
            author.email,
            label="Other user sees author's email on the post",
        )

        await author_context.close()
        await reader_context.close()
