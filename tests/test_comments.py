import asyncio

import allure
import pytest
from playwright.async_api import expect

from models.posts_dto import AddCommentDTO, ReplyCommentDTO
from utils.assertions.ui_expectations import (
    assert_comment_added_success,
    assert_comment_validation_error,
    assert_reply_added_success,
)
from utils.database.database_helpers import (
    count_comments_in_db,
    fetch_single_post_by_title,
    wait_for_comment_in_db,
)

# ----------- позитивные тесты добавления комментария к посту -----------


@allure.feature("Post comments")
@allure.story("Add comment")
@allure.severity(allure.severity_level.CRITICAL)
async def test_add_comment(
    user_api_created_ui_authorized, make_post_api_created, session_sql_client, home_page
):
    user = user_api_created_ui_authorized
    created_post = await make_post_api_created(email=user.email, password=user.password)

    db_post = await asyncio.to_thread(
        fetch_single_post_by_title, session_sql_client, created_post.title
    )
    post_id = db_post["id"]

    post_page = await home_page.navigate_to_post_by_id(post_id)
    await post_page.should_have_url(f"/post/{post_id}")

    comment_text = AddCommentDTO.random().text
    await post_page.add_comment(comment_text)
    await assert_comment_added_success(post_page)
    await post_page.should_have_comment(comment_text)

    with allure.step("Verify comment in database"):
        db_comment = await wait_for_comment_in_db(
            session_sql_client,
            post_id=post_id,
            text=comment_text,
        )
        assert db_comment["parent_id"] is None
        assert db_comment["text"] == comment_text


@pytest.mark.parametrize(
    "comment_text",
    ["A", "A" * 255],
    ids=["min", "max"],
)
@allure.feature("Post comments")
@allure.story("Add comment | boundary valid values")
@allure.severity(allure.severity_level.NORMAL)
async def test_add_comment_boundary_valid(
    user_api_created_ui_authorized,
    make_post_api_created,
    home_page,
    comment_text,
):
    user = user_api_created_ui_authorized
    created_post = await make_post_api_created(email=user.email, password=user.password)

    await home_page.reload()
    post_page = await home_page.open_post(title=created_post.title)
    await post_page.add_comment(comment_text)
    await assert_comment_added_success(post_page)
    await post_page.should_have_comment(comment_text)


@allure.feature("Post comments")
@allure.story("Add comment | special symbols")
@allure.severity(allure.severity_level.NORMAL)
async def test_add_comment_special_symbols(
    user_api_created_ui_authorized,
    make_post_api_created,
    home_page,
):
    user = user_api_created_ui_authorized
    created_post = await make_post_api_created(email=user.email, password=user.password)

    await home_page.reload()
    post_page = await home_page.open_post(title=created_post.title)

    special_text = "🔥 Привет <b>друг</b> & welcome!"
    await post_page.add_comment(special_text)
    await assert_comment_added_success(post_page)
    await post_page.should_have_comment(special_text)


# ----------- негативные тесты добавления комментария к посту -----------


@pytest.mark.parametrize(
    ("comment_text", "expect_disabled"),
    [
        ("", True),
        ("A" * 256, False),
    ],
    ids=["empty", "too_long"],
)
@allure.feature("Post comments")
@allure.story("Add comment | boundary invalid values")
@allure.severity(allure.severity_level.NORMAL)
async def test_add_comment_boundary_invalid(
    user_api_created_ui_authorized,
    make_post_api_created,
    home_page,
    comment_text,
    expect_disabled,
):
    user = user_api_created_ui_authorized
    created_post = await make_post_api_created(email=user.email, password=user.password)

    await home_page.reload()
    post_page = await home_page.open_post(title=created_post.title)

    await post_page.comments.form.fill(comment_text)
    if expect_disabled:
        await post_page.comments.form.submit_button.should_be_disabled()
    else:
        await post_page.comments.form.submit_button.should_be_enabled()
        await post_page.comments.form.submit()
        await assert_comment_validation_error(post_page)
        await expect(
            post_page.comments.items.filter(has_text=comment_text)
        ).to_have_count(0)


# ----------- позитивные тесты добавления ответа к комментарию -----------


