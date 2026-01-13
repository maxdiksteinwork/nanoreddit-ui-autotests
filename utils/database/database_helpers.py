import asyncio
from typing import Any, Awaitable, Callable, Dict, Optional

import allure

DEFAULT_POLL_INTERVAL = 0.3
FAST_POLL_INTERVAL = 0.1


async def _wait_for_condition(
    check_func: Callable[[], Awaitable[Any]],
    *,
    timeout: float,
    poll_interval: float = DEFAULT_POLL_INTERVAL,
    error_message: str,
) -> Any:
    deadline = asyncio.get_running_loop().time() + timeout
    while True:
        result = await check_func()
        if result:
            # если результат - список, возвращаем первый элемент, иначе сам результат
            return result[0] if isinstance(result, list) and result else result
        if asyncio.get_running_loop().time() > deadline:
            raise AssertionError(error_message)
        await asyncio.sleep(poll_interval)


def _build_comment_conditions(
    post_id: str,
    text: str,
    parent_comment_id: Optional[str] = None,
) -> tuple[list[str], list[str]]:
    conditions = ["post_id::text = %s", "text = %s"]
    params: list[str] = [post_id, text]
    if parent_comment_id is None:
        conditions.append("parent_id IS NULL")
    else:
        conditions.append("parent_id::text = %s")
        params.append(parent_comment_id)
    return conditions, params


def fetch_single_user(
    sql_client,
    email: str,
    *,
    columns: Optional[str] = None,
    error_message: Optional[str] = None,
) -> Dict[str, Any]:
    with allure.step(f"Fetch single user by email '{email}' from DB"):
        rows = get_user_by_email(sql_client, email, columns=columns)
        if len(rows) != 1:
            expected = error_message or f"Expected exactly 1 user with email {email}"
            raise AssertionError(f"{expected}; found {len(rows)}")
        return rows[0]


def get_table_count(
    sql_client,
    table_name: str,
    where_clause: Optional[str] = None,
    params: Optional[tuple] = None,
) -> int:
    step_name = f"Get count from table '{table_name}'"
    if where_clause:
        step_name += " with condition"
    with allure.step(step_name):
        sql = f"SELECT COUNT(*) as count FROM {table_name}"
        if where_clause:
            sql += f" {where_clause}"

        result = sql_client.query(sql, params or ())
        count = result[0]["count"] if result else 0

        allure.attach(
            f"Table: {table_name}\nWhere: {where_clause or 'N/A'}\nCount: {count}",
            name=f"DB count: {table_name}",
            attachment_type=allure.attachment_type.TEXT,
        )

        return count


async def clear_all_posts(
    sql_client,
    *,
    timeout: float = 2.0,
) -> None:
    with allure.step("Delete all posts, comments, and votes from DB"):
        await asyncio.to_thread(sql_client.execute, "DELETE FROM votes")
        await asyncio.to_thread(sql_client.execute, "DELETE FROM comments")
        await asyncio.to_thread(sql_client.execute, "DELETE FROM posts")

    with allure.step(f"Wait for tables to be empty (timeout: {timeout}s)"):
        deadline = asyncio.get_running_loop().time() + timeout
        while True:
            posts_count = await asyncio.to_thread(get_table_count, sql_client, "posts")
            comments_count = await asyncio.to_thread(get_table_count, sql_client, "comments")
            votes_count = await asyncio.to_thread(get_table_count, sql_client, "votes")

            if posts_count == 0 and comments_count == 0 and votes_count == 0:
                return

            if asyncio.get_running_loop().time() > deadline:
                raise AssertionError(
                    f"Tables not empty within {timeout}s: posts={posts_count}, "
                    f"comments={comments_count}, votes={votes_count}"
                )
            await asyncio.sleep(FAST_POLL_INTERVAL)


async def delete_user_by_email(
    sql_client,
    email: str,
) -> None:
    with allure.step(f"Delete user with email '{email}' from DB"):
        await asyncio.to_thread(
            sql_client.execute,
            "DELETE FROM users WHERE email = %s",
            (email,),
        )


async def delete_post_by_title_and_author(
    sql_client,
    *,
    title: str,
    author_email: str,
) -> None:
    with allure.step(f"Delete post with title '{title}' by author '{author_email}' from DB"):
        await asyncio.to_thread(
            sql_client.execute,
            """
            DELETE FROM posts
            WHERE author_id = (SELECT id FROM users WHERE email = %s)
                  AND title = %s
            """,
            (author_email, title),
        )


def get_user_by_email(sql_client, email: str, columns: Optional[str] = None):
    with allure.step(f"Get user by email '{email}' from DB"):
        columns = columns or "id, username, email, banned_until, role"
        rows = sql_client.query(f"SELECT {columns} FROM users WHERE email = %s", (email,))
        return rows


