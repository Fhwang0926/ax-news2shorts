#!/usr/bin/env python3
"""Local Phase 1 pipeline for approval-gated Korean senior storytoon Shorts."""

from __future__ import annotations

import argparse
import copy
import functools
import getpass
import hashlib
import json
import math
import os
import re
import shutil
import ssl
import subprocess
import sys
import tempfile
import time
import uuid
from datetime import datetime, timezone
from datetime import timedelta
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
STORY_TEMPLATE = PLUGIN_ROOT / "templates" / "senior" / "story.template.json"
STYLE_PRESETS = PLUGIN_ROOT / "assets" / "senior" / "style-presets.json"
YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"
YOUTUBE_KEYCHAIN_SERVICE = "shorts-suite.youtube-data-api-key"
YOUTUBE_KEYCHAIN_LABEL = "Shorts Suite YouTube Data API key"
LEGACY_YOUTUBE_KEYCHAIN_SERVICE = "senior-shorts.youtube-data-api-key"
YOUTUBE_ENVIRONMENT_VARIABLE = "YOUTUBE_API_KEY"
DEFAULT_DISCOVERY_QUERIES = (
    "60대 가족 갈등 사연 쇼츠",
    "70대 반전 인생 사연 쇼츠",
    "은퇴 후 인간관계 사연 쇼츠",
)
SENIOR_SIGNAL_TERMS = (
    "60대",
    "70대",
    "80대",
    "시니어",
    "노년",
    "은퇴",
    "퇴직",
    "황혼",
    "부모",
    "아버지",
    "어머니",
    "할머니",
    "할아버지",
    "자식",
    "며느리",
    "사위",
)
STORY_ROLES = (
    "hook",
    "character_intro",
    "incident",
    "conflict",
    "escalation",
    "pre_reveal",
    "reveal",
    "afterglow",
)
HOOK_SCORE_FIELDS = (
    "curiosity",
    "emotion",
    "conflict",
    "clarity",
    "spoiler_control",
)
MOTIONS = {
    "static",
    "slow_zoom_in",
    "slow_zoom_out",
    "pan_left",
    "pan_right",
    "pan_up",
    "pan_down",
    "zoom_face",
}
EMOTIONS = {"sad", "tension", "shock", "warm", "happy", "mystery", "neutral"}
AUDIO_EXTENSIONS = (".aiff", ".aif", ".wav", ".mp3", ".m4a", ".aac", ".flac")
IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp")
FONT_CANDIDATES = (
    Path("/System/Library/Fonts/AppleSDGothicNeo.ttc"),
    Path("/System/Library/Fonts/Supplemental/AppleGothic.ttf"),
    Path("/Library/Fonts/NotoSansCJKkr-Regular.otf"),
)


class SeniorShortsError(RuntimeError):
    pass


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def clean(value: Any) -> str:
    return " ".join(str(value or "").split())


