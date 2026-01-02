from __future__ import annotations

from typing import TYPE_CHECKING

import allure
from playwright.async_api import Locator, expect

from ui.pages.base_page import BasePage

if TYPE_CHECKING:
    from ui.pages.login_page import LoginPage
    from ui.pages.register_page import RegisterPage


async def expect_contains_text(locator: Locator, text: str, *, label: str) -> None:
    with allure.step(label):
        await expect(locator).to_contain_text(text)


async def _assert_single_toast(page, *, message: str, label: str) -> None:
    base_page = BasePage(page)
    await expect_contains_text(base_page.get_last_toast(), message, label=label)
    # проверяем, что тостов с таким текстом ровно 1 (для защиты от дублей при double click)
    toasts_with_message = page.locator(BasePage.TOAST_SELECTOR).filter(has_text=message)
    try:
        await expect(toasts_with_message).to_have_count(1, timeout=100)
    except AssertionError as exc:
        actual = await toasts_with_message.count()
        raise AssertionError(
            f"Expected exactly one toast with message '{message}', but {actual} toast(s) found"
        ) from exc


async def assert_registration_error(
    register_page: RegisterPage, *, message: str = "Ошибка регистрации"
) -> None:
    with allure.step("Validate registration error UI state"):
        await _assert_single_toast(
            register_page.page,
            message=message,
            label=f'Ensure toast contains "{message}"',
        )
        await register_page.should_have_url("register")


async def assert_registration_success(
    register_page: RegisterPage,
    *,
    message: str = "Регистрация успешна",
) -> None:
    with allure.step("Validate registration success UI state"):
        await _assert_single_toast(
            register_page.page,
            message=message,
            label=f'Ensure toast contains "{message}"',
        )
        await register_page.should_have_url("login")


async def assert_login_success(
    login_page: LoginPage,
    *,
    message: str = "Успешный вход",
    expected_url: str = "/",
    expected_email: str | None = None,
    label: str | None = None,
) -> None:
    with allure.step("Validate login success UI state"):
        await _assert_single_toast(
            login_page.page,
            message=message,
            label=label or f'Ensure toast contains "{message}"',
        )
        await login_page.should_have_url(expected_url)
        if expected_email:
            await login_page.navbar.should_be_user_nav(email=expected_email)


async def assert_login_error(
    login_page: LoginPage,
    *,
    message: str = "Ошибка входа",
) -> None:
    with allure.step("Validate login error UI state"):
        await _assert_single_toast(
            login_page.page,
            message=message,
            label=f'Ensure toast contains "{message}"',
        )
        await login_page.should_have_url("login")


async def assert_post_creation_success(
    page,
    *,
    message: str = "Пост успешно создан",
) -> None:
    with allure.step("Validate post creation success toast"):
        await _assert_single_toast(
            page,
            message=message,
            label=f'Ensure toast contains "{message}"',
        )


async def assert_comment_added_success(
    post_page,
    *,
    message: str = "Комментарий добавлен",
) -> None:
    with allure.step("Validate comment added success toast"):
        await _assert_single_toast(
            post_page.page,
            message=message,
            label=f'Ensure toast contains "{message}"',
        )


async def assert_reply_added_success(
    post_page,
    *,
    message: str = "Ответ добавлен",
) -> None:
    with allure.step("Validate reply added success toast"):
        await _assert_single_toast(
            post_page.page,
            message=message,
            label=f'Ensure toast contains "{message}"',
        )


async def assert_comment_validation_error(
    post_page,
    *,
    message: str = "Validation error",
) -> None:
    with allure.step("Validate comment validation error toast"):
        await _assert_single_toast(
            post_page.page,
            message=message,
            label=f'Ensure toast contains "{message}"',
        )


async def assert_user_banned_success(
    page_object,
    *,
    message: str = "Пользователь успешно забанен",
) -> None:
    with allure.step("Validate user banned success toast"):
        await _assert_single_toast(
            page_object.page,
            message=message,
            label=f'Ensure toast contains "{message}"',
        )


async def assert_user_unbanned_success(
    page_object,
    *,
    message: str = "Пользователь успешно разбанен",
) -> None:
    with allure.step("Validate user unbanned success toast"):
        await _assert_single_toast(
            page_object.page,
            message=message,
            label=f'Ensure toast contains "{message}"',
        )


async def assert_banned_user_toast(
    page_object,
    *,
    message: str = "User is banned",
) -> None:
    with allure.step("Validate banned user toast"):
        await _assert_single_toast(
            page_object.page,
            message=message,
            label=f'Ensure toast contains "{message}"',
        )
