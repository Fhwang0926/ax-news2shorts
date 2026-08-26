#!/usr/bin/env python3
"""Local tooling for the healing2shorts Codex plugin.

The CLI records a user-selected story and food-video candidate, creates a
self-contained review project, renders a vertical Korean story Short, and
keeps publication readiness separate from local render success. It can fetch
an explicitly authorized HTTPS direct-media URL, but never downloads from a
Douyin page, removes source text or watermarks, or uploads externally.
"""

from __future__ import annotations

import argparse
import datetime as dt
import functools
import getpass
import hashlib
import ipaddress
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import socket
import ssl
import subprocess
import sys
import tempfile
from typing import Any
from urllib import error, request
from urllib.parse import urljoin, urlparse
from zoneinfo import ZoneInfo


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
KST = ZoneInfo("Asia/Seoul")
REVIEW_WIDTH = 540
REVIEW_HEIGHT = 960
FINAL_WIDTH = 720
FINAL_HEIGHT = 1280
OUTPUT_WIDTH = FINAL_WIDTH
OUTPUT_HEIGHT = FINAL_HEIGHT
CANVAS_WIDTH = 1080
CANVAS_HEIGHT = 1920
FRAME_RATE = 30
MIN_DURATION = 30.0
MAX_DURATION = 45.0
MEDIA_SUFFIXES = {".mp4", ".mov", ".mkv", ".webm"}
MAX_REMOTE_SOURCE_BYTES = 512 * 1024 * 1024
VIDEO_TEXT_STATUSES = {"none", "non_chinese_only", "chinese_present", "unknown"}
BLOCKED_DOWNLOAD_HOST_SUFFIXES = (
    "douyin.com",
    "iesdouyin.com",
    "snssdk.com",
    "pstatp.com",
    "byteimg.com",
)
RIGHTS_STATUSES = {
    "owned",
    "licensed",
    "permission_confirmed",
    "negotiation_pending",
    "not_permitted",
}
FINAL_RIGHTS_STATUSES = {"owned", "licensed", "permission_confirmed"}
STORY_MODES = {"article", "anecdote"}
ANECDOTE_ORIGINS = {"submitted", "public_post", "fictionalized"}
LEGACY_REQUIRED_BEATS = ("hook", "context", "conflict", "rehook", "turn", "payoff")
EVENT_REQUIRED_BEATS = (
    "cold_open",
    "setup",
    "problem",
    "clue",
    "escalation",
    "reveal",
    "afterglow",
)
REQUIRED_BEATS = LEGACY_REQUIRED_BEATS
LEGACY_STORY_SCORE_FIELDS = (
    "hook_strength",
    "emotional_arc",
    "turn_and_payoff",
    "food_visual_fit",
    "evidence_and_safety",
)
EVENT_STORY_SCORE_CAPS = {
    "hook_and_open_loop": 20,
    "character_and_event": 15,
    "tension_and_progression": 20,
    "reveal_and_payoff": 25,
    "spoken_naturalness": 10,
    "food_action_sync": 10,
}
STORY_ENGINES = {
    "missing_routine",
    "object_mystery",
    "misunderstanding_reveal",
    "quiet_sacrifice",
    "returned_promise",
}
EVENT_STORY_REQUIRED_FIELDS = (
    "anchor_event",
    "protagonist",
    "central_question",
    "obstacle",
    "reveal",
    "payoff_object",
)
EVENT_STORY_MIN_BEST_SCORE = 70
DIALOGUE_STORY_CONTRACT_VERSION = 3
DIALOGUE_STORY_MIN_DURATION = 40.0
DIALOGUE_STORY_MIN_TURNS = 10
DIALOGUE_STORY_MAX_TURNS = 14
DIALOGUE_STORY_MIN_SPEAKER_CHANGES = 7
DIALOGUE_STORY_MIN_TEXT_RATIO = 0.6
SENSITIVE_TOPICS = {
    "crime",
    "death",
    "minor",
    "medical",
    "self_harm",
    "severe_family_conflict",
}
APPROVALS = (
    "story_reviewed",
    "visual_reviewed",
    "rights_reviewed",
    "sensitive_reviewed",
    "upload_reviewed",
)
FONT_CANDIDATES = (
    Path("/System/Library/Fonts/AppleSDGothicNeo.ttc"),
    Path("/Library/Fonts/NotoSansKR-Regular.otf"),
    Path("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
)
TYPECAST_TTS_URL = "https://api.typecast.ai/v1/text-to-speech"
TYPECAST_MODEL = "ssfm-v30"
TYPECAST_VOICE_ID = "tc_692799c46508f6b9468c54c7"
TYPECAST_VOICE_NAME = "Daeun"
TYPECAST_DIALOGUE_VOICES = {
    "Daeun": {
        "voice_id": "tc_692799c46508f6b9468c54c7",
        "tempo": 1.10,
        "profile": "warm-story-narrator",
    },
    "Moonjung": {
        "voice_id": "tc_68f9c6a72f0f04a417bb136f",
        "tempo": 1.08,
        "profile": "warm-elderly-character",
    },
}
AMBIENT_MODES = {"synthetic_gentle", "synthetic_emotional", "synthetic_melancholy"}
DIALOGUE_TURN_GAP = 0.18
EMOTIONAL_BGM_CHORDS = (
    (220.00, 261.63, 329.63),
    (174.61, 220.00, 261.63),
    (130.81, 164.81, 196.00),
    (196.00, 246.94, 293.66),
    (220.00, 261.63, 329.63),
    (174.61, 220.00, 261.63),
    (130.81, 164.81, 196.00),
)
TYPECAST_KEYCHAIN_SERVICE = "news2shorts.typecast.api-key"
TYPECAST_SETUP_COMMAND = "python3 plugins/news2shorts/scripts/news2shorts.py configure-typecast"


class HealingShortsError(RuntimeError):
    pass


def now_kst() -> dt.datetime:
    return dt.datetime.now(KST)


def iso_now() -> str:
    return now_kst().isoformat(timespec="seconds")


def text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise HealingShortsError(f"{label}은(는) 숫자여야 합니다.")
    return float(value)


def require_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise HealingShortsError(f"{label}은(는) JSON 객체여야 합니다.")
    return value


def require_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise HealingShortsError(f"{label}은(는) 배열이어야 합니다.")
    return value


def load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError as exc:
        raise HealingShortsError(f"필수 파일이 없습니다: {path}") from exc
    except json.JSONDecodeError as exc:
        raise HealingShortsError(f"JSON 형식이 잘못되었습니다: {path}: {exc}") from exc


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def slugify(value: str) -> str:
    cleaned = re.sub(r"[^0-9A-Za-z가-힣]+", "-", value.strip().lower()).strip("-")
    return cleaned[:72] or "healing-short"


def sha256_for(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_checked(command: list[str], label: str) -> subprocess.CompletedProcess[str]:
    try:
        result = subprocess.run(
            command,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except OSError as exc:
        raise HealingShortsError(f"{label} 실행 실패: {exc}") from exc
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip() or "알 수 없는 오류"
        raise HealingShortsError(f"{label} 실패: {detail}")
    return result


def resolve_project_path(project_dir: Path, relative: str, *, must_exist: bool = True) -> Path:
    if not relative:
        raise HealingShortsError("빈 프로젝트 상대 경로는 사용할 수 없습니다.")
    candidate = (project_dir / relative).resolve()
    try:
        candidate.relative_to(project_dir.resolve())
    except ValueError as exc:
        raise HealingShortsError(f"프로젝트 밖의 경로는 사용할 수 없습니다: {relative}") from exc
    if must_exist and not candidate.is_file():
        raise HealingShortsError(f"프로젝트 파일을 찾을 수 없습니다: {relative}")
    return candidate


def relative_project_path(project_dir: Path, path: Path) -> str:
    return path.resolve().relative_to(project_dir.resolve()).as_posix()


def public_url(value: str, label: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise HealingShortsError(f"{label}은(는) 공개 http 또는 https URL이어야 합니다.")
    if parsed.username or parsed.password:
        raise HealingShortsError(f"{label}에는 사용자 정보가 포함될 수 없습니다.")
    return value


def blocked_download_host(hostname: str) -> bool:
    normalized = hostname.rstrip(".").lower()
    return any(
        normalized == suffix or normalized.endswith(f".{suffix}")
        for suffix in BLOCKED_DOWNLOAD_HOST_SUFFIXES
    )


def require_public_download_host(hostname: str) -> None:
    if not hostname:
        raise HealingShortsError("직접 원본 URL의 호스트가 비었습니다.")
    if hostname.lower() == "localhost" or hostname.lower().endswith(".local"):
        raise HealingShortsError("로컬·사설 호스트에서는 원본을 가져올 수 없습니다.")
    try:
        addresses = {ipaddress.ip_address(hostname)}
    except ValueError:
        try:
            resolved = socket.getaddrinfo(hostname, 443, type=socket.SOCK_STREAM)
        except socket.gaierror as exc:
            raise HealingShortsError(f"직접 원본 URL 호스트를 확인할 수 없습니다: {hostname}") from exc
        addresses = {ipaddress.ip_address(item[4][0]) for item in resolved}
    if not addresses or any(not address.is_global for address in addresses):
        raise HealingShortsError("직접 원본 URL은 공개 인터넷 호스트여야 합니다.")


def authorized_source_url(value: str, label: str = "authorized source URL") -> str:
    public_url(value, label)
    parsed = urlparse(value)
    if parsed.scheme != "https":
        raise HealingShortsError(f"{label}은(는) HTTPS URL이어야 합니다.")
    hostname = (parsed.hostname or "").rstrip(".").lower()
    if blocked_download_host(hostname):
        raise HealingShortsError(
            "도우인 페이지·CDN 자동 다운로드는 지원하지 않습니다. "
            "제작자나 라이선스 제공처가 준 직접 원본 URL을 사용하세요."
        )
    require_public_download_host(hostname)
    return value


def url_without_secret_query(value: str) -> str:
    parsed = urlparse(value)
    return parsed._replace(query="", fragment="").geturl()


class AuthorizedRedirectHandler(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        destination = urljoin(req.full_url, newurl)
        authorized_source_url(destination, "redirected source URL")
        return super().redirect_request(req, fp, code, msg, headers, destination)


def download_authorized_source(url: str, destination_dir: Path) -> tuple[Path, dict[str, Any]]:
    checked_url = authorized_source_url(url)
    opener = request.build_opener(AuthorizedRedirectHandler())
    source_request = request.Request(
        checked_url,
        headers={
            "User-Agent": "healing2shorts/0.2 authorized-source-import",
            "Accept": "video/*, application/octet-stream;q=0.8",
        },
    )
    try:
        response = opener.open(source_request, timeout=45)
    except error.HTTPError as exc:
        raise HealingShortsError(f"권리 확인 원본 가져오기 실패: HTTP {exc.code}") from exc
    except error.URLError as exc:
        raise HealingShortsError(f"권리 확인 원본 가져오기 실패: {exc.reason}") from exc
    with response:
        final_url = authorized_source_url(response.geturl(), "final source URL")
        content_type = response.headers.get_content_type().lower()
        suffix = Path(urlparse(final_url).path).suffix.lower()
        if suffix not in MEDIA_SUFFIXES:
            suffix = {
                "video/mp4": ".mp4",
                "video/quicktime": ".mov",
                "video/x-matroska": ".mkv",
                "video/webm": ".webm",
            }.get(content_type, ".mp4")
        if not (content_type.startswith("video/") or content_type == "application/octet-stream"):
            raise HealingShortsError(
                f"직접 원본 URL이 영상 응답이 아닙니다: {content_type or 'unknown'}"
            )
        raw_length = response.headers.get("Content-Length", "").strip()
        if raw_length.isdigit() and int(raw_length) > MAX_REMOTE_SOURCE_BYTES:
            raise HealingShortsError("직접 원본 영상은 512MB 이하여야 합니다.")
        destination_dir.mkdir(parents=True, exist_ok=True)
        destination = destination_dir / f"authorized-source{suffix}"
        received = 0
        try:
            with destination.open("wb") as handle:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    received += len(chunk)
                    if received > MAX_REMOTE_SOURCE_BYTES:
                        raise HealingShortsError("직접 원본 영상은 512MB 이하여야 합니다.")
                    handle.write(chunk)
        except Exception:
            destination.unlink(missing_ok=True)
            raise
    if received <= 0:
        destination.unlink(missing_ok=True)
        raise HealingShortsError("직접 원본 URL에서 빈 파일을 받았습니다.")
    return destination, {
        "method": "authorized_https_direct_media",
        "automated_download": True,
        "downloaded_at": iso_now(),
        "direct_url": url_without_secret_query(final_url),
        "bytes": received,
        "watermark_removed": False,
        "source_text_removed": False,
    }


def media_probe(path: Path) -> dict[str, Any]:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        raise HealingShortsError("ffprobe가 필요합니다. doctor 결과를 확인하세요.")
    result = run_checked(
        [
            ffprobe,
            "-v",
            "error",
            "-show_streams",
            "-show_format",
            "-of",
            "json",
            str(path),
        ],
        "미디어 정보 확인",
    )
    payload = require_object(json.loads(result.stdout), "ffprobe 결과")
    streams = require_list(payload.get("streams", []), "ffprobe streams")
    video = next((item for item in streams if item.get("codec_type") == "video"), None)
    audio = next((item for item in streams if item.get("codec_type") == "audio"), None)
    if not isinstance(video, dict):
        raise HealingShortsError(f"영상 스트림이 없습니다: {path}")
    raw_duration = payload.get("format", {}).get("duration") or video.get("duration") or 0
    try:
        duration = float(raw_duration)
    except (TypeError, ValueError) as exc:
        raise HealingShortsError(f"영상 길이를 확인할 수 없습니다: {path}") from exc
    raw_rate = text(video.get("avg_frame_rate") or video.get("r_frame_rate"))
    frame_rate = 0.0
    if "/" in raw_rate:
        numerator, denominator = raw_rate.split("/", 1)
        try:
            frame_rate = float(numerator) / max(float(denominator), 1.0)
        except ValueError:
            frame_rate = 0.0
    return {
        "duration_seconds": round(duration, 3),
        "width": int(video.get("width") or 0),
        "height": int(video.get("height") or 0),
        "frame_rate": round(frame_rate, 3),
        "video_codec": text(video.get("codec_name")),
        "audio_codec": text(audio.get("codec_name")) if isinstance(audio, dict) else "",
        "has_audio": isinstance(audio, dict),
    }


def audio_duration(path: Path) -> float:
    ffprobe = shutil.which("ffprobe") or "ffprobe"
    result = run_checked(
        [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        "오디오 길이 확인",
    )
    try:
        return float(result.stdout.strip())
    except ValueError as exc:
        raise HealingShortsError(f"오디오 길이를 확인할 수 없습니다: {path}") from exc


def find_font() -> Path:
    for candidate in FONT_CANDIDATES:
        if candidate.is_file():
            return candidate
    raise HealingShortsError("한글 렌더링에 사용할 폰트를 찾지 못했습니다.")


def load_font(size: int, *, bold: bool = False):
    from PIL import ImageFont

    path = find_font()
    if bold and path.name == "AppleSDGothicNeo.ttc":
        return ImageFont.truetype(str(path), size=size, index=14)
    if bold:
        for candidate in (
            path.with_name("NotoSansKR-Bold.otf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        ):
            if candidate.is_file():
                return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.truetype(str(path), size=size)


def candidate_by_id(payload: Any, candidate_id: str, label: str) -> dict[str, Any]:
    root = require_object(payload, label)
    candidates = require_list(root.get("candidates", []), f"{label}.candidates")
    if not 1 <= len(candidates) <= 3:
        raise HealingShortsError(f"{label} 후보는 1~3개여야 합니다: {len(candidates)}")
    if root.get("selection_required") is not True:
        raise HealingShortsError(f"{label}.selection_required는 true여야 합니다.")
    if label == "story candidates":
        validate_story_recommendation(root, candidates)
    matches = [item for item in candidates if isinstance(item, dict) and text(item.get("id")) == candidate_id]
    if len(matches) != 1:
        raise HealingShortsError(f"{label}에서 후보 ID를 하나 찾을 수 없습니다: {candidate_id}")
    selected = matches[0]
    if label == "video candidates":
        video_text_profile(selected)
    return selected


def validate_story_recommendation(
    root: dict[str, Any], candidates: list[Any]
) -> dict[str, Any]:
    contract_version = root.get("version", 1)
    if isinstance(contract_version, bool) or contract_version not in {1, 2, 3}:
        raise HealingShortsError("story candidates.version은 1, 2 또는 3이어야 합니다.")
    best_candidate_id = text(root.get("best_candidate_id"))
    best_candidate_reason = text(root.get("best_candidate_reason"))
    if not best_candidate_id or not best_candidate_reason:
        raise HealingShortsError(
            "story candidates에는 best_candidate_id와 best_candidate_reason이 필요합니다."
        )
    rankings: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for index, value in enumerate(candidates, start=1):
        candidate = require_object(value, f"story candidate {index}")
        candidate_id = text(candidate.get("id"))
        if not candidate_id or candidate_id in seen_ids:
            raise HealingShortsError("스토리 후보 id는 비어 있지 않은 고유 값이어야 합니다.")
        seen_ids.add(candidate_id)
        candidate_version = candidate.get("contract_version", contract_version)
        if candidate_version != contract_version:
            raise HealingShortsError(
                f"{candidate_id}.contract_version은 최상위 version과 같아야 합니다."
            )
        normalize_beats(candidate, contract_version=contract_version)
        if contract_version in {2, 3}:
            gate_errors: list[str] = []
            gate_warnings: list[str] = []
            validate_story_source(
                candidate,
                gate_errors,
                gate_warnings,
                publish_ready=False,
            )
            if gate_errors:
                raise HealingShortsError(
                    f"{candidate_id} 출처·사연 안전 게이트 실패: " + "; ".join(gate_errors)
                )
        score = require_object(candidate.get("story_score"), f"{candidate_id}.story_score")
        values: dict[str, int] = {}
        score_caps = (
            EVENT_STORY_SCORE_CAPS
            if contract_version in {2, 3}
            else {field: 20 for field in LEGACY_STORY_SCORE_FIELDS}
        )
        for field, cap in score_caps.items():
            value = score.get(field)
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= cap:
                raise HealingShortsError(
                    f"{candidate_id}.story_score.{field}는 0~{cap} 정수여야 합니다."
                )
            values[field] = value
        total = score.get("total")
        if isinstance(total, bool) or not isinstance(total, int) or total != sum(values.values()):
            raise HealingShortsError(
                f"{candidate_id}.story_score.total은 점수 항목의 합과 같아야 합니다."
            )
        if not text(score.get("reason")):
            raise HealingShortsError(f"{candidate_id}.story_score.reason이 필요합니다.")
        rankings.append({"id": candidate_id, "total": total, **values})
    if contract_version in {2, 3}:
        expected_best = max(
            rankings,
            key=lambda item: (
                item["total"],
                item["hook_and_open_loop"],
                item["reveal_and_payoff"],
                item["tension_and_progression"],
            ),
        )
        if expected_best["total"] < EVENT_STORY_MIN_BEST_SCORE:
            raise HealingShortsError(
                "사건형 후보의 최고점이 70점 미만입니다. BEST를 정하지 말고 후보를 다시 조사하세요."
            )
    else:
        expected_best = max(
            rankings,
            key=lambda item: (
                item["total"],
                item["hook_strength"],
                item["turn_and_payoff"],
                item["food_visual_fit"],
            ),
        )
    if best_candidate_id != expected_best["id"]:
        raise HealingShortsError(
            f"best_candidate_id는 최고점 후보 {expected_best['id']}여야 합니다."
        )
    return {
        "best_candidate_id": best_candidate_id,
        "best_candidate_reason": best_candidate_reason,
        "contract_version": contract_version,
    }


def normalize_beats(
    candidate: dict[str, Any], *, contract_version: int = 1
) -> list[dict[str, Any]]:
    if contract_version in {2, 3}:
        story_engine = text(candidate.get("story_engine"))
        if story_engine not in STORY_ENGINES:
            raise HealingShortsError(
                "사건형 후보 story_engine은 지원되는 다섯 유형 중 하나여야 합니다."
            )
        for field in EVENT_STORY_REQUIRED_FIELDS:
            if not text(candidate.get(field)):
                raise HealingShortsError(f"사건형 후보에는 {field}가 필요합니다.")
        required_beats = EVENT_REQUIRED_BEATS
    else:
        required_beats = LEGACY_REQUIRED_BEATS
    beats = require_list(candidate.get("beats", []), "story candidate beats")
    if len(beats) != len(required_beats):
        raise HealingShortsError(
            f"선택한 스토리 후보에는 정확히 {len(required_beats)}개 기본 비트가 필요합니다."
        )
    mode = text(candidate.get("mode"))
    if mode not in STORY_MODES:
        raise HealingShortsError("스토리 후보 mode는 article 또는 anecdote여야 합니다.")
    raw_claims = candidate.get("claims", [])
    if contract_version == 3 and mode != "anecdote":
        raise HealingShortsError("대화형 힐링 썰 v3 후보는 anecdote 모드여야 합니다.")
    if contract_version in {2, 3} and mode == "article" and not isinstance(raw_claims, list):
        raise HealingShortsError("기사형 후보 claims는 배열이어야 합니다.")
    claim_ids = {
        text(item.get("id"))
        for item in (raw_claims if isinstance(raw_claims, list) else [])
        if isinstance(item, dict) and text(item.get("id"))
    }
    normalized: list[dict[str, Any]] = []
    for index, expected in enumerate(required_beats):
        beat = require_object(beats[index], f"story beat {index + 1}")
        actual = text(beat.get("beat"))
        if actual != expected:
            raise HealingShortsError(
                f"스토리 비트 순서가 잘못되었습니다: {index + 1}은 {expected}여야 합니다."
            )
        caption = text(beat.get("caption"))
        narration = text(beat.get("narration"))
        if not caption or not narration:
            raise HealingShortsError(f"{expected} 비트에는 caption과 narration이 필요합니다.")
        if contract_version == 3 and any(
            re.match(r"^\s*[^:：\n]{1,10}\s*[:：]\s*", line)
            for line in caption.splitlines()
        ):
            raise HealingShortsError(
                "대화형 화면 자막에는 '할머니:' 같은 화자 라벨을 넣지 말고 실제 문구만 사용하세요."
            )
        normalized_beat = {"beat": expected, "caption": caption, "narration": narration}
        if contract_version in {2, 3}:
            linked_claims = beat.get("claim_ids", [])
            if mode == "article":
                if not isinstance(linked_claims, list) or not linked_claims:
                    raise HealingShortsError(f"기사형 {expected} 비트에는 claim_ids가 필요합니다.")
                unknown_claims = {str(item) for item in linked_claims} - claim_ids
                if unknown_claims:
                    raise HealingShortsError(
                        f"{expected} 비트가 존재하지 않는 claim을 참조합니다: "
                        + ", ".join(sorted(unknown_claims))
                    )
            elif linked_claims and not isinstance(linked_claims, list):
                raise HealingShortsError(f"{expected}.claim_ids는 배열이어야 합니다.")
            normalized_beat["claim_ids"] = (
                list(linked_claims) if isinstance(linked_claims, list) else []
            )
        if contract_version == 3:
            turn_ids = beat.get("dialogue_turn_ids")
            if not isinstance(turn_ids, list) or not turn_ids or any(
                not text(value) for value in turn_ids
            ):
                raise HealingShortsError(
                    f"대화형 {expected} 비트에는 dialogue_turn_ids가 필요합니다."
                )
            normalized_beat["dialogue_turn_ids"] = [text(value) for value in turn_ids]
        normalized.append(normalized_beat)
    if contract_version == 3:
        validate_dialogue_story(candidate, normalized)
    if contract_version in {2, 3} and mode == "article":
        cold_open_claims = set(normalized[0]["claim_ids"])
        reveal_claims = set(normalized[5]["claim_ids"])
        if not reveal_claims - cold_open_claims:
            raise HealingShortsError(
                "reveal 비트에는 cold_open에서 아직 밝히지 않은 새 claim이 최소 1개 필요합니다."
            )
    return normalized


def validate_dialogue_story(
    candidate: dict[str, Any], beats: list[dict[str, Any]]
) -> None:
    turns = require_list(candidate.get("dialogue_turns", []), "dialogue_turns")
    if not DIALOGUE_STORY_MIN_TURNS <= len(turns) <= DIALOGUE_STORY_MAX_TURNS:
        raise HealingShortsError(
            "대화형 힐링 썰에는 10~14개의 대사가 필요합니다."
        )
    normalized_turns: list[dict[str, str]] = []
    seen_ids: set[str] = set()
    for index, value in enumerate(turns, start=1):
        turn = require_object(value, f"dialogue turn {index}")
        turn_id = text(turn.get("id"))
        speaker = text(turn.get("speaker"))
        turn_text = text(turn.get("text"))
        if not turn_id or turn_id in seen_ids:
            raise HealingShortsError("dialogue_turns.id는 비어 있지 않은 고유 값이어야 합니다.")
        if not speaker or not turn_text:
            raise HealingShortsError("각 dialogue turn에는 speaker와 text가 필요합니다.")
        seen_ids.add(turn_id)
        normalized_turns.append({"id": turn_id, "speaker": speaker, "text": turn_text})
    speakers = {turn["speaker"] for turn in normalized_turns}
    if not 2 <= len(speakers) <= 3:
        raise HealingShortsError("대화형 힐링 썰에는 2~3명의 화자가 필요합니다.")
    speaker_changes = sum(
        current["speaker"] != previous["speaker"]
        for previous, current in zip(normalized_turns, normalized_turns[1:])
    )
    if speaker_changes < DIALOGUE_STORY_MIN_SPEAKER_CHANGES:
        raise HealingShortsError(
            "대화형 힐링 썰에는 화자 교대가 7회 이상 필요합니다."
        )
    ordered_ids = [turn["id"] for turn in normalized_turns]
    used_ids = [
        turn_id
        for beat in beats
        for turn_id in beat.get("dialogue_turn_ids", [])
    ]
    if used_ids != ordered_ids:
        raise HealingShortsError(
            "각 대사는 7개 비트에서 원래 순서대로 정확히 한 번 사용해야 합니다."
        )
    turns_by_id = {turn["id"]: turn for turn in normalized_turns}
    for beat in beats:
        narration = text(beat.get("narration"))
        for turn_id in beat.get("dialogue_turn_ids", []):
            turn = turns_by_id[turn_id]
            if turn["text"] not in narration:
                raise HealingShortsError(
                    f"{beat['beat']} 내레이션에 {turn_id} 대사가 포함되어야 합니다."
                )
    dialogue_characters = sum(len(re.sub(r"\s+", "", turn["text"])) for turn in normalized_turns)
    narration_characters = sum(len(re.sub(r"\s+", "", text(beat.get("narration")))) for beat in beats)
    if not narration_characters or dialogue_characters / narration_characters < DIALOGUE_STORY_MIN_TEXT_RATIO:
        raise HealingShortsError("대화문이 전체 내레이션 글자의 60% 이상이어야 합니다.")


def video_text_profile(
    candidate: dict[str, Any], *, required_segments: int = len(LEGACY_REQUIRED_BEATS)
) -> tuple[str, list[dict[str, float]]]:
    status = text(candidate.get("visual_text_status")) or "unknown"
    if status not in VIDEO_TEXT_STATUSES:
        raise HealingShortsError(
            "video candidate visual_text_status는 none, non_chinese_only, "
            "chinese_present 또는 unknown이어야 합니다."
        )
    raw_segments = candidate.get("text_free_segments", [])
    if not isinstance(raw_segments, list):
        raise HealingShortsError("video candidate text_free_segments는 배열이어야 합니다.")
    segments: list[dict[str, float]] = []
    for index, value in enumerate(raw_segments, start=1):
        segment = require_object(value, f"text_free_segment {index}")
        start = number(segment.get("start_seconds"), f"text_free_segment {index}.start_seconds")
        duration = number(
            segment.get("duration_seconds"), f"text_free_segment {index}.duration_seconds"
        )
        if start < 0 or duration < 0.5:
            raise HealingShortsError("중국어 없는 추천 구간은 시작 0초 이상, 길이 0.5초 이상이어야 합니다.")
        segments.append(
            {"start_seconds": round(start, 3), "duration_seconds": round(duration, 3)}
        )
    if status == "chinese_present" and len(segments) < required_segments:
        raise HealingShortsError(
            "중국어가 보이는 후보는 원문 삭제 대신 서로 다른 중국어 없는 구간 "
            f"{required_segments}개 이상이 필요합니다."
        )
    return status, segments


def default_project_dir(title: str, output_root: str) -> Path:
    date_value = now_kst().date().isoformat()
    return Path(output_root).expanduser().resolve() / date_value / slugify(title)


def copy_source_video(source: Path, project_dir: Path) -> tuple[Path, dict[str, Any]]:
    if not source.is_file():
        raise HealingShortsError(f"로컬 음식 영상이 없습니다: {source}")
    if source.suffix.lower() not in MEDIA_SUFFIXES:
        raise HealingShortsError("음식 영상은 MP4, MOV, MKV 또는 WebM이어야 합니다.")
    probe = media_probe(source)
    if probe["duration_seconds"] < 6:
        raise HealingShortsError("음식 영상은 자연스러운 구간 선택을 위해 최소 6초가 필요합니다.")
    destination = project_dir / "assets" / "source" / f"food-source{source.suffix.lower()}"
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return destination, probe


def story_source_from_candidate(
    candidate: dict[str, Any], recommendation: dict[str, Any], *, contract_version: int
) -> dict[str, Any]:
    mode = text(candidate.get("mode"))
    if mode not in STORY_MODES:
        raise HealingShortsError("스토리 후보 mode는 article 또는 anecdote여야 합니다.")
    source = {
        "version": contract_version,
        "story_contract_version": contract_version,
        "selected_at": iso_now(),
        "id": text(candidate.get("id")),
        "mode": mode,
        "title": text(candidate.get("title")),
        "selection_reason": text(candidate.get("selection_reason")),
        "emotional_arc": text(candidate.get("emotional_arc")),
        "story_score": candidate.get("story_score", {}),
        "recommendation": {
            **recommendation,
            "selected_was_best": text(candidate.get("id"))
            == recommendation["best_candidate_id"],
        },
        "sensitive_topics": candidate.get("sensitive_topics", []),
        "sources": candidate.get("sources", []),
        "claims": candidate.get("claims", []),
        "anecdote": candidate.get("anecdote", {}),
        "candidate_snapshot": candidate,
    }
    if contract_version in {2, 3}:
        for field in ("story_engine", *EVENT_STORY_REQUIRED_FIELDS):
            source[field] = candidate.get(field)
    if contract_version == 3:
        source["dialogue_turns"] = candidate.get("dialogue_turns", [])
    if not source["id"] or not source["title"]:
        raise HealingShortsError("선택한 스토리 후보에는 id와 title이 필요합니다.")
    require_list(source["sensitive_topics"], "sensitive_topics")
    return source


def video_source_from_candidate(
    candidate: dict[str, Any],
    project_dir: Path,
    source_path: Path,
    probe: dict[str, Any],
    acquisition: dict[str, Any],
) -> dict[str, Any]:
    status = text(candidate.get("rights_status"))
    if status not in RIGHTS_STATUSES:
        raise HealingShortsError(f"지원하지 않는 영상 권리 상태입니다: {status or 'empty'}")
    if status == "not_permitted":
        raise HealingShortsError("not_permitted 영상 후보는 프로젝트에 연결할 수 없습니다.")
    source_url = text(candidate.get("source_url"))
    if source_url:
        public_url(source_url, "video source_url")
    visual_text_status, text_free_segments = video_text_profile(candidate)
    return {
        "version": 1,
        "selected_at": iso_now(),
        "id": text(candidate.get("id")),
        "platform": text(candidate.get("platform")) or "local",
        "source_url": source_url,
        "creator": text(candidate.get("creator")),
        "scene_summary": text(candidate.get("scene_summary")),
        "selection_reason": text(candidate.get("selection_reason")),
        "collected_at": text(candidate.get("collected_at")),
        "watermark_present": candidate.get("watermark_present"),
        "visual_text": {
            "status": visual_text_status,
            "text_free_segments": text_free_segments,
            "review_note": text(candidate.get("visual_text_review_note")),
            "source_text_removed": False,
        },
        "local_path": relative_project_path(project_dir, source_path),
        "sha256": sha256_for(source_path),
        "probe": probe,
        "rights": {
            "status": status,
            "rights_holder": text(candidate.get("creator")),
            "permission_date": "",
            "youtube_scope": False,
            "commercial_use": False,
            "editing_allowed": False,
            "voice_overlay_allowed": False,
            "source_asmr_approved": False,
            "attribution": "",
            "expires_at": "",
            "permission_reference": "",
            "permission_reference_sha256": "",
        },
        "candidate_snapshot": candidate,
        "acquisition": acquisition,
    }


def create_storyboard(
    beats: list[dict[str, Any]],
    source_duration: float,
    target_duration: float,
    video_candidate: dict[str, Any],
    *,
    contract_version: int = 1,
) -> dict[str, Any]:
    durations = storyboard_durations(beats, target_duration, contract_version=contract_version)
    visual_text_status, text_free_segments = video_text_profile(
        video_candidate, required_segments=len(beats)
    )
    scenes: list[dict[str, Any]] = []
    for index, (beat, scene_duration) in enumerate(zip(beats, durations), start=1):
        source_chunk = max(0.5, min(scene_duration, source_duration / len(beats)))
        max_start = max(0.0, source_duration - source_chunk)
        if len(text_free_segments) >= len(beats):
            selected_segment = text_free_segments[index - 1]
            start = selected_segment["start_seconds"]
            selected_duration = min(source_chunk, selected_segment["duration_seconds"])
            scene_text_status = "none"
        else:
            ratio = (index - 1) / max(len(beats) - 1, 1)
            start = max_start * ratio
            selected_duration = min(source_chunk, source_duration - start)
            scene_text_status = visual_text_status
        if start + selected_duration > source_duration:
            raise HealingShortsError(
                f"중국어 없는 추천 구간이 원본 영상 범위를 벗어났습니다: scene-{index:02d}"
            )
        scenes.append(
            {
                "id": f"scene-{index:02d}",
                "beat": beat["beat"],
                "duration": scene_duration,
                "source_start_seconds": round(start, 3),
                "source_duration_seconds": round(selected_duration, 3),
                "source_text_status": scene_text_status,
                "caption": beat["caption"],
                "narration": beat["narration"],
                "claim_ids": beat.get("claim_ids", []),
                "dialogue_turn_ids": beat.get("dialogue_turn_ids", []),
                "narration_audio": "",
            }
        )
    return {
        "version": 1,
        "story_contract_version": contract_version,
        "title": "",
        "selected_story_id": "",
        "total_duration_seconds": round(target_duration, 3),
        "scenes": scenes,
    }


def storyboard_durations(
    beats: list[dict[str, Any]], target_duration: float, *, contract_version: int = 1
) -> list[float]:
    if contract_version not in {2, 3}:
        duration = round(target_duration / len(beats), 3)
        durations = [duration] * len(beats)
        durations[-1] = round(durations[-1] + target_duration - sum(durations), 3)
        return durations
    if [text(item.get("beat")) for item in beats] != list(EVENT_REQUIRED_BEATS):
        raise HealingShortsError("사건형 스토리보드는 7개 비트를 순서대로 사용해야 합니다.")
    if contract_version == 3 and target_duration < DIALOGUE_STORY_MIN_DURATION:
        raise HealingShortsError("대화형 힐링 썰은 40~45초로 제작해야 합니다.")
    cold_open = 2.5
    weights = [4.5, 5.5, 5.0, 6.0, 6.0, 6.5]
    durations = [3.0] * len(weights)
    remaining = target_duration - cold_open - sum(durations)
    if remaining < 0:
        raise HealingShortsError("사건형 스토리보드 길이가 너무 짧습니다.")
    active = set(range(len(weights)))
    while remaining > 0.000001 and active:
        weight_total = sum(weights[index] for index in active)
        capped: list[int] = []
        for index in active:
            increment = remaining * weights[index] / weight_total
            if durations[index] + increment > 8.0:
                capped.append(index)
        if not capped:
            for index in active:
                durations[index] += remaining * weights[index] / weight_total
            remaining = 0.0
            break
        for index in capped:
            remaining -= 8.0 - durations[index]
            durations[index] = 8.0
            active.remove(index)
    result = [cold_open, *durations]
    result = [round(value, 3) for value in result]
    result[-1] = round(result[-1] + target_duration - sum(result), 3)
    return result


def script_markdown(title: str, story_source: dict[str, Any], storyboard: dict[str, Any]) -> str:
    lines = [f"# {title}", "", f"- mode: {story_source['mode']}", "- status: review-only script", ""]
    for scene in storyboard["scenes"]:
        lines.extend(
            [
                f"## {scene['id']} · {scene['beat']}",
                "",
                f"화면: {scene['caption']}",
                "",
                f"내레이션: {scene['narration']}",
                "",
            ]
        )
    lines.append("이 문서는 검토용이며 실제 렌더 타임라인은 storyboard.json입니다.")
    lines.append("")
    return "\n".join(lines)


def command_init(args: argparse.Namespace) -> int:
    story_payload = load_json(Path(args.story_candidates).expanduser().resolve())
    video_payload = load_json(Path(args.video_candidates).expanduser().resolve())
    story_candidate = candidate_by_id(story_payload, args.story_id, "story candidates")
    video_candidate = candidate_by_id(video_payload, args.video_id, "video candidates")
    story_root = require_object(story_payload, "story candidates")
    story_recommendation = validate_story_recommendation(
        story_root,
        require_list(story_root.get("candidates", []), "story candidates.candidates"),
    )
    contract_version = int(story_recommendation["contract_version"])
    beats = normalize_beats(story_candidate, contract_version=contract_version)
    title = args.title or text(story_candidate.get("title")) or "힐링쇼츠"
    target_duration = (
        args.duration
        if args.duration is not None
        else 42.0 if contract_version == DIALOGUE_STORY_CONTRACT_VERSION else 36.0
    )
    if not MIN_DURATION <= target_duration <= MAX_DURATION:
        raise HealingShortsError(
            f"--duration은 {MIN_DURATION:.0f}~{MAX_DURATION:.0f}초여야 합니다."
        )
    if contract_version == DIALOGUE_STORY_CONTRACT_VERSION and target_duration < DIALOGUE_STORY_MIN_DURATION:
        raise HealingShortsError("대화형 힐링 썰의 --duration은 40~45초여야 합니다.")
    project_dir = (
        Path(args.project_dir).expanduser().resolve()
        if args.project_dir
        else default_project_dir(title, args.output_root)
    )
    if project_dir.exists():
        raise HealingShortsError(f"프로젝트 경로가 이미 존재합니다: {project_dir}")
    rights_status = text(video_candidate.get("rights_status"))
    temporary_source: tempfile.TemporaryDirectory[str] | None = None
    if args.source_video:
        selected_source = Path(args.source_video).expanduser().resolve()
        acquisition = {
            "method": "user_or_creator_supplied_local_file",
            "automated_download": False,
            "watermark_removed": False,
            "source_text_removed": False,
        }
    else:
        if rights_status not in FINAL_RIGHTS_STATUSES:
            raise HealingShortsError(
                "자동 원본 가져오기는 owned, licensed 또는 permission_confirmed 후보만 허용합니다."
            )
        if not args.confirm_download_rights:
            raise HealingShortsError(
                "직접 원본 URL의 다운로드·편집 권리가 있으면 --confirm-download-rights를 추가하세요."
            )
        temporary_source = tempfile.TemporaryDirectory(prefix="healing2shorts-authorized-source-")
        selected_source, acquisition = download_authorized_source(
            args.authorized_source_url, Path(temporary_source.name)
        )
    try:
        project_dir.mkdir(parents=True)
        source_path, probe = copy_source_video(selected_source, project_dir)
    finally:
        if temporary_source is not None:
            temporary_source.cleanup()
    story_source = story_source_from_candidate(
        story_candidate, story_recommendation, contract_version=contract_version
    )
    video_source = video_source_from_candidate(
        video_candidate, project_dir, source_path, probe, acquisition
    )
    storyboard = create_storyboard(
        beats,
        float(probe["duration_seconds"]),
        target_duration,
        video_candidate,
        contract_version=contract_version,
    )
    storyboard["title"] = title
    storyboard["selected_story_id"] = story_source["id"]
    created_at = iso_now()
    project = {
        "version": 1,
        "title": title,
        "slug": project_dir.name,
        "created_at": created_at,
        "updated_at": created_at,
        "timezone": "Asia/Seoul",
        "status": "source_ready",
        "story_mode": story_source["mode"],
        "selected_story_id": story_source["id"],
        "selected_video_id": video_source["id"],
        "target_duration_seconds": target_duration,
        "story_contract_version": contract_version,
        "review_render_profile": {
            "width": REVIEW_WIDTH,
            "height": REVIEW_HEIGHT,
            "frame_rate": FRAME_RATE,
            "video_codec": "h264",
            "audio_codec": "aac",
        },
        "render_profile": {
            "width": OUTPUT_WIDTH,
            "height": OUTPUT_HEIGHT,
            "frame_rate": FRAME_RATE,
            "video_codec": "h264",
            "audio_codec": "aac",
        },
        "narration": {
            "provider": "typecast",
            "model": TYPECAST_MODEL,
            "voice_id": TYPECAST_VOICE_ID,
            "voice_name": TYPECAST_VOICE_NAME,
            "tempo": 1.0,
            "local_tts_fallback": False,
        },
        "audio": {
            "source_music_muted": True,
            "source_asmr_enabled": False,
            "ambient_mode": (
                "synthetic_melancholy" if contract_version == 3 else "synthetic_gentle"
            ),
            "bgm_volume": 0.90 if contract_version == 3 else 0.32,
            "bgm_rights": "synthetic_original",
            "continuous_bgm": contract_version == 3,
        },
        "presentation": {
            "style": "dialogue_clean" if contract_version == 3 else "legacy_card",
            "title_position": "top_band" if contract_version == 3 else "top",
            "caption_position": "center",
            "caption_background": False if contract_version == 3 else True,
            "header_style": "curiosity_band" if contract_version == 3 else "overlay",
            "topic_title": title if contract_version == 3 else "",
            "topic_hook": (
                text(story_source.get("central_question")) if contract_version == 3 else ""
            ),
        },
        "approvals": {name: False for name in APPROVALS},
        "publication": {
            "publish_blocked": True,
            "reason": "권리와 검토 승인이 완료되지 않았습니다.",
            "upload_performed": False,
        },
    }
    rights_manifest = {
        "version": 1,
        "updated_at": created_at,
        "assets": [
            {
                "id": "food-source",
                "path": video_source["local_path"],
                "kind": "video",
                "source_url": video_source["source_url"],
                "creator": video_source["creator"],
                "platform": video_source["platform"],
                "sha256": video_source["sha256"],
                "rights_status": video_source["rights"]["status"],
                "permission_reference": "",
                "watermark_present": video_source["watermark_present"],
                "watermark_removed": False,
                "source_text_status": video_source["visual_text"]["status"],
                "source_text_removed": False,
            }
        ],
        "proof_boundary": "로컬 파일과 입력 기록이며 게시·수익화 권리 판정이 아닙니다.",
    }
    disclosure = ""
    if story_source["mode"] == "anecdote":
        disclosure = text(require_object(story_source.get("anecdote", {}), "anecdote").get("disclosure"))
    publish = {
        "version": 1,
        "title_candidates": [title, f"{title} | 따뜻한 사연", f"마지막 한마디가 바꾼 하루 | {title}"],
        "description": (
            f"{title}\n\n{disclosure or '확인된 출처의 사실을 바탕으로 새롭게 구성한 이야기입니다.'}\n\n"
            "#힐링스토리 #음식영상 #Shorts"
        ),
        "hashtags": ["힐링스토리", "음식영상", "Shorts"],
        "category": "Entertainment",
        "language": "ko",
        "visibility": "private",
        "rights_review_required": True,
        "publish_blocked": True,
        "upload_performed": False,
    }
    write_json(project_dir / "project.json", project)
    write_json(project_dir / "story-source.json", story_source)
    write_json(project_dir / "video-source.json", video_source)
    write_json(project_dir / "storyboard.json", storyboard)
    write_json(project_dir / "rights-manifest.json", rights_manifest)
    write_json(project_dir / "publish.json", publish)
    (project_dir / "script.md").write_text(
        script_markdown(title, story_source, storyboard), encoding="utf-8"
    )
    print(project_dir)
    return 0


def keychain_typecast_api_key() -> str:
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
def typecast_key_record() -> tuple[str, str | None]:
    environment_key = os.environ.get("TYPECAST_API_KEY", "").strip()
    if environment_key:
        return environment_key, "environment"
    keychain_key = keychain_typecast_api_key()
    if keychain_key:
        return keychain_key, "keychain"
    return "", None


def typecast_keychain_check_limited() -> bool:
    return sys.platform == "darwin" and bool(os.environ.get("CODEX_SANDBOX"))


@functools.cache
def verified_ssl_context() -> ssl.SSLContext:
    default_paths = ssl.get_default_verify_paths()
    if default_paths.cafile and Path(default_paths.cafile).is_file():
        return ssl.create_default_context()
    for candidate in (Path("/etc/ssl/cert.pem"), Path("/opt/homebrew/etc/openssl@3/cert.pem")):
        if candidate.is_file():
            return ssl.create_default_context(cafile=str(candidate))
    return ssl.create_default_context()


def typecast_audio(
    path: Path,
    narration: str,
    *,
    voice_id: str,
    tempo: float,
    previous_text: str,
    next_text: str,
) -> None:
    api_key, _ = typecast_key_record()
    if not api_key:
        if typecast_keychain_check_limited():
            raise HealingShortsError(
                "이 Codex 실행에서는 Typecast 키체인 접근이 제한될 수 있습니다. 사용자 터미널에서 "
                f"`{TYPECAST_SETUP_COMMAND}`를 확인하세요. 로컬 TTS로 자동 대체하지 않습니다."
            )
        raise HealingShortsError(
            "Typecast API 키가 없습니다. TYPECAST_API_KEY를 설정하거나 "
            f"`{TYPECAST_SETUP_COMMAND}`를 실행하세요."
        )
    if not narration or len(narration) > 2000:
        raise HealingShortsError("Typecast 장면 내레이션은 1~2,000자여야 합니다.")
    payload = {
        "voice_id": voice_id,
        "text": narration,
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
            "audio_tempo": tempo,
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
            "User-Agent": "healing2shorts/0.1",
        },
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=60, context=verified_ssl_context()) as response:
            audio = response.read()
    except error.HTTPError as exc:
        messages = {
            401: "TYPECAST_API_KEY를 확인하세요.",
            402: "Typecast 사용량 또는 결제 상태를 확인하세요.",
            429: "Typecast 요청 한도를 초과했습니다.",
        }
        raise HealingShortsError(
            f"Typecast TTS 요청 실패: HTTP {exc.code}. {messages.get(exc.code, 'Typecast 설정을 확인하세요.')}"
        ) from exc
    except error.URLError as exc:
        raise HealingShortsError(f"Typecast TTS 연결 실패: {exc.reason}") from exc
    if len(audio) < 12 or audio[:4] != b"RIFF" or audio[8:12] != b"WAVE":
        raise HealingShortsError("Typecast TTS 응답이 WAV 오디오가 아닙니다.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(audio)


def command_doctor(args: argparse.Namespace) -> int:
    _, key_source = typecast_key_record()
    font = next((str(path) for path in FONT_CANDIDATES if path.is_file()), "")
    report = {
        "plugin_root": str(PLUGIN_ROOT),
        "python": sys.version.split()[0],
        "ffmpeg": shutil.which("ffmpeg") or "",
        "ffprobe": shutil.which("ffprobe") or "",
        "pillow": bool(importlib.util.find_spec("PIL")),
        "font": font,
        "typecast_api_key_configured": key_source is not None,
        "typecast_api_key_source": key_source,
        "typecast_keychain_check_limited": key_source is None and typecast_keychain_check_limited(),
        "typecast_voice": {"name": TYPECAST_VOICE_NAME, "id": TYPECAST_VOICE_ID},
        "typecast_setup_command": "" if key_source else TYPECAST_SETUP_COMMAND,
        "ready_for_silent_render": bool(
            shutil.which("ffmpeg")
            and shutil.which("ffprobe")
            and importlib.util.find_spec("PIL")
            and font
        ),
        "external_download": "authorized_https_direct_media_only",
        "douyin_download": False,
        "external_upload": False,
        "watermark_removal": False,
        "source_text_removal": False,
        "text_free_segment_filtering": True,
    }
    report["ready_for_typecast_render"] = bool(
        report["ready_for_silent_render"] and report["typecast_api_key_configured"]
    )
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        for key, value in report.items():
            print(f"{key}: {value}")
    return 0 if report["ready_for_silent_render"] else 1


def load_project_package(project_dir: Path) -> dict[str, dict[str, Any]]:
    names = (
        "project.json",
        "story-source.json",
        "video-source.json",
        "storyboard.json",
        "rights-manifest.json",
        "publish.json",
    )
    package: dict[str, dict[str, Any]] = {}
    for name in names:
        package[name] = require_object(load_json(project_dir / name), name)
    return package


def video_path(project_dir: Path, video_source: dict[str, Any]) -> Path:
    return resolve_project_path(project_dir, text(video_source.get("local_path")))


def validate_story_source(
    story: dict[str, Any], errors: list[str], warnings: list[str], *, publish_ready: bool
) -> None:
    mode = text(story.get("mode"))
    if mode not in STORY_MODES:
        errors.append("story-source.json mode는 article 또는 anecdote여야 합니다.")
        return
    sensitive = story.get("sensitive_topics")
    if not isinstance(sensitive, list):
        errors.append("story-source.json sensitive_topics는 배열이어야 합니다.")
    elif any(not text(item) for item in sensitive):
        errors.append("sensitive_topics에는 빈 값을 넣을 수 없습니다.")
    contract_version = story.get(
        "story_contract_version", story.get("contract_version", story.get("version", 1))
    )
    if contract_version == DIALOGUE_STORY_CONTRACT_VERSION:
        snapshot = story.get("candidate_snapshot")
        dialogue_candidate = snapshot if isinstance(snapshot, dict) else story
        try:
            normalize_beats(dialogue_candidate, contract_version=3)
        except HealingShortsError as exc:
            errors.append(str(exc))
    if mode == "article":
        sources = story.get("sources")
        claims = story.get("claims")
        if not isinstance(sources, list) or len(sources) < 2:
            errors.append("기사형 스토리에는 원 출처와 독립 출처를 포함해 최소 2개 출처가 필요합니다.")
            sources = []
        source_ids: set[str] = set()
        kinds: set[str] = set()
        non_newspic_domains: set[str] = set()
        for index, value in enumerate(sources, start=1):
            if not isinstance(value, dict):
                errors.append(f"기사 출처는 객체여야 합니다: source-{index:02d}")
                continue
            source_id = text(value.get("id"))
            url = text(value.get("url"))
            kind = text(value.get("kind"))
            publisher = text(value.get("publisher"))
            if not source_id or source_id in source_ids:
                errors.append(f"기사 출처 ID가 없거나 중복입니다: source-{index:02d}")
            source_ids.add(source_id)
            if not url or not publisher:
                errors.append(f"기사 출처에는 url과 publisher가 필요합니다: {source_id or index}")
            else:
                try:
                    public_url(url, f"source {source_id} URL")
                    hostname = (urlparse(url).hostname or "").lower()
                    if not hostname.endswith("newspic.kr"):
                        non_newspic_domains.add(hostname)
                except HealingShortsError as exc:
                    errors.append(str(exc))
            kinds.add(kind)
        if not kinds.intersection({"primary", "official", "original"}):
            errors.append("기사형 스토리에는 primary, official 또는 original 출처가 필요합니다.")
        if "independent" not in kinds:
            errors.append("기사형 스토리에는 independent 출처가 필요합니다.")
        if len(non_newspic_domains) < 2:
            errors.append("뉴스픽 이외의 서로 다른 원 출처·독립 출처 도메인 2개가 필요합니다.")
        if not isinstance(claims, list) or len(claims) < 3:
            errors.append("기사형 스토리에는 source ID가 연결된 claim이 최소 3개 필요합니다.")
            claims = []
        claim_ids: set[str] = set()
        for index, value in enumerate(claims, start=1):
            if not isinstance(value, dict):
                errors.append(f"claim은 객체여야 합니다: claim-{index:02d}")
                continue
            claim_id = text(value.get("id"))
            claim_text = text(value.get("text"))
            linked = value.get("source_ids")
            if not claim_id or claim_id in claim_ids or not claim_text:
                errors.append(f"claim id가 없거나 중복이거나 text가 비었습니다: claim-{index:02d}")
            claim_ids.add(claim_id)
            if not isinstance(linked, list) or not linked:
                errors.append(f"claim에는 source_ids가 필요합니다: {claim_id or index}")
            elif set(str(item) for item in linked) - source_ids:
                errors.append(f"claim이 존재하지 않는 source ID를 참조합니다: {claim_id or index}")
    else:
        anecdote = story.get("anecdote")
        if not isinstance(anecdote, dict):
            errors.append("익명 사연형에는 anecdote 객체가 필요합니다.")
            return
        origin = text(anecdote.get("origin_kind"))
        if origin not in ANECDOTE_ORIGINS:
            errors.append("anecdote.origin_kind는 submitted, public_post, fictionalized 중 하나여야 합니다.")
        if not text(anecdote.get("disclosure")):
            errors.append("익명 사연형에는 업로드 설명용 disclosure가 필요합니다.")
        removed = anecdote.get("identity_fields_removed")
        if not isinstance(removed, list) or not removed:
            errors.append("익명 사연형에는 identity_fields_removed가 필요합니다.")
        consent = text(anecdote.get("consent_status"))
        if origin == "submitted" and consent not in {"permission_confirmed", "owned"}:
            (errors if publish_ready else warnings).append(
                "직접 제보 사연의 게시에는 permission_confirmed 또는 owned 동의 상태가 필요합니다."
            )
        if origin == "public_post" and consent not in {"permission_confirmed", "fictionalized"}:
            (errors if publish_ready else warnings).append(
                "공개 게시물 사연은 표현 사용 허가 또는 충분한 재구성 검토가 필요합니다."
            )


def validate_storyboard(
    storyboard: dict[str, Any],
    source_duration: float,
    errors: list[str],
    warnings: list[str],
    *,
    publish_ready: bool,
) -> None:
    scenes = storyboard.get("scenes")
    contract_version = storyboard.get("story_contract_version", 1)
    event_contract = contract_version in {2, 3}
    required_beats = EVENT_REQUIRED_BEATS if event_contract else LEGACY_REQUIRED_BEATS
    invalid_scenes = not isinstance(scenes, list)
    if isinstance(scenes, list):
        invalid_scenes = len(scenes) != 7 if event_contract else not 6 <= len(scenes) <= 8
    if invalid_scenes:
        errors.append(
            "storyboard.json 사건형에는 정확히 7개 장면이 필요합니다."
            if event_contract
            else "storyboard.json에는 6~8개 장면이 필요합니다."
        )
        return
    total = 0.0
    beat_positions: dict[str, int] = {}
    ranges: set[tuple[float, float]] = set()
    previous_start = -1.0
    chinese_text_scenes: list[str] = []
    unknown_text_scenes: list[str] = []
    dialogue_turn_ids: list[str] = []
    for index, value in enumerate(scenes, start=1):
        if not isinstance(value, dict):
            errors.append(f"storyboard scene은 객체여야 합니다: {index}")
            continue
        scene_id = text(value.get("id")) or f"scene-{index:02d}"
        beat = text(value.get("beat"))
        if beat in required_beats and beat not in beat_positions:
            beat_positions[beat] = index
        try:
            duration = number(value.get("duration"), f"{scene_id}.duration")
            start = number(value.get("source_start_seconds"), f"{scene_id}.source_start_seconds")
            source_seconds = number(
                value.get("source_duration_seconds"), f"{scene_id}.source_duration_seconds"
            )
        except HealingShortsError as exc:
            errors.append(str(exc))
            continue
        total += duration
        minimum, maximum = (
            (2.0, 3.0)
            if event_contract and beat == "cold_open"
            else (3.0, 8.0)
        )
        if not minimum <= duration <= maximum:
            errors.append(
                f"장면 길이는 {minimum:g}~{maximum:g}초여야 합니다: {scene_id}: {duration}"
            )
        if start < 0 or source_seconds <= 0 or start + source_seconds > source_duration + 0.05:
            errors.append(f"원본 영상 범위를 벗어난 장면입니다: {scene_id}")
        pair = (round(start, 2), round(source_seconds, 2))
        if pair in ranges:
            errors.append(f"같은 원본 구간을 반복 사용합니다: {scene_id}")
        ranges.add(pair)
        if start < previous_start:
            warnings.append(f"원본 구간 순서가 뒤로 이동합니다: {scene_id}")
        previous_start = start
        source_text_status = text(value.get("source_text_status")) or "unknown"
        if source_text_status not in VIDEO_TEXT_STATUSES:
            errors.append(f"지원하지 않는 원본 화면 문자 상태입니다: {scene_id}: {source_text_status}")
        elif source_text_status == "chinese_present":
            chinese_text_scenes.append(scene_id)
        elif source_text_status == "unknown":
            unknown_text_scenes.append(scene_id)
        caption = text(value.get("caption"))
        narration = text(value.get("narration"))
        if not caption or len(caption) > 44:
            errors.append(f"화면 자막은 1~44자여야 합니다: {scene_id}")
        if caption.count("\n") > 1:
            errors.append(f"화면 자막은 최대 2줄이어야 합니다: {scene_id}")
        if not narration or len(narration) > 180:
            errors.append(f"내레이션은 1~180자여야 합니다: {scene_id}")
        if contract_version == DIALOGUE_STORY_CONTRACT_VERSION:
            scene_turn_ids = value.get("dialogue_turn_ids")
            if not isinstance(scene_turn_ids, list) or not scene_turn_ids or any(
                not text(turn_id) for turn_id in scene_turn_ids
            ):
                errors.append(f"대화형 장면에는 dialogue_turn_ids가 필요합니다: {scene_id}")
            else:
                dialogue_turn_ids.extend(text(turn_id) for turn_id in scene_turn_ids)
    if not MIN_DURATION <= total <= MAX_DURATION:
        errors.append(f"스토리보드 총 길이는 30~45초여야 합니다: {total:.3f}초")
    if contract_version == DIALOGUE_STORY_CONTRACT_VERSION:
        if total < DIALOGUE_STORY_MIN_DURATION:
            errors.append(f"대화형 힐링 썰은 40~45초여야 합니다: {total:.3f}초")
        if len(dialogue_turn_ids) < DIALOGUE_STORY_MIN_TURNS:
            errors.append("대화형 스토리보드에는 대사 10개 이상이 필요합니다.")
        if len(dialogue_turn_ids) != len(set(dialogue_turn_ids)):
            errors.append("대화형 스토리보드에서 같은 대사를 반복 사용할 수 없습니다.")
    positions = [beat_positions.get(beat, 0) for beat in required_beats]
    if not all(positions) or positions != sorted(positions):
        errors.append("필수 비트 순서가 필요합니다: " + "→".join(required_beats))
    if chinese_text_scenes:
        errors.append(
            "중국어가 보이는 원본 구간은 사용할 수 없습니다. 해당 구간을 제외하세요: "
            + ", ".join(chinese_text_scenes)
        )
    if unknown_text_scenes:
        message = (
            "원본 화면의 중국어 유무를 확인하고 source_text_status를 갱신하세요: "
            + ", ".join(unknown_text_scenes)
        )
        (errors if publish_ready else warnings).append(message)


def permission_complete(rights: dict[str, Any], status: str) -> bool:
    if status == "owned":
        return bool(text(rights.get("rights_holder")))
    return bool(
        text(rights.get("rights_holder"))
        and text(rights.get("permission_date"))
        and rights.get("youtube_scope") is True
        and rights.get("commercial_use") is True
        and rights.get("editing_allowed") is True
        and rights.get("voice_overlay_allowed") is True
        and text(rights.get("permission_reference"))
        and text(rights.get("permission_reference_sha256"))
    )


def validate_project(
    project_dir: Path, *, publish_ready: bool
) -> tuple[list[str], list[str], dict[str, dict[str, Any]] | None]:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        package = load_project_package(project_dir)
    except HealingShortsError as exc:
        return [str(exc)], warnings, None
    project = package["project.json"]
    story = package["story-source.json"]
    video = package["video-source.json"]
    storyboard = package["storyboard.json"]
    manifest = package["rights-manifest.json"]
    publish = package["publish.json"]
    validate_story_source(story, errors, warnings, publish_ready=publish_ready)
    try:
        source_path = video_path(project_dir, video)
        digest = sha256_for(source_path)
        if digest != text(video.get("sha256")):
            errors.append("로컬 음식 영상 SHA-256이 video-source.json과 다릅니다.")
        probe = media_probe(source_path)
        validate_storyboard(
            storyboard,
            float(probe["duration_seconds"]),
            errors,
            warnings,
            publish_ready=publish_ready,
        )
    except HealingShortsError as exc:
        errors.append(str(exc))
        probe = {}
    rights = video.get("rights")
    if not isinstance(rights, dict):
        errors.append("video-source.json rights는 객체여야 합니다.")
        rights = {}
    status = text(rights.get("status"))
    if status not in RIGHTS_STATUSES:
        errors.append(f"지원하지 않는 영상 권리 상태입니다: {status or 'empty'}")
    elif status == "not_permitted":
        errors.append("not_permitted 영상은 검토·최종 렌더에 사용할 수 없습니다.")
    elif publish_ready and status not in FINAL_RIGHTS_STATUSES:
        errors.append("게시 준비에는 owned, licensed 또는 permission_confirmed 영상이 필요합니다.")
    elif status == "negotiation_pending":
        warnings.append("영상 권리 협의 중이므로 로컬 검토본만 허용됩니다.")
    if publish_ready and status in FINAL_RIGHTS_STATUSES and not permission_complete(rights, status):
        errors.append("최종 권리 상태에 필요한 권리자·범위·증빙 기록이 불완전합니다.")
    visual_text = video.get("visual_text")
    if not isinstance(visual_text, dict):
        errors.append("video-source.json visual_text는 객체여야 합니다.")
    elif visual_text.get("source_text_removed") is not False:
        errors.append("source_text_removed는 false여야 합니다. 원문 삭제 대신 구간을 제외하세요.")
    assets = manifest.get("assets")
    if not isinstance(assets, list) or len(assets) != 1:
        errors.append("rights-manifest.json에는 음식 영상 자산 한 개가 필요합니다.")
    elif isinstance(assets[0], dict):
        if text(assets[0].get("sha256")) != text(video.get("sha256")):
            errors.append("rights-manifest 영상 SHA-256이 video-source.json과 다릅니다.")
        if assets[0].get("watermark_removed") is not False:
            errors.append("watermark_removed는 false여야 합니다.")
        if assets[0].get("source_text_removed") is not False:
            errors.append("source_text_removed는 false여야 합니다.")
    approvals = project.get("approvals")
    if not isinstance(approvals, dict):
        errors.append("project.json approvals는 객체여야 합니다.")
        approvals = {}
    if publish_ready:
        for name in ("story_reviewed", "visual_reviewed", "rights_reviewed", "upload_reviewed"):
            if approvals.get(name) is not True:
                errors.append(f"게시 준비 승인 누락: {name}")
        sensitive = story.get("sensitive_topics") if isinstance(story.get("sensitive_topics"), list) else []
        if sensitive and approvals.get("sensitive_reviewed") is not True:
            errors.append("민감 주제 스토리는 sensitive_reviewed 승인이 필요합니다.")
        draft_render = project.get("draft_render")
        if (
            not isinstance(draft_render, dict)
            or not text(draft_render.get("path"))
            or not resolve_project_path(project_dir, text(draft_render.get("path"))).is_file()
        ):
            errors.append("최종 렌더 전에 검토용 draft 렌더가 필요합니다.")
    expected_profile = project.get("render_profile")
    if not isinstance(expected_profile, dict) or (
        expected_profile.get("width"), expected_profile.get("height"), expected_profile.get("frame_rate")
    ) != (OUTPUT_WIDTH, OUTPUT_HEIGHT, FRAME_RATE):
        errors.append("render_profile은 720x1280, 30fps여야 합니다.")
    review_profile = project.get("review_render_profile")
    if review_profile is not None and (
        not isinstance(review_profile, dict)
        or (
            review_profile.get("width"),
            review_profile.get("height"),
            review_profile.get("frame_rate"),
        )
        != (REVIEW_WIDTH, REVIEW_HEIGHT, FRAME_RATE)
    ):
        errors.append("review_render_profile은 540x960, 30fps여야 합니다.")
    if publish.get("upload_performed") is not False:
        errors.append("publish.json upload_performed는 false여야 합니다.")
    if probe and probe.get("width", 0) <= 0:
        errors.append("원본 영상 해상도를 확인할 수 없습니다.")
    return errors, warnings, package


def command_validate(args: argparse.Namespace) -> int:
    project_dir = Path(args.project_dir).expanduser().resolve()
    errors, warnings, _ = validate_project(project_dir, publish_ready=args.publish_ready)
    report = {
        "ok": not errors,
        "mode": "publish_ready" if args.publish_ready else "review_ready",
        "errors": errors,
        "warnings": warnings,
        "proof_boundary": "정적·로컬 파일 검사이며 사실성, 법률 판단, 플랫폼 승인 증명이 아닙니다.",
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


def extract_frame(source: Path, timestamp: float, destination: Path, *, crop: bool = False) -> None:
    ffmpeg = shutil.which("ffmpeg") or "ffmpeg"
    filter_value = (
        f"scale={OUTPUT_WIDTH}:{OUTPUT_HEIGHT}:force_original_aspect_ratio=increase,"
        f"crop={OUTPUT_WIDTH}:{OUTPUT_HEIGHT},setsar=1"
        if crop
        else "scale=360:-2"
    )
    run_checked(
        [
            ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            f"{timestamp:.3f}",
            "-i",
            str(source),
            "-frames:v",
            "1",
            "-vf",
            filter_value,
            "-q:v",
            "2",
            "-y",
            str(destination),
        ],
        "프리뷰 프레임 추출",
    )


def command_preview(args: argparse.Namespace) -> int:
    project_dir = Path(args.project_dir).expanduser().resolve()
    package = load_project_package(project_dir)
    source = video_path(project_dir, package["video-source.json"])
    probe = media_probe(source)
    preview_dir = project_dir / "previews"
    contact_sheet = preview_dir / "contact-sheet.jpg"
    crop_preview = preview_dir / "crop-preview.jpg"
    existing = [path for path in (contact_sheet, crop_preview) if path.exists()]
    if existing and not args.overwrite:
        raise HealingShortsError(
            f"프리뷰가 이미 있습니다: {existing[0]}. 덮어쓰려면 --overwrite를 사용하세요."
        )
    preview_dir.mkdir(parents=True, exist_ok=True)
    duration = float(probe["duration_seconds"])
    timestamps = [duration * (index + 1) / 13 for index in range(12)]
    frames: list[Path] = []
    for index, timestamp in enumerate(timestamps, start=1):
        frame = preview_dir / f"frame-{index:02d}.jpg"
        extract_frame(source, timestamp, frame)
        frames.append(frame)
    extract_frame(source, duration / 2, crop_preview, crop=True)
    from PIL import Image, ImageDraw

    thumb_width = 360
    label_height = 38
    opened: list[Any] = []
    for frame in frames:
        image = Image.open(frame).convert("RGB")
        opened.append(image)
    thumb_height = max(1, int(opened[0].height * thumb_width / opened[0].width))
    sheet = Image.new("RGB", (thumb_width * 3, (thumb_height + label_height) * 4), "#15110F")
    draw = ImageDraw.Draw(sheet)
    font = load_font(24, bold=True)
    for index, image in enumerate(opened):
        image.thumbnail((thumb_width, thumb_height))
        x = (index % 3) * thumb_width
        y = (index // 3) * (thumb_height + label_height)
        sheet.paste(image, (x, y))
        draw.text((x + 10, y + thumb_height + 5), f"{timestamps[index]:.1f}s", font=font, fill="white")
        image.close()
    sheet.save(contact_sheet, quality=90)
    project = package["project.json"]
    project["status"] = "previewed"
    project["updated_at"] = iso_now()
    project["preview"] = {
        "contact_sheet": relative_project_path(project_dir, contact_sheet),
        "crop_preview": relative_project_path(project_dir, crop_preview),
        "timestamps": [round(value, 3) for value in timestamps],
        "watermark_review_required": True,
        "source_text_review_required": True,
        "source_text_removal_supported": False,
        "review_instruction": (
            "중국어가 보이는 구간은 storyboard.json에서 다른 구간으로 교체하고 "
            "source_text_status를 none 또는 non_chinese_only로 기록하세요."
        ),
    }
    write_json(project_dir / "project.json", project)
    print(contact_sheet)
    print(crop_preview)
    return 0


def yes_no(value: str | None) -> bool | None:
    if value is None:
        return None
    return value == "yes"


def command_record_rights(args: argparse.Namespace) -> int:
    project_dir = Path(args.project_dir).expanduser().resolve()
    package = load_project_package(project_dir)
    video = package["video-source.json"]
    manifest = package["rights-manifest.json"]
    project = package["project.json"]
    rights = require_object(video.get("rights"), "video-source rights")
    rights["status"] = args.status
    for key in ("rights_holder", "permission_date", "attribution", "expires_at"):
        value = getattr(args, key)
        if value is not None:
            rights[key] = value.strip()
    for key in (
        "youtube_scope",
        "commercial_use",
        "editing_allowed",
        "voice_overlay_allowed",
        "source_asmr_approved",
    ):
        value = yes_no(getattr(args, key))
        if value is not None:
            rights[key] = value
    if args.permission_reference:
        source = Path(args.permission_reference).expanduser().resolve()
        if not source.is_file():
            raise HealingShortsError(f"권리 증빙 파일이 없습니다: {source}")
        destination = project_dir / "assets" / "rights" / source.name
        if destination.exists() and not args.overwrite:
            raise HealingShortsError(
                f"권리 증빙 파일이 이미 있습니다: {destination}. 덮어쓰려면 --overwrite를 사용하세요."
            )
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        rights["permission_reference"] = relative_project_path(project_dir, destination)
        rights["permission_reference_sha256"] = sha256_for(destination)
    approvals = require_object(project.get("approvals"), "project approvals")
    if args.confirm_story_review:
        approvals["story_reviewed"] = True
    if args.confirm_visual_review:
        approvals["visual_reviewed"] = True
    if args.confirm_sensitive_review:
        approvals["sensitive_reviewed"] = True
    if args.confirm_upload_review:
        approvals["upload_reviewed"] = True
    if args.status in FINAL_RIGHTS_STATUSES and permission_complete(rights, args.status):
        approvals["rights_reviewed"] = True
    project["audio"]["source_asmr_enabled"] = rights.get("source_asmr_approved") is True
    project["updated_at"] = iso_now()
    manifest["updated_at"] = iso_now()
    assets = require_list(manifest.get("assets", []), "rights-manifest assets")
    if not assets or not isinstance(assets[0], dict):
        raise HealingShortsError("rights-manifest 음식 영상 자산이 없습니다.")
    assets[0]["rights_status"] = args.status
    assets[0]["permission_reference"] = text(rights.get("permission_reference"))
    write_json(project_dir / "video-source.json", video)
    write_json(project_dir / "rights-manifest.json", manifest)
    write_json(project_dir / "project.json", project)
    print(json.dumps({"rights": rights, "approvals": approvals}, ensure_ascii=False, indent=2))
    return 0


def create_silent_audio(path: Path, duration: float) -> None:
    run_checked(
        [
            shutil.which("ffmpeg") or "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            "anullsrc=r=48000:cl=stereo",
            "-t",
            f"{duration:.3f}",
            "-c:a",
            "pcm_s16le",
            "-y",
            str(path),
        ],
        "무음 오디오 생성",
    )


def create_ambient_audio(
    path: Path,
    duration: float,
    *,
    mode: str = "synthetic_gentle",
    scene_index: int = 0,
) -> None:
    if mode not in AMBIENT_MODES:
        raise HealingShortsError(f"지원하지 않는 배경음 모드입니다: {mode}")
    if mode == "synthetic_melancholy":
        slow_pulse = "(0.58+0.42*abs(sin(PI*0.125*t)))"
        expression = (
            f"0.075*sin(2*PI*110.00*t)*{slow_pulse}"
            f"+0.060*sin(2*PI*130.81*t)*{slow_pulse}"
            f"+0.048*sin(2*PI*164.81*t)*{slow_pulse}"
            "+0.020*sin(2*PI*220.00*t)"
        )
        audio_filter = (
            "aformat=sample_fmts=s16:channel_layouts=stereo,"
            "lowpass=f=1350,aecho=0.8:0.84:420|840:0.12|0.06,"
            f"atrim=duration={duration:.3f},asetpts=PTS-STARTPTS,"
            "afade=t=in:st=0:d=1.2,"
            f"afade=t=out:st={max(0.0, duration - 1.4):.3f}:d=1.4"
        )
    elif mode == "synthetic_emotional":
        root, third, fifth = EMOTIONAL_BGM_CHORDS[
            scene_index % len(EMOTIONAL_BGM_CHORDS)
        ]
        pulse = "(0.62+0.38*abs(sin(PI*0.5*t)))"
        expression = (
            f"0.060*sin(2*PI*{root:.2f}*t)*{pulse}"
            f"+0.046*sin(2*PI*{third:.2f}*t)*{pulse}"
            f"+0.034*sin(2*PI*{fifth:.2f}*t)*{pulse}"
            f"+0.014*sin(2*PI*{root * 2:.2f}*t)"
        )
        audio_filter = (
            "aformat=sample_fmts=s16:channel_layouts=stereo,"
            "lowpass=f=1800,aecho=0.8:0.82:150|300:0.14|0.07,"
            f"atrim=duration={duration:.3f},asetpts=PTS-STARTPTS,"
            "afade=t=in:st=0:d=0.12,"
            f"afade=t=out:st={max(0.0, duration - 0.18):.3f}:d=0.18"
        )
    else:
        expression = (
            "0.012*sin(2*PI*196*t)+0.007*sin(2*PI*293.66*t)+0.004*sin(2*PI*392*t)"
        )
        audio_filter = (
            "aformat=sample_fmts=s16:channel_layouts=stereo,afade=t=in:st=0:d=0.4,"
            f"afade=t=out:st={max(0.0, duration - 0.5):.3f}:d=0.5"
        )
    run_checked(
        [
            shutil.which("ffmpeg") or "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            f"aevalsrc={expression}:s=48000:d={duration:.3f}",
            "-af",
            audio_filter,
            "-c:a",
            "pcm_s16le",
            "-y",
            str(path),
        ],
        "앰비언트 오디오 생성",
    )


def concatenate_dialogue_audio(paths: list[Path], destination: Path, *, gap: float = 0.18) -> None:
    if not paths:
        raise HealingShortsError("연결할 대화 음성이 없습니다.")
    ffmpeg = shutil.which("ffmpeg") or "ffmpeg"
    command = [ffmpeg, "-hide_banner", "-loglevel", "error"]
    filters: list[str] = []
    labels: list[str] = []
    for index, path in enumerate(paths):
        command.extend(["-i", str(path)])
        label = f"voice{index}"
        filters.append(
            f"[{index}:a]aresample=48000,aformat=sample_fmts=s16:channel_layouts=mono[{label}]"
        )
        labels.append(f"[{label}]")
        if index < len(paths) - 1:
            gap_label = f"gap{index}"
            filters.append(f"anullsrc=r=48000:cl=mono:d={gap:.3f}[{gap_label}]")
            labels.append(f"[{gap_label}]")
    filters.append(f"{''.join(labels)}concat=n={len(labels)}:v=0:a=1[out]")
    destination.parent.mkdir(parents=True, exist_ok=True)
    command.extend(
        [
            "-filter_complex",
            ";".join(filters),
            "-map",
            "[out]",
            "-c:a",
            "pcm_s16le",
            "-y",
            str(destination),
        ]
    )
    run_checked(command, "화자별 Typecast 대화 음성 연결")


def dialogue_turn_audio_items(
    scene: dict[str, Any],
    story: dict[str, Any],
    project: dict[str, Any],
    project_dir: Path,
) -> list[dict[str, Any]]:
    narration_config = project.get("narration")
    if not isinstance(narration_config, dict):
        return []
    speaker_voices = narration_config.get("speaker_voices")
    if not isinstance(speaker_voices, dict) or not speaker_voices:
        return []
    turn_ids = scene.get("dialogue_turn_ids")
    turns = story.get("dialogue_turns")
    if not isinstance(turn_ids, list) or not turn_ids or not isinstance(turns, list):
        return []
    normalized_turns = [turn for turn in turns if isinstance(turn, dict)]
    turns_by_id = {text(turn.get("id")): turn for turn in normalized_turns}
    ordered_ids = [text(turn.get("id")) for turn in normalized_turns]
    audio_items: list[dict[str, Any]] = []
    for turn_id_value in turn_ids:
        turn_id = text(turn_id_value)
        turn = turns_by_id.get(turn_id)
        if not isinstance(turn, dict):
            raise HealingShortsError(f"대화 음성에 필요한 turn을 찾지 못했습니다: {turn_id}")
        speaker = text(turn.get("speaker"))
        voice = speaker_voices.get(speaker)
        if not isinstance(voice, dict):
            raise HealingShortsError(f"화자별 Typecast 음성 설정이 없습니다: {speaker}")
        voice_id = text(voice.get("voice_id"))
        voice_name = text(voice.get("voice_name")) or speaker
        tempo = float(voice.get("tempo") or 1.0)
        if not voice_id:
            raise HealingShortsError(f"화자별 Typecast voice_id가 없습니다: {speaker}")
        narration = text(turn.get("text"))
        cache_key = hashlib.sha256(
            f"{turn_id}\0{narration}\0{voice_id}\0{tempo:.3f}".encode("utf-8")
        ).hexdigest()[:12]
        turn_audio = (
            project_dir
            / "assets"
            / "narration"
            / f"{slugify(turn_id)}-{slugify(voice_name)}-{cache_key}.wav"
        )
        if not turn_audio.is_file():
            turn_position = ordered_ids.index(turn_id)
            previous_text = (
                text(normalized_turns[turn_position - 1].get("text"))
                if turn_position > 0
                else ""
            )
            next_text = (
                text(normalized_turns[turn_position + 1].get("text"))
                if turn_position + 1 < len(normalized_turns)
                else ""
            )
            typecast_audio(
                turn_audio,
                narration,
                voice_id=voice_id,
                tempo=tempo,
                previous_text=previous_text,
                next_text=next_text,
            )
        audio_items.append(
            {
                "id": turn_id,
                "speaker": speaker,
                "text": narration,
                "path": turn_audio,
                "duration_seconds": audio_duration(turn_audio),
            }
        )
    return audio_items


def dialogue_scene_audio(
    scene: dict[str, Any],
    story: dict[str, Any],
    project: dict[str, Any],
    project_dir: Path,
    index: int,
) -> tuple[Path | None, list[dict[str, Any]]]:
    audio_items = dialogue_turn_audio_items(scene, story, project, project_dir)
    if not audio_items:
        return None, []
    audio_paths = [require_object(item, "dialogue audio item")["path"] for item in audio_items]
    scene_key = hashlib.sha256(
        "\0".join(path.name for path in audio_paths).encode("utf-8")
    ).hexdigest()[:12]
    persistent = (
        project_dir
        / "assets"
        / "narration"
        / f"scene-{index:02d}-typecast-dialogue-{scene_key}.wav"
    )
    if not persistent.is_file():
        concatenate_dialogue_audio(audio_paths, persistent, gap=DIALOGUE_TURN_GAP)
    return persistent, audio_items


def scene_narration_audio(
    scene: dict[str, Any],
    story: dict[str, Any],
    project: dict[str, Any],
    project_dir: Path,
    work_dir: Path,
    index: int,
    *,
    no_tts: bool,
    previous_text: str,
    next_text: str,
) -> tuple[Path, float, str, list[dict[str, Any]]]:
    configured = text(scene.get("narration_audio"))
    if configured:
        path = resolve_project_path(project_dir, configured)
        return path, audio_duration(path), "provided", []
    requested = number(scene.get("duration"), f"scene {index}.duration")
    if no_tts:
        path = work_dir / f"scene-{index:02d}-silent.wav"
        create_silent_audio(path, requested)
        return path, requested, "silent", []
    dialogue_audio, dialogue_items = dialogue_scene_audio(
        scene, story, project, project_dir, index
    )
    if dialogue_audio is not None:
        return (
            dialogue_audio,
            audio_duration(dialogue_audio),
            "typecast-dialogue",
            dialogue_items,
        )
    narration_config = require_object(project.get("narration"), "project narration")
    persistent = project_dir / "assets" / "narration" / f"scene-{index:02d}-typecast.wav"
    if not persistent.is_file():
        typecast_audio(
            persistent,
            text(scene.get("narration")),
            voice_id=text(narration_config.get("voice_id")) or TYPECAST_VOICE_ID,
            tempo=float(narration_config.get("tempo") or 1.0),
            previous_text=previous_text,
            next_text=next_text,
        )
    return persistent, audio_duration(persistent), "typecast", []


def wrap_caption(draw: Any, value: str, font: Any, max_width: int) -> list[str]:
    normalized = re.sub(r"\s+", " ", value.strip())
    if "\n" in value:
        lines = [part.strip() for part in value.splitlines() if part.strip()]
        return lines[:2]
    words = normalized.split(" ")
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if draw.textbbox((0, 0), candidate, font=font)[2] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    if len(lines) <= 2:
        return lines
    merged = " ".join(lines[1:])
    while draw.textbbox((0, 0), merged + "…", font=font)[2] > max_width and len(merged) > 1:
        merged = merged[:-1]
    return [lines[0], merged.rstrip() + "…"]


def draw_curiosity_header(
    draw: Any,
    project: dict[str, Any],
    story: dict[str, Any],
    presentation: dict[str, Any],
) -> None:
    topic_font = load_font(50, bold=True)
    hook_font = load_font(64, bold=True)
    header_height = 450
    draw.rectangle((0, 0, CANVAS_WIDTH, header_height), fill=(4, 52, 88, 255))
    draw.rectangle(
        (0, header_height - 6, CANVAS_WIDTH, header_height),
        fill=(70, 218, 214, 255),
    )

    topic = text(presentation.get("topic_title")) or text(project.get("title"))
    topic_lines = wrap_caption(draw, topic[:48], topic_font, 960)
    topic_y = 92
    topic_line_height = 62
    for line in topic_lines:
        box = draw.textbbox((0, 0), line, font=topic_font, stroke_width=2)
        width = box[2] - box[0]
        draw.text(
            ((CANVAS_WIDTH - width) / 2, topic_y),
            line,
            font=topic_font,
            fill=(255, 255, 255, 255),
            stroke_width=3,
            stroke_fill=(0, 22, 40, 240),
        )
        topic_y += topic_line_height

    hook = text(presentation.get("topic_hook")) or text(story.get("central_question"))
    if hook and hook != topic:
        hook_lines = wrap_caption(draw, hook[:42], hook_font, 960)
        hook_y = max(230, topic_y + 18)
        for line in hook_lines:
            box = draw.textbbox((0, 0), line, font=hook_font, stroke_width=2)
            width = box[2] - box[0]
            draw.text(
                ((CANVAS_WIDTH - width) / 2, hook_y),
                line,
                font=hook_font,
                fill=(79, 235, 226, 255),
                stroke_width=3,
                stroke_fill=(0, 22, 40, 240),
            )
            hook_y += 78


def draw_dialogue_clean_overlay(
    draw: Any, scene: dict[str, Any], project: dict[str, Any], story: dict[str, Any]
) -> None:
    title_font = load_font(58, bold=True)
    caption = text(scene.get("caption"))
    caption_length = len(re.sub(r"\s+", "", caption))
    caption_font_size = (
        48
        if caption_length > 32
        else 58
        if caption_length > 24
        else 70
        if caption_length > 16
        else 88
    )
    caption_font = load_font(caption_font_size, bold=True)
    source_font = load_font(24)

    raw_presentation = project.get("presentation")
    presentation = raw_presentation if isinstance(raw_presentation, dict) else {}
    if text(presentation.get("header_style")) == "curiosity_band":
        draw_curiosity_header(draw, project, story, presentation)
    else:
        title_lines = wrap_caption(draw, text(project.get("title"))[:40], title_font, 840)
        title_line_height = 74
        title_height = max(1, len(title_lines)) * title_line_height
        panel_top = 54
        panel_bottom = panel_top + title_height + 46
        draw.rounded_rectangle(
            (54, panel_top, 1026, panel_bottom),
            radius=32,
            fill=(16, 13, 12, 190),
            outline=(235, 167, 83, 245),
            width=4,
        )
        title_y = panel_top + 22
        for line in title_lines:
            box = draw.textbbox((0, 0), line, font=title_font, stroke_width=2)
            width = box[2] - box[0]
            draw.text(
                ((CANVAS_WIDTH - width) / 2, title_y),
                line,
                font=title_font,
                fill=(255, 249, 236, 255),
                stroke_width=3,
                stroke_fill=(0, 0, 0, 235),
            )
            title_y += title_line_height
        draw.rounded_rectangle(
            (390, panel_bottom - 10, 690, panel_bottom - 3),
            radius=4,
            fill=(235, 167, 83, 255),
        )

    lines = wrap_caption(draw, caption, caption_font, 930)
    line_height = int(caption_font_size * 1.38)
    total_height = max(1, len(lines)) * line_height
    caption_y = 1030 - total_height / 2
    for line in lines:
        box = draw.textbbox((0, 0), line, font=caption_font, stroke_width=3)
        width = box[2] - box[0]
        x = (CANVAS_WIDTH - width) / 2
        draw.text(
            (x + 5, caption_y + 7),
            line,
            font=caption_font,
            fill=(0, 0, 0, 170),
            stroke_width=8,
            stroke_fill=(0, 0, 0, 120),
        )
        draw.text(
            (x, caption_y),
            line,
            font=caption_font,
            fill=(255, 255, 255, 255),
            stroke_width=6,
            stroke_fill=(0, 0, 0, 245),
        )
        caption_y += line_height

    source_label = (
        text(story.get("anecdote", {}).get("disclosure"))
        if story.get("mode") == "anecdote"
        else "출처 확인 완료"
    )
    if source_label:
        draw.text(
            (72, 1780),
            source_label[:52],
            font=source_font,
            fill=(250, 244, 232, 235),
            stroke_width=2,
            stroke_fill=(0, 0, 0, 210),
        )


def draw_overlay(
    scene: dict[str, Any], project: dict[str, Any], story: dict[str, Any], destination: Path
) -> None:
    from PIL import Image, ImageDraw

    image = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image, "RGBA")
    presentation = project.get("presentation")
    style = text(presentation.get("style")) if isinstance(presentation, dict) else ""
    if style == "dialogue_clean":
        draw_dialogue_clean_overlay(draw, scene, project, story)
        destination.parent.mkdir(parents=True, exist_ok=True)
        image.save(destination, format="PNG", optimize=True)
        return
    title_font = load_font(34, bold=True)
    beat_font = load_font(28, bold=True)
    caption_font = load_font(82, bold=True)
    source_font = load_font(26)
    beat_labels = {
        "hook": "오늘의 이야기",
        "context": "그날",
        "conflict": "하지만",
        "rehook": "그런데",
        "turn": "그 순간",
        "payoff": "마지막 한마디",
    }
    draw.rounded_rectangle((54, 62, 1026, 170), radius=28, fill=(20, 15, 12, 175))
    draw.text((88, 90), text(project.get("title"))[:28], font=title_font, fill=(255, 248, 235, 255))
    beat_label = beat_labels.get(text(scene.get("beat")), "이야기")
    draw.rounded_rectangle((66, 1270, 300, 1340), radius=25, fill=(222, 154, 82, 230))
    draw.text((95, 1288), beat_label, font=beat_font, fill=(34, 22, 15, 255))
    draw.rounded_rectangle((54, 1360, 1026, 1715), radius=42, fill=(14, 11, 10, 205))
    caption = text(scene.get("caption"))
    lines = wrap_caption(draw, caption, caption_font, 850)
    line_height = 112
    total_height = len(lines) * line_height
    y = 1515 - total_height / 2
    for line in lines:
        box = draw.textbbox((0, 0), line, font=caption_font, stroke_width=2)
        width = box[2] - box[0]
        draw.text(
            ((CANVAS_WIDTH - width) / 2, y),
            line,
            font=caption_font,
            fill=(255, 255, 255, 255),
            stroke_width=4,
            stroke_fill=(0, 0, 0, 220),
        )
        y += line_height
    if story.get("mode") == "article":
        publishers = [
            text(item.get("publisher"))
            for item in story.get("sources", [])
            if isinstance(item, dict) and text(item.get("publisher"))
        ]
        source_label = "출처 확인: " + " · ".join(dict.fromkeys(publishers[:2]))
    else:
        source_label = text(story.get("anecdote", {}).get("disclosure")) or "사연을 바탕으로 재구성"
    draw.text((72, 1740), source_label[:52], font=source_font, fill=(245, 235, 220, 220))
    destination.parent.mkdir(parents=True, exist_ok=True)
    image.save(destination, format="PNG", optimize=True)


def render_scene(
    source: Path,
    source_probe: dict[str, Any],
    scene: dict[str, Any],
    overlays: list[dict[str, Any]],
    narration: Path,
    ambient: Path,
    destination: Path,
    duration: float,
    *,
    asmr_enabled: bool,
    bgm_volume: float,
    output_width: int,
    output_height: int,
    crf: int,
) -> None:
    ffmpeg = shutil.which("ffmpeg") or "ffmpeg"
    start = number(scene.get("source_start_seconds"), "source_start_seconds")
    source_seconds = number(scene.get("source_duration_seconds"), "source_duration_seconds")
    if not overlays:
        raise HealingShortsError("장면 렌더에는 하나 이상의 자막 오버레이가 필요합니다.")
    command = [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-ss",
        f"{start:.3f}",
        "-t",
        f"{source_seconds:.3f}",
        "-i",
        str(source),
    ]
    for overlay in overlays:
        command.extend(
            [
                "-loop",
                "1",
                "-framerate",
                str(FRAME_RATE),
                "-i",
                str(overlay["path"]),
            ]
        )
    narration_input = len(overlays) + 1
    ambient_input = narration_input + 1
    command.extend(["-i", str(narration), "-i", str(ambient)])
    filters = [
        f"[0:v]trim=duration={source_seconds:.3f},setpts=PTS-STARTPTS,"
        f"tpad=stop_mode=clone:stop_duration={duration:.3f},"
        f"scale={CANVAS_WIDTH}:{CANVAS_HEIGHT}:force_original_aspect_ratio=increase,"
        f"crop={CANVAS_WIDTH}:{CANVAS_HEIGHT},setsar=1,fps={FRAME_RATE},"
        f"trim=duration={duration:.3f}[base]",
        f"[{narration_input}:a]atrim=duration={duration:.3f},asetpts=PTS-STARTPTS,"
        f"apad=pad_dur={duration:.3f},volume=1.0[narration]",
        f"[{ambient_input}:a]atrim=duration={duration:.3f},asetpts=PTS-STARTPTS,"
        f"volume={bgm_volume:.3f}[ambient]",
    ]
    video_label = "base"
    for overlay_index, overlay in enumerate(overlays, start=1):
        output_label = f"overlay{overlay_index}"
        start_seconds = float(overlay["start_seconds"])
        end_seconds = float(overlay["end_seconds"])
        filters.append(
            f"[{video_label}][{overlay_index}:v]overlay=0:0:format=auto:"
            f"enable='between(t,{start_seconds:.3f},{end_seconds:.3f})'[{output_label}]"
        )
        video_label = output_label
    filters.append(
        f"[{video_label}]scale={output_width}:{output_height},format=yuv420p[vout]"
    )
    audio_inputs = "[narration][ambient]"
    input_count = 2
    if asmr_enabled and source_probe.get("has_audio"):
        filters.append(
            f"[0:a]atrim=duration={source_seconds:.3f},asetpts=PTS-STARTPTS,"
            f"apad=pad_dur={duration:.3f},volume=0.10[asmr]"
        )
        audio_inputs = "[narration][ambient][asmr]"
        input_count = 3
    filters.append(
        f"{audio_inputs}amix=inputs={input_count}:duration=longest:dropout_transition=0:normalize=0,"
        f"atrim=duration={duration:.3f},alimiter=limit=0.95[aout]"
    )
    command.extend(
        [
            "-filter_complex",
            ";".join(filters),
            "-map",
            "[vout]",
            "-map",
            "[aout]",
            "-t",
            f"{duration:.3f}",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            str(crf),
            "-r",
            str(FRAME_RATE),
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-ar",
            "48000",
            "-movflags",
            "+faststart",
            "-y",
            str(destination),
        ]
    )
    run_checked(command, f"{text(scene.get('id')) or 'scene'} 렌더")


def mix_continuous_bgm(
    source: Path,
    background_music: Path,
    destination: Path,
    *,
    duration: float,
    volume: float,
) -> None:
    run_checked(
        [
            shutil.which("ffmpeg") or "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(source),
            "-i",
            str(background_music),
            "-filter_complex",
            (
                f"[0:a]atrim=duration={duration:.3f},asetpts=PTS-STARTPTS[voice];"
                f"[1:a]atrim=duration={duration:.3f},asetpts=PTS-STARTPTS,"
                f"volume={volume:.3f}[bgm];"
                "[voice][bgm]amix=inputs=2:duration=first:dropout_transition=0:normalize=0,"
                "alimiter=limit=0.95[aout]"
            ),
            "-map",
            "0:v",
            "-map",
            "[aout]",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-ar",
            "48000",
            "-movflags",
            "+faststart",
            "-y",
            str(destination),
        ],
        "전체 길이 감동 배경음 믹스",
    )


def render_raw_clip(
    source: Path, scene: dict[str, Any], destination: Path, duration: float
) -> None:
    ffmpeg = shutil.which("ffmpeg") or "ffmpeg"
    start = number(scene.get("source_start_seconds"), "source_start_seconds")
    source_seconds = number(scene.get("source_duration_seconds"), "source_duration_seconds")
    run_checked(
        [
            ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            f"{start:.3f}",
            "-t",
            f"{source_seconds:.3f}",
            "-i",
            str(source),
            "-vf",
            f"tpad=stop_mode=clone:stop_duration={duration:.3f},"
            f"scale={OUTPUT_WIDTH}:{OUTPUT_HEIGHT}:force_original_aspect_ratio=increase,"
            f"crop={OUTPUT_WIDTH}:{OUTPUT_HEIGHT},setsar=1,fps={FRAME_RATE},"
            f"trim=duration={duration:.3f},format=yuv420p",
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "21",
            "-r",
            str(FRAME_RATE),
            "-movflags",
            "+faststart",
            "-y",
            str(destination),
        ],
        f"{text(scene.get('id')) or 'scene'} 편집 클립 생성",
    )


def srt_time(seconds: float) -> str:
    milliseconds = int(round(seconds * 1000))
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def dialogue_caption_cues(
    audio_items: list[dict[str, Any]], scene_duration: float
) -> list[dict[str, Any]]:
    if not audio_items:
        return []
    cues: list[dict[str, Any]] = []
    cursor = 0.0
    for index, item in enumerate(audio_items):
        turn_duration = float(item["duration_seconds"])
        is_last = index == len(audio_items) - 1
        cue_end = scene_duration if is_last else min(
            scene_duration, cursor + turn_duration + DIALOGUE_TURN_GAP
        )
        cues.append(
            {
                "id": text(item.get("id")),
                "speaker": text(item.get("speaker")),
                "text": text(item.get("text")),
                "start_seconds": round(cursor, 3),
                "end_seconds": round(cue_end, 3),
            }
        )
        cursor += turn_duration + (0.0 if is_last else DIALOGUE_TURN_GAP)
    return cues


def write_srt(path: Path, scenes: list[dict[str, Any]], reports: list[dict[str, Any]]) -> None:
    cursor = 0.0
    blocks: list[str] = []
    cue_index = 1
    for scene, report in zip(scenes, reports):
        duration = float(report["rendered_duration_seconds"])
        caption_cues = report.get("caption_cues")
        if not isinstance(caption_cues, list) or not caption_cues:
            caption_cues = [
                {
                    "text": text(scene.get("caption")),
                    "start_seconds": 0.0,
                    "end_seconds": duration,
                }
            ]
        for cue in caption_cues:
            if not isinstance(cue, dict):
                continue
            start = cursor + float(cue["start_seconds"])
            end = cursor + min(duration, float(cue["end_seconds"]))
            blocks.append(
                f"{cue_index}\n{srt_time(start)} --> {srt_time(end)}\n{text(cue.get('text'))}\n"
            )
            cue_index += 1
        cursor += duration
    path.write_text("\n".join(blocks), encoding="utf-8")


def render_settings(draft: bool) -> tuple[int, int, int]:
    return (REVIEW_WIDTH, REVIEW_HEIGHT, 23) if draft else (FINAL_WIDTH, FINAL_HEIGHT, 20)


def write_upload_package(
    project_dir: Path,
    package: dict[str, dict[str, Any]],
    *,
    video_output: str,
    draft: bool,
) -> tuple[Path, Path, bool]:
    project = package["project.json"]
    story = package["story-source.json"]
    video = package["video-source.json"]
    publish = package["publish.json"]
    rights = require_object(video.get("rights"), "video rights")
    publish_errors, _, _ = validate_project(project_dir, publish_ready=True)
    publish_blocked = draft or bool(publish_errors)
    source_lines: list[str] = []
    if story.get("mode") == "article":
        for item in story.get("sources", []):
            if isinstance(item, dict):
                publisher = text(item.get("publisher"))
                url = text(item.get("url"))
                if publisher and url and not (urlparse(url).hostname or "").lower().endswith("newspic.kr"):
                    source_lines.append(f"- {publisher}: {url}")
    else:
        disclosure = text(story.get("anecdote", {}).get("disclosure"))
        if disclosure:
            source_lines.append(f"- {disclosure}")
    attribution = text(rights.get("attribution"))
    description = text(publish.get("description"))
    if source_lines:
        description += "\n\n이야기 출처·표시\n" + "\n".join(source_lines)
    if attribution:
        description += f"\n\n영상 크레딧\n{attribution}"
    title_candidates = publish.get("title_candidates") if isinstance(publish.get("title_candidates"), list) else []
    title = text(title_candidates[0]) if title_candidates else text(project.get("title"))
    payload = {
        "version": 1,
        "generated_at": iso_now(),
        "video": video_output,
        "title": title,
        "description": description,
        "tags": publish.get("hashtags", []),
        "language": "ko",
        "category": text(publish.get("category")) or "Entertainment",
        "visibility": "private",
        "publish_blocked": publish_blocked,
        "publish_block_reasons": publish_errors,
        "rights_status": text(rights.get("status")),
        "rights_review_required": publish_blocked,
        "audience_review_required": True,
        "altered_content_review_required": True,
        "paid_promotion_review_required": True,
        "upload_performed": False,
    }
    json_path = project_dir / "youtube-upload.json"
    markdown_path = project_dir / "youtube-upload.md"
    write_json(json_path, payload)
    markdown = [
        "# YouTube 업로드 정보",
        "",
        f"- 영상: `{video_output}`",
        f"- 제목: {title}",
        f"- 게시 차단: {'예' if publish_blocked else '아니오'}",
        f"- 권리 상태: {payload['rights_status']}",
        "- 공개 범위: 비공개로 시작 후 사람이 확인",
        "- 실제 업로드: 수행하지 않음",
        "",
        "## 설명",
        "",
        description,
        "",
        "## 게시 전 확인",
        "",
        "- 시청자층, 합성·변형 콘텐츠, 유료 프로모션, 연령 제한을 사람이 확인합니다.",
    ]
    if publish_errors:
        markdown.extend(["", "## 차단 사유", "", *(f"- {item}" for item in publish_errors)])
    markdown.append("")
    markdown_path.write_text("\n".join(markdown), encoding="utf-8")
    publish["publish_blocked"] = publish_blocked
    publish["rights_review_required"] = publish_blocked
    publish["upload_performed"] = False
    write_json(project_dir / "publish.json", publish)
    project["publication"] = {
        "publish_blocked": publish_blocked,
        "reason": "\n".join(publish_errors) if publish_errors else "로컬 게시 준비 검증 통과",
        "upload_performed": False,
    }
    write_json(project_dir / "project.json", project)
    return json_path, markdown_path, publish_blocked


def command_render(args: argparse.Namespace) -> int:
    project_dir = Path(args.project_dir).expanduser().resolve()
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise HealingShortsError("렌더링에는 ffmpeg와 ffprobe가 필요합니다.")
    if not importlib.util.find_spec("PIL"):
        raise HealingShortsError("렌더링에는 Pillow가 필요합니다.")
    find_font()
    draft = args.draft
    output_width, output_height, output_crf = render_settings(draft)
    if args.final and args.no_tts:
        raise HealingShortsError("--no-tts는 무음 기술 검토용이며 최종 렌더에는 사용할 수 없습니다.")
    errors, warnings, package = validate_project(project_dir, publish_ready=args.final)
    if errors or package is None:
        raise HealingShortsError("렌더 전 검증 실패:\n- " + "\n- ".join(errors))
    for warning in warnings:
        print(f"warning: {warning}")
    project = package["project.json"]
    story = package["story-source.json"]
    video = package["video-source.json"]
    storyboard = package["storyboard.json"]
    audio_config = project.get("audio")
    if not isinstance(audio_config, dict):
        audio_config = {}
    ambient_mode = text(audio_config.get("ambient_mode")) or "synthetic_gentle"
    raw_bgm_volume = audio_config.get("bgm_volume", 0.32)
    bgm_volume = number(raw_bgm_volume, "audio.bgm_volume")
    continuous_bgm = audio_config.get("continuous_bgm") is True
    if ambient_mode not in AMBIENT_MODES:
        raise HealingShortsError(f"지원하지 않는 배경음 모드입니다: {ambient_mode}")
    if not 0.0 <= bgm_volume <= 1.0:
        raise HealingShortsError("audio.bgm_volume은 0과 1 사이여야 합니다.")
    scenes = require_list(storyboard.get("scenes", []), "storyboard scenes")
    source = video_path(project_dir, video)
    source_probe = media_probe(source)
    output = project_dir / "outputs" / ("review.mp4" if draft else "short.mp4")
    if output.exists() and not args.overwrite:
        raise HealingShortsError(f"출력 파일이 이미 있습니다: {output}. 덮어쓰려면 --overwrite를 사용하세요.")
    output.parent.mkdir(parents=True, exist_ok=True)
    edit_package = project_dir / "edit-package"
    clips_dir = edit_package / "clips"
    audio_dir = edit_package / "audio"
    metadata_dir = edit_package / "metadata"
    for directory in (clips_dir, audio_dir, metadata_dir):
        directory.mkdir(parents=True, exist_ok=True)
    if continuous_bgm:
        for stale_bgm in audio_dir.glob("scene-*-bgm.wav"):
            stale_bgm.unlink()
    reports: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix=".healing2shorts-", dir=project_dir) as temp_name:
        work_dir = Path(temp_name)
        scene_paths: list[Path] = []
        for index, value in enumerate(scenes, start=1):
            scene = require_object(value, f"scene {index}")
            previous_text = text(scenes[index - 2].get("narration")) if index > 1 else ""
            next_text = text(scenes[index].get("narration")) if index < len(scenes) else ""
            narration, measured_audio, audio_source, dialogue_items = scene_narration_audio(
                scene,
                story,
                project,
                project_dir,
                work_dir,
                index,
                no_tts=args.no_tts,
                previous_text=previous_text,
                next_text=next_text,
            )
            requested = number(scene.get("duration"), f"scene {index}.duration")
            duration = max(requested, measured_audio + 0.25 if audio_source != "silent" else requested)
            scene_limit = (
                3.0
                if storyboard.get("story_contract_version", 1) in {2, 3}
                and text(scene.get("beat")) == "cold_open"
                else 8.0
            )
            if duration > scene_limit:
                raise HealingShortsError(
                    f"scene {index}의 음성 포함 길이가 {scene_limit:g}초를 초과합니다: "
                    f"{duration:.3f}"
                )
            caption_cues = dialogue_caption_cues(dialogue_items, duration)
            if not caption_cues:
                caption_cues = [
                    {
                        "text": text(scene.get("caption")),
                        "start_seconds": 0.0,
                        "end_seconds": round(duration, 3),
                    }
                ]
            overlays: list[dict[str, Any]] = []
            for cue_index, cue in enumerate(caption_cues, start=1):
                overlay_path = work_dir / f"overlay-{index:02d}-{cue_index:02d}.png"
                overlay_scene = dict(scene)
                overlay_scene["caption"] = text(cue.get("text"))
                draw_overlay(overlay_scene, project, story, overlay_path)
                overlays.append(
                    {
                        "path": overlay_path,
                        "start_seconds": cue["start_seconds"],
                        "end_seconds": cue["end_seconds"],
                    }
                )
            ambient = work_dir / f"ambient-{index:02d}.wav"
            scene_path = work_dir / f"scene-{index:02d}.mp4"
            if continuous_bgm:
                create_silent_audio(ambient, duration)
            else:
                create_ambient_audio(
                    ambient,
                    duration,
                    mode=ambient_mode,
                    scene_index=index - 1,
                )
            render_scene(
                source,
                source_probe,
                scene,
                overlays,
                narration,
                ambient,
                scene_path,
                duration,
                asmr_enabled=bool(project.get("audio", {}).get("source_asmr_enabled")),
                bgm_volume=0.0 if continuous_bgm else bgm_volume,
                output_width=output_width,
                output_height=output_height,
                crf=output_crf,
            )
            scene_paths.append(scene_path)
            raw_clip = clips_dir / f"scene-{index:02d}.mp4"
            render_raw_clip(source, scene, raw_clip, duration)
            narration_copy = audio_dir / f"scene-{index:02d}.wav"
            if narration.resolve() != narration_copy.resolve():
                shutil.copy2(narration, narration_copy)
            report = {
                "id": text(scene.get("id")) or f"scene-{index:02d}",
                "beat": text(scene.get("beat")),
                "requested_duration_seconds": round(requested, 3),
                "rendered_duration_seconds": round(duration, 3),
                "audio_source": audio_source,
                "source_start_seconds": scene.get("source_start_seconds"),
                "source_duration_seconds": scene.get("source_duration_seconds"),
                "edit_clip": relative_project_path(project_dir, raw_clip),
                "edit_audio": relative_project_path(project_dir, narration_copy),
                "caption_mode": "turn_synced" if dialogue_items else "scene",
                "caption_cues": caption_cues,
            }
            if not continuous_bgm:
                bgm_copy = audio_dir / f"scene-{index:02d}-bgm.wav"
                shutil.copy2(ambient, bgm_copy)
                report["edit_bgm"] = relative_project_path(project_dir, bgm_copy)
            reports.append(report)
        total = sum(float(item["rendered_duration_seconds"]) for item in reports)
        if not MIN_DURATION <= total <= MAX_DURATION:
            raise HealingShortsError(f"실제 렌더 길이는 30~45초여야 합니다: {total:.3f}초")
        concat = work_dir / "concat.txt"
        concat.write_text("".join(f"file '{path.as_posix()}'\n" for path in scene_paths), encoding="utf-8")
        joined_output = work_dir / "joined-without-bgm.mp4" if continuous_bgm else output
        run_checked(
            [
                shutil.which("ffmpeg") or "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat),
                "-c",
                "copy",
                "-movflags",
                "+faststart",
                "-y",
                str(joined_output),
            ],
            "최종 장면 연결",
        )
        if continuous_bgm:
            full_bgm = audio_dir / "background-music.wav"
            create_ambient_audio(full_bgm, total, mode=ambient_mode)
            mix_continuous_bgm(
                joined_output,
                full_bgm,
                output,
                duration=total,
                volume=bgm_volume,
            )
            relative_bgm = relative_project_path(project_dir, full_bgm)
            for report in reports:
                report["edit_bgm"] = relative_bgm
    probe = media_probe(output)
    if (probe["width"], probe["height"], probe["video_codec"], probe["audio_codec"]) != (
        output_width,
        output_height,
        "h264",
        "aac",
    ):
        raise HealingShortsError(
            f"렌더 결과가 {output_width}x{output_height} H.264/AAC 계약을 만족하지 않습니다."
        )
    if not MIN_DURATION - 0.1 <= float(probe["duration_seconds"]) <= MAX_DURATION + 0.1:
        raise HealingShortsError("렌더 결과 길이가 30~45초 범위를 벗어났습니다.")
    write_srt(edit_package / "captions.srt", scenes, reports)
    for name in (
        "project.json",
        "story-source.json",
        "video-source.json",
        "storyboard.json",
        "rights-manifest.json",
        "publish.json",
    ):
        shutil.copy2(project_dir / name, metadata_dir / name)
    edit_manifest = {
        "version": 1,
        "generated_at": iso_now(),
        "compatible_with": ["CapCut Desktop/Web", "Vrew"],
        "canvas": {"width": OUTPUT_WIDTH, "height": OUTPUT_HEIGHT, "frame_rate": FRAME_RATE},
        "source_audio_muted": not bool(project.get("audio", {}).get("source_asmr_enabled")),
        "background_music": {
            "mode": ambient_mode,
            "volume": bgm_volume,
            "rights": text(audio_config.get("bgm_rights")) or "synthetic_original",
            "continuous": continuous_bgm,
            "path": "audio/background-music.wav" if continuous_bgm else "",
        },
        "captions": "captions.srt",
        "scenes": reports,
        "metadata_dir": "metadata",
        "proof_boundary": "편집 패키지 생성이며 게시 권리 증명이 아닙니다.",
    }
    write_json(edit_package / "edit-manifest.json", edit_manifest)
    project["status"] = "draft_rendered" if draft else "rendered"
    project["updated_at"] = iso_now()
    project["last_render"] = {
        "path": relative_project_path(project_dir, output),
        "draft": draft,
        "width": output_width,
        "height": output_height,
        "frame_rate": FRAME_RATE,
        "rendered_at": iso_now(),
        "sha256": sha256_for(output),
    }
    if draft:
        project["draft_render"] = dict(project["last_render"])
    write_json(project_dir / "project.json", project)
    package["project.json"] = project
    upload_json, upload_md, publish_blocked = write_upload_package(
        project_dir,
        package,
        video_output=relative_project_path(project_dir, output),
        draft=draft,
    )
    shutil.copy2(project_dir / "project.json", metadata_dir / "project.json")
    shutil.copy2(project_dir / "publish.json", metadata_dir / "publish.json")
    report = {
        "version": 1,
        "rendered_at": iso_now(),
        "draft": draft,
        "output": relative_project_path(project_dir, output),
        "output_sha256": sha256_for(output),
        "probe": probe,
        "background_music": {
            "mode": ambient_mode,
            "volume": bgm_volume,
            "rights": text(audio_config.get("bgm_rights")) or "synthetic_original",
            "continuous": continuous_bgm,
            "path": relative_project_path(project_dir, audio_dir / "background-music.wav")
            if continuous_bgm
            else "",
        },
        "scenes": reports,
        "edit_package": relative_project_path(project_dir, edit_package / "edit-manifest.json"),
        "youtube_upload": {
            "json": relative_project_path(project_dir, upload_json),
            "markdown": relative_project_path(project_dir, upload_md),
            "publish_blocked": publish_blocked,
            "upload_performed": False,
        },
        "proof_boundary": "로컬 MP4 속성과 패키지 생성 확인이며 사실성·권리·수익화 증명이 아닙니다.",
    }
    write_json(project_dir / "render-report.json", report)
    print(output)
    return 0


def command_upload_package(args: argparse.Namespace) -> int:
    project_dir = Path(args.project_dir).expanduser().resolve()
    package = load_project_package(project_dir)
    project = package["project.json"]
    last_render = project.get("last_render")
    if not isinstance(last_render, dict) or not text(last_render.get("path")):
        raise HealingShortsError("업로드 패키지를 만들 렌더 결과가 없습니다.")
    _, markdown, _ = write_upload_package(
        project_dir,
        package,
        video_output=text(last_render.get("path")),
        draft=last_render.get("draft") is True,
    )
    print(markdown.read_text(encoding="utf-8"), end="")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="힐링쇼츠 로컬 제작 도구")
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor = subparsers.add_parser("doctor", help="로컬 렌더·Typecast 환경을 확인합니다.")
    doctor.add_argument("--json", action="store_true")
    doctor.set_defaults(handler=command_doctor)

    init = subparsers.add_parser("init", help="선택된 스토리와 음식 영상으로 프로젝트를 만듭니다.")
    init.add_argument("--story-candidates", required=True)
    init.add_argument("--story-id", required=True)
    init.add_argument("--video-candidates", required=True)
    init.add_argument("--video-id", required=True)
    source = init.add_mutually_exclusive_group(required=True)
    source.add_argument("--source-video")
    source.add_argument("--authorized-source-url")
    init.add_argument(
        "--confirm-download-rights",
        action="store_true",
        help="직접 원본 URL의 다운로드·편집 권리가 있음을 확인합니다.",
    )
    init.add_argument("--title")
    init.add_argument(
        "--duration",
        type=float,
        help="기본값: 대화형 v3 42초, 기존 v1/v2 36초",
    )
    init.add_argument("--project-dir")
    init.add_argument("--output-root", default="projects/healing2shorts")
    init.set_defaults(handler=command_init)

    preview = subparsers.add_parser("preview", help="접촉시트와 9:16 크롭 프리뷰를 만듭니다.")
    preview.add_argument("--project-dir", required=True)
    preview.add_argument("--overwrite", action="store_true")
    preview.set_defaults(handler=command_preview)

    rights = subparsers.add_parser("record-rights", help="영상 권리와 사람 검토 승인을 기록합니다.")
    rights.add_argument("--project-dir", required=True)
    rights.add_argument("--status", choices=sorted(RIGHTS_STATUSES), required=True)
    rights.add_argument("--rights-holder")
    rights.add_argument("--permission-date")
    rights.add_argument("--youtube-scope", choices=("yes", "no"))
    rights.add_argument("--commercial-use", choices=("yes", "no"))
    rights.add_argument("--editing-allowed", choices=("yes", "no"))
    rights.add_argument("--voice-overlay-allowed", choices=("yes", "no"))
    rights.add_argument("--source-asmr-approved", choices=("yes", "no"))
    rights.add_argument("--attribution")
    rights.add_argument("--expires-at")
    rights.add_argument("--permission-reference")
    rights.add_argument("--confirm-story-review", action="store_true")
    rights.add_argument("--confirm-visual-review", action="store_true")
    rights.add_argument("--confirm-sensitive-review", action="store_true")
    rights.add_argument("--confirm-upload-review", action="store_true")
    rights.add_argument("--overwrite", action="store_true")
    rights.set_defaults(handler=command_record_rights)

    validate = subparsers.add_parser("validate", help="검토 또는 게시 준비 상태를 검사합니다.")
    validate.add_argument("--project-dir", required=True)
    validate.add_argument("--publish-ready", action="store_true")
    validate.set_defaults(handler=command_validate)

    render = subparsers.add_parser("render", help="검토본 또는 최종 로컬 MP4를 렌더합니다.")
    render.add_argument("--project-dir", required=True)
    mode = render.add_mutually_exclusive_group(required=True)
    mode.add_argument("--draft", action="store_true")
    mode.add_argument("--final", action="store_true")
    render.add_argument("--no-tts", action="store_true")
    render.add_argument("--overwrite", action="store_true")
    render.set_defaults(handler=command_render)

    upload = subparsers.add_parser("upload-package", help="업로드 문구와 검토 상태를 출력합니다.")
    upload.add_argument("--project-dir", required=True)
    upload.set_defaults(handler=command_upload_package)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return int(args.handler(args))
    except HealingShortsError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("error: 사용자가 작업을 중단했습니다.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
