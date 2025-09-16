"""主程序入口。"""
from __future__ import annotations

import threading
from typing import Iterable

from loguru import logger

from .audio import AudioRecorder
from .config import XFYunCredentials, load_credentials
from .hotkey import GlobalHotkey
from .insertion import TextInserter
from .speech_client import XFYunAPIError, XFYunIatClient


class VoiceInputApp:
    def __init__(self, hotkey: str = "<shift>+<space>") -> None:
        self._credentials: XFYunCredentials = load_credentials()
        self._client = XFYunIatClient(self._credentials)
        self._recorder = AudioRecorder()
        self._inserter = TextInserter()
        self._hotkey = GlobalHotkey(hotkey, self._toggle_recording)
        self._recording = False
        self._lock = threading.Lock()
        self._processing_thread: threading.Thread | None = None

    def run(self) -> None:
        logger.info("语音输入助手已启动，快捷键 {}", self._hotkey.combination)
        logger.info("按下快捷键开始录音，再按一次结束并识别")
        self._hotkey.start()
        self._hotkey.join()

    def _toggle_recording(self) -> None:
        with self._lock:
            if self._recording:
                self._recording = False
                audio = self._recorder.stop()
                if not audio:
                    logger.warning("未捕获到音频，忽略本次识别")
                    return
                if self._processing_thread and self._processing_thread.is_alive():
                    logger.warning("上一段音频仍在识别中，请稍候")
                    return
                self._processing_thread = threading.Thread(
                    target=self._process_audio,
                    args=(audio,),
                    daemon=True,
                )
                self._processing_thread.start()
            else:
                if self._processing_thread and self._processing_thread.is_alive():
                    logger.warning("识别尚未完成，请稍后再试")
                    return
                self._recorder.start()
                self._recording = True
                logger.info("开始录音... 再次按下快捷键结束")

    def _process_audio(self, audio: bytes) -> None:
        logger.info("开始向讯飞发送音频，长度 {} 字节", len(audio))
        chunks = AudioRecorder.split_pcm(audio)
        try:
            text = self._client.recognize(chunks)
        except XFYunAPIError as exc:
            logger.error("讯飞接口报错: {}", exc)
            return
        except Exception as exc:  # pragma: no cover - 捕获未知错误
            logger.exception("识别失败: {}", exc)
            return

        if text.strip():
            logger.info("识别完成: {}", text)
            self._inserter.insert(text)
        else:
            logger.info("讯飞返回空文本")


def main() -> None:
    logger.remove()
    logger.add(lambda msg: print(msg, end=""))
    try:
        app = VoiceInputApp()
    except Exception as exc:
        logger.error("启动失败: {}", exc)
        return
    app.run()


if __name__ == "__main__":
    main()
