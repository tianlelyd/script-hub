"""向当前焦点应用填充文本。"""
from __future__ import annotations

import time
from typing import Optional

import pyperclip
from loguru import logger
from pynput.keyboard import Controller, Key


class TextInserter:
    """通过剪贴板 + Cmd+V 的方式插入文本。"""

    def __init__(self) -> None:
        self._keyboard = Controller()

    def insert(self, text: str) -> None:
        if not text:
            logger.info("文本为空，跳过填充")
            return

        previous_clipboard: Optional[str] = None
        try:
            previous_clipboard = pyperclip.paste()
        except pyperclip.PyperclipException as exc:  # pragma: no cover - 平台差异
            logger.debug("读取剪贴板失败: {}", exc)

        try:
            pyperclip.copy(text)
            time.sleep(0.05)
            with self._keyboard.pressed(Key.cmd):
                self._keyboard.press("v")
                self._keyboard.release("v")
            time.sleep(0.1)
            logger.info("已将识别文本粘贴到当前输入焦点")
        finally:
            if previous_clipboard is not None:
                try:
                    pyperclip.copy(previous_clipboard)
                except pyperclip.PyperclipException as exc:  # pragma: no cover
                    logger.debug("恢复剪贴板失败: {}", exc)
