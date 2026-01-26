import os
import shutil

import pytest
from dotenv import load_dotenv

from settings import get_settings

ALLURE_DIR = "reports/allure-results"

pytest_plugins = (
    "utils.fixtures.base_ui",
    "utils.fixtures.users_ui",
    "utils.fixtures.posts_ui",
    "utils.fixtures.admin_ui",
)


def pytest_addoption(parser: pytest.Parser) -> None:
    """
    --env=local|dev|stg|prod-test
    """
    parser.addoption(
        "--env",
        action="store",
        default="local",
        choices=["local", "dev", "stg", "prod-test"],
        help=(
            "Target environment for tests. "
            "Controls which .env.* file will be loaded "
            "(local -> .env, dev -> .env.dev, stg -> .env.stg, "
            "prod-test -> .env.prod-test)."
        ),
    )


def _load_env_for_pytest(config: pytest.Config) -> str:
    """
    выбирает .env-файл на основе опции --env и подгружает его в переменные окружения.
    """
    env_name: str = config.getoption("--env")
    env_file_map = {
        "local": ".env",
        "dev": ".env.dev",
        "stg": ".env.stg",
        "prod-test": ".env.prod-test",
    }
    env_file = env_file_map.get(env_name, ".env")
    os.environ["TEST_ENV"] = env_name

    load_dotenv(dotenv_path=env_file, override=True)
    return env_file


def pytest_configure(config: pytest.Config) -> None:
    _load_env_for_pytest(config)
    _ = get_settings()

    if os.path.exists(ALLURE_DIR):
        try:
            shutil.rmtree(ALLURE_DIR)
        except (PermissionError, OSError):
            try:
                for filename in os.listdir(ALLURE_DIR):
                    file_path = os.path.join(ALLURE_DIR, filename)
                    try:
                        if os.path.isfile(file_path) or os.path.islink(file_path):
                            os.unlink(file_path)
                        elif os.path.isdir(file_path):
                            shutil.rmtree(file_path)
                    except (PermissionError, OSError):
                        pass
            except (PermissionError, OSError):
                pass

    os.makedirs(ALLURE_DIR, exist_ok=True)


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    os.makedirs(ALLURE_DIR, exist_ok=True)
    settings = get_settings()

    env_file = os.path.join(ALLURE_DIR, "environment.properties")
    with open(env_file, "w", encoding="utf-8") as f:
        f.write(f"Base\\ URL={settings.base_url}\n")
        f.write(f"API\\ Base\\ URL={settings.api_base_url}\n")
        f.write(f"Default\\ Timeout={settings.default_timeout_ms}ms\n")
        f.write(f"Screenshot\\ Dir={settings.screenshot_dir}\n")
        f.write(f"Test\\ Env={os.environ.get('TEST_ENV', 'local')}\n")
        f.write(f"Build\\ ID={os.environ.get('CI_PIPELINE_ID', 'manual')}\n")

    print(f"\n[ALLURE] environment.properties generated at: {os.path.abspath(env_file)}")
