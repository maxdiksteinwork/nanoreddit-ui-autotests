import asyncio
from typing import Any, AsyncGenerator, Awaitable, Callable, List, Literal

import pytest
import pytest_asyncio
from pytest import FixtureRequest
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
from ui.pages.create_post_page import CreatePostPage
from ui.pages.home_page import HomePage
from ui.pages.login_page import LoginPage
from ui.pages.post_page import PostPage
from ui.pages.register_page import RegisterPage
from utils.allure_helpers import (
    attach_console_logs,
    attach_dom_snapshot,
    attach_screenshot,
)
from utils.clients.api_client import ApiClient
from utils.clients.sql_client import SQLClient

PageType = Literal["home", "create_post", "post", "login", "register"]


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


async def _create_guest_context(browser: Browser) -> BrowserContext:
    """создает гостевой контекст без авторизации"""
    settings = get_settings()
    ctx = await browser.new_context()
    ctx.set_default_timeout(settings.default_timeout_ms)
    return ctx


def _create_page_instance(page_type: PageType, base_page: Page):
    """создаёт экземпляр страницы нужного типа"""
    page_classes = {
        "home": HomePage,
        "create_post": CreatePostPage,
        "post": PostPage,
        "login": LoginPage,
        "register": RegisterPage,
    }
    return page_classes[page_type](base_page)


async def _attach_artifacts_async(page: Page) -> None:
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
    yield browser
    await browser.close()


@pytest.fixture
def make_authenticated_context(
    session_browser: Browser, session_api_client: ApiClient
) -> Callable[[RegisterUserDTO], Awaitable[BrowserContext]]:
    """фабрика для создания авторизованного контекста"""

    async def _create_context(user: RegisterUserDTO) -> BrowserContext:
        return await _create_authenticated_context(session_browser, user, session_api_client)

    return _create_context


@pytest.fixture
def make_page(
    session_browser: Browser,
    make_authenticated_context,
    request: FixtureRequest,
) -> Callable[[PageType, RegisterUserDTO | None], Awaitable[Any]]:
    """фабрика для создания страниц с разными ролями"""

    async def _make_page(
        page_type: PageType,
        user: RegisterUserDTO | None = None,
    ):
        if user is None:
            # гостевая страница
            guest_context = await _create_guest_context(session_browser)
            base_page = await guest_context.new_page()
            _setup_console_logging(base_page)
            # сохраняем ссылку на страницу для прикрепления артефактов и закрытия
            request.node._active_page = base_page
            request.node._active_context = guest_context
        else:
            # авторизованная страница
            auth_context = await make_authenticated_context(user)
            base_page = await auth_context.new_page()
            _setup_console_logging(base_page)
            request.node._active_page = base_page
            request.node._active_context = auth_context

        return _create_page_instance(page_type, base_page)

    return _make_page


@pytest.fixture(scope="session")
def session_api_client() -> ApiClient:
    settings = get_settings()
    client = ApiClient(base_url=settings.api_base_url)
    yield client
    client.close()


@pytest.fixture(scope="session")
def session_sql_client() -> SQLClient:
    settings = get_settings()
    client = SQLClient(
        host=settings.db_host,
        port=settings.db_port,
        dbname=settings.db_name,
        user=settings.db_user,
        password=settings.db_password.get_secret_value(),
    )
    yield client
    client.close()


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call) -> None:
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
async def cleanup_page(request: FixtureRequest) -> AsyncGenerator[None, Any]:
    """
    закрывает страницу и контекст после выполнения теста
    """
    yield

    page = getattr(request.node, "_active_page", None)
    context = getattr(request.node, "_active_context", None)
    
    if page is not None:
        try:
            if not page.is_closed():
                await page.close()
        except Exception:
            pass
        request.node._active_page = None
    
    if context is not None:
        try:
            await context.close()
        except Exception:
            pass
        request.node._active_context = None
