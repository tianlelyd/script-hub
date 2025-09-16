"""全局快捷键监听。"""
from __future__ import annotations

from typing import Callable

from loguru import logger
from pynput import keyboard


class GlobalHotkey:
    """包装 pynput 实现的全局快捷键。"""

    def __init__(self, combination: str, on_activate: Callable[[], None]) -> None:
        self._combination = combination
        self._on_activate = on_activate
        self._listener = keyboard.GlobalHotKeys({combination: self._handle_activate})

    def start(self) -> None:
        logger.info("注册全局快捷键: {}", self._combination)
        self._listener.start()

    def stop(self) -> None:
        logger.info("注销全局快捷键")
        self._listener.stop()

    def join(self) -> None:
        self._listener.join()

    @property
    def combination(self) -> str:
        return self._combination

    def _handle_activate(self) -> None:
        logger.debug("触发快捷键 {}", self._combination)
        self._on_activate()
