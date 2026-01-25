import allure

from models.posts_dto import AddCommentDTO, PublishPostDTO
from utils.assertions.ui_expectations import assert_banned_user_toast


class TestBannedUser:

    # ----------- негативные тесты действий забаненного юзера -----------
    
    @allure.feature("Banned user")
    @allure.story("Cannot publish post")
    @allure.severity(allure.severity_level.CRITICAL)
    async def test_banned_user_cannot_publish_post(self, banned_user_api_created, make_page):
        post_data = PublishPostDTO.random()

        create_post_page = await make_page("create_post", user=banned_user_api_created)
        await create_post_page.open()
        await create_post_page.create_post_model(post_data)

        await assert_banned_user_toast(create_post_page)
        await create_post_page.should_have_url("create-post")

    @allure.feature("Banned user")
    @allure.story("Cannot vote on post")
    @allure.severity(allure.severity_level.NORMAL)
    async def test_banned_user_cannot_vote_on_post(
        self,
        user_api_created,
        make_post_api_created,
        banned_user_api_created,
        make_page,
    ):
        created_post = await make_post_api_created(
            email=user_api_created.email, password=user_api_created.password
        )

        home_page = await make_page("home", user=banned_user_api_created)
        await home_page.open()
        post_page = await home_page.open_post(title=created_post.title)

        initial_score_text = await post_page.post.vote_score.get_locator().inner_text()
        initial_score = int(initial_score_text)

        await post_page.vote_up()
        await assert_banned_user_toast(post_page)
        await post_page.post.should_have_score(initial_score)

    @allure.feature("Banned user")
    @allure.story("Cannot add comment")
    @allure.severity(allure.severity_level.CRITICAL)
    async def test_banned_user_cannot_add_comment(
        self,
        user_api_created,
        make_post_api_created,
        banned_user_api_created,
        make_page,
    ):
        created_post = await make_post_api_created(
            email=user_api_created.email, password=user_api_created.password
        )

        home_page = await make_page("home", user=banned_user_api_created)
        await home_page.open()
        post_page = await home_page.open_post(title=created_post.title)

        initial_count = await post_page.comments.items.count()
        comment_text = AddCommentDTO.random().text
        await post_page.add_comment(comment_text)

        await assert_banned_user_toast(post_page)
        final_count = await post_page.comments.items.count()
        assert final_count == initial_count, f"Expected {initial_count} comments, found {final_count}"

    @allure.feature("Banned user")
    @allure.story("Cannot reply to comment")
    @allure.severity(allure.severity_level.CRITICAL)
    async def test_banned_user_cannot_reply_to_comment(
        self,
        user_api_created,
        make_post_api_created_with_comment,
        banned_user_api_created,
        make_page,
    ):
        post_id, existing_comment = await make_post_api_created_with_comment(
            email=user_api_created.email,
            password=user_api_created.password,
        )

        post_page = await make_page("post", user=banned_user_api_created)
        await post_page.open_by_id(post_id)
        await post_page.comments.should_have_comment_with_text(existing_comment)
        comment = await post_page.comments.get_comment_by_index(0)

        initial_replies = await comment.replies()
        initial_replies_count = len(initial_replies)

        reply_text = AddCommentDTO.random().text
        await comment.reply(reply_text)
        await assert_banned_user_toast(post_page)

        final_replies = await comment.replies()
        final_replies_count = len(final_replies)
        assert final_replies_count == initial_replies_count, (
            f"Expected {initial_replies_count} replies, found {final_replies_count}"
        )
