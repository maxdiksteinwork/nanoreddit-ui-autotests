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

from settings import get_settings
from utils.allure_helpers import (
    attach_console_logs,
    attach_dom_snapshot,
    attach_screenshot,
)
from utils.clients.api_client import ApiClient
from utils.clients.sql_client import SQLClient


@pytest_asyncio.fixture(scope="session")
async def session_playwright_instance() -> AsyncGenerator[Playwright, Any]:
    async with async_playwright() as playwright:
        yield playwright


@pytest_asyncio.fixture(scope="session")
async def session_browser(
    session_playwright_instance: Playwright,
) -> AsyncGenerator[Browser, Any]:
    settings = get_settings()
    browser = await session_playwright_instance.chromium.launch(
        headless=settings.headless
    )
    try:
        yield browser
    finally:
        await browser.close()


@pytest.fixture
async def context(
    session_browser: Browser,
) -> AsyncGenerator[BrowserContext, Any]:
    settings = get_settings()
    ctx = await session_browser.new_context()  # глянуть нужно ли передавать base url
    ctx.set_default_timeout(settings.default_timeout_ms)
    try:
        yield ctx
    finally:
        await ctx.close()


@pytest.fixture
async def page(context: BrowserContext) -> AsyncGenerator[Page, Any]:
    new_page = await context.new_page()
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

    new_page.on("console", _handle_console)
    setattr(new_page, "_console_logs", console_messages)

    try:
        yield new_page
    finally:
        try:
            new_page.off("console", _handle_console)
        except Exception:
            pass
        await new_page.close()


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


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item):
    """
    сохраняет результат каждой стадии теста (setup/call/teardown) прямо на объекте item.
    capture_artifacts затем использует эти атрибуты, чтобы понять, упал ли тест
    """
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)


@pytest.fixture(autouse=True)
async def capture_artifacts(request, page: Page):
    """
    если тест провалился на стадии call, делает полноэкранный скриншот и прикрепляет
    его к отчёту Allure (папка берётся из Settings)
    """
    yield

    rep = getattr(request.node, "rep_call", None)
    if rep is None or rep.passed:
        return

    if page is None or page.is_closed():
        return

    await attach_screenshot(page, name="Screenshot")
    await attach_dom_snapshot(page, name="DOM snapshot")
    console_logs: list[str] | None = getattr(page, "_console_logs", None)
    if console_logs:
        attach_console_logs(console_logs, name="Console logs")