def read_json(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except FileNotFoundError as exc:
        raise SeniorShortsError(f"파일을 찾을 수 없습니다: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SeniorShortsError(f"JSON 형식이 올바르지 않습니다: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise SeniorShortsError(f"JSON 최상위 값은 객체여야 합니다: {path}")
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, delete=False, suffix=".tmp"
    ) as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        temporary = Path(handle.name)
    os.replace(temporary, path)


def print_json(payload: Any) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(command, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        detail = clean(completed.stderr) or clean(completed.stdout) or "명령 실행 실패"
        raise SeniorShortsError(f"{Path(command[0]).name}: {detail}")
    return completed


def project_paths(project_dir: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    project_dir = project_dir.resolve()
    project = read_json(project_dir / "project.json")
    story = read_json(project_dir / "story.json")
    return project, story


def save_project(project_dir: Path, project: dict[str, Any]) -> None:
    project["updated_at"] = now_iso()
    write_json(project_dir / "project.json", project)


def set_state(
    project: dict[str, Any], stage: str, status: str, detail: str = ""
) -> None:
    states = project.setdefault("states", {})
    states[stage] = {"status": status, "updated_at": now_iso(), "detail": detail}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def approval_current(project_dir: Path, project: dict[str, Any], key: str) -> bool:
    approvals = project.get("approvals") or {}
    if not bool(approvals.get(key)):
        return False
    if key == "script_reviewed":
        return approvals.get("script_sha256") == sha256_file(project_dir / "story.json")
    if key == "character_reviewed":
        image = expected_image(project_dir, 1)
        return bool(image and approvals.get("character_image_sha256") == sha256_file(image))
    if key == "synthetic_disclosure_reviewed":
        return approvals.get("disclosure_text") == clean(project.get("disclosure_text"))
    if key == "draft_reviewed":
        draft = project_dir / "final" / "review.mp4"
        return bool(draft.is_file() and approvals.get("draft_sha256") == sha256_file(draft))
    return True


def require_approval(
    project_dir: Path, project: dict[str, Any], key: str, message: str
) -> None:
    if not approval_current(project_dir, project, key):
        raise SeniorShortsError(message)


def expected_image(project_dir: Path, scene_number: int) -> Path | None:
    base = project_dir / "images" / f"scene{scene_number:02d}"
    return next((base.with_suffix(ext) for ext in IMAGE_EXTENSIONS if base.with_suffix(ext).is_file()), None)


def expected_audio(project_dir: Path, scene_number: int) -> Path | None:
    base = project_dir / "audio" / f"scene{scene_number:02d}"
    return next((base.with_suffix(ext) for ext in AUDIO_EXTENSIONS if base.with_suffix(ext).is_file()), None)


def youtube_setup_command(command: str) -> str:
    script = PLUGIN_ROOT / "scripts" / "shorts_suite.py"
    return f'python3 -B "{script}" senior {command}'


@functools.cache
def trusted_ca_file() -> str:
    default_paths = ssl.get_default_verify_paths()
    if default_paths.cafile and Path(default_paths.cafile).is_file():
        return str(Path(default_paths.cafile))
    for candidate in (
        Path("/etc/ssl/cert.pem"),
        Path("/opt/homebrew/etc/openssl@3/cert.pem"),
    ):
        if candidate.is_file():
            return str(candidate)
    return ""


@functools.cache
def verified_ssl_context() -> ssl.SSLContext:
    ca_file = trusted_ca_file()
    if ca_file:
        return ssl.create_default_context(cafile=ca_file)
    return ssl.create_default_context()


def youtube_keychain_check_limited() -> bool:
    return sys.platform == "darwin" and bool(os.environ.get("CODEX_SANDBOX"))


def keychain_youtube_api_key(service: str = YOUTUBE_KEYCHAIN_SERVICE) -> str:
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
                service,
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
def youtube_api_key_record() -> tuple[str, str | None]:
    environment_key = os.environ.get(YOUTUBE_ENVIRONMENT_VARIABLE, "").strip()
    if environment_key:
        return environment_key, "environment"
    keychain_key = keychain_youtube_api_key()
    if keychain_key:
        return keychain_key, "keychain"
    legacy_keychain_key = keychain_youtube_api_key(LEGACY_YOUTUBE_KEYCHAIN_SERVICE)
    if legacy_keychain_key:
        return legacy_keychain_key, "legacy-keychain"
    return "", None


def youtube_request(
    resource: str,
    params: dict[str, Any],
    *,
    api_key: str | None = None,
    timeout: float = 20,
) -> dict[str, Any]:
    resolved_key = (api_key or youtube_api_key_record()[0]).strip()
    if not resolved_key:
        raise SeniorShortsError(
            "YouTube Data API 키가 없습니다. "
            f"`{youtube_setup_command('configure-youtube')}`를 먼저 실행하세요."
        )
    url = f"{YOUTUBE_API_BASE}/{resource}?{urlencode(params, doseq=True)}"
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "senior-shorts/0.1",
            "X-Goog-Api-Key": resolved_key,
        },
    )
    try:
        with urlopen(request, timeout=timeout, context=verified_ssl_context()) as response:
            body = response.read()
    except HTTPError as exc:
        detail = ""
        try:
            payload = json.loads(exc.read().decode("utf-8"))
            detail = clean(((payload.get("error") or {}).get("message")))
        except (UnicodeDecodeError, json.JSONDecodeError, AttributeError):
            detail = ""
        suffix = f": {detail}" if detail else ""
        raise SeniorShortsError(f"YouTube Data API 요청 실패 ({exc.code}){suffix}") from exc
    except (URLError, TimeoutError) as exc:
        raise SeniorShortsError(f"YouTube Data API 연결 실패: {exc}") from exc
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SeniorShortsError("YouTube Data API JSON 응답을 읽을 수 없습니다.") from exc
    if not isinstance(payload, dict):
        raise SeniorShortsError("YouTube Data API 응답 형식이 올바르지 않습니다.")
    return payload


def validate_youtube_api_key(api_key: str | None = None) -> None:
    youtube_request(
        "i18nRegions",
        {"part": "snippet", "hl": "ko", "fields": "items(id)"},
        api_key=api_key,
        timeout=15,
    )


def parse_youtube_duration(value: str) -> float:
    match = re.fullmatch(
        r"P(?:(?P<days>\d+)D)?T(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?",
        value or "",
    )
    if not match:
        return 0.0
    return (
        int(match.group("days") or 0) * 86400
        + int(match.group("hours") or 0) * 3600
        + int(match.group("minutes") or 0) * 60
        + int(match.group("seconds") or 0)
    )


def parse_youtube_published(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except (ValueError, AttributeError):
        return datetime.now(timezone.utc)


def score_youtube_signal(
    title: str,
    published_at: str,
    views: int,
    comments: int,
    window_days: int,
) -> dict[str, float]:
    age_days = max(1.0, (datetime.now(timezone.utc) - parse_youtube_published(published_at)).total_seconds() / 86400)
    views_per_day = views / age_days
    velocity = min(40.0, math.log10(views_per_day + 1) / 5 * 40)
    comments_per_thousand = comments / max(views, 1) * 1000
    engagement = min(20.0, comments_per_thousand * 2)
    recency = max(0.0, 20.0 * (1 - age_days / max(window_days, 1)))
    relevance_count = sum(1 for term in SENIOR_SIGNAL_TERMS if term in title)
    relevance = min(20.0, relevance_count * 5)
    return {
        "view_velocity": round(velocity, 2),
        "comment_engagement": round(engagement, 2),
        "recency": round(recency, 2),
        "senior_relevance": round(relevance, 2),
        "total": round(velocity + engagement + recency + relevance, 2),
        "views_per_day": round(views_per_day, 2),
        "comments_per_thousand_views": round(comments_per_thousand, 3),
    }


def validate_story(story: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if not clean(story.get("title")):
        errors.append("title이 필요합니다.")
    if story.get("fictionalization") != "fictionalized":
        errors.append("Phase 1 사연은 fictionalization=fictionalized여야 합니다.")

    try:
        target_duration = float(story.get("target_duration"))
    except (TypeError, ValueError):
        target_duration = 0
        errors.append("target_duration은 숫자여야 합니다.")
    if target_duration and not 45 <= target_duration <= 60:
        errors.append("target_duration은 45~60초여야 합니다.")

    characters = story.get("characters")
    if not isinstance(characters, list) or not characters:
        errors.append("characters는 1명 이상의 배열이어야 합니다.")
        characters = []
    character_ids: set[str] = set()
    for index, character in enumerate(characters, 1):
        if not isinstance(character, dict):
            errors.append(f"characters[{index}]는 객체여야 합니다.")
            continue
        character_id = clean(character.get("id"))
        if not character_id:
            errors.append(f"characters[{index}].id가 필요합니다.")
        elif character_id in character_ids:
            errors.append(f"캐릭터 id가 중복됩니다: {character_id}")
        character_ids.add(character_id)
        for field in ("name", "age", "gender", "appearance", "hair", "clothes", "personality"):
            if character.get(field) in (None, ""):
                errors.append(f"characters[{index}].{field}가 필요합니다.")

    hooks = story.get("hooks")
    if not isinstance(hooks, list) or len(hooks) != 5:
        errors.append("hooks는 정확히 5개여야 합니다.")
        hooks = []
    hook_ids: set[str] = set()
    hook_totals: dict[str, int] = {}
    hook_texts: dict[str, str] = {}
    for index, hook in enumerate(hooks, 1):
        if not isinstance(hook, dict):
            errors.append(f"hooks[{index}]는 객체여야 합니다.")
            continue
        hook_id = clean(hook.get("id"))
        hook_text = clean(hook.get("text"))
        if not hook_id or hook_id in hook_ids:
            errors.append(f"hooks[{index}].id가 비어 있거나 중복됩니다.")
        if not hook_text:
            errors.append(f"hooks[{index}].text가 필요합니다.")
        hook_ids.add(hook_id)
        hook_texts[hook_id] = hook_text
        scores = hook.get("scores")
        if not isinstance(scores, dict):
            errors.append(f"hooks[{index}].scores가 필요합니다.")
            continue
        score_total = 0
        valid_scores = True
        for field in HOOK_SCORE_FIELDS:
            value = scores.get(field)
            if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 20:
                errors.append(f"hooks[{index}].scores.{field}는 0~20 정수여야 합니다.")
                valid_scores = False
            else:
                score_total += value
        if valid_scores and hook.get("total") != score_total:
            errors.append(f"hooks[{index}].total은 세부 점수 합계 {score_total}이어야 합니다.")
        if valid_scores:
            hook_totals[hook_id] = score_total

    selected_hook_id = clean(story.get("selected_hook_id"))
    if selected_hook_id not in hook_ids:
        errors.append("selected_hook_id는 hooks의 id 중 하나여야 합니다.")
    elif hook_totals and hook_totals.get(selected_hook_id) != max(hook_totals.values()):
        errors.append("selected_hook_id는 합계가 가장 높은 훅이어야 합니다.")
    if selected_hook_id in hook_texts and clean(story.get("hook")) != hook_texts[selected_hook_id]:
        errors.append("hook은 선택된 훅의 text와 같아야 합니다.")

    scenes = story.get("scenes")
    if not isinstance(scenes, list) or len(scenes) != 8:
        errors.append("scenes는 정확히 8개여야 합니다.")
        scenes = []
    total_duration = 0.0
    narration_length = 0
    for index, scene in enumerate(scenes, 1):
        if not isinstance(scene, dict):
            errors.append(f"scenes[{index}]는 객체여야 합니다.")
            continue
        if scene.get("scene") != index:
            errors.append(f"scenes[{index}].scene은 {index}여야 합니다.")
        if scene.get("role") != STORY_ROLES[index - 1]:
            errors.append(f"Scene {index} role은 {STORY_ROLES[index - 1]}여야 합니다.")
        narration = clean(scene.get("narration"))
        subtitle = str(scene.get("subtitle") or "").strip()
        if not narration:
            errors.append(f"Scene {index} narration이 필요합니다.")
        if not subtitle:
            errors.append(f"Scene {index} subtitle이 필요합니다.")
        narration_length += len(narration.replace(" ", ""))
        subtitle_lines = subtitle.splitlines()
        if len(subtitle_lines) > 2:
            errors.append(f"Scene {index} subtitle은 2줄 이하여야 합니다.")
        for line in subtitle_lines:
            if len(line.replace(" ", "")) > 16:
                errors.append(f"Scene {index} subtitle 한 줄은 공백 제외 16자 이하여야 합니다.")
        highlights = scene.get("highlight")
        if not isinstance(highlights, list) or len(highlights) > 2:
            errors.append(f"Scene {index} highlight는 최대 2개의 배열이어야 합니다.")
        else:
            for word in highlights:
                if clean(word) and clean(word) not in clean(subtitle):
                    errors.append(f"Scene {index} highlight가 subtitle에 없습니다: {word}")
        scene_characters = scene.get("characters")
        if not isinstance(scene_characters, list):
            errors.append(f"Scene {index} characters는 배열이어야 합니다.")
        else:
            unknown = [clean(item) for item in scene_characters if clean(item) not in character_ids]
            if unknown:
                errors.append(f"Scene {index}에 정의되지 않은 캐릭터가 있습니다: {', '.join(unknown)}")
        if not clean(scene.get("visual_prompt")):
            errors.append(f"Scene {index} visual_prompt가 필요합니다.")
        if scene.get("emotion") not in EMOTIONS:
            errors.append(f"Scene {index} emotion이 지원 목록에 없습니다.")
        if scene.get("motion") not in MOTIONS:
            errors.append(f"Scene {index} motion이 지원 목록에 없습니다.")
        if scene.get("video_mode") not in {"static", "ken_burns"}:
            errors.append(f"Scene {index} video_mode는 static 또는 ken_burns여야 합니다.")
        try:
            duration = float(scene.get("duration"))
        except (TypeError, ValueError):
            errors.append(f"Scene {index} duration은 숫자여야 합니다.")
            duration = 0
        if duration and not 3 <= duration <= 12:
            errors.append(f"Scene {index} duration은 3~12초여야 합니다.")
        total_duration += duration

    if scenes and not 45 <= total_duration <= 60:
        errors.append(f"장면 duration 합계는 45~60초여야 합니다: {total_duration:.2f}초")
    if target_duration and abs(total_duration - target_duration) > 3:
        warnings.append(
            f"장면 duration 합계가 목표 길이와 3초 넘게 다릅니다: {total_duration:.2f}/{target_duration:.2f}초"
        )
    if narration_length and narration_length < 180:
        warnings.append("전체 내레이션이 짧아 목표 길이에 비해 여백이 많을 수 있습니다.")
    if narration_length > 600:
        warnings.append("전체 내레이션이 길어 빠른 말하기가 필요할 수 있습니다.")
    return errors, warnings


def approval_errors(
    project_dir: Path, project: dict[str, Any], publish_ready: bool = False
) -> list[str]:
    required = {
        "script_reviewed": "대본 승인이 필요합니다.",
        "character_reviewed": "첫 캐릭터 이미지 승인이 필요합니다.",
        "synthetic_disclosure_reviewed": "합성·창작 고지 승인이 필요합니다.",
    }
    if publish_ready:
        required["draft_reviewed"] = "검토본 승인이 필요합니다."
    return [message for key, message in required.items() if not approval_current(project_dir, project, key)]


def asset_errors(project_dir: Path, story: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for scene in story.get("scenes") or []:
        number = int(scene.get("scene") or 0)
        if not expected_image(project_dir, number):
            errors.append(f"Scene {number} 이미지가 없습니다.")
        if not expected_audio(project_dir, number):
            errors.append(f"Scene {number} 음성이 없습니다.")
    audio_manifest_path = project_dir / "audio" / "audio-manifest.json"
    if not audio_manifest_path.is_file():
        errors.append("audio/audio-manifest.json이 없습니다.")
    else:
        audio_manifest = read_json(audio_manifest_path)
        if audio_manifest.get("story_sha256") != sha256_file(project_dir / "story.json"):
            errors.append("음성이 현재 story.json과 일치하지 않습니다. voice를 다시 실행하세요.")
        try:
            duration = float(audio_manifest.get("duration") or 0)
        except (TypeError, ValueError):
            duration = 0
        if not 45 <= duration <= 60:
            errors.append(f"음성 타임라인 합계는 45~60초여야 합니다: {duration:.3f}초")
    subtitle_json_path = project_dir / "subtitles" / "subtitle.json"
    if not (project_dir / "subtitles" / "subtitle.ass").is_file():
        errors.append("subtitles/subtitle.ass가 없습니다.")
    if not subtitle_json_path.is_file():
        errors.append("subtitles/subtitle.json이 없습니다.")
    elif audio_manifest_path.is_file():
        subtitle_manifest = read_json(subtitle_json_path)
        if subtitle_manifest.get("story_sha256") != sha256_file(project_dir / "story.json"):
            errors.append("자막이 현재 story.json과 일치하지 않습니다. subtitle을 다시 실행하세요.")
        if subtitle_manifest.get("audio_manifest_sha256") != sha256_file(audio_manifest_path):
            errors.append("자막이 현재 음성 타임라인과 일치하지 않습니다. subtitle을 다시 실행하세요.")
    return errors


def media_report(path: Path) -> dict[str, Any]:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        raise SeniorShortsError("미디어 검사에는 ffprobe가 필요합니다.")
    completed = run(
        [
            ffprobe,
            "-v",
            "error",
            "-show_streams",
            "-show_format",
            "-of",
            "json",
            str(path),
        ]
    )
    return json.loads(completed.stdout)


def final_media_errors(path: Path) -> tuple[list[str], dict[str, Any]]:
    if not path.is_file():
        return [f"최종 영상을 찾을 수 없습니다: {path}"], {}
    report = media_report(path)
    streams = report.get("streams") or []
    videos = [stream for stream in streams if stream.get("codec_type") == "video"]
    audios = [stream for stream in streams if stream.get("codec_type") == "audio"]
    errors: list[str] = []
    if not videos:
        errors.append("영상 스트림이 없습니다.")
    else:
        video = videos[0]
        if video.get("width") != 1080 or video.get("height") != 1920:
            errors.append(f"해상도는 1080x1920이어야 합니다: {video.get('width')}x{video.get('height')}")
    if not audios:
        errors.append("오디오 스트림이 없습니다.")
    try:
        duration = float((report.get("format") or {}).get("duration") or 0)
    except (TypeError, ValueError):
        duration = 0
    if duration and not 45 <= duration <= 61:
        errors.append(f"영상 길이는 45~60초 범위여야 합니다: {duration:.3f}초")
    return errors, report


def command_doctor(args: argparse.Namespace) -> None:
    font = next((str(path) for path in FONT_CANDIDATES if path.is_file()), "")
    ffmpeg = shutil.which("ffmpeg") or ""
    try:
        import PIL

        pillow = PIL.__version__
    except ImportError:
        pillow = ""
    libass_ready = bool(
        ffmpeg and ffmpeg_has_filter(ffmpeg, "ass") and ffmpeg_has_filter(ffmpeg, "drawtext")
    )
    pillow_overlay_ready = bool(
        ffmpeg and pillow and ffmpeg_has_filter(ffmpeg, "overlay") and font
    )
    subtitle_renderer = (
        "libass" if libass_ready else "pillow-overlay" if pillow_overlay_ready else ""
    )
    youtube_key, youtube_key_source = youtube_api_key_record()
    youtube_check_limited = youtube_key_source is None and youtube_keychain_check_limited()
    youtube_api_reachable: bool | None = None
    youtube_api_error = ""
    if args.check_youtube and youtube_key:
        try:
            validate_youtube_api_key(youtube_key)
            youtube_api_reachable = True
        except SeniorShortsError as exc:
            youtube_api_reachable = False
            youtube_api_error = str(exc)
    if youtube_key_source:
        youtube_guidance = "YouTube Data API 키를 사용할 수 있습니다."
    elif youtube_check_limited:
        youtube_guidance = (
            "현재 Codex 실행에서는 macOS 키체인 조회가 제한될 수 있습니다. "
            f"사용자 터미널에서 `{youtube_setup_command('doctor --check-youtube --json')}`를 다시 실행하세요."
        )
    else:
        youtube_guidance = (
            "YouTube Data API 키가 없습니다. "
            f"`{youtube_setup_command('configure-youtube')}`를 한 번 실행하세요."
        )
    result: dict[str, Any] = {
        "python": sys.version.split()[0],
        "ffmpeg": ffmpeg,
        "ffprobe": shutil.which("ffprobe") or "",
        "pillow": pillow,
        "macos_say": shutil.which("say") or "",
        "korean_font": font,
        "subtitle_renderer": subtitle_renderer,
        "comfyui": {"url": args.comfyui_url, "running": False, "detail": "not checked"},
        "youtube_api": {
            "configured": youtube_key_source is not None,
            "source": youtube_key_source,
            "keychain_check_limited": youtube_check_limited,
            "checked": bool(args.check_youtube),
            "reachable": youtube_api_reachable,
            "error": youtube_api_error,
            "setup_command": "" if youtube_key_source else youtube_setup_command("configure-youtube"),
            "guidance": youtube_guidance,
            "ssl_ca_file": trusted_ca_file(),
            "ssl_verification_enabled": True,
        },
    }
    if args.comfyui_url:
        try:
            request_json(f"{args.comfyui_url.rstrip('/')}/system_stats", timeout=2)
            result["comfyui"] = {"url": args.comfyui_url, "running": True, "detail": "ok"}
        except SeniorShortsError as exc:
            result["comfyui"] = {"url": args.comfyui_url, "running": False, "detail": str(exc)}
    result["ready_for_render"] = bool(
        result["ffmpeg"] and result["ffprobe"] and font and subtitle_renderer
    )
    result["ready_for_discovery"] = bool(
        youtube_key_source and (youtube_api_reachable is not False)
    )
    if args.json:
        print_json(result)
    else:
        for key, value in result.items():
            print(f"{key}: {value}")


def command_configure_youtube(args: argparse.Namespace) -> None:
    if sys.platform != "darwin":
        raise SeniorShortsError(
            "macOS 키체인은 이 운영체제에서 사용할 수 없습니다. "
            f"{YOUTUBE_ENVIRONMENT_VARIABLE} 환경변수를 사용하세요."
        )
    security = shutil.which("security")
    if not security:
        raise SeniorShortsError("macOS security 명령을 찾을 수 없습니다.")
    print("YouTube Data API 키를 macOS 키체인에 저장합니다.")
    print("표시되는 password 프롬프트에 키를 입력하세요. 입력 내용은 화면에 표시되지 않습니다.")
    try:
        result = subprocess.run(
            [
                security,
                "add-generic-password",
                "-U",
                "-a",
                getpass.getuser(),
                "-s",
                YOUTUBE_KEYCHAIN_SERVICE,
                "-l",
                YOUTUBE_KEYCHAIN_LABEL,
                "-w",
            ],
            check=False,
        )
    except OSError as exc:
        raise SeniorShortsError(f"macOS 키체인 실행 실패: {exc}") from exc
    if result.returncode != 0:
        raise SeniorShortsError("YouTube Data API 키를 macOS 키체인에 저장하지 못했습니다.")
    youtube_api_key_record.cache_clear()
    stored_key, source = youtube_api_key_record()
    if not stored_key or source != "keychain":
        raise SeniorShortsError("저장 후 YouTube Data API 키를 키체인에서 확인하지 못했습니다.")
    try:
        validate_youtube_api_key(stored_key)
    except SeniorShortsError as exc:
        raise SeniorShortsError(
            "키는 키체인에 저장했지만 YouTube Data API 검증에 실패했습니다. "
            "Google Cloud에서 YouTube Data API v3 활성화와 API 제한을 확인하세요. "
            f"원인: {exc}"
        ) from exc
    print("YouTube Data API 키를 키체인에 저장하고 공개 데이터 조회를 확인했습니다.")


def command_discover(args: argparse.Namespace) -> None:
    if not 1 <= args.days <= 365:
        raise SeniorShortsError("days는 1~365 범위여야 합니다.")
    if not 1 <= args.per_query <= 25:
        raise SeniorShortsError("per-query는 1~25 범위여야 합니다.")
    if not 1 <= args.max_signals <= 100:
        raise SeniorShortsError("max-signals는 1~100 범위여야 합니다.")
    if not 30 <= args.max_duration <= 180:
        raise SeniorShortsError("max-duration은 30~180초 범위여야 합니다.")
    queries = list(dict.fromkeys(clean(query) for query in (args.query or DEFAULT_DISCOVERY_QUERIES)))
    queries = [query for query in queries if query]
    if not queries:
        raise SeniorShortsError("검색어가 필요합니다.")
    api_key, source = youtube_api_key_record()
    if not api_key:
        raise SeniorShortsError(
            "YouTube Data API 키가 없습니다. "
            f"`{youtube_setup_command('configure-youtube')}`를 먼저 실행하세요."
        )
    published_after = (datetime.now(timezone.utc) - timedelta(days=args.days)).isoformat(
        timespec="seconds"
    ).replace("+00:00", "Z")
    matches: dict[str, dict[str, Any]] = {}
    for query in queries:
        response = youtube_request(
            "search",
            {
                "part": "snippet",
                "q": query,
                "type": "video",
                "order": "viewCount",
                "videoDuration": "short",
                "publishedAfter": published_after,
                "regionCode": "KR",
                "relevanceLanguage": "ko",
                "safeSearch": "moderate",
                "maxResults": args.per_query,
                "fields": "items(id/videoId,snippet(title,channelId,channelTitle,publishedAt,thumbnails/high/url))",
            },
            api_key=api_key,
        )
        for item in response.get("items") or []:
            video_id = clean((item.get("id") or {}).get("videoId"))
            if not video_id:
                continue
            record = matches.setdefault(
                video_id,
                {
                    "video_id": video_id,
                    "search_snippet": item.get("snippet") or {},
                    "matched_queries": [],
                },
            )
            if query not in record["matched_queries"]:
                record["matched_queries"].append(query)
    video_ids = list(matches)
    signals: list[dict[str, Any]] = []
    videos_calls = 0
    for offset in range(0, len(video_ids), 50):
        chunk = video_ids[offset : offset + 50]
        if not chunk:
            continue
        videos_calls += 1
        response = youtube_request(
            "videos",
            {
                "part": "snippet,statistics,contentDetails,status",
                "id": ",".join(chunk),
                "fields": "items(id,snippet(title,channelId,channelTitle,publishedAt,thumbnails/high/url),statistics(viewCount,commentCount,likeCount),contentDetails/duration,status(privacyStatus,embeddable))",
            },
            api_key=api_key,
        )
        for item in response.get("items") or []:
            video_id = clean(item.get("id"))
            matched = matches.get(video_id)
            if not matched:
                continue
            duration = parse_youtube_duration(clean((item.get("contentDetails") or {}).get("duration")))
            if not duration or duration > args.max_duration:
                continue
            snippet = item.get("snippet") or matched["search_snippet"]
            statistics = item.get("statistics") or {}
            status = item.get("status") or {}
            title = clean(snippet.get("title"))
            published_at = clean(snippet.get("publishedAt"))
            try:
                views = int(statistics.get("viewCount") or 0)
                comments = int(statistics.get("commentCount") or 0)
                likes = int(statistics.get("likeCount") or 0)
            except (TypeError, ValueError):
                views, comments, likes = 0, 0, 0
            score = score_youtube_signal(title, published_at, views, comments, args.days)
            signals.append(
                {
                    "signal_id": f"yt-{video_id}",
                    "platform": "youtube",
                    "video_id": video_id,
                    "canonical_url": f"https://www.youtube.com/watch?v={video_id}",
                    "title": title,
                    "channel_id": clean(snippet.get("channelId")),
                    "channel_title": clean(snippet.get("channelTitle")),
                    "published_at": published_at,
                    "duration_seconds": round(duration, 3),
                    "views": views,
                    "likes": likes,
                    "comments": comments,
                    "thumbnail_url": clean(((snippet.get("thumbnails") or {}).get("high") or {}).get("url")),
                    "matched_queries": matched["matched_queries"],
                    "score": score,
                    "public_status": clean(status.get("privacyStatus")),
                    "embeddable": bool(status.get("embeddable")),
                    "rights_state": "signal_only",
                    "reuse_allowed": False,
                    "source_text_use": "pattern_only",
                }
            )
    signals.sort(key=lambda item: item["score"]["total"], reverse=True)
    signals = signals[: args.max_signals]
    if not signals:
        raise SeniorShortsError("조건에 맞는 YouTube 소재 신호를 찾지 못했습니다.")
    output = (
        Path(args.output).resolve()
        if args.output
        else Path.cwd()
        / "outputs"
        / "senior-shorts"
        / "discovery"
        / datetime.now().strftime("%Y%m%d_%H%M%S")
        / "youtube-signals.json"
    )
    payload = {
        "schema_version": 1,
        "generated_at": now_iso(),
        "source": "youtube_data_api_v3",
        "api_key_source": source,
        "window_days": args.days,
        "published_after": published_after,
        "queries": queries,
        "quota_estimate": {
            "search_list_calls": len(queries),
            "videos_list_calls": videos_calls,
            "note": "각 추가 페이지는 별도 호출입니다. 이 명령은 페이지네이션하지 않습니다.",
        },
        "selection_required": True,
        "production_allowed": False,
        "rights_policy": "메타데이터는 소재 신호에만 사용하며 영상, 대사, 사건, 결말을 복제하지 않습니다.",
        "signals": signals,
    }
    write_json(output, payload)
    print_json(
        {
            "output": str(output),
            "signals": len(signals),
            "selection_required": True,
            "next": "신호를 묶어 서로 다른 창작 후보를 정확히 3개 작성한 뒤 사용자 선택을 기다리세요.",
        }
    )


def validate_candidate_file(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    candidates = payload.get("candidates")
    if not isinstance(candidates, list) or len(candidates) != 3:
        return ["candidates는 정확히 3개여야 합니다."]
    candidate_ids: set[str] = set()
    for index, candidate in enumerate(candidates, 1):
        if not isinstance(candidate, dict):
            errors.append(f"candidates[{index}]는 객체여야 합니다.")
            continue
        candidate_id = clean(candidate.get("id"))
        if not candidate_id or candidate_id in candidate_ids:
            errors.append(f"candidates[{index}].id가 비어 있거나 중복됩니다.")
        candidate_ids.add(candidate_id)
        for field in (
            "title",
            "logline",
            "audience_pain",
            "conflict",
            "twist_direction",
            "eight_scene_fit",
            "originality_note",
        ):
            if not clean(candidate.get(field)):
                errors.append(f"candidates[{index}].{field}가 필요합니다.")
        signal_ids = candidate.get("source_signal_ids")
        if not isinstance(signal_ids, list) or not signal_ids:
            errors.append(f"candidates[{index}].source_signal_ids가 필요합니다.")
        if candidate.get("rights_mode") != "original_fiction":
            errors.append(f"candidates[{index}].rights_mode는 original_fiction이어야 합니다.")
        try:
            score = float(candidate.get("score"))
        except (TypeError, ValueError):
            score = -1
        if not 0 <= score <= 100:
            errors.append(f"candidates[{index}].score는 0~100이어야 합니다.")
    return errors


def command_select(args: argparse.Namespace) -> None:
    candidates_path = Path(args.candidates).resolve()
    payload = read_json(candidates_path)
    errors = validate_candidate_file(payload)
    if errors:
        raise SeniorShortsError("후보 검증에 실패했습니다: " + " / ".join(errors))
    selected = next(
        (candidate for candidate in payload["candidates"] if clean(candidate.get("id")) == args.candidate_id),
        None,
    )
    if selected is None:
        raise SeniorShortsError(f"후보를 찾을 수 없습니다: {args.candidate_id}")
    output = Path(args.output).resolve() if args.output else candidates_path.parent / "selection.json"
    selection = {
        "schema_version": 1,
        "selected_at": now_iso(),
        "candidate_file": str(candidates_path),
        "candidate_file_sha256": sha256_file(candidates_path),
        "selected_candidate_id": args.candidate_id,
        "selected_candidate": selected,
        "user_selection_required": True,
        "selection_recorded": True,
    }
    write_json(output, selection)
    print_json({"output": str(output), "selected_candidate_id": args.candidate_id})


def command_init(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir).resolve()
    if (project_dir / "project.json").exists() or (project_dir / "story.json").exists():
        raise SeniorShortsError("기존 프로젝트는 init으로 덮어쓸 수 없습니다.")
    if not 45 <= args.duration <= 60:
        raise SeniorShortsError("duration은 45~60초여야 합니다.")
    for name in ("discovery", "images", "audio", "subtitles", "video", "final"):
        (project_dir / name).mkdir(parents=True, exist_ok=True)
    selection: dict[str, Any] | None = None
    if args.selection:
        selection_path = Path(args.selection).resolve()
        selection = read_json(selection_path)
        selected = selection.get("selected_candidate")
        if not isinstance(selected, dict) or not clean(selected.get("logline")):
            raise SeniorShortsError("selection.json에 선택된 창작 후보가 없습니다.")
        if not selection.get("selection_recorded") or selected.get("rights_mode") != "original_fiction":
            raise SeniorShortsError("select 명령으로 기록된 original_fiction 후보만 사용할 수 있습니다.")
        topic = clean(selected.get("logline"))
        shutil.copy2(selection_path, project_dir / "discovery" / "selection.json")
    else:
        topic = clean(args.topic)
    if not topic:
        raise SeniorShortsError("topic 또는 selection이 필요합니다.")
    story = read_json(STORY_TEMPLATE)
    story["source_topic"] = topic
    story["target_age"] = args.target_age
    story["target_duration"] = args.duration
    durations = [float(scene["duration"]) for scene in story["scenes"]]
    scale = args.duration / sum(durations)
    adjusted = [round(value * scale, 2) for value in durations]
    adjusted[-1] = round(adjusted[-1] + args.duration - sum(adjusted), 2)
    for scene, duration in zip(story["scenes"], adjusted):
        scene["duration"] = duration
    project = {
        "schema_version": 1,
        "plugin": "senior-shorts",
        "content_type": "fictional_storytoon",
        "topic": topic,
        "target_age": args.target_age,
        "target_duration": args.duration,
        "style_id": "korean_senior_storytoon_v1",
        "disclosure_text": "AI로 제작한 창작 사연입니다.",
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "approvals": {
            "script_reviewed": False,
            "character_reviewed": False,
            "synthetic_disclosure_reviewed": False,
            "draft_reviewed": False,
        },
        "states": {
            "story": {"status": "pending", "updated_at": now_iso(), "detail": "story.json 작성 필요"},
            "image_prompts": {"status": "pending", "updated_at": now_iso(), "detail": ""},
            "images": {"status": "pending", "updated_at": now_iso(), "detail": ""},
            "voice": {"status": "pending", "updated_at": now_iso(), "detail": ""},
            "subtitles": {"status": "pending", "updated_at": now_iso(), "detail": ""},
            "render": {"status": "pending", "updated_at": now_iso(), "detail": ""},
        },
    }
    if selection is not None:
        project["discovery"] = {
            "selection_path": "discovery/selection.json",
            "selected_candidate_id": selection.get("selected_candidate_id"),
            "source_mode": "youtube_signal_to_original_fiction",
        }
    write_json(project_dir / "project.json", project)
    write_json(project_dir / "story.json", story)
    print_json({"project_dir": str(project_dir), "next": "story.json을 작성한 뒤 validate를 실행하세요."})


def command_validate(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir).resolve()
    project, story = project_paths(project_dir)
    errors, warnings = validate_story(story)
    if args.render_ready or args.publish_ready or args.final:
        errors.extend(
            approval_errors(project_dir, project, publish_ready=args.publish_ready or args.final)
        )
    if args.render_ready or args.publish_ready or args.final:
        errors.extend(asset_errors(project_dir, story))
    media: dict[str, Any] = {}
    if args.final:
        final_errors, media = final_media_errors(project_dir / "final" / "final.mp4")
        errors.extend(final_errors)
    if not errors:
        set_state(project, "story", "done", "structured story validated")
    else:
        set_state(project, "story", "failed", f"{len(errors)} validation errors")
    save_project(project_dir, project)
    result = {"ok": not errors, "errors": errors, "warnings": warnings}
    if media:
        result["media"] = media
    print_json(result)
    if errors:
        raise SeniorShortsError("검증에 실패했습니다.")


def command_approve(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir).resolve()
    project, story = project_paths(project_dir)
    selected = [args.script, args.character, args.synthetic_disclosure, args.draft_review]
    if not any(selected):
        raise SeniorShortsError("기록할 승인 옵션을 하나 이상 지정하세요.")
    approvals = project.setdefault("approvals", {})
    if args.script:
        errors, _ = validate_story(story)
        if errors:
            raise SeniorShortsError("대본 검증을 통과한 뒤 승인할 수 있습니다: " + " / ".join(errors))
        approvals["script_reviewed"] = True
        approvals["script_reviewed_at"] = now_iso()
        approvals["script_sha256"] = sha256_file(project_dir / "story.json")
    if args.character:
        require_approval(
            project_dir, project, "script_reviewed", "대본 승인 후 캐릭터를 승인할 수 있습니다."
        )
        character_image = expected_image(project_dir, 1)
        if not character_image:
            raise SeniorShortsError("첫 캐릭터 이미지 images/scene01.*가 필요합니다.")
        approvals["character_reviewed"] = True
        approvals["character_reviewed_at"] = now_iso()
        approvals["character_image_sha256"] = sha256_file(character_image)
    if args.synthetic_disclosure:
        require_approval(
            project_dir,
            project,
            "script_reviewed",
            "대본 승인 후 합성·창작 고지를 승인할 수 있습니다.",
        )
        require_approval(
            project_dir,
            project,
            "character_reviewed",
            "캐릭터 승인 후 합성·창작 고지를 승인할 수 있습니다.",
        )
        if not clean(project.get("disclosure_text")):
            raise SeniorShortsError("project.json disclosure_text가 필요합니다.")
        approvals["synthetic_disclosure_reviewed"] = True
        approvals["synthetic_disclosure_reviewed_at"] = now_iso()
        approvals["disclosure_text"] = clean(project.get("disclosure_text"))
    if args.draft_review:
        pending = approval_errors(project_dir, project)
        if pending:
            raise SeniorShortsError(pending[0])
        draft = project_dir / "final" / "review.mp4"
        if not draft.is_file():
            raise SeniorShortsError("검토본 final/review.mp4가 필요합니다.")
        approvals["draft_reviewed"] = True
        approvals["draft_reviewed_at"] = now_iso()
        approvals["draft_sha256"] = sha256_file(draft)
    save_project(project_dir, project)
    print_json({"approvals": approvals})


def character_prompt(character: dict[str, Any]) -> str:
    return ", ".join(
        clean(character.get(field))
        for field in ("name", "age", "gender", "appearance", "hair", "clothes", "personality")
        if clean(character.get(field))
    )


def command_image_prompts(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir).resolve()
    project, story = project_paths(project_dir)
    require_approval(
        project_dir, project, "script_reviewed", "대본 승인 후 이미지 프롬프트를 만들 수 있습니다."
    )
    errors, _ = validate_story(story)
    if errors:
        raise SeniorShortsError("대본 검증에 실패했습니다: " + " / ".join(errors))
    presets = read_json(STYLE_PRESETS)
    style_id = clean(project.get("style_id"))
    style = presets.get(style_id)
    if not isinstance(style, dict):
        raise SeniorShortsError(f"스타일 프리셋을 찾을 수 없습니다: {style_id}")
    characters = {clean(item.get("id")): item for item in story["characters"]}
    prompts: list[dict[str, Any]] = []
    for scene in story["scenes"]:
        scene_characters = [
            character_prompt(characters[character_id])
            for character_id in scene.get("characters") or []
            if character_id in characters
        ]
        positive = ", ".join(
            item
            for item in (
                clean(style.get("prompt")),
                "9:16 portrait frame, keep lower-center subtitle safe area uncluttered",
                "; ".join(scene_characters),
                clean(scene.get("visual_prompt")),
            )
            if item
        )
        number = int(scene["scene"])
        prompts.append(
            {
                "scene": number,
                "positive_prompt": positive,
                "negative_prompt": clean(style.get("negative_prompt")),
                "seed": 2026082800 + number,
                "output_path": f"images/scene{number:02d}.png",
            }
        )
    payload = {
        "schema_version": 1,
        "style_id": style_id,
        "story_sha256": sha256_file(project_dir / "story.json"),
        "prompts": prompts,
    }
    write_json(project_dir / "image-prompts.json", payload)
    set_state(project, "image_prompts", "done", "8 scene prompts generated")
    save_project(project_dir, project)
    print_json({"output": str(project_dir / "image-prompts.json"), "count": len(prompts)})


def request_json(
    url: str, *, payload: dict[str, Any] | None = None, timeout: float = 10
) -> dict[str, Any]:
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = Request(url, data=data, headers=headers, method="POST" if data is not None else "GET")
    try:
        with urlopen(request, timeout=timeout) as response:
            body = response.read()
    except (HTTPError, URLError, TimeoutError) as exc:
        raise SeniorShortsError(f"ComfyUI 요청 실패: {url}: {exc}") from exc
    try:
        result = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SeniorShortsError(f"ComfyUI JSON 응답을 읽을 수 없습니다: {url}") from exc
    if not isinstance(result, dict):
        raise SeniorShortsError(f"ComfyUI 응답 형식이 올바르지 않습니다: {url}")
    return result


def request_bytes(url: str, timeout: float = 30) -> bytes:
    try:
        with urlopen(Request(url, headers={"Accept": "image/*"}), timeout=timeout) as response:
            return response.read()
    except (HTTPError, URLError, TimeoutError) as exc:
        raise SeniorShortsError(f"ComfyUI 이미지 요청 실패: {url}: {exc}") from exc


def workflow_node(workflow: dict[str, Any], node_id: str) -> dict[str, Any]:
    node = workflow.get(str(node_id))
    if not isinstance(node, dict) or not isinstance(node.get("inputs"), dict):
        raise SeniorShortsError(f"ComfyUI workflow 노드를 찾을 수 없습니다: {node_id}")
    return node


def render_comfy_scene(args: argparse.Namespace, prompt: dict[str, Any], output: Path) -> None:
    workflow = copy.deepcopy(read_json(Path(args.workflow).resolve()))
    workflow_node(workflow, args.prompt_node)["inputs"][args.prompt_input] = prompt["positive_prompt"]
    if args.negative_node:
        workflow_node(workflow, args.negative_node)["inputs"][args.negative_input] = prompt["negative_prompt"]
    if args.seed_node:
        workflow_node(workflow, args.seed_node)["inputs"][args.seed_input] = int(prompt["seed"])
    base_url = args.url.rstrip("/")
    queued = request_json(
        f"{base_url}/prompt",
        payload={"prompt": workflow, "client_id": str(uuid.uuid4())},
        timeout=15,
    )
    prompt_id = clean(queued.get("prompt_id"))
    if not prompt_id:
        raise SeniorShortsError(f"ComfyUI prompt_id가 없습니다: {queued}")
    deadline = time.monotonic() + args.timeout
    history_entry: dict[str, Any] | None = None
    while time.monotonic() < deadline:
        history = request_json(f"{base_url}/history/{prompt_id}", timeout=10)
        candidate = history.get(prompt_id)
        if isinstance(candidate, dict):
            history_entry = candidate
            break
        time.sleep(1)
    if history_entry is None:
        raise SeniorShortsError(f"ComfyUI 생성 시간이 {args.timeout}초를 초과했습니다: {prompt_id}")
    outputs = history_entry.get("outputs") or {}
    node_output = outputs.get(str(args.output_node))
    if not isinstance(node_output, dict):
        raise SeniorShortsError(f"ComfyUI 출력 노드를 찾을 수 없습니다: {args.output_node}")
    images = node_output.get("images")
    if not isinstance(images, list) or not images:
        raise SeniorShortsError(f"ComfyUI 출력 이미지가 없습니다: {args.output_node}")
    image = images[0]
    query = urlencode(
        {
            "filename": image.get("filename") or "",
            "subfolder": image.get("subfolder") or "",
            "type": image.get("type") or "output",
        }
    )
    content = request_bytes(f"{base_url}/view?{query}", timeout=30)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(content)


def command_comfyui(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir).resolve()
    project, story = project_paths(project_dir)
    require_approval(project_dir, project, "script_reviewed", "대본 승인 후 이미지를 생성할 수 있습니다.")
    if args.all:
        require_approval(
            project_dir,
            project,
            "character_reviewed",
            "첫 캐릭터 이미지 승인 후 전체 장면을 생성할 수 있습니다.",
        )
    prompts_payload = read_json(project_dir / "image-prompts.json")
    if prompts_payload.get("story_sha256") != sha256_file(project_dir / "story.json"):
        raise SeniorShortsError("이미지 프롬프트가 현재 story.json과 다릅니다. image-prompts를 다시 실행하세요.")
    prompts = prompts_payload.get("prompts") or []
    if args.all:
        selected = [
            item
            for item in prompts
            if args.overwrite or not expected_image(project_dir, int(item.get("scene") or 0))
        ]
    else:
        selected = [item for item in prompts if item.get("scene") == args.scene]
    if not selected:
        if args.all:
            set_state(project, "images", "done", "all scene images ready")
            save_project(project_dir, project)
            print_json({"generated": [], "missing": [], "detail": "모든 장면 이미지가 이미 있습니다."})
            return
        raise SeniorShortsError("생성할 장면 프롬프트를 찾을 수 없습니다.")
    for prompt in selected:
        number = int(prompt["scene"])
        output = project_dir / "images" / f"scene{number:02d}.png"
        if output.exists() and not args.overwrite:
            raise SeniorShortsError(f"기존 이미지는 --overwrite 없이 덮어쓸 수 없습니다: {output}")
        render_comfy_scene(args, prompt, output)
    missing = [number for number in range(1, 9) if not expected_image(project_dir, number)]
    set_state(
        project,
        "images",
        "done" if not missing else "pending",
        "all scene images ready" if not missing else f"missing scenes: {missing}",
    )
    save_project(project_dir, project)
    print_json({"generated": [item["scene"] for item in selected], "missing": missing})


def audio_duration(path: Path) -> float:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        raise SeniorShortsError("음성 길이 확인에는 ffprobe가 필요합니다.")
    completed = run(
        [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ]
    )
    try:
        return float(completed.stdout.strip())
    except ValueError as exc:
        raise SeniorShortsError(f"음성 길이를 읽을 수 없습니다: {path}") from exc


def available_macos_voice(requested: str) -> str:
    say = shutil.which("say")
    if not say:
        raise SeniorShortsError("macOS say 명령을 찾을 수 없습니다.")
    voices = run([say, "-v", "?"]).stdout.splitlines()
    names = [line.split()[0] for line in voices if line.strip()]
    if requested:
        if requested not in names:
            raise SeniorShortsError(f"macOS 음성을 찾을 수 없습니다: {requested}")
        return requested
    if "Yuna" in names:
        return "Yuna"
    for line in voices:
        if "ko_KR" in line or "ko-KR" in line:
            return line.split()[0]
    return ""


def source_audio(source_dir: Path, number: int) -> Path | None:
    base = source_dir / f"scene{number:02d}"
    return next((base.with_suffix(ext) for ext in AUDIO_EXTENSIONS if base.with_suffix(ext).is_file()), None)


def command_voice(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir).resolve()
    project, story = project_paths(project_dir)
    require_approval(project_dir, project, "script_reviewed", "대본 승인 후 음성을 만들 수 있습니다.")
    require_approval(project_dir, project, "character_reviewed", "캐릭터 승인 후 음성을 만들 수 있습니다.")
    require_approval(
        project_dir,
        project,
        "synthetic_disclosure_reviewed",
        "합성·창작 고지 승인 후 음성을 만들 수 있습니다.",
    )
    errors, _ = validate_story(story)
    if errors:
        raise SeniorShortsError("대본 검증에 실패했습니다: " + " / ".join(errors))
    source_dir = Path(args.source_dir).resolve() if args.source_dir else None
    if args.provider == "files" and source_dir is None:
        raise SeniorShortsError("provider=files에는 --source-dir가 필요합니다.")
    voice = available_macos_voice(args.voice) if args.provider == "macos" else ""
    say = shutil.which("say") or "say"
    manifest: list[dict[str, Any]] = []
    cursor = 0.0
    for scene in story["scenes"]:
        number = int(scene["scene"])
        if args.provider == "macos":
            output = project_dir / "audio" / f"scene{number:02d}.aiff"
            if output.exists() and not args.overwrite:
                raise SeniorShortsError(f"기존 음성은 --overwrite 없이 덮어쓸 수 없습니다: {output}")
            command = [say]
            if voice:
                command.extend(["-v", voice])
            command.extend(["-r", str(args.rate), "-o", str(output), clean(scene.get("narration"))])
            run(command)
        else:
            assert source_dir is not None
            source = source_audio(source_dir, number)
            if source is None:
                raise SeniorShortsError(f"장면 음성을 찾을 수 없습니다: {source_dir}/scene{number:02d}.*")
            output = project_dir / "audio" / f"scene{number:02d}{source.suffix.lower()}"
            if output.exists() and not args.overwrite:
                raise SeniorShortsError(f"기존 음성은 --overwrite 없이 덮어쓸 수 없습니다: {output}")
            shutil.copy2(source, output)
        measured = audio_duration(output)
        timeline_duration = max(float(scene["duration"]), measured + 0.35)
        manifest.append(
            {
                "scene": number,
                "path": str(output.relative_to(project_dir)),
                "audio_duration": round(measured, 3),
                "timeline_start": round(cursor, 3),
                "timeline_duration": round(timeline_duration, 3),
            }
        )
        cursor += timeline_duration
    audio_manifest = {
        "schema_version": 1,
        "story_sha256": sha256_file(project_dir / "story.json"),
        "provider": args.provider,
        "voice": voice,
        "rate": args.rate if args.provider == "macos" else None,
        "duration": round(cursor, 3),
        "scenes": manifest,
    }
    write_json(project_dir / "audio" / "audio-manifest.json", audio_manifest)
    set_state(project, "voice", "done", f"{args.provider}, {cursor:.3f}s")
    save_project(project_dir, project)
    print_json(audio_manifest)


def ass_timestamp(seconds: float) -> str:
    centiseconds = max(0, int(round(seconds * 100)))
    hours, remainder = divmod(centiseconds, 360000)
    minutes, remainder = divmod(remainder, 6000)
    secs, cs = divmod(remainder, 100)
    return f"{hours}:{minutes:02d}:{secs:02d}.{cs:02d}"


def ass_escape(text: str, highlights: list[str]) -> str:
    escaped = text.replace("\\", r"\\").replace("{", r"\{").replace("}", r"\}")
    escaped = escaped.replace("\n", r"\N")
    for word in sorted((clean(item) for item in highlights if clean(item)), key=len, reverse=True):
        escaped = escaped.replace(
            word,
            r"{\c&H0000E6FF&}" + word + r"{\c&H00FFFFFF&}",
        )
    return escaped


def command_subtitle(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir).resolve()
    project, story = project_paths(project_dir)
    manifest = read_json(project_dir / "audio" / "audio-manifest.json")
    if manifest.get("story_sha256") != sha256_file(project_dir / "story.json"):
        raise SeniorShortsError("음성이 현재 story.json과 다릅니다. voice를 다시 실행하세요.")
    timeline = {int(item["scene"]): item for item in manifest.get("scenes") or []}
    presets = read_json(STYLE_PRESETS)
    style = presets.get(clean(project.get("style_id"))) or {}
    font = clean(style.get("font")) or "Apple SD Gothic Neo"
    font_size = int(style.get("subtitle_font_size") or 86)
    margin_v = int(style.get("subtitle_margin_v") or 330)
    events: list[dict[str, Any]] = []
    ass_lines = [
        "[Script Info]",
        "ScriptType: v4.00+",
        "PlayResX: 1080",
        "PlayResY: 1920",
        "ScaledBorderAndShadow: yes",
        "WrapStyle: 2",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        f"Style: Senior,{font},{font_size},&H00FFFFFF,&H0000E6FF,&H00000000,&H78000000,-1,0,0,0,100,100,0,0,1,6,1,2,70,70,{margin_v},1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    for scene in story["scenes"]:
        number = int(scene["scene"])
        item = timeline.get(number)
        if not item:
            raise SeniorShortsError(f"Scene {number} 음성 타임라인이 없습니다.")
        start = float(item["timeline_start"])
        end = start + float(item["timeline_duration"])
        text = str(scene.get("subtitle") or "").strip()
        highlights = scene.get("highlight") or []
        events.append(
            {
                "scene": number,
                "start": round(start, 3),
                "end": round(end, 3),
                "text": text,
                "highlight": highlights,
                "effect": "emphasis" if highlights else "none",
            }
        )
        ass_lines.append(
            "Dialogue: 0,"
            f"{ass_timestamp(start)},{ass_timestamp(end)},Senior,,0,0,0,,"
            r"{\fad(120,120)}"
            + ass_escape(text, highlights)
        )
    audio_manifest_path = project_dir / "audio" / "audio-manifest.json"
    write_json(
        project_dir / "subtitles" / "subtitle.json",
        {
            "schema_version": 1,
            "story_sha256": sha256_file(project_dir / "story.json"),
            "audio_manifest_sha256": sha256_file(audio_manifest_path),
            "events": events,
        },
    )
    ass_path = project_dir / "subtitles" / "subtitle.ass"
    ass_path.write_text("\n".join(ass_lines) + "\n", encoding="utf-8")
    set_state(project, "subtitles", "done", f"{len(events)} events")
    save_project(project_dir, project)
    print_json({"json": str(project_dir / "subtitles" / "subtitle.json"), "ass": str(ass_path)})


def motion_filter(motion: str, duration: float) -> str:
    base = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920"
    if motion == "static":
        return base + ",fps=30,format=yuv420p"
    frames = max(2, int(round(duration * 30)))
    progress = f"on/{frames - 1}"
    zoom = "1.08"
    x = "iw/2-(iw/zoom/2)"
    y = "ih/2-(ih/zoom/2)"
    if motion in {"slow_zoom_in", "zoom_face"}:
        zoom = f"min(1+0.08*{progress},1.08)"
    elif motion == "slow_zoom_out":
        zoom = f"max(1.08-0.08*{progress},1.0)"
    elif motion == "pan_left":
        x = f"(iw-iw/zoom)*(1-{progress})"
    elif motion == "pan_right":
        x = f"(iw-iw/zoom)*{progress}"
    elif motion == "pan_up":
        y = f"(ih-ih/zoom)*(1-{progress})"
    elif motion == "pan_down":
        y = f"(ih-ih/zoom)*{progress}"
    return (
        base
        + f",zoompan=z='{zoom}':x='{x}':y='{y}':d=1:s=1080x1920:fps=30,format=yuv420p"
    )


def ffconcat_quote(path: Path) -> str:
    return str(path.resolve()).replace("'", "'\\''")


def filter_path(path: Path) -> str:
    return str(path.resolve()).replace("\\", "\\\\").replace(":", r"\:").replace("'", r"\'")


def ffmpeg_has_filter(ffmpeg: str, filter_name: str) -> bool:
    completed = subprocess.run(
        [ffmpeg, "-hide_banner", "-filters"],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    return completed.returncode == 0 and bool(
        re.search(rf"\b{re.escape(filter_name)}\s+", completed.stdout)
    )


def draw_caption_line(
    draw: Any,
    line: str,
    y: float,
    font: Any,
    highlights: list[str],
) -> None:
    width = float(draw.textlength(line, font=font))
    x = (1080 - width) / 2
    draw.text(
        (x, y),
        line,
        font=font,
        fill=(255, 255, 255, 255),
        stroke_width=6,
        stroke_fill=(0, 0, 0, 255),
    )
    for word in (clean(item) for item in highlights if clean(item)):
        start = 0
        while True:
            index = line.find(word, start)
            if index < 0:
                break
            word_x = x + float(draw.textlength(line[:index], font=font))
            draw.text(
                (word_x, y),
                word,
                font=font,
                fill=(255, 230, 0, 255),
                stroke_width=6,
                stroke_fill=(0, 0, 0, 255),
            )
            start = index + len(word)


def create_caption_overlay(
    project_dir: Path,
    project: dict[str, Any],
    scene: dict[str, Any],
    *,
    draft: bool,
) -> Path:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as exc:
        raise SeniorShortsError(
            "현재 FFmpeg에 ass 필터가 없어 Pillow 자막 fallback이 필요합니다."
        ) from exc
    font_path = next((path for path in FONT_CANDIDATES if path.is_file()), None)
    if font_path is None:
        raise SeniorShortsError("Pillow 자막 합성에 사용할 한글 폰트를 찾을 수 없습니다.")
    presets = read_json(STYLE_PRESETS)
    style = presets.get(clean(project.get("style_id"))) or {}
    font_size = int(style.get("subtitle_font_size") or 86)
    margin_v = int(style.get("subtitle_margin_v") or 330)
    font = ImageFont.truetype(str(font_path), font_size)
    overlay = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    lines = str(scene.get("subtitle") or "").strip().splitlines()
    if not lines:
        raise SeniorShortsError(f"Scene {scene.get('scene')} subtitle이 비어 있습니다.")
    line_gap = 18
    line_heights = [
        max(1, draw.textbbox((0, 0), line, font=font, stroke_width=6)[3]) for line in lines
    ]
    total_height = sum(line_heights) + line_gap * max(0, len(lines) - 1)
    y = 1920 - margin_v - total_height
    max_width = max(float(draw.textlength(line, font=font)) for line in lines)
    box_left = max(40, int((1080 - max_width) / 2) - 34)
    box_right = min(1040, int((1080 + max_width) / 2) + 34)
    draw.rounded_rectangle(
        (box_left, int(y) - 22, box_right, int(y + total_height) + 22),
        radius=24,
        fill=(0, 0, 0, 96),
    )
    highlights = scene.get("highlight") or []
    for line, line_height in zip(lines, line_heights):
        draw_caption_line(draw, line, y, font, highlights)
        y += line_height + line_gap
    if draft:
        review_font = ImageFont.truetype(str(font_path), 30)
        label = "LOCAL REVIEW"
        bbox = draw.textbbox((0, 0), label, font=review_font)
        label_width = bbox[2] - bbox[0]
        label_height = bbox[3] - bbox[1]
        x = 1080 - label_width - 42
        y = 36
        draw.rounded_rectangle(
            (x - 16, y - 10, x + label_width + 16, y + label_height + 14),
            radius=10,
            fill=(0, 0, 0, 110),
        )
        draw.text((x, y), label, font=review_font, fill=(255, 255, 255, 210))
    output = project_dir / "video" / "captions" / f"scene{int(scene['scene']):02d}.png"
    output.parent.mkdir(parents=True, exist_ok=True)
    overlay.save(output)
    return output


def render_scene(
    ffmpeg: str,
    image: Path,
    audio: Path,
    output: Path,
    motion: str,
    duration: float,
    overwrite: bool,
    caption_overlay: Path | None = None,
) -> None:
    if output.exists() and not overwrite:
        raise SeniorShortsError(f"기존 장면 영상은 --overwrite 없이 덮어쓸 수 없습니다: {output}")
    command = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y" if overwrite else "-n"]
    command.extend(["-loop", "1", "-framerate", "30", "-i", str(image), "-i", str(audio)])
    if caption_overlay is not None:
        command.extend(
            [
                "-loop",
                "1",
                "-framerate",
                "30",
                "-i",
                str(caption_overlay),
                "-filter_complex",
                f"[0:v]{motion_filter(motion, duration)}[base];"
                "[base][2:v]overlay=0:0:format=auto[v]",
                "-map",
                "[v]",
                "-map",
                "1:a:0",
            ]
        )
    else:
        command.extend(["-vf", motion_filter(motion, duration)])
    command.extend(
        [
            "-af",
            f"apad,atrim=0:{duration:.3f}",
            "-t",
            f"{duration:.3f}",
            "-r",
            "30",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "20",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-ar",
            "48000",
            "-ac",
            "2",
            "-movflags",
            "+faststart",
            str(output),
        ]
    )
    run(command)


def command_render(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir).resolve()
    project, story = project_paths(project_dir)
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise SeniorShortsError("렌더링에는 ffmpeg가 필요합니다.")
    if not 0 <= args.bgm_volume <= 1:
        raise SeniorShortsError("bgm-volume은 0~1 범위여야 합니다.")
    story_errors, _ = validate_story(story)
    errors = story_errors + approval_errors(project_dir, project, publish_ready=args.final)
    errors.extend(asset_errors(project_dir, story))
    if errors:
        raise SeniorShortsError("렌더 준비 검증에 실패했습니다: " + " / ".join(errors))
    manifest = read_json(project_dir / "audio" / "audio-manifest.json")
    timeline = {int(item["scene"]): item for item in manifest.get("scenes") or []}
    libass_ready = ffmpeg_has_filter(ffmpeg, "ass") and (
        args.final or ffmpeg_has_filter(ffmpeg, "drawtext")
    )
    subtitle_renderer = "libass" if libass_ready else "pillow-overlay"
    caption_overlays: dict[int, Path] = {}
    if not libass_ready:
        if not ffmpeg_has_filter(ffmpeg, "overlay"):
            raise SeniorShortsError(
                "현재 FFmpeg에 ass와 overlay 필터가 모두 없어 자막을 합성할 수 없습니다."
            )
        caption_overlays = {
            int(scene["scene"]): create_caption_overlay(
                project_dir, project, scene, draft=not args.final
            )
            for scene in story["scenes"]
        }
    clips: list[Path] = []
    for scene in story["scenes"]:
        number = int(scene["scene"])
        image = expected_image(project_dir, number)
        audio = expected_audio(project_dir, number)
        assert image is not None and audio is not None
        duration = float(timeline[number]["timeline_duration"])
        clip = project_dir / "video" / f"scene{number:02d}.mp4"
        render_scene(
            ffmpeg,
            image,
            audio,
            clip,
            clean(scene.get("motion")),
            duration,
            args.overwrite,
            caption_overlays.get(number),
        )
        clips.append(clip)
    concat_file = project_dir / "video" / "scenes.ffconcat"
    concat_file.write_text(
        "ffconcat version 1.0\n" + "".join(f"file '{ffconcat_quote(path)}'\n" for path in clips),
        encoding="utf-8",
    )
    combined = project_dir / "video" / "combined.mp4"
    if combined.exists() and not args.overwrite:
        raise SeniorShortsError(f"기존 합본은 --overwrite 없이 덮어쓸 수 없습니다: {combined}")
    run(
        [
            ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-y" if args.overwrite else "-n",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_file),
            "-c",
            "copy",
            str(combined),
        ]
    )
    output = project_dir / "final" / ("final.mp4" if args.final else "review.mp4")
    if output.exists() and not args.overwrite:
        raise SeniorShortsError(f"기존 출력은 --overwrite 없이 덮어쓸 수 없습니다: {output}")
    ass_filter = ""
    if libass_ready:
        ass_filter = f"ass=filename='{filter_path(project_dir / 'subtitles' / 'subtitle.ass')}'"
        if not args.final:
            ass_filter += ",drawtext=text='LOCAL REVIEW':fontcolor=white@0.75:fontsize=30:x=w-tw-40:y=40:box=1:boxcolor=black@0.35"
    command = [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y" if args.overwrite else "-n",
        "-i",
        str(combined),
    ]
    total_duration = float(manifest.get("duration") or 0)
    if args.bgm:
        bgm = Path(args.bgm).resolve()
        if not bgm.is_file():
            raise SeniorShortsError(f"BGM 파일을 찾을 수 없습니다: {bgm}")
        fade_start = max(0.0, total_duration - 1.0)
        command.extend(["-stream_loop", "-1", "-i", str(bgm)])
        if libass_ready:
            command.extend(
                [
                    "-filter_complex",
                    f"[0:v]{ass_filter}[v];"
                    f"[0:a]volume=1.0[a0];"
                    f"[1:a]volume={args.bgm_volume:.3f},atrim=0:{total_duration:.3f},"
                    f"afade=t=out:st={fade_start:.3f}:d=1[a1];"
                    "[a0][a1]amix=inputs=2:duration=first:dropout_transition=0[a]",
                    "-map",
                    "[v]",
                    "-map",
                    "[a]",
                ]
            )
        else:
            command.extend(
                [
                    "-filter_complex",
                    f"[0:a]volume=1.0[a0];"
                    f"[1:a]volume={args.bgm_volume:.3f},atrim=0:{total_duration:.3f},"
                    f"afade=t=out:st={fade_start:.3f}:d=1[a1];"
                    "[a0][a1]amix=inputs=2:duration=first:dropout_transition=0[a]",
                    "-map",
                    "0:v:0",
                    "-map",
                    "[a]",
                ]
            )
    else:
        if libass_ready:
            command.extend(["-vf", ass_filter])
        command.extend(["-map", "0:v:0", "-map", "0:a:0"])
    command.extend(
        [
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "20",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
            "-shortest",
            str(output),
        ]
    )
    run(command)
    final_errors, report = final_media_errors(output)
    if final_errors:
        raise SeniorShortsError("렌더 결과 검사에 실패했습니다: " + " / ".join(final_errors))
    report_payload = {
        "schema_version": 1,
        "mode": "final" if args.final else "draft",
        "output": str(output.relative_to(project_dir)),
        "created_at": now_iso(),
        "subtitle_renderer": subtitle_renderer,
        "ffprobe": report,
        "limits": {
            "local_media_validated": True,
            "uploaded": False,
            "platform_approval_proven": False,
            "monetization_proven": False,
        },
    }
    write_json(project_dir / "final" / "render-report.json", report_payload)
    set_state(project, "render", "done", report_payload["mode"])
    save_project(project_dir, project)
    print_json({"output": str(output), "report": str(project_dir / "final" / "render-report.json")})


def command_status(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir).resolve()
    project, story = project_paths(project_dir)
    images = [number for number in range(1, 9) if expected_image(project_dir, number)]
    audio = [number for number in range(1, 9) if expected_audio(project_dir, number)]
    print_json(
        {
            "project_dir": str(project_dir),
            "topic": project.get("topic"),
            "title": story.get("title"),
            "states": project.get("states"),
            "approvals": project.get("approvals"),
            "images": images,
            "audio": audio,
            "review": (project_dir / "final" / "review.mp4").is_file(),
            "final": (project_dir / "final" / "final.mp4").is_file(),
        }
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor = subparsers.add_parser("doctor", help="현재 로컬 렌더·소재 발굴 환경을 확인합니다.")
    doctor.add_argument("--comfyui-url", default="")
    doctor.add_argument("--check-youtube", action="store_true")
    doctor.add_argument("--json", action="store_true")
    doctor.set_defaults(func=command_doctor)

    configure_youtube = subparsers.add_parser(
        "configure-youtube", help="YouTube Data API 키를 macOS 키체인에 저장합니다."
    )
    configure_youtube.set_defaults(func=command_configure_youtube)

    discover = subparsers.add_parser(
        "discover", help="YouTube 공개 메타데이터에서 시니어 사연 소재 신호를 수집합니다."
    )
    discover.add_argument("--query", action="append", help="반복 지정할 수 있습니다.")
    discover.add_argument("--days", type=int, default=90)
    discover.add_argument("--per-query", type=int, default=10)
    discover.add_argument("--max-signals", type=int, default=30)
    discover.add_argument("--max-duration", type=int, default=180)
    discover.add_argument("--output")
    discover.set_defaults(func=command_discover)

    select = subparsers.add_parser("select", help="사용자가 선택한 창작 소재 후보를 기록합니다.")
    select.add_argument("--candidates", required=True)
    select.add_argument("--candidate-id", required=True)
    select.add_argument("--output")
    select.set_defaults(func=command_select)

    init = subparsers.add_parser("init", help="새 Phase 1 프로젝트를 만듭니다.")
    init_source = init.add_mutually_exclusive_group(required=True)
    init_source.add_argument("--topic")
    init_source.add_argument("--selection")
    init.add_argument("--project-dir", required=True)
    init.add_argument("--target-age", default="55-75")
    init.add_argument("--duration", type=int, default=55)
    init.set_defaults(func=command_init)

    validate = subparsers.add_parser("validate", help="대본, 자산, 최종 미디어를 검사합니다.")
    validate.add_argument("--project-dir", required=True)
    level = validate.add_mutually_exclusive_group()
    level.add_argument("--render-ready", action="store_true")
    level.add_argument("--publish-ready", action="store_true")
    level.add_argument("--final", action="store_true")
    validate.set_defaults(func=command_validate)

    approve = subparsers.add_parser("approve", help="사용자 검토 승인을 기록합니다.")
    approve.add_argument("--project-dir", required=True)
    approve.add_argument("--script", action="store_true")
    approve.add_argument("--character", action="store_true")
    approve.add_argument("--synthetic-disclosure", action="store_true")
    approve.add_argument("--draft-review", action="store_true")
    approve.set_defaults(func=command_approve)

    prompts = subparsers.add_parser("image-prompts", help="8개 장면 이미지 프롬프트를 만듭니다.")
    prompts.add_argument("--project-dir", required=True)
    prompts.set_defaults(func=command_image_prompts)

    comfyui = subparsers.add_parser("comfyui", help="실행 중인 ComfyUI API로 장면 이미지를 만듭니다.")
    comfyui.add_argument("--project-dir", required=True)
    comfyui.add_argument("--workflow", required=True)
    comfyui.add_argument("--url", default="http://127.0.0.1:8188")
    comfyui.add_argument("--prompt-node", required=True)
    comfyui.add_argument("--prompt-input", default="text")
    comfyui.add_argument("--negative-node")
    comfyui.add_argument("--negative-input", default="text")
    comfyui.add_argument("--seed-node")
    comfyui.add_argument("--seed-input", default="seed")
    comfyui.add_argument("--output-node", required=True)
    selection = comfyui.add_mutually_exclusive_group(required=True)
    selection.add_argument("--scene", type=int, choices=range(1, 9))
    selection.add_argument("--all", action="store_true")
    comfyui.add_argument("--timeout", type=int, default=600)
    comfyui.add_argument("--overwrite", action="store_true")
    comfyui.set_defaults(func=command_comfyui)

    voice = subparsers.add_parser("voice", help="장면별 음성을 생성하거나 가져옵니다.")
    voice.add_argument("--project-dir", required=True)
    voice.add_argument("--provider", choices=("macos", "files"), default="macos")
    voice.add_argument("--voice", default="")
    voice.add_argument("--rate", type=int, default=165)
    voice.add_argument("--source-dir")
    voice.add_argument("--overwrite", action="store_true")
    voice.set_defaults(func=command_voice)

    subtitle = subparsers.add_parser("subtitle", help="JSON과 ASS 자막을 만듭니다.")
    subtitle.add_argument("--project-dir", required=True)
    subtitle.set_defaults(func=command_subtitle)

    render = subparsers.add_parser("render", help="Pan/Zoom 검토본 또는 최종본을 렌더합니다.")
    render.add_argument("--project-dir", required=True)
    mode = render.add_mutually_exclusive_group(required=True)
    mode.add_argument("--draft", action="store_true")
    mode.add_argument("--final", action="store_true")
    render.add_argument("--bgm")
    render.add_argument("--bgm-volume", type=float, default=0.12)
    render.add_argument("--overwrite", action="store_true")
    render.set_defaults(func=command_render)

    status = subparsers.add_parser("status", help="프로젝트 단계와 승인 상태를 확인합니다.")
    status.add_argument("--project-dir", required=True)
    status.set_defaults(func=command_status)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except SeniorShortsError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
