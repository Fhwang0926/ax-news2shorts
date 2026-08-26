#!/usr/bin/env python3
"""Evidence-gated animal viral Shorts project and local renderer."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import math
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import wave
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from youtube_delivery import (
    CTA_TAIL_SECONDS,
    YouTubeDeliveryError,
    append_cta_tail,
    read_upload_package,
    write_upload_package,
)


PLUGIN_VERSION = "0.5.0+codex.20260825132723"
SCHEMA_VERSION = "2.0"
CANVAS_WIDTH = 720
CANVAS_HEIGHT = 1280
VIDEO_TOP = 264
VIDEO_HEIGHT = 768
FOOTER_TOP = 1032
BOTTOM_SAFE_TOP = 1128
RIGHT_SAFE_WIDTH = 86
TEMPLATE_ID = "animal-viral-card-v1"
LEGACY_VISUAL_PRESET = TEMPLATE_ID
DEFAULT_VISUAL_PRESET = "observation-contrast-v1"
VISUAL_PRESETS = {LEGACY_VISUAL_PRESET, DEFAULT_VISUAL_PRESET}
SUBJECT_LABEL_MAX_CHARS = 12

PLATFORMS = {"tiktok", "youtube_shorts"}
RIGHTS_STATUSES = {
    "owned",
    "licensed",
    "permission_confirmed",
    "public_domain",
    "unknown",
    "review_required",
    "not_permitted",
}
LOCAL_REVIEW_RIGHTS = {"unknown", "review_required"}
MEDIA_SUFFIXES = {".mp4", ".mov", ".mkv", ".webm", ".m4v"}
EMOTION_CONFIDENCE = {"observed", "caregiver_report", "inference"}
MUSIC_MOODS = {"playful", "tension", "tender", "relief", "gentle"}
MUSIC_CUES = {"intro", "build", "steady", "drop", "impact", "release"}
SFX_TYPES = {"question_pop", "soft_whoosh", "bass_drum"}
SOURCE_AUDIO_PRIORITIES = {"high", "normal", "low"}
CAPTION_STYLES = {"question", "buildup", "turn", "payoff"}
NARRATIVE_ACTS = ("setup", "build", "turn", "payoff")
FUN_MECHANISMS = {
    "race-comparison",
    "escalating-wait",
    "delayed-reveal",
    "synchronized-reaction",
    "rule-break",
    "callback",
    "before-after-contrast",
}
MAX_SHORT_SECONDS = 59.5
ACT_DEFAULTS = {
    "setup": {"energy": 0.28, "cue": "intro", "caption_style": "question"},
    "build": {"energy": 0.55, "cue": "build", "caption_style": "buildup"},
    "turn": {"energy": 0.32, "cue": "drop", "caption_style": "turn"},
    "payoff": {"energy": 0.86, "cue": "impact", "caption_style": "payoff"},
}
ACT_MUSIC_CUES = {
    "setup": {"intro", "steady"},
    "build": {"build", "steady"},
    "turn": {"drop", "impact"},
    "payoff": {"impact", "release"},
}
MOOD_BPM = {"playful": 118, "tension": 102, "tender": 84, "relief": 106, "gentle": 88}
SOURCE_AUDIO_DUCK_DB = {"high": 20.0, "normal": 15.0, "low": 12.0}
ARCHETYPE_GUIDES = {
    "comic-reversal": (16.0, 24.0),
    "skill-challenge": (20.0, 35.0),
    "relationship-before-after": (12.0, 20.0),
    "emotional-assist": (18.0, 28.0),
    "pure-behavior-loop": (6.0, 10.0),
}
CANDIDATE_WEIGHTS = {
    "first_frame_hook": 20.0,
    "state_change_density": 20.0,
    "payoff_clarity": 20.0,
    "event_completeness": 15.0,
    "relationship_roles": 10.0,
    "vertical_edit_fit": 10.0,
    "korean_context_fit": 5.0,
}
EVIDENCE_STORY_WEIGHTS = {
    "evidence_grounding": 25.0,
    "first_1_5s_hook": 20.0,
    "state_change_density": 20.0,
    "payoff_clarity": 15.0,
    "relationship_roles": 10.0,
    "loopability": 10.0,
}
FUN_STORY_WEIGHTS = {
    "hook_curiosity": 15.0,
    "build_escalation": 20.0,
    "rehook_strength": 15.0,
    "turn_surprise": 20.0,
    "payoff_satisfaction": 20.0,
    "replay_comment_potential": 10.0,
}
PENALTIES = {
    "explanation_over_5s": 10.0,
    "static_over_10s": 15.0,
    "text_translation_only": 10.0,
}
HARD_REJECTIONS = {"missing_resolution", "near_full_reupload"}
CLICKBAIT = ("충격", "소름", "눈물주의", "대박", "역대급")
SENSITIVE_CATEGORIES = {"rescue", "illness", "abuse", "injury", "death", "treatment"}
FONT_CANDIDATES = (
    Path("/System/Library/Fonts/AppleSDGothicNeo.ttc"),
    Path("/System/Library/Fonts/Supplemental/AppleGothic.ttf"),
    Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
    Path("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"),
)


class AnimalViralShortsError(RuntimeError):
    """Expected user-facing error."""


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def clean_text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def fail(message: str) -> None:
    raise AnimalViralShortsError(message)


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise AnimalViralShortsError(f"필수 파일이 없습니다: {path}") from exc
    except json.JSONDecodeError as exc:
        raise AnimalViralShortsError(f"JSON 형식이 올바르지 않습니다: {path}: {exc}") from exc


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def ensure_new(paths: list[Path], overwrite: bool = False) -> None:
    existing = [str(path) for path in paths if path.exists()]
    if existing and not overwrite:
        fail("기존 결과를 교체하려면 --overwrite가 필요합니다: " + ", ".join(existing))


def require_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        fail(f"{label}은(는) JSON 객체여야 합니다.")
    return value


def require_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        fail(f"{label}은(는) 배열이어야 합니다.")
    return value


def require_text(value: Any, label: str, minimum: int = 1) -> str:
    result = clean_text(value)
    if len(result) < minimum:
        fail(f"{label}은(는) {minimum}자 이상이어야 합니다.")
    return result


def require_number(
    value: Any,
    label: str,
    minimum: float | None = None,
    maximum: float | None = None,
) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        fail(f"{label}은(는) 숫자여야 합니다.")
    result = float(value)
    if minimum is not None and result < minimum:
        fail(f"{label}은(는) {minimum} 이상이어야 합니다.")
    if maximum is not None and result > maximum:
        fail(f"{label}은(는) {maximum} 이하여야 합니다.")
    return result


def require_bool(value: Any, label: str) -> bool:
    if not isinstance(value, bool):
        fail(f"{label}은(는) true 또는 false여야 합니다.")
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_project_path(project_dir: Path, relative: str, *, exists: bool = False) -> Path:
    candidate = (project_dir / relative).resolve()
    root = project_dir.resolve()
    if candidate != root and root not in candidate.parents:
        fail(f"프로젝트 밖 경로는 사용할 수 없습니다: {relative}")
    if exists and not candidate.exists():
        fail(f"프로젝트 파일이 없습니다: {relative}")
    return candidate


def relative_path(project_dir: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(project_dir.resolve()).as_posix()
    except ValueError as exc:
        raise AnimalViralShortsError(f"프로젝트 밖 파일은 등록할 수 없습니다: {path}") from exc


def run_checked(command: list[str], label: str, timeout: int = 600) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            command,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
    except FileNotFoundError as exc:
        raise AnimalViralShortsError(f"{label} 실행 파일을 찾지 못했습니다.") from exc
    except subprocess.TimeoutExpired as exc:
        raise AnimalViralShortsError(f"{label} 시간이 초과되었습니다.") from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or "").strip()
        raise AnimalViralShortsError(f"{label} 실패: {detail[-2000:]}") from exc


def probe_media(path: Path) -> dict[str, Any]:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        fail("ffprobe가 필요합니다.")
    result = run_checked(
        [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "format=duration,size,bit_rate,format_name:"
            "stream=index,codec_type,codec_name,width,height,r_frame_rate,sample_rate,channels",
            "-of",
            "json",
            str(path),
        ],
        "FFprobe",
        timeout=60,
    )
    payload = require_object(json.loads(result.stdout), "ffprobe")
    streams = require_list(payload.get("streams", []), "ffprobe.streams")
    video = next((item for item in streams if item.get("codec_type") == "video"), {})
    audio = next((item for item in streams if item.get("codec_type") == "audio"), {})
    media_format = require_object(payload.get("format", {}), "ffprobe.format")
    duration = float(media_format.get("duration") or 0)
    if not video or duration <= 0:
        fail(f"유효한 영상 스트림을 확인하지 못했습니다: {path}")
    frame_rate = clean_text(video.get("r_frame_rate"))
    fps = 0.0
    if "/" in frame_rate:
        numerator, denominator = frame_rate.split("/", 1)
        if float(denominator):
            fps = float(numerator) / float(denominator)
    return {
        "duration_seconds": round(duration, 3),
        "size_bytes": int(media_format.get("size") or path.stat().st_size),
        "format_name": clean_text(media_format.get("format_name")),
        "video_codec": clean_text(video.get("codec_name")),
        "width": int(video.get("width") or 0),
        "height": int(video.get("height") or 0),
        "fps": round(fps, 3),
        "has_audio": bool(audio),
        "audio_codec": clean_text(audio.get("codec_name")),
        "sample_rate": int(audio.get("sample_rate") or 0),
        "channels": int(audio.get("channels") or 0),
    }


def parse_iso(value: Any, label: str) -> str:
    text = require_text(value, label)
    normalized = text[:-1] + "+00:00" if text.endswith("Z") else text
    try:
        dt.datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise AnimalViralShortsError(f"{label}은(는) ISO 8601 시각이어야 합니다.") from exc
    return text


def slugify(value: str) -> str:
    result = re.sub(r"[^a-zA-Z0-9가-힣]+", "-", value).strip("-").lower()
    return result[:64] or "animal-short"


def platform_from_url(url: str) -> tuple[str, str]:
    parsed = urlparse(url)
    host = parsed.netloc.lower().split(":")[0]
    if parsed.scheme != "https":
        fail("소스 URL은 HTTPS여야 합니다.")
    if host == "www.tiktok.com" or host.endswith(".tiktok.com"):
        match = re.search(r"/video/(\d+)", parsed.path)
        if not match:
            fail("TikTok 원본 URL에는 /video/<id>가 필요합니다.")
        return "tiktok", match.group(1)
    if host in {"www.youtube.com", "youtube.com"}:
        match = re.match(r"/shorts/([A-Za-z0-9_-]{6,})", parsed.path)
        if not match:
            fail("YouTube 원본 URL은 /shorts/<id> 형식이어야 합니다.")
        return "youtube_shorts", match.group(1)
    fail("지원하는 URL은 TikTok 또는 YouTube Shorts 정식 URL입니다.")


def rights_from(value: Any, label: str = "rights") -> dict[str, Any]:
    if isinstance(value, str):
        status = value
        evidence = ""
    else:
        obj = require_object(value, label)
        status = require_text(obj.get("status"), f"{label}.status")
        evidence = clean_text(obj.get("evidence"))
    if status not in RIGHTS_STATUSES:
        fail(f"{label}.status는 다음 중 하나여야 합니다: {', '.join(sorted(RIGHTS_STATUSES))}")
    return {
        "status": status,
        "evidence": evidence,
        "publication_eligibility": "not_assessed",
    }


def candidate_list(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        values = payload
    else:
        obj = require_object(payload, "후보 입력")
        values = obj.get("ranked_candidates", obj.get("candidates", []))
    return [require_object(item, f"candidate[{index}]") for index, item in enumerate(require_list(values, "candidates"))]


def latest_metrics(value: Any, label: str) -> dict[str, float]:
    if isinstance(value, list):
        if not value:
            fail(f"{label}이 비어 있습니다.")
        raw = require_object(value[-1], f"{label}[-1]")
    else:
        raw = require_object(value, label)
    result: dict[str, float] = {}
    for key in ("views", "likes", "comments", "shares"):
        if raw.get(key) is not None:
            result[key] = require_number(raw.get(key), f"{label}.{key}", 0)
    if "views" not in result:
        fail(f"{label}.views가 필요합니다.")
    return result


def normalize_candidate(value: dict[str, Any], index: int) -> tuple[dict[str, Any], list[str]]:
    issues: list[str] = []
    candidate_id = require_text(value.get("id"), f"candidate[{index}].id")
    url = require_text(value.get("canonical_url", value.get("url")), f"{candidate_id}.canonical_url")
    platform, url_video_id = platform_from_url(url)
    declared_platform = require_text(value.get("platform"), f"{candidate_id}.platform")
    if declared_platform not in PLATFORMS or declared_platform != platform:
        issues.append("플랫폼 값과 정식 URL이 일치하지 않습니다.")
    declared_video_id = require_text(value.get("video_id"), f"{candidate_id}.video_id")
    if declared_video_id != url_video_id:
        issues.append("video_id가 정식 URL과 일치하지 않습니다.")
    creator = require_text(value.get("creator"), f"{candidate_id}.creator")
    collected_at = parse_iso(value.get("collected_at"), f"{candidate_id}.collected_at")
    metric_source_url = require_text(value.get("metric_source_url"), f"{candidate_id}.metric_source_url")
    if urlparse(metric_source_url).scheme != "https":
        issues.append("지표 출처 URL은 HTTPS여야 합니다.")
    collector = require_text(value.get("collector"), f"{candidate_id}.collector")
    scene_summary = require_text(value.get("scene_summary"), f"{candidate_id}.scene_summary", 10)
    animal = require_object(value.get("animal"), f"{candidate_id}.animal")
    species = require_text(animal.get("species"), f"{candidate_id}.animal.species")
    behavior_value = animal.get("observable_behavior")
    if isinstance(behavior_value, list):
        behaviors = [require_text(item, f"{candidate_id}.animal.observable_behavior") for item in behavior_value]
    else:
        behaviors = [require_text(behavior_value, f"{candidate_id}.animal.observable_behavior")]
    state_changes = [
        require_text(item, f"{candidate_id}.state_changes")
        for item in require_list(value.get("state_changes"), f"{candidate_id}.state_changes")
    ]
    if len(state_changes) < 2:
        issues.append("시작·변화·결말 중 최소 2개 상태가 필요합니다.")
    explanation_input = require_object(
        value.get("content_explanation", {}),
        f"{candidate_id}.content_explanation",
    )
    content_explanation = {
        "story_flow": clean_text(explanation_input.get("story_flow")) or " → ".join(state_changes),
        "appeal": clean_text(explanation_input.get("appeal")),
        "adaptation_note": clean_text(explanation_input.get("adaptation_note")),
        "limitations": clean_text(explanation_input.get("limitations")),
    }
    metrics = latest_metrics(value.get("metrics"), f"{candidate_id}.metrics")
    rights = rights_from(value.get("rights", "unknown"), f"{candidate_id}.rights")
    sensitive = require_object(value.get("sensitive", {}), f"{candidate_id}.sensitive")
    sensitive_flag = bool(sensitive.get("is_sensitive", False))
    categories = [
        require_text(item, f"{candidate_id}.sensitive.categories")
        for item in require_list(sensitive.get("categories", []), f"{candidate_id}.sensitive.categories")
    ]
    fit_input = require_object(value.get("editorial_fit"), f"{candidate_id}.editorial_fit")
    fit: dict[str, float] = {}
    for key, maximum in CANDIDATE_WEIGHTS.items():
        fit[key] = require_number(fit_input.get(key), f"{candidate_id}.editorial_fit.{key}", 0, maximum)
    flags = require_object(value.get("penalties", {}), f"{candidate_id}.penalties")
    active_flags = sorted(key for key, flag in flags.items() if flag is True)
    for key, flag in flags.items():
        if not isinstance(flag, bool):
            issues.append(f"penalties.{key}는 true 또는 false여야 합니다.")
    if any(key in active_flags for key in HARD_REJECTIONS):
        issues.append("실제 결말이 없거나 원본 전체 재업로드에 가까운 후보입니다.")

    views = metrics["views"]
    if views < 1_000_000:
        issues.append("검증 조회수가 100만 미만입니다.")
    interactions = sum(metrics.get(key, 0) for key in ("likes", "comments", "shares"))
    engagement = interactions / views if views else 0
    if platform == "tiktok":
        supporting = (
            views >= 3_000_000
            or metrics.get("shares", 0) >= 10_000
            or interactions >= 100_000
            or engagement >= 0.08
        )
    else:
        supporting = (
            views >= 3_000_000
            or metrics.get("likes", 0) >= 5_000
            or metrics.get("comments", 0) >= 300
        )
    if not supporting:
        issues.append("플랫폼별 보조 도달·참여 조건을 충족하지 못했습니다.")

    base_score = sum(fit.values())
    penalty_total = sum(PENALTIES.get(key, 0) for key in active_flags)
    score = max(0.0, base_score - penalty_total)
    if fit["first_frame_hook"] < 12:
        issues.append("첫 프레임 훅 점수가 12점 미만입니다.")
    if fit["state_change_density"] < 12:
        issues.append("상태 변화 점수가 12점 미만입니다.")
    if fit["payoff_clarity"] < 12:
        issues.append("결말 점수가 12점 미만입니다.")
    if score < 70:
        issues.append("감점 후 편집 적합성 총점이 70점 미만입니다.")

    normalized = {
        "id": candidate_id,
        "platform": platform,
        "canonical_url": url,
        "video_id": url_video_id,
        "creator": creator,
        "published_at": clean_text(value.get("published_at")),
        "collected_at": collected_at,
        "collector": collector,
        "metric_source_url": metric_source_url,
        "scene_summary": scene_summary,
        "content_explanation": content_explanation,
        "animal": {
            "species": species,
            "observable_behavior": behaviors,
        },
        "state_changes": state_changes,
        "metrics": {
            **{key: int(number) for key, number in metrics.items()},
            "interactions": int(interactions),
            "engagement_rate": round(engagement, 6),
        },
        "sensitive": {
            "is_sensitive": sensitive_flag,
            "categories": categories,
            "welfare_note": clean_text(sensitive.get("welfare_note")),
        },
        "rights": rights,
        "editorial_fit": {
            "components": fit,
            "base_score": round(base_score, 2),
            "penalties": active_flags,
            "penalty_total": round(penalty_total, 2),
            "score": round(score, 2),
        },
    }
    return normalized, issues


def candidate_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Animal Viral Shorts 후보 비교",
        "",
        f"- 생성 시각: {payload['generated_at']}",
        f"- 통과: {len(payload['ranked_candidates'])}개",
        f"- 제외: {len(payload['rejected_candidates'])}개",
        "",
    ]
    for index, item in enumerate(payload["ranked_candidates"], start=1):
        metrics = item["metrics"]
        metric_parts = [f"조회수 {metrics['views']:,}"]
        for key, label in (("likes", "좋아요"), ("comments", "댓글"), ("shares", "공유")):
            if key in metrics:
                metric_parts.append(f"{label} {metrics[key]:,}")
        explanation = item["content_explanation"]
        lines.extend(
            [
                f"## {index}. {item['id']} — {item['editorial_fit']['score']:.1f}점",
                "",
                f"- 플랫폼: {item['platform']}",
                f"- 제작자: {item['creator']}",
                f"- 공개 지표: {' · '.join(metric_parts)}",
                f"- 지표 수집 시각: {item['collected_at']}",
                f"- 한 줄 내용: {item['scene_summary']}",
                f"- 내용 흐름: {explanation['story_flow']}",
                f"- 장면 변화: {' → '.join(item['state_changes'])}",
                f"- 실제 행동: {', '.join(item['animal']['observable_behavior'])}",
                f"- 흥미 포인트: {explanation['appeal'] or '별도 설명 미기록'}",
                f"- 활용 방향: {explanation['adaptation_note'] or '별도 설명 미기록'}",
                f"- 활용 한계: {explanation['limitations'] or '별도 설명 미기록'}",
                f"- 복지 검토: {item['sensitive']['welfare_note'] or '특이사항 미기록'}",
                f"- 권리 상태: {item['rights']['status']}",
                f"- 원본: {item['canonical_url']}",
                f"- 지표 근거: {item['metric_source_url']}",
                "",
            ]
        )
    if payload["rejected_candidates"]:
        lines.extend(["## 제외 후보", ""])
        for item in payload["rejected_candidates"]:
            lines.append(f"- {item['id']}: {'; '.join(item['reasons'])}")
    lines.extend(
        [
            "",
            "이 순위는 편집 적합성 비교이며 실제 조회수, 게시 권리, 수익화를 보장하지 않습니다.",
            "사용자가 후보를 선택하기 전에는 획득하거나 렌더링하지 않습니다.",
            "",
        ]
    )
    return "\n".join(lines)


def command_score_candidates(args: argparse.Namespace) -> int:
    input_path = Path(args.input).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()
    markdown_path = output_path.with_suffix(".md")
    ensure_new([output_path, markdown_path], args.overwrite)
    values = candidate_list(read_json(input_path))
    ranked: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for index, value in enumerate(values):
        try:
            normalized, issues = normalize_candidate(value, index)
        except AnimalViralShortsError as exc:
            rejected.append({"id": clean_text(value.get("id")) or f"candidate-{index + 1}", "reasons": [str(exc)]})
            continue
        key = (normalized["platform"], normalized["video_id"])
        if key in seen:
            issues.append("같은 플랫폼 영상 ID가 이미 포함되어 있습니다.")
        seen.add(key)
        if issues:
            rejected.append({"id": normalized["id"], "reasons": issues})
        else:
            ranked.append(normalized)
    ranked.sort(key=lambda item: (item["editorial_fit"]["score"], item["metrics"]["views"]), reverse=True)
    top_k = min(max(int(args.top_k), 1), 3)
    omitted = ranked[top_k:]
    for item in omitted:
        rejected.append({"id": item["id"], "reasons": ["상위 후보 수 제한으로 비교 목록에서 제외되었습니다."]})
    payload = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": now_iso(),
        "selection_required": True,
        "auto_selected": False,
        "top_k": top_k,
        "ranked_candidates": ranked[:top_k],
        "rejected_candidates": rejected,
        "disclaimer": "편집 적합성 점수는 실제 조회수 또는 게시 권리를 예측하지 않습니다.",
    }
    write_json(output_path, payload)
    markdown_path.write_text(candidate_markdown(payload), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def selected_candidate(path: Path, candidate_id: str) -> dict[str, Any]:
    values = candidate_list(read_json(path))
    for value in values:
        if clean_text(value.get("id")) == candidate_id:
            if "editorial_fit" in value and "components" in require_object(value["editorial_fit"], "editorial_fit"):
                return value
            normalized, issues = normalize_candidate(value, 0)
            if issues:
                fail("선택 후보가 자격 조건을 통과하지 못했습니다: " + "; ".join(issues))
            return normalized
    fail(f"선택 후보를 찾지 못했습니다: {candidate_id}")


def source_entry_from_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "kind": "public_url",
        "platform": candidate["platform"],
        "video_id": candidate["video_id"],
        "original_url": candidate["canonical_url"],
        "creator": candidate["creator"],
        "selected_candidate_id": candidate["id"],
        "selected_at": now_iso(),
        "metrics_snapshot": candidate["metrics"],
        "metric_source_url": candidate["metric_source_url"],
        "collected_at": candidate["collected_at"],
        "animal": candidate["animal"],
        "sensitive": candidate["sensitive"],
        "rights": candidate["rights"],
        "media": [],
    }


def source_entry_from_url(url: str, creator: str, rights_status: str) -> dict[str, Any]:
    platform, video_id = platform_from_url(url)
    return {
        "kind": "public_url",
        "platform": platform,
        "video_id": video_id,
        "original_url": url,
        "creator": creator,
        "selected_candidate_id": "",
        "selected_at": now_iso(),
        "metrics_snapshot": {},
        "metric_source_url": "",
        "collected_at": "",
        "animal": {},
        "sensitive": {"is_sensitive": False, "categories": [], "welfare_note": ""},
        "rights": rights_from(rights_status),
        "media": [],
    }


def base_project(
    project_dir: Path,
    source: dict[str, Any],
    status: str,
    visual_preset: str,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "plugin": "animal-viral-shorts",
        "plugin_version": PLUGIN_VERSION,
        "project_id": project_dir.name,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "status": status,
        "local_only": True,
        "template": {
            "id": TEMPLATE_ID,
            "visual_preset": visual_preset,
            "width": CANVAS_WIDTH,
            "height": CANVAS_HEIGHT,
            "fps": 30,
            "background": "#F5F1EA",
            "text": "#141414",
            "accent": "#C94F3D",
            "regions": {
                "top_safe": [0, 0, 720, 56],
                "headline": [0, 56, 720, 208],
                "video": [0, 264, 720, 768],
                "caption": [0, 1032, 720, 96],
                "bottom_safe": [0, 1128, 720, 152],
                "right_safe_width": RIGHT_SAFE_WIDTH,
            },
        },
        "selections": {
            "source": {
                "confirmed": True,
                "candidate_id": clean_text(source.get("selected_candidate_id")),
                "confirmed_at": now_iso(),
            },
            "story": {
                "confirmed": False,
                "story_id": "",
                "confirmed_at": "",
            },
        },
        "draft_review": {
            "approved": False,
            "story_fit": "pending",
            "music_fit": "pending",
            "reviewed_at": "",
        },
        "publication": {
            "supported": False,
            "eligibility": "not_assessed",
        },
    }


def base_rights_manifest(source: dict[str, Any]) -> dict[str, Any]:
    rights = require_object(source.get("rights"), "source.rights")
    return {
        "schema_version": SCHEMA_VERSION,
        "updated_at": now_iso(),
        "local_only": True,
        "publication_eligibility": "not_assessed",
        "source": {
            "platform": clean_text(source.get("platform")),
            "creator": clean_text(source.get("creator")),
            "original_url": clean_text(source.get("original_url")),
            "rights_status": clean_text(rights.get("status")),
            "rights_evidence": clean_text(rights.get("evidence")),
            "sha256": "",
        },
        "assets": [],
        "limitations": [
            "로컬 렌더는 게시 권리, 공정 이용, 수익화 또는 플랫폼 승인을 증명하지 않습니다.",
            "공개 접근 가능성은 재사용 허가가 아닙니다.",
        ],
    }


def write_project(
    project_dir: Path,
    source: dict[str, Any],
    status: str,
    visual_preset: str,
) -> None:
    project_dir.mkdir(parents=True, exist_ok=False)
    for relative in ("assets/source", "assets/preview", "assets/music", "outputs"):
        safe_project_path(project_dir, relative).mkdir(parents=True, exist_ok=True)
    write_json(project_dir / "project.json", base_project(project_dir, source, status, visual_preset))
    write_json(project_dir / "source.json", source)
    write_json(project_dir / "rights-manifest.json", base_rights_manifest(source))


def command_init(args: argparse.Namespace) -> int:
    project_dir = Path(args.project_dir).expanduser().resolve()
    if project_dir.exists():
        fail(f"프로젝트 폴더가 이미 있습니다: {project_dir}")
    modes = sum(bool(value) for value in (args.candidates, args.source_file, args.source_url))
    if modes != 1:
        fail("--candidates, --source-file, --source-url 중 정확히 하나를 사용해야 합니다.")

    if args.candidates:
        if not args.candidate_id:
            fail("--candidates에는 사용자가 선택한 --candidate-id가 필요합니다.")
        candidate = selected_candidate(Path(args.candidates).expanduser().resolve(), args.candidate_id)
        source = source_entry_from_candidate(candidate)
        if clean_text(source["rights"].get("status")) == "not_permitted":
            fail("not_permitted 후보로는 프로젝트를 만들 수 없습니다.")
        write_project(project_dir, source, "source_selected", args.visual_preset)
    elif args.source_url:
        creator = require_text(args.creator, "--creator")
        status = require_text(args.rights_status, "--rights-status")
        source = source_entry_from_url(args.source_url, creator, status)
        if status == "not_permitted":
            fail("not_permitted URL로는 프로젝트를 만들 수 없습니다.")
        write_project(project_dir, source, "source_selected", args.visual_preset)
    else:
        creator = require_text(args.creator, "--creator")
        status = require_text(args.rights_status, "--rights-status")
        if status not in RIGHTS_STATUSES:
            fail("지원하지 않는 권리 상태입니다.")
        if status == "not_permitted":
            fail("not_permitted 로컬 파일로는 프로젝트를 만들 수 없습니다.")
        source_path = Path(args.source_file).expanduser().resolve()
        if not source_path.is_file() or source_path.suffix.lower() not in MEDIA_SUFFIXES:
            fail("읽을 수 있는 MP4, MOV, MKV, WEBM 또는 M4V 파일이 필요합니다.")
        source = {
            "kind": "local_file",
            "platform": "local",
            "video_id": "",
            "original_url": "",
            "original_local_path": str(source_path),
            "creator": creator,
            "selected_candidate_id": "",
            "selected_at": now_iso(),
            "metrics_snapshot": {},
            "metric_source_url": "",
            "collected_at": "",
            "animal": {},
            "sensitive": {"is_sensitive": False, "categories": [], "welfare_note": ""},
            "rights": rights_from(status),
            "media": [],
        }
        write_project(project_dir, source, "source_selected", args.visual_preset)
        destination = project_dir / "assets" / "source" / f"source{source_path.suffix.lower()}"
        shutil.copy2(source_path, destination)
        media = {
            "id": "primary",
            "relative_path": relative_path(project_dir, destination),
            "sha256": sha256_file(destination),
            "probe": probe_media(destination),
        }
        source["media"] = [media]
        source["acquired_at"] = now_iso()
        project = read_json(project_dir / "project.json")
        project["status"] = "source_acquired"
        project["updated_at"] = now_iso()
        rights = read_json(project_dir / "rights-manifest.json")
        rights["source"]["sha256"] = media["sha256"]
        rights["updated_at"] = now_iso()
        write_json(project_dir / "source.json", source)
        write_json(project_dir / "project.json", project)
        write_json(project_dir / "rights-manifest.json", rights)
    print(json.dumps({"project_dir": str(project_dir), "status": read_json(project_dir / "project.json")["status"]}, ensure_ascii=False, indent=2))
    return 0


def load_project(project_dir: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    project = require_object(read_json(project_dir / "project.json"), "project.json")
    source = require_object(read_json(project_dir / "source.json"), "source.json")
    if clean_text(project.get("plugin")) != "animal-viral-shorts":
        fail("animal-viral-shorts 프로젝트가 아닙니다.")
    return project, source


def normalize_visual_preset(value: Any, label: str, *, fallback: str) -> str:
    preset = clean_text(value) or fallback
    if preset not in VISUAL_PRESETS:
        fail(f"{label}이 지원되지 않습니다: {preset}")
    return preset


def project_visual_preset(project: dict[str, Any]) -> str:
    template = require_object(project.get("template"), "project.template")
    return normalize_visual_preset(
        template.get("visual_preset"),
        "project.template.visual_preset",
        fallback=LEGACY_VISUAL_PRESET,
    )


def source_media(project_dir: Path, source: dict[str, Any]) -> tuple[Path, dict[str, Any]]:
    media = require_list(source.get("media", []), "source.media")
    if len(media) != 1:
        fail("선택 원본 미디어가 하나 등록되어야 합니다.")
    entry = require_object(media[0], "source.media[0]")
    path = safe_project_path(project_dir, require_text(entry.get("relative_path"), "source.media[0].relative_path"), exists=True)
    return path, entry


def yt_dlp_command() -> list[str]:
    executable = shutil.which("yt-dlp")
    if executable:
        return [executable]
    if importlib.util.find_spec("yt_dlp"):
        return [sys.executable, "-m", "yt_dlp"]
    fail("yt-dlp가 필요합니다. 제3자 다운로드 서비스로 우회하지 않습니다.")


def command_acquire(args: argparse.Namespace) -> int:
    project_dir = Path(args.project_dir).expanduser().resolve()
    project, source = load_project(project_dir)
    if clean_text(source.get("rights", {}).get("status")) == "not_permitted":
        fail("not_permitted 소스는 획득할 수 없습니다.")
    if source.get("media"):
        path, _ = source_media(project_dir, source)
        print(json.dumps({"status": "source_acquired", "media": str(path)}, ensure_ascii=False, indent=2))
        return 0
    if clean_text(source.get("kind")) != "public_url":
        fail("획득할 공개 URL이 없습니다.")
    if not re.fullmatch(r"\d+(?:\.\d+)?[KMG]?", args.max_filesize, re.IGNORECASE):
        fail("--max-filesize는 500M 같은 형식이어야 합니다.")
    url = require_text(source.get("original_url"), "source.original_url")
    platform_from_url(url)
    output_template = project_dir / "assets" / "source" / "source.%(ext)s"
    command = yt_dlp_command() + [
        "--no-playlist",
        "--no-overwrites",
        "--restrict-filenames",
        "--max-filesize",
        args.max_filesize,
        "-f",
        "bv*+ba/b",
        "--merge-output-format",
        "mp4",
        "-o",
        str(output_template),
        url,
    ]
    try:
        run_checked(command, "선택 원본 획득", timeout=900)
    except AnimalViralShortsError:
        project["status"] = "source_pending"
        project["updated_at"] = now_iso()
        project["source_pending_reason"] = "직접 획득 실패. 권한 있는 로컬 파일이 필요합니다."
        write_json(project_dir / "project.json", project)
        raise
    files = [
        path
        for path in (project_dir / "assets" / "source").iterdir()
        if path.is_file() and path.suffix.lower() in MEDIA_SUFFIXES
    ]
    if len(files) != 1:
        fail("획득 후 원본 미디어를 하나로 확정하지 못했습니다.")
    path = files[0]
    entry = {
        "id": "primary",
        "relative_path": relative_path(project_dir, path),
        "sha256": sha256_file(path),
        "probe": probe_media(path),
    }
    source["media"] = [entry]
    source["acquired_at"] = now_iso()
    project["status"] = "source_acquired"
    project["updated_at"] = now_iso()
    rights = require_object(read_json(project_dir / "rights-manifest.json"), "rights-manifest.json")
    rights["source"]["sha256"] = entry["sha256"]
    rights["updated_at"] = now_iso()
    write_json(project_dir / "source.json", source)
    write_json(project_dir / "project.json", project)
    write_json(project_dir / "rights-manifest.json", rights)
    print(json.dumps({"status": project["status"], "media": entry}, ensure_ascii=False, indent=2))
    return 0


def find_font() -> Path:
    font = next((path for path in FONT_CANDIDATES if path.is_file()), None)
    if not font:
        fail("한국어 자막 렌더용 글꼴을 찾지 못했습니다.")
    return font


def command_preview(args: argparse.Namespace) -> int:
    project_dir = Path(args.project_dir).expanduser().resolve()
    project, source = load_project(project_dir)
    if clean_text(project.get("status")) not in {"source_acquired", "source_review_ready", "source_reviewed", "stories_ready", "story_selected", "composed", "render_ready", "rendered_local", "rendered_draft", "draft_approved"}:
        fail("원본 획득 후 preview를 만들 수 있습니다.")
    media_path, media_entry = source_media(project_dir, source)
    probe = require_object(media_entry.get("probe"), "source.media.probe")
    duration = require_number(probe.get("duration_seconds"), "source.media.probe.duration_seconds", 0.01)
    interval = require_number(args.interval, "--interval", 0.25)
    max_frames = int(require_number(args.max_frames, "--max-frames", 1, 120))
    preview_dir = project_dir / "assets" / "preview"
    existing = list(preview_dir.glob("frame-*.jpg")) + [preview_dir / "contact-sheet.jpg", preview_dir / "preview.json"]
    ensure_new(existing, args.overwrite)
    if args.overwrite:
        for path in existing:
            if path.exists() and path.is_file():
                path.unlink()
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        fail("preview 생성에는 ffmpeg가 필요합니다.")
    frame_pattern = preview_dir / "frame-%03d.jpg"
    run_checked(
        [
            ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(media_path),
            "-vf",
            f"fps=1/{interval},scale=320:-2",
            "-frames:v",
            str(max_frames),
            "-q:v",
            "3",
            "-y",
            str(frame_pattern),
        ],
        "대표 프레임 생성",
    )
    frames = sorted(preview_dir.glob("frame-*.jpg"))
    if not frames:
        fail("대표 프레임이 생성되지 않았습니다.")
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as exc:
        raise AnimalViralShortsError("콘택트시트 생성에는 Pillow가 필요합니다.") from exc
    columns = 4
    thumb_w, thumb_h = 320, 220
    rows = math.ceil(len(frames) / columns)
    sheet = Image.new("RGB", (columns * thumb_w, rows * thumb_h), "#F5F1EA")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.truetype(str(find_font()), 18)
    frame_records: list[dict[str, Any]] = []
    for index, frame_path in enumerate(frames):
        image = Image.open(frame_path).convert("RGB")
        image.thumbnail((thumb_w, thumb_h - 28))
        x = (index % columns) * thumb_w + (thumb_w - image.width) // 2
        y = (index // columns) * thumb_h
        sheet.paste(image, (x, y))
        seconds = min(index * interval, duration)
        label = f"{seconds:.1f}s"
        draw.text(((index % columns) * thumb_w + 8, y + thumb_h - 26), label, font=font, fill="#141414")
        frame_records.append(
            {
                "relative_path": relative_path(project_dir, frame_path),
                "approx_seconds": round(seconds, 3),
            }
        )
    contact_sheet = preview_dir / "contact-sheet.jpg"
    sheet.save(contact_sheet, quality=90)
    preview_payload = {
        "generated_at": now_iso(),
        "source": relative_path(project_dir, media_path),
        "duration_seconds": duration,
        "interval_seconds": interval,
        "frames": frame_records,
        "contact_sheet": relative_path(project_dir, contact_sheet),
        "visual_review_required": True,
    }
    write_json(preview_dir / "preview.json", preview_payload)
    project["status"] = "source_review_ready"
    project["updated_at"] = now_iso()
    project["preview"] = {
        "relative_path": relative_path(project_dir, preview_dir / "preview.json"),
        "contact_sheet": relative_path(project_dir, contact_sheet),
        "generated_at": preview_payload["generated_at"],
    }
    write_json(project_dir / "project.json", project)
    print(json.dumps(preview_payload, ensure_ascii=False, indent=2))
    return 0


def normalized_region(value: Any, label: str) -> dict[str, float]:
    obj = require_object(value, label)
    result = {
        "x": require_number(obj.get("x"), f"{label}.x", 0, 1),
        "y": require_number(obj.get("y"), f"{label}.y", 0, 1),
        "width": require_number(obj.get("width"), f"{label}.width", 0.01, 1),
        "height": require_number(obj.get("height"), f"{label}.height", 0.01, 1),
    }
    if result["x"] + result["width"] > 1.000001 or result["y"] + result["height"] > 1.000001:
        fail(f"{label} 영역이 프레임 밖으로 나갑니다.")
    if obj.get("radius") is not None:
        result["radius"] = require_number(obj.get("radius"), f"{label}.radius", 4, 40)
    return result


def regions_overlap(left: dict[str, float], right: dict[str, float]) -> bool:
    return not (
        left["x"] + left["width"] <= right["x"]
        or right["x"] + right["width"] <= left["x"]
        or left["y"] + left["height"] <= right["y"]
        or right["y"] + right["height"] <= left["y"]
    )


def source_caption_override(value: Any, label: str, scene_duration: float) -> dict[str, Any]:
    obj = require_object(value, label)
    region = normalized_region(obj.get("canvas_region"), f"{label}.canvas_region")
    if region["y"] < VIDEO_TOP / CANVAS_HEIGHT or region["y"] + region["height"] > FOOTER_TOP / CANVAS_HEIGHT:
        fail(f"{label}.canvas_region은 원본 영상 영역 안에 있어야 합니다.")
    if region["x"] + region["width"] > (CANVAS_WIDTH - RIGHT_SAFE_WIDTH) / CANVAS_WIDTH:
        fail(f"{label}.canvas_region은 오른쪽 플랫폼 UI 안전 영역을 침범할 수 없습니다.")
    if region["width"] < 0.2 or region["height"] < 0.05:
        fail(f"{label}.canvas_region은 번역 문구를 읽을 수 있는 크기여야 합니다.")
    start = require_number(obj.get("start_seconds"), f"{label}.start_seconds", 0, scene_duration)
    end = require_number(obj.get("end_seconds"), f"{label}.end_seconds", start + 0.01, scene_duration)
    if obj.get("reviewed_safe") is not True:
        fail(f"{label}.reviewed_safe는 사람 검토 후 true여야 합니다.")
    if obj.get("not_observation") is not True:
        fail(f"{label}.not_observation는 번역을 관찰 근거와 분리하기 위해 true여야 합니다.")
    return {
        "source_text": require_text(obj.get("source_text"), f"{label}.source_text"),
        "text": require_text(obj.get("text"), f"{label}.text"),
        "label": clean_text(obj.get("label")) or "원문 의역",
        "start_seconds": round(start, 3),
        "end_seconds": round(end, 3),
        "canvas_region": region,
        "reviewed_safe": True,
        "not_observation": True,
    }


def sfx_event(value: Any, label: str, scene_duration: float) -> dict[str, Any]:
    obj = require_object(value, label)
    effect_type = require_text(obj.get("type"), f"{label}.type")
    if effect_type not in SFX_TYPES:
        fail(f"{label}.type이 지원되지 않습니다: {effect_type}")
    return {
        "type": effect_type,
        "offset_seconds": round(require_number(obj.get("offset_seconds", 0), f"{label}.offset_seconds", 0, scene_duration), 3),
        "gain_db": round(require_number(obj.get("gain_db", -8), f"{label}.gain_db", -24, 0), 2),
    }


def observation_record(value: Any, index: int, duration: float) -> dict[str, Any]:
    obj = require_object(value, f"observations[{index}]")
    observation_id = require_text(obj.get("id"), f"observations[{index}].id")
    start = require_number(obj.get("start_seconds"), f"{observation_id}.start_seconds", 0)
    end = require_number(obj.get("end_seconds"), f"{observation_id}.end_seconds", start + 0.01)
    if end > duration + 0.05:
        fail(f"{observation_id} 타임코드가 원본 길이를 넘습니다.")
    confidence = require_text(obj.get("confidence"), f"{observation_id}.confidence")
    if confidence not in EMOTION_CONFIDENCE:
        fail(f"{observation_id}.confidence는 observed, caregiver_report, inference 중 하나여야 합니다.")
    return {
        "id": observation_id,
        "start_seconds": round(start, 3),
        "end_seconds": round(end, 3),
        "subject": require_text(obj.get("subject"), f"{observation_id}.subject"),
        "action": require_text(obj.get("action"), f"{observation_id}.action", 2),
        "visible_evidence": require_text(obj.get("visible_evidence"), f"{observation_id}.visible_evidence", 2),
        "confidence": confidence,
    }


def command_observe(args: argparse.Namespace) -> int:
    project_dir = Path(args.project_dir).expanduser().resolve()
    project, source = load_project(project_dir)
    if clean_text(project.get("status")) not in {"source_review_ready", "source_reviewed"}:
        fail("preview 프레임을 생성하고 실제 화면을 검토한 뒤 관찰 결과를 등록할 수 있습니다.")
    media_path, media_entry = source_media(project_dir, source)
    duration = require_number(media_entry.get("probe", {}).get("duration_seconds"), "source duration", 0.01)
    payload = require_object(read_json(Path(args.input).expanduser().resolve()), "관찰 입력")
    species = require_text(payload.get("species"), "species")
    subjects = [require_text(item, "subjects[]") for item in require_list(payload.get("subjects"), "subjects")]
    if not subjects:
        fail("한 개 이상의 관찰 대상이 필요합니다.")
    roles = [require_text(item, "relationship_roles[]") for item in require_list(payload.get("relationship_roles", []), "relationship_roles")]
    behaviors = [require_text(item, "observed_behaviors[]") for item in require_list(payload.get("observed_behaviors"), "observed_behaviors")]
    if len(behaviors) < 2:
        fail("서로 다른 관찰 행동이 2개 이상 필요합니다.")
    observations = [
        observation_record(value, index, duration)
        for index, value in enumerate(require_list(payload.get("observations"), "observations"))
    ]
    if len(observations) < 2:
        fail("시작·변화·결말을 뒷받침할 관찰 구간이 2개 이상 필요합니다.")
    if len({item["id"] for item in observations}) != len(observations):
        fail("관찰 ID는 서로 달라야 합니다.")

    sensitive_input = require_object(payload.get("sensitive", {}), "sensitive")
    categories = [require_text(item, "sensitive.categories[]") for item in require_list(sensitive_input.get("categories", []), "sensitive.categories")]
    fact_sources = [
        require_object(item, "sensitive.fact_sources[]")
        for item in require_list(sensitive_input.get("fact_sources", []), "sensitive.fact_sources")
    ]
    for index, fact in enumerate(fact_sources):
        require_text(fact.get("url"), f"sensitive.fact_sources[{index}].url")
        require_text(fact.get("supports"), f"sensitive.fact_sources[{index}].supports")
    if set(categories) & SENSITIVE_CATEGORIES and len(fact_sources) < 2:
        fail("구조·질병·학대·부상·사망·치료 소재에는 독립 사실 출처 2개가 필요합니다.")

    protected_input = require_object(payload.get("protected_regions", {}), "protected_regions")
    protected: dict[str, list[dict[str, float]]] = {}
    for key in ("watermarks", "animal_faces", "human_faces"):
        protected[key] = [
            normalized_region(item, f"protected_regions.{key}[{index}]")
            for index, item in enumerate(require_list(protected_input.get(key, []), f"protected_regions.{key}"))
        ]
    caption_input = require_object(payload.get("source_caption", {}), "source_caption")
    caption_detected = bool(caption_input.get("detected", False))
    caption_regions: list[dict[str, Any]] = []
    for index, value in enumerate(require_list(caption_input.get("regions", []), "source_caption.regions")):
        obj = require_object(value, f"source_caption.regions[{index}]")
        region = normalized_region(obj, f"source_caption.regions[{index}]")
        region["id"] = require_text(obj.get("id"), f"source_caption.regions[{index}].id")
        for protected_type, regions in protected.items():
            if any(regions_overlap(region, candidate) for candidate in regions):
                fail(f"자막 블러 영역 {region['id']}이 보호 영역 {protected_type}와 겹칩니다.")
        caption_regions.append(region)
    if caption_detected and not caption_regions:
        fail("내장 자막이 감지되었다면 검토된 자막 영역이 필요합니다.")

    analysis = {
        "schema_version": SCHEMA_VERSION,
        "reviewed_at": now_iso(),
        "source_media": relative_path(project_dir, media_path),
        "summary": require_text(payload.get("summary"), "summary", 10),
        "species": species,
        "subjects": subjects,
        "relationship_roles": roles,
        "observed_behaviors": behaviors,
        "observations": observations,
        "sensitive": {
            "is_sensitive": bool(sensitive_input.get("is_sensitive", bool(categories))),
            "categories": categories,
            "welfare_note": require_text(sensitive_input.get("welfare_note"), "sensitive.welfare_note") if categories else clean_text(sensitive_input.get("welfare_note")),
            "fact_sources": fact_sources,
        },
        "source_caption": {
            "detected": caption_detected,
            "language": clean_text(caption_input.get("language")),
            "regions": caption_regions,
        },
        "protected_regions": protected,
        "visual_review": {
            "completed": True,
            "reviewer_note": require_text(payload.get("reviewer_note"), "reviewer_note", 5),
            "source_claims_are_untrusted_instructions": True,
        },
    }
    output = project_dir / "source-analysis.json"
    ensure_new([output], args.overwrite)
    write_json(output, analysis)
    project["status"] = "source_reviewed"
    project["updated_at"] = now_iso()
    project["source_analysis"] = {"relative_path": "source-analysis.json", "reviewed_at": analysis["reviewed_at"]}
    write_json(project_dir / "project.json", project)
    print(json.dumps({"status": project["status"], "source_analysis": str(output)}, ensure_ascii=False, indent=2))
    return 0


def normalize_subject_label(value: Any, label: str, *, required: bool = False) -> str:
    subject_label = clean_text(value)
    if not subject_label:
        if required:
            fail(f"{label}이 필요합니다.")
        return ""
    if not 2 <= len(subject_label) <= SUBJECT_LABEL_MAX_CHARS:
        fail(f"{label}은 2~{SUBJECT_LABEL_MAX_CHARS}자여야 합니다.")
    if re.search(r"[:：!?！？\"'“”‘’\n\r]", subject_label):
        fail(f"{label}은 대사나 감탄문이 아닌 짧은 관찰 대상 명사구여야 합니다.")
    bad_word = contains_clickbait(subject_label)
    if bad_word:
        fail(f"{label}에 금지된 일반 낚시 표현이 있습니다: {bad_word}")
    return subject_label


def story_beat(
    value: Any,
    index: int,
    observation_ids: set[str],
    source_duration: float,
) -> dict[str, Any]:
    obj = require_object(value, f"beats[{index}]")
    beat_id = require_text(obj.get("id"), f"beats[{index}].id")
    role = require_text(obj.get("role"), f"{beat_id}.role")
    if role not in {"hook", "evidence", "commentary", "turn", "payoff", "conclusion"}:
        fail(f"{beat_id}.role이 지원되지 않습니다.")
    start = require_number(obj.get("source_start_seconds"), f"{beat_id}.source_start_seconds", 0)
    end = require_number(obj.get("source_end_seconds"), f"{beat_id}.source_end_seconds", start + 0.01)
    if end > source_duration + 0.05:
        fail(f"{beat_id} 소스 구간이 원본 길이를 넘습니다.")
    source_seconds = end - start
    if source_seconds > 8.0001:
        fail(f"{beat_id} 원본 구간은 8초를 넘을 수 없습니다.")
    output_duration = require_number(
        obj.get("output_duration_seconds", source_seconds),
        f"{beat_id}.output_duration_seconds",
        0.25,
        source_seconds + 1.5,
    )
    evidence = [
        require_text(item, f"{beat_id}.observation_ids[]")
        for item in require_list(obj.get("observation_ids"), f"{beat_id}.observation_ids")
    ]
    if not evidence or any(item not in observation_ids for item in evidence):
        fail(f"{beat_id}는 source-analysis.json의 관찰 ID를 하나 이상 참조해야 합니다.")
    focus = require_object(obj.get("focus_point", {"x": 0.5, "y": 0.5}), f"{beat_id}.focus_point")
    focus_point = {
        "x": require_number(focus.get("x"), f"{beat_id}.focus_point.x", 0, 1),
        "y": require_number(focus.get("y"), f"{beat_id}.focus_point.y", 0, 1),
    }
    act = require_text(obj.get("act"), f"{beat_id}.act")
    if act not in NARRATIVE_ACTS:
        fail(f"{beat_id}.act는 setup, build, turn, payoff 중 하나여야 합니다.")
    caption = require_text(obj.get("caption"), f"{beat_id}.caption", 2)
    caption_style = require_text(obj.get("caption_style"), f"{beat_id}.caption_style")
    if caption_style not in CAPTION_STYLES:
        fail(f"{beat_id}.caption_style이 지원되지 않습니다.")
    if caption_style != ACT_DEFAULTS[act]["caption_style"]:
        fail(f"{beat_id}.caption_style은 {act} 장면의 {ACT_DEFAULTS[act]['caption_style']}이어야 합니다.")
    subject_label = normalize_subject_label(obj.get("subject_label"), f"{beat_id}.subject_label")
    emphasis_phrase = require_text(obj.get("emphasis_phrase"), f"{beat_id}.emphasis_phrase")
    if emphasis_phrase not in caption:
        fail(f"{beat_id}.emphasis_phrase는 장면 자막에 포함되어야 합니다.")
    music_cue = require_text(obj.get("music_cue"), f"{beat_id}.music_cue")
    if music_cue not in MUSIC_CUES:
        fail(f"{beat_id}.music_cue가 지원되지 않습니다.")
    if music_cue not in ACT_MUSIC_CUES[act]:
        fail(f"{beat_id}.music_cue가 {act} 장면과 자연스럽게 대응하지 않습니다.")
    music_mood = require_text(obj.get("music_mood"), f"{beat_id}.music_mood")
    if music_mood not in MUSIC_MOODS:
        fail(f"{beat_id}.music_mood가 지원되지 않습니다.")
    source_audio_priority = require_text(obj.get("source_audio_priority"), f"{beat_id}.source_audio_priority")
    if source_audio_priority not in SOURCE_AUDIO_PRIORITIES:
        fail(f"{beat_id}.source_audio_priority가 지원되지 않습니다.")
    overrides = [
        source_caption_override(value, f"{beat_id}.source_caption_overrides[{override_index}]", output_duration)
        for override_index, value in enumerate(require_list(obj.get("source_caption_overrides", []), f"{beat_id}.source_caption_overrides"))
    ]
    sfx_events = [
        sfx_event(value, f"{beat_id}.sfx_events[{event_index}]", output_duration)
        for event_index, value in enumerate(require_list(obj.get("sfx_events", []), f"{beat_id}.sfx_events"))
    ]
    return {
        "id": beat_id,
        "role": role,
        "source_start_seconds": round(start, 3),
        "source_end_seconds": round(end, 3),
        "source_clip_seconds": round(source_seconds, 3),
        "output_duration_seconds": round(output_duration, 3),
        "act": act,
        "caption": caption,
        "subject_label": subject_label,
        "caption_style": caption_style,
        "emphasis_phrase": emphasis_phrase,
        "music_cue": music_cue,
        "music_mood": music_mood,
        "source_audio_priority": source_audio_priority,
        "observation_ids": evidence,
        "focus_point": focus_point,
        "continuous_action": bool(obj.get("continuous_action", False)),
        "visual_change_count": int(require_number(obj.get("visual_change_count", 1), f"{beat_id}.visual_change_count", 0, 10)),
        "source_caption_region_id": clean_text(obj.get("source_caption_region_id")),
        "source_caption_overrides": overrides,
        "sfx_events": sfx_events,
    }


def contains_clickbait(*values: str) -> str:
    joined = " ".join(values)
    return next((word for word in CLICKBAIT if word in joined), "")


def subject_label_is_grounded(subject_label: str, candidates: list[str]) -> bool:
    normalized_label = re.sub(r"\s+", "", subject_label)
    label_tokens = set(re.findall(r"[0-9A-Za-z가-힣]{2,}", subject_label))
    for candidate in candidates:
        normalized_candidate = re.sub(r"\s+", "", clean_text(candidate))
        if not normalized_candidate:
            continue
        if normalized_label in normalized_candidate or normalized_candidate in normalized_label:
            return True
        candidate_tokens = set(re.findall(r"[0-9A-Za-z가-힣]{2,}", candidate))
        if label_tokens & candidate_tokens:
            return True
    return False


def normalize_story(
    value: Any,
    index: int,
    analysis: dict[str, Any],
    source_duration: float,
    visual_preset: str,
) -> dict[str, Any]:
    story = require_object(value, f"stories[{index}]")
    story_id = require_text(story.get("id"), f"stories[{index}].id")
    archetype = require_text(story.get("archetype"), f"{story_id}.archetype")
    if archetype not in ARCHETYPE_GUIDES:
        fail(f"{story_id}.archetype이 지원되지 않습니다.")
    sensitive = require_object(analysis.get("sensitive", {}), "source-analysis.sensitive")
    if bool(sensitive.get("is_sensitive")) and archetype == "comic-reversal":
        fail(f"{story_id}: 민감한 동물 소재에는 comic-reversal을 사용할 수 없습니다.")
    hook = require_text(story.get("hook"), f"{story_id}.hook", 4)
    headline = require_object(story.get("headline"), f"{story_id}.headline")
    line1 = require_text(headline.get("line1"), f"{story_id}.headline.line1", 2)
    line2 = require_text(headline.get("line2"), f"{story_id}.headline.line2", 2)
    accent = require_text(headline.get("accent_phrase"), f"{story_id}.headline.accent_phrase", 1)
    if accent not in line1 and accent not in line2:
        fail(f"{story_id}.headline.accent_phrase는 두 헤드라인 중 하나에 포함되어야 합니다.")
    if len(line1) > 24 or len(line2) > 24:
        fail(f"{story_id} 헤드라인은 줄당 24자를 넘을 수 없습니다.")
    bad_word = contains_clickbait(hook, line1, line2)
    if bad_word:
        fail(f"{story_id}에 금지된 일반 낚시 표현이 있습니다: {bad_word}")
    observation_values = [
        require_object(item, "source-analysis.observations[]")
        for item in require_list(analysis.get("observations"), "source-analysis.observations")
    ]
    observations_by_id = {
        require_text(item.get("id"), "source-analysis.observations[].id"): item
        for item in observation_values
    }
    observation_ids = set(observations_by_id)
    beats = [
        story_beat(item, beat_index, observation_ids, source_duration)
        for beat_index, item in enumerate(require_list(story.get("beats"), f"{story_id}.beats"))
    ]
    if visual_preset == DEFAULT_VISUAL_PRESET:
        reviewed_subjects = [
            require_text(item, "source-analysis.subjects[]")
            for item in require_list(analysis.get("subjects"), "source-analysis.subjects")
        ]
        for beat in beats:
            subject_label = clean_text(beat.get("subject_label"))
            if not subject_label:
                fail(f"{story_id}.{beat['id']}에는 관찰 대비형 subject_label이 필요합니다.")
            grounded_subjects = reviewed_subjects + [
                require_text(observations_by_id[observation_id].get("subject"), f"{observation_id}.subject")
                for observation_id in beat["observation_ids"]
            ]
            if not subject_label_is_grounded(subject_label, grounded_subjects):
                fail(f"{story_id}.{beat['id']}.subject_label이 검토된 관찰 대상과 연결되지 않습니다.")
        for beat in beats[:-1]:
            if beat["output_duration_seconds"] > 3.0:
                fail(f"{story_id}.{beat['id']} 관찰 대비형 장면은 3초를 넘을 수 없습니다.")
        if beats and beats[-1]["output_duration_seconds"] > 4.0:
            fail(f"{story_id}.{beats[-1]['id']} 관찰 대비형 결말 장면은 프레임 고정을 포함해 4초를 넘을 수 없습니다.")
    if not 4 <= len(beats) <= 12:
        fail(f"{story_id}는 기승전결을 구성하는 4~12개 비트가 필요합니다.")
    if beats[0]["role"] != "hook":
        fail(f"{story_id}의 첫 비트는 hook이어야 합니다.")
    if beats[-1]["role"] not in {"payoff", "conclusion"}:
        fail(f"{story_id}의 마지막 비트는 payoff 또는 conclusion이어야 합니다.")
    if not any(beat["role"] == "turn" for beat in beats):
        fail(f"{story_id}에는 명시적인 turn 비트가 필요합니다.")
    act_positions = [NARRATIVE_ACTS.index(beat["act"]) for beat in beats]
    if set(beat["act"] for beat in beats) != set(NARRATIVE_ACTS):
        fail(f"{story_id}에는 setup, build, turn, payoff 기승전결이 모두 필요합니다.")
    if act_positions != sorted(act_positions):
        fail(f"{story_id}의 기승전결 순서가 뒤바뀌었습니다.")
    if beats[0]["act"] != "setup" or beats[-1]["act"] != "payoff":
        fail(f"{story_id}는 setup으로 시작하고 payoff로 끝나야 합니다.")
    final_hold = beats[-1]["output_duration_seconds"] - beats[-1]["source_clip_seconds"]
    if not 0.5 <= final_hold <= 1.0:
        fail(f"{story_id} 마지막 비트는 실제 소스 구간 뒤 0.5~1초 프레임 고정 시간을 포함해야 합니다.")
    for beat in beats:
        bad_word = contains_clickbait(beat["caption"])
        if bad_word:
            fail(f"{story_id}.{beat['id']} 자막에 금지 표현이 있습니다: {bad_word}")
    duration_target = require_number(
        story.get("duration_target_seconds"),
        f"{story_id}.duration_target_seconds",
        0.25,
        MAX_SHORT_SECONDS,
    )
    output_duration = sum(item["output_duration_seconds"] for item in beats)
    if abs(output_duration - duration_target) > 0.75:
        fail(f"{story_id} 비트 합계와 목표 길이 차이는 0.75초 이하여야 합니다.")
    cursor = 0.0
    turn_start = 0.0
    for beat in beats:
        if beat["role"] == "turn":
            turn_start = cursor
            break
        cursor += beat["output_duration_seconds"]
    if turn_start > output_duration * 0.75:
        fail(f"{story_id} turn 비트는 전체 길이의 75% 이전에 시작해야 합니다.")
    score_input = require_object(story.get("score"), f"{story_id}.score")
    components: dict[str, float] = {}
    for key, maximum_score in EVIDENCE_STORY_WEIGHTS.items():
        components[key] = require_number(score_input.get(key), f"{story_id}.score.{key}", 0, maximum_score)
    score_total = sum(components.values())
    if score_total < 75:
        fail(f"{story_id} 근거 스토리 점수가 75점 미만입니다.")
    fun_input = require_object(story.get("fun_score"), f"{story_id}.fun_score")
    fun_components: dict[str, float] = {}
    for key, maximum_score in FUN_STORY_WEIGHTS.items():
        fun_components[key] = require_number(fun_input.get(key), f"{story_id}.fun_score.{key}", 0, maximum_score)
    fun_total = sum(fun_components.values())
    if fun_total < 75:
        fail(f"{story_id} 재미 점수가 75점 미만입니다.")
    payoff = require_object(story.get("payoff"), f"{story_id}.payoff")
    payoff_observations = [
        require_text(item, f"{story_id}.payoff.observation_ids[]")
        for item in require_list(payoff.get("observation_ids"), f"{story_id}.payoff.observation_ids")
    ]
    if not payoff_observations or any(item not in observation_ids for item in payoff_observations):
        fail(f"{story_id} 결말은 실제 관찰 ID와 연결되어야 합니다.")
    mood = require_text(story.get("music_mood"), f"{story_id}.music_mood")
    if mood not in MUSIC_MOODS:
        fail(f"{story_id}.music_mood가 지원되지 않습니다.")
    narrative_arc_input = require_object(story.get("narrative_arc"), f"{story_id}.narrative_arc")
    narrative_arc = {
        act: require_text(narrative_arc_input.get(act), f"{story_id}.narrative_arc.{act}", 3)
        for act in NARRATIVE_ACTS
    }
    viewer_question = require_text(story.get("viewer_question"), f"{story_id}.viewer_question", 4)
    fun_mechanism = require_text(story.get("fun_mechanism"), f"{story_id}.fun_mechanism")
    if fun_mechanism not in FUN_MECHANISMS:
        fail(f"{story_id}.fun_mechanism이 지원되지 않습니다.")
    roles = [
        require_text(item, f"{story_id}.relationship_roles[]")
        for item in require_list(story.get("relationship_roles"), f"{story_id}.relationship_roles")
    ]
    if not roles:
        fail(f"{story_id}에 관계 역할이 필요합니다.")
    risk = require_object(story.get("risk"), f"{story_id}.risk")
    if bool(risk.get("invented_dialogue", False)) or bool(risk.get("unsupported_emotion", False)):
        fail(f"{story_id}는 실제 영상에 없는 대사나 감정 단정을 포함할 수 없습니다.")
    return {
        "id": story_id,
        "visual_preset": visual_preset,
        "archetype": archetype,
        "hook": hook,
        "headline": {
            "line1": line1,
            "line2": line2,
            "accent_phrase": accent,
        },
        "perspective": require_text(story.get("perspective"), f"{story_id}.perspective", 3),
        "viewer_question": viewer_question,
        "fun_mechanism": fun_mechanism,
        "narrative_arc": narrative_arc,
        "relationship_roles": roles,
        "beats": beats,
        "turn": require_text(story.get("turn"), f"{story_id}.turn", 3),
        "payoff": {
            "text": require_text(payoff.get("text"), f"{story_id}.payoff.text", 3),
            "observation_ids": payoff_observations,
            "time_seconds": require_number(payoff.get("time_seconds"), f"{story_id}.payoff.time_seconds", 0, source_duration),
        },
        "duration_target_seconds": round(duration_target, 3),
        "music_mood": mood,
        "risk": {
            "invented_dialogue": False,
            "unsupported_emotion": False,
            "note": require_text(risk.get("note"), f"{story_id}.risk.note", 3),
        },
        "score": {
            "components": components,
            "total": round(score_total, 2),
        },
        "fun_score": {
            "components": fun_components,
            "total": round(fun_total, 2),
        },
        "duration_guide_seconds": list(ARCHETYPE_GUIDES[archetype]),
    }


def stories_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Animal Viral Shorts 스토리 3안",
        "",
        "아래 세 안은 실제 관찰 타임코드에 연결되어 있으며 자동 선택되지 않습니다.",
        "",
    ]
    for index, story in enumerate(payload["stories"], start=1):
        lines.extend(
            [
                f"## {index}. {story['id']} — {story['archetype']} / 근거 {story['score']['total']:.1f}점 / 재미 {story['fun_score']['total']:.1f}점",
                "",
                f"- 훅: {story['hook']}",
                f"- 화면 프리셋: {story['visual_preset']}",
                f"- 헤드라인: {story['headline']['line1']} / {story['headline']['line2']}",
                f"- 관점: {story['perspective']}",
                f"- 시청자 질문: {story['viewer_question']}",
                f"- 재미 장치: {story['fun_mechanism']}",
                f"- 관계 역할: {', '.join(story['relationship_roles'])}",
                f"- 전환: {story['turn']}",
                f"- 결말: {story['payoff']['text']}",
                f"- 길이: {story['duration_target_seconds']:.1f}초",
                f"- BGM 분위기: {story['music_mood']}",
                f"- 과장 위험: {story['risk']['note']}",
                "",
                "### 기승전결",
                "",
                f"- 기: {story['narrative_arc']['setup']}",
                f"- 승: {story['narrative_arc']['build']}",
                f"- 전: {story['narrative_arc']['turn']}",
                f"- 결: {story['narrative_arc']['payoff']}",
                "",
                "### 비트",
                "",
            ]
        )
        for beat in story["beats"]:
            evidence = ", ".join(beat["observation_ids"])
            subject = f"[{beat['subject_label']}] " if beat.get("subject_label") else ""
            lines.append(
                f"- {beat['act']} / {beat['role']} {beat['source_start_seconds']:.2f}~{beat['source_end_seconds']:.2f}s: "
                f"{subject}{beat['caption']} · 강조 `{beat['emphasis_phrase']}` · 음악 {beat['music_cue']} ({evidence})"
            )
        lines.append("")
    lines.extend(["사용자가 1개 스토리를 명시적으로 선택한 뒤에만 compose와 render를 진행합니다.", ""])
    return "\n".join(lines)


def command_stories(args: argparse.Namespace) -> int:
    project_dir = Path(args.project_dir).expanduser().resolve()
    project, source = load_project(project_dir)
    if clean_text(project.get("status")) != "source_reviewed":
        fail("source_reviewed 상태에서만 스토리 3안을 등록할 수 있습니다.")
    analysis = require_object(read_json(project_dir / "source-analysis.json"), "source-analysis.json")
    _, media_entry = source_media(project_dir, source)
    source_duration = require_number(media_entry.get("probe", {}).get("duration_seconds"), "source duration", 0.01)
    input_payload = read_json(Path(args.input).expanduser().resolve())
    if isinstance(input_payload, list):
        values = input_payload
    else:
        values = require_object(input_payload, "스토리 입력").get("stories", [])
    values = require_list(values, "stories")
    if len(values) != 3:
        fail("통과 가능한 서로 다른 스토리안이 정확히 3개일 때만 등록할 수 있습니다.")
    visual_preset = project_visual_preset(project)
    stories = [
        normalize_story(value, index, analysis, source_duration, visual_preset)
        for index, value in enumerate(values)
    ]
    if len({item["id"] for item in stories}) != 3:
        fail("스토리 ID는 서로 달라야 합니다.")
    if len({item["fun_mechanism"] for item in stories}) != 3:
        fail("세 스토리안은 훅 문구만 바꾼 안이 아니라 서로 다른 재미 장치를 사용해야 합니다.")
    output_json = project_dir / "story-options.json"
    output_md = project_dir / "story-options.md"
    ensure_new([output_json, output_md], args.overwrite)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": now_iso(),
        "selection_required": True,
        "auto_selected": False,
        "stories": stories,
    }
    write_json(output_json, payload)
    output_md.write_text(stories_markdown(payload), encoding="utf-8")
    project["status"] = "stories_ready"
    project["updated_at"] = now_iso()
    project["story_options"] = {
        "json": "story-options.json",
        "markdown": "story-options.md",
        "count": 3,
    }
    write_json(project_dir / "project.json", project)
    print(
        json.dumps(
            {
                "status": project["status"],
                "stories": [
                    {
                        "id": item["id"],
                        "evidence_score": item["score"]["total"],
                        "fun_score": item["fun_score"]["total"],
                        "fun_mechanism": item["fun_mechanism"],
                    }
                    for item in stories
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def command_select_story(args: argparse.Namespace) -> int:
    project_dir = Path(args.project_dir).expanduser().resolve()
    project, _ = load_project(project_dir)
    if clean_text(project.get("status")) != "stories_ready":
        fail("stories_ready 상태에서만 사용자의 스토리 선택을 기록할 수 있습니다.")
    options = require_object(read_json(project_dir / "story-options.json"), "story-options.json")
    stories = require_list(options.get("stories"), "story-options.stories")
    selected = next((item for item in stories if clean_text(item.get("id")) == args.story_id), None)
    if not selected:
        fail(f"스토리 ID를 찾지 못했습니다: {args.story_id}")
    selection_path = project_dir / "selection.json"
    ensure_new([selection_path], args.overwrite)
    selection = {
        "schema_version": SCHEMA_VERSION,
        "story_id": args.story_id,
        "selected_at": now_iso(),
        "selected_by": "user",
        "note": clean_text(args.note),
        "auto_selected": False,
    }
    write_json(selection_path, selection)
    project["status"] = "story_selected"
    project["updated_at"] = now_iso()
    project["selections"]["story"] = {
        "confirmed": True,
        "story_id": args.story_id,
        "confirmed_at": selection["selected_at"],
    }
    project["draft_review"] = {
        "approved": False,
        "story_fit": "pending",
        "music_fit": "pending",
        "reviewed_at": "",
    }
    write_json(project_dir / "project.json", project)
    print(json.dumps({"status": project["status"], "selection": selection}, ensure_ascii=False, indent=2))
    return 0


def selected_story(project_dir: Path) -> dict[str, Any]:
    selection = require_object(read_json(project_dir / "selection.json"), "selection.json")
    story_id = require_text(selection.get("story_id"), "selection.story_id")
    options = require_object(read_json(project_dir / "story-options.json"), "story-options.json")
    for value in require_list(options.get("stories"), "story-options.stories"):
        story = require_object(value, "story-options.story")
        if clean_text(story.get("id")) == story_id:
            return story
    fail("선택 기록과 story-options.json이 일치하지 않습니다.")


def command_compose(args: argparse.Namespace) -> int:
    project_dir = Path(args.project_dir).expanduser().resolve()
    project, source = load_project(project_dir)
    if clean_text(project.get("status")) != "story_selected":
        fail("사용자가 스토리를 선택한 뒤에만 compose할 수 있습니다.")
    story = selected_story(project_dir)
    project_preset = project_visual_preset(project)
    visual_preset = normalize_visual_preset(
        story.get("visual_preset"),
        "selected story visual_preset",
        fallback=project_preset,
    )
    if visual_preset != project_preset:
        fail("선택 스토리와 프로젝트의 화면 프리셋이 일치하지 않습니다.")
    analysis = require_object(read_json(project_dir / "source-analysis.json"), "source-analysis.json")
    observations = {
        clean_text(item.get("id")): item
        for item in require_list(analysis.get("observations"), "source-analysis.observations")
        if isinstance(item, dict)
    }
    caption_regions = {
        clean_text(item.get("id")): item
        for item in require_list(analysis.get("source_caption", {}).get("regions", []), "source_caption.regions")
        if isinstance(item, dict)
    }
    script_path = project_dir / "script.json"
    storyboard_path = project_dir / "storyboard.json"
    music_path = project_dir / "music-plan.json"
    ensure_new([script_path, storyboard_path, music_path], args.overwrite)
    script_segments: list[dict[str, Any]] = []
    scenes: list[dict[str, Any]] = []
    music_segments: list[dict[str, Any]] = []
    sfx_events: list[dict[str, Any]] = []
    output_cursor = 0.0
    for index, beat_value in enumerate(require_list(story.get("beats"), "selected story beats"), start=1):
        beat = require_object(beat_value, f"beat {index}")
        evidence = [observations[item] for item in beat["observation_ids"]]
        confidence = "observed"
        if any(clean_text(item.get("confidence")) == "inference" for item in evidence):
            confidence = "inference"
        elif any(clean_text(item.get("confidence")) == "caregiver_report" for item in evidence):
            confidence = "caregiver_report"
        source_caption_region_id = clean_text(beat.get("source_caption_region_id"))
        edit_actions = ["no_scene_transition"]
        blur_region: dict[str, Any] | None = None
        if source_caption_region_id:
            if source_caption_region_id not in caption_regions:
                fail(f"등록되지 않은 자막 영역입니다: {source_caption_region_id}")
            edit_actions.append("source_caption_blur")
            blur_region = caption_regions[source_caption_region_id]
        if index == len(story["beats"]):
            edit_actions.append("hold_last_frame")
        segment = {
            "id": beat["id"],
            "role": beat["role"],
            "act": beat["act"],
            "caption": beat["caption"],
            "subject_label": clean_text(beat.get("subject_label")),
            "caption_style": beat["caption_style"],
            "emphasis_phrase": beat["emphasis_phrase"],
            "observation_ids": beat["observation_ids"],
            "evidence": [clean_text(item.get("visible_evidence")) for item in evidence],
        }
        scene = {
            "id": f"scene-{index:02d}-{beat['role']}",
            "role": beat["role"],
            "act": beat["act"],
            "fun_mechanism": story["fun_mechanism"],
            "source_clip_id": "primary",
            "source_start_seconds": beat["source_start_seconds"],
            "source_end_seconds": beat["source_end_seconds"],
            "source_clip_seconds": beat["source_clip_seconds"],
            "duration": beat["output_duration_seconds"],
            "headline": story["headline"],
            "caption": beat["caption"],
            "subject_label": clean_text(beat.get("subject_label")),
            "caption_style": beat["caption_style"],
            "emphasis_phrase": beat["emphasis_phrase"],
            "source_evidence": {
                "observation_ids": beat["observation_ids"],
                "visible_evidence": segment["evidence"],
            },
            "animal_emotion": {
                "label": beat["caption"],
                "confidence": confidence,
                "evidence": segment["evidence"],
                "music_mood": beat["music_mood"],
            },
            "focus_point": beat["focus_point"],
            "layout": "auto",
            "continuous_action": beat["continuous_action"],
            "visual_change_count": beat["visual_change_count"],
            "edit_actions": edit_actions,
            "hold_last_frame_seconds": round(beat["output_duration_seconds"] - beat["source_clip_seconds"], 3) if index == len(story["beats"]) else 0,
            "source_caption_region_id": source_caption_region_id,
            "source_caption_overrides": beat.get("source_caption_overrides", []),
        }
        if beat.get("source_caption_overrides"):
            scene["edit_actions"].append("source_caption_translation_override")
        if blur_region is not None:
            scene["source_caption_blur_region"] = blur_region
        script_segments.append(segment)
        scenes.append(scene)
        music_segments.append(
            {
                "scene_id": scene["id"],
                "act": beat["act"],
                "start_seconds": round(output_cursor, 3),
                "end_seconds": round(output_cursor + beat["output_duration_seconds"], 3),
                "profile_id": beat["music_mood"],
                "energy": ACT_DEFAULTS[beat["act"]]["energy"],
                "cue": beat["music_cue"],
                "impact": beat["music_cue"] == "impact",
                "source_audio_priority": beat["source_audio_priority"],
                "bgm_below_source_db": SOURCE_AUDIO_DUCK_DB[beat["source_audio_priority"]],
            }
        )
        for event in beat.get("sfx_events", []):
            sfx_events.append(
                {
                    "scene_id": scene["id"],
                    "type": event["type"],
                    "time_seconds": round(output_cursor + float(event["offset_seconds"]), 3),
                    "gain_db": event["gain_db"],
                }
            )
        output_cursor += beat["output_duration_seconds"]
    script = {
        "schema_version": SCHEMA_VERSION,
        "created_at": now_iso(),
        "story_id": story["id"],
        "story_model": {
            "subject": analysis["subjects"],
            "trigger": script_segments[0]["caption"],
            "action": [item["caption"] for item in script_segments[1:-2] or script_segments[1:2]],
            "reaction": script_segments[-2]["caption"] if len(script_segments) > 3 else script_segments[-1]["caption"],
            "resolution": story["payoff"]["text"],
        },
        "narrative_arc": story["narrative_arc"],
        "viewer_question": story["viewer_question"],
        "fun_mechanism": story["fun_mechanism"],
        "fun_score": story["fun_score"],
        "hook": story["hook"],
        "turn": story["turn"],
        "payoff": story["payoff"],
        "segments": script_segments,
        "audio": {
            "tts": False,
            "narration": False,
            "source_audio": True,
            "bgm": True,
            "sfx": bool(sfx_events),
        },
    }
    storyboard = {
        "schema_version": SCHEMA_VERSION,
        "created_at": now_iso(),
        "template_id": TEMPLATE_ID,
        "visual_preset": visual_preset,
        "story_id": story["id"],
        "archetype": story["archetype"],
        "narrative_arc": story["narrative_arc"],
        "viewer_question": story["viewer_question"],
        "fun_mechanism": story["fun_mechanism"],
        "fun_score": story["fun_score"],
        "duration_target_seconds": story["duration_target_seconds"],
        "scenes": scenes,
    }
    music_plan = {
        "schema_version": SCHEMA_VERSION,
        "mode": "synthetic_score_v2",
        "profile_id": story["music_mood"],
        "bpm": MOOD_BPM[story["music_mood"]],
        "vocals": False,
        "tts": False,
        "source_audio_primary": True,
        "bgm_below_source_db": 15,
        "fade_in_seconds": 0.08,
        "fade_out_seconds": 0.3,
        "segments": music_segments,
        "sfx": {
            "mode": "renderer_generated",
            "vocals": False,
            "events": sfx_events,
        },
        "target_lufs": -15,
        "true_peak_dbfs": -1,
        "license": {
            "name": "renderer-generated",
            "official_source_url": "",
            "attribution": "",
        },
    }
    write_json(script_path, script)
    write_json(storyboard_path, storyboard)
    write_json(music_path, music_plan)
    project["status"] = "composed"
    project["updated_at"] = now_iso()
    project["draft_review"] = {
        "approved": False,
        "story_fit": "pending",
        "music_fit": "pending",
        "reviewed_at": "",
    }
    project["composition"] = {
        "story_id": story["id"],
        "visual_preset": visual_preset,
        "script": "script.json",
        "storyboard": "storyboard.json",
        "music_plan": "music-plan.json",
    }
    write_json(project_dir / "project.json", project)
    print(json.dumps({"status": project["status"], "story_id": story["id"], "scenes": len(scenes)}, ensure_ascii=False, indent=2))
    return 0


def edit_plan_text(
    project: dict[str, Any],
    source: dict[str, Any],
    storyboard: dict[str, Any],
    music: dict[str, Any],
) -> str:
    lines = [
        "# Animal Viral Shorts 편집 계획",
        "",
        f"- 프로젝트: {project['project_id']}",
        f"- 스토리: {storyboard['story_id']} ({storyboard['archetype']})",
        f"- 템플릿: {storyboard['template_id']} / 720x1280 / 30fps",
        f"- 화면 프리셋: {clean_text(storyboard.get('visual_preset')) or LEGACY_VISUAL_PRESET}",
        f"- 원본: {clean_text(source.get('original_url')) or clean_text(source.get('original_local_path'))}",
        f"- 제작자: {source['creator']}",
        f"- 권리 상태: {source['rights']['status']}",
        f"- 오디오: 원본음 + {music['mode']} 비보컬 BGM + 비보컬 효과음, TTS 없음",
        f"- 시청자 질문: {clean_text(storyboard.get('viewer_question')) or '기존 v1 스토리'}",
        f"- 재미 장치: {clean_text(storyboard.get('fun_mechanism')) or '기존 v1 스토리'}",
        "",
    ]
    narrative_arc = storyboard.get("narrative_arc")
    if isinstance(narrative_arc, dict):
        lines.extend(
            [
                "## 기승전결",
                "",
                f"- 기: {clean_text(narrative_arc.get('setup'))}",
                f"- 승: {clean_text(narrative_arc.get('build'))}",
                f"- 전: {clean_text(narrative_arc.get('turn'))}",
                f"- 결: {clean_text(narrative_arc.get('payoff'))}",
                "",
            ]
        )
    lines.extend(["## 장면", ""])
    music_by_scene = {
        clean_text(item.get("scene_id")): item
        for item in require_list(music.get("segments", []), "music.segments")
        if isinstance(item, dict)
    }
    sfx_by_scene: dict[str, list[dict[str, Any]]] = {}
    for value in require_list(require_object(music.get("sfx", {"events": []}), "music.sfx").get("events", []), "music.sfx.events"):
        if isinstance(value, dict):
            sfx_by_scene.setdefault(clean_text(value.get("scene_id")), []).append(value)
    cursor = 0.0
    for scene_value in require_list(storyboard.get("scenes"), "storyboard.scenes"):
        scene = require_object(scene_value, "storyboard.scene")
        duration = float(scene["duration"])
        lines.extend(
            [
                f"### {scene['id']} — {cursor:.2f}~{cursor + duration:.2f}s",
                "",
                f"- 역할: {scene['role']}",
                f"- 기승전결: {clean_text(scene.get('act')) or 'legacy'}",
                f"- 원본: {scene['source_start_seconds']:.2f}~{scene['source_end_seconds']:.2f}s",
                f"- 관찰 대상: {clean_text(scene.get('subject_label')) or '표시 없음'}",
                f"- 자막: {scene['caption']}",
                f"- 자막 강조: {clean_text(scene.get('emphasis_phrase')) or '없음'} / {clean_text(scene.get('caption_style')) or 'legacy'}",
                f"- 근거: {', '.join(scene['source_evidence']['visible_evidence'])}",
                f"- 수정: {', '.join(scene['edit_actions'])}",
                f"- 초점: x={scene['focus_point']['x']:.2f}, y={scene['focus_point']['y']:.2f}",
                f"- 음악: {clean_text(music_by_scene.get(scene['id'], {}).get('profile_id')) or clean_text(music.get('profile_id'))} / "
                f"{clean_text(music_by_scene.get(scene['id'], {}).get('cue')) or 'legacy'} / "
                f"원본음 {clean_text(music_by_scene.get(scene['id'], {}).get('source_audio_priority')) or 'normal'} 우선",
                "",
            ]
        )
        for override in require_list(scene.get("source_caption_overrides", []), "scene.source_caption_overrides"):
            if isinstance(override, dict):
                lines.append(
                    f"- {clean_text(override.get('label')) or '원문 의역'}: "
                    f"{clean_text(override.get('source_text'))} → {clean_text(override.get('text'))} "
                    f"({float(override.get('start_seconds') or 0):.2f}~{float(override.get('end_seconds') or 0):.2f}s, 관찰 근거 아님)"
                )
        for event in sfx_by_scene.get(clean_text(scene.get("id")), []):
            lines.append(f"- 효과음: {clean_text(event.get('type'))} / 전체 {float(event.get('time_seconds') or 0):.2f}s")
        if scene.get("source_caption_overrides") or sfx_by_scene.get(clean_text(scene.get("id"))):
            lines.append("")
        cursor += duration
    lines.extend(
        [
            "## 검토 경계",
            "",
            "- 원본 제작자 워터마크는 유지한다.",
            "- 자막 블러는 source-analysis.json에서 보호 영역과 충돌하지 않은 영역만 사용한다.",
            "- 원문 번역·의역 카드는 영어 자막이 나타나는 검토 구간에만 표시하며 관찰 근거로 사용하지 않는다.",
            "- 이 편집 계획은 게시 권리, 공정 이용, 수익화 또는 조회수를 보장하지 않는다.",
            "",
        ]
    )
    return "\n".join(lines)


def command_edit_plan(args: argparse.Namespace) -> int:
    project_dir = Path(args.project_dir).expanduser().resolve()
    project, source = load_project(project_dir)
    if clean_text(project.get("status")) not in {"composed", "render_ready", "rendered_draft", "draft_approved", "rendered_local"}:
        fail("compose 후 편집 계획을 만들 수 있습니다.")
    storyboard = require_object(read_json(project_dir / "storyboard.json"), "storyboard.json")
    music = require_object(read_json(project_dir / "music-plan.json"), "music-plan.json")
    path = project_dir / "edit-plan.md"
    ensure_new([path], args.overwrite)
    path.write_text(edit_plan_text(project, source, storyboard, music), encoding="utf-8")
    project["edit_plan"] = {"relative_path": "edit-plan.md", "generated_at": now_iso()}
    project["updated_at"] = now_iso()
    write_json(project_dir / "project.json", project)
    print(json.dumps({"edit_plan": str(path)}, ensure_ascii=False, indent=2))
    return 0


def validate_blur_regions(analysis: dict[str, Any], scenes: list[Any]) -> list[str]:
    errors: list[str] = []
    protected_input = require_object(analysis.get("protected_regions", {}), "source-analysis.protected_regions")
    protected: list[tuple[str, dict[str, float]]] = []
    for key in ("watermarks", "animal_faces", "human_faces"):
        for index, item in enumerate(require_list(protected_input.get(key, []), f"protected_regions.{key}")):
            protected.append((key, normalized_region(item, f"protected_regions.{key}[{index}]")))
    for index, scene_value in enumerate(scenes):
        scene = require_object(scene_value, f"scene[{index}]")
        actions = require_list(scene.get("edit_actions", []), f"scene[{index}].edit_actions")
        if "source_caption_blur" not in actions:
            continue
        try:
            region = normalized_region(scene.get("source_caption_blur_region"), f"scene[{index}].source_caption_blur_region")
        except AnimalViralShortsError as exc:
            errors.append(str(exc))
            continue
        for protected_type, protected_region in protected:
            if regions_overlap(region, protected_region):
                errors.append(f"scene[{index}] 자막 블러가 보호 영역 {protected_type}와 겹칩니다.")
    return errors


def validate_music(
    project_dir: Path,
    music: dict[str, Any],
    rights: dict[str, Any],
    scenes: list[Any],
) -> list[str]:
    errors: list[str] = []
    mode = clean_text(music.get("mode"))
    if mode not in {"synthetic_ambient", "synthetic_score_v2", "licensed_track"}:
        errors.append("music-plan.mode는 synthetic_score_v2, synthetic_ambient 또는 licensed_track이어야 합니다.")
        return errors
    if music.get("vocals") is not False or music.get("tts") is not False:
        errors.append("보컬, TTS 또는 내레이션 음악 설정은 허용되지 않습니다.")
    sfx = require_object(music.get("sfx", {"mode": "renderer_generated", "vocals": False, "events": []}), "music-plan.sfx")
    if clean_text(sfx.get("mode")) != "renderer_generated" or sfx.get("vocals") is not False:
        errors.append("효과음은 renderer_generated 비보컬 모드여야 합니다.")
    total_duration = sum(float(require_object(item, "scene").get("duration") or 0) for item in scenes)
    scene_ids_for_sfx = {clean_text(require_object(item, "scene").get("id")) for item in scenes}
    for index, value in enumerate(require_list(sfx.get("events", []), "music-plan.sfx.events")):
        try:
            event = require_object(value, f"music-plan.sfx.events[{index}]")
            if require_text(event.get("type"), f"sfx event[{index}].type") not in SFX_TYPES:
                errors.append(f"sfx event[{index}] 효과음 유형이 지원되지 않습니다.")
            if require_text(event.get("scene_id"), f"sfx event[{index}].scene_id") not in scene_ids_for_sfx:
                errors.append(f"sfx event[{index}] 장면 ID가 스토리보드에 없습니다.")
            require_number(event.get("time_seconds"), f"sfx event[{index}].time_seconds", 0, total_duration)
            require_number(event.get("gain_db"), f"sfx event[{index}].gain_db", -24, 0)
        except AnimalViralShortsError as exc:
            errors.append(str(exc))
    if mode in {"synthetic_ambient", "synthetic_score_v2"}:
        if clean_text(music.get("profile_id")) not in MUSIC_MOODS:
            errors.append("지원하지 않는 생성 BGM 분위기입니다.")
    if mode == "synthetic_score_v2" or clean_text(music.get("schema_version")).startswith("2"):
        segments = require_list(music.get("segments"), "music-plan.segments")
        scene_ids = [clean_text(require_object(item, "scene").get("id")) for item in scenes]
        if len(segments) != len(scene_ids):
            errors.append("장면별 음악 구간은 모든 장면과 정확히 하나씩 대응해야 합니다.")
        segment_ids: list[str] = []
        cursor = 0.0
        for index, value in enumerate(segments):
            try:
                segment = require_object(value, f"music-plan.segments[{index}]")
                scene_id = require_text(segment.get("scene_id"), f"music segment[{index}].scene_id")
                segment_ids.append(scene_id)
                act = require_text(segment.get("act"), f"music segment[{index}].act")
                if act not in NARRATIVE_ACTS:
                    errors.append(f"music segment[{index}] 기승전결 역할이 올바르지 않습니다.")
                if clean_text(segment.get("profile_id")) not in MUSIC_MOODS:
                    errors.append(f"music segment[{index}] 분위기가 지원되지 않습니다.")
                if clean_text(segment.get("cue")) not in MUSIC_CUES:
                    errors.append(f"music segment[{index}] 큐가 지원되지 않습니다.")
                elif act in ACT_MUSIC_CUES and clean_text(segment.get("cue")) not in ACT_MUSIC_CUES[act]:
                    errors.append(f"music segment[{index}] 큐가 {act} 장면과 대응하지 않습니다.")
                if clean_text(segment.get("source_audio_priority")) not in SOURCE_AUDIO_PRIORITIES:
                    errors.append(f"music segment[{index}] 원본음 우선순위가 올바르지 않습니다.")
                start = require_number(segment.get("start_seconds"), f"music segment[{index}].start_seconds", 0)
                end = require_number(segment.get("end_seconds"), f"music segment[{index}].end_seconds", start + 0.01)
                require_number(segment.get("energy"), f"music segment[{index}].energy", 0, 1)
                require_number(segment.get("bgm_below_source_db"), f"music segment[{index}].bgm_below_source_db", 10, 24)
                if abs(start - cursor) > 0.05:
                    errors.append(f"music segment[{index}] 시작 시점이 앞 구간과 이어지지 않습니다.")
                cursor = end
            except AnimalViralShortsError as exc:
                errors.append(str(exc))
        if segment_ids != scene_ids:
            errors.append("장면과 음악 구간의 순서 또는 ID가 일치하지 않습니다.")
        if mode == "synthetic_score_v2":
            return errors
    if mode == "synthetic_ambient":
        return errors
    track = music.get("track")
    if not isinstance(track, dict):
        errors.append("licensed_track에는 track 객체가 필요합니다.")
        return errors
    for key in ("relative_path", "title", "creator", "official_source_url", "license_name", "license_url", "attribution", "sha256"):
        if not clean_text(track.get(key)):
            errors.append(f"music-plan.track.{key}가 필요합니다.")
    if errors:
        return errors
    try:
        path = safe_project_path(project_dir, track["relative_path"], exists=True)
    except AnimalViralShortsError as exc:
        errors.append(str(exc))
        return errors
    if sha256_file(path) != track["sha256"]:
        errors.append("라이선스 음원 SHA-256이 현재 파일과 일치하지 않습니다.")
    matching_asset = next(
        (
            item
            for item in require_list(rights.get("assets", []), "rights.assets")
            if isinstance(item, dict) and clean_text(item.get("relative_path")) == track["relative_path"]
        ),
        None,
    )
    if not matching_asset:
        errors.append("라이선스 음원이 rights-manifest.json에 등록되지 않았습니다.")
    return errors


def validate_project(project_dir: Path, *, final: bool) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        project, source = load_project(project_dir)
    except AnimalViralShortsError as exc:
        return [str(exc)], warnings
    try:
        project_preset = project_visual_preset(project)
    except AnimalViralShortsError as exc:
        errors.append(str(exc))
        project_preset = LEGACY_VISUAL_PRESET
    rights_status = clean_text(source.get("rights", {}).get("status"))
    if rights_status not in RIGHTS_STATUSES:
        errors.append("지원하지 않는 원본 권리 상태입니다.")
    if rights_status == "not_permitted":
        errors.append("not_permitted 소스는 렌더링할 수 없습니다.")
    if rights_status in LOCAL_REVIEW_RIGHTS:
        warnings.append("권리 불명 소스이므로 개인 로컬 검토용으로만 취급합니다.")
    if project.get("publication", {}).get("supported") is not False:
        errors.append("MVP는 외부 게시를 지원하지 않아야 합니다.")
    try:
        media_path, media_entry = source_media(project_dir, source)
        if clean_text(media_entry.get("sha256")) != sha256_file(media_path):
            errors.append("등록된 원본 SHA-256과 현재 파일이 일치하지 않습니다.")
        source_duration = require_number(media_entry.get("probe", {}).get("duration_seconds"), "source duration", 0.01)
    except AnimalViralShortsError as exc:
        errors.append(str(exc))
        source_duration = 0.0
    if not final:
        return errors, warnings
    if clean_text(project.get("status")) not in {"composed", "render_ready", "rendered_draft", "draft_approved", "rendered_local"}:
        errors.append("최종 검증에는 composed 상태가 필요합니다.")
    required_names = (
        "source-analysis.json",
        "story-options.json",
        "selection.json",
        "script.json",
        "storyboard.json",
        "music-plan.json",
        "rights-manifest.json",
    )
    payloads: dict[str, dict[str, Any]] = {}
    for name in required_names:
        try:
            payloads[name] = require_object(read_json(project_dir / name), name)
        except AnimalViralShortsError as exc:
            errors.append(str(exc))
    if any(name not in payloads for name in required_names):
        return errors, warnings
    analysis = payloads["source-analysis.json"]
    story_options = payloads["story-options.json"]
    selection = payloads["selection.json"]
    script = payloads["script.json"]
    storyboard = payloads["storyboard.json"]
    music = payloads["music-plan.json"]
    rights = payloads["rights-manifest.json"]
    try:
        storyboard_preset = normalize_visual_preset(
            storyboard.get("visual_preset"),
            "storyboard.visual_preset",
            fallback=LEGACY_VISUAL_PRESET,
        )
    except AnimalViralShortsError as exc:
        errors.append(str(exc))
        storyboard_preset = LEGACY_VISUAL_PRESET
    if storyboard_preset != project_preset:
        errors.append("프로젝트와 스토리보드의 화면 프리셋이 일치하지 않습니다.")
    storyboard_v2 = clean_text(storyboard.get("schema_version")).startswith("2") or isinstance(storyboard.get("narrative_arc"), dict)
    stories = require_list(story_options.get("stories"), "story-options.stories")
    if len(stories) != 3:
        errors.append("스토리 옵션은 정확히 3개여야 합니다.")
    story_id = clean_text(selection.get("story_id"))
    selected_story_value = next(
        (item for item in stories if isinstance(item, dict) and clean_text(item.get("id")) == story_id),
        None,
    )
    if not story_id or selected_story_value is None:
        errors.append("사용자가 선택한 스토리가 story-options.json에 없습니다.")
    else:
        try:
            selected_story_preset = normalize_visual_preset(
                selected_story_value.get("visual_preset"),
                "selected story visual_preset",
                fallback=LEGACY_VISUAL_PRESET,
            )
            if selected_story_preset != storyboard_preset:
                errors.append("선택 스토리와 스토리보드의 화면 프리셋이 일치하지 않습니다.")
        except AnimalViralShortsError as exc:
            errors.append(str(exc))
    if selection.get("auto_selected") is not False or clean_text(selection.get("selected_by")) != "user":
        errors.append("스토리 선택은 자동 선택이 아니라 사용자 선택이어야 합니다.")
    audio = require_object(script.get("audio", {}), "script.audio")
    if audio.get("tts") is not False or audio.get("narration") is not False:
        errors.append("TTS와 내레이션은 비활성화되어야 합니다.")
    if any(key in script for key in ("narration_audio", "tts_audio", "voiceover")):
        errors.append("대본에 내레이션 또는 TTS 오디오가 포함되어 있습니다.")
    scenes = require_list(storyboard.get("scenes"), "storyboard.scenes")
    if storyboard_v2 and not 4 <= len(scenes) <= 12:
        errors.append("v2 스토리보드는 기승전결을 구성하는 4~12개 장면이어야 합니다.")
    if not storyboard_v2 and not 3 <= len(scenes) <= 6:
        errors.append("기존 v1 스토리보드 장면은 3~6개여야 합니다.")
    total_duration = 0.0
    source_seconds_total = 0.0
    turn_start: float | None = None
    scene_acts: list[str] = []
    reviewed_subjects = [
        clean_text(item)
        for item in analysis.get("subjects", [])
        if clean_text(item)
    ]
    observation_subjects = {
        clean_text(item.get("id")): clean_text(item.get("subject"))
        for item in analysis.get("observations", [])
        if isinstance(item, dict) and clean_text(item.get("id"))
    }
    for index, scene_value in enumerate(scenes):
        try:
            scene = require_object(scene_value, f"scene[{index}]")
            role = require_text(scene.get("role"), f"scene[{index}].role")
            duration = require_number(scene.get("duration"), f"scene[{index}].duration", 0.25, 9.5)
            source_seconds = require_number(scene.get("source_clip_seconds"), f"scene[{index}].source_clip_seconds", 0.01, 8)
            source_start = require_number(scene.get("source_start_seconds"), f"scene[{index}].source_start_seconds", 0)
            source_end = require_number(scene.get("source_end_seconds"), f"scene[{index}].source_end_seconds", source_start)
            if abs((source_end - source_start) - source_seconds) > 0.05:
                errors.append(f"scene[{index}] 원본 구간 길이가 source_clip_seconds와 일치하지 않습니다.")
            if source_duration and source_end > source_duration + 0.05:
                errors.append(f"scene[{index}] 원본 구간이 영상 길이를 넘습니다.")
            if duration > 5 and (not bool(scene.get("continuous_action")) or int(scene.get("visual_change_count", 0)) < 2):
                errors.append(f"scene[{index}] 5초 초과 장면에는 연속 행동과 2회 이상 시각 변화가 필요합니다.")
            caption = require_text(scene.get("caption"), f"scene[{index}].caption")
            if len(caption) > 26:
                warnings.append(f"scene[{index}] 자막이 권장 26자를 넘습니다.")
            evidence = require_object(scene.get("source_evidence"), f"scene[{index}].source_evidence")
            scene_observation_ids = require_list(
                evidence.get("observation_ids"),
                f"scene[{index}].source_evidence.observation_ids",
            )
            if not scene_observation_ids:
                errors.append(f"scene[{index}]에 관찰 근거가 없습니다.")
            if storyboard_preset == DEFAULT_VISUAL_PRESET:
                subject_label = normalize_subject_label(
                    scene.get("subject_label"),
                    f"scene[{index}].subject_label",
                    required=True,
                )
                grounded_subjects = reviewed_subjects + [
                    observation_subjects.get(clean_text(observation_id), "")
                    for observation_id in scene_observation_ids
                ]
                if not subject_label_is_grounded(subject_label, grounded_subjects):
                    errors.append(f"scene[{index}].subject_label이 검토된 관찰 대상과 연결되지 않습니다.")
                duration_limit = 4.0 if index == len(scenes) - 1 else 3.0
                if duration > duration_limit:
                    errors.append(f"scene[{index}] 관찰 대비형 장면은 {duration_limit:.0f}초를 넘을 수 없습니다.")
            emotion = require_object(scene.get("animal_emotion"), f"scene[{index}].animal_emotion")
            if clean_text(emotion.get("confidence")) not in EMOTION_CONFIDENCE:
                errors.append(f"scene[{index}] 감정 근거 수준이 올바르지 않습니다.")
            if not require_list(emotion.get("evidence"), f"scene[{index}].animal_emotion.evidence"):
                errors.append(f"scene[{index}] 감정 표현에 실제 행동 근거가 없습니다.")
            if storyboard_v2:
                act = require_text(scene.get("act"), f"scene[{index}].act")
                if act not in NARRATIVE_ACTS:
                    errors.append(f"scene[{index}] 기승전결 역할이 올바르지 않습니다.")
                else:
                    scene_acts.append(act)
                caption_style = require_text(scene.get("caption_style"), f"scene[{index}].caption_style")
                if caption_style not in CAPTION_STYLES:
                    errors.append(f"scene[{index}] 하단 메시지 스타일이 올바르지 않습니다.")
                elif act in ACT_DEFAULTS and caption_style != ACT_DEFAULTS[act]["caption_style"]:
                    errors.append(f"scene[{index}] 하단 메시지 스타일이 {act} 역할과 대응하지 않습니다.")
                emphasis = require_text(scene.get("emphasis_phrase"), f"scene[{index}].emphasis_phrase")
                if emphasis not in caption:
                    errors.append(f"scene[{index}] 강조 문구가 자막에 포함되지 않습니다.")
            overrides = require_list(scene.get("source_caption_overrides", []), f"scene[{index}].source_caption_overrides")
            actions = require_list(scene.get("edit_actions", []), f"scene[{index}].edit_actions")
            if overrides and "source_caption_translation_override" not in actions:
                errors.append(f"scene[{index}] 번역 오버라이드 수정 기록이 없습니다.")
            for override_index, value in enumerate(overrides):
                source_caption_override(value, f"scene[{index}].source_caption_overrides[{override_index}]", duration)
            if (role == "turn" or clean_text(scene.get("act")) == "turn") and turn_start is None:
                turn_start = total_duration
            total_duration += duration
            source_seconds_total += source_seconds
        except AnimalViralShortsError as exc:
            errors.append(str(exc))
    if scenes:
        first = require_object(scenes[0], "scene[0]")
        last = require_object(scenes[-1], "scene[-1]")
        if clean_text(first.get("role")) != "hook":
            errors.append("첫 장면은 hook이어야 합니다.")
        if clean_text(last.get("role")) not in {"payoff", "conclusion"}:
            errors.append("마지막 장면은 실제 payoff 또는 conclusion이어야 합니다.")
        actions = require_list(last.get("edit_actions", []), "last scene edit_actions")
        hold = float(last.get("hold_last_frame_seconds") or 0)
        if "hold_last_frame" not in actions or not 0.5 <= hold <= 1.0:
            errors.append("마지막 장면은 실제 최종 프레임을 0.5~1초 유지해야 합니다.")
    if not 0 < total_duration <= MAX_SHORT_SECONDS:
        errors.append(f"최종 길이는 59.5초 이하여야 합니다: {total_duration:.2f}초")
    target = float(storyboard.get("duration_target_seconds") or 0)
    if abs(total_duration - target) > 0.75:
        errors.append("스토리보드 장면 합계와 목표 길이 차이는 0.75초 이하여야 합니다.")
    if turn_start is None:
        errors.append("스토리보드에 명시적인 turn 장면이 필요합니다.")
    elif total_duration and turn_start > total_duration * 0.75:
        errors.append("전환 또는 재훅은 전체 길이의 75% 이전에 시작해야 합니다.")
    if storyboard_v2:
        if set(scene_acts) != set(NARRATIVE_ACTS):
            errors.append("v2 스토리보드에는 setup, build, turn, payoff가 모두 필요합니다.")
        elif [NARRATIVE_ACTS.index(act) for act in scene_acts] != sorted(NARRATIVE_ACTS.index(act) for act in scene_acts):
            errors.append("v2 스토리보드의 기승전결 순서가 뒤바뀌었습니다.")
        narrative_arc = require_object(storyboard.get("narrative_arc"), "storyboard.narrative_arc")
        for act in NARRATIVE_ACTS:
            if not clean_text(narrative_arc.get(act)):
                errors.append(f"storyboard.narrative_arc.{act}가 필요합니다.")
        fun_score = require_object(storyboard.get("fun_score"), "storyboard.fun_score")
        if float(fun_score.get("total") or 0) < 75:
            errors.append("선택 스토리의 재미 점수는 75점 이상이어야 합니다.")
    if rights_status in LOCAL_REVIEW_RIGHTS:
        if source_seconds_total > 18.0001:
            errors.append("권리 불명 소스의 원본 사용 총합은 18초를 넘을 수 없습니다.")
        if source_duration and source_seconds_total >= source_duration * 0.9:
            errors.append("권리 불명 소스를 사실상 전체 재업로드하는 구성은 허용되지 않습니다.")
    errors.extend(validate_blur_regions(analysis, scenes))
    errors.extend(validate_music(project_dir, music, rights, scenes))
    return errors, warnings


def command_validate(args: argparse.Namespace) -> int:
    project_dir = Path(args.project_dir).expanduser().resolve()
    errors, warnings = validate_project(project_dir, final=args.final)
    result = {
        "ok": not errors,
        "final": bool(args.final),
        "errors": errors,
        "warnings": warnings,
        "proof_boundary": {
            "source_and_schema": not errors,
            "visual_truth": "human-reviewed source-analysis.json",
            "rights": "recorded, not legally adjudicated",
            "publication": False,
            "performance_prediction": False,
        },
    }
    if not errors and args.final:
        project, _ = load_project(project_dir)
        if clean_text(project.get("status")) in {"composed", "render_ready"}:
            project["status"] = "render_ready"
            project["updated_at"] = now_iso()
            project["final_validation"] = {"validated_at": project["updated_at"], "ok": True}
            write_json(project_dir / "project.json", project)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


def fitted_font(draw: Any, text: str, maximum_width: int, start: int, minimum: int) -> Any:
    from PIL import ImageFont

    font_path = find_font()
    for size in range(start, minimum - 1, -2):
        font = ImageFont.truetype(str(font_path), size)
        box = draw.textbbox((0, 0), text, font=font)
        if box[2] - box[0] <= maximum_width:
            return font
    return ImageFont.truetype(str(font_path), minimum)


def wrap_caption(draw: Any, text: str, font: Any, maximum_width: int, maximum_lines: int = 2) -> list[str]:
    if not text:
        return [""]
    lines: list[str] = []
    current = ""
    for character in text:
        proposal = current + character
        width = draw.textbbox((0, 0), proposal, font=font)[2]
        if current and width > maximum_width:
            lines.append(current)
            current = character
        else:
            current = proposal
    if current:
        lines.append(current)
    if len(lines) > maximum_lines:
        lines = lines[:maximum_lines]
        final = lines[-1]
        while final and draw.textbbox((0, 0), final + "…", font=font)[2] > maximum_width:
            final = final[:-1]
        lines[-1] = final.rstrip() + "…"
    return lines


def draw_centered(draw: Any, text: str, y: int, font: Any, fill: str, maximum_width: int = 600) -> int:
    lines = wrap_caption(draw, text, font, maximum_width)
    line_height = font.size + 8
    for offset, line in enumerate(lines):
        box = draw.textbbox((0, 0), line, font=font)
        width = box[2] - box[0]
        draw.text(((CANVAS_WIDTH - width) / 2, y + offset * line_height), line, font=font, fill=fill)
    return y + len(lines) * line_height


def draw_mixed_centered(
    draw: Any,
    text: str,
    accent: str,
    y: int,
    font: Any,
    *,
    normal_fill: str = "#141414",
    accent_fill: str = "#C94F3D",
    maximum_width: int = 600,
) -> None:
    if not accent or accent not in text:
        draw_centered(draw, text, y, font, normal_fill, maximum_width)
        return
    before, after = text.split(accent, 1)
    parts = [(before, normal_fill), (accent, accent_fill), (after, normal_fill)]
    widths = [draw.textbbox((0, 0), part, font=font)[2] for part, _ in parts]
    x = (CANVAS_WIDTH - sum(widths)) / 2
    for (part, color), width in zip(parts, widths):
        draw.text((x, y), part, font=font, fill=color)
        x += width


def draw_mixed_left(
    draw: Any,
    text: str,
    accent: str,
    x: int,
    y: int,
    font: Any,
    *,
    normal_fill: str,
    accent_fill: str,
) -> None:
    if not accent or accent not in text:
        draw.text((x, y), text, font=font, fill=normal_fill)
        return
    before, after = text.split(accent, 1)
    for part, color in ((before, normal_fill), (accent, accent_fill), (after, normal_fill)):
        draw.text((x, y), part, font=font, fill=color)
        box = draw.textbbox((0, 0), part, font=font)
        x += box[2] - box[0]


def draw_footer_message(draw: Any, scene: dict[str, Any]) -> None:
    caption = require_text(scene.get("caption"), "scene.caption")
    style = clean_text(scene.get("caption_style"))
    if style not in CAPTION_STYLES:
        style = {
            "hook": "question",
            "turn": "turn",
            "payoff": "payoff",
            "conclusion": "payoff",
        }.get(clean_text(scene.get("role")), "buildup")
    emphasis = clean_text(scene.get("emphasis_phrase"))
    if emphasis not in caption:
        emphasis = ""
    font_range = {
        "question": (46, 34),
        "buildup": (44, 32),
        "turn": (48, 34),
        "payoff": (52, 36),
    }
    start_size, minimum_size = font_range[style]
    caption_font = fitted_font(draw, caption, 540, start_size, minimum_size)
    caption_lines = wrap_caption(draw, caption, caption_font, 540)
    line_height = caption_font.size + 4
    total_height = len(caption_lines) * line_height
    caption_y = FOOTER_TOP + max(4, (96 - total_height) // 2)
    normal_fill = "#141414"
    accent_fill = "#C94F3D"
    if style == "payoff":
        draw.rounded_rectangle((64, FOOTER_TOP + 7, 630, BOTTOM_SAFE_TOP - 7), radius=18, fill="#141414")
        normal_fill = "#F5F1EA"
        accent_fill = "#F07B67"
    elif style == "turn":
        draw.rounded_rectangle((64, FOOTER_TOP + 8, 630, BOTTOM_SAFE_TOP - 8), radius=16, fill="#ECD8D2")
    elif style == "question":
        draw.rounded_rectangle((64, FOOTER_TOP + 8, 70, BOTTOM_SAFE_TOP - 8), radius=3, fill="#C94F3D")
    else:
        draw.rectangle((90, FOOTER_TOP + 8, 630, FOOTER_TOP + 12), fill="#D9D1C7")
    for line_index, line in enumerate(caption_lines):
        line_accent = emphasis if emphasis and emphasis in line else ""
        draw_mixed_centered(
            draw,
            line,
            line_accent,
            caption_y + line_index * line_height,
            caption_font,
            normal_fill=normal_fill,
            accent_fill=accent_fill,
            maximum_width=540,
        )


def observation_subject_color(subject_label: str) -> str:
    palette = ("#315B70", "#7A3E48", "#5F6241", "#604B78")
    digest = hashlib.sha256(subject_label.encode("utf-8")).digest()
    return palette[digest[0] % len(palette)]


def draw_observation_contrast_footer(draw: Any, scene: dict[str, Any]) -> None:
    caption = require_text(scene.get("caption"), "scene.caption")
    subject_label = normalize_subject_label(
        scene.get("subject_label"),
        "scene.subject_label",
        required=True,
    )
    style = clean_text(scene.get("caption_style"))
    if style not in CAPTION_STYLES:
        style = {
            "hook": "question",
            "turn": "turn",
            "payoff": "payoff",
            "conclusion": "payoff",
        }.get(clean_text(scene.get("role")), "buildup")
    emphasis = clean_text(scene.get("emphasis_phrase"))
    if emphasis not in caption:
        emphasis = ""
    card_fill = {
        "question": "#FFFFFF",
        "buildup": "#FFF1B8",
        "turn": "#F4D9D2",
        "payoff": "#141414",
    }[style]
    normal_fill = "#F7F4ED" if style == "payoff" else "#141414"
    accent_fill = {
        "question": "#C94F3D",
        "buildup": "#8A5B00",
        "turn": "#B83C2F",
        "payoff": "#F2C94C",
    }[style]
    draw.rounded_rectangle((42, FOOTER_TOP + 7, 630, BOTTOM_SAFE_TOP - 7), radius=15, fill=card_fill)
    draw.rounded_rectangle((42, FOOTER_TOP + 7, 48, BOTTOM_SAFE_TOP - 7), radius=3, fill=accent_fill)

    label_font = fitted_font(draw, subject_label, 112, 26, 20)
    label_box = draw.textbbox((0, 0), subject_label, font=label_font)
    label_width = min(142, max(86, label_box[2] - label_box[0] + 24))
    label_left = 56
    label_right = label_left + label_width
    draw.rounded_rectangle(
        (label_left, FOOTER_TOP + 23, label_right, BOTTOM_SAFE_TOP - 23),
        radius=12,
        fill=observation_subject_color(subject_label),
    )
    label_x = label_left + (label_width - (label_box[2] - label_box[0])) / 2
    label_y = FOOTER_TOP + (96 - label_font.size) / 2 - 2
    draw.text((label_x, label_y), subject_label, font=label_font, fill="#FFFFFF")

    caption_x = label_right + 16
    maximum_width = 614 - caption_x
    caption_font = fitted_font(draw, caption, maximum_width, 38, 28)
    caption_lines = wrap_caption(draw, caption, caption_font, maximum_width)
    line_height = caption_font.size + 3
    caption_y = FOOTER_TOP + max(4, (96 - len(caption_lines) * line_height) // 2)
    for line_index, line in enumerate(caption_lines):
        line_accent = emphasis if emphasis and emphasis in line else ""
        draw_mixed_left(
            draw,
            line,
            line_accent,
            caption_x,
            caption_y + line_index * line_height,
            caption_font,
            normal_fill=normal_fill,
            accent_fill=accent_fill,
        )


def make_overlay(
    project_dir: Path,
    scene: dict[str, Any],
    source: dict[str, Any],
    path: Path,
    *,
    draft: bool,
    visual_preset: str,
) -> None:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as exc:
        raise AnimalViralShortsError("렌더링에는 Pillow가 필요합니다.") from exc
    image = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    headline = require_object(scene.get("headline"), "scene.headline")
    line1 = require_text(headline.get("line1"), "scene.headline.line1")
    line2 = require_text(headline.get("line2"), "scene.headline.line2")
    accent = require_text(headline.get("accent_phrase"), "scene.headline.accent_phrase")
    if visual_preset == DEFAULT_VISUAL_PRESET:
        draw.rectangle((0, 0, CANVAS_WIDTH, VIDEO_TOP), fill="#FFFDF8")
        draw.rectangle((0, FOOTER_TOP, CANVAS_WIDTH, CANVAS_HEIGHT), fill="#FFFDF8")
        title_font_1 = fitted_font(draw, line1, 600, 54, 38)
        title_font_2 = fitted_font(draw, line2, 600, 54, 38)
        draw_mixed_centered(draw, line1, accent, 84, title_font_1, accent_fill="#C43C2D")
        draw_mixed_centered(draw, line2, accent, 150, title_font_2, accent_fill="#C43C2D")
        draw.rounded_rectangle((278, 230, 442, 237), radius=4, fill="#F2C94C")
        draw_observation_contrast_footer(draw, scene)
    else:
        draw.rectangle((0, 0, CANVAS_WIDTH, VIDEO_TOP), fill="#F5F1EA")
        draw.rectangle((0, FOOTER_TOP, CANVAS_WIDTH, CANVAS_HEIGHT), fill="#F5F1EA")
        title_font_1 = fitted_font(draw, line1, 600, 48, 36)
        title_font_2 = fitted_font(draw, line2, 600, 48, 36)
        draw_mixed_centered(draw, line1, accent, 92, title_font_1)
        draw_mixed_centered(draw, line2, accent, 156, title_font_2)
        draw_footer_message(draw, scene)
    credit = " · ".join(filter(None, (clean_text(source.get("creator")), clean_text(source.get("platform")).replace("_", " "))))
    if credit:
        credit_font = ImageFont.truetype(str(find_font()), 18)
        box = draw.textbbox((0, 0), credit, font=credit_font)
        draw.rounded_rectangle((12, 994, 24 + box[2], 1026), radius=6, fill=(20, 20, 20, 150))
        draw.text((18, 998), credit, font=credit_font, fill="white")
    image.save(path, format="PNG", optimize=True)


def make_translation_overlay(override: dict[str, Any], path: Path) -> None:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as exc:
        raise AnimalViralShortsError("렌더링에는 Pillow가 필요합니다.") from exc
    image = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    region = normalized_region(override.get("canvas_region"), "source_caption_override.canvas_region")
    x = round(region["x"] * CANVAS_WIDTH)
    y = round(region["y"] * CANVAS_HEIGHT)
    width = round(region["width"] * CANVAS_WIDTH)
    height = round(region["height"] * CANVAS_HEIGHT)
    draw.rounded_rectangle((x, y, x + width, y + height), radius=12, fill=(20, 20, 20, 255))
    label_font = ImageFont.truetype(str(find_font()), 15)
    draw.text((x + 12, y + 7), clean_text(override.get("label")) or "원문 의역", font=label_font, fill="#F07B67")
    text = require_text(override.get("text"), "source_caption_override.text")
    text_font = fitted_font(draw, text, width - 24, 29, 21)
    lines = wrap_caption(draw, text, text_font, width - 24, maximum_lines=2)
    line_height = text_font.size + 3
    text_y = y + 27
    for index, line in enumerate(lines):
        draw.text((x + 12, text_y + index * line_height), line, font=text_font, fill="#FFFFFF")
    image.save(path, format="PNG", optimize=True)


def blur_prefix(scene: dict[str, Any], probe: dict[str, Any]) -> tuple[str, str]:
    actions = require_list(scene.get("edit_actions", []), "scene.edit_actions")
    if "source_caption_blur" not in actions:
        return "[0:v]null[clean];", "[clean]"
    region = normalized_region(scene.get("source_caption_blur_region"), "scene.source_caption_blur_region")
    requested_radius = int(region.get("radius", 20))
    patch_width = float(probe["width"]) * region["width"]
    patch_height = float(probe["height"]) * region["height"]
    radius = max(1, min(requested_radius, int(min(patch_width, patch_height) / 2) - 1))
    prefix = (
        "[0:v]split=2[base0][blur0];"
        f"[blur0]crop=w=iw*{region['width']}:h=ih*{region['height']}:"
        f"x=iw*{region['x']}:y=ih*{region['y']},"
        f"boxblur=luma_radius={radius}:luma_power=1[patch];"
        f"[base0][patch]overlay=x=main_w*{region['x']}:y=main_h*{region['y']}[clean];"
    )
    return prefix, "[clean]"


def video_filter(
    scene: dict[str, Any],
    probe: dict[str, Any],
    padding_seconds: float,
) -> str:
    prefix, clean = blur_prefix(scene, probe)
    focus = require_object(scene.get("focus_point"), "scene.focus_point")
    focus_x = require_number(focus.get("x"), "focus_point.x", 0, 1)
    focus_y = require_number(focus.get("y"), "focus_point.y", 0, 1)
    width = require_number(probe.get("width"), "source width", 1)
    height = require_number(probe.get("height"), "source height", 1)
    ratio = width / height
    tail = f",fps=30,tpad=stop_mode=clone:stop_duration={padding_seconds:.3f},setpts=PTS-STARTPTS"
    if ratio <= 0.8:
        transform = (
            f"{clean}scale={CANVAS_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=increase,"
            f"crop={CANVAS_WIDTH}:{VIDEO_HEIGHT}:"
            f"x=(in_w-out_w)*{focus_x:.4f}:y=(in_h-out_h)*{focus_y:.4f}"
            f"{tail}[content];"
        )
    else:
        transform = (
            f"{clean}split=2[widebg][widefg];"
            f"[widebg]scale={CANVAS_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=increase,"
            f"crop={CANVAS_WIDTH}:{VIDEO_HEIGHT},boxblur=24:2[bg];"
            f"[widefg]scale={CANVAS_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=decrease[fg];"
            f"[bg][fg]overlay=(W-w)/2:(H-h)/2{tail}[content];"
        )
    return (
        prefix
        + transform
        + f"[content]pad={CANVAS_WIDTH}:{CANVAS_HEIGHT}:0:{VIDEO_TOP}:color=0xF5F1EA[canvas];"
        + "[canvas][1:v]overlay=0:0:format=auto,format=yuv420p[outv]"
    )


def render_scene(
    media_path: Path,
    media_probe: dict[str, Any],
    overlay_path: Path,
    scene: dict[str, Any],
    output: Path,
    translation_overlays: list[tuple[Path, float, float]] | None = None,
) -> dict[str, Any]:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        fail("렌더링에는 ffmpeg가 필요합니다.")
    source_start = require_number(scene.get("source_start_seconds"), "scene.source_start_seconds", 0)
    source_seconds = require_number(scene.get("source_clip_seconds"), "scene.source_clip_seconds", 0.01, 8)
    duration = require_number(scene.get("duration"), "scene.duration", 0.25, 9.5)
    hold = require_number(scene.get("hold_last_frame_seconds", 0), "scene.hold_last_frame_seconds", 0, 1)
    input_seconds = min(source_seconds, duration)
    if hold:
        input_seconds = max(0.25, min(input_seconds, duration - hold))
    padding = max(0.0, duration - input_seconds)
    command = [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-ss",
        f"{source_start:.3f}",
        "-t",
        f"{input_seconds:.3f}",
        "-i",
        str(media_path),
        "-loop",
        "1",
        "-t",
        f"{duration:.3f}",
        "-i",
        str(overlay_path),
    ]
    translation_overlays = translation_overlays or []
    for translation_path, _, _ in translation_overlays:
        command.extend(["-loop", "1", "-t", f"{duration:.3f}", "-i", str(translation_path)])
    has_audio = bool(media_probe.get("has_audio"))
    audio_input = "[0:a]"
    if not has_audio:
        command.extend(
            [
                "-f",
                "lavfi",
                "-t",
                f"{duration:.3f}",
                "-i",
                "anullsrc=channel_layout=stereo:sample_rate=48000",
            ]
        )
        audio_input = f"[{2 + len(translation_overlays)}:a]"
    filters = video_filter(scene, media_probe, padding)
    video_output = "[outv]"
    for index, (_, start, end) in enumerate(translation_overlays, start=2):
        next_output = f"[translated{index}]"
        filters += (
            f";{video_output}[{index}:v]overlay=0:0:enable='between(t,{start:.3f},{end:.3f})':"
            f"format=auto{next_output}"
        )
        video_output = next_output
    if has_audio:
        filters += (
            f";{audio_input}atrim=0:{input_seconds:.3f},asetpts=PTS-STARTPTS,"
            f"apad=pad_dur={padding:.3f},atrim=0:{duration:.3f}[outa]"
        )
    else:
        filters += f";{audio_input}atrim=0:{duration:.3f},asetpts=PTS-STARTPTS[outa]"
    command.extend(
        [
            "-filter_complex",
            filters,
            "-map",
            video_output,
            "-map",
            "[outa]",
            "-t",
            f"{duration:.3f}",
            "-r",
            "30",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "160k",
            "-ar",
            "48000",
            "-ac",
            "2",
            "-movflags",
            "+faststart",
            "-y",
            str(output),
        ]
    )
    run_checked(command, f"{scene['id']} 렌더", timeout=900)
    return {
        "id": scene["id"],
        "duration_seconds": duration,
        "source_start_seconds": source_start,
        "source_input_seconds": round(input_seconds, 3),
        "held_frame_seconds": round(padding, 3),
        "source_audio_present": has_audio,
        "layout": "portrait_cover" if media_probe["width"] / media_probe["height"] <= 0.8 else "wide_blurred_background",
        "edit_actions": scene["edit_actions"],
        "source_caption_translation_overrides": len(translation_overlays),
    }


def create_synthetic_bgm(path: Path, duration: float, profile: str) -> None:
    frequencies = {
        "playful": (261.63, 329.63, 392.00, 329.63),
        "tension": (110.00, 116.54, 123.47, 116.54),
        "tender": (220.00, 277.18, 329.63, 277.18),
        "relief": (196.00, 246.94, 293.66, 392.00),
        "gentle": (174.61, 220.00, 261.63, 220.00),
    }
    notes = frequencies.get(profile)
    if not notes:
        fail(f"지원하지 않는 BGM 분위기입니다: {profile}")
    sample_rate = 48000
    total_frames = max(1, int(duration * sample_rate))
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(2)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        frames = bytearray()
        for index in range(total_frames):
            seconds = index / sample_rate
            note_index = int(seconds / 0.5) % len(notes)
            local = seconds % 0.5
            envelope = min(1.0, local / 0.05) * min(1.0, (0.5 - local) / 0.08)
            frequency = notes[note_index]
            sample = (
                math.sin(2 * math.pi * frequency * seconds)
                + 0.3 * math.sin(2 * math.pi * frequency * 2 * seconds)
            )
            value = int(max(-1, min(1, sample * envelope * 0.035)) * 32767)
            frames.extend(struct.pack("<hh", value, value))
        handle.writeframes(frames)


def create_synthetic_score_v2(path: Path, duration: float, music: dict[str, Any]) -> None:
    """Generate one coherent no-vocal score with scene-aware energy and cue changes."""
    chords = {
        "playful": ((261.63, 329.63, 392.00), (293.66, 369.99, 440.00)),
        "tension": ((110.00, 130.81, 164.81), (116.54, 138.59, 174.61)),
        "tender": ((220.00, 261.63, 329.63), (196.00, 246.94, 293.66)),
        "relief": ((196.00, 246.94, 293.66), (220.00, 277.18, 329.63)),
        "gentle": ((174.61, 220.00, 261.63), (196.00, 246.94, 293.66)),
    }
    segments = [
        require_object(item, "music-plan.segment")
        for item in require_list(music.get("segments"), "music-plan.segments")
    ]
    if not segments:
        fail("장면별 생성 음악 구간이 없습니다.")
    bpm = require_number(music.get("bpm"), "music-plan.bpm", 60, 180)
    sample_rate = 48_000
    total_frames = max(1, round(duration * sample_rate))
    beat_seconds = 60.0 / bpm
    half_beat = beat_seconds / 2
    fade_in = require_number(music.get("fade_in_seconds", 0.08), "music-plan.fade_in_seconds", 0, 1)
    fade_out = require_number(music.get("fade_out_seconds", 0.3), "music-plan.fade_out_seconds", 0, 2)
    path.parent.mkdir(parents=True, exist_ok=True)
    frames = bytearray()
    segment_index = 0
    for frame in range(total_frames):
        seconds = frame / sample_rate
        while segment_index + 1 < len(segments) and seconds >= float(segments[segment_index].get("end_seconds") or 0):
            segment_index += 1
        segment = segments[segment_index]
        start = float(segment.get("start_seconds") or 0)
        end = float(segment.get("end_seconds") or duration)
        local = max(0.0, seconds - start)
        segment_duration = max(0.01, end - start)
        profile = clean_text(segment.get("profile_id"))
        if profile not in chords:
            fail(f"지원하지 않는 장면 음악 분위기입니다: {profile}")
        energy = float(segment.get("energy") or 0.5)
        duck_db = float(segment.get("bgm_below_source_db") or 15)
        duck_gain = 10 ** ((15.0 - duck_db) / 20.0)
        chord_pair = chords[profile]
        chord = chord_pair[(int(seconds / (beat_seconds * 4))) % len(chord_pair)]
        step_phase = seconds % half_beat
        step_index = int(seconds / half_beat) % 4
        arpeggio = (chord[0], chord[1], chord[2], chord[1] * 2)[step_index]
        pluck_envelope = min(1.0, step_phase / 0.012) * math.exp(-6.5 * step_phase / half_beat)
        pluck_left = (
            math.sin(2 * math.pi * arpeggio * seconds)
            + 0.28 * math.sin(4 * math.pi * arpeggio * seconds)
        ) * pluck_envelope * 0.13
        pluck_right = (
            math.sin(2 * math.pi * arpeggio * 1.003 * seconds)
            + 0.28 * math.sin(4 * math.pi * arpeggio * 1.003 * seconds)
        ) * pluck_envelope * 0.13
        pad_left = sum(math.sin(2 * math.pi * frequency * seconds) for frequency in chord) * 0.018
        pad_right = sum(math.sin(2 * math.pi * frequency * 1.002 * seconds) for frequency in chord) * 0.018
        beat_phase = seconds % beat_seconds
        bass = math.sin(2 * math.pi * (chord[0] / 2) * seconds) * math.exp(-4.2 * beat_phase / beat_seconds) * 0.12
        rhythmic = profile not in {"tender", "gentle"}
        kick = 0.0
        hat = 0.0
        if rhythmic and energy >= 0.35:
            kick_frequency = 50.0 + 65.0 * math.exp(-24.0 * beat_phase)
            kick = math.sin(2 * math.pi * kick_frequency * beat_phase) * math.exp(-14.0 * beat_phase) * 0.22
            hat_phase = seconds % half_beat
            hat_noise = math.sin(2 * math.pi * 8_093 * seconds) * math.sin(2 * math.pi * 11_141 * seconds)
            hat = hat_noise * math.exp(-36.0 * hat_phase) * 0.035
        cue = clean_text(segment.get("cue"))
        cue_gain = 1.0
        if cue == "drop" and local < 0.28:
            cue_gain = 0.06 if local < 0.16 else 0.06 + 0.94 * ((local - 0.16) / 0.12)
        impact = 0.0
        if cue == "impact" and local < 0.38:
            impact = (
                0.34 * math.sin(2 * math.pi * (58.0 + 105.0 * math.exp(-9.0 * local)) * local)
                + 0.08 * math.sin(2 * math.pi * 1_620 * local)
            ) * math.exp(-7.2 * local)
        boundary_gain = min(1.0, local / 0.04, max(0.0, segment_duration - local) / 0.04)
        track_gain = 1.0
        if fade_in > 0:
            track_gain *= min(1.0, seconds / fade_in)
        if fade_out > 0:
            track_gain *= min(1.0, max(0.0, duration - seconds) / fade_out)
        gain = max(0.0, min(1.4, energy * duck_gain)) * cue_gain * boundary_gain * track_gain
        left = math.tanh((pluck_left + pad_left + bass + kick + hat + impact) * gain * 1.2) * 0.78
        right = math.tanh((pluck_right + pad_right + bass + kick + 0.82 * hat + impact) * gain * 1.2) * 0.78
        frames.extend(struct.pack("<hh", round(left * 32767), round(right * 32767)))
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(2)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(frames)


def create_synthetic_sfx(path: Path, duration: float, events: list[Any]) -> dict[str, Any]:
    """Generate a deterministic full-length no-vocal SFX track."""
    normalized_events: list[dict[str, Any]] = []
    for index, value in enumerate(events):
        event = require_object(value, f"music-plan.sfx.events[{index}]")
        effect_type = require_text(event.get("type"), f"sfx event[{index}].type")
        if effect_type not in SFX_TYPES:
            fail(f"지원하지 않는 효과음입니다: {effect_type}")
        normalized_events.append(
            {
                "scene_id": clean_text(event.get("scene_id")),
                "type": effect_type,
                "time_seconds": require_number(event.get("time_seconds"), f"sfx event[{index}].time_seconds", 0, duration),
                "gain_db": require_number(event.get("gain_db", -8), f"sfx event[{index}].gain_db", -24, 0),
            }
        )
    sample_rate = 48_000
    total_frames = max(1, round(duration * sample_rate))
    frames = bytearray()
    for frame in range(total_frames):
        seconds = frame / sample_rate
        sample = 0.0
        for event in normalized_events:
            local = seconds - float(event["time_seconds"])
            gain = 10 ** (float(event["gain_db"]) / 20.0)
            if event["type"] == "question_pop" and 0 <= local <= 0.42:
                envelope = min(1.0, local / 0.012) * math.exp(-6.4 * local)
                rising = math.sin(2 * math.pi * (390.0 * local + 470.0 * local * local))
                answer_local = local - 0.14
                answer = 0.0
                if answer_local >= 0:
                    answer = math.sin(2 * math.pi * 690.0 * answer_local) * math.exp(-8.5 * answer_local)
                sample += (0.42 * rising * envelope + 0.24 * answer) * gain
            elif event["type"] == "soft_whoosh" and 0 <= local <= 0.32:
                phase = local / 0.32
                envelope = math.sin(math.pi * phase) ** 1.4
                noise = math.sin(2 * math.pi * 2_791 * seconds) * math.sin(2 * math.pi * 4_087 * seconds)
                tone = math.sin(2 * math.pi * (180.0 + 520.0 * phase) * local)
                sample += (0.22 * noise + 0.12 * tone) * envelope * gain
            elif event["type"] == "bass_drum" and 0 <= local <= 0.9:
                attack = min(1.0, local / 0.008)
                envelope = attack * math.exp(-4.8 * local)
                phase = 2 * math.pi * (42.0 * local + (82.0 / 6.0) * (1.0 - math.exp(-6.0 * local)))
                body = math.sin(phase)
                sub_tail = math.sin(2 * math.pi * 48.0 * local) * math.exp(-5.2 * local)
                click = math.sin(2 * math.pi * 1_050.0 * local) * math.exp(-55.0 * local)
                sample += (0.7 * body * envelope + 0.14 * sub_tail + 0.08 * click) * gain
        value = round(max(-0.92, min(0.92, sample)) * 32767)
        frames.extend(struct.pack("<hh", value, value))
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(2)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(frames)
    return {
        "mode": "renderer_generated",
        "source": "renderer-generated no-vocal PCM",
        "events": normalized_events,
        "sha256": sha256_file(path),
        "rights_status": "owned",
    }


def concatenate_scenes(scene_paths: list[Path], destination: Path, work_dir: Path) -> None:
    concat_path = work_dir / "concat.txt"
    concat_lines = []
    for path in scene_paths:
        escaped = path.as_posix().replace("'", "'\\''")
        concat_lines.append(f"file '{escaped}'")
    concat_path.write_text("\n".join(concat_lines) + "\n", encoding="utf-8")
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
            str(concat_path),
            "-c",
            "copy",
            "-movflags",
            "+faststart",
            "-y",
            str(destination),
        ],
        "장면 합치기",
        timeout=900,
    )


def mix_final_audio(
    video_path: Path,
    music_path: Path,
    output: Path,
    duration: float,
    *,
    music_volume: float,
    loop_music: bool,
    music: dict[str, Any],
    sfx_path: Path | None = None,
) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        fail("오디오 믹싱에는 ffmpeg가 필요합니다.")
    command = [ffmpeg, "-hide_banner", "-loglevel", "error", "-i", str(video_path)]
    if loop_music:
        command.extend(["-stream_loop", "-1"])
    command.extend(["-i", str(music_path)])
    if sfx_path is not None:
        command.extend(["-i", str(sfx_path)])
    volume_filter = f"volume={music_volume:.6f}"
    if clean_text(music.get("mode")) == "licensed_track" and isinstance(music.get("segments"), list):
        expression = f"{music_volume:.6f}"
        for value in reversed(require_list(music.get("segments"), "music-plan.segments")):
            segment = require_object(value, "music-plan.segment")
            start = float(segment.get("start_seconds") or 0)
            end = float(segment.get("end_seconds") or duration)
            duck_db = float(segment.get("bgm_below_source_db") or 15)
            segment_volume = music_volume * (10 ** ((15.0 - duck_db) / 20.0))
            expression = f"if(between(t,{start:.3f},{end:.3f}),{segment_volume:.6f},{expression})"
        volume_filter = f"volume='{expression}':eval=frame"
    fade_in = float(music.get("fade_in_seconds") or 0)
    fade_out = float(music.get("fade_out_seconds") or 0)
    music_filters = [volume_filter]
    if fade_in > 0:
        music_filters.append(f"afade=t=in:st=0:d={fade_in:.3f}")
    if fade_out > 0:
        music_filters.append(f"afade=t=out:st={max(0.0, duration - fade_out):.3f}:d={fade_out:.3f}")
    mix_inputs = "[source][bgm]"
    mix_count = 2
    sfx_filter = ""
    if sfx_path is not None:
        sfx_filter = "[2:a]volume=1.0[sfx];"
        mix_inputs += "[sfx]"
        mix_count = 3
    command.extend(
        [
            "-filter_complex",
            f"[0:a]volume=1.0[source];[1:a]{','.join(music_filters)}[bgm];"
            f"{sfx_filter}{mix_inputs}amix=inputs={mix_count}:duration=first:dropout_transition=0,"
            "loudnorm=I=-15:LRA=11:TP=-1[outa]",
            "-map",
            "0:v",
            "-map",
            "[outa]",
            "-t",
            f"{duration:.3f}",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "160k",
            "-ar",
            "48000",
            "-ac",
            "2",
            "-movflags",
            "+faststart",
            "-y",
            str(output),
        ]
    )
    run_checked(command, "원본음과 BGM 믹싱", timeout=900)


def last_frame_luma(video_path: Path, work_dir: Path) -> float:
    frame_path = work_dir / "last-frame.png"
    run_checked(
        [
            shutil.which("ffmpeg") or "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-sseof",
            "-0.08",
            "-i",
            str(video_path),
            "-frames:v",
            "1",
            "-y",
            str(frame_path),
        ],
        "마지막 프레임 검사",
        timeout=120,
    )
    try:
        from PIL import Image, ImageStat
    except ImportError as exc:
        raise AnimalViralShortsError("마지막 프레임 검사에는 Pillow가 필요합니다.") from exc
    image = Image.open(frame_path).convert("L")
    return float(ImageStat.Stat(image).mean[0])


def delivery_note_text(
    project: dict[str, Any],
    source: dict[str, Any],
    script: dict[str, Any],
    output: Path,
    report: dict[str, Any],
) -> str:
    rights = require_object(source.get("rights"), "source.rights")
    lines = [
        "# Animal Viral Shorts 로컬 전달 노트",
        "",
        f"- 결과물: {output.name}",
        f"- 스토리: {script['story_id']}",
        f"- 원본 제작자: {source['creator']}",
        f"- 원본 URL: {clean_text(source.get('original_url')) or '로컬 제공 파일'}",
        f"- 원본 권리 상태: {rights['status']}",
        f"- 원본 SHA-256: {source['media'][0]['sha256']}",
        f"- 오디오: 원본음 + {report['music']['mode']} 비보컬 BGM + "
        f"{len(report.get('sound_effects', {}).get('events', []))}개 비보컬 효과음",
        f"- 검토 승인: {'필요' if report['draft'] else '재미·음악 사용자 승인 완료'}",
        "- TTS·내레이션: 없음",
        "- 외부 업로드: 수행하지 않음",
        "",
        "## 증거 경계",
        "",
    ]
    for segment in script["segments"]:
        lines.append(f"- {segment['id']}: {'; '.join(segment['evidence'])}")
    lines.extend(
        [
            "",
            "이 로컬 MP4는 기술적 렌더 결과입니다. 게시 허가, 공정 이용, 수익화 가능성, 사실 확정, 동물 복지 전문 판단 또는 바이럴 성과를 증명하지 않습니다.",
            "",
        ]
    )
    return "\n".join(lines)


def command_approve_draft(args: argparse.Namespace) -> int:
    project_dir = Path(args.project_dir).expanduser().resolve()
    project, _ = load_project(project_dir)
    if clean_text(project.get("status")) not in {"rendered_draft", "draft_approved"}:
        fail("검토용 렌더를 만든 뒤에만 재미와 음악 적합성을 승인할 수 있습니다.")
    draft_report_path = project_dir / "draft-render-report.json"
    if not draft_report_path.is_file():
        draft_report_path = project_dir / "render-report.json"
    report = require_object(read_json(draft_report_path), draft_report_path.name)
    if report.get("draft") is not True:
        fail("최종본이 아니라 render --draft 결과를 검토해야 합니다.")
    review_path = project_dir / "draft-review.json"
    ensure_new([review_path], args.overwrite)
    approved = args.story_fit == "pass" and args.music_fit == "pass"
    review = {
        "schema_version": SCHEMA_VERSION,
        "reviewed_at": now_iso(),
        "reviewed_by": "user",
        "story_fit": args.story_fit,
        "music_fit": args.music_fit,
        "approved": approved,
        "note": clean_text(args.note),
        "draft_output": clean_text(report.get("output")),
        "rendered_at": clean_text(report.get("rendered_at")),
    }
    write_json(review_path, review)
    project["status"] = "draft_approved" if approved else "rendered_draft"
    project["updated_at"] = review["reviewed_at"]
    project["draft_review"] = review
    write_json(project_dir / "project.json", project)
    print(json.dumps({"status": project["status"], "draft_review": review}, ensure_ascii=False, indent=2))
    return 0


def command_render(args: argparse.Namespace) -> int:
    project_dir = Path(args.project_dir).expanduser().resolve()
    errors, warnings = validate_project(project_dir, final=True)
    if errors:
        fail("최종 렌더 검증 실패:\n- " + "\n- ".join(errors))
    project, source = load_project(project_dir)
    if clean_text(project.get("status")) not in {"composed", "render_ready", "rendered_draft", "draft_approved", "rendered_local"}:
        fail("최종 검증을 통과한 프로젝트만 렌더링할 수 있습니다.")
    if not args.draft:
        review = require_object(read_json(project_dir / "draft-review.json"), "draft-review.json")
        if review.get("approved") is not True or clean_text(review.get("story_fit")) != "pass" or clean_text(review.get("music_fit")) != "pass":
            fail("최종본은 사용자가 검토용 영상의 재미와 음악을 모두 승인한 뒤에만 렌더링할 수 있습니다.")
    storyboard = require_object(read_json(project_dir / "storyboard.json"), "storyboard.json")
    visual_preset = normalize_visual_preset(
        storyboard.get("visual_preset"),
        "storyboard.visual_preset",
        fallback=LEGACY_VISUAL_PRESET,
    )
    script = require_object(read_json(project_dir / "script.json"), "script.json")
    music = require_object(read_json(project_dir / "music-plan.json"), "music-plan.json")
    media_path, media_entry = source_media(project_dir, source)
    media_probe = require_object(media_entry.get("probe"), "source.media.probe")
    default_output = "outputs/preview.mp4" if args.draft else "outputs/short.mp4"
    output_relative = args.output or default_output
    if Path(output_relative).suffix.lower() != ".mp4":
        fail("출력 파일은 프로젝트 내부 .mp4 경로여야 합니다.")
    output = safe_project_path(project_dir, output_relative)
    report_path = project_dir / ("draft-render-report.json" if args.draft else "render-report.json")
    delivery = project_dir / ("draft-delivery-note.md" if args.draft else "delivery-note.md")
    ensure_new([output, report_path, delivery], args.overwrite)
    output.parent.mkdir(parents=True, exist_ok=True)
    scenes = require_list(storyboard.get("scenes"), "storyboard.scenes")
    total_duration = sum(float(require_object(item, "scene").get("duration") or 0) for item in scenes)
    if total_duration + CTA_TAIL_SECONDS > MAX_SHORT_SECONDS:
        fail(
            f"장면 길이 {total_duration:.2f}초에 CTA {CTA_TAIL_SECONDS:.1f}초를 더하면 "
            f"최대 {MAX_SHORT_SECONDS:.1f}초를 초과합니다. 결론 이전 장면을 줄이세요."
        )
    scene_reports: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix=".animal-viral-render-", dir=project_dir) as temp_name:
        work_dir = Path(temp_name)
        scene_paths: list[Path] = []
        for index, scene_value in enumerate(scenes, start=1):
            scene = require_object(scene_value, f"scene[{index}]")
            overlay = work_dir / f"overlay-{index:02d}.png"
            scene_path = work_dir / f"scene-{index:02d}.mp4"
            make_overlay(
                project_dir,
                scene,
                source,
                overlay,
                draft=args.draft,
                visual_preset=visual_preset,
            )
            translation_overlays: list[tuple[Path, float, float]] = []
            for override_index, value in enumerate(require_list(scene.get("source_caption_overrides", []), "scene.source_caption_overrides"), start=1):
                override = require_object(value, f"scene source caption override[{override_index}]")
                translation_path = work_dir / f"translation-{index:02d}-{override_index:02d}.png"
                make_translation_overlay(override, translation_path)
                translation_overlays.append(
                    (
                        translation_path,
                        float(override["start_seconds"]),
                        float(override["end_seconds"]),
                    )
                )
            scene_reports.append(
                render_scene(
                    media_path,
                    media_probe,
                    overlay,
                    scene,
                    scene_path,
                    translation_overlays=translation_overlays,
                )
            )
            scene_paths.append(scene_path)
        concatenated = work_dir / "concatenated.mp4"
        concatenate_scenes(scene_paths, concatenated, work_dir)
        mode = clean_text(music.get("mode"))
        if mode in {"synthetic_ambient", "synthetic_score_v2"}:
            music_path = work_dir / "synthetic-bgm.wav"
            if mode == "synthetic_score_v2":
                create_synthetic_score_v2(music_path, total_duration, music)
            else:
                create_synthetic_bgm(music_path, total_duration, clean_text(music.get("profile_id")))
            music_volume = 10 ** (-float(music.get("bgm_below_source_db", 15)) / 20)
            loop_music = False
            music_report = {
                "mode": mode,
                "profile_id": clean_text(music.get("profile_id")),
                "bpm": music.get("bpm"),
                "segments": music.get("segments", []),
                "source": "renderer-generated no-vocal PCM",
                "sha256": sha256_file(music_path),
                "rights_status": "owned",
                "licensed_asset": False,
            }
        else:
            track = require_object(music.get("track"), "music-plan.track")
            music_path = safe_project_path(project_dir, require_text(track.get("relative_path"), "track.relative_path"), exists=True)
            music_volume = require_number(track.get("volume", 0.18), "track.volume", 0.01, 0.5)
            loop_music = True
            music_report = {
                "mode": mode,
                "title": track["title"],
                "creator": track["creator"],
                "official_source_url": track["official_source_url"],
                "license_name": track["license_name"],
                "attribution": track["attribution"],
                "sha256": track["sha256"],
                "licensed_asset": True,
            }
        sfx = require_object(music.get("sfx", {"events": []}), "music-plan.sfx")
        sfx_events = require_list(sfx.get("events", []), "music-plan.sfx.events")
        sfx_path: Path | None = None
        if sfx_events:
            sfx_path = work_dir / "synthetic-sfx.wav"
            sfx_report = create_synthetic_sfx(sfx_path, total_duration, sfx_events)
        else:
            sfx_report = {
                "mode": "renderer_generated",
                "source": "none",
                "events": [],
                "rights_status": "owned",
            }
        mix_final_audio(
            concatenated,
            music_path,
            output,
            total_duration,
            music_volume=music_volume,
            loop_music=loop_music,
            music=music,
            sfx_path=sfx_path,
        )
        cta_output = work_dir / "cta-appended.mp4"
        try:
            cta_report = append_cta_tail(
                output,
                cta_output,
                width=CANVAS_WIDTH,
                height=CANVAS_HEIGHT,
                source_duration=total_duration,
                has_audio=True,
                font_path=find_font(),
                headline="다음 동물 이야기도",
                prompt="구독 · 좋아요",
                ffmpeg=shutil.which("ffmpeg") or "ffmpeg",
            )
        except YouTubeDeliveryError as exc:
            fail(str(exc))
        cta_output.replace(output)
        final_probe = probe_media(output)
        luma = last_frame_luma(output, work_dir)
    specification_errors: list[str] = []
    if final_probe["video_codec"] != "h264":
        specification_errors.append("영상 코덱이 H.264가 아닙니다.")
    if (final_probe["width"], final_probe["height"]) != (CANVAS_WIDTH, CANVAS_HEIGHT):
        specification_errors.append("영상 해상도가 720x1280이 아닙니다.")
    if final_probe["audio_codec"] != "aac" or not final_probe["has_audio"]:
        specification_errors.append("AAC 오디오 트랙이 없습니다.")
    if abs(final_probe["fps"] - 30) > 0.2:
        specification_errors.append("프레임 레이트가 30fps가 아닙니다.")
    if not 0 < final_probe["duration_seconds"] <= MAX_SHORT_SECONDS:
        specification_errors.append("최종 길이가 59.5초 범위를 벗어났습니다.")
    if luma < 8:
        specification_errors.append("마지막 프레임이 검게 끝납니다.")
    if specification_errors:
        if output.exists():
            output.unlink()
        fail("렌더 결과 기술 검증 실패:\n- " + "\n- ".join(specification_errors))
    report = {
        "schema_version": SCHEMA_VERSION,
        "rendered_at": now_iso(),
        "draft": bool(args.draft),
        "local_only": True,
        "output": relative_path(project_dir, output),
        "template_id": clean_text(storyboard.get("template_id")) or TEMPLATE_ID,
        "visual_preset": visual_preset,
        "source_audio_primary": True,
        "tts": False,
        "narration": False,
        "cta_tail": cta_report,
        "music": music_report,
        "sound_effects": sfx_report,
        "scenes": scene_reports,
        "video": final_probe,
        "last_frame_mean_luma": round(luma, 2),
        "warnings": warnings,
        "draft_review_required": bool(args.draft),
        "story_and_music_user_approved": not bool(args.draft),
        "proof_boundary": {
            "technical_render": True,
            "publication_permission": False,
            "monetization_eligibility": False,
            "performance_guarantee": False,
        },
    }
    rights_status = clean_text(require_object(source.get("rights"), "source.rights").get("status")) or "unknown"
    title = clean_text(project.get("title")) or f"{clean_text(source.get('creator')) or '동물'}의 반전 이야기"
    first_scene = require_object(require_list(storyboard.get("scenes"), "storyboard.scenes")[0], "storyboard.scene[0]")
    first_headline = require_object(first_scene.get("headline"), "storyboard.scene[0].headline")
    description_heading = clean_text(first_headline.get("line1")) or "동물 반전 이야기"
    upload_json, upload_md, _ = write_upload_package(
        project_dir,
        video_path=relative_path(project_dir, output),
        title=title,
        description=(
            f"{description_heading}\n\n실제 영상에서 확인한 행동을 바탕으로 기승전결로 재구성한 동물 쇼츠입니다.\n"
            f"권리 상태: {rights_status}\n\n#동물 #Shorts"
        ),
        tags=["동물", "동물쇼츠", "반전", "Shorts"],
        thumbnail_note="CTA 직전 결론 장면에서 동물 행동과 반전 자막이 함께 보이는 프레임",
        playlist="동물 이야기",
        category="Pets & Animals",
        language="ko",
        pinned_comment=f"{title}에서 가장 인상적이었던 행동은 무엇인가요?",
        rights_status=rights_status,
        synthetic_elements=True,
        generated_at=report["rendered_at"],
        preserve_existing_description=False,
    )
    report["youtube_upload"] = {
        "json": relative_path(project_dir, upload_json),
        "markdown": relative_path(project_dir, upload_md),
        "upload_performed": False,
    }
    write_json(report_path, report)
    delivery.write_text(delivery_note_text(project, source, script, output, report), encoding="utf-8")
    if not (project_dir / "edit-plan.md").exists():
        (project_dir / "edit-plan.md").write_text(edit_plan_text(project, source, storyboard, music), encoding="utf-8")
    project["status"] = "rendered_draft" if args.draft else "rendered_local"
    project["updated_at"] = now_iso()
    if args.draft:
        project["draft_review"] = {
            "approved": False,
            "story_fit": "pending",
            "music_fit": "pending",
            "reviewed_at": "",
        }
    project["last_render"] = {
        "relative_path": report["output"],
        "report": report_path.name,
        "delivery_note": delivery.name,
        "draft": bool(args.draft),
        "rendered_at": report["rendered_at"],
    }
    write_json(project_dir / "project.json", project)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


def command_upload_package(args: argparse.Namespace) -> int:
    project_dir = Path(args.project_dir).expanduser().resolve()
    try:
        _, markdown = read_upload_package(project_dir / "youtube-upload.json")
    except YouTubeDeliveryError as exc:
        fail(str(exc))
    print(markdown, end="")
    return 0


def command_doctor(args: argparse.Namespace) -> int:
    try:
        import PIL  # type: ignore

        pillow = PIL.__version__
    except ImportError:
        pillow = None
    payload = {
        "plugin": "animal-viral-shorts",
        "version": PLUGIN_VERSION,
        "python": sys.version.split()[0],
        "ffmpeg": shutil.which("ffmpeg"),
        "ffprobe": shutil.which("ffprobe"),
        "yt_dlp": shutil.which("yt-dlp") or ("python-module" if importlib.util.find_spec("yt_dlp") else None),
        "pillow": pillow,
        "korean_font": str(next((path for path in FONT_CANDIDATES if path.is_file()), "")),
        "platforms": sorted(PLATFORMS),
        "render": {
            "width": CANVAS_WIDTH,
            "height": CANVAS_HEIGHT,
            "fps": 30,
            "audio": "source audio plus no-vocal BGM and optional no-vocal SFX",
            "tts": False,
            "upload": False,
            "maximum_duration_seconds": MAX_SHORT_SECONDS,
            "narrative": "setup-build-turn-payoff",
            "draft_approval_required": True,
            "visual_presets": sorted(VISUAL_PRESETS),
            "new_project_default_visual_preset": DEFAULT_VISUAL_PRESET,
            "legacy_visual_preset_fallback": LEGACY_VISUAL_PRESET,
        },
        "collector": "Codex Skill public-web research; CLI has no scraper or AI API",
        "ready_for_metadata": True,
        "ready_for_preview_and_render": bool(shutil.which("ffmpeg") and shutil.which("ffprobe") and pillow and next((path for path in FONT_CANDIDATES if path.is_file()), None)),
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        for key, value in payload.items():
            print(f"{key}: {json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else value}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="검증된 동물 바이럴 소스를 두 번 선택해 기승전결·장면별 BGM이 있는 720x1280 로컬 쇼츠로 만드는 도구."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor = subparsers.add_parser("doctor", help="로컬 도구, 글꼴과 범위를 확인합니다.")
    doctor.add_argument("--json", action="store_true", help="JSON으로 출력합니다.")
    doctor.set_defaults(handler=command_doctor)

    score = subparsers.add_parser("score-candidates", help="TikTok·YouTube Shorts 동물 후보를 검증하고 최대 3개로 정규화합니다.")
    score.add_argument("--input", required=True, help="후보 입력 JSON")
    score.add_argument("--output", required=True, help="순위 JSON 출력")
    score.add_argument("--top-k", type=int, default=3, help="최대 비교 후보 수, 상한 3")
    score.add_argument("--overwrite", action="store_true", help="기존 순위 JSON과 Markdown을 교체합니다.")
    score.set_defaults(handler=command_score_candidates)

    init = subparsers.add_parser("init", help="사용자가 선택한 후보, URL 또는 로컬 영상으로 프로젝트를 만듭니다.")
    init.add_argument("--project-dir", required=True, help="새 프로젝트 폴더")
    init.add_argument("--candidates", help="score-candidates 결과 또는 후보 JSON")
    init.add_argument("--candidate-id", help="사용자가 선택한 후보 ID")
    init.add_argument("--source-file", help="사용자가 권한을 확인한 로컬 영상")
    init.add_argument("--source-url", help="사용자가 선택한 TikTok 또는 YouTube Shorts URL")
    init.add_argument("--creator", help="직접 제공 소스 제작자")
    init.add_argument("--rights-status", choices=sorted(RIGHTS_STATUSES), default="unknown", help="직접 제공 소스 권리 상태")
    init.add_argument(
        "--visual-preset",
        choices=sorted(VISUAL_PRESETS),
        default=DEFAULT_VISUAL_PRESET,
        help="신규 프로젝트 화면 프리셋. 기존 프로젝트는 animal-viral-card-v1로 호환됩니다.",
    )
    init.set_defaults(handler=command_init)

    acquire = subparsers.add_parser("acquire", help="선택된 정식 URL만 yt-dlp로 로컬 획득합니다.")
    acquire.add_argument("--project-dir", required=True, help="animal-viral-shorts 프로젝트")
    acquire.add_argument("--max-filesize", default="500M", help="최대 파일 크기")
    acquire.set_defaults(handler=command_acquire)

    preview = subparsers.add_parser("preview", help="사람의 시각 검토용 프레임과 콘택트시트를 생성합니다.")
    preview.add_argument("--project-dir", required=True, help="animal-viral-shorts 프로젝트")
    preview.add_argument("--interval", type=float, default=2.0, help="프레임 간격 초")
    preview.add_argument("--max-frames", type=int, default=60, help="최대 프레임 수, 상한 120")
    preview.add_argument("--overwrite", action="store_true", help="기존 preview 자산을 교체합니다.")
    preview.set_defaults(handler=command_preview)

    observe = subparsers.add_parser("observe", help="검토한 행동·타임코드·보호 영역을 등록합니다.")
    observe.add_argument("--project-dir", required=True, help="animal-viral-shorts 프로젝트")
    observe.add_argument("--input", required=True, help="검토 완료 관찰 JSON")
    observe.add_argument("--overwrite", action="store_true", help="기존 source-analysis.json을 교체합니다.")
    observe.set_defaults(handler=command_observe)

    stories = subparsers.add_parser("stories", help="실제 관찰에 근거한 서로 다른 스토리 3안을 검증합니다.")
    stories.add_argument("--project-dir", required=True, help="animal-viral-shorts 프로젝트")
    stories.add_argument("--input", required=True, help="Skill이 작성한 스토리 3안 JSON")
    stories.add_argument("--overwrite", action="store_true", help="기존 스토리 옵션을 교체합니다.")
    stories.set_defaults(handler=command_stories)

    select_story = subparsers.add_parser("select-story", help="사용자가 명시적으로 고른 스토리를 기록합니다.")
    select_story.add_argument("--project-dir", required=True, help="animal-viral-shorts 프로젝트")
    select_story.add_argument("--story-id", required=True, help="선택한 스토리 ID")
    select_story.add_argument("--note", default="", help="사용자 선택 메모")
    select_story.add_argument("--overwrite", action="store_true", help="기존 선택 기록을 교체합니다.")
    select_story.set_defaults(handler=command_select_story)

    compose = subparsers.add_parser("compose", help="선택 스토리를 대본·스토리보드·음악 계획으로 조합합니다.")
    compose.add_argument("--project-dir", required=True, help="animal-viral-shorts 프로젝트")
    compose.add_argument("--overwrite", action="store_true", help="기존 조합 파일을 교체합니다.")
    compose.set_defaults(handler=command_compose)

    edit_plan = subparsers.add_parser("edit-plan", help="사람이 검토할 Markdown 편집 계획을 만듭니다.")
    edit_plan.add_argument("--project-dir", required=True, help="animal-viral-shorts 프로젝트")
    edit_plan.add_argument("--overwrite", action="store_true", help="기존 편집 계획을 교체합니다.")
    edit_plan.set_defaults(handler=command_edit_plan)

    validate = subparsers.add_parser("validate", help="상태·근거·권리·렌더 계약을 정적으로 검사합니다.")
    validate.add_argument("--project-dir", required=True, help="animal-viral-shorts 프로젝트")
    validate.add_argument("--final", action="store_true", help="최종 MP4 렌더 전 게이트까지 검사합니다.")
    validate.set_defaults(handler=command_validate)

    approve = subparsers.add_parser("approve-draft", help="검토용 영상의 재미와 음악 적합성에 대한 사용자 결정을 기록합니다.")
    approve.add_argument("--project-dir", required=True, help="animal-viral-shorts 프로젝트")
    approve.add_argument("--story-fit", required=True, choices=("pass", "revise"), help="기승전결과 재미 적합성")
    approve.add_argument("--music-fit", required=True, choices=("pass", "revise"), help="내용과 음악의 자연스러운 적합성")
    approve.add_argument("--note", default="", help="사용자 검토 메모")
    approve.add_argument("--overwrite", action="store_true", help="기존 검토 기록을 교체합니다.")
    approve.set_defaults(handler=command_approve_draft)

    render = subparsers.add_parser("render", help="검증된 선택안을 720x1280 H.264/AAC 로컬 MP4로 렌더링합니다.")
    render.add_argument("--project-dir", required=True, help="animal-viral-shorts 프로젝트")
    render.add_argument("--draft", action="store_true", help="검토용 outputs/preview.mp4를 만듭니다.")
    render.add_argument("--output", help="프로젝트 내부 MP4 경로")
    render.add_argument("--overwrite", action="store_true", help="기존 MP4를 교체합니다.")
    render.set_defaults(handler=command_render)

    upload_package = subparsers.add_parser("upload-package", help="렌더 결과의 YouTube 업로드 정보를 출력합니다.")
    upload_package.add_argument("--project-dir", required=True, help="Animal Viral Shorts 프로젝트 폴더")
    upload_package.set_defaults(handler=command_upload_package)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.handler(args)
    except AnimalViralShortsError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
