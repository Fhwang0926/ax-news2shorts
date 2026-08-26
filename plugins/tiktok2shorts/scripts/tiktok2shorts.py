#!/usr/bin/env python3
"""Local project tooling for the tiktok2shorts Codex plugin.

This tool accepts animal candidate data from structured exports or public
metadata research instead of scraping TikTok. It scores observed metrics,
prepares an animal-emotion project, and renders a local-only review video.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Any
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

from youtube_delivery import (
    CTA_TAIL_SECONDS,
    YouTubeDeliveryError,
    append_cta_tail,
    read_upload_package,
    write_upload_package,
)


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
KST = ZoneInfo("Asia/Seoul")
CANVAS_WIDTH = 1080
CANVAS_HEIGHT = 1920
OUTPUT_WIDTH = 720
OUTPUT_HEIGHT = 1280
ALLOWED_RIGHTS_STATUSES = {"owned", "licensed", "permission_confirmed"}
KNOWN_RIGHTS_STATUSES = ALLOWED_RIGHTS_STATUSES | {"unknown", "review_required", "not_permitted"}
LOCAL_USE_RIGHTS_STATUSES = KNOWN_RIGHTS_STATUSES - {"not_permitted"}
PROVEN_VIRAL_MIN_VIEWS = 1_000_000
PROVEN_VIRAL_STRONG_VIEWS = 3_000_000
PROVEN_VIRAL_MIN_SHARES = 10_000
PROVEN_VIRAL_MIN_INTERACTIONS = 100_000
PROVEN_VIRAL_MIN_ENGAGEMENT_RATE = 0.08
WHITEBOARD_FIT_MIN_SCORE = 70.0
WHITEBOARD_FIT_MIN_HOOK = 12.0
WHITEBOARD_FIT_MIN_PAYOFF = 12.0
WHITEBOARD_FIT_MIN_COMPOSITION = 6.0
WHITEBOARD_FIT_MIN_DISTINCT_BEATS = 3
RISK_CATEGORIES = {"news", "politics", "current-affairs", "crime", "health", "finance", "war"}
ANIMAL_CATEGORIES = {"animal", "animals", "pet", "pets", "wildlife", "animal-rescue"}
EMOTION_CONFIDENCE_LEVELS = {"observed", "caregiver_report", "inference"}
MUSIC_PROFILES = {
    "gentle": {
        "label": "잔잔한 관찰",
        "frequencies": (261.63, 329.63, 392.0),
        "description": "휴식·차분한 관찰 장면을 위한 잔잔한 무보컬 앰비언트",
    },
    "tender": {
        "label": "따뜻한 공감",
        "frequencies": (220.0, 277.18, 329.63),
        "description": "애착·이별·돌봄 장면을 위한 따뜻한 무보컬 앰비언트",
    },
    "tension": {
        "label": "조심스러운 긴장",
        "frequencies": (174.61, 220.0, 261.63),
        "description": "경계·불안 가능성 장면을 과장하지 않고 받쳐 주는 낮은 앰비언트",
    },
    "relief": {
        "label": "안도",
        "frequencies": (293.66, 369.99, 440.0),
        "description": "안전 확인·회복·재회 장면을 위한 밝은 무보컬 앰비언트",
    },
    "playful": {
        "label": "통통 튀는 상황극",
        "frequencies": (329.63, 415.3, 493.88),
        "description": "사람 사는 하소연처럼 풀어낸 코믹 장면을 위한 통통 튀는 무보컬 리듬",
    },
}
EMOTION_CONFIDENCE_LABELS = {
    "observed": "관찰",
    "caregiver_report": "보호자 설명",
    "inference": "행동 해석",
}
MEDIA_SUFFIXES = {".mp4", ".mov", ".mkv", ".webm"}
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}
AUDIO_SUFFIXES = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"}
FONT_CANDIDATES = (
    Path("/System/Library/Fonts/AppleSDGothicNeo.ttc"),
    Path("/Library/Fonts/NotoSansKR-Regular.otf"),
    Path("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
)
ALLOWED_EDIT_ACTIONS = {
    "crop_9_16",
    "reframe_subject",
    "slow_zoom",
    "freeze_frame",
    "focus_arrow",
    "source_audio_duck",
    "korean_caption_safe_area",
    "source_caption_safe_reframe",
    "source_caption_blur",
    "source_attribution",
    "no_scene_transition",
    "hold_last_frame",
    "ai_reconstruction_label",
}
SOURCE_CAPTION_MODES = {
    "not_detected",
    "preserve",
    "preserve_and_localize_bottom",
    "blur_and_localize_bottom",
}
EDIT_ACTION_LABELS = {
    "crop_9_16": "9:16 세로 크롭",
    "reframe_subject": "피사체 중심 리프레임",
    "slow_zoom": "완만한 확대",
    "freeze_frame": "핵심 프레임 정지",
    "focus_arrow": "화살표·강조 표시",
    "source_audio_duck": "원본 오디오를 낮춰 사용",
    "korean_caption_safe_area": "별도 안전 영역에 짧은 한국어 화면 문구 배치",
    "source_caption_safe_reframe": "하단 패널에 가려지는 원본 자막을 화면 이동으로 안전 영역에 보존",
    "source_caption_blur": "검토한 원본 외국어 자막 영역만 선택적으로 블러 처리",
    "source_attribution": "출처·제작자 표기",
    "no_scene_transition": "장면 사이 페이드·전환 효과 없음",
    "hold_last_frame": "결론 장면의 마지막 유효 프레임을 짧게 고정",
    "ai_reconstruction_label": "AI 재현 또는 합성 장면 표기",
}


class TikTok2ShortsError(RuntimeError):
    pass


def now_kst() -> dt.datetime:
    return dt.datetime.now(KST)


def iso_now() -> str:
    return now_kst().isoformat(timespec="seconds")


def fail(message: str, exit_code: int = 1) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(exit_code)


def load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError as exc:
        raise TikTok2ShortsError(f"필수 파일이 없습니다: {path}") from exc
    except json.JSONDecodeError as exc:
        raise TikTok2ShortsError(f"JSON 형식이 잘못되었습니다: {path}: {exc}") from exc


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def resolve_project_path(project_dir: Path, relative: str, *, must_exist: bool = True) -> Path:
    if not relative:
        raise TikTok2ShortsError("빈 프로젝트 상대 경로는 사용할 수 없습니다.")
    candidate = (project_dir / relative).resolve()
    try:
        candidate.relative_to(project_dir.resolve())
    except ValueError as exc:
        raise TikTok2ShortsError(f"프로젝트 밖의 경로는 사용할 수 없습니다: {relative}") from exc
    if must_exist and not candidate.is_file():
        raise TikTok2ShortsError(f"프로젝트 파일을 찾을 수 없습니다: {relative}")
    return candidate


def relative_project_path(project_dir: Path, path: Path) -> str:
    return str(path.resolve().relative_to(project_dir.resolve()))


def sha256_for(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def media_duration_seconds(path: Path) -> float | None:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        return None
    result = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            str(path),
        ],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    if result.returncode:
        return None
    try:
        duration = float(json.loads(result.stdout)["format"]["duration"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None
    return round(duration, 3) if duration >= 0 else None


def require_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TikTok2ShortsError(f"{label}은(는) JSON 객체여야 합니다.")
    return value


def require_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise TikTok2ShortsError(f"{label}은(는) 배열이어야 합니다.")
    return value


def text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TikTok2ShortsError(f"{label}은(는) 0 이상의 숫자여야 합니다.")
    if value < 0:
        raise TikTok2ShortsError(f"{label}은(는) 0 이상의 숫자여야 합니다.")
    return float(value)


def parse_datetime(value: Any, label: str) -> dt.datetime:
    raw = text(value)
    if not raw:
        raise TikTok2ShortsError(f"{label} 시간이 비어 있습니다.")
    try:
        parsed = dt.datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as exc:
        raise TikTok2ShortsError(f"{label} 시간이 ISO 8601 형식이 아닙니다: {raw}") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=KST)
    return parsed.astimezone(KST)


def slugify(value: str) -> str:
    value = re.sub(r"[^0-9A-Za-z가-힣]+", "-", value.strip().lower())
    return value.strip("-")[:72] or "tiktok-short"


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(value, maximum))


def candidate_records(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        candidates = payload
    else:
        root = require_object(payload, "후보 입력")
        candidates = root.get("ranked_candidates", root.get("candidates"))
    candidates = require_list(candidates, "candidates 또는 ranked_candidates")

    records: list[dict[str, Any]] = []
    for index, item in enumerate(candidates, start=1):
        entry = require_object(item, f"후보 {index}")
        candidate = entry.get("candidate", entry)
        candidate = require_object(candidate, f"후보 {index}")
        candidate_id = text(candidate.get("id"))
        if not candidate_id:
            raise TikTok2ShortsError(f"후보 {index}에 id가 없습니다.")
        if not text(candidate.get("url")):
            raise TikTok2ShortsError(f"후보 {candidate_id}에 원본 URL이 없습니다.")
        records.append(
            {
                "candidate": candidate,
                "viral_assessment": entry.get("viral_assessment", candidate.get("viral_assessment")),
                "whiteboard_fit_assessment": entry.get(
                    "whiteboard_fit_assessment",
                    candidate.get("whiteboard_fit_assessment"),
                ),
            }
        )
    return records


def normalise_metrics(candidate: dict[str, Any]) -> list[dict[str, Any]]:
    metrics = require_list(candidate.get("metrics", []), f"후보 {candidate['id']}의 metrics")
    points: list[dict[str, Any]] = []
    for index, item in enumerate(metrics, start=1):
        point = require_object(item, f"후보 {candidate['id']}의 metrics[{index}]")
        collected_at = parse_datetime(point.get("collected_at"), f"metrics[{index}].collected_at")
        values = {
            "views": number(point.get("views"), f"metrics[{index}].views"),
            "likes": number(point.get("likes", 0), f"metrics[{index}].likes"),
            "comments": number(point.get("comments", 0), f"metrics[{index}].comments"),
            "shares": number(point.get("shares", 0), f"metrics[{index}].shares"),
        }
        if any(value < 0 for value in values.values()):
            raise TikTok2ShortsError(f"후보 {candidate['id']}의 metrics[{index}]에는 음수 지표를 사용할 수 없습니다.")
        points.append({"collected_at": collected_at, **values})
    points.sort(key=lambda point: point["collected_at"])
    for previous, current in zip(points, points[1:]):
        if previous["collected_at"] == current["collected_at"]:
            raise TikTok2ShortsError(f"후보 {candidate['id']}에 같은 수집 시각이 중복되었습니다.")
    return points


def candidate_age_hours(candidate: dict[str, Any], latest_collected_at: dt.datetime) -> float | None:
    published_at = text(candidate.get("published_at"))
    if not published_at:
        return None
    return max(0.0, (latest_collected_at - parse_datetime(published_at, "published_at")).total_seconds() / 3600)


def animal_candidate_issues(candidate: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    if text(candidate.get("platform")).lower() != "tiktok":
        issues.append("이 플러그인은 TikTok 동물 쇼츠만 후보로 받습니다.")
    if text(candidate.get("category")).lower() not in ANIMAL_CATEGORIES:
        issues.append("category는 animals, pets, wildlife 등 동물 카테고리여야 합니다.")
    animal = candidate.get("animal")
    if not isinstance(animal, dict):
        issues.append("animal 객체에 종과 실제 행동 근거를 기록해야 합니다.")
    else:
        if not text(animal.get("species")):
            issues.append("animal.species에 동물 종 또는 품종이 필요합니다.")
        if len(text(animal.get("observable_behavior"))) < 12:
            issues.append("animal.observable_behavior에는 실제로 보이는 행동을 12자 이상 기록해야 합니다.")
    return issues


def candidate_quality_issues(candidate: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    parsed = urlparse(text(candidate.get("url")))
    hostname = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or not (hostname == "tiktok.com" or hostname.endswith(".tiktok.com")):
        issues.append("TikTok 원본 HTTPS URL이 필요합니다.")
    issues.extend(animal_candidate_issues(candidate))
    if not text(candidate.get("creator")):
        issues.append("원본 creator가 필요합니다.")
    if not text(candidate.get("collector")):
        issues.append("후보 수집 경로 collector가 필요합니다.")
    metrics_source = urlparse(text(candidate.get("metrics_source_url")))
    if metrics_source.scheme != "https" or not metrics_source.hostname:
        issues.append("지표 확인 근거인 metrics_source_url이 필요합니다.")
    if not text(candidate.get("published_at")):
        issues.append("원본 published_at이 필요합니다.")
    if not (text(candidate.get("title")) or text(candidate.get("description"))):
        issues.append("내용을 판단할 title 또는 description이 필요합니다.")
    if len(text(candidate.get("content_summary"))) < 20:
        issues.append("실제 장면을 설명하는 content_summary가 20자 이상 필요합니다.")
    return issues


def proven_viral_classification(latest_views: float) -> str:
    if latest_views >= 10_000_000:
        return "mass_viral"
    if latest_views >= PROVEN_VIRAL_STRONG_VIEWS:
        return "major_viral"
    return "confirmed_viral"


def calculate_viral_assessment(candidate: dict[str, Any]) -> dict[str, Any]:
    points = normalise_metrics(candidate)
    quality_issues = candidate_quality_issues(candidate)
    if not points:
        return {
            "status": "rejected",
            "viral_score": None,
            "classification": "not_proven_viral",
            "qualification": {
                "eligible": False,
                "reasons": ["검증 가능한 조회수 관측값이 없습니다.", *quality_issues],
            },
        }

    first = points[0]
    latest = points[-1]
    latest_views = max(latest["views"], 1.0)
    latest_interactions = latest["likes"] + latest["comments"] + latest["shares"]
    share_rate = latest["shares"] / latest_views
    comment_rate = latest["comments"] / latest_views
    like_rate = latest["likes"] / latest_views
    engagement_rate = latest_interactions / latest_views
    age_hours = candidate_age_hours(candidate, latest["collected_at"])

    elapsed_hours: float | None = None
    view_delta: float | None = None
    view_velocity: float | None = None
    acceleration: float | None = None
    if len(points) >= 2:
        elapsed_hours = (latest["collected_at"] - first["collected_at"]).total_seconds() / 3600
        if elapsed_hours <= 0:
            raise TikTok2ShortsError(f"후보 {candidate['id']}의 수집 간격이 올바르지 않습니다.")
        view_delta = max(0.0, latest["views"] - first["views"])
        view_velocity = view_delta / elapsed_hours
    if len(points) >= 3:
        previous = points[-2]
        before_previous = points[-3]
        current_hours = (latest["collected_at"] - previous["collected_at"]).total_seconds() / 3600
        previous_hours = (previous["collected_at"] - before_previous["collected_at"]).total_seconds() / 3600
        previous_velocity = max(0.0, previous["views"] - before_previous["views"]) / previous_hours
        current_velocity = max(0.0, latest["views"] - previous["views"]) / current_hours
        acceleration = 2.0 if previous_velocity == 0 and current_velocity > 0 else (
            current_velocity / previous_velocity if previous_velocity > 0 else 0.0
        )

    proof_signals: list[str] = []
    if latest_views >= PROVEN_VIRAL_STRONG_VIEWS:
        proof_signals.append(f"조회수 {latest_views:,.0f}회")
    if latest["shares"] >= PROVEN_VIRAL_MIN_SHARES:
        proof_signals.append(f"공유 {latest['shares']:,.0f}회")
    if latest_interactions >= PROVEN_VIRAL_MIN_INTERACTIONS:
        proof_signals.append(f"상호작용 {latest_interactions:,.0f}회")
    if engagement_rate >= PROVEN_VIRAL_MIN_ENGAGEMENT_RATE:
        proof_signals.append(f"참여율 {engagement_rate:.1%}")

    rejection_reasons = list(quality_issues)
    if latest_views < PROVEN_VIRAL_MIN_VIEWS:
        rejection_reasons.append(f"최신 조회수가 {PROVEN_VIRAL_MIN_VIEWS:,.0f}회 미만입니다.")
    elif not proof_signals:
        rejection_reasons.append("조회수 외에 대규모 도달 또는 참여를 확인할 보조 신호가 부족합니다.")
    eligible = not rejection_reasons

    components = {
        "absolute_views": round(50.0 * clamp(math.log10(latest_views) / 7.0, 0.0, 1.0), 2),
        "absolute_shares": round(20.0 * clamp(math.log10(latest["shares"] + 1.0) / 5.0, 0.0, 1.0), 2),
        "engagement_rate": round(15.0 * clamp(engagement_rate / 0.12, 0.0, 1.0), 2),
        "absolute_comments": round(5.0 * clamp(math.log1p(latest["comments"]) / math.log1p(50_000), 0.0, 1.0), 2),
        "source_quality": 10.0 if not quality_issues else round(10.0 * clamp(1.0 - len(quality_issues) / 5.0, 0.0, 1.0), 2),
    }
    score = round(sum(components.values()), 2)
    return {
        "status": "confirmed_viral" if eligible else "rejected",
        "viral_score": score if eligible else None,
        "classification": proven_viral_classification(latest_views) if eligible else "not_proven_viral",
        "qualification": {
            "eligible": eligible,
            "proof_signals": proof_signals,
            "reasons": rejection_reasons,
            "thresholds": {
                "minimum_views": PROVEN_VIRAL_MIN_VIEWS,
                "strong_views": PROVEN_VIRAL_STRONG_VIEWS,
                "minimum_shares": PROVEN_VIRAL_MIN_SHARES,
                "minimum_interactions": PROVEN_VIRAL_MIN_INTERACTIONS,
                "minimum_engagement_rate": PROVEN_VIRAL_MIN_ENGAGEMENT_RATE,
            },
        },
        "metrics_window": {
            "first_collected_at": first["collected_at"].isoformat(timespec="seconds"),
            "latest_collected_at": latest["collected_at"].isoformat(timespec="seconds"),
            "elapsed_hours": round(elapsed_hours, 2) if elapsed_hours is not None else None,
        },
        "observed_metrics": {
            "latest_views": round(latest["views"], 2),
            "latest_likes": round(latest["likes"], 2),
            "latest_comments": round(latest["comments"], 2),
            "latest_shares": round(latest["shares"], 2),
            "latest_interactions": round(latest_interactions, 2),
            "view_delta": round(view_delta, 2) if view_delta is not None else None,
            "view_velocity_per_hour": round(view_velocity, 2) if view_velocity is not None else None,
            "acceleration": round(acceleration, 3) if acceleration is not None else None,
            "share_rate": round(share_rate, 5),
            "comment_rate": round(comment_rate, 5),
            "like_rate": round(like_rate, 5),
            "engagement_rate": round(engagement_rate, 5),
            "age_hours": round(age_hours, 2) if age_hours is not None else None,
        },
        "components": components,
        "method_note": (
            "이 점수는 이미 확인된 절대 조회수·공유·상호작용과 출처 완성도를 비교합니다. "
            "성장 속도와 가속도는 참고값일 뿐 선정 자격이나 점수에 사용하지 않습니다."
        ),
    }


def opportunity_assessment(candidate: dict[str, Any], viral_score: float | None) -> dict[str, Any]:
    relevance = candidate.get("korea_relevance_score")
    saturation = candidate.get("youtube_korea_saturation_score")
    if viral_score is None or relevance is None or saturation is None:
        return {
            "opportunity_score": None,
            "status": "research_required",
            "reason": "바이럴 점수와 근거가 있는 한국 관련성·국내 YouTube 포화도 점수가 모두 필요합니다.",
        }
    relevance_number = number(relevance, "korea_relevance_score")
    saturation_number = number(saturation, "youtube_korea_saturation_score")
    if relevance_number > 100 or saturation_number > 100:
        raise TikTok2ShortsError("한국 관련성과 YouTube 포화도 점수는 0~100이어야 합니다.")
    score = round(viral_score * 0.55 + relevance_number * 0.30 + (100.0 - saturation_number) * 0.15, 2)
    return {
        "opportunity_score": score,
        "status": "scored",
        "components": {
            "viral_score": viral_score,
            "korea_relevance_score": relevance_number,
            "youtube_korea_saturation_score": saturation_number,
        },
        "method_note": "입력자가 근거 링크와 함께 확인한 비교 가정입니다. 사실이나 수익을 보장하지 않습니다.",
    }


def whiteboard_fit_assessment(candidate: dict[str, Any], viral_score: float | None) -> dict[str, Any]:
    reasons: list[str] = []
    fit_root = candidate.get("format_fit")
    fit = fit_root.get("whiteboard") if isinstance(fit_root, dict) else None
    if not isinstance(fit, dict):
        fit = {}
        reasons.append("format_fit.whiteboard 근거가 필요합니다.")

    def scored_evidence(key: str, label: str, maximum: float) -> float:
        value = fit.get(key)
        if not isinstance(value, dict):
            reasons.append(f"format_fit.whiteboard.{key} 점수와 근거가 필요합니다.")
            return 0.0
        raw_score = value.get("score")
        if isinstance(raw_score, bool) or not isinstance(raw_score, (int, float)):
            reasons.append(f"{label} 점수는 0~{maximum:g} 숫자여야 합니다.")
            score = 0.0
        else:
            score = float(raw_score)
            if not 0.0 <= score <= maximum:
                reasons.append(f"{label} 점수는 0~{maximum:g} 범위여야 합니다.")
                score = 0.0
        if len(text(value.get("evidence"))) < 12:
            reasons.append(f"{label}에는 관찰 가능한 근거를 12자 이상 기록해야 합니다.")
        return score

    hook_score = scored_evidence("hook", "첫 2초 화이트보드 훅", 20.0)
    payoff_score = scored_evidence("abstraction_payoff", "추상화 후 결말", 20.0)
    composition_score = scored_evidence("composition", "윤곽·구도 명확성", 10.0)

    raw_beats = fit.get("distinct_visual_beats")
    valid_actions: set[str] = set()
    if not isinstance(raw_beats, list):
        reasons.append("format_fit.whiteboard.distinct_visual_beats 배열이 필요합니다.")
        raw_beats = []
    for index, raw_beat in enumerate(raw_beats, start=1):
        if not isinstance(raw_beat, dict):
            reasons.append(f"화이트보드 행동 장면 {index}는 객체여야 합니다.")
            continue
        action = text(raw_beat.get("observed_action"))
        time_reference = text(raw_beat.get("time_reference"))
        if len(action) < 12:
            reasons.append(f"화이트보드 행동 장면 {index}의 observed_action을 12자 이상 기록해야 합니다.")
            continue
        if not time_reference:
            reasons.append(f"화이트보드 행동 장면 {index}의 time_reference가 필요합니다.")
            continue
        valid_actions.add(action)
    distinct_beat_count = len(valid_actions)
    if distinct_beat_count < WHITEBOARD_FIT_MIN_DISTINCT_BEATS:
        reasons.append(f"서로 다른 화이트보드 행동 장면이 최소 {WHITEBOARD_FIT_MIN_DISTINCT_BEATS}개 필요합니다.")
    distinct_beats_score = min(20.0, distinct_beat_count * 5.0)

    raw_disqualifiers = fit.get("disqualifiers")
    if not isinstance(raw_disqualifiers, list):
        reasons.append("format_fit.whiteboard.disqualifiers 배열이 필요합니다.")
        disqualifiers: list[str] = []
    else:
        disqualifiers = [text(item) for item in raw_disqualifiers if text(item)]
    if disqualifiers:
        reasons.append("화이트보드 부적합 요인이 있습니다: " + ", ".join(disqualifiers))

    viral_component = 0.0
    if viral_score is None:
        reasons.append("검증된 바이럴 점수가 필요합니다.")
    else:
        viral_component = round(viral_score * 0.25, 2)

    relevance = candidate.get("korea_relevance_score")
    if isinstance(relevance, bool) or not isinstance(relevance, (int, float)):
        reasons.append("korea_relevance_score가 필요합니다.")
        korean_component = 0.0
    else:
        relevance_number = float(relevance)
        if not 0.0 <= relevance_number <= 100.0:
            reasons.append("korea_relevance_score는 0~100 범위여야 합니다.")
            korean_component = 0.0
        else:
            korean_component = round(relevance_number * 0.05, 2)

    if hook_score < WHITEBOARD_FIT_MIN_HOOK:
        reasons.append(f"첫 2초 화이트보드 훅 점수가 {WHITEBOARD_FIT_MIN_HOOK:g}점 미만입니다.")
    if payoff_score < WHITEBOARD_FIT_MIN_PAYOFF:
        reasons.append(f"추상화 후 결말 점수가 {WHITEBOARD_FIT_MIN_PAYOFF:g}점 미만입니다.")
    if composition_score < WHITEBOARD_FIT_MIN_COMPOSITION:
        reasons.append(f"윤곽·구도 명확성 점수가 {WHITEBOARD_FIT_MIN_COMPOSITION:g}점 미만입니다.")

    components = {
        "verified_viral": viral_component,
        "first_two_seconds_hook": hook_score,
        "distinct_visual_beats": distinct_beats_score,
        "abstraction_payoff": payoff_score,
        "composition_clarity": composition_score,
        "korea_relevance": korean_component,
    }
    score = round(sum(components.values()), 2)
    if score < WHITEBOARD_FIT_MIN_SCORE:
        reasons.append(f"화이트보드 후보 점수가 {WHITEBOARD_FIT_MIN_SCORE:g}점 미만입니다.")
    reasons = list(dict.fromkeys(reasons))
    return {
        "target_format": "whiteboard",
        "eligible": not reasons,
        "score": score,
        "threshold": WHITEBOARD_FIT_MIN_SCORE,
        "components": components,
        "distinct_visual_beat_count": distinct_beat_count,
        "disqualifiers": disqualifiers,
        "reasons": reasons,
        "method_note": (
            "검증된 원본 성과 25, 첫 2초 훅 20, 서로 다른 행동 20, 추상화 후 결말 20, "
            "윤곽·구도 10, 한국 관련성 5를 비교합니다. 점수는 성과를 보장하지 않습니다."
        ),
    }


def command_score(args: argparse.Namespace) -> int:
    records = candidate_records(load_json(Path(args.input)))
    target_format = text(args.target_format)
    ranked: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for record in records:
        assessment = calculate_viral_assessment(record["candidate"])
        opportunity = opportunity_assessment(record["candidate"], assessment["viral_score"])
        entry = {
            "candidate": record["candidate"],
            "viral_assessment": assessment,
            "opportunity_assessment": opportunity,
        }
        if target_format == "whiteboard":
            fit_assessment = whiteboard_fit_assessment(record["candidate"], assessment["viral_score"])
            entry["whiteboard_fit_assessment"] = fit_assessment
            qualified = assessment["qualification"]["eligible"] and fit_assessment["eligible"]
        else:
            qualified = assessment["qualification"]["eligible"]
        (ranked if qualified else rejected).append(entry)
    if target_format == "whiteboard":
        ranked.sort(
            key=lambda entry: (
                entry["whiteboard_fit_assessment"]["score"],
                entry["viral_assessment"]["viral_score"] or -1,
            ),
            reverse=True,
        )
    else:
        ranked.sort(
            key=lambda entry: (
                entry["viral_assessment"]["viral_score"] or -1,
                entry["opportunity_assessment"]["opportunity_score"] or -1,
            ),
            reverse=True,
        )
    for index, entry in enumerate(ranked, start=1):
        entry["rank"] = index
    result = {
        "version": 4,
        "generated_at": iso_now(),
        "ranking_basis": {
            "viral_score": "확인된 절대 조회수 50, 절대 공유 20, 참여율 15, 절대 댓글 5, 출처 품질 10",
            "qualification": "TikTok 동물 후보 중 조회수 100만 이상이며 조회 300만, 공유 1만, 상호작용 10만, 참여율 8% 중 하나 이상을 확인한 후보만 포함",
            "animal_gate": "platform=tiktok, 동물 category, animal.species, animal.observable_behavior를 모두 확인한 후보만 포함",
            "opportunity_score": "선정 후 참고값: 바이럴 55, 한국 관련성 30, 국내 YouTube 저포화도 15",
        },
        "ranked_candidates": ranked,
        "rejected_candidates": rejected,
    }
    if target_format == "whiteboard":
        result["target_format"] = "whiteboard"
        result["ranking_basis"]["whiteboard_fit"] = (
            "바이럴 25, 첫 2초 훅 20, 서로 다른 행동 20, 추상화 후 결말 20, 윤곽·구도 10, 한국 관련성 5; "
            "70점과 필수 하한을 모두 통과한 후보만 포함"
        )
    write_json(Path(args.output), result)
    print(f"qualified {len(ranked)} of {len(records)} candidates: {args.output}")
    return 0


def selected_record(payload: Any, candidate_id: str) -> dict[str, Any]:
    for record in candidate_records(payload):
        if text(record["candidate"].get("id")) == candidate_id:
            return record
    raise TikTok2ShortsError(f"candidate_id를 찾을 수 없습니다: {candidate_id}")


def rights_status(candidate: dict[str, Any]) -> tuple[str, str]:
    rights = candidate.get("rights", {})
    rights = rights if isinstance(rights, dict) else {}
    status = text(rights.get("permission_status") or rights.get("status")) or "unknown"
    reference = text(rights.get("permission_reference"))
    if status not in KNOWN_RIGHTS_STATUSES:
        raise TikTok2ShortsError(
            "rights.permission_status는 owned, licensed, permission_confirmed, unknown, review_required, not_permitted 중 하나여야 합니다."
        )
    return status, reference


def candidate_is_sensitive(candidate: dict[str, Any]) -> bool:
    category = text(candidate.get("category")).lower()
    animal = candidate.get("animal")
    welfare_risk = bool(animal.get("welfare_risk")) if isinstance(animal, dict) else False
    return category in RISK_CATEGORIES or bool(candidate.get("sensitive_topic")) or welfare_risk


def write_project_skeleton(project_dir: Path, record: dict[str, Any]) -> None:
    candidate = record["candidate"]
    assessment = record.get("viral_assessment")
    whiteboard_assessment = record.get("whiteboard_fit_assessment")
    permission_status, permission_reference = rights_status(candidate)
    title = text(candidate.get("title")) or text(candidate.get("description")) or candidate["id"]
    sensitive = candidate_is_sensitive(candidate)
    created_at = iso_now()
    source_creator = text(candidate.get("creator")).lstrip("@")
    channel_label = f"TikTok @{source_creator}" if source_creator else "원본 TikTok 채널"

    project = {
        "version": 2,
        "title": title,
        "slug": project_dir.name,
        "created_at": created_at,
        "updated_at": created_at,
        "timezone": "Asia/Seoul",
        "status": "research_pending",
        "production_mode": "animal-emotion-explainer",
        "distribution_mode": "local_only",
        "template": {
            "id": "animal-emotion-story-v1",
            "description": "상단 고정 채널 정보, 중앙 원본 장면, 하단 역할·상황극 자막을 사용합니다.",
            "channel_label": channel_label,
            "source_caption_handling": {
                "mode": "not_detected",
                "detected": False,
                "language": "",
                "bridges": [],
                "review_note": "미리보기 프레임에서 원본 내장 자막을 확인한 뒤 갱신합니다.",
            },
        },
        "render_profile": {
            "width": 720,
            "height": 1280,
            "frame_rate": 30,
            "video_codec": "h264",
            "audio_codec": "aac",
        },
        "sensitive_topic": sensitive,
        "source_clip_policy": {
            "full_video_reupload": False,
            "translation_overlay_only": False,
            "max_seconds_per_source_clip": 8,
            "max_total_source_clip_seconds": 18,
            "note": "원본은 필요한 맥락을 보여주는 자료 화면으로만 사용합니다. 권리와 변형적 사용 판단은 별도 검토가 필요합니다.",
        },
        "approvals": {
            "editorial_reviewed": False,
            "translation_reviewed": False,
            "rights_reviewed": False,
            "altered_content_disclosure_reviewed": False,
        },
    }
    source = {
        "version": 1,
        "candidate_id": candidate["id"],
        "platform": text(candidate.get("platform")) or "tiktok",
        "original_url": candidate["url"],
        "creator": text(candidate.get("creator")),
        "published_at": text(candidate.get("published_at")),
        "collector": text(candidate.get("collector")),
        "collected_at": text(candidate.get("collected_at")),
        "rights": {
            "permission_status": permission_status,
            "permission_reference": permission_reference,
            "review_note": "",
        },
        "candidate_snapshot": candidate,
        "viral_assessment": assessment,
        "source_media": [],
    }
    if isinstance(whiteboard_assessment, dict):
        project["downstream_target"] = "whiteboard-shorts"
        source["whiteboard_fit_assessment"] = whiteboard_assessment
    analysis = {
        "version": 2,
        "status": "pending",
        "transcript": {
            "language": "",
            "text": "",
            "source": "",
            "reviewed": False,
        },
        "visual_summary": "",
        "viral_reason": "",
        "korean_angle": "",
        "korean_explanation": "",
        "fact_sources": [],
        "translation_notes": [],
        "sensitive_content_note": "",
        "animal_analysis": {
            "species": text(require_object(candidate.get("animal"), "candidate.animal").get("species")),
            "context": "",
            "observed_behaviors": [],
            "emotion_interpretation_note": "감정은 단정하지 않고 영상에서 확인한 행동과 보호자 설명을 바탕으로 관찰 또는 해석으로 구분합니다.",
            "welfare_or_safety_note": "",
        },
    }
    commentary_plan = {
        "version": 2,
        "format": "animal-emotion-explainer",
        "target_duration_seconds": 32,
        "beats": [
            {"id": "beat-01", "type": "hook", "purpose": "동물의 실제 행동이 드러나는 장면과 상황을 먼저 제시합니다."},
            {"id": "beat-02", "type": "context", "purpose": "종·장소·관계를 확인 가능한 범위에서 설명합니다."},
            {"id": "beat-03", "type": "evidence", "purpose": "행동 신호와 감정 해석의 근거를 짧은 원본 장면으로 보여 줍니다."},
            {"id": "beat-04", "type": "turn", "purpose": "행동 변화 또는 보호자 반응을 실제 장면으로 연결합니다."},
            {"id": "beat-05", "type": "payoff", "purpose": "동물의 안전·관계·행동 변화가 확인되는 장면을 충분히 보여 줍니다."},
            {"id": "beat-06", "type": "conclusion", "purpose": "원본에서 확인한 최종 상태와 과장 없는 행동 해석으로 마무리합니다."},
        ],
    }
    script = {
        "version": 1,
        "hook": "",
        "segments": [],
        "storyboard_override": {
            "enabled": False,
            "scenes": [],
        },
        "review_note": "시나리오는 별도 전달 문서로 제공하고, 영상에는 검토된 짧은 화면 문구와 동물 행동·감정 해석만 남깁니다. 감정은 단정하지 않고 장면의 animal_emotion.confidence를 관찰·보호자 설명·행동 해석으로 표시합니다.",
    }
    storyboard = {
        "version": 2,
        "format": "animal-emotion-story-v1",
        "scenes": [],
    }
    music_plan = {
        "version": 1,
        "mode": "synthetic_ambient",
        "profile_id": "",
        "selection": "auto_from_scene_emotion",
        "reason": "장면별 동물 행동·감정 해석이 채워진 뒤 무보컬 앰비언트 프로필을 자동 선택합니다.",
        "vocals": False,
        "external_track": False,
        "rights": {
            "permission_status": "owned",
            "note": "렌더러가 새로 만든 무보컬 톤 베드이며 외부 음원을 사용하지 않습니다.",
        },
    }
    rights_manifest = {
        "version": 1,
        "source": {
            "original_url": candidate["url"],
            "creator": text(candidate.get("creator")),
            "permission_status": permission_status,
            "permission_reference": permission_reference,
        },
        "assets": [],
        "note": "로컬 제작에 사용한 원본과 보조 자산의 출처 및 확인된 권리 정보를 기록합니다.",
    }
    publish = {
        "version": 1,
        "title_candidates": [],
        "description": "",
        "hashtags": [],
        "source_attribution": "",
        "altered_or_synthetic_content": False,
        "disclosure_note": "",
    }

    write_json(project_dir / "project.json", project)
    write_json(project_dir / "source.json", source)
    write_json(project_dir / "viral-analysis.json", analysis)
    write_json(project_dir / "commentary-plan.json", commentary_plan)
    write_json(project_dir / "script.json", script)
    write_json(project_dir / "storyboard.json", storyboard)
    write_json(project_dir / "music-plan.json", music_plan)
    write_json(project_dir / "rights-manifest.json", rights_manifest)
    write_json(project_dir / "publish.json", publish)
    (project_dir / "assets" / "source").mkdir(parents=True, exist_ok=True)
    (project_dir / "assets" / "supporting").mkdir(parents=True, exist_ok=True)
    (project_dir / "outputs").mkdir(parents=True, exist_ok=True)


def command_init(args: argparse.Namespace) -> int:
    record = selected_record(load_json(Path(args.candidates)), args.candidate_id)
    candidate = record["candidate"]
    title = text(candidate.get("title")) or text(candidate.get("description")) or candidate["id"]
    output_root = Path(args.output_root)
    date_path = now_kst().date().isoformat()
    project_dir = output_root / date_path / slugify(title)
    if project_dir.exists():
        raise TikTok2ShortsError(f"이미 같은 프로젝트 경로가 있습니다: {project_dir}")
    write_project_skeleton(project_dir, record)
    print(f"initialized animal-emotion template local-only project: {project_dir}")
    return 0


def load_project_package(project_dir: Path, names: tuple[str, ...]) -> dict[str, dict[str, Any]]:
    package: dict[str, dict[str, Any]] = {}
    for name in names:
        package[name] = require_object(load_json(project_dir / name), name)
    return package


def download_rights_gate(source: dict[str, Any]) -> str:
    rights = require_object(source.get("rights"), "source.rights")
    status = text(rights.get("permission_status"))
    reference = text(rights.get("permission_reference"))
    if status == "not_permitted":
        raise TikTok2ShortsError("not_permitted로 기록된 원본은 다운로드할 수 없습니다.")
    if status not in LOCAL_USE_RIGHTS_STATUSES:
        raise TikTok2ShortsError("로컬 다운로드에는 source.json의 권리 상태를 먼저 기록하세요.")
    if status in ALLOWED_RIGHTS_STATUSES and reference:
        return "rights_cleared"
    return "local_personal_use"


def source_media_by_id(source: dict[str, Any], project_dir: Path, *, files_required: bool) -> dict[str, dict[str, Any]]:
    media = require_list(source.get("source_media"), "source_media")
    records: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(media, start=1):
        record = require_object(item, f"source_media[{index}]")
        media_id = text(record.get("id"))
        relative_path = text(record.get("relative_path"))
        if not media_id or not relative_path:
            raise TikTok2ShortsError(f"source_media[{index}]에 id와 relative_path가 필요합니다.")
        if media_id in records:
            raise TikTok2ShortsError(f"source_media ID가 중복되었습니다: {media_id}")
        resolve_project_path(project_dir, relative_path, must_exist=files_required)
        records[media_id] = record
    return records


def source_download_file(project_dir: Path) -> Path | None:
    source_dir = project_dir / "assets" / "source"
    if not source_dir.is_dir():
        return None
    candidates = [
        path for path in source_dir.iterdir()
        if path.is_file() and path.suffix.lower() in MEDIA_SUFFIXES and path.name.startswith("source.")
    ]
    if not candidates:
        return None
    if len(candidates) > 1:
        raise TikTok2ShortsError("assets/source에 source.* 영상이 여러 개입니다. 자동 다운로드 파일을 하나만 유지하세요.")
    return candidates[0]


def command_download(args: argparse.Namespace) -> int:
    project_dir = Path(args.project_dir).resolve()
    if not project_dir.is_dir():
        raise TikTok2ShortsError(f"프로젝트 폴더를 찾을 수 없습니다: {project_dir}")
    if importlib.util.find_spec("yt_dlp") is None:
        raise TikTok2ShortsError(
            "yt-dlp가 설치되지 않았습니다. 이 플러그인 환경에 yt-dlp를 설치한 뒤 doctor를 다시 실행하세요."
        )
    package = load_project_package(project_dir, ("project.json", "source.json", "rights-manifest.json"))
    source = package["source.json"]
    rights_manifest = package["rights-manifest.json"]
    project = package["project.json"]
    acquisition_scope = download_rights_gate(source)

    original_url = text(source.get("original_url"))
    parsed = urlparse(original_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.username or parsed.password:
        raise TikTok2ShortsError("자동 다운로드는 사용자 정보가 없는 http 또는 https 원본 URL만 사용할 수 있습니다.")

    existing_media = source_media_by_id(source, project_dir, files_required=False)
    if "source-video-01" in existing_media:
        existing_path = resolve_project_path(project_dir, text(existing_media["source-video-01"].get("relative_path")), must_exist=False)
        if existing_path.is_file():
            print(f"source already downloaded: {existing_path}")
            return 0
        raise TikTok2ShortsError("기존 source-video-01 기록이 있으나 파일이 없습니다. 무단 덮어쓰기를 막기 위해 중단합니다.")
    if source_download_file(project_dir):
        raise TikTok2ShortsError("다운로드 영상이 이미 있습니다. source.json에 기록을 먼저 복구하거나 별도 프로젝트를 사용하세요.")

    source_dir = project_dir / "assets" / "source"
    source_dir.mkdir(parents=True, exist_ok=True)
    output_template = source_dir / "source.%(ext)s"
    command = [
        sys.executable,
        "-m",
        "yt_dlp",
        "--no-config",
        "--no-playlist",
        "--no-progress",
        "--no-warnings",
        "--max-filesize",
        args.max_filesize,
        "--format",
        "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/b",
        "--merge-output-format",
        "mp4",
        "--write-info-json",
        "--no-overwrites",
        "--output",
        str(output_template),
        original_url,
    ]
    result = subprocess.run(
        command,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode:
        detail = (result.stderr or result.stdout).strip().splitlines()[-1:] or ["unknown error"]
        raise TikTok2ShortsError(f"원본 다운로드에 실패했습니다: {detail[0]}")

    downloaded = source_download_file(project_dir)
    if downloaded is None:
        raise TikTok2ShortsError("yt-dlp가 완료되었지만 예상한 원본 영상 파일을 찾지 못했습니다.")
    metadata_path = downloaded.with_suffix(".info.json")
    source_rights = require_object(source.get("rights"), "source.rights")
    media_record = {
        "id": "source-video-01",
        "relative_path": relative_project_path(project_dir, downloaded),
        "metadata_path": relative_project_path(project_dir, metadata_path) if metadata_path.is_file() else "",
        "downloaded_at": iso_now(),
        "download_method": "yt-dlp public URL without cookies or login",
        "original_url": original_url,
        "rights_status": text(source_rights.get("permission_status")),
        "rights_reference": text(source_rights.get("permission_reference")),
        "acquisition_scope": acquisition_scope,
        "sha256": sha256_for(downloaded),
        "file_size_bytes": downloaded.stat().st_size,
        "duration_seconds": media_duration_seconds(downloaded),
    }
    source["source_media"] = [*require_list(source.get("source_media"), "source_media"), media_record]
    source["download"] = {
        "status": "completed",
        "downloaded_at": media_record["downloaded_at"],
        "tool": "yt-dlp",
        "authentication": "none",
        "scope": acquisition_scope,
    }
    project["status"] = "source_downloaded"
    project["updated_at"] = iso_now()
    assets = require_list(rights_manifest.get("assets"), "rights-manifest.assets")
    assets.append(
        {
            "id": "source-video-01",
            "kind": "source_video",
            "relative_path": media_record["relative_path"],
            "original_url": original_url,
            "creator": text(source.get("creator")),
            "permission_status": media_record["rights_status"],
            "permission_reference": media_record["rights_reference"],
            "acquisition_scope": acquisition_scope,
            "sha256": media_record["sha256"],
        }
    )
    rights_manifest["assets"] = assets
    write_json(project_dir / "project.json", project)
    write_json(project_dir / "source.json", source)
    write_json(project_dir / "rights-manifest.json", rights_manifest)
    label = "rights-cleared source" if acquisition_scope == "rights_cleared" else "local-use source"
    print(f"downloaded {label}: {downloaded}")
    return 0


def command_preview(args: argparse.Namespace) -> int:
    project_dir = Path(args.project_dir).resolve()
    if not project_dir.is_dir():
        raise TikTok2ShortsError(f"프로젝트 폴더를 찾을 수 없습니다: {project_dir}")
    if not shutil.which("ffmpeg"):
        raise TikTok2ShortsError("편집 위치 미리보기에는 ffmpeg가 필요합니다.")
    if args.interval <= 0 or args.max_frames < 1:
        raise TikTok2ShortsError("interval은 0보다 크고 max_frames는 1 이상이어야 합니다.")
    package = load_project_package(project_dir, ("project.json", "source.json"))
    project = package["project.json"]
    source = package["source.json"]
    source_media = source_media_by_id(source, project_dir, files_required=True)
    if "source-video-01" not in source_media:
        raise TikTok2ShortsError("미리보기 전에 승인된 원본을 download 명령으로 내려받으세요.")
    media = source_media["source-video-01"]
    source_path = resolve_project_path(project_dir, text(media.get("relative_path")))
    frames_dir = project_dir / "assets" / "analysis" / "frames"
    if frames_dir.exists() and any(frames_dir.iterdir()):
        raise TikTok2ShortsError("기존 미리보기 프레임이 있습니다. 원본과 다른 프레임을 섞지 않도록 새 프로젝트를 사용하세요.")
    frames_dir.mkdir(parents=True, exist_ok=True)
    frame_pattern = frames_dir / "frame-%03d.jpg"
    result = subprocess.run(
        [
            shutil.which("ffmpeg") or "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(source_path),
            "-vf",
            f"fps=1/{args.interval},scale=480:-2",
            "-frames:v",
            str(args.max_frames),
            str(frame_pattern),
        ],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode:
        detail = result.stderr.strip().splitlines()[-1:] or ["unknown error"]
        raise TikTok2ShortsError(f"원본 미리보기 프레임 생성에 실패했습니다: {detail[0]}")
    frames = sorted(path for path in frames_dir.glob("frame-*.jpg") if path.is_file())
    if not frames:
        raise TikTok2ShortsError("ffmpeg가 완료되었지만 미리보기 프레임을 만들지 못했습니다.")
    preview = {
        "version": 1,
        "generated_at": iso_now(),
        "source_media_id": "source-video-01",
        "source_relative_path": text(media.get("relative_path")),
        "sample_interval_seconds": args.interval,
        "timestamps_are_approximate": True,
        "frames": [
            {
                "index": index,
                "approx_source_seconds": round((index - 1) * args.interval, 2),
                "relative_path": relative_project_path(project_dir, path),
            }
            for index, path in enumerate(frames, start=1)
        ],
    }
    write_json(project_dir / "preview.json", preview)
    source["analysis_preview"] = {
        "relative_path": "preview.json",
        "generated_at": preview["generated_at"],
        "frame_count": len(frames),
        "sample_interval_seconds": args.interval,
    }
    project["status"] = "source_preview_ready"
    project["updated_at"] = iso_now()
    write_json(project_dir / "source.json", source)
    write_json(project_dir / "project.json", project)
    print(f"generated {len(frames)} approximate timeline frames: {frames_dir}")
    return 0


def timecode(seconds: float) -> str:
    whole_seconds = int(seconds)
    minutes, remaining_seconds = divmod(whole_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    fraction = seconds - whole_seconds
    if hours:
        return f"{hours:02d}:{minutes:02d}:{remaining_seconds + fraction:05.2f}"
    return f"{minutes:02d}:{remaining_seconds + fraction:05.2f}"


def edit_actions(scene: dict[str, Any], index: int) -> list[str]:
    actions = require_list(scene.get("edit_actions"), f"scene {index}.edit_actions")
    values: list[str] = []
    for action in actions:
        value = text(action)
        if value not in ALLOWED_EDIT_ACTIONS:
            choices = ", ".join(sorted(ALLOWED_EDIT_ACTIONS))
            raise TikTok2ShortsError(f"scene {index}의 edit_actions 값이 올바르지 않습니다: {value}. 허용값: {choices}")
        values.append(value)
    if not values:
        raise TikTok2ShortsError(f"scene {index}에는 적어도 하나의 edit_actions 값이 필요합니다.")
    return values


def source_caption_blur_region(scene: dict[str, Any], index: int) -> dict[str, float]:
    region = require_object(scene.get("source_caption_blur_region"), f"scene {index}.source_caption_blur_region")
    values = {
        key: number(region.get(key), f"scene {index}.source_caption_blur_region.{key}")
        for key in ("x", "y", "width", "height", "radius")
    }
    if not 0 <= values["x"] < 1 or not 0 <= values["y"] < 1:
        raise TikTok2ShortsError(f"scene {index}.source_caption_blur_region의 x, y는 0 이상 1 미만이어야 합니다.")
    if not 0 < values["width"] <= 1 or not 0 < values["height"] <= 1:
        raise TikTok2ShortsError(f"scene {index}.source_caption_blur_region의 width, height는 0 초과 1 이하여야 합니다.")
    if values["x"] + values["width"] > 1 or values["y"] + values["height"] > 1:
        raise TikTok2ShortsError(f"scene {index}.source_caption_blur_region이 원본 프레임 범위를 벗어납니다.")
    if not 4 <= values["radius"] <= 40:
        raise TikTok2ShortsError(f"scene {index}.source_caption_blur_region.radius는 4~40 범위여야 합니다.")
    return values


def hold_last_frame_seconds(scene: dict[str, Any], index: int) -> float:
    seconds = number(scene.get("hold_last_frame_seconds"), f"scene {index}.hold_last_frame_seconds")
    if not 0.2 <= seconds <= 2:
        raise TikTok2ShortsError(f"scene {index}.hold_last_frame_seconds는 0.2~2초 범위여야 합니다.")
    return seconds


def hold_last_frame_source_offset_seconds(scene: dict[str, Any], index: int) -> float:
    seconds = number(
        scene.get("hold_last_frame_source_offset_seconds", 0),
        f"scene {index}.hold_last_frame_source_offset_seconds",
    )
    if not 0 <= seconds <= 1:
        raise TikTok2ShortsError(f"scene {index}.hold_last_frame_source_offset_seconds는 0~1초 범위여야 합니다.")
    return seconds


def project_source_caption_handling(project: dict[str, Any]) -> dict[str, Any]:
    template = project.get("template")
    if not isinstance(template, dict):
        return {}
    handling = template.get("source_caption_handling")
    return handling if isinstance(handling, dict) else {}


def validate_source_caption_handling(project: dict[str, Any], scenes: list[Any]) -> list[str]:
    """Validate the reviewed source-caption treatment and its Korean reading path."""
    errors: list[str] = []
    handling = project_source_caption_handling(project)
    if not handling:
        return errors

    mode = text(handling.get("mode"))
    detected = handling.get("detected")
    if mode not in SOURCE_CAPTION_MODES:
        errors.append("project.template.source_caption_handling.mode가 올바르지 않습니다.")
    if not isinstance(detected, bool):
        errors.append("project.template.source_caption_handling.detected는 true 또는 false여야 합니다.")
        return errors

    raw_bridges = handling.get("bridges")
    if not isinstance(raw_bridges, list):
        errors.append("project.template.source_caption_handling.bridges는 배열이어야 합니다.")
        return errors
    if not detected:
        if mode != "not_detected":
            errors.append("원본 내장 자막이 없으면 source_caption_handling.mode는 not_detected여야 합니다.")
        if raw_bridges:
            errors.append("원본 내장 자막이 없으면 source_caption_handling.bridges는 비어 있어야 합니다.")
        return errors

    if not text(handling.get("language")):
        errors.append("확인된 원본 내장 자막의 language를 기록해야 합니다.")
    if mode == "not_detected":
        errors.append("원본 내장 자막이 확인되면 source_caption_handling.mode를 보존 또는 블러 처리 모드로 바꾸세요.")
    if mode in {"preserve_and_localize_bottom", "blur_and_localize_bottom"} and not raw_bridges:
        errors.append("외국어 원본 자막을 한국어로 연결할 source_caption_handling.bridges가 필요합니다.")

    blur_scene_count = 0
    for index, scene_value in enumerate(scenes, start=1):
        if not isinstance(scene_value, dict):
            continue
        actions = scene_value.get("edit_actions")
        if not isinstance(actions, list) or "source_caption_blur" not in actions:
            continue
        blur_scene_count += 1
        if "source_caption_safe_reframe" in actions:
            errors.append(f"scene {index}에는 source_caption_blur와 source_caption_safe_reframe을 함께 사용할 수 없습니다.")
    if mode == "blur_and_localize_bottom" and blur_scene_count == 0:
        errors.append("blur_and_localize_bottom 모드에는 source_caption_blur 편집 장면이 필요합니다.")
    if mode != "blur_and_localize_bottom" and blur_scene_count:
        errors.append("source_caption_blur 편집은 source_caption_handling.mode가 blur_and_localize_bottom일 때만 사용할 수 있습니다.")

    scenes_by_id = {
        text(scene.get("id")): scene
        for value in scenes
        if isinstance(value, dict)
        for scene in [value]
        if text(scene.get("id"))
    }
    for index, value in enumerate(raw_bridges, start=1):
        if not isinstance(value, dict):
            errors.append(f"source_caption_handling.bridges[{index}]는 객체여야 합니다.")
            continue
        scene_id = text(value.get("scene_id"))
        source_text = text(value.get("source_text"))
        korean_text = text(value.get("korean_text"))
        if not scene_id or not source_text or not korean_text:
            errors.append(f"source_caption_handling.bridges[{index}]에는 scene_id, source_text, korean_text가 필요합니다.")
            continue
        scene = scenes_by_id.get(scene_id)
        if scene is None:
            errors.append(f"source_caption_handling.bridges[{index}].scene_id를 storyboard에서 찾을 수 없습니다: {scene_id}")
            continue
        if text(scene.get("korean_caption")) != korean_text:
            errors.append(f"{scene_id}의 korean_caption은 source_caption_handling bridge의 korean_text와 같아야 합니다.")
    return errors


def build_edit_plan_lines(
    project_dir: Path,
    project: dict[str, Any],
    source: dict[str, Any],
    scenes: list[Any],
    music_choice: dict[str, Any],
    *,
    rendered_durations: list[float] | None = None,
) -> list[str]:
    source_media = source_media_by_id(source, project_dir, files_required=True)
    if not scenes:
        raise TikTok2ShortsError("편집 계획을 만들려면 storyboard.json에 장면이 최소 하나 필요합니다.")
    if rendered_durations is not None and len(rendered_durations) != len(scenes):
        raise TikTok2ShortsError("실제 렌더 장면 길이와 스토리보드 장면 수가 일치하지 않습니다.")

    lines = [
        f"# {text(project.get('title')) or project_dir.name} 편집 지시서",
        "",
        "## 공통 원칙",
        "",
        "- 원본 전체를 재업로드하지 않고, 원본 화면과 짧은 한국어 화면 문구로 맥락을 전달합니다.",
        "- 시나리오 전문과 TTS는 영상에 넣지 않고 delivery-note.md에 분리합니다.",
        "- 장면의 동물 감정은 확정 사실처럼 말하지 않고 관찰·보호자 설명·행동 해석 중 하나로 표시합니다.",
        f"- 배경음: {text(music_choice.get('label'))} ({text(music_choice.get('profile_id'))}) — {text(music_choice.get('description'))}",
        "- 원본 워터마크와 출처 표시는 보존합니다. 한국어 화면 문구는 별도 안전 영역에 둡니다.",
        "- 원본 인물의 말이나 사실관계를 바꾸지 않습니다. AI 재현 장면은 별도 표기를 사용합니다.",
        "- 장면 위치는 " + ("최종 MP4의 실제 렌더 길이" if rendered_durations is not None else "스토리보드 요청 길이") + "를 기준으로 기록합니다.",
        "",
        "## 장면별 수정 위치와 방법",
    ]
    if text(music_choice.get("mode")) == "licensed_track":
        track = require_object(music_choice.get("track"), "resolved music track")
        lines[-1:-1] = [
            f"- 음악 원본: {text(track.get('title'))} — {text(track.get('creator'))} / {text(track.get('source_url'))}",
            f"- 음악 라이선스: {text(track.get('license'))} / {text(track.get('license_url'))}",
            f"- 음악 출처 문구: {text(track.get('attribution'))}",
            "",
        ]
    source_caption_handling = project_source_caption_handling(project)
    if source_caption_handling.get("detected") is True:
        caption_mode = text(source_caption_handling.get("mode"))
        bridge_summaries = [
            f"{text(item.get('scene_id'))}: {text(item.get('source_text'))} → {text(item.get('korean_text'))}"
            for item in source_caption_handling.get("bridges", [])
            if isinstance(item, dict)
        ]
        lines[-1:-1] = [
            f"- 원본 내장 자막 처리: {caption_mode} / 언어 {text(source_caption_handling.get('language'))}",
            (
                "- 검토한 원본 자막 사각 영역만 블러하고, 큰 하단 한국어 자막에 뜻과 상황극 훅을 통합합니다."
                if caption_mode == "blur_and_localize_bottom"
                else "- 원문은 화면에 보존하고 큰 하단 한국어 자막에 뜻과 상황극 훅을 통합합니다."
            ),
            *[f"- 원문 연결: {summary}" for summary in bridge_summaries],
            "",
        ]
    timeline_position = 0.0
    for index, scene_value in enumerate(scenes, start=1):
        scene = require_object(scene_value, f"scene {index}")
        scene_id = text(scene.get("id")) or f"scene-{index:02d}"
        duration = rendered_durations[index - 1] if rendered_durations is not None else number(scene.get("duration"), f"scene {index}.duration")
        narration = text(scene.get("korean_narration"))
        caption = text(scene.get("korean_caption"))
        role = text(scene.get("role")) or "commentary"
        emotion = scene_animal_emotion(scene, index)
        emotion_evidence = [
            text(item)
            for item in require_list(emotion.get("evidence"), f"scene {index}.animal_emotion.evidence")
            if text(item)
        ]
        actions = edit_actions(scene, index)
        lines.extend(
            [
                "",
                f"### {index}. {scene_id} ({role})",
                "",
                f"- 최종 영상 위치: {timecode(timeline_position)} ~ {timecode(timeline_position + duration)} ({duration:g}초)",
                f"- 별도 시나리오 문구: {narration or '[작성 필요]'}",
                f"- 화면 자막: {caption or '[작성 필요]'}",
                f"- 동물 행동·감정 표시: {EMOTION_CONFIDENCE_LABELS.get(text(emotion.get('confidence')), '[작성 필요]')} · {text(emotion.get('label')) or '[작성 필요]'}",
                f"- 감정 근거: {' / '.join(emotion_evidence) or '[작성 필요]'}",
                f"- 장면 음악 큐: {text(emotion.get('music_mood')) or '[작성 필요]'}",
                "- 수정 방식:",
            ]
        )
        lines.extend([f"  - {EDIT_ACTION_LABELS[action]}" for action in actions])
        if "source_caption_blur" in actions:
            region = source_caption_blur_region(scene, index)
            lines.append(
                "  - 블러 좌표(원본 프레임 비율): "
                f"x={region['x']:.3f}, y={region['y']:.3f}, "
                f"width={region['width']:.3f}, height={region['height']:.3f}, radius={region['radius']:.0f}"
            )
        if "hold_last_frame" in actions:
            lines.append(f"  - 마지막 프레임 고정 시간: {hold_last_frame_seconds(scene, index):g}초")
            lines.append(
                f"  - 마지막 유효 프레임 선택 위치: 원본 구간 끝에서 "
                f"{hold_last_frame_source_offset_seconds(scene, index):g}초 앞"
            )

        source_seconds = number(scene.get("source_clip_seconds", 0), f"scene {index}.source_clip_seconds")
        if source_seconds:
            source_id = text(scene.get("source_clip_id"))
            if source_id not in source_media:
                raise TikTok2ShortsError(f"scene {index}의 source_clip_id를 source.json에서 찾을 수 없습니다: {source_id}")
            source_start = number(scene.get("source_start_seconds"), f"scene {index}.source_start_seconds")
            media = source_media[source_id]
            media_duration = media.get("duration_seconds")
            if isinstance(media_duration, (int, float)) and source_start + source_seconds > float(media_duration) + 0.01:
                raise TikTok2ShortsError(f"scene {index}의 원본 범위가 다운로드된 영상 길이를 벗어납니다.")
            lines.extend(
                [
                    f"- 원본 사용 위치: {text(media.get('relative_path'))}",
                    f"- 원본 구간: {timecode(source_start)} ~ {timecode(source_start + source_seconds)} ({source_seconds:g}초)",
                ]
            )
        else:
            lines.append("- 원본 클립: 사용하지 않음. 해설용 보조 화면·그래픽 또는 권리 확인된 자산을 사용합니다.")
        timeline_position += duration
    return lines


def write_edit_plan(
    project_dir: Path,
    project: dict[str, Any],
    source: dict[str, Any],
    scenes: list[Any],
    music_choice: dict[str, Any],
    *,
    rendered_durations: list[float] | None = None,
) -> Path:
    lines = build_edit_plan_lines(
        project_dir,
        project,
        source,
        scenes,
        music_choice,
        rendered_durations=rendered_durations,
    )
    plan_path = project_dir / "edit-plan.md"
    plan_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return plan_path


def write_delivery_note(
    project_dir: Path,
    project: dict[str, Any],
    source: dict[str, Any],
    script: dict[str, Any],
    scenes: list[Any],
    output: Path,
    music_choice: dict[str, Any],
    *,
    script_override_applied: bool,
) -> Path:
    original_url = text(source.get("original_url"))
    creator = text(source.get("creator"))
    lines = [
        f"# {text(project.get('title')) or project_dir.name} 전달 안내",
        "",
        "## 결과물",
        "",
        f"- 로컬 MP4: {relative_project_path(project_dir, output)}",
        "- 영상에는 TTS·외부 내레이션 파일·시나리오 전문을 넣지 않습니다.",
        f"- 대본 오버라이드 반영: {'예' if script_override_applied else '아니오'}",
        "",
        "## 원본 링크",
        "",
        f"- 제작자: {creator or '미상'}",
        f"- TikTok 원본: {original_url or '기록 없음'}",
        "",
    ]
    source_caption_handling = project_source_caption_handling(project)
    if source_caption_handling.get("detected") is True:
        caption_mode = text(source_caption_handling.get("mode"))
        lines.extend(
            [
                "## 원본 내장 자막",
                "",
                f"- 처리: {caption_mode}",
                f"- 언어: {text(source_caption_handling.get('language'))}",
                (
                    "- 검토한 원본 자막 영역만 블러하고 큰 하단 한국어 자막에 뜻과 상황극 훅을 통합했습니다."
                    if caption_mode == "blur_and_localize_bottom"
                    else "- 원문은 화면에 보존하고 큰 하단 한국어 자막에 뜻과 상황극 훅을 통합했습니다."
                ),
            ]
        )
        for item in source_caption_handling.get("bridges", []):
            if isinstance(item, dict):
                lines.append(
                    f"- {text(item.get('scene_id'))}: {text(item.get('source_text'))} → {text(item.get('korean_text'))}"
                )
        lines.append("")
    lines.extend(
        [
            "## 배경음",
            "",
            f"- 프로필: {text(music_choice.get('label'))} ({text(music_choice.get('profile_id'))})",
            f"- 선택 근거: {text(music_choice.get('description'))}",
        ]
    )
    if text(music_choice.get("mode")) == "licensed_track":
        track = require_object(music_choice.get("track"), "resolved music track")
        lines.extend(
            [
                f"- 곡: {text(track.get('title'))} — {text(track.get('creator'))}",
                f"- 원본: {text(track.get('source_url'))}",
                f"- 라이선스: {text(track.get('license'))} — {text(track.get('license_url'))}",
                f"- 필수 출처 문구: {text(track.get('attribution'))}",
                "- 원곡의 일부를 길이에 맞게 잘라 배경음으로 사용했습니다.",
                "",
            ]
        )
    else:
        lines.extend(["- 외부 음원·보컬 없이 렌더러가 생성한 무보컬 음악입니다.", ""])
    conclusion = next(
        (
            require_object(scene_value, "storyboard conclusion")
            for scene_value in reversed(scenes)
            if scene_role(require_object(scene_value, "storyboard conclusion")) == "conclusion"
        ),
        None,
    )
    if conclusion:
        lines.extend(
            [
                "## 영상 속 최종 결론",
                "",
                f"- {text(conclusion.get('headline'))}: {text(conclusion.get('korean_caption'))}",
                "",
            ]
        )
    lines.extend(["## 영상 속 동물 행동·감정 해석", ""])
    for index, scene_value in enumerate(scenes, start=1):
        scene = require_object(scene_value, f"scene {index}")
        emotion = scene_animal_emotion(scene, index)
        basis = [text(item) for item in require_list(emotion.get("evidence"), f"scene {index}.animal_emotion.evidence") if text(item)]
        lines.append(
            f"- {text(scene.get('id')) or f'scene-{index:02d}'}: "
            f"{EMOTION_CONFIDENCE_LABELS.get(text(emotion.get('confidence')), '행동 해석')} · "
            f"{text(emotion.get('label'))} (근거: {' / '.join(basis)})"
        )
    lines.append("")
    lines.extend(["## 영상에 포함하지 않은 시나리오", ""])
    segments = nonempty_segments(script)
    scenario_values = [text(segment.get("korean_narration")) for segment in segments]
    for index, scenario in enumerate((value for value in scenario_values if value), start=1):
        lines.append(f"{index}. {scenario}")
    if not any(scenario_values):
        lines.append("- 작성된 시나리오가 없습니다.")

    lines.extend(["", "## 영상에 남긴 화면 문구", ""])
    for index, scene_value in enumerate(scenes, start=1):
        scene = require_object(scene_value, f"scene {index}")
        caption = text(scene.get("korean_caption"))
        if caption:
            lines.append(f"- {text(scene.get('id')) or f'scene-{index:02d}'}: {caption}")
    note_path = project_dir / "delivery-note.md"
    note_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return note_path


def command_edit_plan(args: argparse.Namespace) -> int:
    project_dir = Path(args.project_dir).resolve()
    if not project_dir.is_dir():
        raise TikTok2ShortsError(f"프로젝트 폴더를 찾을 수 없습니다: {project_dir}")
    package = load_project_package(project_dir, ("project.json", "source.json", "script.json", "storyboard.json", "music-plan.json"))
    project = package["project.json"]
    source = package["source.json"]
    script = package["script.json"]
    storyboard = package["storyboard.json"]
    music_plan = package["music-plan.json"]
    scenes, _ = apply_storyboard_override(script, require_list(storyboard.get("scenes"), "storyboard.scenes"))
    music_choice = resolve_music_plan(music_plan, scenes, project_dir=project_dir)

    plan_path = write_edit_plan(project_dir, project, source, scenes, music_choice)
    project["status"] = "edit_plan_ready"
    project["updated_at"] = iso_now()
    project["edit_plan"] = {
        "relative_path": "edit-plan.md",
        "generated_at": iso_now(),
        "source_clip_policy_checked": True,
    }
    write_json(project_dir / "project.json", project)
    print(f"generated edit plan: {plan_path}")
    return 0


def json_file(project_dir: Path, name: str, errors: list[str]) -> dict[str, Any] | None:
    path = project_dir / name
    try:
        return require_object(load_json(path), name)
    except TikTok2ShortsError as exc:
        errors.append(str(exc))
        return None


def nonempty_segments(script: dict[str, Any]) -> list[dict[str, Any]]:
    segments = script.get("segments")
    if not isinstance(segments, list):
        raise TikTok2ShortsError("script.json의 segments는 배열이어야 합니다.")
    return [require_object(segment, "script.json segment") for segment in segments]


def text_includes_keyword(value: str, keywords: list[str]) -> bool:
    return any(keyword in value for keyword in keywords)


def validate_grounded_scene_content(script: dict[str, Any], scenes: list[Any]) -> list[str]:
    """Require each displayed explanation to be tied to an observed source action."""
    errors: list[str] = []
    segments = nonempty_segments(script)
    segments_by_id = {
        text(segment.get("id")): segment
        for segment in segments
        if text(segment.get("id"))
    }
    seen_segment_ids: set[str] = set()

    for index, scene_value in enumerate(scenes, start=1):
        scene = require_object(scene_value, f"scene {index}")
        scene_id = text(scene.get("id")) or f"scene-{index:02d}"
        evidence = require_object(scene.get("source_evidence"), f"scene {index}.source_evidence")
        observed_action = text(evidence.get("observed_action"))
        if not observed_action:
            errors.append(f"scene {index}.source_evidence.observed_action에 원본에서 확인한 실제 동작을 기록하세요.")
        raw_keywords = require_list(evidence.get("keywords"), f"scene {index}.source_evidence.keywords")
        keywords = [text(value) for value in raw_keywords if text(value)]
        if len(keywords) < 2:
            errors.append(f"scene {index}.source_evidence.keywords에는 실제 동물·행동·상호작용을 가리키는 두 개 이상의 핵심어가 필요합니다.")
            continue
        if any(keyword not in observed_action for keyword in keywords):
            errors.append(f"scene {index}.source_evidence.observed_action에는 등록한 핵심어를 모두 포함해야 합니다.")

        segment_id = text(scene.get("script_segment_id"))
        segment = segments_by_id.get(segment_id)
        if not segment:
            errors.append(f"scene {index}.script_segment_id는 script.json의 실제 해설 구간을 가리켜야 합니다.")
            continue
        seen_segment_ids.add(segment_id)
        if text(segment.get("source_scene_id")) != scene_id:
            errors.append(f"script.json의 {segment_id}.source_scene_id는 {scene_id}이어야 합니다.")
        narration = text(segment.get("korean_narration"))
        if not narration or sum(keyword in narration for keyword in keywords) < 2:
            errors.append(f"script.json의 {segment_id}에는 원본 근거 핵심어 두 개 이상을 포함한 실제 해설이 필요합니다.")

        screen_text = " ".join((text(scene.get("headline")), text(scene.get("korean_caption"))))
        if not screen_text or not text_includes_keyword(screen_text, keywords):
            errors.append(f"scene {index}의 headline 또는 korean_caption에는 원본 근거 핵심어가 필요합니다.")

    for segment_id, segment in segments_by_id.items():
        if text(segment.get("kind")) in {"narration", "commentary"} and text(segment.get("korean_narration")) and segment_id not in seen_segment_ids:
            errors.append(f"script.json의 {segment_id}는 어떤 storyboard 장면에도 연결되지 않았습니다.")
    return errors


def scene_animal_emotion(scene: dict[str, Any], index: int) -> dict[str, Any]:
    return require_object(scene.get("animal_emotion"), f"scene {index}.animal_emotion")


def validate_animal_emotion_content(scenes: list[Any]) -> list[str]:
    """Keep animal feelings as evidence-backed interpretation, never as a certainty by default."""
    errors: list[str] = []
    for index, scene_value in enumerate(scenes, start=1):
        scene = require_object(scene_value, f"scene {index}")
        try:
            emotion = scene_animal_emotion(scene, index)
            label = text(emotion.get("label"))
            confidence = text(emotion.get("confidence"))
            mood = text(emotion.get("music_mood"))
            evidence = [text(item) for item in require_list(emotion.get("evidence"), f"scene {index}.animal_emotion.evidence") if text(item)]
            if not label:
                errors.append(f"scene {index}.animal_emotion.label에는 화면에 표시할 동물 행동 해석이 필요합니다.")
            if confidence not in EMOTION_CONFIDENCE_LEVELS:
                errors.append("scene %d.animal_emotion.confidence는 observed, caregiver_report, inference 중 하나여야 합니다." % index)
            if not evidence:
                errors.append(f"scene {index}.animal_emotion.evidence에는 감정 표기의 행동 근거가 필요합니다.")
            if mood not in MUSIC_PROFILES:
                errors.append(f"scene {index}.animal_emotion.music_mood는 지원 음악 프로필이어야 합니다: {', '.join(MUSIC_PROFILES)}")
            source_evidence = require_object(scene.get("source_evidence"), f"scene {index}.source_evidence")
            keywords = [
                text(item)
                for item in require_list(source_evidence.get("keywords"), f"scene {index}.source_evidence.keywords")
                if text(item)
            ]
            combined_evidence = " ".join(evidence)
            if evidence and keywords and not text_includes_keyword(combined_evidence, keywords):
                errors.append(f"scene {index}.animal_emotion.evidence에는 원본 행동 핵심어가 하나 이상 필요합니다.")
        except TikTok2ShortsError as exc:
            errors.append(str(exc))
    return errors


def resolve_music_plan(
    music_plan: dict[str, Any],
    scenes: list[Any],
    *,
    project_dir: Path | None = None,
) -> dict[str, Any]:
    """Choose generated music or a locally stored track with a verified reusable licence."""
    mode = text(music_plan.get("mode"))
    if music_plan.get("vocals") is not False:
        raise TikTok2ShortsError("동물 상황극 템플릿은 보컬 음악을 지원하지 않습니다.")
    rights = require_object(music_plan.get("rights"), "music-plan.rights")
    rights_status = text(rights.get("permission_status"))

    if mode == "licensed_track":
        if music_plan.get("external_track") is not True:
            raise TikTok2ShortsError("licensed_track 모드는 external_track을 true로 기록해야 합니다.")
        if rights_status not in {"licensed", "permission_confirmed"}:
            raise TikTok2ShortsError("라이선스 음악의 권리 상태는 licensed 또는 permission_confirmed여야 합니다.")
        track = require_object(music_plan.get("track"), "music-plan.track")
        relative_path = text(track.get("relative_path"))
        title = text(track.get("title"))
        creator = text(track.get("creator"))
        source_url = text(track.get("source_url"))
        license_name = text(track.get("license"))
        license_url = text(track.get("license_url"))
        attribution = text(track.get("attribution"))
        if not all((relative_path, title, creator, source_url, license_name, license_url, attribution)):
            raise TikTok2ShortsError("licensed_track에는 파일·곡명·제작자·원본 URL·라이선스·출처 문구가 모두 필요합니다.")
        if Path(relative_path).suffix.lower() not in AUDIO_SUFFIXES:
            raise TikTok2ShortsError("licensed_track.relative_path는 지원되는 오디오 파일이어야 합니다.")
        if not source_url.startswith("https://") or not license_url.startswith("https://"):
            raise TikTok2ShortsError("licensed_track의 원본과 라이선스 URL은 HTTPS여야 합니다.")
        if project_dir is not None:
            resolve_project_path(project_dir, relative_path, must_exist=True)
        start_seconds = number(track.get("start_seconds", 0), "music-plan.track.start_seconds")
        volume = number(track.get("volume", 0.16), "music-plan.track.volume")
        if start_seconds < 0:
            raise TikTok2ShortsError("music-plan.track.start_seconds는 0 이상이어야 합니다.")
        if not 0 < volume <= 1:
            raise TikTok2ShortsError("music-plan.track.volume은 0보다 크고 1 이하여야 합니다.")
        profile_id = text(music_plan.get("profile_id")) or "licensed-track"
        return {
            "mode": mode,
            "profile_id": profile_id,
            "selection": "licensed_track",
            "label": f"{title} — {creator}",
            "description": f"{license_name} 조건으로 기록된 무보컬 라이선스 음악",
            "track": {
                "relative_path": relative_path,
                "title": title,
                "creator": creator,
                "source_url": source_url,
                "license": license_name,
                "license_url": license_url,
                "attribution": attribution,
                "isrc": text(track.get("isrc")),
                "start_seconds": start_seconds,
                "volume": volume,
            },
        }

    if mode != "synthetic_ambient":
        raise TikTok2ShortsError("music-plan.json의 mode는 synthetic_ambient 또는 licensed_track이어야 합니다.")
    if music_plan.get("external_track") is not False:
        raise TikTok2ShortsError("synthetic_ambient 모드는 external_track을 false로 기록해야 합니다.")
    if rights_status != "owned":
        raise TikTok2ShortsError("생성 음악의 권리 상태는 owned로 기록해야 합니다.")

    configured = text(music_plan.get("profile_id"))
    if configured:
        if configured not in MUSIC_PROFILES:
            raise TikTok2ShortsError(f"music-plan.profile_id는 지원 음악 프로필이어야 합니다: {', '.join(MUSIC_PROFILES)}")
        profile_id = configured
        selection = "manual"
    else:
        moods: list[str] = []
        for index, scene_value in enumerate(scenes, start=1):
            scene = require_object(scene_value, f"scene {index}")
            emotion = scene_animal_emotion(scene, index)
            mood = text(emotion.get("music_mood"))
            if mood in MUSIC_PROFILES:
                moods.append(mood)
        profile_id = moods[-1] if moods else "gentle"
        selection = "auto_from_scene_emotion"
    return {
        "mode": mode,
        "profile_id": profile_id,
        "selection": selection,
        "label": text(MUSIC_PROFILES[profile_id]["label"]),
        "description": text(MUSIC_PROFILES[profile_id]["description"]),
    }


def apply_storyboard_override(script: dict[str, Any], scenes: list[Any]) -> tuple[list[dict[str, Any]], bool]:
    """Apply only reviewed on-screen text overrides; timing and source ranges stay immutable."""
    original_scenes = [require_object(scene, "storyboard scene") for scene in scenes]
    override_value = script.get("storyboard_override")
    if override_value is None:
        return [dict(scene) for scene in original_scenes], False
    override = require_object(override_value, "script.storyboard_override")
    if override.get("enabled") is not True:
        return [dict(scene) for scene in original_scenes], False

    configured_scenes = require_list(override.get("scenes"), "script.storyboard_override.scenes")
    scene_indexes = {
        text(scene.get("id")): index
        for index, scene in enumerate(original_scenes)
        if text(scene.get("id"))
    }
    updated_scenes = [dict(scene) for scene in original_scenes]
    seen_ids: set[str] = set()
    for override_value in configured_scenes:
        item = require_object(override_value, "script.storyboard_override scene")
        scene_id = text(item.get("scene_id"))
        if not scene_id or scene_id not in scene_indexes:
            raise TikTok2ShortsError("script.storyboard_override의 scene_id가 storyboard.json의 장면을 가리켜야 합니다.")
        if scene_id in seen_ids:
            raise TikTok2ShortsError(f"script.storyboard_override에 중복된 scene_id가 있습니다: {scene_id}")
        seen_ids.add(scene_id)
        target = updated_scenes[scene_indexes[scene_id]]
        applied = False
        for field in ("headline", "korean_caption"):
            if field not in item:
                continue
            value = text(item.get(field))
            if not value:
                raise TikTok2ShortsError(f"script.storyboard_override.{field}은 비워 둘 수 없습니다.")
            target[field] = value
            applied = True
        if not applied:
            raise TikTok2ShortsError(f"script.storyboard_override {scene_id}에는 화면 문구가 하나 이상 필요합니다.")
    return updated_scenes, True


def rights_asset_for_path(rights: dict[str, Any], relative_path: str) -> dict[str, Any] | None:
    normalized = Path(relative_path).as_posix()
    assets = rights.get("assets")
    if not isinstance(assets, list):
        return None
    for item in assets:
        if not isinstance(item, dict):
            continue
        recorded_path = text(item.get("relative_path") or item.get("path"))
        if recorded_path and Path(recorded_path).as_posix() == normalized:
            return item
    return None


def normalized_focus_point(scene: dict[str, Any], index: int) -> tuple[float, float] | None:
    point = scene.get("focus_point")
    if point is None:
        return None
    point = require_object(point, f"scene {index}.focus_point")
    x = number(point.get("x"), f"scene {index}.focus_point.x")
    y = number(point.get("y"), f"scene {index}.focus_point.y")
    if x > 1 or y > 1:
        raise TikTok2ShortsError(f"scene {index}.focus_point의 x와 y는 0~1 범위여야 합니다.")
    return x, y


def validate_project(project_dir: Path, final: bool) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    production_output = final
    if not project_dir.is_dir():
        return [f"프로젝트 폴더를 찾을 수 없습니다: {project_dir}"], warnings

    project = json_file(project_dir, "project.json", errors)
    source = json_file(project_dir, "source.json", errors)
    analysis = json_file(project_dir, "viral-analysis.json", errors)
    script = json_file(project_dir, "script.json", errors)
    storyboard = json_file(project_dir, "storyboard.json", errors)
    music_plan = json_file(project_dir, "music-plan.json", errors)
    rights = json_file(project_dir, "rights-manifest.json", errors)
    publish = json_file(project_dir, "publish.json", errors)
    if any(value is None for value in (project, source, analysis, script, storyboard, music_plan, rights, publish)):
        return errors, warnings
    assert project and source and analysis and script and storyboard and music_plan and rights and publish

    if project.get("production_mode") != "animal-emotion-explainer":
        errors.append("project.json의 production_mode는 animal-emotion-explainer여야 합니다.")
    if project.get("distribution_mode") != "local_only":
        errors.append("project.json의 distribution_mode는 local_only여야 합니다.")
    template = require_object(project.get("template"), "project.template")
    if text(template.get("id")) != "animal-emotion-story-v1":
        errors.append("project.json의 template.id는 animal-emotion-story-v1이어야 합니다.")
    render_profile = require_object(project.get("render_profile"), "render_profile")
    if (render_profile.get("width"), render_profile.get("height")) != (OUTPUT_WIDTH, OUTPUT_HEIGHT):
        errors.append(f"project.json의 render_profile은 {OUTPUT_WIDTH}x{OUTPUT_HEIGHT}여야 합니다.")
    if not text(source.get("original_url")):
        errors.append("source.json에 original_url이 필요합니다.")
    if text(source.get("platform")).lower() != "tiktok":
        errors.append("source.json의 platform은 tiktok이어야 합니다.")
    candidate_snapshot = source.get("candidate_snapshot")
    if not isinstance(candidate_snapshot, dict):
        errors.append("source.json에 동물 후보 근거인 candidate_snapshot이 필요합니다.")
    else:
        errors.extend(animal_candidate_issues(candidate_snapshot))
    if not text(source.get("collector")):
        warnings.append("source.json에 후보를 얻은 허용 수집 도구 또는 원본 경로를 기록하세요.")
    try:
        source_media = source_media_by_id(source, project_dir, files_required=False)
    except TikTok2ShortsError as exc:
        errors.append(str(exc))
        source_media = {}

    source_policy = require_object(project.get("source_clip_policy"), "source_clip_policy")
    max_per_clip = number(source_policy.get("max_seconds_per_source_clip"), "max_seconds_per_source_clip")
    max_total = number(source_policy.get("max_total_source_clip_seconds"), "max_total_source_clip_seconds")
    if source_policy.get("full_video_reupload") is not False:
        errors.append("원본 전체 재업로드는 이 플러그인의 범위가 아닙니다.")
    if source_policy.get("translation_overlay_only") is not False:
        errors.append("단순 번역 자막 덮어쓰기는 이 플러그인의 범위가 아닙니다.")

    scenes = storyboard.get("scenes")
    if not isinstance(scenes, list):
        errors.append("storyboard.json의 scenes는 배열이어야 합니다.")
        scenes = []
    else:
        try:
            scenes, _ = apply_storyboard_override(script, scenes)
        except TikTok2ShortsError as exc:
            errors.append(str(exc))
            scenes = []
    if production_output and scenes:
        try:
            errors.extend(validate_source_caption_handling(project, scenes))
            errors.extend(validate_grounded_scene_content(script, scenes))
            errors.extend(validate_animal_emotion_content(scenes))
            music_choice = resolve_music_plan(music_plan, scenes, project_dir=project_dir)
            if text(music_choice.get("mode")) == "licensed_track":
                track = require_object(music_choice.get("track"), "music-plan.track")
                relative_path = text(track.get("relative_path"))
                asset = rights_asset_for_path(rights, relative_path)
                if asset is None:
                    errors.append("라이선스 음원을 rights-manifest.json assets에 기록해야 합니다.")
                else:
                    if text(asset.get("permission_status")) not in {"licensed", "permission_confirmed"}:
                        errors.append("라이선스 음원의 rights-manifest 권리 상태가 올바르지 않습니다.")
                    for field in ("source_url", "license", "license_url", "attribution", "sha256"):
                        if not text(asset.get(field)):
                            errors.append(f"라이선스 음원의 rights-manifest.{field} 기록이 필요합니다.")
                    recorded_sha256 = text(asset.get("sha256"))
                    if recorded_sha256:
                        track_path = resolve_project_path(project_dir, relative_path, must_exist=True)
                        if sha256_for(track_path) != recorded_sha256:
                            errors.append("라이선스 음원 파일의 SHA-256이 rights-manifest 기록과 다릅니다.")
        except TikTok2ShortsError as exc:
            errors.append(str(exc))
    total_duration = 0.0
    total_source_clip_duration = 0.0
    for index, scene_value in enumerate(scenes, start=1):
        try:
            scene = require_object(scene_value, f"scene {index}")
            duration = number(scene.get("duration"), f"scene {index}.duration")
            if duration <= 0:
                errors.append(f"scene {index}.duration은 0보다 커야 합니다.")
            source_clip_seconds = number(scene.get("source_clip_seconds", 0), f"scene {index}.source_clip_seconds")
            total_duration += duration
            total_source_clip_duration += source_clip_seconds
            actions = edit_actions(scene, index)
            if "source_caption_safe_reframe" in actions:
                source_vertical_shift_pixels = number(
                    scene.get("source_vertical_shift_pixels", 180),
                    f"scene {index}.source_vertical_shift_pixels",
                )
                if not 1 <= source_vertical_shift_pixels <= 400:
                    errors.append(f"scene {index}.source_vertical_shift_pixels는 1~400 범위여야 합니다.")
                if not source_clip_seconds:
                    errors.append(f"scene {index}.source_caption_safe_reframe은 원본 영상 구간에만 사용할 수 있습니다.")
            if "source_caption_blur" in actions:
                if not source_clip_seconds:
                    errors.append(f"scene {index}.source_caption_blur는 원본 영상 구간에만 사용할 수 있습니다.")
                try:
                    source_caption_blur_region(scene, index)
                except TikTok2ShortsError as exc:
                    errors.append(str(exc))
            if "hold_last_frame" in actions:
                try:
                    hold_seconds = hold_last_frame_seconds(scene, index)
                    source_offset = hold_last_frame_source_offset_seconds(scene, index)
                    if not source_clip_seconds:
                        errors.append(f"scene {index}.hold_last_frame은 원본 영상 구간에만 사용할 수 있습니다.")
                    elif source_offset >= source_clip_seconds:
                        errors.append(f"scene {index}.hold_last_frame_source_offset_seconds가 원본 구간보다 짧아야 합니다.")
                    elif abs(duration - (source_clip_seconds - source_offset + hold_seconds)) > 0.05:
                        errors.append(
                            f"scene {index}.duration은 원본 구간에서 마지막 소스 오프셋을 뺀 뒤 고정 시간을 더한 값이어야 합니다."
                        )
                    if text(scene.get("role")) != "conclusion" or index != len(scenes):
                        errors.append("hold_last_frame은 마지막 conclusion 장면에만 사용할 수 있습니다.")
                except TikTok2ShortsError as exc:
                    errors.append(str(exc))
            focus_point = normalized_focus_point(scene, index)
            if "focus_arrow" in actions and focus_point is None:
                errors.append(f"scene {index}의 focus_arrow에는 0~1 좌표 focus_point.x, focus_point.y가 필요합니다.")
            visual_path = text(scene.get("visual_path"))
            if not source_clip_seconds and not visual_path:
                errors.append(f"scene {index}에는 실제 원본 구간 또는 출처가 기록된 visual_path가 필요합니다. 자동 해설 카드는 사용하지 않습니다.")
            if visual_path:
                try:
                    visual = resolve_project_path(project_dir, visual_path, must_exist=production_output)
                    if visual.suffix.lower() not in IMAGE_SUFFIXES | MEDIA_SUFFIXES:
                        errors.append(f"scene {index}.visual_path는 지원되는 이미지 또는 영상이어야 합니다.")
                except TikTok2ShortsError as exc:
                    errors.append(str(exc))
                asset = rights_asset_for_path(rights, visual_path)
                if final:
                    if asset is None:
                        warnings.append(f"scene {index}.visual_path의 출처 기록이 rights-manifest.json에 없습니다.")
                    else:
                        asset_status = text(asset.get("permission_status")) or "unknown"
                        if asset_status == "not_permitted":
                            errors.append(f"scene {index}.visual_path는 not_permitted로 기록되어 사용할 수 없습니다.")
                        elif asset_status not in LOCAL_USE_RIGHTS_STATUSES:
                            warnings.append(f"scene {index}.visual_path의 권리 상태를 확인하세요.")
            if text(scene.get("narration_audio")):
                errors.append(f"scene {index}.narration_audio는 더 이상 지원하지 않습니다. 시나리오는 script.json과 delivery-note.md로 분리하세요.")
            if production_output:
                if not text(scene.get("korean_caption")):
                    errors.append(f"scene {index}에는 최종 영상용 korean_caption이 필요합니다.")
            if source_clip_seconds > max_per_clip:
                errors.append(f"scene {index}의 원본 클립은 {max_per_clip:g}초를 넘을 수 없습니다.")
            if source_clip_seconds:
                source_id = text(scene.get("source_clip_id"))
                if not source_id:
                    errors.append(f"scene {index}의 원본 클립 ID가 없습니다.")
                elif source_id not in source_media:
                    errors.append(f"scene {index}의 source_clip_id를 source.json에서 찾을 수 없습니다: {source_id}")
                else:
                    source_start = number(scene.get("source_start_seconds"), f"scene {index}.source_start_seconds")
                    media_duration = source_media[source_id].get("duration_seconds")
                    if isinstance(media_duration, (int, float)) and source_start + source_clip_seconds > float(media_duration) + 0.01:
                        errors.append(f"scene {index}의 원본 범위가 다운로드된 영상 길이를 벗어납니다.")
        except TikTok2ShortsError as exc:
            errors.append(str(exc))
    if total_source_clip_duration > max_total:
        errors.append(f"원본 클립 총 길이는 {max_total:g}초를 넘을 수 없습니다.")

    if production_output:
        source_rights = require_object(source.get("rights"), "source.rights")
        status = text(source_rights.get("permission_status"))
        approval = require_object(project.get("approvals"), "approvals")
        for key in (
            "editorial_reviewed",
            "translation_reviewed",
            "altered_content_disclosure_reviewed",
        ):
            if approval.get(key) is not True:
                errors.append(f"로컬 결과물 생성 전 approvals.{key}를 검토 후 true로 기록해야 합니다.")
        if status == "not_permitted":
            errors.append("not_permitted로 기록된 원본은 로컬 결과물에도 사용할 수 없습니다.")
        elif status not in LOCAL_USE_RIGHTS_STATUSES:
            errors.append("source.json의 권리 상태를 known 목록 중 하나로 기록하세요.")
        transcript = require_object(analysis.get("transcript"), "viral-analysis.transcript")
        if transcript.get("reviewed") is not True:
            errors.append("최종 준비에는 원문 transcript의 검토 기록이 필요합니다.")
        for field in ("visual_summary", "viral_reason", "korean_angle", "korean_explanation"):
            if not text(analysis.get(field)):
                errors.append(f"최종 준비에는 viral-analysis.json의 {field}가 필요합니다.")
        animal_analysis = require_object(analysis.get("animal_analysis"), "viral-analysis.animal_analysis")
        if not text(animal_analysis.get("species")):
            errors.append("최종 준비에는 viral-analysis.json의 animal_analysis.species가 필요합니다.")
        if len(require_list(animal_analysis.get("observed_behaviors"), "animal_analysis.observed_behaviors")) < 2:
            errors.append("최종 준비에는 animal_analysis.observed_behaviors가 두 개 이상 필요합니다.")
        if not text(animal_analysis.get("welfare_or_safety_note")):
            errors.append("최종 준비에는 animal_analysis.welfare_or_safety_note가 필요합니다.")
        if project.get("sensitive_topic") is True and len(require_list(analysis.get("fact_sources"), "fact_sources")) < 2:
            errors.append("민감 주제 최종 준비에는 독립적인 사실 확인 출처가 최소 2개 필요합니다.")
        try:
            segments = nonempty_segments(script)
            commentary_segments = [
                segment for segment in segments
                if text(segment.get("kind")) in {"narration", "commentary"} and text(segment.get("korean_narration"))
            ]
            if len(commentary_segments) < 3:
                errors.append("최종 준비에는 별도 전달용 한국어 시나리오 구간이 최소 3개 필요합니다.")
        except TikTok2ShortsError as exc:
            errors.append(str(exc))
        if len(scenes) < 4:
            errors.append("최종 준비에는 스토리보드 장면이 최소 4개 필요합니다.")
        elif scene_role(require_object(scenes[-1], "마지막 storyboard 장면")) != "conclusion":
            errors.append("최종 준비에는 실제 완성 화면과 결론 문구를 담은 마지막 conclusion 장면이 필요합니다.")
        if not 15 <= total_duration <= 60:
            errors.append("최종 준비용 스토리보드 길이는 15~60초여야 합니다.")
        assets = rights.get("assets")
        if total_source_clip_duration and not isinstance(assets, list):
            errors.append("원본 클립을 썼다면 rights-manifest.json의 assets 배열이 필요합니다.")
        if total_source_clip_duration and isinstance(assets, list) and not assets:
            warnings.append("원본 클립의 출처 기록을 rights-manifest.json에 추가하세요.")
        if total_source_clip_duration:
            for media_id, media in source_media.items():
                try:
                    resolve_project_path(project_dir, text(media.get("relative_path")), must_exist=True)
                except TikTok2ShortsError as exc:
                    errors.append(f"최종 준비 전 {media_id}: {exc}")
        edit_plan_value = project.get("edit_plan")
        edit_plan = edit_plan_value if isinstance(edit_plan_value, dict) else {}
        if not text(edit_plan.get("relative_path")):
            errors.append("최종 준비에는 edit-plan.md 생성 기록이 필요합니다.")
        else:
            try:
                resolve_project_path(project_dir, text(edit_plan.get("relative_path")), must_exist=True)
            except TikTok2ShortsError as exc:
                errors.append(f"최종 준비 전 편집 지시서를 찾을 수 없습니다: {exc}")
    else:
        if not scenes:
            warnings.append("아직 스토리보드가 비어 있습니다. 동물 후보 선택 후 행동·감정 해설 장면을 작성하세요.")
        if text(source.get("rights", {}).get("permission_status")) not in ALLOWED_RIGHTS_STATUSES:
            warnings.append("원본 영상 권리 상태가 확정되지 않았습니다. 현재 흐름은 로컬 결과물 생성만 지원합니다.")

    return errors, warnings


def command_validate(args: argparse.Namespace) -> int:
    project_dir = Path(args.project_dir)
    errors, warnings = validate_project(project_dir, final=args.final)
    for warning in warnings:
        print(f"warning: {warning}")
    if errors:
        for item in errors:
            print(f"error: {item}", file=sys.stderr)
        return 1
    label = "local render readiness" if args.final else "project skeleton"
    print(f"validated {label}: {project_dir}")
    return 0


def run_checked(command: list[str], label: str) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            command,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except FileNotFoundError as exc:
        raise TikTok2ShortsError(f"{label}에 필요한 명령을 찾을 수 없습니다: {command[0]}") from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or "unknown error").strip().splitlines()
        raise TikTok2ShortsError(f"{label}에 실패했습니다: {detail[-1] if detail else 'unknown error'}") from exc


def find_font() -> Path:
    font = next((candidate for candidate in FONT_CANDIDATES if candidate.is_file()), None)
    if font is None:
        raise TikTok2ShortsError("한국어 자막을 렌더할 글꼴을 찾지 못했습니다. doctor 결과를 확인하세요.")
    return font


def media_probe(path: Path) -> dict[str, Any]:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        raise TikTok2ShortsError("렌더 결과 검증에는 ffprobe가 필요합니다.")
    result = run_checked(
        [ffprobe, "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
        "미디어 정보 확인",
    )
    try:
        payload = require_object(json.loads(result.stdout), "ffprobe 결과")
        streams = require_list(payload.get("streams"), "ffprobe streams")
        video = next((item for item in streams if isinstance(item, dict) and item.get("codec_type") == "video"), None)
        audio = next((item for item in streams if isinstance(item, dict) and item.get("codec_type") == "audio"), None)
        duration = float(require_object(payload.get("format"), "ffprobe format").get("duration", 0))
        video_duration = float(video.get("duration", duration)) if isinstance(video, dict) else 0
        audio_duration = float(audio.get("duration", duration)) if isinstance(audio, dict) else 0
    except (TikTok2ShortsError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise TikTok2ShortsError(f"미디어 정보를 해석할 수 없습니다: {path}") from exc
    return {
        "duration_seconds": round(duration, 3),
        "video_duration_seconds": round(video_duration, 3),
        "audio_duration_seconds": round(audio_duration, 3),
        "video_codec": text(video.get("codec_name")) if isinstance(video, dict) else "",
        "width": video.get("width") if isinstance(video, dict) else None,
        "height": video.get("height") if isinstance(video, dict) else None,
        "audio_codec": text(audio.get("codec_name")) if isinstance(audio, dict) else "",
        "has_video": video is not None,
        "has_audio": audio is not None,
    }


def wrap_caption(draw: Any, value: str, font: Any, max_width: int) -> list[str]:
    lines: list[str] = []
    for paragraph in value.splitlines() or [""]:
        current = ""
        for character in paragraph:
            trial = current + character
            width = draw.textbbox((0, 0), trial, font=font)[2]
            if current and width > max_width:
                lines.append(current.strip())
                current = character.lstrip()
            else:
                current = trial
        if current.strip():
            lines.append(current.strip())
    return lines


def fitted_caption(draw: Any, value: str, *, max_width: int, max_lines: int, start_size: int) -> tuple[Any, list[str]]:
    from PIL import ImageFont

    font_path = find_font()
    for size in range(start_size, 29, -2):
        font = ImageFont.truetype(str(font_path), size=size)
        lines = wrap_caption(draw, value, font, max_width)
        if len(lines) <= max_lines:
            return font, lines
    font = ImageFont.truetype(str(font_path), size=30)
    all_lines = wrap_caption(draw, value, font, max_width)
    lines = all_lines[:max_lines]
    if len(all_lines) > max_lines and lines:
        lines[-1] = lines[-1].rstrip(". ") + "…"
    return font, lines


def draw_centered(draw: Any, lines: list[str], font: Any, y: int, fill: str, spacing: int = 12) -> int:
    for line in lines:
        bounds = draw.textbbox((0, 0), line, font=font)
        width = bounds[2] - bounds[0]
        height = bounds[3] - bounds[1]
        draw.text(((CANVAS_WIDTH - width) / 2, y), line, font=font, fill=fill)
        y += height + spacing
    return y


def draw_focus_arrow(draw: Any, point: tuple[float, float]) -> None:
    target_x, target_y = int(point[0] * CANVAS_WIDTH), int(point[1] * CANVAS_HEIGHT)
    start_x = target_x - 220 if target_x >= CANVAS_WIDTH / 2 else target_x + 220
    start_y = max(510, target_y - 190)
    draw.line((start_x, start_y, target_x, target_y), fill="#FF4D4D", width=22)
    angle = math.atan2(target_y - start_y, target_x - start_x)
    wing = 54
    points = [
        (target_x, target_y),
        (
            target_x - wing * math.cos(angle - math.pi / 6),
            target_y - wing * math.sin(angle - math.pi / 6),
        ),
        (
            target_x - wing * math.cos(angle + math.pi / 6),
            target_y - wing * math.sin(angle + math.pi / 6),
        ),
    ]
    draw.polygon(points, fill="#FF4D4D")


def scene_role(scene: dict[str, Any]) -> str:
    role = text(scene.get("role")).lower()
    return role if role in {"hook", "evidence", "commentary", "payoff", "conclusion"} else "commentary"


def scene_palette(scene: dict[str, Any]) -> tuple[str, str, str]:
    role = scene_role(scene)
    palettes = {
        "hook": ("#FF6B4A", "#FFB15C", "#2A0E13"),
        "evidence": ("#39B8E7", "#7DE2CF", "#08202D"),
        "commentary": ("#8C78FF", "#C7B6FF", "#171233"),
        "payoff": ("#FF815D", "#FFD56A", "#35140E"),
        "conclusion": ("#45D2A4", "#A8EDC6", "#092D25"),
    }
    return palettes[role]


def emotion_palette(scene: dict[str, Any]) -> tuple[str, str]:
    emotion = scene.get("animal_emotion")
    mood = text(emotion.get("music_mood")) if isinstance(emotion, dict) else "gentle"
    palettes = {
        "gentle": ("#2D7A70", "#DDF3ED"),
        "tender": ("#A95466", "#F9E4E8"),
        "tension": ("#86631C", "#FFF1C6"),
        "relief": ("#4475B8", "#E2ECFF"),
        "playful": ("#9A5B13", "#FFF0D8"),
    }
    return palettes.get(mood, palettes["gentle"])


def caption_overlay(
    scene: dict[str, Any],
    project: dict[str, Any],
    *,
    draft: bool,
    credit: str,
) -> Any:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as exc:
        raise TikTok2ShortsError("MP4 렌더에는 현재 환경에 설치된 Pillow가 필요합니다.") from exc

    overlay = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    font_path = find_font()
    small_font = ImageFont.truetype(str(font_path), size=30)
    accent, _ = emotion_palette(scene)
    draw.rectangle((0, 0, CANVAS_WIDTH, 230), fill="#FFFFFF")
    draw.rectangle((0, 216, CANVAS_WIDTH, 230), fill=accent)

    template = project.get("template")
    template = template if isinstance(template, dict) else {}
    channel_label = text(template.get("channel_label"))
    if not channel_label:
        channel_label = credit.removeprefix("출처: ").replace("TikTok / ", "TikTok @") if credit else "원본 TikTok 채널"
    channel_font, channel_lines = fitted_caption(draw, channel_label, max_width=900, max_lines=1, start_size=54)
    draw_centered(draw, channel_lines, channel_font, 76, "#161616", spacing=6)

    draw.rectangle((0, 1360, CANVAS_WIDTH, CANVAS_HEIGHT), fill="#FFFFFF")
    draw.rectangle((0, 1360, CANVAS_WIDTH, 1374), fill=accent)
    headline = text(scene.get("headline"))
    if headline:
        headline_font, headline_lines = fitted_caption(draw, headline, max_width=900, max_lines=2, start_size=40)
        draw_centered(draw, headline_lines, headline_font, 1425, accent, spacing=7)
    caption = text(scene.get("korean_caption"))
    if caption:
        caption_font, caption_lines = fitted_caption(draw, caption, max_width=900, max_lines=3, start_size=60)
        draw_centered(draw, caption_lines, caption_font, 1530, "#111111", spacing=12)

    actions = edit_actions(scene, 0)
    if "focus_arrow" in actions:
        point = normalized_focus_point(scene, 0)
        if point is not None:
            draw_focus_arrow(draw, point)
    if "ai_reconstruction_label" in actions:
        label = "AI 재현 장면"
        bounds = draw.textbbox((0, 0), label, font=small_font)
        label_width = bounds[2] - bounds[0]
        draw.rounded_rectangle((CANVAS_WIDTH - label_width - 105, 43, 1025, 100), radius=17, fill="#F2C45E")
        draw.text((CANVAS_WIDTH - label_width - 82, 54), label, font=small_font, fill="#241900")
    compact_channel = "".join(character.lower() for character in channel_label if character.isalnum())
    compact_credit = "".join(character.lower() for character in credit if character.isalnum())
    if credit and compact_channel not in compact_credit and compact_credit not in compact_channel:
        credit_font, credit_lines = fitted_caption(draw, credit, max_width=820, max_lines=2, start_size=30)
        draw_centered(draw, credit_lines, credit_font, 1814, "#767676", spacing=4)
    if draft:
        label = "검토용"
        bounds = draw.textbbox((0, 0), label, font=small_font)
        label_width = bounds[2] - bounds[0]
        draw.rounded_rectangle((CANVAS_WIDTH - label_width - 105, 1842, 1025, 1897), radius=16, fill="#C73B43")
        draw.text((CANVAS_WIDTH - label_width - 82, 1853), label, font=small_font, fill="#FFFFFF")
    return overlay


def render_static_frame(
    scene: dict[str, Any],
    project: dict[str, Any],
    visual_path: Path | None,
    destination: Path,
    *,
    draft: bool,
    credit: str,
) -> None:
    try:
        from PIL import Image, ImageDraw, ImageFilter, ImageOps
    except ImportError as exc:
        raise TikTok2ShortsError("MP4 렌더에는 현재 환경에 설치된 Pillow가 필요합니다.") from exc

    if visual_path is not None:
        try:
            source = ImageOps.exif_transpose(Image.open(visual_path)).convert("RGB")
        except Exception as exc:
            raise TikTok2ShortsError(f"보조 이미지를 열 수 없습니다: {visual_path}") from exc
        canvas = ImageOps.fit(source, (CANVAS_WIDTH, CANVAS_HEIGHT), method=Image.Resampling.LANCZOS)
        blurred = canvas.filter(ImageFilter.GaussianBlur(radius=16))
        canvas = Image.blend(blurred, Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), "#0B111B"), 0.22)
    else:
        raise TikTok2ShortsError("의미 없는 자동 해설 카드는 렌더하지 않습니다. scene.visual_path 또는 원본 구간을 지정하세요.")
    overlay = caption_overlay(scene, project, draft=draft, credit=credit)
    Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB").save(destination, format="PNG", optimize=True)


def create_silent_audio(path: Path, duration: float) -> None:
    ffmpeg = shutil.which("ffmpeg") or "ffmpeg"
    run_checked(
        [
            ffmpeg,
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
        "무음 트랙 생성",
    )


def create_mood_bed(path: Path, duration: float, profile_id: str) -> None:
    if profile_id not in MUSIC_PROFILES:
        raise TikTok2ShortsError(f"지원하지 않는 음악 프로필입니다: {profile_id}")
    frequencies = MUSIC_PROFILES[profile_id]["frequencies"]
    if profile_id == "playful":
        notes = (329.63, 415.30, 493.88, 659.25, 493.88)
        note_seconds = 0.4
        cycle_seconds = note_seconds * len(notes)
        note_envelope = f"min(1,mod(t,{note_seconds})/0.025)*pow(max(0,1-mod(t,{note_seconds})/{note_seconds}),4)"

        def comic_channel(detune: float) -> str:
            melody = "+".join(
                f"sin(2*PI*{frequency * detune:.3f}*t)*between(mod(t,{cycle_seconds}),{index * note_seconds:.1f},{(index + 1) * note_seconds:.1f})"
                for index, frequency in enumerate(notes)
            )
            bass = (
                f"0.140*sin(2*PI*{164.81 * detune:.3f}*t)"
                "*min(1,mod(t,0.8)/0.025)*pow(max(0,1-mod(t,0.8)/0.8),5)"
            )
            tick = (
                f"0.050*sin(2*PI*{1396.91 * detune:.3f}*t)"
                "*min(1,mod(t,0.2)/0.008)*pow(max(0,1-mod(t,0.2)/0.2),14)"
            )
            return f"0.450*({melody})*({note_envelope})+{bass}+{tick}"

        left = comic_channel(1.0)
        right = comic_channel(1.004)
    else:
        amplitude = "0.018"
        movement = "(0.76+0.24*sin(2*PI*0.23*t))"
        left = amplitude + "*(" + "+".join(f"sin(2*PI*{frequency}*t)" for frequency in frequencies) + ")*" + movement
        right = amplitude + "*(" + "+".join(f"sin(2*PI*{frequency * 1.004:.3f}*t)" for frequency in frequencies) + ")*" + movement
    run_checked(
        [
            shutil.which("ffmpeg") or "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            f"aevalsrc=exprs='{left}|{right}':s=48000:d={duration:.3f}",
            "-c:a",
            "pcm_s16le",
            "-y",
            str(path),
        ],
        "동물 감정용 무보컬 배경음 생성",
    )


def concatenate_mood_beds(paths: list[Path], destination: Path) -> None:
    if not paths:
        raise TikTok2ShortsError("이어 붙일 배경음 구간이 없습니다.")
    concat_file = destination.with_suffix(".txt")
    concat_file.write_text("".join(f"file '{path.as_posix()}'\n" for path in paths), encoding="utf-8")
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
            str(concat_file),
            "-c:a",
            "pcm_s16le",
            "-y",
            str(destination),
        ],
        "장면별 무보컬 배경음 연결",
    )


def align_media_duration(video: Path, output: Path, duration: float) -> None:
    run_checked(
        [
            shutil.which("ffmpeg") or "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(video),
            "-filter_complex",
            f"[0:v]tpad=stop_mode=clone:stop_duration=2,trim=duration={duration:.3f},"
            f"setpts=PTS-STARTPTS,format=yuv420p[v];"
            f"[0:a]apad=pad_dur=2,atrim=duration={duration:.3f},asetpts=PTS-STARTPTS[a]",
            "-map",
            "[v]",
            "-map",
            "[a]",
            "-t",
            f"{duration:.3f}",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "20",
            "-r",
            "30",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-ar",
            "48000",
            "-movflags",
            "+faststart",
            "-y",
            str(output),
        ],
        "최종 영상·오디오 길이 정렬",
    )


def mix_mood_bed(video: Path, mood_bed: Path, output: Path) -> None:
    run_checked(
        [
            shutil.which("ffmpeg") or "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(video),
            "-i",
            str(mood_bed),
            "-filter_complex",
            "[0:a]volume=0.82[scene_audio];[1:a]volume=0.34[mood_bed];"
            "[scene_audio][mood_bed]amix=inputs=2:duration=first:dropout_transition=0[a]",
            "-map",
            "0:v:0",
            "-map",
            "[a]",
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
            str(output),
        ],
        "동물 감정용 배경음 합성",
    )


def mix_licensed_track(
    video: Path,
    track: Path,
    output: Path,
    *,
    duration: float,
    start_seconds: float,
    volume: float,
) -> None:
    fade_out_start = max(0.0, duration - 0.45)
    run_checked(
        [
            shutil.which("ffmpeg") or "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(video),
            "-stream_loop",
            "-1",
            "-ss",
            f"{start_seconds:.3f}",
            "-i",
            str(track),
            "-filter_complex",
            f"[0:a]volume=0.82[scene_audio];"
            f"[1:a]atrim=duration={duration:.3f},asetpts=PTS-STARTPTS,volume={volume:.3f},"
            f"afade=t=in:st=0:d=0.12,afade=t=out:st={fade_out_start:.3f}:d=0.45[music];"
            "[scene_audio][music]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[a]",
            "-map",
            "0:v:0",
            "-map",
            "[a]",
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
            str(output),
        ],
        "라이선스 배경음 합성",
    )


def render_scene_silence(work_dir: Path, index: int, duration: float) -> Path:
    silent = work_dir / f"scene-{index:02d}-silent.wav"
    create_silent_audio(silent, duration)
    return silent


def render_static_scene(
    frame: Path,
    audio: Path,
    destination: Path,
    duration: float,
    *,
    slow_zoom: bool,
) -> None:
    video_filter = (
        "zoompan=z='min(zoom+0.00045,1.045)':x='iw/2-(iw/zoom/2)':"
        f"y='ih/2-(ih/zoom/2)':d=1:s={CANVAS_WIDTH}x{CANVAS_HEIGHT}:fps=30,scale={OUTPUT_WIDTH}:{OUTPUT_HEIGHT}"
        if slow_zoom
        else f"scale={OUTPUT_WIDTH}:{OUTPUT_HEIGHT},fps=30"
    )
    fade_out = max(0.0, duration - 0.15)
    run_checked(
        [
            shutil.which("ffmpeg") or "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-loop",
            "1",
            "-framerate",
            "30",
            "-i",
            str(frame),
            "-i",
            str(audio),
            "-t",
            f"{duration:.3f}",
            "-vf",
            f"{video_filter},fade=t=in:st=0:d=0.12,fade=t=out:st={fade_out:.3f}:d=0.12,format=yuv420p",
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "20",
            "-r",
            "30",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-ar",
            "48000",
            "-af",
            "apad",
            "-movflags",
            "+faststart",
            "-y",
            str(destination),
        ],
        "정적 장면 렌더",
    )


def render_video_scene(
    video: Path,
    overlay: Path,
    audio: Path,
    destination: Path,
    duration: float,
    *,
    start: float,
    input_seconds: float,
    actions: list[str],
    source_vertical_shift_pixels: float = 0,
    source_caption_blur: dict[str, float] | None = None,
    last_frame_hold_seconds: float = 0,
) -> bool:
    probe = media_probe(video)
    has_source_audio = bool(probe["has_audio"])
    use_source_audio = "source_audio_duck" in actions and has_source_audio
    command = [shutil.which("ffmpeg") or "ffmpeg", "-hide_banner", "-loglevel", "error"]
    if start > 0:
        command.extend(["-ss", f"{start:.3f}"])
    command.extend(["-t", f"{input_seconds:.3f}", "-i", str(video)])
    command.extend(["-loop", "1", "-framerate", "30", "-i", str(overlay), "-i", str(audio)])

    if "freeze_frame" in actions:
        video_chain = "trim=start_frame=0:end_frame=1,setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration=90"
    else:
        video_chain = f"trim=duration={input_seconds:.3f},setpts=PTS-STARTPTS"
    video_chain += (
        f",scale={CANVAS_WIDTH}:{CANVAS_HEIGHT}:force_original_aspect_ratio=increase,"
        f"crop={CANVAS_WIDTH}:{CANVAS_HEIGHT},setsar=1"
    )
    if "source_caption_safe_reframe" in actions and source_vertical_shift_pixels > 0:
        shifted_height = CANVAS_HEIGHT - int(source_vertical_shift_pixels)
        video_chain += (
            f",crop={CANVAS_WIDTH}:{shifted_height}:0:{int(source_vertical_shift_pixels)},"
            f"pad={CANVAS_WIDTH}:{CANVAS_HEIGHT}:0:0:black"
        )
    if "slow_zoom" in actions:
        video_chain += (
            ",zoompan=z='min(zoom+0.00045,1.045)':x='iw/2-(iw/zoom/2)':"
            f"y='ih/2-(ih/zoom/2)':d=1:s={CANVAS_WIDTH}x{CANVAS_HEIGHT}:fps=30"
        )
    else:
        video_chain += ",fps=30"
    if "freeze_frame" not in actions:
        pad_seconds = last_frame_hold_seconds + (1 / 30) if last_frame_hold_seconds > 0 else 90
        video_chain += f",tpad=stop_mode=clone:stop_duration={pad_seconds:.3f}"
    transition_filter = ""
    if "no_scene_transition" not in actions:
        fade_out = max(0.0, duration - 0.15)
        transition_filter = f",fade=t=in:st=0:d=0.12,fade=t=out:st={fade_out:.3f}:d=0.12"
    if source_caption_blur is not None:
        blur_x = int(source_caption_blur["x"] * CANVAS_WIDTH)
        blur_y = int(source_caption_blur["y"] * CANVAS_HEIGHT)
        blur_width = int(source_caption_blur["width"] * CANVAS_WIDTH)
        blur_height = int(source_caption_blur["height"] * CANVAS_HEIGHT)
        blur_radius = int(source_caption_blur["radius"])
        filters = (
            f"[0:v]{video_chain},trim=duration={duration:.3f}[base_raw];"
            f"[base_raw]split=2[base][blur_input];"
            f"[blur_input]crop={blur_width}:{blur_height}:{blur_x}:{blur_y},"
            f"boxblur=luma_radius={blur_radius}:luma_power=3:chroma_radius={blur_radius}:chroma_power=3[blurred_caption];"
            f"[base][blurred_caption]overlay={blur_x}:{blur_y}:format=auto[base_blurred];"
            f"[base_blurred][1:v]overlay=0:0:format=auto:shortest=1,scale={OUTPUT_WIDTH}:{OUTPUT_HEIGHT}"
            f"{transition_filter},format=yuv420p[v]"
        )
    else:
        filters = (
            f"[0:v]{video_chain},trim=duration={duration:.3f}[base];"
            f"[base][1:v]overlay=0:0:format=auto:shortest=1,scale={OUTPUT_WIDTH}:{OUTPUT_HEIGHT}"
            f"{transition_filter},format=yuv420p[v]"
        )
    if use_source_audio:
        filters += (
            f";[0:a]atrim=duration={input_seconds:.3f},asetpts=PTS-STARTPTS,volume=0.12,"
            f"apad=pad_dur={duration:.3f}[source_audio];"
            f"[2:a]atrim=duration={duration:.3f},asetpts=PTS-STARTPTS,apad=pad_dur={duration:.3f}[narration];"
            f"[source_audio][narration]amix=inputs=2:duration=longest:dropout_transition=0,"
            f"atrim=duration={duration:.3f}[mixed_audio]"
        )
    command.extend(["-filter_complex", filters, "-map", "[v]"])
    if use_source_audio:
        command.extend(["-map", "[mixed_audio]"])
    else:
        command.extend(["-map", "2:a:0", "-af", "apad"])
    command.extend(
        [
            "-t",
            f"{duration:.3f}",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "20",
            "-r",
            "30",
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
    run_checked(command, "영상 장면 렌더")
    return use_source_audio


def scene_credit(
    scene: dict[str, Any],
    source: dict[str, Any],
    rights: dict[str, Any],
    visual_path: str,
    *,
    source_scene: bool,
) -> str:
    configured = text(scene.get("credit"))
    if configured:
        return configured
    if source_scene:
        creator = text(source.get("creator"))
        return f"출처: TikTok / {creator}" if creator else "출처: 원본 TikTok"
    asset = rights_asset_for_path(rights, visual_path) if visual_path else None
    if asset:
        creator = text(asset.get("creator"))
        return f"출처: {creator}" if creator else ""
    return ""


def command_render(args: argparse.Namespace) -> int:
    project_dir = Path(args.project_dir).resolve()
    if not project_dir.is_dir():
        raise TikTok2ShortsError(f"프로젝트 폴더를 찾을 수 없습니다: {project_dir}")
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise TikTok2ShortsError("MP4 렌더와 결과 검증에는 ffmpeg와 ffprobe가 필요합니다.")
    find_font()
    try:
        import PIL  # noqa: F401
    except ImportError as exc:
        raise TikTok2ShortsError("MP4 렌더에는 현재 환경에 설치된 Pillow가 필요합니다.") from exc
    local_output = not args.draft
    errors, warnings = validate_project(project_dir, final=local_output)
    if errors:
        raise TikTok2ShortsError("렌더 전 검증 실패:\n- " + "\n- ".join(errors))
    for warning in warnings:
        print(f"warning: {warning}")

    package = load_project_package(
        project_dir,
        ("project.json", "source.json", "script.json", "storyboard.json", "music-plan.json", "rights-manifest.json"),
    )
    project = package["project.json"]
    source = package["source.json"]
    script = package["script.json"]
    storyboard = package["storyboard.json"]
    music_plan = package["music-plan.json"]
    rights = package["rights-manifest.json"]
    scenes, script_override_applied = apply_storyboard_override(
        script,
        require_list(storyboard.get("scenes"), "storyboard.scenes"),
    )
    if not scenes:
        raise TikTok2ShortsError("렌더할 storyboard 장면이 없습니다.")
    music_choice = resolve_music_plan(music_plan, scenes, project_dir=project_dir)
    default_output = "outputs/preview.mp4" if args.draft else "outputs/short.mp4"
    output_name = args.output or default_output
    if Path(output_name).suffix.lower() != ".mp4":
        raise TikTok2ShortsError("렌더 출력은 .mp4 파일이어야 합니다.")
    output = resolve_project_path(project_dir, output_name, must_exist=False)
    if output.exists() and not args.overwrite:
        raise TikTok2ShortsError(f"출력 파일이 이미 있습니다: {output}. 덮어쓰려면 --overwrite를 사용하세요.")
    output.parent.mkdir(parents=True, exist_ok=True)
    source_media = source_media_by_id(source, project_dir, files_required=True)

    scene_reports: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix=".tiktok2shorts-", dir=project_dir) as temp_name:
        work_dir = Path(temp_name)
        rendered_scenes: list[Path] = []
        for index, scene_value in enumerate(scenes, start=1):
            scene = require_object(scene_value, f"scene {index}")
            actions = edit_actions(scene, index)
            caption_blur = source_caption_blur_region(scene, index) if "source_caption_blur" in actions else None
            last_frame_hold = hold_last_frame_seconds(scene, index) if "hold_last_frame" in actions else 0
            last_frame_source_offset = (
                hold_last_frame_source_offset_seconds(scene, index) if "hold_last_frame" in actions else 0
            )
            source_vertical_shift_pixels = number(
                scene.get("source_vertical_shift_pixels", 180 if "source_caption_safe_reframe" in actions else 0),
                f"scene {index}.source_vertical_shift_pixels",
            )
            requested_duration = number(scene.get("duration"), f"scene {index}.duration")
            audio = render_scene_silence(work_dir, index, requested_duration)
            duration = requested_duration
            audio_source = "silent_track"
            if duration > 90:
                raise TikTok2ShortsError(f"scene {index}의 렌더 길이가 90초를 넘습니다.")

            source_seconds = number(scene.get("source_clip_seconds", 0), f"scene {index}.source_clip_seconds")
            source_scene = source_seconds > 0
            visual_value = text(scene.get("visual_path"))
            visual_path: Path | None = None
            visual_start = number(scene.get("visual_start_seconds", 0), f"scene {index}.visual_start_seconds")
            input_seconds = duration
            if source_scene:
                source_id = text(scene.get("source_clip_id"))
                visual_path = resolve_project_path(project_dir, text(source_media[source_id].get("relative_path")))
                visual_start = number(scene.get("source_start_seconds"), f"scene {index}.source_start_seconds")
                input_seconds = source_seconds - last_frame_source_offset
            elif visual_value:
                visual_path = resolve_project_path(project_dir, visual_value)

            credit = scene_credit(scene, source, rights, visual_value, source_scene=source_scene)
            scene_path = work_dir / f"scene-{index:02d}.mp4"
            source_audio_ducked = False
            if visual_path is not None and visual_path.suffix.lower() in MEDIA_SUFFIXES:
                overlay_path = work_dir / f"scene-{index:02d}-overlay.png"
                caption_overlay(
                    scene,
                    project,
                    draft=args.draft,
                    credit=credit,
                ).save(overlay_path, format="PNG", optimize=True)
                source_audio_ducked = render_video_scene(
                    visual_path,
                    overlay_path,
                    audio,
                    scene_path,
                    duration,
                    start=visual_start,
                    input_seconds=input_seconds,
                    actions=actions,
                    source_vertical_shift_pixels=source_vertical_shift_pixels,
                    source_caption_blur=caption_blur,
                    last_frame_hold_seconds=last_frame_hold,
                )
                visual_kind = "source_video" if source_scene else "supporting_video"
            else:
                if visual_path is None:
                    raise TikTok2ShortsError(f"scene {index}에는 실제 원본 구간 또는 visual_path가 필요합니다.")
                frame_path = work_dir / f"scene-{index:02d}.png"
                render_static_frame(
                    scene,
                    project,
                    visual_path,
                    frame_path,
                    draft=args.draft,
                    credit=credit,
                )
                render_static_scene(
                    frame_path,
                    audio,
                    scene_path,
                    duration,
                    slow_zoom="slow_zoom" in actions,
                )
                visual_kind = "supporting_image"
            rendered_scenes.append(scene_path)
            scene_reports.append(
                {
                    "id": text(scene.get("id")) or f"scene-{index:02d}",
                    "role": scene_role(scene),
                    "requested_duration_seconds": round(requested_duration, 3),
                    "rendered_duration_seconds": round(duration, 3),
                    "visual_kind": visual_kind,
                    "visual_path": relative_project_path(project_dir, visual_path) if visual_path else "",
                    "audio_source": audio_source,
                    "edit_actions": actions,
                    "source_audio_ducked": source_audio_ducked,
                    "source_vertical_shift_pixels": source_vertical_shift_pixels,
                    "source_caption_blur_region": caption_blur,
                    "hold_last_frame_seconds": last_frame_hold,
                    "hold_last_frame_source_offset_seconds": last_frame_source_offset,
                    "music_profile_id": "",
                }
            )

        rendered_position = 0.0
        for scene_report in scene_reports:
            rendered_duration = float(scene_report["rendered_duration_seconds"])
            scene_report["rendered_start_seconds"] = round(rendered_position, 3)
            rendered_position += rendered_duration
            scene_report["rendered_end_seconds"] = round(rendered_position, 3)
        rendered_total = rendered_position
        if local_output and (rendered_total < 15 or rendered_total + CTA_TAIL_SECONDS > 60):
            raise TikTok2ShortsError(
                f"본문은 15초 이상이고 CTA {CTA_TAIL_SECONDS:.1f}초를 포함한 최종 길이는 60초 이하여야 합니다: "
                f"{rendered_total + CTA_TAIL_SECONDS:.2f}초"
            )
        concat_file = work_dir / "concat.txt"
        concat_file.write_text(
            "".join(f"file '{path.as_posix()}'\n" for path in rendered_scenes),
            encoding="utf-8",
        )
        concatenated = work_dir / "concatenated-scenes.mp4"
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
                str(concat_file),
                "-c",
                "copy",
                "-movflags",
                "+faststart",
                "-y",
                str(concatenated),
            ],
            "장면 합치기",
        )
        aligned_concatenated = work_dir / "aligned-scenes.mp4"
        align_media_duration(concatenated, aligned_concatenated, rendered_total)
        licensed_music = text(music_choice.get("mode")) == "licensed_track"
        manual_music_profile = text(music_choice.get("selection")) == "manual"
        if licensed_music:
            track = require_object(music_choice.get("track"), "music-plan.track")
            track_path = resolve_project_path(project_dir, text(track.get("relative_path")), must_exist=True)
            for scene_report in scene_reports:
                scene_report["music_profile_id"] = text(music_choice.get("profile_id"))
            mix_licensed_track(
                aligned_concatenated,
                track_path,
                output,
                duration=rendered_total,
                start_seconds=number(track.get("start_seconds", 0), "music-plan.track.start_seconds"),
                volume=number(track.get("volume", 0.16), "music-plan.track.volume"),
            )
        else:
            mood_segments: list[Path] = []
            for index, (scene_value, scene_report) in enumerate(zip(scenes, scene_reports), start=1):
                scene = require_object(scene_value, f"scene {index}")
                emotion = scene_animal_emotion(scene, index)
                profile_id = (
                    text(music_choice.get("profile_id"))
                    if manual_music_profile
                    else text(emotion.get("music_mood"))
                )
                mood_segment = work_dir / f"mood-{index:02d}.wav"
                create_mood_bed(mood_segment, float(scene_report["rendered_duration_seconds"]), profile_id)
                mood_segments.append(mood_segment)
                scene_report["music_profile_id"] = profile_id
            mood_bed = work_dir / "animal-emotion-bed.wav"
            concatenate_mood_beds(mood_segments, mood_bed)
            mix_mood_bed(aligned_concatenated, mood_bed, output)
        cta_output = work_dir / "cta-appended.mp4"
        try:
            cta_report = append_cta_tail(
                output,
                cta_output,
                width=OUTPUT_WIDTH,
                height=OUTPUT_HEIGHT,
                source_duration=rendered_total,
                has_audio=True,
                font_path=find_font(),
                headline="다음 동물 이야기도",
                prompt="구독 · 좋아요",
                ffmpeg=shutil.which("ffmpeg") or "ffmpeg",
            )
        except YouTubeDeliveryError as exc:
            raise TikTok2ShortsError(str(exc)) from exc
        cta_output.replace(output)

    if local_output:
        rendered_durations = [float(item["rendered_duration_seconds"]) for item in scene_reports]
        write_edit_plan(project_dir, project, source, scenes, music_choice, rendered_durations=rendered_durations)
        project["edit_plan"] = {
            "relative_path": "edit-plan.md",
            "generated_at": iso_now(),
            "source_clip_policy_checked": True,
            "timing_basis": "rendered_mp4",
        }
        delivery_note_path = write_delivery_note(
            project_dir,
            project,
            source,
            script,
            scenes,
            output,
            music_choice,
            script_override_applied=script_override_applied,
        )
        project["delivery_note"] = {
            "relative_path": relative_project_path(project_dir, delivery_note_path),
            "generated_at": iso_now(),
            "includes_original_url": bool(text(source.get("original_url"))),
            "scenario_in_video": False,
            "script_override_applied": script_override_applied,
        }
    else:
        delivery_note_path = None

    video = media_probe(output)
    specification_errors: list[str] = []
    if video["video_codec"] != "h264":
        specification_errors.append("영상 코덱이 H.264가 아닙니다.")
    if (video["width"], video["height"]) != (OUTPUT_WIDTH, OUTPUT_HEIGHT):
        specification_errors.append(f"영상 해상도가 {OUTPUT_WIDTH}x{OUTPUT_HEIGHT}가 아닙니다.")
    if video["audio_codec"] != "aac":
        specification_errors.append("오디오 코덱이 AAC가 아닙니다.")
    if not video["has_video"] or not video["has_audio"]:
        specification_errors.append("최종 파일에 영상 또는 오디오 스트림이 없습니다.")
    if video["audio_duration_seconds"] - video["video_duration_seconds"] > (1 / 30) + 0.005:
        specification_errors.append("영상 스트림이 오디오보다 한 프레임 이상 먼저 끝납니다.")
    if specification_errors:
        raise TikTok2ShortsError("렌더 결과 검증 실패:\n- " + "\n- ".join(specification_errors))

    report = {
        "version": 1,
        "rendered_at": iso_now(),
        "draft": bool(args.draft),
        "local_only": True,
        "output": relative_project_path(project_dir, output),
        "audio_mode": (
            "source_audio_ducked_or_silent_plus_licensed_track"
            if licensed_music
            else "source_audio_ducked_or_silent_plus_synthetic_ambient"
        ),
        "music": {
            **music_choice,
            "source": (
                "locally stored licensed track with recorded source and attribution"
                if licensed_music
                else "renderer-generated synthetic ambient; no external track or vocals"
            ),
            "scene_profile_mode": (
                "licensed_single_track"
                if licensed_music
                else ("manual_single_profile" if manual_music_profile else "scene_emotion_cues")
            ),
        },
        "scenario_in_video": False,
        "script_override_applied": script_override_applied,
        "original_source": {
            "url": text(source.get("original_url")),
            "creator": text(source.get("creator")),
        },
        "source_caption_handling": project_source_caption_handling(project),
        "cta_tail": cta_report,
        "delivery_note": relative_project_path(project_dir, delivery_note_path) if delivery_note_path else "",
        "scenes": scene_reports,
        "video": video,
        "warnings": warnings,
    }
    publish_path = project_dir / "publish.json"
    publish = require_object(load_json(publish_path), "publish.json") if publish_path.is_file() else {}
    title_candidates = publish.get("title_candidates") if isinstance(publish.get("title_candidates"), list) else []
    title = text(title_candidates[0]) if title_candidates else text(project.get("title"))
    title = title or f"{text(source.get('creator')) or '동물'}의 반전 순간"
    description = text(publish.get("description")) or (
        f"{title}\n\n실제 동물 행동을 근거로 한국어 상황극 자막을 구성한 로컬 쇼츠입니다.\n"
        f"원본 제작자: {text(source.get('creator')) or '확인 필요'}\n\n#동물 #Shorts"
    )
    hashtags = publish.get("hashtags") if isinstance(publish.get("hashtags"), list) else []
    rights_status = text(require_object(rights.get("source"), "rights-manifest.source").get("permission_status")) or "unknown"
    upload_json, upload_md, _ = write_upload_package(
        project_dir,
        video_path=relative_project_path(project_dir, output),
        title=title,
        description=description,
        tags=[*(text(value) for value in hashtags), "동물", "Shorts"],
        thumbnail_note="CTA 직전 결론 장면에서 동물 행동과 하단 상황극 자막이 함께 보이는 프레임",
        playlist="동물 상황극",
        category="Pets & Animals",
        language="ko",
        pinned_comment=f"{title}에서 가장 공감됐던 장면은 무엇인가요?",
        rights_status=rights_status,
        synthetic_elements=True,
        generated_at=report["rendered_at"],
    )
    report["youtube_upload"] = {
        "json": relative_project_path(project_dir, upload_json),
        "markdown": relative_project_path(project_dir, upload_md),
        "upload_performed": False,
    }
    write_json(project_dir / "render-report.json", report)
    if local_output:
        music_plan["resolved_mode"] = text(music_choice.get("mode"))
        music_plan["resolved_profile_id"] = text(music_choice.get("profile_id"))
        music_plan["resolved_selection"] = text(music_choice.get("selection"))
        music_plan["resolved_reason"] = text(music_choice.get("description"))
        music_plan["resolved_at"] = iso_now()
        write_json(project_dir / "music-plan.json", music_plan)
    project["status"] = "rendered_draft" if args.draft else "rendered_local"
    project["updated_at"] = iso_now()
    project["last_render"] = {
        "relative_path": report["output"],
        "rendered_at": report["rendered_at"],
        "draft": report["draft"],
        "local_only": report["local_only"],
        "report_path": "render-report.json",
    }
    write_json(project_dir / "project.json", project)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


def command_upload_package(args: argparse.Namespace) -> int:
    project_dir = Path(args.project_dir).expanduser().resolve()
    try:
        _, markdown = read_upload_package(project_dir / "youtube-upload.json")
    except YouTubeDeliveryError as exc:
        raise TikTok2ShortsError(str(exc)) from exc
    print(markdown, end="")
    return 0


def command_doctor(_: argparse.Namespace) -> int:
    try:
        import PIL  # type: ignore

        pillow = PIL.__version__
    except ImportError:
        pillow = None
    font = next((str(candidate) for candidate in FONT_CANDIDATES if candidate.is_file()), None)
    print(f"python: {sys.version.split()[0]}")
    print(f"ffmpeg: {'available' if shutil.which('ffmpeg') else 'not found (required for preview and render)'}")
    print(f"ffprobe: {'available' if shutil.which('ffprobe') else 'not found (required for duration and render checks)'}")
    print(f"pillow: {pillow or 'not found (required for Korean caption render)'}")
    print(f"font: {font or 'not found (required for Korean caption render)'}")
    print(f"yt-dlp: {'available' if importlib.util.find_spec('yt_dlp') else 'not found (required for approved-source download)'}")
    print("collector: TikTok Creative Center, public animal candidate metadata, or approved provider export; no direct scraper")
    print("download: local-only source acquisition; no cookies, login, playlist, or overwrite")
    print("rendering: local-only animal-emotion 720x1280 short.mp4 with validated no-vocal music; no upload capability")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="TikTok 동물 바이럴 후보와 감정 해설형 로컬 쇼츠 제작 도구.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor = subparsers.add_parser("doctor", help="로컬 MVP 환경과 범위를 표시합니다.")
    doctor.set_defaults(handler=command_doctor)

    score = subparsers.add_parser("score", help="구조화된 TikTok 동물 후보만 검증·점수화합니다.")
    score.add_argument("--input", required=True, help="candidates 배열이 있는 JSON 파일")
    score.add_argument("--output", required=True, help="점수화 결과 JSON 파일")
    score.add_argument(
        "--target-format",
        choices=("whiteboard",),
        default="",
        help="화이트보드 변환 적합도까지 검증할 때 whiteboard를 지정합니다.",
    )
    score.set_defaults(handler=command_score)

    init = subparsers.add_parser("init", help="선택한 동물 후보의 감정 해설형 쇼츠 프로젝트를 초기화합니다.")
    init.add_argument("--candidates", required=True, help="원본 후보 또는 score 결과 JSON 파일")
    init.add_argument("--candidate-id", required=True, help="사용자가 선택한 후보 ID")
    init.add_argument(
        "--output-root",
        default="outputs/tiktok2shorts",
        help="프로젝트 출력 루트 (기본: outputs/tiktok2shorts)",
    )
    init.set_defaults(handler=command_init)

    download = subparsers.add_parser(
        "download",
        help="선택한 후보의 공개 URL 원본을 로컬 프로젝트로 다운로드합니다.",
    )
    download.add_argument("--project-dir", required=True, help="tiktok2shorts 프로젝트 폴더")
    download.add_argument(
        "--max-filesize",
        default="500M",
        help="yt-dlp 최대 파일 크기 (기본: 500M)",
    )
    download.set_defaults(handler=command_download)

    preview = subparsers.add_parser("preview", help="다운로드한 원본의 편집 위치 검토용 시간 프레임을 만듭니다.")
    preview.add_argument("--project-dir", required=True, help="tiktok2shorts 프로젝트 폴더")
    preview.add_argument("--interval", type=float, default=2.0, help="프레임 간격(초, 기본: 2)")
    preview.add_argument("--max-frames", type=int, default=60, help="최대 프레임 수(기본: 60)")
    preview.set_defaults(handler=command_preview)

    edit_plan = subparsers.add_parser("edit-plan", help="스토리보드의 구간·수정 방식을 사람이 검토할 편집 지시서로 만듭니다.")
    edit_plan.add_argument("--project-dir", required=True, help="tiktok2shorts 프로젝트 폴더")
    edit_plan.set_defaults(handler=command_edit_plan)

    render = subparsers.add_parser("render", help="검토된 동물 감정 스토리보드를 무보컬 배경음과 함께 720x1280 로컬 MP4로 렌더링합니다.")
    render.add_argument("--project-dir", required=True, help="tiktok2shorts 프로젝트 폴더")
    render.add_argument("--draft", action="store_true", help="최종 승인 전 검토용 preview.mp4를 만듭니다.")
    render.add_argument(
        "--output",
        help="프로젝트 내부 MP4 경로 (기본: preview.mp4 또는 short.mp4)",
    )
    render.add_argument("--overwrite", action="store_true", help="기존 출력 MP4를 덮어씁니다.")
    render.set_defaults(handler=command_render)

    upload_package = subparsers.add_parser("upload-package", help="렌더 결과의 YouTube 업로드 정보를 출력합니다.")
    upload_package.add_argument("--project-dir", required=True, help="tiktok2shorts 프로젝트 폴더")
    upload_package.set_defaults(handler=command_upload_package)

    validate = subparsers.add_parser("validate", help="프로젝트의 해설·출처·로컬 렌더 준비 상태를 정적 검사합니다.")
    validate.add_argument("--project-dir", required=True, help="tiktok2shorts 프로젝트 폴더")
    validate.add_argument("--final", action="store_true", help="로컬 MP4 렌더 전 요구 사항까지 검사")
    validate.set_defaults(handler=command_validate)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.handler(args)
    except TikTok2ShortsError as exc:
        fail(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
