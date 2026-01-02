import asyncio

import allure

from utils.assertions.ui_expectations import expect_contains_text
from utils.database.database_helpers import fetch_single_post_by_title

# ----------- позитивные тесты -----------


@allure.feature("Post details")
@allure.story("Content")
@allure.severity(allure.severity_level.CRITICAL)
async def test_post_details_content(
    user_api_created_ui_authorized, make_post_api_created, session_sql_client, home_page
):
    user = user_api_created_ui_authorized
    created_post = await make_post_api_created(email=user.email, password=user.password)

    with allure.step("Verify post content in database"):
        db_post = await asyncio.to_thread(
            fetch_single_post_by_title, session_sql_client, created_post.title
        )
        assert db_post["content"] == created_post.content

    post_page = await home_page.navigate_to_post_by_id(db_post["id"])
    await post_page.should_have_url(f"/post/{db_post['id']}")
    await post_page.should_display_post(
        title=created_post.title,
        content_fragment=created_post.content,
        author_fragment="я",
    )


@allure.feature("Post details")
@allure.story("Voting")
@allure.severity(allure.severity_level.NORMAL)
async def test_post_vote_up_down(
    user_api_created_ui_authorized, make_post_api_created, home_page
):
    user = user_api_created_ui_authorized
    created_post = await make_post_api_created(email=user.email, password=user.password)

    await home_page.reload()
    post_page = await home_page.open_post(title=created_post.title)
    await post_page.post.should_have_score(0)

    async def _vote_and_check(action, expected_score: int):
        await action()
        await expect_contains_text(
            post_page.get_last_toast(),
            "Голос учтён",
            label="Ensure vote toast is shown",
        )
        await post_page.post.should_have_score(expected_score)

    await _vote_and_check(post_page.vote_up, 1)
    await _vote_and_check(post_page.vote_up, 1)
    await _vote_and_check(post_page.vote_down, -1)
    await _vote_and_check(post_page.vote_down, -1)
