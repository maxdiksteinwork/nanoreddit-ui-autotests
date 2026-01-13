import asyncio
from typing import Any, AsyncGenerator, List

import pytest
import pytest_asyncio
from playwright.async_api import (
    Browser,
    BrowserContext,
    ConsoleMessage,
    Page,
    Playwright,
    async_playwright,
)

from models.auth_dto import RegisterUserDTO
from settings import get_settings
from utils.allure_helpers import (
    attach_console_logs,
    attach_dom_snapshot,
    attach_screenshot,
)
from utils.clients.api_client import ApiClient
from utils.clients.sql_client import SQLClient


def _setup_console_logging(page: Page) -> List[str]:
    console_messages: List[str] = []

    def _handle_console(msg: ConsoleMessage) -> None:
        location = msg.location
        location_suffix = ""
        if location and location.get("url"):
            url = location["url"]
            line = location.get("lineNumber")
            location_suffix = f" @ {url}"
            if line is not None:
                location_suffix += f":{line}"
        console_messages.append(f"[{msg.type.upper()}] {msg.text}{location_suffix}")

    page.on("console", _handle_console)
    page._console_logs = console_messages
    return console_messages


def _cleanup_console_logging(page: Page) -> None:
    try:
        page.off("console", lambda msg: None)
    except Exception:
        pass


async def _create_authenticated_context(
    browser: Browser,
    user: RegisterUserDTO,
    api_client: ApiClient,
) -> BrowserContext:
    """создает контекст с токеном пользователя в localStorage"""
    settings = get_settings()
    token = api_client.login_and_get_token(
        email=user.email,
        password=user.password,
    )
    ctx = await browser.new_context(
        storage_state={
            "origins": [
                {
                    "origin": settings.base_url.rstrip("/"),
                    "localStorage": [{"name": "token", "value": token}],
                }
            ]
        }
    )
    ctx.set_default_timeout(settings.default_timeout_ms)
    return ctx


async def _attach_artifacts_async(page: Page):
    await attach_screenshot(page, name="Screenshot")
    await attach_dom_snapshot(page, name="DOM snapshot")
    console_logs: list[str] | None = getattr(page, "_console_logs", None)
    if console_logs:
        attach_console_logs(console_logs, name="Console logs")


@pytest_asyncio.fixture(scope="session")
async def session_playwright_instance() -> AsyncGenerator[Playwright, Any]:
    async with async_playwright() as playwright:
        playwright.selectors.set_test_id_attribute("qa-data")
        yield playwright


@pytest_asyncio.fixture(scope="session")
async def session_browser(
    session_playwright_instance: Playwright,
) -> AsyncGenerator[Browser, Any]:
    settings = get_settings()
    browser = await session_playwright_instance.chromium.launch(headless=settings.headless)
    try:
        yield browser
    finally:
        await browser.close()


@pytest.fixture(scope="session")
def session_api_client():
    settings = get_settings()
    client = ApiClient(base_url=settings.api_base_url)
    try:
        yield client
    finally:
        client.close()


@pytest.fixture(scope="session")
def session_sql_client():
    settings = get_settings()
    client = SQLClient(
        host=settings.db_host,
        port=settings.db_port,
        dbname=settings.db_name,
        user=settings.db_user,
        password=settings.db_password.get_secret_value(),
    )
    try:
        yield client
    finally:
        client.close()


@pytest.fixture
def make_authenticated_context(session_browser: Browser, session_api_client: ApiClient):
    """фабрика для создания авторизованного контекста"""

    async def _create_context(user: RegisterUserDTO) -> BrowserContext:
        return await _create_authenticated_context(session_browser, user, session_api_client)

    return _create_context


@pytest_asyncio.fixture
async def context(
    session_browser: Browser,
) -> AsyncGenerator[BrowserContext, Any]:
    settings = get_settings()
    ctx = await session_browser.new_context()
    ctx.set_default_timeout(settings.default_timeout_ms)
    try:
        yield ctx
    finally:
        await ctx.close()


