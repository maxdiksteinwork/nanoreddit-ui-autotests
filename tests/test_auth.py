import asyncio

import allure
import pytest
from faker import Faker
from playwright.async_api import expect

from models.auth_dto import LoginUserDTO, RegisterUserDTO
from utils.assertions.ui_expectations import (
    assert_login_error,
    assert_login_success,
    assert_registration_error,
    assert_registration_success,
    expect_contains_text,
)
from utils.data_generators.fake_credentials import (
    fake_email,
    fake_password,
    fake_username,
)
from utils.database.database_helpers import (
    delete_user_by_email,
    fetch_single_user,
    get_table_count,
)

faker = Faker()
EDGE_CASE_PASSWORD = "Passw0rd"


def _email_with_lengths(local_len: int, domain_before_dot: int, domain_after_dot: int) -> str:
    local_part = faker.pystr(min_chars=local_len, max_chars=local_len)
    domain_before = faker.pystr(min_chars=domain_before_dot, max_chars=domain_before_dot).lower()
    domain_after = faker.pystr(min_chars=domain_after_dot, max_chars=domain_after_dot).lower()
    return f"{local_part}@{domain_before}.{domain_after}"


def _password_with_length(length: int) -> str:
    base = "Aa1"
    if length <= len(base):
        return base[:length]
    return base + "0" * (length - len(base))


async def _assert_password_visibility_toggle(
    page, test_id: str, *, step_name: str | None = None
) -> None:
    step_name = step_name or "Verify password visibility toggle"
    with allure.step(step_name):
        container = page.get_by_test_id(test_id)
        password_input = container.locator("input")
        eye_toggle = container.locator(".n-input__eye").first
        await expect(password_input).to_have_attribute("type", "password")
        await expect(eye_toggle).to_be_visible()
        await eye_toggle.click()
        await expect(password_input).to_have_attribute("type", "text")
        await eye_toggle.click()
        await expect(password_input).to_have_attribute("type", "password")


# ----------- позитивные тесты register и login -----------


@allure.feature("Auth UI")
@allure.story("Register user")
@allure.severity(allure.severity_level.CRITICAL)
async def test_register_user(register_page, session_sql_client):
    random_user = RegisterUserDTO.random()
    await register_page.open()
    await register_page.register_user_model(random_user)
    await assert_registration_success(register_page)

    with allure.step("Validate registered user in DB"):
        db_user = await asyncio.to_thread(
            fetch_single_user,
            session_sql_client,
            random_user.email,
            columns="id, username, email",
        )
        assert db_user["username"] == random_user.username
        assert db_user["email"] == random_user.email


@allure.feature("Auth UI")
@allure.story("Register and login")
@allure.severity(allure.severity_level.CRITICAL)
async def test_register_and_login(register_page, login_page):
    random_user = RegisterUserDTO.random()
    await register_page.open()
    await register_page.register_user_model(random_user)
    await assert_registration_success(register_page)

    login_user = LoginUserDTO.from_register(random_user)
    await login_page.open()
    await login_page.login_user_model(login_user)
    await assert_login_success(login_page, expected_email=login_user.email)


@allure.feature("Auth UI")
@allure.story("Register and login with problematic password")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.xfail(reason="BUG: UI login отклоняет пароль без спецсимволов @#$%^&+=", strict=False)
async def test_register_and_login_with_problematic_password(register_page, login_page):
    user = RegisterUserDTO(
        email=fake_email(),
        username=fake_username(),
        password=EDGE_CASE_PASSWORD,
        passwordConfirmation=EDGE_CASE_PASSWORD,
    )

    await register_page.open()
    await register_page.register_user_model(user)
    await assert_registration_success(register_page)

    login_user = LoginUserDTO.from_register(user)
    await login_page.open()
    await login_page.login_user_model(login_user)
    await assert_login_success(login_page, expected_email=login_user.email)


# ----------- граничные значения register -----------


@allure.feature("Auth UI")
@allure.story("Register user | boundary values")
@allure.severity(allure.severity_level.NORMAL)
async def test_register_with_min_values(register_page, session_sql_client):
    minimal_user = RegisterUserDTO.minimal()
    await delete_user_by_email(session_sql_client, minimal_user.email)
    await register_page.open()
    try:
        await register_page.register_user_model(minimal_user)
        await assert_registration_success(register_page)
    finally:
        await delete_user_by_email(session_sql_client, minimal_user.email)


@allure.feature("Auth UI")
@allure.story("Register user | boundary values")
@allure.severity(allure.severity_level.NORMAL)
async def test_register_with_max_values(register_page):
    await register_page.open()
    max_email = _email_with_lengths(64, 63, 63)
    max_username = faker.unique.pystr(min_chars=255, max_chars=255)
    max_password = _password_with_length(72)
    user = RegisterUserDTO(
        email=max_email,
        username=max_username,
        password=max_password,
        passwordConfirmation=max_password,
    )
    await register_page.register_user_model(user)
    await assert_registration_success(register_page)


# ----------- негативные тесты register -----------


