import allure

from utils.assertions.ui_expectations import expect_contains_text


class TestPostDetails:
    # ----------- позитивные тесты -----------

    @allure.feature("Post details")
    @allure.story("Content")
    @allure.severity(allure.severity_level.CRITICAL)
    async def test_post_details_content(
        self, user_api_created, make_post_api_created_with_db, make_page
    ):
        created_post, db_post = await make_post_api_created_with_db(
            email=user_api_created.email, password=user_api_created.password
        )

        home_page = await make_page("home", user=user_api_created)
        await home_page.open()
        post_page = await home_page.navigate_to_post_by_id(db_post["id"])
        await post_page.wait_for_path(f"post/{db_post['id']}")
        await post_page.should_display_post(
            title=created_post.title,
            content_fragment=created_post.content,
            author_fragment="я",
        )

    @allure.feature("Post details")
    @allure.story("Voting")
    @allure.severity(allure.severity_level.NORMAL)
    async def test_post_vote_up_down(self, user_api_created, make_post_api_created, make_page):
        created_post = await make_post_api_created(
            email=user_api_created.email, password=user_api_created.password
        )

        home_page = await make_page("home", user=user_api_created)
        await home_page.open()
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
