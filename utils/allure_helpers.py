import json
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Sequence

import allure

if TYPE_CHECKING:
    from playwright.async_api import Page


def attach_db_query(
    sql: str,
    params: Optional[tuple],
    rows: List[Dict[str, Any]],
    name: str = "SQL query",
    limit: int = 5,
) -> None:
    with allure.step(name):
        info: Dict[str, Any] = {
            "sql": sql,
            "params": params,
            "row_count": len(rows),
        }

        if rows:
            subset = rows[:limit]
            if len(rows) > limit:
                info["note"] = f"Showing first {limit} of {len(rows)} rows"
            info["results"] = subset

        allure.attach(
            json.dumps(info, default=str, ensure_ascii=False, indent=2),
            name=name,
            attachment_type=allure.attachment_type.JSON,
        )


async def attach_screenshot(
    page: "Page", name: str = "Screenshot", full_page: bool = True
) -> None:
    try:
        screenshot_bytes = await page.screenshot(full_page=full_page)
        allure.attach(
            screenshot_bytes,
            name=name,
            attachment_type=allure.attachment_type.PNG,
        )
    except Exception as exc:  # pragma: no cover - best effort attachment
        allure.attach(
            f"Failed to capture screenshot: {exc}",
            name=name,
            attachment_type=allure.attachment_type.TEXT,
        )


async def attach_dom_snapshot(page: "Page", name: str = "DOM snapshot") -> None:
    if page is None or page.is_closed():
        return
    attachment_type = allure.attachment_type.HTML
    try:
        dom = await page.content()
    except Exception as exc:  # pragma: no cover - best effort attachment
        dom = f"Failed to capture DOM: {exc}"
        attachment_type = allure.attachment_type.TEXT
    allure.attach(
        dom,
        name=name,
        attachment_type=attachment_type,
    )


def attach_console_logs(logs: Sequence[str], name: str = "Console logs") -> None:
    if not logs:
        return
    body = "\n".join(logs)
    allure.attach(
        body,
        name=name,
        attachment_type=allure.attachment_type.TEXT,
    )
