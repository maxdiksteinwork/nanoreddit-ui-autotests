from __future__ import annotations

import asyncio
from typing import Awaitable, Callable

import pytest
import pytest_asyncio

from models.posts_dto import AddCommentDTO, PublishPostDTO
from utils.clients.api_client import ApiClient
from utils.database.database_helpers import fetch_single_post_by_title
from utils.database.database_helpers import clear_all_posts
from utils.database.database_helpers import delete_post_by_title_and_author


@pytest.fixture
def make_post_api_created(
    session_api_client: ApiClient,
) -> Callable[[str, str, PublishPostDTO | None], Awaitable[PublishPostDTO]]:
    async def _publish(
        *, email: str, password: str, payload: PublishPostDTO | None = None
    ) -> PublishPostDTO:
        data = payload or PublishPostDTO.random()
        token = await asyncio.to_thread(
            session_api_client.login_and_get_token, email=email, password=password
        )
        await asyncio.to_thread(
            session_api_client.publish_post,
            token=token,
            title=data.title,
            content=data.content,
        )
        return data

    return _publish


@pytest.fixture
def make_post_api_created_with_db(
    make_post_api_created,
    session_sql_client,
) -> Callable[[str, str, PublishPostDTO | None], Awaitable[tuple[PublishPostDTO, dict]]]:
    async def _publish_with_db(
        *, email: str, password: str, payload: PublishPostDTO | None = None
    ) -> tuple[PublishPostDTO, dict]:
        created = await make_post_api_created(email=email, password=password, payload=payload)
        db_post = await asyncio.to_thread(fetch_single_post_by_title, session_sql_client, created.title)
        return created, db_post

    return _publish_with_db


@pytest.fixture
def make_post_api_created_with_comment(
    session_api_client: ApiClient,
) -> Callable[[str, str, PublishPostDTO | None, str | None], Awaitable[tuple[str, str]]]:
    async def _publish_with_comment(
        *,
        email: str,
        password: str,
        post_payload: PublishPostDTO | None = None,
        comment_text: str | None = None,
    ) -> tuple[str, str]:
        post_data = post_payload or PublishPostDTO.random()
        comment = comment_text or AddCommentDTO.random().text

        token = await asyncio.to_thread(
            session_api_client.login_and_get_token, email=email, password=password
        )
        post_response = await asyncio.to_thread(
            session_api_client.publish_post,
            token=token,
            title=post_data.title,
            content=post_data.content,
        )
        post_id = post_response["responseData"]["id"]
        await asyncio.to_thread(
            session_api_client.add_comment, token=token, post_id=post_id, text=comment
        )
        return post_id, comment

    return _publish_with_comment


@pytest_asyncio.fixture
async def empty_posts_db(session_sql_client):
    await clear_all_posts(session_sql_client)
    yield


@pytest_asyncio.fixture
async def post_db_cleanup(session_sql_client, user_api_created):
    created_titles: list[str] = []

    def register(*, title: str) -> None:
        created_titles.append(title)

    yield register

    for title in created_titles:
        await delete_post_by_title_and_author(
            session_sql_client,
            title=title,
            author_email=user_api_created.email,
        )
