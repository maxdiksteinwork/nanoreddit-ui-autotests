import allure
import pytest
from playwright.async_api import expect

from ui.pages.home_page import HomePage
from utils.assertions.ui_expectations import (
    assert_user_banned_success,
    assert_user_unbanned_success,
)
from utils.database.database_helpers import wait_for_user_ban_status

# ----------- позитивные тесты -----------


@allure.feature("Admin tools")
@allure.story("Admin profile displays admin role")
@allure.severity(allure.severity_level.MINOR)
async def test_admin_profile_modal_shows_admin_role(
    admin_api_created_ui_authorized, page
):
    navbar = HomePage(page).navbar
    modal = await navbar.open_profile()
    await modal.should_show_role("ROLE_ADMIN")


@allure.feature("Admin tools")
@allure.story("View user profile")
@allure.severity(allure.severity_level.CRITICAL)
async def test_admin_view_user_profile(
    admin_api_created_ui_authorized,
    user_api_created,
    make_post_via_api_and_open_author_modal,
):
    _, modal = await make_post_via_api_and_open_author_modal(user_api_created)
    await modal.should_show_email(user_api_created.email)
    await modal.should_show_username(user_api_created.username)
    await modal.should_show_role("ROLE_USER")


@allure.feature("Admin tools")
@allure.story("Ban user")
@allure.severity(allure.severity_level.CRITICAL)
async def test_admin_ban_user(
    admin_api_created_ui_authorized,
    user_api_created,
    make_post_via_api_and_open_author_modal,
    session_sql_client,
):
    post_page, modal = await make_post_via_api_and_open_author_modal(user_api_created)
    await modal.banned_until_field.should_contain_text("null")
    await modal.ban_button.should_be_enabled()
    await modal.unban_button.should_be_disabled()
    await modal.ban_user(seconds=3600)

    with allure.step("Verify user is banned in database"):
        db_user = await wait_for_user_ban_status(
            session_sql_client,
            email=user_api_created.email,
            banned=True,
        )
        assert db_user["banned_until"], "User is not banned in DB"

    await assert_user_banned_success(post_page)
    await modal.ban_button.should_be_disabled()
    await modal.unban_button.should_be_enabled()
    await modal.banned_until_field.should_not_contain_text("null")


@allure.feature("Admin tools")
@allure.story("Ban another admin")
@allure.severity(allure.severity_level.NORMAL)
async def test_admin_ban_another_admin(
    admin_api_created_ui_authorized,
    user_api_created,
    make_admin_api_created,
    make_post_via_api_and_open_author_modal,
):
    admin_user = make_admin_api_created(user=user_api_created)

    post_page, modal = await make_post_via_api_and_open_author_modal(admin_user)
    await modal.should_show_role("ROLE_ADMIN")
    await modal.ban_user(seconds=3600)
    await assert_user_banned_success(post_page)


@allure.feature("Admin tools")
@allure.story("Unban user")
@allure.severity(allure.severity_level.CRITICAL)
async def test_admin_unban_user(
    admin_api_created_ui_authorized,
    user_api_created,
    make_post_via_api_and_open_author_modal,
    open_author_modal,
    session_sql_client,
):
    post_page, modal = await make_post_via_api_and_open_author_modal(user_api_created)
    await modal.ban_user(seconds=3600)
    await assert_user_banned_success(post_page)
    await modal.close()

    modal = await open_author_modal(post_page)
    await modal.ban_button.should_be_disabled()
    await modal.unban_button.should_be_enabled()
    await modal.unban_user()
    await assert_user_unbanned_success(post_page)

    with allure.step("Verify user is unbanned in database"):
        db_user = await wait_for_user_ban_status(
            session_sql_client,
            email=user_api_created.email,
            banned=False,
        )
        assert db_user["banned_until"] is None, "User should be unbanned in DB"


# ----------- негативные тесты -----------


@allure.feature("Admin tools")
@allure.story("Ban already banned user")
@allure.severity(allure.severity_level.NORMAL)
async def test_admin_ban_already_banned_user(
    admin_api_created_ui_authorized,
    make_post_via_api_and_open_author_modal,
    open_author_modal,
    user_api_created,
):
    post_page, modal = await make_post_via_api_and_open_author_modal(user_api_created)
    await modal.ban_user(seconds=3600)
    await assert_user_banned_success(post_page)
    await modal.close()
    modal = await open_author_modal(post_page)
    await modal.ban_button.should_be_disabled()
    await modal.unban_button.should_be_enabled()


@allure.feature("Admin tools")
@allure.story("Ban with invalid duration")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.parametrize("duration", [0, -10, "10abc"])
async def test_admin_ban_invalid_duration(
    admin_api_created_ui_authorized,
    user_api_created,
    make_post_via_api_and_open_author_modal,
    duration,
):
    post_page, modal = await make_post_via_api_and_open_author_modal(user_api_created)
    await modal.ban_user(raw_input=str(duration))
    if isinstance(duration, str):
        await assert_user_banned_success(post_page)
        value = await modal.ban_duration_input.get_locator().input_value()
        assert value.isdigit(), "Duration input should contain numeric substring only"
    else:
        await assert_user_banned_success(post_page)
        await expect(modal.ban_duration_input.get_locator()).to_have_value("1")