@pytest_asyncio.fixture
async def authenticated_context(
    session_browser: Browser,
    user_api_created: RegisterUserDTO,
    session_api_client: ApiClient,
) -> AsyncGenerator[BrowserContext, Any]:
    ctx = await _create_authenticated_context(session_browser, user_api_created, session_api_client)
    try:
        yield ctx
    finally:
        await ctx.close()


@pytest_asyncio.fixture
async def admin_authenticated_context(
    session_browser: Browser,
    admin_api_created: RegisterUserDTO,
    session_api_client: ApiClient,
) -> AsyncGenerator[BrowserContext, Any]:
    ctx = await _create_authenticated_context(
        session_browser, admin_api_created, session_api_client
    )
    try:
        yield ctx
    finally:
        await ctx.close()


@pytest_asyncio.fixture
async def banned_authenticated_context(
    session_browser: Browser,
    banned_user_api_created: RegisterUserDTO,
    session_api_client: ApiClient,
) -> AsyncGenerator[BrowserContext, Any]:
    ctx = await _create_authenticated_context(
        session_browser, banned_user_api_created, session_api_client
    )
    try:
        yield ctx
    finally:
        await ctx.close()


@pytest_asyncio.fixture
async def page(context: BrowserContext, request) -> AsyncGenerator[Page, Any]:
    new_page = await context.new_page()
    _setup_console_logging(new_page)
    # сохраняем ссылку на страницу для прикрепления артефактов и закрытия
    request.node._active_page = new_page
    try:
        yield new_page
    finally:
        _cleanup_console_logging(new_page)
        # страница будет закрыта в cleanup_page


@pytest_asyncio.fixture
async def authenticated_page(
    authenticated_context: BrowserContext,
    request,
) -> AsyncGenerator[Page, Any]:
    new_page = await authenticated_context.new_page()
    _setup_console_logging(new_page)
    request.node._active_page = new_page
    try:
        yield new_page
    finally:
        _cleanup_console_logging(new_page)


@pytest_asyncio.fixture
async def admin_authenticated_page(
    admin_authenticated_context: BrowserContext,
    request,
) -> AsyncGenerator[Page, Any]:
    new_page = await admin_authenticated_context.new_page()
    _setup_console_logging(new_page)
    request.node._active_page = new_page
    try:
        yield new_page
    finally:
        _cleanup_console_logging(new_page)


@pytest_asyncio.fixture
async def banned_authenticated_page(
    banned_authenticated_context: BrowserContext,
    request,
) -> AsyncGenerator[Page, Any]:
    new_page = await banned_authenticated_context.new_page()
    _setup_console_logging(new_page)
    request.node._active_page = new_page
    try:
        yield new_page
    finally:
        _cleanup_console_logging(new_page)


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    """
    сохраняет результат каждой стадии теста (setup/call/teardown) прямо на объекте item.
    если тест упал на стадии call, прикрепляет артефакты (скриншот, DOM, логи)
    """
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)

    if call.when == "call" and rep.failed:
        page = getattr(item, "_active_page", None)
        if page is not None:
            try:
                if not page.is_closed():
                    # запускаем async функцию из синхронного контекста
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            import concurrent.futures

                            with concurrent.futures.ThreadPoolExecutor() as executor:
                                future = executor.submit(asyncio.run, _attach_artifacts_async(page))
                                future.result(timeout=10)
                        else:
                            loop.run_until_complete(_attach_artifacts_async(page))
                    except RuntimeError:
                        asyncio.run(_attach_artifacts_async(page))
            except Exception:
                pass


@pytest_asyncio.fixture(autouse=True)
async def cleanup_page(request):
    """
    закрывает страницу после выполнения теста
    """
    yield

    page = getattr(request.node, "_active_page", None)
    if page is not None:
        try:
            if not page.is_closed():
                await page.close()
        except Exception:
            pass
        request.node._active_page = None
