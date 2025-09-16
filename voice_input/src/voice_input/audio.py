"""音频采集工具。"""
from __future__ import annotations

import threading
from typing import Iterable

import numpy as np
import sounddevice as sd
from loguru import logger


class AudioRecorder:
    """使用 sounddevice 采集麦克风音频。"""

    def __init__(
        self,
        *,
        samplerate: int = 16000,
        channels: int = 1,
        dtype: str = "int16",
        chunk_millis: int = 40,
    ) -> None:
        self._samplerate = samplerate
        self._channels = channels
        self._dtype = dtype
        self._chunk_size = int(self._samplerate * chunk_millis / 1000)
        self._frames: list[np.ndarray] = []
        self._stream: sd.InputStream | None = None
        self._lock = threading.Lock()
        self._active = False

    def start(self) -> None:
        with self._lock:
            if self._active:
                return
            self._frames = []
            self._stream = sd.InputStream(
                samplerate=self._samplerate,
                channels=self._channels,
                dtype=self._dtype,
                blocksize=self._chunk_size,
                callback=self._callback,
            )
            self._stream.start()
            self._active = True
            logger.info("开始录音")

    def stop(self) -> bytes:
        with self._lock:
            if not self._active:
                return b""
            assert self._stream is not None
            self._stream.stop()
            self._stream.close()
            actual_rate = getattr(self._stream, "samplerate", self._samplerate)
            self._stream = None
            self._active = False
            frames = self._frames
            self._frames = []
            logger.info("结束录音，帧数: {}，采样率: {}", len(frames), actual_rate)

        if not frames:
            return b""

        audio_array = np.concatenate(frames, axis=0)
        rms = float(np.sqrt(np.mean(np.square(audio_array.astype(np.float32)))))
        peak = int(np.max(np.abs(audio_array)))
        logger.debug("录音能量 RMS: {:.2f}, 峰值: {}", rms, peak)

        return audio_array.tobytes()

    def _callback(self, indata, frames, time, status) -> None:  # type: ignore[override]
        if status:
            logger.warning("录音状态: {}", status)
        with self._lock:
            if not self._active:
                return
            self._frames.append(indata.copy())

    @staticmethod
    def split_pcm(audio: bytes, chunk_size: int = 1280) -> Iterable[bytes]:
        """将 PCM 流拆分成固定大小的片段。"""
        for start in range(0, len(audio), chunk_size):
            yield audio[start : start + chunk_size]
