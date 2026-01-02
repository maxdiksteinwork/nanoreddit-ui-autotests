import allure
from playwright.async_api import Page

from ui.page_factory.button import Button
from ui.page_factory.input import Input


class LoginForm:
    SECTION = "Login form"
    EMAIL_INPUT_LOCATOR = "[qa-data='login-email-input'] input"
    PASSWORD_INPUT_LOCATOR = "[qa-data='login-password-input'] input"
    SUBMIT_BUTTON_LOCATOR = "[qa-data='login-submit-btn']"
    PASSWORD_INPUT_CONTAINER_LOCATOR = "[qa-data='login-password-input']"

    def __init__(self, page: Page) -> None:
        self.email_input = Input(
            page,
            locator=self.EMAIL_INPUT_LOCATOR,
            name="Email",
            section=self.SECTION,
        )
        self.password_input = Input(
            page,
            locator=self.PASSWORD_INPUT_LOCATOR,
            name="Password",
            section=self.SECTION,
        )
        self.submit_button = Button(
            page,
            locator=self.SUBMIT_BUTTON_LOCATOR,
            name="Submit login",
            section=self.SECTION,
        )

    async def fill_email(self, email: str) -> None:
        await self.email_input.fill(email, validate_value=True)

    async def fill_password(self, password: str) -> None:
        await self.password_input.fill(password)

    async def submit(self) -> None:
        await self.submit_button.click()

    async def login(self, *, email: str, password: str) -> None:
        with allure.step(f"Logging in as {email}"):
            await self.fill_email(email)
            await self.fill_password(password)
            await self.submit()
