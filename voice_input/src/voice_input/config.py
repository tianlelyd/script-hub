"""加载讯飞语音开放平台相关配置。"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


@dataclass(frozen=True)
class XFYunCredentials:
    app_id: str
    api_key: str
    api_secret: str


class MissingCredentialError(RuntimeError):
    """缺少必要的讯飞平台凭据。"""


def load_credentials(env_path: Optional[Path] = None) -> XFYunCredentials:
    """从 .env (或传入路径) 加载凭据。"""

    if env_path is None:
        env_path = Path.cwd() / ".env"

    if env_path.exists():
        load_dotenv(env_path)

    app_id = os.getenv("APPID")
    api_key = os.getenv("APIKey") or os.getenv("API_KEY")
    api_secret = os.getenv("APISecret") or os.getenv("API_SECRET")

    if not all([app_id, api_key, api_secret]):
        raise MissingCredentialError("请在 .env 中配置 APPID、APIKey、APISecret")

    return XFYunCredentials(app_id=app_id, api_key=api_key, api_secret=api_secret)
