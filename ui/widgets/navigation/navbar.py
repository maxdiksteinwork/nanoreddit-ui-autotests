import allure
from playwright.async_api import Page, expect

from ui.page_factory.button import Button
from ui.page_factory.link import Link
from ui.widgets.profile.user_profile_modal import UserProfileModal


class Navbar:
    SECTION = "Navbar"
    LOGO_LOCATOR = "[qa-data='navbar-logo']"
    HOME_LINK_LOCATOR = "role=menuitem[name='Главная']"
    LOGIN_LINK_LOCATOR = "role=menuitem[name='Войти']"
    REGISTER_LINK_LOCATOR = "role=menuitem[name='Регистрация']"
    CREATE_POST_LINK_LOCATOR = "role=menuitem[name='Создать пост']"
    THEME_SWITCH_LOCATOR = "nav .navbar-right [role='switch']"
    LOGOUT_BUTTON_LOCATOR = "role=button[name='Выйти']"
    USER_EMAIL_LINK_LOCATOR = "[qa-data='navbar-user-info']"

    def __init__(self, page: Page) -> None:
        self.page = page
        self.logo = Link(
            page,
            locator=self.LOGO_LOCATOR,
            name="Logo",
            section=self.SECTION,
        )
        self.home_link = Link(
            page,
            locator=self.HOME_LINK_LOCATOR,
            name="Главная",
            section=self.SECTION,
        )
        self.login_link = Link(
            page,
            locator=self.LOGIN_LINK_LOCATOR,
            name="Войти",
            section=self.SECTION,
        )
        self.register_link = Link(
            page,
            locator=self.REGISTER_LINK_LOCATOR,
            name="Регистрация",
            section=self.SECTION,
        )
        self.create_post_link = Link(
            page,
            locator=self.CREATE_POST_LINK_LOCATOR,
            name="Создать пост",
            section=self.SECTION,
        )
        self.theme_switch = Button(
            page,
            locator=self.THEME_SWITCH_LOCATOR,
            name="Theme switch",
            section=self.SECTION,
        )
        self.logout_button = Button(
            page,
            locator=self.LOGOUT_BUTTON_LOCATOR,
            name="Logout",
            section=self.SECTION,
        )
        self.user_email_link = Link(
            page,
            locator=self.USER_EMAIL_LINK_LOCATOR,
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
                with self.user_email_link._action_step(
                    f'Assert link contains "{email}"'
                ):
                    locator = self.user_email_link.get_locator()
                    await expect(locator).to_contain_text(email)

    async def open_profile(self) -> UserProfileModal:
        with allure.step("Open user profile"):
            await self.user_email_link.should_be_visible()
            await self.user_email_link.click()
            modal = UserProfileModal(self.page)
            await modal.should_be_visible()
            return modal