@allure.feature("Post comments")
@allure.story("Reply comment")
@allure.severity(allure.severity_level.CRITICAL)
async def test_reply_comment(
    user_api_created_ui_authorized, make_post_api_created, session_sql_client, home_page
):
    user = user_api_created_ui_authorized
    created_post = await make_post_api_created(email=user.email, password=user.password)

    db_post = await asyncio.to_thread(
        fetch_single_post_by_title, session_sql_client, created_post.title
    )
    post_id = db_post["id"]

    post_page = await home_page.navigate_to_post_by_id(post_id)
    root_comment_text = AddCommentDTO.random().text
    await post_page.add_comment(root_comment_text)
    await assert_comment_added_success(post_page)
    await post_page.should_have_comment(root_comment_text)

    db_parent = await wait_for_comment_in_db(
        session_sql_client, post_id=post_id, text=root_comment_text
    )
    parent_comment_id = db_parent["id"]

    comment_item = await post_page.comments.get_comment_by_index(0)
    await comment_item.should_contain_text(root_comment_text)

    reply_text = ReplyCommentDTO.random().text
    await comment_item.reply(reply_text)
    await assert_reply_added_success(post_page)

    reply_item = await comment_item.wait_for_reply_with_text(reply_text)
    assert reply_item, "Reply not found in UI"

    db_reply = await wait_for_comment_in_db(
        session_sql_client,
        post_id=post_id,
        text=reply_text,
        parent_comment_id=parent_comment_id,
    )
    assert db_reply["parent_id"] == parent_comment_id


@allure.feature("Post comments")
@allure.story("Reply comment | nested replies")
@allure.severity(allure.severity_level.NORMAL)
async def test_reply_to_reply_nested(
    user_api_created_ui_authorized, make_post_api_created, home_page
):
    user = user_api_created_ui_authorized
    created_post = await make_post_api_created(email=user.email, password=user.password)

    await home_page.reload()
    post_page = await home_page.open_post(title=created_post.title)

    root_comment_text = AddCommentDTO.random().text
    await post_page.add_comment(root_comment_text)
    await assert_comment_added_success(post_page)
    await post_page.should_have_comment(root_comment_text)

    comment_item = await post_page.comments.get_comment_by_index(0)
    await comment_item.should_contain_text(root_comment_text)

    first_reply = ReplyCommentDTO.random().text
    await comment_item.reply(first_reply)
    await assert_reply_added_success(post_page)
    lvl1_item = await comment_item.wait_for_reply_with_text(first_reply)

    second_reply = ReplyCommentDTO.random().text
    await lvl1_item.reply(second_reply)
    await assert_reply_added_success(post_page)
    await lvl1_item.wait_for_reply_with_text(second_reply)


@allure.feature("Post comments")
@allure.story("Reply comment | special symbols")
@allure.severity(allure.severity_level.NORMAL)
async def test_reply_special_symbols(
    user_api_created_ui_authorized, make_post_api_created, home_page
):
    user = user_api_created_ui_authorized
    created_post = await make_post_api_created(email=user.email, password=user.password)

    await home_page.reload()
    post_page = await home_page.open_post(title=created_post.title)

    root_comment_text = AddCommentDTO.random().text
    await post_page.add_comment(root_comment_text)
    await assert_comment_added_success(post_page)
    await post_page.should_have_comment(root_comment_text)

    comment_item = await post_page.comments.get_comment_by_index(0)
    await comment_item.should_contain_text(root_comment_text)

    reply_text = "🔥 Привет <b>друг</b> & welcome!"
    await comment_item.reply(reply_text)
    await assert_reply_added_success(post_page)
    await comment_item.wait_for_reply_with_text(reply_text)


@pytest.mark.parametrize(
    "reply_text",
    ["R", "R" * 255],
    ids=["min", "max"],
)
@allure.feature("Post comments")
@allure.story("Reply comment | boundary valid values")
@allure.severity(allure.severity_level.NORMAL)
async def test_reply_comment_boundary_valid(
    user_api_created_ui_authorized, make_post_api_created, home_page, reply_text
):
    user = user_api_created_ui_authorized
    created_post = await make_post_api_created(email=user.email, password=user.password)

    await home_page.reload()
    post_page = await home_page.open_post(title=created_post.title)

    root_comment_text = AddCommentDTO.random().text
    await post_page.add_comment(root_comment_text)
    await assert_comment_added_success(post_page)
    await post_page.should_have_comment(root_comment_text)

    comment_item = await post_page.comments.get_comment_by_index(0)
    await comment_item.should_contain_text(root_comment_text)

    await comment_item.reply(reply_text)
    await assert_reply_added_success(post_page)
    await comment_item.wait_for_reply_with_text(reply_text)


