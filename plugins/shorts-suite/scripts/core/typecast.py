"""Shared verified Typecast access for Shorts Suite production roles."""

from __future__ import annotations

import functools
import getpass
import json
import os
from pathlib import Path
import shutil
import ssl
import subprocess
import sys
from urllib import error, request


TYPECAST_TTS_URL = "https://api.typecast.ai/v1/text-to-speech"
TYPECAST_MODEL = "ssfm-v30"
TYPECAST_KEYCHAIN_SERVICE = "news2shorts.typecast.api-key"


class TypecastError(RuntimeError):
    pass


def _keychain_api_key() -> str:
    if sys.platform != "darwin":
        return ""
    security = shutil.which("security")
    if not security:
        return ""
    try:
        result = subprocess.run(
            [
                security,
                "find-generic-password",
                "-a",
                getpass.getuser(),
                "-s",
                TYPECAST_KEYCHAIN_SERVICE,
                "-w",
            ],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
    except OSError:
        return ""
    return result.stdout.strip() if result.returncode == 0 else ""


@functools.cache
def api_key_record() -> tuple[str, str | None]:
    environment_key = os.environ.get("TYPECAST_API_KEY", "").strip()
    if environment_key:
        return environment_key, "environment"
    keychain_key = _keychain_api_key()
    if keychain_key:
        return keychain_key, "keychain"
    return "", None


def keychain_check_limited() -> bool:
    return sys.platform == "darwin" and bool(os.environ.get("CODEX_SANDBOX"))


@functools.cache
def verified_ssl_context() -> ssl.SSLContext:
    paths = ssl.get_default_verify_paths()
    if paths.cafile and Path(paths.cafile).is_file():
        return ssl.create_default_context()
    try:
        import certifi  # type: ignore

        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


def synthesize_wav(
    path: Path,
    text: str,
    *,
    voice_id: str,
    tempo: float = 1.0,
    previous_text: str = "",
    next_text: str = "",
    user_agent: str = "shorts-suite/0.1",
) -> str:
    api_key, key_source = api_key_record()
    if not api_key:
        raise TypecastError(
            "Typecast API 키가 없습니다. news2shorts.typecast.api-key 키체인 항목 또는 "
            "TYPECAST_API_KEY를 설정하세요. 로컬 TTS로 자동 대체하지 않습니다."
        )
    if not text or len(text) > 2000:
        raise TypecastError("Typecast 내레이션은 1~2,000자여야 합니다.")
    payload = {
        "voice_id": voice_id,
        "text": text,
        "model": TYPECAST_MODEL,
        "language": "kor",
        "prompt": {
            "emotion_type": "smart",
            "previous_text": previous_text[-2000:],
            "next_text": next_text[:2000],
        },
        "output": {
            "target_lufs": -14.0,
            "audio_pitch": 0,
            "audio_tempo": min(2.0, max(0.5, float(tempo))),
            "audio_format": "wav",
        },
        "seed": 42,
    }
    req = request.Request(
        TYPECAST_TTS_URL,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "X-API-KEY": api_key,
            "Content-Type": "application/json",
            "User-Agent": user_agent,
        },
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=60, context=verified_ssl_context()) as response:
            audio = response.read()
    except error.HTTPError as exc:
        detail = {
            401: "API 키",
            402: "사용량 또는 결제 상태",
            429: "요청 한도",
        }.get(exc.code, "요청 설정")
        raise TypecastError(
            f"Typecast TTS 요청 실패: HTTP {exc.code}. {detail}를 확인하세요."
        ) from exc
    except error.URLError as exc:
        raise TypecastError(f"Typecast TTS 연결 실패: {exc.reason}") from exc
    if len(audio) < 12 or audio[:4] != b"RIFF" or audio[8:12] != b"WAVE":
        raise TypecastError("Typecast TTS 응답이 WAV 오디오가 아닙니다.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(audio)
    return key_source or "unknown"