def get_post_by_title(
    sql_client,
    title: str,
    *,
    columns: Optional[str] = None,
    author_email: Optional[str] = None,
):
    step_name = f"Get post by title '{title}' from DB"
    if author_email:
        step_name += f" by author '{author_email}'"
    with allure.step(step_name):
        if columns is None:
            columns = "p.id::text, p.title, p.content, p.created_at, u.email"

        where_clause = "WHERE p.title = %s"
        params = [title]

        if author_email:
            where_clause += " AND u.email = %s"
            params.append(author_email)

        query = f"""
            SELECT {columns}
            FROM posts p
            JOIN users u ON u.id = p.author_id
            {where_clause}
            ORDER BY p.created_at DESC
        """

        return sql_client.query(query, tuple(params))


def fetch_single_post_by_title(
    sql_client,
    title: str,
    *,
    columns: Optional[str] = None,
    author_email: Optional[str] = None,
    error_message: Optional[str] = None,
) -> Dict[str, Any]:
    step_name = f"Fetch single post by title '{title}' from DB"
    if author_email:
        step_name += f" by author '{author_email}'"
    with allure.step(step_name):
        rows = get_post_by_title(sql_client, title, columns=columns, author_email=author_email)
        if len(rows) != 1:
            expected = error_message or f"Expected exactly 1 post with title '{title}'"
            if author_email:
                expected += f" by author {author_email}"
            raise AssertionError(f"{expected}; found {len(rows)}")
        return rows[0]


async def wait_for_post_in_db(
    sql_client,
    title: str,
    *,
    author_email: Optional[str] = None,
    timeout: float = 5.0,
    columns: Optional[str] = None,
) -> Dict[str, Any]:
    step_name = f"Wait for post '{title}' to appear in DB"
    if author_email:
        step_name += f" by author '{author_email}'"
    with allure.step(step_name):

        async def _check():
            with allure.step("Check post in DB"):
                return await asyncio.to_thread(
                    get_post_by_title,
                    sql_client,
                    title,
                    columns=columns,
                    author_email=author_email,
                )

        error_msg = f"Post '{title}'"
        if author_email:
            error_msg += f" by {author_email}"
        error_msg += f" not found in DB within {timeout} seconds"

        return await _wait_for_condition(_check, timeout=timeout, error_message=error_msg)


async def wait_for_comment_in_db(
    sql_client,
    *,
    post_id: str,
    text: str,
    parent_comment_id: Optional[str] = None,
    timeout: float = 3.0,
) -> Dict[str, Any]:
    step_name = f"Wait for comment to appear in DB (post_id: {post_id})"
    if parent_comment_id:
        step_name += f" (reply to {parent_comment_id})"
    with allure.step(step_name):
        conditions, params = _build_comment_conditions(post_id, text, parent_comment_id)

        query = f"""
            SELECT id::text, text, parent_id::text, post_id::text
            FROM comments
            WHERE {" AND ".join(conditions)}
            ORDER BY created_at DESC
            LIMIT 1
        """

        async def _check():
            with allure.step("Check comment in DB"):
                return await asyncio.to_thread(sql_client.query, query, tuple(params))

        error_msg = f"Comment with text '{text[:50]}...'"
        if parent_comment_id:
            error_msg += f" (reply to {parent_comment_id})"
        error_msg += f" not found in DB within {timeout} seconds"

        return await _wait_for_condition(_check, timeout=timeout, error_message=error_msg)


async def wait_for_user_ban_status(
    sql_client,
    *,
    email: str,
    banned: bool,
    timeout: float = 3.0,
) -> Dict[str, Any]:
    status_text = "banned" if banned else "unbanned"
    with allure.step(f"Wait for user '{email}' to be {status_text} in DB"):
        ban_condition = "IS NOT NULL" if banned else "IS NULL"

        query = f"""
            SELECT id::text, email, username, role, banned_until
            FROM users
            WHERE email = %s AND banned_until {ban_condition}
            LIMIT 1
        """

        async def _check():
            with allure.step("Check user ban status in DB"):
                return await asyncio.to_thread(sql_client.query, query, (email,))

        error_msg = f"User with email '{email}' is not {status_text} in DB within {timeout} seconds"
        return await _wait_for_condition(
            _check,
            timeout=timeout,
            poll_interval=FAST_POLL_INTERVAL,
            error_message=error_msg,
        )


def count_comments_in_db(
    sql_client,
    *,
    post_id: str,
    text: str,
    parent_comment_id: Optional[str] = None,
) -> int:
    step_name = f"Count comments in DB (post_id: {post_id})"
    if parent_comment_id:
        step_name += f" (reply to {parent_comment_id})"
    with allure.step(step_name):
        conditions, params = _build_comment_conditions(post_id, text, parent_comment_id)

        query = f"""
            SELECT COUNT(*)::int AS count
            FROM comments
            WHERE {" AND ".join(conditions)}
        """
        rows = sql_client.query(query, tuple(params))
        return rows[0]["count"] if rows else 0