# ----------- негативные тесты добавления ответа к комментарию -----------


@pytest.mark.parametrize(
    ("reply_text", "expect_disabled"),
    [
        ("", True),
        ("R" * 256, False),
    ],
    ids=["empty", "too_long"],
)
@allure.feature("Post comments")
@allure.story("Reply comment | boundary invalid values")
@allure.severity(allure.severity_level.NORMAL)
async def test_reply_comment_boundary_invalid(
    user_api_created_ui_authorized,
    make_post_api_created,
    home_page,
    reply_text,
    expect_disabled,
):
    user = user_api_created_ui_authorized
    created_post = await make_post_api_created(email=user.email, password=user.password)

    await home_page.reload()
    post_page = await home_page.open_post(title=created_post.title)

    root_comment_text = AddCommentDTO.random().text
    await post_page.add_comment(root_comment_text)
    await assert_comment_added_success(post_page)
    await post_page.should_have_comment(root_comment_text)

    comment_item = await post_page.comments.get_comment_by_index(0)
    await comment_item.should_contain_text(root_comment_text)
    initial_replies = len(await comment_item.replies())

    await comment_item.click_reply()
    await comment_item.reply_textarea.fill(reply_text, validate_value=True)

    if expect_disabled:
        await comment_item.reply_submit.should_be_disabled()
    else:
        await comment_item.reply_submit.should_be_enabled()
        await comment_item.reply_submit.click()
        await assert_comment_validation_error(post_page)

    final_replies = len(await comment_item.replies())
    assert final_replies == initial_replies, "Reply count should not change"


# ----------- дополнительные UX-проверки -----------


@allure.feature("Post comments")
@allure.story("Add comment | interaction resilience")
@allure.severity(allure.severity_level.NORMAL)
async def test_add_comment_submit_double_click(
    user_api_created_ui_authorized, make_post_api_created, session_sql_client, home_page
):
    user = user_api_created_ui_authorized
    created_post = await make_post_api_created(email=user.email, password=user.password)

    db_post = await asyncio.to_thread(
        fetch_single_post_by_title, session_sql_client, created_post.title
    )
    post_id = db_post["id"]

    post_page = await home_page.navigate_to_post_by_id(post_id)
    comment_text = AddCommentDTO.random().text
    await post_page.comments.form.fill(comment_text)
    await post_page.comments.form.submit_button.should_be_enabled()
    await post_page.comments.form.submit_button.double_click()

    count = await asyncio.to_thread(
        count_comments_in_db,
        session_sql_client,
        post_id=post_id,
        text=comment_text,
    )
    assert count == 1, "Double click created duplicate comments in DB"
    await assert_comment_added_success(post_page)
    await post_page.should_have_comment(comment_text)


@allure.feature("Post comments")
@allure.story("Reply comment | interaction resilience")
@allure.severity(allure.severity_level.NORMAL)
async def test_reply_comment_submit_double_click(
    user_api_created_ui_authorized, make_post_api_created, session_sql_client, home_page
):
    user = user_api_created_ui_authorized
    created_post = await make_post_api_created(email=user.email, password=user.password)

    db_post = await asyncio.to_thread(
        fetch_single_post_by_title, session_sql_client, created_post.title
    )
    post_id = db_post["id"]

    post_page = await home_page.navigate_to_post_by_id(post_id)
    root_comment_text = AddCommentDTO.random().text
    await post_page.add_comment(root_comment_text)
    await assert_comment_added_success(post_page)
    await post_page.should_have_comment(root_comment_text)

    db_parent = await wait_for_comment_in_db(
        session_sql_client,
        post_id=post_id,
        text=root_comment_text,
    )
    parent_comment_id = db_parent["id"]

    comment_item = await post_page.comments.get_comment_by_index(0)
    await comment_item.should_contain_text(root_comment_text)

    reply_text = ReplyCommentDTO.random().text
    await comment_item.click_reply()
    await comment_item.reply_textarea.fill(reply_text, validate_value=True)
    await comment_item.reply_submit.should_be_enabled()
    await comment_item.reply_submit.double_click()

    count = await asyncio.to_thread(
        count_comments_in_db,
        session_sql_client,
        post_id=post_id,
        text=reply_text,
        parent_comment_id=parent_comment_id,
    )
    assert count == 1, "Double click created duplicate replies in DB"
    await assert_reply_added_success(post_page)
    await comment_item.wait_for_reply_with_text(reply_text)
