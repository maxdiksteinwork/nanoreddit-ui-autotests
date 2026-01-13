import asyncio

import allure
from playwright.async_api import expect

from utils.database.database_helpers import fetch_single_user

# ----------- позитивные тесты -----------


@allure.feature("Profile modal")
@allure.story("Display user info")
@allure.severity(allure.severity_level.NORMAL)
async def test_profile_modal_shows_user(
    user_api_created, session_sql_client, authenticated_home_page
):
    user = user_api_created
    await authenticated_home_page.open()

    with allure.step("Fetch user data from database"):
        db_user = await asyncio.to_thread(
            fetch_single_user,
            session_sql_client,
            user.email,
            columns="id::text, email, username, role",
        )

    modal = await authenticated_home_page.navbar.open_profile()

    with allure.step("Verify all user information is displayed correctly"):
        await modal.should_show_email(db_user["email"])
        await modal.should_show_username(db_user["username"])
        await modal.should_show_id(db_user["id"])
        await modal.should_show_role(db_user["role"])


@allure.feature("Profile modal")
@allure.story("Close interaction")
@allure.severity(allure.severity_level.MINOR)
async def test_profile_modal_closes(user_api_created, authenticated_home_page):
    user = user_api_created
    await authenticated_home_page.open()

    modal = await authenticated_home_page.navbar.open_profile()

    with allure.step("Close modal using close button"):
        await modal.close()
        await expect(modal.dialog).to_be_hidden()
        await authenticated_home_page.navbar.should_be_user_nav(email=user.email)

    with allure.step("Reopen modal and close by clicking overlay"):
        modal = await authenticated_home_page.navbar.open_profile()
        await authenticated_home_page.page.mouse.click(5, 5)
        await expect(modal.dialog).to_be_hidden()
        await authenticated_home_page.navbar.should_be_user_nav(email=user.email)

    with allure.step("Reopen modal and close using 'Space' key"):
        modal = await authenticated_home_page.navbar.open_profile()
        await authenticated_home_page.page.keyboard.press("Space")
        await expect(modal.dialog).to_be_hidden()
        await authenticated_home_page.navbar.should_be_user_nav(email=user.email)