@allure.feature("Auth UI")
@allure.story("Register user | validation errors")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.parametrize(
    "email_len_local,email_len_domain_before,email_len_domain_after,username_len,password_len",
    [
        (65, 63, 63, 255, 72),
        (64, 64, 63, 255, 72),
        (64, 63, 64, 255, 72),
        (64, 63, 63, 256, 72),
        (64, 63, 63, 255, 73),
    ],
    ids=[
        "email_local_part_too_long",
        "email_domain_before_dot_too_long",
        "email_domain_after_dot_too_long",
        "username_too_long",
        "password_too_long",
    ],
)
async def test_register_with_exceeding_max_values(
    register_page,
    email_len_local,
    email_len_domain_before,
    email_len_domain_after,
    username_len,
    password_len,
):
    await register_page.open()
    email = _email_with_lengths(email_len_local, email_len_domain_before, email_len_domain_after)
    username = faker.pystr(min_chars=username_len, max_chars=username_len)
    password = _password_with_length(password_len)

    await register_page.register_user(
        email=email,
        username=username,
        password=password,
        password_confirmation=password,
    )
    await assert_registration_error(register_page)


@allure.feature("Auth UI")
@allure.story("Register user | validation errors")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.parametrize(
    "empty",
    [
        "email",
        "username",
        "password",
        "password_confirmation",
        "all",
    ],
    ids=[
        "empty_email",
        "empty_username",
        "empty_password",
        "empty_password_confirmation",
        "empty_all",
    ],
)
async def test_register_with_empty_fields(register_page, empty):
    await register_page.open()
    user = RegisterUserDTO.random()
    email = "" if empty in {"email", "all"} else user.email
    username = "" if empty in {"username", "all"} else user.username
    password = "" if empty in {"password", "all"} else user.password
    password_confirmation = (
        "" if empty in {"password_confirmation", "all"} else user.passwordConfirmation
    )

    await register_page.form.fill_email(email)
    await register_page.form.fill_username(username)
    await register_page.form.fill_password(password)
    await register_page.form.fill_password_confirmation(password_confirmation)
    await register_page.form.submit()
    await assert_registration_error(register_page)


@allure.feature("Auth UI")
@allure.story("Register user | validation errors")
@allure.severity(allure.severity_level.NORMAL)
async def test_register_with_mismatched_passwords(register_page):
    user = RegisterUserDTO.random()
    user.passwordConfirmation = fake_password()
    await register_page.open()
    await register_page.register_user_model(user)
    await assert_registration_error(register_page)


@allure.feature("Auth UI")
@allure.story("Register user | validation errors")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.parametrize(
    "invalid_email",
    [
        "plainaddress",
        "missingatsign.com",
        "@missinglocal.com",
        "local@.com",
        "local@domain",
        "local@domain..com",
    ],
)
async def test_register_with_invalid_email(register_page, invalid_email, session_sql_client):
    await register_page.open()
    user = RegisterUserDTO.random()
    user.email = invalid_email
    try:
        await register_page.register_user(
            email=user.email,
            username=user.username,
            password=user.password,
            password_confirmation=user.passwordConfirmation,
        )
    finally:
        await delete_user_by_email(session_sql_client, user.email)
    with allure.step("Validate email validation error UI state"):
        email_feedback = register_page.form.get_feedback()
        await expect(email_feedback).to_be_visible()
        await expect_contains_text(
            email_feedback, "email", label="Ensure email feedback contains 'email' hint"
        )
        await register_page.should_have_url("register")


@allure.feature("Auth UI")
@allure.story("Register user | validation errors")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.parametrize("field", ["email", "username"])
async def test_register_with_existing_email_or_username(register_page, user_api_created, field):
    user = RegisterUserDTO.random()
    await register_page.open()
    if field == "email":
        user.email = user_api_created.email
    else:
        user.username = user_api_created.username

    await register_page.register_user_model(user)
    await assert_registration_error(register_page)


@allure.feature("Auth UI")
@allure.story("Register user | validation errors")
@allure.severity(allure.severity_level.NORMAL)
async def test_register_email_case_insensitive(register_page, user_api_created: RegisterUserDTO):
    user = RegisterUserDTO.random()
    user.email = user_api_created.email.upper()
    await register_page.open()
    await register_page.register_user_model(user)
    await assert_registration_error(register_page)


@allure.feature("Auth UI")
@allure.story("Register user | validation errors")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.parametrize(
    "invalid_password",
    [
        "short",
        "alllowercase",
        "ALLUPPERCASE",
        "12345678",
        "Password",
        "Pass word1",
    ],
)
async def test_register_with_invalid_passwords(register_page, invalid_password):
    user = RegisterUserDTO.random()
    user.password = invalid_password
    user.passwordConfirmation = invalid_password
    await register_page.open()
    await register_page.register_user_model(user)
    await assert_registration_error(register_page)


# ----------- негативные тесты login -----------


