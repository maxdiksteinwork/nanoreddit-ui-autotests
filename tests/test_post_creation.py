import asyncio

import allure
import pytest

from models.posts_dto import PublishPostDTO
from utils.assertions.ui_expectations import (
    assert_post_creation_success,
    expect_contains_text,
)
from utils.database.database_helpers import (
    get_post_by_title,
    wait_for_post_in_db,
)


class TestPostCreation:
    # ----------- позитивные тесты создания поста -----------

    @allure.feature("Post creation")
    @allure.story("Create post")
    @allure.severity(allure.severity_level.CRITICAL)
    async def test_create_post(self, user_api_created, session_sql_client, make_page):
        payload = PublishPostDTO.random()

        create_post_page = await make_page("create_post", user=user_api_created)
        await create_post_page.open()
        await create_post_page.create_post_model(payload)
        await assert_post_creation_success(create_post_page.page)

        db_post = await wait_for_post_in_db(
            session_sql_client, payload.title, author_email=user_api_created.email
        )
        assert db_post["title"] == payload.title
        assert db_post["content"] == payload.content

    @allure.feature("Post creation")
    @allure.story("Create post with special characters")
    @allure.severity(allure.severity_level.NORMAL)
    async def test_create_post_special_characters(
        self, user_api_created, session_sql_client, post_db_cleanup, make_page
    ):
        fancy_title = "🔥 Привет <b>друг</b> & welcome!"
        fancy_content = (
            "🔥 Привет <b>друг</b> & welcome! This is a test post with emojis & HTML-like tags."
        )
        fancy_payload = PublishPostDTO(title=fancy_title, content=fancy_content)
        post_db_cleanup(title=fancy_title)

        create_post_page = await make_page("create_post", user=user_api_created)
        await create_post_page.open()
        await create_post_page.create_post_model(fancy_payload)
        await assert_post_creation_success(create_post_page.page)

        db_post = await wait_for_post_in_db(
            session_sql_client, fancy_title, author_email=user_api_created.email
        )
        assert db_post["title"] == fancy_title
        assert db_post["content"] == fancy_content

    @allure.feature("Post creation")
    @allure.story("Boundary values")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize(
        "title,content",
        [
            ("A", "C"),
            ("A" * 255, "Valid content"),
            ("Valid title", "C" * 1000),
        ],
        ids=["minimal", "max_title", "long_content"],
    )
    async def test_create_post_boundary_valid(self, user_api_created, make_page, title, content):
        payload = PublishPostDTO(title=title, content=content)
        create_post_page = await make_page("create_post", user=user_api_created)
        await create_post_page.open()
        await create_post_page.create_post_model(payload)
        await assert_post_creation_success(create_post_page.page)

    # ----------- негативные тесты создания поста -----------

    @allure.feature("Post creation")
    @allure.story("Boundary values")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize(
        "title,content,expectation",
        [
            pytest.param("", "Valid content", "button_disabled", id="empty_title"),
            pytest.param("Valid title", "", "button_disabled", id="empty_content"),
            pytest.param("A" * 256, "Valid content", "api_error", id="title_too_long"),
            # pytest.param("Valid title", "C"*30000, "api_error", id="title_too_long")
            # на данный момент тест ломается от таких значений,
            # хотя в реальном браузере такое значение принимается.
            # Будет заведен баг.
        ],
    )
    async def test_create_post_boundary_invalid(
        self, user_api_created, make_page, title, content, expectation
    ):
        payload = PublishPostDTO(title=title, content=content)
        create_post_page = await make_page("create_post", user=user_api_created)
        await create_post_page.open()
        await create_post_page.form.title_input.fill(payload.title)
        await create_post_page.form.content_input.fill(payload.content)

        if expectation == "button_disabled":
            await create_post_page.form.submit_button.should_be_disabled()
        else:
            await create_post_page.form.submit_button.should_be_enabled()
            await create_post_page.form.submit()
            await expect_contains_text(
                create_post_page.get_last_toast(),
                "Validation error",
                label="Ensure validation error toast is shown",
            )

    # ----------- дополнительные UX-проверки -----------

    @allure.feature("Post creation")
    @allure.story("Interaction resilience")
    @allure.severity(allure.severity_level.NORMAL)
    async def test_create_post_submit_double_click(
        self, user_api_created, session_sql_client, make_page
    ):
        title = "Double-click resilience"
        content = "Valid content for double-click test"
        payload = PublishPostDTO(title=title, content=content)

        create_post_page = await make_page("create_post", user=user_api_created)
        await create_post_page.open()
        await create_post_page.form.title_input.fill(payload.title)
        await create_post_page.form.content_input.fill(payload.content)

        await create_post_page.form.submit_button.should_be_enabled()
        await create_post_page.form.submit_button.double_click()

        with allure.step("Validate only one created post in DB"):
            await wait_for_post_in_db(
                session_sql_client, title, author_email=user_api_created.email
            )
            posts = await asyncio.to_thread(
                get_post_by_title, session_sql_client, title, author_email=user_api_created.email
            )
            assert len(posts) == 1, "Double click created duplicate posts in DB"

        await assert_post_creation_success(create_post_page.page)
