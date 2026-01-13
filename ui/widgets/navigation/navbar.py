import allure
from playwright.async_api import Page, expect

from ui.page_factory.button import Button
from ui.page_factory.link import Link
from ui.widgets.profile.user_profile_modal import UserProfileModal


class Navbar:
    SECTION = "Navbar"
    LOGO_TEST_ID = "navbar-logo"
    USER_EMAIL_LINK_TEST_ID = "navbar-user-info"
    LOGOUT_BUTTON_TEST_ID = "navbar-logout-btn"

    def __init__(self, page: Page) -> None:
        self.page = page
        self.logo = Link(
            page,
            locator=page.get_by_test_id(self.LOGO_TEST_ID),
            name="Logo",
            section=self.SECTION,
        )
        self.home_link = Link(
            page,
            locator=page.get_by_role("menuitem", name="Главная"),
            name="Главная",
            section=self.SECTION,
        )
        self.login_link = Link(
            page,
            locator=page.get_by_role("menuitem", name="Войти"),
            name="Войти",
            section=self.SECTION,
        )
        self.register_link = Link(
            page,
            locator=page.get_by_role("menuitem", name="Регистрация"),
            name="Регистрация",
            section=self.SECTION,
        )
        self.create_post_link = Link(
            page,
            locator=page.get_by_role("menuitem", name="Создать пост"),
            name="Создать пост",
            section=self.SECTION,
        )
        self.theme_switch = Button(
            page,
            locator=page.locator(".navbar-right").get_by_role("switch"),
            name="Theme switch",
            section=self.SECTION,
        )
        self.logout_button = Button(
            page,
            locator=page.get_by_test_id(self.LOGOUT_BUTTON_TEST_ID),
            name="Logout",
            section=self.SECTION,
        )
        self.user_email_link = Link(
            page,
            locator=page.get_by_test_id(self.USER_EMAIL_LINK_TEST_ID),
            name="User email",
            section=self.SECTION,
        )

    async def go_home(self) -> None:
        await self.home_link.click()

    async def open_login(self) -> None:
        await self.login_link.click()

    async def open_register(self) -> None:
        await self.register_link.click()

    async def toggle_theme(self) -> None:
        await self.theme_switch.click()

    async def should_be_visible(self) -> None:
        with allure.step("Checking that navbar is visible"):
            await expect(self.page.locator("nav")).to_be_visible()

    async def should_be_guest_nav(self) -> None:
        with allure.step("Ensure guest navigation is visible"):
            await self.login_link.should_be_visible()
            await self.register_link.should_be_visible()
            await expect(self.logout_button.get_locator()).to_have_count(0)
            await expect(self.create_post_link.get_locator()).to_have_count(0)

    async def should_be_user_nav(self, *, email: str | None = None) -> None:
        with allure.step("Ensure authenticated navigation is visible"):
            await self.create_post_link.should_be_visible()
            await self.logout_button.should_be_visible()
            await self.user_email_link.should_be_visible()
            if email:
                with self.user_email_link._action_step(f'Assert link contains "{email}"'):
                    locator = self.user_email_link.get_locator()
                    await expect(locator).to_contain_text(email)

    async def open_profile(self) -> UserProfileModal:
        with allure.step("Open user profile"):
            await self.user_email_link.should_be_visible()
            await self.user_email_link.click()
            modal = UserProfileModal(self.page)
            await modal.should_be_visible()
            return modal
