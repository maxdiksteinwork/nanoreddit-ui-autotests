import json
from typing import Any, Dict

import allure
import requests


class ApiClient:
    def __init__(self, base_url: str, timeout: int = 10) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    def close(self) -> None:
        self.session.close()

    def register_user(
        self, *, email: str, username: str, password: str
    ) -> Dict[str, Any]:
        with allure.step(f"Register user: {email}"):
            payload = {
                "email": email,
                "username": username,
                "password": password,
                "passwordConfirmation": password,
            }
            url = f"{self.base_url}/api/v1/auth/register"
            response = self.session.post(url, json=payload, timeout=self.timeout)

            self._attach_json("Auth register request", {"url": url, "payload": payload})
            self._attach_json(
                "Auth register response",
                {"status_code": response.status_code, "body": self._safe_json(response)},
            )

            response.raise_for_status()
            return response.json()

    def login_user(self, *, email: str, password: str) -> Dict[str, Any]:
        with allure.step(f"Login user: {email}"):
            payload = {"email": email, "password": password}
            url = f"{self.base_url}/api/v1/auth/login"
            response = self.session.post(url, json=payload, timeout=self.timeout)

            self._attach_json("Auth login request", {"url": url, "payload": payload})
            self._attach_json(
                "Auth login response",
                {"status_code": response.status_code, "body": self._safe_json(response)},
            )

            response.raise_for_status()
            return response.json()

    def publish_post(self, *, token: str, title: str, content: str) -> Dict[str, Any]:
        with allure.step(f"Publish post: {title[:50]}{'...' if len(title) > 50 else ''}"):
            payload = {"title": title, "content": content}
            url = f"{self.base_url}/api/v1/posts/publish"
            headers = {"Authorization": f"Bearer {token}"}
            response = self.session.post(
                url,
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )

            self._attach_json(
                "Posts publish request",
                {"url": url, "payload": payload},
            )
            self._attach_json(
                "Posts publish response",
                {"status_code": response.status_code, "body": self._safe_json(response)},
            )

            response.raise_for_status()
            return response.json()

    def ban_user(self, *, email: str, seconds: int, token: str) -> Dict[str, Any]:
        with allure.step(f"Ban user: {email} for {seconds} seconds"):
            url = f"{self.base_url}/api/v1/admin/management/ban/byEmail/{email}"
            headers = {"Authorization": f"Bearer {token}"}
            response = self.session.post(
                url,
                params={"forSeconds": seconds},
                headers=headers,
                timeout=self.timeout,
            )

            self._attach_json(
                "Admin ban user request",
                {"url": url, "params": {"forSeconds": seconds}, "email": email},
            )
            self._attach_json(
                "Admin ban user response",
                {"status_code": response.status_code, "body": self._safe_json(response)},
            )

            response.raise_for_status()
            return response.json()

    def add_comment(self, *, token: str, post_id: str, text: str) -> Dict[str, Any]:
        with allure.step(f"Add comment to post {post_id}"):
            payload = {"text": text}
            url = f"{self.base_url}/api/v1/posts/{post_id}/addComment"
            headers = {"Authorization": f"Bearer {token}"}
            response = self.session.post(
                url,
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )

            self._attach_json(
                "Posts add comment request",
                {"url": url, "payload": payload, "post_id": post_id},
            )
            self._attach_json(
                "Posts add comment response",
                {"status_code": response.status_code, "body": self._safe_json(response)},
            )

            response.raise_for_status()
            return response.json()

    @staticmethod
    def _safe_json(response: requests.Response) -> Any:
        try:
            return response.json()
        except ValueError:
            return response.text

    @staticmethod
    def _attach_json(name: str, payload: Any) -> None:
        try:
            body = json.dumps(payload, indent=2, ensure_ascii=False)
        except (TypeError, ValueError):
            body = str(payload)
        allure.attach(body, name=name, attachment_type=allure.attachment_type.JSON)
