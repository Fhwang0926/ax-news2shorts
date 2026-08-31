#!/usr/bin/env python3
"""Download a public TikTok video exposed by TikTok's official embed player.

This module never reuses a browser profile, login, cookies, or credentials. It
opens the official player in an isolated temporary Chrome profile, accepts only
TikTok-owned media URLs emitted by a video/source element, and preserves the
downloaded stream without watermark-removal processing.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import shutil
import ssl
import subprocess
import tempfile
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, HTTPSHandler, ProxyHandler, Request, build_opener


TIKTOK_PAGE_HOSTS = {"tiktok.com", "www.tiktok.com", "m.tiktok.com"}
TIKTOK_MEDIA_HOST_SUFFIXES = (
    ".tiktok.com",
    ".tiktokcdn.com",
    ".tiktokcdn-us.com",
    ".tiktokv.com",
    ".byteoversea.com",
    ".ibytedtos.com",
    ".muscdn.com",
)
CHROME_CANDIDATES = (
    Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
    Path("/Applications/Chromium.app/Contents/MacOS/Chromium"),
    Path("/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"),
)
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
)


class PublicTikTokDownloadError(RuntimeError):
    pass


@dataclass(frozen=True)
class PublicTikTokDownloadResult:
    player_url: str
    final_media_host: str
    content_type: str
    file_size_bytes: int


class _TikTokRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        _validate_media_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def parse_max_filesize(value: str) -> int:
    match = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*([KMGT]?)(?:I?B)?\s*", value, re.IGNORECASE)
    if not match:
        raise PublicTikTokDownloadError(f"지원하지 않는 최대 파일 크기 형식입니다: {value}")
    amount = float(match.group(1))
    unit = match.group(2).upper()
    multiplier = {"": 1, "K": 1024, "M": 1024**2, "G": 1024**3, "T": 1024**4}[unit]
    size = int(amount * multiplier)
    if size <= 0:
        raise PublicTikTokDownloadError("최대 파일 크기는 0보다 커야 합니다.")
    return size


def extract_tiktok_post_id(original_url: str) -> str:
    parsed = urlparse(original_url)
    hostname = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or hostname not in TIKTOK_PAGE_HOSTS or parsed.username or parsed.password:
        raise PublicTikTokDownloadError("공식 TikTok HTTPS 영상 URL만 공개 플레이어 폴백에 사용할 수 있습니다.")
    match = re.search(r"/(?:@[^/]+/video|player/v1)/(\d+)(?:/|$)", parsed.path)
    if not match:
        raise PublicTikTokDownloadError("TikTok 영상 URL에서 게시물 ID를 찾지 못했습니다.")
    return match.group(1)


def find_chrome() -> Path | None:
    for candidate in CHROME_CANDIDATES:
        if candidate.is_file():
            return candidate
    for name in ("google-chrome", "chromium", "chromium-browser", "microsoft-edge"):
        executable = shutil.which(name)
        if executable:
            return Path(executable)
    return None


def _is_tiktok_media_host(hostname: str) -> bool:
    host = hostname.lower().rstrip(".")
    return host == "www.tiktok.com" or any(host.endswith(suffix) for suffix in TIKTOK_MEDIA_HOST_SUFFIXES)


def _validate_media_url(url: str) -> None:
    parsed = urlparse(url)
    hostname = parsed.hostname or ""
    if parsed.scheme != "https" or parsed.username or parsed.password or not _is_tiktok_media_host(hostname):
        raise PublicTikTokDownloadError("공식 TikTok 미디어 호스트가 아닌 주소는 다운로드하지 않습니다.")


def _verified_ssl_context() -> ssl.SSLContext:
    try:
        import certifi  # type: ignore

        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


def select_trusted_media_url(urls: list[str]) -> str:
    for url in urls:
        try:
            _validate_media_url(url)
        except PublicTikTokDownloadError:
            continue
        return url
    raise PublicTikTokDownloadError("공식 TikTok 플레이어에서 공개 영상 주소를 찾지 못했습니다.")


def resolve_public_player_media_url(
    original_url: str,
    *,
    chrome_path: Path | None = None,
    timeout_seconds: int = 35,
) -> tuple[str, str]:
    post_id = extract_tiktok_post_id(original_url)
    player_url = (
        f"https://www.tiktok.com/player/v1/{post_id}"
        "?controls=1&description=1&autoplay=1&muted=1"
    )
    browser = chrome_path or find_chrome()
    if browser is None:
        raise PublicTikTokDownloadError("공식 공개 플레이어 폴백에 사용할 Chrome 계열 브라우저가 없습니다.")

    try:
        from websockets.sync.client import connect
    except ImportError as exc:
        raise PublicTikTokDownloadError("공식 공개 플레이어 폴백에 필요한 websockets 모듈이 없습니다.") from exc

    try:
        with tempfile.TemporaryDirectory(prefix="tiktok-public-player-") as profile_dir:
            process = subprocess.Popen(
                [
                    str(browser),
                    "--headless=new",
                    "--disable-gpu",
                    "--no-first-run",
                    "--no-default-browser-check",
                    "--remote-debugging-address=127.0.0.1",
                    "--remote-debugging-port=0",
                    "--remote-allow-origins=*",
                    f"--user-data-dir={profile_dir}",
                    "--autoplay-policy=no-user-gesture-required",
                    player_url,
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            try:
                port_file = Path(profile_dir) / "DevToolsActivePort"
                deadline = time.monotonic() + min(timeout_seconds, 15)
                while not port_file.is_file() and time.monotonic() < deadline:
                    if process.poll() is not None:
                        raise PublicTikTokDownloadError("공식 TikTok 플레이어를 열지 못했습니다.")
                    time.sleep(0.1)
                if not port_file.is_file():
                    raise PublicTikTokDownloadError("공식 TikTok 플레이어 연결 시간이 초과되었습니다.")

                port = int(port_file.read_text(encoding="utf-8").splitlines()[0])
                local_opener = build_opener(ProxyHandler({}))
                with local_opener.open(f"http://127.0.0.1:{port}/json/list", timeout=5) as response:
                    targets = json.load(response)
                target = next(
                    item
                    for item in targets
                    if item.get("type") == "page" and item.get("url") == player_url
                )
                websocket_url = target["webSocketDebuggerUrl"]
                with connect(websocket_url, open_timeout=5, close_timeout=2) as websocket:
                    request_id = 0

                    def call(method: str, params: dict[str, object] | None = None) -> dict[str, object]:
                        nonlocal request_id
                        request_id += 1
                        websocket.send(json.dumps({"id": request_id, "method": method, "params": params or {}}))
                        while True:
                            message = json.loads(websocket.recv(timeout=5))
                            if message.get("id") == request_id:
                                return message

                    call("Runtime.enable")
                    media_urls: list[str] = []
                    clicked_play = False
                    deadline = time.monotonic() + max(timeout_seconds - 15, 10)
                    while time.monotonic() < deadline:
                        result = call(
                            "Runtime.evaluate",
                            {
                                "expression": (
                                    "Array.from(document.querySelectorAll('video,source'))"
                                    ".map(e => e.currentSrc || e.src || e.getAttribute('src')).filter(Boolean)"
                                ),
                                "returnByValue": True,
                            },
                        )
                        payload = result.get("result")
                        if isinstance(payload, dict):
                            runtime_result = payload.get("result")
                            if isinstance(runtime_result, dict) and isinstance(runtime_result.get("value"), list):
                                media_urls = [url for url in runtime_result["value"] if isinstance(url, str)]
                        if media_urls:
                            return select_trusted_media_url(media_urls), player_url
                        if not clicked_play:
                            call(
                                "Runtime.evaluate",
                                {
                                    "expression": (
                                        "document.querySelector('button[aria-label=\\\"Play video\\\"]')?.click(); true"
                                    ),
                                    "returnByValue": True,
                                },
                            )
                            clicked_play = True
                        time.sleep(0.5)
                raise PublicTikTokDownloadError("공식 TikTok 플레이어에서 공개 영상 주소를 찾지 못했습니다.")
            finally:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
    except PublicTikTokDownloadError:
        raise
    except Exception as exc:
        raise PublicTikTokDownloadError("공식 TikTok 플레이어 연결에 실패했습니다.") from exc


def download_public_tiktok_video(
    original_url: str,
    output_path: Path,
    *,
    max_filesize: str = "500M",
    chrome_path: Path | None = None,
) -> PublicTikTokDownloadResult:
    if output_path.exists():
        raise PublicTikTokDownloadError(f"기존 파일을 덮어쓰지 않습니다: {output_path}")
    max_bytes = parse_max_filesize(max_filesize)
    media_url, player_url = resolve_public_player_media_url(original_url, chrome_path=chrome_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    partial_path = output_path.with_name(f"{output_path.name}.part")
    if partial_path.exists():
        raise PublicTikTokDownloadError(f"기존 임시 파일을 덮어쓰지 않습니다: {partial_path}")

    request = Request(
        media_url,
        headers={
            "Accept": "video/mp4,video/*;q=0.9,*/*;q=0.8",
            "Referer": player_url,
            "User-Agent": USER_AGENT,
        },
        method="GET",
    )
    opener = build_opener(_TikTokRedirectHandler(), HTTPSHandler(context=_verified_ssl_context()))
    total = 0
    content_type = ""
    final_url = media_url
    try:
        with opener.open(request, timeout=35) as response, partial_path.open("xb") as output:
            final_url = response.geturl()
            _validate_media_url(final_url)
            content_type = response.headers.get_content_type().lower()
            content_length = response.headers.get("Content-Length")
            if content_length and int(content_length) > max_bytes:
                raise PublicTikTokDownloadError("공개 영상이 설정한 최대 파일 크기를 초과합니다.")
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > max_bytes:
                    raise PublicTikTokDownloadError("공개 영상이 설정한 최대 파일 크기를 초과합니다.")
                output.write(chunk)
        with partial_path.open("rb") as handle:
            header = handle.read(64)
        if b"ftyp" not in header:
            raise PublicTikTokDownloadError(
                f"공식 플레이어 응답이 MP4 영상이 아닙니다: {content_type or 'unknown'}"
            )
        os.link(partial_path, output_path)
        partial_path.unlink()
    except (HTTPError, URLError, OSError, ValueError) as exc:
        raise PublicTikTokDownloadError(f"공식 TikTok 플레이어 영상 저장에 실패했습니다: {exc}") from exc
    finally:
        if partial_path.exists():
            partial_path.unlink()

    return PublicTikTokDownloadResult(
        player_url=player_url,
        final_media_host=(urlparse(final_url).hostname or "").lower(),
        content_type=content_type,
        file_size_bytes=total,
    )
