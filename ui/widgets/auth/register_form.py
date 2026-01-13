import allure
from playwright.async_api import Locator, Page

from ui.page_factory.button import Button
from ui.page_factory.input import Input


class RegisterForm:
    SECTION = "Register form"
    EMAIL_INPUT_TEST_ID = "register-email-input"
    USERNAME_INPUT_TEST_ID = "register-username-input"
    PASSWORD_INPUT_TEST_ID = "register-password-input"
    PASSWORD_CONFIRM_INPUT_TEST_ID = "register-password-confirm-input"
    SUBMIT_BUTTON_TEST_ID = "register-submit-btn"
    FEEDBACK_LOCATOR = ".n-form-item-feedback"

    def __init__(self, page: Page) -> None:
        self.page = page
        self.email_input = Input(
            page,
            locator=page.get_by_test_id(self.EMAIL_INPUT_TEST_ID).locator("input"),
            name="Email",
            section=self.SECTION,
        )
        self.username_input = Input(
            page,
            locator=page.get_by_test_id(self.USERNAME_INPUT_TEST_ID).locator("input"),
            name="Username",
            section=self.SECTION,
        )
        self.password_input = Input(
            page,
            locator=page.get_by_test_id(self.PASSWORD_INPUT_TEST_ID).locator("input"),
            name="Password",
            section=self.SECTION,
        )
        self.password_confirm_input = Input(
            page,
            locator=page.get_by_test_id(self.PASSWORD_CONFIRM_INPUT_TEST_ID).locator("input"),
            name="Password confirmation",
            section=self.SECTION,
        )
        self.submit_button = Button(
            page,
            locator=page.get_by_test_id(self.SUBMIT_BUTTON_TEST_ID),
            name="Submit registration",
            section=self.SECTION,
        )

    async def fill_email(self, email: str) -> None:
        await self.email_input.fill(email, validate_value=True)

    async def fill_username(self, username: str) -> None:
        await self.username_input.fill(username, validate_value=True)

    async def fill_password(self, password: str) -> None:
        await self.password_input.fill(password)

    async def fill_password_confirmation(self, password: str) -> None:
        await self.password_confirm_input.fill(password)

    async def submit(self) -> None:
        await self.submit_button.click()

    async def register(
        self,
        *,
        email: str,
        username: str,
        password: str,
        password_confirmation: str | None = None,
    ) -> None:
        with allure.step("Registering a new user via UI"):
            await self.fill_email(email)
            await self.fill_username(username)
            await self.fill_password(password)
            await self.fill_password_confirmation(password_confirmation or password)
            await self.submit()

    def get_feedback(self) -> Locator:
        return self.page.locator(self.FEEDBACK_LOCATOR).first