@allure.feature("Auth UI")
@allure.story("Login | authentication errors")
@allure.severity(allure.severity_level.CRITICAL)
async def test_login_with_wrong_password(login_page, user_api_created: RegisterUserDTO):
    await login_page.open()
    await login_page.form.fill_email(user_api_created.email)
    await login_page.form.fill_password(fake_password())
    await login_page.form.submit()
    await assert_login_error(login_page)


@allure.feature("Auth UI")
@allure.story("Login | authentication errors")
@allure.severity(allure.severity_level.NORMAL)
async def test_login_with_nonexistent_email(login_page):
    await login_page.open()
    await login_page.form.fill_email(fake_email())
    await login_page.form.fill_password(fake_password())
    await login_page.form.submit()
    await assert_login_error(login_page)


@allure.feature("Auth UI")
@allure.story("Login | validation errors")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.parametrize(
    "empty",
    [
        "email",
        "password",
        "all",
    ],
    ids=[
        "empty_email",
        "empty_password",
        "empty_all",
    ],
)
async def test_login_with_empty_fields(login_page, empty):
    await login_page.open()
    email = "" if empty in {"email", "all"} else fake_email()
    password = "" if empty in {"password", "all"} else fake_password()

    await login_page.form.fill_email(email)
    await login_page.form.fill_password(password)
    await login_page.form.submit()
    await assert_login_error(login_page)


# ----------- дополнительные UX-проверки -----------


@allure.feature("Auth UI")
@allure.story("Register user | password visibility")
@allure.severity(allure.severity_level.MINOR)
async def test_register_password_visibility_toggle(register_page):
    await register_page.open()
    await register_page.form.fill_password("user.password")
    await register_page.form.fill_password_confirmation("user.passwordConfirmation")

    await _assert_password_visibility_toggle(
        register_page.page,
        register_page.form.PASSWORD_INPUT_TEST_ID,
        step_name="Verify password field visibility toggle",
    )
    await _assert_password_visibility_toggle(
        register_page.page,
        register_page.form.PASSWORD_CONFIRM_INPUT_TEST_ID,
        step_name="Verify password confirmation field visibility toggle",
    )


@allure.feature("Auth UI")
@allure.story("Login | password visibility")
@allure.severity(allure.severity_level.MINOR)
async def test_login_password_visibility_toggle(login_page):
    await login_page.open()
    await login_page.form.fill_password("user.password")

    await _assert_password_visibility_toggle(
        login_page.page,
        login_page.form.PASSWORD_INPUT_TEST_ID,
        step_name="Verify password field visibility toggle",
    )


@allure.feature("Auth UI")
@allure.story("Register user | interaction resilience")
@allure.severity(allure.severity_level.NORMAL)
async def test_register_submit_double_click(register_page, session_sql_client):
    user = RegisterUserDTO.random()
    await register_page.open()
    await register_page.form.fill_email(user.email)
    await register_page.form.fill_username(user.username)
    await register_page.form.fill_password(user.password)
    await register_page.form.fill_password_confirmation(user.password)
    await register_page.form.submit_button.double_click()
    await assert_registration_success(register_page)

    count = await asyncio.to_thread(
        get_table_count,
        session_sql_client,
        "users",
        where_clause="WHERE email = %s",
        params=(user.email,),
    )
    assert count == 1, "Double click created duplicate users"


@allure.feature("Auth UI")
@allure.story("Login | interaction resilience")
@allure.severity(allure.severity_level.MINOR)
async def test_login_submit_double_click(login_page, user_api_created: RegisterUserDTO):
    await login_page.open()
    await login_page.form.fill_email(user_api_created.email)
    await login_page.form.fill_password(user_api_created.password)
    await login_page.form.submit_button.double_click()
    await assert_login_success(login_page, expected_email=user_api_created.email)


@allure.feature("Auth UI")
@allure.story("Theme switcher")
@allure.severity(allure.severity_level.MINOR)
async def test_theme_switch_on_login_page(login_page):
    await login_page.open()

    with allure.step("Verify theme switch is visible and get initial state"):
        switch_locator = login_page.navbar.theme_switch.get_locator()
        await expect(switch_locator).to_be_visible()
        html_locator = login_page.page.locator("html")
        initial_state = (await switch_locator.get_attribute("aria-checked")) or "false"
        # default theme is light but the html tag hasn't data-theme attribute
        # in the first fresh session
        initial_theme = await html_locator.get_attribute("data-theme") or "light"
        target_state = "false" if initial_state.lower() == "true" else "true"

    with allure.step("Toggle theme and verify change"):
        await login_page.navbar.toggle_theme()
        await expect(switch_locator).to_have_attribute("aria-checked", target_state)
        toggled_theme = await html_locator.get_attribute("data-theme") or ""
        assert toggled_theme != initial_theme, "HTML data-theme did not change after toggle"

    with allure.step("Toggle theme back and verify return to initial state"):
        await login_page.navbar.toggle_theme()
        await expect(switch_locator).to_have_attribute("aria-checked", initial_state)
        reverted_theme = await html_locator.get_attribute("data-theme") or ""
        assert reverted_theme == initial_theme, "Theme switcher did not return to initial state"
