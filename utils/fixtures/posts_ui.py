from __future__ import annotations

import asyncio

import pytest

from models.posts_dto import AddCommentDTO, PublishPostDTO


@pytest.fixture
def make_post_api_created(session_api_client):
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
def make_post_api_created_with_comment(session_api_client):
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
