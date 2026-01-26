import allure
from playwright.async_api import expect


class TestProfileModal:
    # ----------- позитивные тесты -----------

    @allure.feature("Profile modal")
    @allure.story("Display user info")
    @allure.severity(allure.severity_level.NORMAL)
    async def test_profile_modal_shows_user(self, user_api_created, db_user_api_created, make_page):
        home_page = await make_page("home", user=user_api_created)
        await home_page.open()
        db_user = db_user_api_created

        modal = await home_page.navbar.open_profile()

        with allure.step("Verify all user information is displayed correctly"):
            await modal.should_show_email(db_user["email"])
            await modal.should_show_username(db_user["username"])
            await modal.should_show_id(db_user["id"])
            await modal.should_show_role(db_user["role"])

    @allure.feature("Profile modal")
    @allure.story("Close interaction")
    @allure.severity(allure.severity_level.MINOR)
    async def test_profile_modal_closes(self, user_api_created, make_page):
        user = user_api_created
        home_page = await make_page("home", user=user_api_created)
        await home_page.open()

        modal = await home_page.navbar.open_profile()

        with allure.step("Close modal using close button"):
            await modal.close()
            await expect(modal.dialog).to_be_hidden()
            await home_page.navbar.should_be_user_nav(email=user.email)

        with allure.step("Reopen modal and close by clicking overlay"):
            modal = await home_page.navbar.open_profile()
            await home_page.page.mouse.click(5, 5)
            await expect(modal.dialog).to_be_hidden()
            await home_page.navbar.should_be_user_nav(email=user.email)

        with allure.step("Reopen modal and close using 'Space' key"):
            modal = await home_page.navbar.open_profile()
            await home_page.page.keyboard.press("Space")
            await expect(modal.dialog).to_be_hidden()
            await home_page.navbar.should_be_user_nav(email=user.email)
