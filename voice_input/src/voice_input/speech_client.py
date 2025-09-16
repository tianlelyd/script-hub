"""讯飞听写 WebSocket 客户端封装。"""
from __future__ import annotations

import base64
import json
import ssl
from dataclasses import dataclass
from datetime import datetime
from email.utils import formatdate
from typing import Dict, Iterable, List, Optional
from urllib.parse import quote
import hmac
import hashlib

from loguru import logger
from websocket import WebSocketConnectionClosedException, create_connection

from .config import XFYunCredentials


_XFYUN_HOST = "iat-api.xfyun.cn"
_XFYUN_ENDPOINT = "/v2/iat"
_XFYUN_URL = f"wss://{_XFYUN_HOST}{_XFYUN_ENDPOINT}"


class XFYunAPIError(RuntimeError):
    """讯飞返回异常。"""


@dataclass
class IatBusinessConfig:
    language: str = "zh_cn"
    domain: str = "iat"
    accent: str = "mandarin"
    vad_eos: int = 3000

    def to_dict(self) -> Dict[str, object]:
        return {
            "language": self.language,
            "domain": self.domain,
            "accent": self.accent,
            "vad_eos": self.vad_eos,
        }


class XFYunIatClient:
    """简化的实时语音听写客户端。"""

    def __init__(
        self,
        credentials: XFYunCredentials,
        *,
        business: Optional[IatBusinessConfig] = None,
        timeout: float = 10.0,
    ) -> None:
        self._credentials = credentials
        self._business = business or IatBusinessConfig()
        self._timeout = timeout

    def recognize(self, audio_chunks: Iterable[bytes]) -> str:
        """将 PCM 音频分段发送到讯飞听写服务并返回识别结果。"""

        url = self._construct_url()
        logger.debug("连接讯飞听写服务: {}", url)
        ws = create_connection(url, timeout=self._timeout, sslopt={"cert_reqs": ssl.CERT_NONE})

        try:
            first_packet = True
            for chunk in audio_chunks:
                if not chunk:
                    continue
                payload = self._make_data_packet(chunk, status=0 if first_packet else 1, include_meta=first_packet)
                ws.send(payload)
                first_packet = False

            # 发送结束包
            ws.send(self._make_data_packet(b"", status=2, include_meta=False))

            return self._collect_result(ws)
        finally:
            try:
                ws.close()
            except WebSocketConnectionClosedException:
                pass

    def _construct_url(self) -> str:
        """构造带鉴权参数的 WebSocket URL。"""

        date = formatdate(timeval=None, localtime=False, usegmt=True)
        signature_text = f"host: {_XFYUN_HOST}\ndate: {date}\nGET {_XFYUN_ENDPOINT} HTTP/1.1"
        signature = hmac.new(
            self._credentials.api_secret.encode("utf-8"),
            signature_text.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).digest()
        signature_base64 = base64.b64encode(signature).decode("utf-8")

        authorization_origin = (
            f'api_key="{self._credentials.api_key}", '
            f'algorithm="hmac-sha256", headers="host date request-line", '
            f'signature="{signature_base64}"'
        )
        authorization = base64.b64encode(authorization_origin.encode("utf-8")).decode("utf-8")

        return f"{_XFYUN_URL}?authorization={authorization}&date={quote(date)}&host={_XFYUN_HOST}"

    def _make_data_packet(self, audio: bytes, *, status: int, include_meta: bool) -> str:
        data = {
            "status": status,
            "audio": base64.b64encode(audio).decode("utf-8"),
            "format": "audio/L16;rate=16000",
            "encoding": "raw",
        }
        payload = {"data": data}
        if include_meta:
            payload["common"] = {"app_id": self._credentials.app_id}
            payload["business"] = self._business.to_dict()
        return json.dumps(payload)

    def _collect_result(self, ws) -> str:
        accumulated: Dict[int, str] = {}
        final_status = None

        while True:
            try:
                raw_message = ws.recv()
            except WebSocketConnectionClosedException:
                break

            if not raw_message:
                break

            response = json.loads(raw_message)
            logger.debug("收到讯飞消息: {}", response)
            code = response.get("code", -1)
            if code != 0:
                message = response.get("message", "未知错误")
                raise XFYunAPIError(f"讯飞接口返回错误: {code} {message}")

            data = response.get("data") or {}
            final_status = data.get("status", final_status)
            result = data.get("result")
            if result:
                text = self._parse_result_segment(result)
                sn = result.get("sn")
                if sn is None:
                    # 若未提供 sn，则退化为简单追加
                    sn = max(accumulated.keys(), default=-1) + 1
                pgs = result.get("pgs")
                if pgs == "rpl":
                    rg = result.get("rg") or []
                    if isinstance(rg, list) and len(rg) == 2:
                        start, end = rg
                        for key in list(accumulated.keys()):
                            if start <= key <= end:
                                accumulated.pop(key, None)
                accumulated[sn] = text

            if final_status == 2:
                break

        ordered_keys = sorted(accumulated.keys())
        return "".join(accumulated[key] for key in ordered_keys)

    @staticmethod
    def _parse_result_segment(result: Dict[str, object]) -> str:
        words: List[str] = []
        for ws in result.get("ws", []):
            for candidate in ws.get("cw", []):
                text = candidate.get("w")
                if text:
                    words.append(text)
        return "".join(words)
