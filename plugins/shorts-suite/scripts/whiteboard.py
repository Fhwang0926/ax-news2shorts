#!/usr/bin/env python3
"""Local project wrapper for the vendored SRT whiteboard renderer."""

from __future__ import annotations

import argparse
from bisect import bisect_right
import copy
import datetime as dt
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
from typing import Any
from urllib.parse import urlparse
from urllib.request import Request, urlopen
import wave
from zoneinfo import ZoneInfo

from core.youtube_delivery import (
    YouTubeDeliveryError,
    append_cta_tail,
    read_upload_package,
    write_upload_package,
)


PLUGIN_ROOT = Path(__file__).resolve().parent.parent
SKILL_ROOT = PLUGIN_ROOT / "skills" / "whiteboard-shorts"
TEMPLATE_ROOT = SKILL_ROOT / "templates"
MUSIC_CATALOG_PATH = SKILL_ROOT / "references" / "shorts-music-catalog.json"
VENDOR_ROOT = PLUGIN_ROOT / "vendor" / "srt-whiteboard-animation"
VENDOR_SCRIPTS = VENDOR_ROOT / "scripts"
VENDOR_ASSETS = VENDOR_ROOT / "assets"
UPSTREAM_COMMIT = "696a7243c0e6ffb6827676e539c2ca5ebae2bf6b"
CLEAN_HAND_ASSET_SHA256 = "6c4430a477fd90eed25469c7228f8716913ee3f9b9031326fa3d0f43db50ebb2"
WHITEBOARD_FIT_MIN_SCORE = 70.0
WHITEBOARD_FIT_MIN_PREVIEW_FRAMES = 6
WHITEBOARD_FIT_MIN_DISTINCT_ACTIONS = 3

KNOWN_RIGHTS_STATUSES = {
    "owned",
    "licensed",
    "permission_confirmed",
    "review_required",
    "unknown",
    "not_permitted",
}
FINAL_RIGHTS_STATUSES = {"owned", "licensed", "permission_confirmed"}
FINAL_APPROVALS = (
    "scene_plan_reviewed",
    "images_reviewed",
    "annotations_reviewed",
    "rights_reviewed",
    "draft_reviewed",
)
CAPTION_POSITIONS = {"top", "middle", "bottom"}
CAPTION_STYLES = {"comic-observation", "shorts-punch", "viral-punch"}
CAPTION_BEATS = {"hook", "setup", "rehook", "escalation", "payoff"}
MOTION_TYPES = {"zoom-in", "zoom-out", "punch-in"}
MUSIC_MODES = {"synthetic_ambient", "synthetic_public_domain_remix", "licensed_catalog"}
PUBLIC_DOMAIN_MELODIES = {
    "can-can": {
        "title": "Galop infernal from Orphee aux enfers",
        "composer": "Jacques Offenbach",
        "source_url": "https://imslp.org/wiki/Orph%C3%A9e_aux_enfers_(Offenbach,_Jacques)",
        "arrangement": "tiktok-punch",
        "default_bpm": 160,
    }
}
MUSIC_PROFILES = {
    "gentle": {
        "label": "잔잔한 관찰",
        "frequencies": (261.63, 329.63, 392.0),
    },
    "tender": {
        "label": "따뜻한 공감",
        "frequencies": (220.0, 277.18, 329.63),
    },
    "tension": {
        "label": "조심스러운 긴장",
        "frequencies": (174.61, 220.0, 261.63),
    },
    "relief": {
        "label": "안도",
        "frequencies": (293.66, 369.99, 440.0),
    },
    "playful": {
        "label": "통통 튀는 상황극",
        "frequencies": (329.63, 415.3, 493.88),
    },
}
VENDOR_FILES = (
    "merge_scenes.py",
    "parse_srt.py",
    "prepare_env.py",
    "render_annotation_preview.py",
    "render_stream_whiteboard.py",
    "stream_render.py",
)
FONT_CANDIDATES = (
    Path("/System/Library/Fonts/AppleSDGothicNeo.ttc"),
    Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf"),
    Path("/Library/Fonts/Arial Unicode.ttf"),
    Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
    Path("C:/Windows/Fonts/malgun.ttf"),
)


class WhiteboardShortsError(RuntimeError):
    pass


def now_kst() -> dt.datetime:
    return dt.datetime.now(ZoneInfo("Asia/Seoul"))


def iso_now() -> str:
    return now_kst().isoformat(timespec="seconds")


def text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def require_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise WhiteboardShortsError(f"{label}은 JSON 객체여야 합니다.")
    return value


def require_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise WhiteboardShortsError(f"{label}은 JSON 배열이어야 합니다.")
    return value


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise WhiteboardShortsError(f"파일을 읽을 수 없습니다: {path}") from exc
    except json.JSONDecodeError as exc:
        raise WhiteboardShortsError(f"올바른 JSON이 아닙니다: {path}: {exc}") from exc


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_template(name: str) -> dict[str, Any]:
    return copy.deepcopy(require_object(load_json(TEMPLATE_ROOT / name), name))


def music_catalog() -> dict[str, Any]:
    return require_object(load_json(MUSIC_CATALOG_PATH), "shorts-music-catalog.json")


def catalog_track(track_id: str) -> dict[str, Any]:
    tracks = require_list(music_catalog().get("tracks"), "shorts music catalog tracks")
    track = next(
        (item for item in tracks if isinstance(item, dict) and text(item.get("id")) == track_id),
        None,
    )
    if not isinstance(track, dict):
        raise WhiteboardShortsError(f"검증된 쇼츠 음원 카탈로그에 없는 track_id입니다: {track_id}")
    return track


def sha256_for(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_project_path(project_dir: Path, relative: str, *, must_exist: bool = True) -> Path:
    raw = Path(relative)
    if raw.is_absolute():
        raise WhiteboardShortsError(f"프로젝트 경로는 상대 경로여야 합니다: {relative}")
    root = project_dir.resolve()
    candidate = (root / raw).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise WhiteboardShortsError(f"프로젝트 밖의 경로는 사용할 수 없습니다: {relative}") from exc
    if must_exist and not candidate.exists():
        raise WhiteboardShortsError(f"프로젝트 파일이 없습니다: {relative}")
    return candidate


def run_checked(command: list[str], label: str) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise WhiteboardShortsError(f"{label} 실패: {detail or '원인을 확인할 수 없습니다.'}")
    return result


def runtime_python() -> Path:
    executable = Path("Scripts/python.exe") if sys.platform.startswith("win") else Path("bin/python")
    local = VENDOR_ROOT / ".venv" / executable
    configured = text(os.environ.get("WHITEBOARD_SHORTS_RUNTIME_PYTHON"))
    if configured:
        return Path(configured).expanduser()
    if local.is_file():
        return local
    cache_root = Path.home() / ".codex" / "plugins" / "cache" / "news2shorts-local" / "whiteboard-shorts"
    candidates = sorted(
        cache_root.glob(f"*/vendor/srt-whiteboard-animation/.venv/{executable.as_posix()}"),
        key=lambda path: path.stat().st_mtime if path.exists() else 0,
        reverse=True,
    )
    return next((path for path in candidates if path.is_file()), local)


def require_runtime() -> Path:
    python = runtime_python()
    if not python.is_file():
        raise WhiteboardShortsError("격리 렌더 환경이 없습니다. 사용자가 요청한 경우에만 setup을 실행하세요.")
    result = subprocess.run(
        [str(python), "-c", "import cv2, numpy, av, PIL"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise WhiteboardShortsError("격리 렌더 환경의 의존성이 완전하지 않습니다. setup --check 결과를 확인하세요.")
    return python


def parse_srt(srt: Path, target_sec: float, min_sec: float, max_sec: float) -> dict[str, Any]:
    result = run_checked(
        [
            sys.executable,
            str(VENDOR_SCRIPTS / "parse_srt.py"),
            str(srt),
            "--target-sec",
            str(target_sec),
            "--min-sec",
            str(min_sec),
            "--max-sec",
            str(max_sec),
        ],
        "SRT 분석",
    )
    return require_object(json.loads(result.stdout), "SRT 분석 결과")


def srt_timestamp(milliseconds: int) -> str:
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, millis = divmod(remainder, 1_000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"


def whiteboard_source_fit_preflight(
    source_project: Path,
    source: dict[str, Any],
    storyboard: dict[str, Any],
    analysis: dict[str, Any],
) -> dict[str, Any]:
    errors: list[str] = []
    assessment = source.get("whiteboard_fit_assessment")
    score: float | None = None
    if not isinstance(assessment, dict):
        errors.append("먼저 tiktok2shorts score --target-format whiteboard로 후보를 검증해야 합니다.")
    else:
        raw_score = assessment.get("score")
        if isinstance(raw_score, bool) or not isinstance(raw_score, (int, float)):
            errors.append("whiteboard_fit_assessment.score가 필요합니다.")
        else:
            score = float(raw_score)
            if score < WHITEBOARD_FIT_MIN_SCORE:
                errors.append(f"화이트보드 후보 점수가 {WHITEBOARD_FIT_MIN_SCORE:g}점 미만입니다.")
        if text(assessment.get("target_format")) != "whiteboard":
            errors.append("whiteboard_fit_assessment.target_format은 whiteboard여야 합니다.")
        if assessment.get("eligible") is not True:
            errors.append("화이트보드 적합성 필수 하한을 통과하지 못한 후보입니다.")

    candidate_snapshot = source.get("candidate_snapshot")
    candidate_format_fit = candidate_snapshot.get("format_fit") if isinstance(candidate_snapshot, dict) else None
    if not isinstance(candidate_format_fit, dict) or not isinstance(candidate_format_fit.get("whiteboard"), dict):
        errors.append("candidate_snapshot에 점수의 근거가 된 format_fit.whiteboard 기록이 필요합니다.")

    if text(analysis.get("status")) != "reviewed":
        errors.append("다운로드한 원본 프레임을 검토하고 viral-analysis.json status를 reviewed로 확정해야 합니다.")
    transcript = analysis.get("transcript")
    if not isinstance(transcript, dict) or transcript.get("reviewed") is not True:
        errors.append("viral-analysis.json의 프레임·원본 검토 기록이 필요합니다.")

    preview_frame_count = 0
    preview_record = source.get("analysis_preview")
    if not isinstance(preview_record, dict):
        errors.append("먼저 tiktok2shorts preview로 시간대별 원본 프레임을 생성해야 합니다.")
    else:
        preview_relative = text(preview_record.get("relative_path"))
        try:
            preview = require_object(load_json(resolve_project_path(source_project, preview_relative)), "TikTok preview.json")
            frames = require_list(preview.get("frames"), "TikTok preview.frames")
            preview_frame_count = len(frames)
            if preview_frame_count < WHITEBOARD_FIT_MIN_PREVIEW_FRAMES:
                errors.append(f"화이트보드 사전 검사에는 원본 프레임이 최소 {WHITEBOARD_FIT_MIN_PREVIEW_FRAMES}장 필요합니다.")
            recorded_count = preview_record.get("frame_count")
            if recorded_count != preview_frame_count:
                errors.append("source.json과 preview.json의 프레임 수가 다릅니다.")
            for index, raw_frame in enumerate(frames, start=1):
                if not isinstance(raw_frame, dict):
                    errors.append(f"preview.frames[{index - 1}] 기록이 올바르지 않습니다.")
                    continue
                frame_relative = text(raw_frame.get("relative_path"))
                try:
                    resolve_project_path(source_project, frame_relative)
                except WhiteboardShortsError as exc:
                    errors.append(str(exc))
        except WhiteboardShortsError as exc:
            errors.append(str(exc))

    source_scenes = storyboard.get("scenes")
    distinct_actions: set[str] = set()
    roles: set[str] = set()
    if not isinstance(source_scenes, list):
        errors.append("TikTok storyboard.scenes가 필요합니다.")
        source_scenes = []
    for index, raw_scene in enumerate(source_scenes, start=1):
        if not isinstance(raw_scene, dict):
            errors.append(f"TikTok storyboard scene {index}가 올바르지 않습니다.")
            continue
        role = text(raw_scene.get("role"))
        if role:
            roles.add(role)
        evidence = raw_scene.get("source_evidence")
        action = text(evidence.get("observed_action")) if isinstance(evidence, dict) else ""
        if action:
            distinct_actions.add(action)
    if len(distinct_actions) < WHITEBOARD_FIT_MIN_DISTINCT_ACTIONS:
        errors.append(f"storyboard에는 서로 다른 실제 행동이 최소 {WHITEBOARD_FIT_MIN_DISTINCT_ACTIONS}개 필요합니다.")
    if "hook" not in roles:
        errors.append("storyboard에 실제 원본 근거가 있는 hook 장면이 필요합니다.")
    if "conclusion" not in roles:
        errors.append("storyboard에 실제 결과를 보여 주는 conclusion 장면이 필요합니다.")
    if not roles.intersection({"turn", "payoff"}):
        errors.append("storyboard에 변화나 결말을 담당하는 turn 또는 payoff 장면이 필요합니다.")

    return {
        "ok": not errors,
        "proof": "whiteboard-source-fit",
        "score": score,
        "threshold": WHITEBOARD_FIT_MIN_SCORE,
        "preview_frame_count": preview_frame_count,
        "storyboard_scene_count": len(source_scenes),
        "distinct_storyboard_actions": len(distinct_actions),
        "roles": sorted(roles),
        "errors": list(dict.fromkeys(errors)),
    }


def load_tiktok_project(source_project: Path) -> dict[str, Any]:
    if not source_project.is_dir():
        raise WhiteboardShortsError(f"TikTok2Shorts 프로젝트 폴더가 없습니다: {source_project}")

    project = require_object(load_json(source_project / "project.json"), "TikTok project.json")
    source = require_object(load_json(source_project / "source.json"), "TikTok source.json")
    analysis = require_object(load_json(source_project / "viral-analysis.json"), "TikTok viral-analysis.json")
    script = require_object(load_json(source_project / "script.json"), "TikTok script.json")
    storyboard = require_object(load_json(source_project / "storyboard.json"), "TikTok storyboard.json")
    rights = require_object(load_json(source_project / "rights-manifest.json"), "TikTok rights-manifest.json")

    if text(source.get("platform")) != "tiktok":
        raise WhiteboardShortsError("source-project는 tiktok2shorts가 만든 TikTok 프로젝트여야 합니다.")
    original_url = text(source.get("original_url"))
    parsed_url = urlparse(original_url)
    hostname = (parsed_url.hostname or "").lower()
    if parsed_url.scheme != "https" or not (hostname == "tiktok.com" or hostname.endswith(".tiktok.com")):
        raise WhiteboardShortsError("TikTok 원본 URL은 canonical HTTPS TikTok URL이어야 합니다.")
    creator = text(source.get("creator"))
    if not creator:
        raise WhiteboardShortsError("TikTok 원본 제작자 기록이 필요합니다.")

    source_rights = require_object(source.get("rights"), "TikTok source.rights")
    rights_source = require_object(rights.get("source"), "TikTok rights-manifest.source")
    permission_status = text(source_rights.get("permission_status"))
    manifest_status = text(rights_source.get("permission_status"))
    if permission_status not in KNOWN_RIGHTS_STATUSES or manifest_status != permission_status:
        raise WhiteboardShortsError("TikTok source와 rights-manifest의 permission_status가 일치해야 합니다.")
    if permission_status == "not_permitted":
        raise WhiteboardShortsError("not_permitted TikTok 원본은 화이트보드 프로젝트로 가져올 수 없습니다.")
    permission_reference = text(source_rights.get("permission_reference"))

    media_records = require_list(source.get("source_media"), "TikTok source_media")
    media = next(
        (item for item in media_records if isinstance(item, dict) and text(item.get("id")) == "source-video-01"),
        None,
    )
    if media is None:
        raise WhiteboardShortsError("먼저 tiktok2shorts download로 원본을 로컬에 받아야 합니다.")
    media_relative = text(media.get("relative_path"))
    media_path = resolve_project_path(source_project, media_relative)
    media_hash = sha256_for(media_path)
    recorded_hash = text(media.get("sha256"))
    if recorded_hash and recorded_hash != media_hash:
        raise WhiteboardShortsError("TikTok 원본 영상 해시가 source.json 기록과 다릅니다.")

    segments = require_list(script.get("segments"), "TikTok script.segments")
    segment_by_id = {
        text(item.get("id")): item
        for item in segments
        if isinstance(item, dict) and text(item.get("id"))
    }
    source_scenes = require_list(storyboard.get("scenes"), "TikTok storyboard.scenes")
    if not source_scenes:
        raise WhiteboardShortsError("TikTok storyboard에 가져올 장면이 없습니다.")
    fit_preflight = whiteboard_source_fit_preflight(source_project, source, storyboard, analysis)
    if not fit_preflight["ok"]:
        raise WhiteboardShortsError(
            "화이트보드 원본 적합성 사전 검사 실패:\n- " + "\n- ".join(fit_preflight["errors"])
        )

    cues: list[dict[str, Any]] = []
    imported_scenes: list[dict[str, Any]] = []
    srt_blocks: list[str] = []
    cursor_ms = 0
    for index, raw_scene in enumerate(source_scenes, start=1):
        source_scene = require_object(raw_scene, f"TikTok storyboard scene {index}")
        source_scene_id = text(source_scene.get("id"))
        segment_id = text(source_scene.get("script_segment_id"))
        segment = segment_by_id.get(segment_id, {})
        narration = text(source_scene.get("korean_narration")) or text(segment.get("korean_narration"))
        if not source_scene_id or not narration:
            raise WhiteboardShortsError(f"TikTok storyboard scene {index}의 id와 한국어 narration이 필요합니다.")
        duration = source_scene.get("duration")
        if isinstance(duration, bool) or not isinstance(duration, (int, float)) or duration <= 0:
            raise WhiteboardShortsError(f"TikTok storyboard scene {index}의 duration이 올바르지 않습니다.")
        evidence = require_object(source_scene.get("source_evidence"), f"TikTok scene {source_scene_id}.source_evidence")
        observed_action = text(evidence.get("observed_action"))
        if not observed_action:
            raise WhiteboardShortsError(f"TikTok scene {source_scene_id}의 observed_action이 필요합니다.")
        animal_emotion = source_scene.get("animal_emotion")
        music_mood = text(animal_emotion.get("music_mood")) if isinstance(animal_emotion, dict) else ""
        if music_mood not in MUSIC_PROFILES:
            music_mood = "playful"

        duration_ms = max(1, round(float(duration) * 1_000))
        end_ms = cursor_ms + duration_ms
        cues.append(
            {
                "index": index,
                "startMs": cursor_ms,
                "endMs": end_ms,
                "durationMs": duration_ms,
                "text": narration,
            }
        )
        srt_blocks.append(
            f"{index}\n{srt_timestamp(cursor_ms)} --> {srt_timestamp(end_ms)}\n{narration}"
        )
        imported_scenes.append(
            {
                "startMs": cursor_ms,
                "endMs": end_ms,
                "sceneDurationMs": duration_ms,
                "cueRange": [index, index],
                "text": narration,
                "visual_description": observed_action,
                "tiktok_source": {
                    "scene_id": source_scene_id,
                    "role": text(source_scene.get("role")),
                    "source_start_seconds": source_scene.get("source_start_seconds"),
                    "source_clip_seconds": source_scene.get("source_clip_seconds"),
                    "headline": text(source_scene.get("headline")),
                    "caption": text(source_scene.get("korean_caption")),
                    "music_mood": music_mood,
                    "source_evidence": evidence,
                },
            }
        )
        cursor_ms = end_ms

    return {
        "title": text(project.get("title")) or source_project.name,
        "source_project": source_project,
        "source": source,
        "storyboard_path": source_project / "storyboard.json",
        "source_path": source_project / "source.json",
        "media_path": media_path,
        "media_relative": media_relative,
        "media_hash": media_hash,
        "original_url": original_url,
        "creator": creator,
        "permission_status": permission_status,
        "permission_reference": permission_reference,
        "candidate_id": text(source.get("candidate_id")),
        "fit_preflight": fit_preflight,
        "parsed": {"cues": cues, "scenes": imported_scenes},
        "srt_text": "\n\n".join(srt_blocks) + "\n",
    }


def project_package(project_dir: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    project = require_object(load_json(project_dir / "project.json"), "project.json")
    scene_plan = require_object(load_json(project_dir / "scene-plan.json"), "scene-plan.json")
    rights = require_object(load_json(project_dir / "rights-manifest.json"), "rights-manifest.json")
    return project, scene_plan, rights


def postproduction_plan(project_dir: Path) -> dict[str, Any]:
    path = project_dir / "post-production.json"
    if not path.is_file():
        return {}
    return require_object(load_json(path), "post-production.json")


def caption_for_scene(postproduction: dict[str, Any], scene_id: str) -> tuple[str, str, str]:
    captions = postproduction.get("captions")
    if not isinstance(captions, dict) or captions.get("enabled") is not True:
        return "", "bottom", "comic-observation"
    items = captions.get("items")
    if not isinstance(items, list):
        return "", "bottom", "comic-observation"
    item = next(
        (
            value
            for value in items
            if isinstance(value, dict) and text(value.get("scene_id")) == scene_id
        ),
        None,
    )
    if not isinstance(item, dict):
        return "", "bottom", "comic-observation"
    return (
        text(item.get("text")),
        text(item.get("position")) or "bottom",
        text(captions.get("style")) or "comic-observation",
    )


def music_plan(postproduction: dict[str, Any]) -> dict[str, Any] | None:
    music = postproduction.get("music")
    return music if isinstance(music, dict) and music.get("enabled") is True else None


def motion_for_scene(postproduction: dict[str, Any], scene_id: str) -> dict[str, Any] | None:
    motion = postproduction.get("motion")
    if not isinstance(motion, dict) or motion.get("enabled") is not True:
        return None
    items = motion.get("items")
    if not isinstance(items, list):
        return None
    item = next(
        (
            value
            for value in items
            if isinstance(value, dict) and text(value.get("scene_id")) == scene_id
        ),
        None,
    )
    return item if isinstance(item, dict) else None


def scene_records(project_dir: Path, scene_plan: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, relative in enumerate(require_list(scene_plan.get("scene_files"), "scene_plan.scene_files"), start=1):
        if not isinstance(relative, str) or not relative:
            raise WhiteboardShortsError(f"scene_files[{index - 1}] 경로가 올바르지 않습니다.")
        records.append(require_object(load_json(resolve_project_path(project_dir, relative)), relative))
    return records


def scene_by_id(project_dir: Path, scene_id: str) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    project, plan, rights = project_package(project_dir)
    scene = next((item for item in scene_records(project_dir, plan) if text(item.get("id")) == scene_id), None)
    if scene is None:
        raise WhiteboardShortsError(f"장면을 찾을 수 없습니다: {scene_id}")
    return project, plan, rights, scene


def ensure_new_project_dir(project_dir: Path) -> None:
    if project_dir.exists() and any(project_dir.iterdir()):
        raise WhiteboardShortsError(f"비어 있지 않은 프로젝트 폴더는 사용할 수 없습니다: {project_dir}")
    project_dir.mkdir(parents=True, exist_ok=True)


def command_doctor(args: argparse.Namespace) -> int:
    python = runtime_python()
    hand_asset = VENDOR_ASSETS / "drawing-hand.png"
    hand_asset_sha256 = sha256_for(hand_asset) if hand_asset.is_file() else ""
    dependency_probe = False
    if python.is_file():
        dependency_probe = subprocess.run(
            [str(python), "-c", "import cv2, numpy, av, PIL"],
            capture_output=True,
        ).returncode == 0
    vendor_status = {name: (VENDOR_SCRIPTS / name).is_file() for name in VENDOR_FILES}
    checks = {
        "python": sys.version.split()[0],
        "current_pillow": bool(importlib.util.find_spec("PIL")),
        "upstream_commit": UPSTREAM_COMMIT,
        "vendor_scripts": vendor_status,
        "hand_asset": hand_asset.is_file(),
        "hand_asset_sha256": hand_asset_sha256,
        "clean_hand_asset": hand_asset_sha256 == CLEAN_HAND_ASSET_SHA256,
        "preview_asset": (VENDOR_ASSETS / "preview.html").is_file(),
        "runtime_python": str(python) if python.is_file() else "",
        "runtime_dependencies": dependency_probe,
        "ffmpeg": shutil.which("ffmpeg") or "",
        "ffprobe": shutil.which("ffprobe") or "",
        "external_upload": False,
    }
    checks["ready_for_render"] = bool(
        all(vendor_status.values())
        and checks["hand_asset"]
        and checks["clean_hand_asset"]
        and checks["preview_asset"]
        and dependency_probe
    )
    if args.json:
        print(json.dumps(checks, ensure_ascii=False, indent=2))
    else:
        for key, value in checks.items():
            print(f"{key}: {value}")
    return 0


def command_setup(args: argparse.Namespace) -> int:
    command = [sys.executable, str(VENDOR_SCRIPTS / "prepare_env.py")]
    if args.check:
        command.append("--check")
    result = subprocess.run(command)
    return result.returncode


def command_preflight(args: argparse.Namespace) -> int:
    source_project = Path(args.source_project).resolve()
    try:
        imported = load_tiktok_project(source_project)
    except WhiteboardShortsError as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "proof": "whiteboard-source-fit",
                    "source_project": str(source_project),
                    "errors": [str(exc)],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1
    payload = dict(require_object(imported["fit_preflight"], "화이트보드 적합성 사전 검사"))
    payload["source_project"] = str(source_project)
    payload["candidate_id"] = text(imported.get("candidate_id"))
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def command_init(args: argparse.Namespace) -> int:
    project_dir = Path(args.project_dir).resolve()
    tiktok_import: dict[str, Any] | None = None
    if args.source_project:
        if args.rights_status or args.rights_reference:
            raise WhiteboardShortsError("source-project는 TikTok 프로젝트의 권리 기록을 그대로 상속하므로 rights 옵션을 받지 않습니다.")
        tiktok_import = load_tiktok_project(Path(args.source_project).resolve())
        parsed = require_object(tiktok_import["parsed"], "TikTok 변환 결과")
        rights_status = text(tiktok_import["permission_status"])
        rights_reference = text(tiktok_import["permission_reference"])
    else:
        source_srt = Path(args.srt).resolve()
        if not source_srt.is_file():
            raise WhiteboardShortsError(f"SRT 파일이 없습니다: {source_srt}")
        if not args.rights_status:
            raise WhiteboardShortsError("로컬 SRT 입력에는 --rights-status가 필요합니다.")
        if not 0 < args.min_sec <= args.target_sec <= args.max_sec:
            raise WhiteboardShortsError("장면 시간은 0 < min-sec <= target-sec <= max-sec 순서여야 합니다.")
        parsed = parse_srt(source_srt, args.target_sec, args.min_sec, args.max_sec)
        rights_status = args.rights_status
        rights_reference = args.rights_reference or ""
    parsed_scenes = require_list(parsed.get("scenes"), "SRT scenes")
    if not parsed_scenes:
        raise WhiteboardShortsError("SRT에서 장면을 만들지 못했습니다.")
    ensure_new_project_dir(project_dir)

    for folder in ("input", "scenes", "previews", "renders", "outputs", "assets/audio"):
        (project_dir / folder).mkdir(parents=True, exist_ok=True)
    destination_srt = project_dir / "input" / "story.srt"
    if tiktok_import:
        destination_srt.write_text(text(tiktok_import["srt_text"]) + "\n", encoding="utf-8")
        media_source = Path(tiktok_import["media_path"])
        media_destination = project_dir / "input" / f"tiktok-source{media_source.suffix.lower()}"
        shutil.copy2(media_source, media_destination)
        shutil.copy2(Path(tiktok_import["source_path"]), project_dir / "input" / "tiktok-source.json")
        shutil.copy2(Path(tiktok_import["storyboard_path"]), project_dir / "input" / "tiktok-storyboard.json")
    else:
        shutil.copy2(source_srt, destination_srt)
    source_hash = sha256_for(destination_srt)

    created_at = iso_now()
    project = load_template("project.template.json")
    project.update(
        {
            "title": args.title or project_dir.name,
            "slug": project_dir.name,
            "created_at": created_at,
            "updated_at": created_at,
            "source_kind": "tiktok_project" if tiktok_import else "local_srt",
            "source_srt": {"path": "input/story.srt", "sha256": source_hash},
        }
    )
    if tiktok_import:
        project["title"] = args.title or text(tiktok_import["title"])
        project["render_profile"]["audio"] = "background_music"
        project["render_profile"]["audio_codec"] = "aac"
        project["source_origin"] = {
            "platform": "tiktok",
            "original_url": text(tiktok_import["original_url"]),
            "creator": text(tiktok_import["creator"]),
            "candidate_id": text(tiktok_import["candidate_id"]),
            "imported_from_project": str(tiktok_import["source_project"]),
            "imported_at": created_at,
            "source_media": {
                "path": str(media_destination.relative_to(project_dir)),
                "sha256": text(tiktok_import["media_hash"]),
                "original_project_path": text(tiktok_import["media_relative"]),
            },
            "source_snapshot": "input/tiktok-source.json",
            "storyboard_snapshot": "input/tiktok-storyboard.json",
            "whiteboard_fit": require_object(tiktok_import["fit_preflight"], "화이트보드 적합성 사전 검사"),
        }

    scene_files: list[str] = []
    for index, raw_scene in enumerate(parsed_scenes, start=1):
        item = require_object(raw_scene, f"parsed scene {index}")
        scene_id = f"scene-{index:02d}"
        relative = f"scenes/{scene_id}.json"
        scene = {
            "version": 1,
            "id": scene_id,
            "sequence": index,
            "source_start_ms": int(item.get("startMs", 0)),
            "source_end_ms": int(item.get("endMs", 0)),
            "scene_duration_ms": int(item.get("sceneDurationMs", 0)),
            "cue_range": item.get("cueRange", []),
            "narration": text(item.get("text")),
            "visual_description": text(item.get("visual_description")),
            "image": f"scenes/{scene_id}.png",
            "annotation": f"scenes/{scene_id}.annotation.json",
        }
        if tiktok_import:
            scene["tiktok_source"] = require_object(item.get("tiktok_source"), f"{scene_id}.tiktok_source")
        write_json(project_dir / relative, scene)
        scene_files.append(relative)

    scene_plan = {
        "version": 1,
        "status": "draft",
        "source_kind": "tiktok_project" if tiktok_import else "local_srt",
        "source_srt": "input/story.srt",
        "target_seconds": args.target_sec,
        "min_seconds": args.min_sec,
        "max_seconds": args.max_sec,
        "cues": require_list(parsed.get("cues"), "SRT cues"),
        "scene_files": scene_files,
    }
    rights = load_template("rights-manifest.template.json")
    rights["source"] = {
        "path": "input/story.srt",
        "sha256": source_hash,
        "permission_status": rights_status,
        "permission_reference": rights_reference,
    }
    if tiktok_import:
        music_segments = [
            {
                "scene_id": f"scene-{index:02d}",
                "profile_id": text(
                    require_object(item.get("tiktok_source"), f"scene-{index:02d}.tiktok_source").get("music_mood")
                )
                or "playful",
                "impact": text(
                    require_object(item.get("tiktok_source"), f"scene-{index:02d}.tiktok_source").get("role")
                )
                in {"turn", "payoff", "conclusion"},
            }
            for index, item in enumerate(parsed_scenes, start=1)
        ]
        high_energy_count = sum(
            value["profile_id"] in {"tension", "relief", "playful"} for value in music_segments
        )
        use_popular_licensed_track = high_energy_count >= math.ceil(len(music_segments) * 0.6)
        popular_track = catalog_track("monkeys-spinning-monkeys") if use_popular_licensed_track else None
        rights["source"].update(
            {
                "platform": "tiktok",
                "original_url": text(tiktok_import["original_url"]),
                "creator": text(tiktok_import["creator"]),
                "source_project": str(tiktok_import["source_project"]),
            }
        )
        rights["assets"] = [
            {
                "id": "tiktok-source-video",
                "kind": "source_video",
                "path": str(media_destination.relative_to(project_dir)),
                "sha256": text(tiktok_import["media_hash"]),
                "original_url": text(tiktok_import["original_url"]),
                "creator": text(tiktok_import["creator"]),
                "permission_status": rights_status,
                "permission_reference": rights_reference,
                "synthetic": False,
                "usage_scope": "local_reference_for_whiteboard",
            },
            {
                "id": "background-music",
                "kind": "background_music",
                "path": (
                    "assets/audio/monkeys-spinning-monkeys.mp3"
                    if use_popular_licensed_track
                    else "assets/audio/background-music.wav"
                ),
                "creator": text(popular_track.get("artist")) if popular_track else "Whiteboard Shorts synthetic tone generator",
                "permission_status": "licensed" if popular_track else "owned",
                "permission_reference": text(popular_track.get("license_url")) if popular_track else "project-generated",
                "synthetic": False if popular_track else True,
                "vocals": False,
                "usage_scope": "local_whiteboard_review",
            },
        ]
        if popular_track:
            rights["assets"][1].update(
                {
                    "track_id": text(popular_track.get("id")),
                    "title": text(popular_track.get("title")),
                    "isrc": text(popular_track.get("isrc")),
                    "source_page": text(popular_track.get("source_page")),
                    "download_url": text(popular_track.get("download_url")),
                    "license_name": text(popular_track.get("license_name")),
                    "license_url": text(popular_track.get("license_url")),
                    "attribution": text(popular_track.get("attribution")),
                    "expected_sha256": text(popular_track.get("known_file_sha256")),
                }
            )

    postproduction = load_template("post-production.template.json")
    if tiktok_import:
        role_positions = {
            "hook": "top",
            "turn": "bottom",
            "evidence": "middle",
            "payoff": "top",
            "conclusion": "middle",
        }
        postproduction["captions"] = {
            "enabled": True,
            "style": "viral-punch",
            "items": [
                {
                    "scene_id": f"scene-{index:02d}",
                    "text": text(require_object(item.get("tiktok_source"), f"scene-{index:02d}.tiktok_source").get("caption"))
                    or text(item.get("text")),
                    "position": role_positions.get(
                        text(require_object(item.get("tiktok_source"), f"scene-{index:02d}.tiktok_source").get("role")),
                        "bottom",
                    ),
                    "beat": (
                        ("hook", "setup", "rehook", "escalation", "payoff")[index - 1]
                        if len(parsed_scenes) == 5
                        else {
                            "hook": "hook",
                            "turn": "rehook",
                            "evidence": "setup",
                            "payoff": "escalation",
                            "conclusion": "payoff",
                        }.get(
                            text(require_object(item.get("tiktok_source"), f"scene-{index:02d}.tiktok_source").get("role")),
                            "setup",
                        )
                    ),
                }
                for index, item in enumerate(parsed_scenes, start=1)
            ],
        }
        postproduction["music"] = {
            "enabled": True,
            "mode": "licensed_catalog" if popular_track else "synthetic_ambient",
            "vocals": False,
            "volume": 0.85 if popular_track else 0.24,
            "fade_in_seconds": 0.04 if popular_track else 0.25,
            "fade_out_seconds": 0.3 if popular_track else 0.45,
            "asset_path": "assets/audio/monkeys-spinning-monkeys.mp3" if popular_track else "assets/audio/background-music.wav",
            "segments": music_segments,
            "rights": {
                "permission_status": "licensed" if popular_track else "owned",
                "note": (
                    "제작자 공식 파일을 CC BY 4.0 조건과 필수 크레딧으로 사용합니다."
                    if popular_track
                    else "렌더러가 새로 만든 무보컬 톤 베드이며 외부 음원을 사용하지 않습니다."
                ),
            },
        }
        if popular_track:
            postproduction["music"].update(
                {
                    "track_id": text(popular_track.get("id")),
                    "title": text(popular_track.get("title")),
                    "artist": text(popular_track.get("artist")),
                    "bpm": popular_track.get("bpm"),
                    "start_seconds": 0.0,
                    "loudness_target_lufs": -14.0,
                    "true_peak_db": -1.5,
                    "license_name": text(popular_track.get("license_name")),
                    "license_url": text(popular_track.get("license_url")),
                    "source_page": text(popular_track.get("source_page")),
                    "attribution": text(popular_track.get("attribution")),
                    "usage_evidence": popular_track.get("usage_evidence"),
                }
            )
        postproduction["motion"] = {
            "enabled": True,
            "items": [
                {
                    "scene_id": f"scene-{index:02d}",
                    "type": "punch-in" if text(require_object(item.get("tiktok_source"), f"scene-{index:02d}.tiktok_source").get("role")) in {"turn", "payoff", "conclusion"} else "zoom-in",
                    "start_scale": 1.0,
                    "end_scale": 1.11 if text(require_object(item.get("tiktok_source"), f"scene-{index:02d}.tiktok_source").get("role")) in {"turn", "payoff", "conclusion"} else 1.05,
                    "focus_x": 0.5,
                    "focus_y": 0.45,
                }
                for index, item in enumerate(parsed_scenes, start=1)
                if text(require_object(item.get("tiktok_source"), f"scene-{index:02d}.tiktok_source").get("role"))
                in {"hook", "turn", "payoff", "conclusion"}
            ],
        }

    write_json(project_dir / "project.json", project)
    write_json(project_dir / "scene-plan.json", scene_plan)
    write_json(project_dir / "rights-manifest.json", rights)
    write_json(project_dir / "post-production.json", postproduction)
    print(json.dumps({"project_dir": str(project_dir), "scene_count": len(scene_files), "status": "planned"}, ensure_ascii=False, indent=2))
    return 0


def is_integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def image_size(path: Path) -> tuple[int, int]:
    try:
        from PIL import Image

        with Image.open(path) as image:
            return image.size
    except ImportError:
        python = require_runtime()
        code = "from PIL import Image; import json,sys; im=Image.open(sys.argv[1]); print(json.dumps(im.size))"
        result = run_checked([str(python), "-c", code, str(path)], "이미지 크기 확인")
        width, height = json.loads(result.stdout)
        return int(width), int(height)


def validate_rect(value: Any, label: str, width: int, height: int, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append(f"{label}은 객체여야 합니다.")
        return
    fields = ("x", "y", "width", "height")
    if any(not is_integer(value.get(field)) for field in fields):
        errors.append(f"{label} 좌표와 크기는 정수여야 합니다.")
        return
    x, y, rect_w, rect_h = (value[field] for field in fields)
    if x < 0 or y < 0 or rect_w <= 0 or rect_h <= 0:
        errors.append(f"{label} 좌표와 크기가 올바르지 않습니다.")
    elif x + rect_w > width or y + rect_h > height:
        errors.append(f"{label}이 캔버스 밖으로 나갑니다.")


def validate_point(value: Any, label: str, width: int, height: int, errors: list[str]) -> None:
    if not isinstance(value, list) or len(value) != 2 or any(not is_integer(item) for item in value):
        errors.append(f"{label}은 정수 좌표 [x, y]여야 합니다.")
        return
    if not (0 <= value[0] < width and 0 <= value[1] < height):
        errors.append(f"{label}이 캔버스 밖에 있습니다.")


def validate_annotation(
    scene: dict[str, Any], image: Path, annotation_path: Path
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    scene_id = text(scene.get("id"))
    annotation = require_object(load_json(annotation_path), str(annotation_path))
    width, height = image_size(image)
    if text(annotation.get("sceneId")) != scene_id:
        errors.append(f"{scene_id}: annotation.sceneId가 장면 ID와 다릅니다.")
    canvas = annotation.get("canvas")
    if not isinstance(canvas, dict) or (canvas.get("width"), canvas.get("height")) != (width, height):
        errors.append(f"{scene_id}: canvas는 실제 이미지 크기 {width}x{height}여야 합니다.")
    if (width, height) != (1080, 1920):
        errors.append(f"{scene_id}: 장면 이미지는 1080x1920이어야 합니다. 현재 {width}x{height}")
    duration = annotation.get("sceneDurationMs")
    expected_duration = scene.get("scene_duration_ms")
    if not is_integer(duration) or duration <= 0:
        errors.append(f"{scene_id}: sceneDurationMs는 양의 정수여야 합니다.")
    elif duration != expected_duration:
        errors.append(f"{scene_id}: sceneDurationMs는 장면 계획의 {expected_duration}ms와 같아야 합니다.")
    if not text(annotation.get("storyBasis")):
        errors.append(f"{scene_id}: storyBasis가 필요합니다.")
    elements = annotation.get("elements")
    if not isinstance(elements, list) or not elements:
        errors.append(f"{scene_id}: elements가 비어 있습니다.")
        return errors, warnings

    sequences: list[int] = []
    ids: set[str] = set()
    previous_end = 0
    final_end = 0
    for index, value in enumerate(elements, start=1):
        label = f"{scene_id}.elements[{index - 1}]"
        if not isinstance(value, dict):
            errors.append(f"{label}은 객체여야 합니다.")
            continue
        element_id = text(value.get("id"))
        if not element_id or element_id in ids:
            errors.append(f"{label}.id가 비어 있거나 중복되었습니다.")
        ids.add(element_id)
        sequence = value.get("sequence")
        if not is_integer(sequence):
            errors.append(f"{label}.sequence는 정수여야 합니다.")
        else:
            sequences.append(sequence)
        for field in ("label", "narrativeRole", "subtitle", "type"):
            if not text(value.get(field)):
                errors.append(f"{label}.{field}가 필요합니다.")
        validate_rect(value.get("region"), f"{label}.region", width, height, errors)
        reveal = value.get("reveal")
        if not isinstance(reveal, dict):
            errors.append(f"{label}.reveal이 필요합니다.")
            continue
        if not text(reveal.get("direction")):
            errors.append(f"{label}.reveal.direction이 필요합니다.")
        mask_padding = reveal.get("maskPaddingPx")
        if not is_integer(mask_padding) or mask_padding < 0:
            errors.append(f"{label}.reveal.maskPaddingPx는 0 이상의 정수여야 합니다.")
        start = reveal.get("startMs")
        interval = reveal.get("durationMs")
        if not is_integer(start) or start < 0 or not is_integer(interval) or interval <= 0:
            errors.append(f"{label}.reveal 시간은 0 이상의 startMs와 양의 durationMs여야 합니다.")
        else:
            if start < previous_end:
                errors.append(f"{label}.reveal 시간이 이전 요소와 겹칩니다.")
            previous_end = start + interval
            final_end = max(final_end, previous_end)
        protected = reveal.get("protectedRegions", [])
        if not isinstance(protected, list):
            errors.append(f"{label}.protectedRegions는 배열이어야 합니다.")
        else:
            for protected_index, region in enumerate(protected):
                validate_rect(region, f"{label}.protectedRegions[{protected_index}]", width, height, errors)
        hand_path = value.get("handPath")
        if not isinstance(hand_path, dict):
            errors.append(f"{label}.handPath가 필요합니다.")
        else:
            validate_point(hand_path.get("start"), f"{label}.handPath.start", width, height, errors)
            validate_point(hand_path.get("end"), f"{label}.handPath.end", width, height, errors)
            if not text(hand_path.get("easing")):
                errors.append(f"{label}.handPath.easing이 필요합니다.")

    if sequences != list(range(1, len(elements) + 1)):
        errors.append(f"{scene_id}: sequence는 1부터 연속이고 elements 순서와 같아야 합니다.")
    if is_integer(duration) and final_end + 500 > duration:
        errors.append(f"{scene_id}: 마지막 요소 뒤에 최소 500ms의 완성 화면 시간이 필요합니다.")
    return errors, warnings


def rights_asset(rights: dict[str, Any], relative_path: str) -> dict[str, Any] | None:
    assets = rights.get("assets", [])
    if not isinstance(assets, list):
        return None
    return next(
        (
            item
            for item in assets
            if isinstance(item, dict) and text(item.get("path")) == relative_path
        ),
        None,
    )


def validate_postproduction(
    project_dir: Path,
    project: dict[str, Any],
    rights: dict[str, Any],
    scenes: list[dict[str, Any]],
    postproduction: dict[str, Any],
    errors: list[str],
    warnings: list[str],
    *,
    render_ready: bool,
) -> None:
    captions = postproduction.get("captions")
    if isinstance(captions, dict) and captions.get("enabled") is True:
        caption_style = text(captions.get("style"))
        if caption_style not in CAPTION_STYLES:
            errors.append("post-production.captions.style이 지원 자막 스타일이 아닙니다.")
        items = captions.get("items")
        if not isinstance(items, list):
            errors.append("post-production.captions.items는 배열이어야 합니다.")
        else:
            seen: set[str] = set()
            beats: list[str] = []
            for index, value in enumerate(items):
                label = f"post-production.captions.items[{index}]"
                if not isinstance(value, dict):
                    errors.append(f"{label}은 객체여야 합니다.")
                    continue
                scene_id = text(value.get("scene_id"))
                caption = text(value.get("text"))
                position = text(value.get("position"))
                if not scene_id or scene_id in seen:
                    errors.append(f"{label}.scene_id가 비어 있거나 중복되었습니다.")
                seen.add(scene_id)
                if not caption or len(caption) > 60 or len(caption.splitlines()) > 2:
                    errors.append(f"{label}.text는 1~60자, 최대 두 줄이어야 합니다.")
                if caption_style == "viral-punch":
                    beat = text(value.get("beat"))
                    beats.append(beat)
                    if len(caption) > 36:
                        errors.append(f"{label}.text는 viral-punch에서 36자 이하여야 합니다.")
                    if beat not in CAPTION_BEATS:
                        errors.append(f"{label}.beat가 지원 쇼츠 문구 역할이 아닙니다.")
                if position not in CAPTION_POSITIONS:
                    errors.append(f"{label}.position은 top, middle, bottom 중 하나여야 합니다.")
            expected = {text(scene.get("id")) for scene in scenes}
            if seen != expected:
                errors.append("자막 사용 시 모든 장면에 정확히 하나의 caption 항목이 필요합니다.")
            if caption_style == "viral-punch" and beats:
                if beats[0] != "hook" or beats[-1] != "payoff" or "rehook" not in beats:
                    errors.append("viral-punch는 첫 장면 hook, 중간 rehook, 마지막 payoff가 필요합니다.")

    music = music_plan(postproduction)
    profile = project.get("render_profile")
    if music is None:
        if isinstance(profile, dict) and profile.get("audio") != "none":
            errors.append("배경음이 없으면 render_profile.audio는 none이어야 합니다.")
        return
    music_mode = text(music.get("mode"))
    if music_mode not in MUSIC_MODES:
        errors.append("지원하지 않는 Whiteboard Shorts 배경음 mode입니다.")
    if music.get("vocals") is not False:
        errors.append("배경음은 무보컬이어야 합니다.")
    volume = music.get("volume")
    fade_in = music.get("fade_in_seconds")
    fade_out = music.get("fade_out_seconds")
    if isinstance(volume, bool) or not isinstance(volume, (int, float)) or not 0 < float(volume) <= 1:
        errors.append("post-production.music.volume은 0보다 크고 1 이하여야 합니다.")
    for label, value in (("fade_in_seconds", fade_in), ("fade_out_seconds", fade_out)):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or float(value) < 0:
            errors.append(f"post-production.music.{label}는 0 이상이어야 합니다.")
    asset_path = text(music.get("asset_path"))
    try:
        resolved_asset = resolve_project_path(project_dir, asset_path, must_exist=False)
    except WhiteboardShortsError as exc:
        errors.append(str(exc))
        resolved_asset = None
    asset = rights_asset(rights, asset_path)
    if asset is None:
        errors.append("배경음의 rights-manifest 자산 기록이 필요합니다.")
    else:
        if asset.get("vocals") is not False:
            errors.append("배경음 권리 기록은 vocals false여야 합니다.")
        if music_mode == "licensed_catalog":
            if text(asset.get("permission_status")) != "licensed" or asset.get("synthetic") is not False:
                errors.append("카탈로그 배경음은 licensed와 synthetic false를 기록해야 합니다.")
        else:
            if text(asset.get("permission_status")) != "owned" or asset.get("synthetic") is not True:
                errors.append("생성 배경음은 owned와 synthetic true를 기록해야 합니다.")
        if resolved_asset is not None and resolved_asset.is_file() and text(asset.get("sha256")):
            if sha256_for(resolved_asset) != text(asset.get("sha256")):
                errors.append("배경음 파일 해시가 rights-manifest와 다릅니다.")
    rights_record = music.get("rights")
    expected_music_status = "licensed" if music_mode == "licensed_catalog" else "owned"
    if not isinstance(rights_record, dict) or text(rights_record.get("permission_status")) != expected_music_status:
        errors.append(f"post-production.music.rights.permission_status는 {expected_music_status}여야 합니다.")
    segments = music.get("segments")
    if not isinstance(segments, list):
        errors.append("post-production.music.segments는 배열이어야 합니다.")
    else:
        seen_segments: set[str] = set()
        for index, value in enumerate(segments):
            label = f"post-production.music.segments[{index}]"
            if not isinstance(value, dict):
                errors.append(f"{label}은 객체여야 합니다.")
                continue
            scene_id = text(value.get("scene_id"))
            profile_id = text(value.get("profile_id"))
            if not scene_id or scene_id in seen_segments:
                errors.append(f"{label}.scene_id가 비어 있거나 중복되었습니다.")
            seen_segments.add(scene_id)
            if profile_id not in MUSIC_PROFILES:
                errors.append(f"{label}.profile_id가 지원 음악 프로필이 아닙니다.")
        expected = {text(scene.get("id")) for scene in scenes}
        if seen_segments != expected:
            errors.append("배경음 사용 시 모든 장면에 정확히 하나의 음악 구간이 필요합니다.")
    if music_mode == "synthetic_public_domain_remix":
        melody_id = text(music.get("melody_id"))
        melody = PUBLIC_DOMAIN_MELODIES.get(melody_id)
        if melody is None:
            errors.append("퍼블릭 도메인 리믹스의 melody_id가 지원 목록에 없습니다.")
        if text(music.get("arrangement")) != "tiktok-punch":
            errors.append("퍼블릭 도메인 리믹스 arrangement는 tiktok-punch여야 합니다.")
        bpm = music.get("bpm")
        if isinstance(bpm, bool) or not isinstance(bpm, (int, float)) or not 120 <= float(bpm) <= 200:
            errors.append("퍼블릭 도메인 리믹스 bpm은 120~200이어야 합니다.")
        loudness_target = music.get("loudness_target_lufs")
        true_peak = music.get("true_peak_db")
        if isinstance(loudness_target, bool) or not isinstance(loudness_target, (int, float)) or not -18 <= float(loudness_target) <= -10:
            errors.append("퍼블릭 도메인 리믹스 loudness_target_lufs는 -18~-10이어야 합니다.")
        if isinstance(true_peak, bool) or not isinstance(true_peak, (int, float)) or not -3 <= float(true_peak) <= -0.5:
            errors.append("퍼블릭 도메인 리믹스 true_peak_db는 -3~-0.5여야 합니다.")
        composition = music.get("composition")
        if not isinstance(composition, dict):
            errors.append("퍼블릭 도메인 리믹스에는 composition 기록이 필요합니다.")
        else:
            if text(composition.get("permission_status")) != "public_domain":
                errors.append("composition.permission_status는 public_domain이어야 합니다.")
            composition_url = text(composition.get("source_url"))
            if urlparse(composition_url).scheme != "https":
                errors.append("composition.source_url은 HTTPS 근거 주소여야 합니다.")
        asset_composition = asset.get("composition") if isinstance(asset, dict) else None
        if not isinstance(asset_composition, dict) or text(asset_composition.get("permission_status")) != "public_domain":
            errors.append("rights-manifest 배경음 자산에도 public_domain 작곡 기록이 필요합니다.")
    if music_mode == "licensed_catalog":
        track_id = text(music.get("track_id"))
        try:
            track = catalog_track(track_id)
        except WhiteboardShortsError as exc:
            errors.append(str(exc))
            track = None
        if isinstance(track, dict):
            required_matches = (
                ("title", "title"),
                ("artist", "artist"),
                ("license_url", "license_url"),
                ("source_page", "source_page"),
                ("attribution", "attribution"),
            )
            for music_key, catalog_key in required_matches:
                if text(music.get(music_key)) != text(track.get(catalog_key)):
                    errors.append(f"카탈로그 배경음 {music_key}가 검증 기록과 다릅니다.")
            if isinstance(asset, dict):
                if text(asset.get("track_id")) != track_id:
                    errors.append("rights-manifest 배경음 track_id가 다릅니다.")
                if text(asset.get("license_url")) != text(track.get("license_url")):
                    errors.append("rights-manifest 배경음 license_url이 다릅니다.")
                if text(asset.get("attribution")) != text(track.get("attribution")):
                    errors.append("rights-manifest 배경음 attribution이 다릅니다.")
                known_hash = text(track.get("known_file_sha256"))
                if resolved_asset is not None and resolved_asset.is_file() and sha256_for(resolved_asset) != known_hash:
                    errors.append("카탈로그 배경음 파일이 공식 검증 해시와 다릅니다.")
            if render_ready and (resolved_asset is None or not resolved_asset.is_file()):
                errors.append("렌더 전에 music-fetch로 검증된 카탈로그 음원을 받아야 합니다.")
        start_seconds = music.get("start_seconds")
        if isinstance(start_seconds, bool) or not isinstance(start_seconds, (int, float)) or float(start_seconds) < 0:
            errors.append("카탈로그 배경음 start_seconds는 0 이상이어야 합니다.")
        for key, minimum, maximum in (("loudness_target_lufs", -18, -10), ("true_peak_db", -3, -0.5)):
            value = music.get(key)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not minimum <= float(value) <= maximum:
                errors.append(f"카탈로그 배경음 {key}가 허용 범위를 벗어났습니다.")
    if not isinstance(profile, dict) or profile.get("audio") != "background_music" or profile.get("audio_codec") != "aac":
        errors.append("배경음 사용 시 render_profile은 background_music/AAC여야 합니다.")

    motion = postproduction.get("motion")
    if isinstance(motion, dict) and motion.get("enabled") is True:
        items = motion.get("items")
        if not isinstance(items, list):
            errors.append("post-production.motion.items는 배열이어야 합니다.")
        else:
            expected_scene_ids = {text(scene.get("id")) for scene in scenes}
            seen_motion: set[str] = set()
            for index, value in enumerate(items):
                label = f"post-production.motion.items[{index}]"
                if not isinstance(value, dict):
                    errors.append(f"{label}은 객체여야 합니다.")
                    continue
                scene_id = text(value.get("scene_id"))
                if scene_id not in expected_scene_ids or scene_id in seen_motion:
                    errors.append(f"{label}.scene_id가 없거나 중복되었습니다.")
                seen_motion.add(scene_id)
                motion_type = text(value.get("type"))
                if motion_type not in MOTION_TYPES:
                    errors.append(f"{label}.type이 지원 줌 유형이 아닙니다.")
                start_scale = value.get("start_scale")
                end_scale = value.get("end_scale")
                for key, number in (("start_scale", start_scale), ("end_scale", end_scale)):
                    if isinstance(number, bool) or not isinstance(number, (int, float)) or not 1 <= float(number) <= 1.2:
                        errors.append(f"{label}.{key}는 1~1.2여야 합니다.")
                for key in ("focus_x", "focus_y"):
                    number = value.get(key)
                    if isinstance(number, bool) or not isinstance(number, (int, float)) or not 0 <= float(number) <= 1:
                        errors.append(f"{label}.{key}는 0~1이어야 합니다.")


def validate_project(
    project_dir: Path,
    *,
    render_ready: bool,
    final: bool,
    selected_scene_ids: set[str] | None = None,
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        project, plan, rights = project_package(project_dir)
        postproduction = postproduction_plan(project_dir)
        scenes = scene_records(project_dir, plan)
    except WhiteboardShortsError as exc:
        return [str(exc)], warnings

    source = project.get("source_srt")
    if not isinstance(source, dict):
        errors.append("project.json의 source_srt가 필요합니다.")
    else:
        try:
            source_path = resolve_project_path(project_dir, text(source.get("path")))
            if sha256_for(source_path) != text(source.get("sha256")):
                errors.append("SRT 파일 해시가 project.json과 다릅니다.")
        except WhiteboardShortsError as exc:
            errors.append(str(exc))

    source_kind = text(project.get("source_kind")) or "local_srt"
    source_origin = project.get("source_origin")
    if source_kind == "tiktok_project":
        if not isinstance(source_origin, dict):
            errors.append("TikTok 프로젝트에는 project.json.source_origin이 필요합니다.")
        else:
            original_url = text(source_origin.get("original_url"))
            parsed_url = urlparse(original_url)
            hostname = (parsed_url.hostname or "").lower()
            if text(source_origin.get("platform")) != "tiktok" or not (
                parsed_url.scheme == "https" and (hostname == "tiktok.com" or hostname.endswith(".tiktok.com"))
            ):
                errors.append("source_origin에는 canonical HTTPS TikTok 원본 URL이 필요합니다.")
            if not text(source_origin.get("creator")):
                errors.append("source_origin.creator가 필요합니다.")
            source_media = source_origin.get("source_media")
            if not isinstance(source_media, dict):
                errors.append("source_origin.source_media가 필요합니다.")
            else:
                try:
                    source_media_path = resolve_project_path(project_dir, text(source_media.get("path")))
                    if sha256_for(source_media_path) != text(source_media.get("sha256")):
                        errors.append("가져온 TikTok 원본 영상 해시가 project.json과 다릅니다.")
                except WhiteboardShortsError as exc:
                    errors.append(str(exc))
    elif source_kind != "local_srt":
        errors.append(f"지원하지 않는 source_kind입니다: {source_kind}")

    profile = project.get("render_profile")
    expected_preview = {"width": 540, "height": 960, "frame_rate": 15}
    expected_final = {"width": 1080, "height": 1920, "frame_rate": 30}
    if not isinstance(profile, dict):
        errors.append("render_profile이 필요합니다.")
    else:
        if profile.get("preview") != expected_preview or profile.get("final") != expected_final:
            errors.append("render_profile은 540x960/15fps 미리보기와 1080x1920/30fps 최종 설정이어야 합니다.")
        if profile.get("video_codec") != "h264":
            errors.append("render_profile.video_codec은 h264여야 합니다.")

    validate_postproduction(
        project_dir,
        project,
        rights,
        scenes,
        postproduction,
        errors,
        warnings,
        render_ready=render_ready,
    )

    rights_source = rights.get("source")
    source_status = text(rights_source.get("permission_status")) if isinstance(rights_source, dict) else ""
    if isinstance(rights_source, dict) and isinstance(source, dict):
        if text(rights_source.get("path")) != text(source.get("path")):
            errors.append("rights-manifest.json의 SRT 경로가 project.json과 다릅니다.")
        if text(rights_source.get("sha256")) != text(source.get("sha256")):
            errors.append("rights-manifest.json의 SRT 해시가 project.json과 다릅니다.")
        if source_kind == "tiktok_project" and isinstance(source_origin, dict):
            if text(rights_source.get("original_url")) != text(source_origin.get("original_url")):
                errors.append("rights-manifest.json의 TikTok 원본 URL이 project.json과 다릅니다.")
            if text(rights_source.get("creator")) != text(source_origin.get("creator")):
                errors.append("rights-manifest.json의 TikTok 제작자가 project.json과 다릅니다.")
    if source_status not in KNOWN_RIGHTS_STATUSES:
        errors.append("SRT 원본의 올바른 permission_status가 필요합니다.")
    elif source_status == "not_permitted":
        errors.append("not_permitted SRT 원본은 미리보기나 렌더에 사용할 수 없습니다.")
    if not scenes:
        errors.append("장면 계획이 비어 있습니다.")
    if not isinstance(rights.get("assets"), list):
        errors.append("rights-manifest.json의 assets는 배열이어야 합니다.")

    seen_ids: set[str] = set()
    for index, scene in enumerate(scenes, start=1):
        scene_id = text(scene.get("id"))
        expected_id = f"scene-{index:02d}"
        if scene_id != expected_id or scene_id in seen_ids:
            errors.append(f"장면 ID는 순서대로 고유해야 합니다: 예상 {expected_id}, 현재 {scene_id or '(없음)'}")
        seen_ids.add(scene_id)
        if not text(scene.get("narration")):
            errors.append(f"{scene_id}: narration이 필요합니다.")
        if not is_integer(scene.get("scene_duration_ms")) or scene.get("scene_duration_ms", 0) <= 0:
            errors.append(f"{scene_id}: scene_duration_ms가 올바르지 않습니다.")
        if source_kind == "tiktok_project":
            tiktok_source = scene.get("tiktok_source")
            if not isinstance(tiktok_source, dict) or not text(tiktok_source.get("scene_id")):
                errors.append(f"{scene_id}: TikTok 원본 장면 연결이 필요합니다.")
            else:
                source_evidence = tiktok_source.get("source_evidence")
                if not isinstance(source_evidence, dict) or not text(source_evidence.get("observed_action")):
                    errors.append(f"{scene_id}: TikTok source_evidence.observed_action이 필요합니다.")
        image_relative = text(scene.get("image"))
        annotation_relative = text(scene.get("annotation"))
        if not image_relative or not annotation_relative:
            errors.append(f"{scene_id}: image와 annotation 경로가 필요합니다.")
            continue
        if selected_scene_ids is not None and scene_id not in selected_scene_ids:
            continue
        image = resolve_project_path(project_dir, image_relative, must_exist=False)
        annotation = resolve_project_path(project_dir, annotation_relative, must_exist=False)
        if not image.is_file() or not annotation.is_file():
            message = f"{scene_id}: 이미지 또는 annotation이 아직 없습니다."
            (errors if render_ready or final else warnings).append(message)
            continue
        asset = rights_asset(rights, image_relative)
        if asset is None:
            (errors if render_ready or final else warnings).append(f"{scene_id}: 이미지 권리 기록이 없습니다.")
        else:
            matching_assets = [
                item
                for item in rights.get("assets", [])
                if isinstance(item, dict) and text(item.get("path")) == image_relative
            ]
            if len(matching_assets) != 1:
                errors.append(f"{scene_id}: 이미지 권리 기록은 정확히 하나여야 합니다.")
            asset_status = text(asset.get("permission_status"))
            if asset_status not in KNOWN_RIGHTS_STATUSES:
                errors.append(f"{scene_id}: 이미지 permission_status가 올바르지 않습니다.")
            elif asset_status == "not_permitted":
                errors.append(f"{scene_id}: not_permitted 이미지는 렌더할 수 없습니다.")
            if final and asset_status not in FINAL_RIGHTS_STATUSES:
                errors.append(f"{scene_id}: clean final에는 확인된 이미지 권리가 필요합니다.")
            if final and asset_status in {"licensed", "permission_confirmed"} and not text(asset.get("permission_reference")):
                errors.append(f"{scene_id}: 확인된 권리의 permission_reference가 필요합니다.")
            if not isinstance(asset.get("synthetic"), bool):
                errors.append(f"{scene_id}: 이미지 권리 기록에 synthetic 불리언이 필요합니다.")
        try:
            scene_errors, scene_warnings = validate_annotation(scene, image, annotation)
            errors.extend(scene_errors)
            warnings.extend(scene_warnings)
        except WhiteboardShortsError as exc:
            errors.append(str(exc))

    if final:
        if source_status not in FINAL_RIGHTS_STATUSES:
            errors.append("clean final에는 확인된 SRT 원본 권리가 필요합니다.")
        if isinstance(rights_source, dict) and source_status in {"licensed", "permission_confirmed"} and not text(rights_source.get("permission_reference")):
            errors.append("확인된 SRT 권리의 permission_reference가 필요합니다.")
        approvals = project.get("approvals")
        if not isinstance(approvals, dict):
            errors.append("project.json의 approvals가 필요합니다.")
        else:
            missing = [name for name in FINAL_APPROVALS if approvals.get(name) is not True]
            if missing:
                errors.append("clean final 승인값이 부족합니다: " + ", ".join(missing))
        if not (project_dir / "outputs" / "preview.mp4").is_file():
            errors.append("clean final 전에 outputs/preview.mp4 초안이 필요합니다.")
    return errors, warnings


def command_validate(args: argparse.Namespace) -> int:
    project_dir = Path(args.project_dir).resolve()
    errors, warnings = validate_project(
        project_dir,
        render_ready=bool(args.render_ready or args.final),
        final=args.final,
    )
    payload = {
        "ok": not errors,
        "proof": "final-gates" if args.final else "render-ready" if args.render_ready else "project-static",
        "errors": errors,
        "warnings": warnings,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


def command_music_fetch(args: argparse.Namespace) -> int:
    project_dir = Path(args.project_dir).resolve()
    _, _, rights = project_package(project_dir)
    postproduction = postproduction_plan(project_dir)
    music = music_plan(postproduction)
    if music is None or text(music.get("mode")) != "licensed_catalog":
        raise WhiteboardShortsError("music-fetch는 licensed_catalog 배경음 프로젝트에서만 사용합니다.")
    planned_track_id = text(music.get("track_id"))
    if args.track and args.track != planned_track_id:
        raise WhiteboardShortsError("요청한 track과 post-production.json의 track_id가 다릅니다.")
    track = catalog_track(planned_track_id)
    asset_path = resolve_project_path(project_dir, text(music.get("asset_path")), must_exist=False)
    asset = rights_asset(rights, text(music.get("asset_path")))
    if asset is None:
        raise WhiteboardShortsError("카탈로그 음원의 rights-manifest 기록이 없습니다.")
    known_hash = text(track.get("known_file_sha256"))
    reused = asset_path.is_file() and sha256_for(asset_path) == known_hash
    if asset_path.exists() and not reused:
        protect_output(asset_path, args.overwrite)
    if not reused:
        asset_path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="whiteboard-music-fetch-") as temporary:
            downloaded = Path(temporary) / "track.mp3"
            download_url = text(track.get("download_url"))
            curl = shutil.which("curl")
            if curl:
                run_checked(
                    [
                        curl,
                        "--fail",
                        "--location",
                        "--silent",
                        "--show-error",
                        "--proto",
                        "=https",
                        "--tlsv1.2",
                        "--user-agent",
                        "WhiteboardShorts/0.5 (+local-review)",
                        "--output",
                        str(downloaded),
                        download_url,
                    ],
                    "공식 음원 다운로드",
                )
            else:
                request = Request(
                    download_url,
                    headers={"User-Agent": "WhiteboardShorts/0.5 (+local-review)"},
                )
                try:
                    with urlopen(request, timeout=30) as response, downloaded.open("wb") as output:
                        shutil.copyfileobj(response, output)
                except OSError as exc:
                    raise WhiteboardShortsError(f"공식 음원 다운로드 실패: {exc}") from exc
            actual_hash = sha256_for(downloaded)
            if actual_hash != known_hash:
                raise WhiteboardShortsError("다운로드한 음원의 SHA-256이 검증 카탈로그와 다릅니다.")
            shutil.copy2(downloaded, asset_path)
    asset.update(
        {
            "sha256": sha256_for(asset_path),
            "downloaded_at": iso_now(),
            "download_source": text(track.get("download_url")),
            "license_verified_at": text(music_catalog().get("verified_at")),
        }
    )
    write_json(project_dir / "rights-manifest.json", rights)
    print(
        json.dumps(
            {
                "ok": True,
                "track_id": planned_track_id,
                "title": text(track.get("title")),
                "artist": text(track.get("artist")),
                "path": str(asset_path),
                "sha256": sha256_for(asset_path),
                "license": text(track.get("license_name")),
                "attribution": text(track.get("attribution")),
                "reused": reused,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def find_font() -> Path | None:
    return next((path for path in FONT_CANDIDATES if path.is_file()), None)


def command_region_preview(args: argparse.Namespace) -> int:
    from PIL import Image, ImageDraw, ImageFont

    image_path = Path(args.image)
    annotation = require_object(load_json(Path(args.annotation)), "annotation")
    image = Image.open(image_path).convert("RGBA")
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    font_path = find_font()
    font = ImageFont.truetype(str(font_path), 28) if font_path else ImageFont.load_default()
    colors = ((38, 103, 255, 230), (255, 105, 92, 230), (41, 167, 102, 230), (181, 100, 255, 230))
    for index, value in enumerate(require_list(annotation.get("elements"), "elements"), start=1):
        element = require_object(value, f"element {index}")
        region = require_object(element.get("region"), f"element {index}.region")
        x, y = int(region["x"]), int(region["y"])
        right, bottom = x + int(region["width"]), y + int(region["height"])
        color = colors[(index - 1) % len(colors)]
        draw.rounded_rectangle((x, y, right, bottom), radius=12, outline=color, width=5, fill=(*color[:3], 24))
        label = f"{index}. {text(element.get('label')) or text(element.get('id'))}"
        text_box = draw.textbbox((0, 0), label, font=font)
        label_width = min(right - x, text_box[2] - text_box[0] + 28)
        draw.rounded_rectangle((x, y, x + label_width, y + 46), radius=8, fill=(255, 255, 255, 235))
        draw.text((x + 14, y + 7), label, font=font, fill=color)
        hand_path = require_object(element.get("handPath"), f"element {index}.handPath")
        start = tuple(hand_path["start"])
        end = tuple(hand_path["end"])
        draw.line((start, end), fill=color, width=5)
        draw.ellipse((end[0] - 7, end[1] - 7, end[0] + 7, end[1] + 7), fill=color)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    Image.alpha_composite(image, overlay).convert("RGB").save(output, quality=95)
    print(f"OUTPUT={output.resolve()}")
    return 0


def command_review_label(args: argparse.Namespace) -> int:
    from PIL import Image, ImageDraw, ImageFont

    width = int(args.width)
    height = int(args.height)
    if width <= 0 or height <= 0:
        raise WhiteboardShortsError("검토 영상 표시 크기는 양수여야 합니다.")
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    font_path = find_font()
    if args.label:
        banner_height = min(72, height)
        draw.rectangle((0, 0, width, banner_height), fill=(0, 0, 0, 174))
        font_size = 28
        while True:
            font = ImageFont.truetype(str(font_path), font_size) if font_path else ImageFont.load_default()
            box = draw.textbbox((0, 0), args.label, font=font)
            if box[2] - box[0] <= width - 24 or font_size <= 14 or not font_path:
                break
            font_size -= 2
        text_width = box[2] - box[0]
        text_height = box[3] - box[1]
        draw.text(
            ((width - text_width) // 2, (banner_height - text_height) // 2 - box[1]),
            args.label,
            font=font,
            fill=(255, 255, 255, 255),
        )

    caption = text(args.caption)
    if caption:
        max_width = width - max(64, width // 10)

        def wrapped_lines(value: str, font: Any) -> list[str]:
            lines: list[str] = []
            for paragraph in value.splitlines() or [""]:
                current = ""
                for character in paragraph:
                    trial = current + character
                    if current and draw.textbbox((0, 0), trial, font=font)[2] > max_width:
                        lines.append(current.strip())
                        current = character.lstrip()
                    else:
                        current = trial
                if current.strip():
                    lines.append(current.strip())
            return lines

        caption_size = min(68, max(32, round(width * 0.062)))
        while True:
            caption_font = (
                ImageFont.truetype(str(font_path), caption_size) if font_path else ImageFont.load_default()
            )
            lines = wrapped_lines(caption, caption_font)
            if len(lines) <= 2 or caption_size <= 30 or not font_path:
                break
            caption_size -= 2
        lines = lines[:2]
        line_boxes = [draw.textbbox((0, 0), line, font=caption_font) for line in lines]
        line_heights = [box[3] - box[1] for box in line_boxes]
        spacing = max(8, round(caption_size * 0.22))
        block_height = sum(line_heights) + spacing * max(0, len(lines) - 1)
        shorts_punch = args.caption_style in {"shorts-punch", "viral-punch"}
        anchor = {
            "top": 0.13 if shorts_punch else 0.16,
            "middle": 0.47,
            "bottom": 0.78 if shorts_punch else 0.76,
        }.get(args.caption_position, 0.76)
        text_top = max(92, min(height - block_height - 80, round(height * anchor)))
        box_width = min(width - 40, max(box[2] - box[0] for box in line_boxes) + 64)
        box_left = (width - box_width) // 2
        box_top = text_top - 24
        box_bottom = text_top + block_height + 24
        if not shorts_punch:
            draw.rounded_rectangle(
                (box_left, box_top, box_left + box_width, box_bottom),
                radius=max(18, width // 36),
                fill=(18, 18, 18, 214),
                outline=(242, 196, 94, 245),
                width=max(2, width // 270),
            )
        cursor_y = text_top
        for line_index, (line, box, line_height) in enumerate(zip(lines, line_boxes, line_heights)):
            line_width = box[2] - box[0]
            text_kwargs: dict[str, Any] = {}
            fill = (255, 242, 0, 255) if shorts_punch and line_index == 0 else (255, 255, 255, 255)
            if shorts_punch:
                text_kwargs = {
                    "stroke_width": max(4, width // 135),
                    "stroke_fill": (8, 8, 8, 255),
                }
            draw.text(
                ((width - line_width) // 2, cursor_y - box[1]),
                line,
                font=caption_font,
                fill=fill,
                **text_kwargs,
            )
            cursor_y += line_height + spacing
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    overlay.save(output)
    print(f"OUTPUT={output.resolve()}")
    return 0


def protect_output(path: Path, overwrite: bool) -> None:
    if path.exists() and not overwrite:
        raise WhiteboardShortsError(f"기존 출력은 --overwrite 없이 덮어쓸 수 없습니다: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)


def render_scene(
    python: Path,
    project_dir: Path,
    scene: dict[str, Any],
    output: Path,
    *,
    fps: int,
    cap_long_edge: int,
    ink_path: str,
    color_fill: str,
    overwrite: bool,
    review_label: str | None,
    caption: str = "",
    caption_position: str = "bottom",
    caption_style: str = "comic-observation",
    motion: dict[str, Any] | None = None,
) -> Path:
    protect_output(output, overwrite)
    image = resolve_project_path(project_dir, text(scene.get("image")))
    annotation = resolve_project_path(project_dir, text(scene.get("annotation")))
    needs_postprocess = bool(review_label or caption or motion)
    if needs_postprocess and not shutil.which("ffmpeg"):
        raise WhiteboardShortsError("검토 표시, 자막과 줌 합성에는 ffmpeg가 필요합니다.")
    with tempfile.TemporaryDirectory(prefix="whiteboard-render-") as temporary:
        temporary_path = Path(temporary)
        render_target = temporary_path / "unlabelled.mp4" if needs_postprocess else output
        run_checked(
            [
                str(python),
                str(VENDOR_SCRIPTS / "render_stream_whiteboard.py"),
                str(image),
                str(annotation),
                str(render_target),
                str(VENDOR_ASSETS / "drawing-hand.png"),
                "--ink-path",
                ink_path,
                "--color-fill",
                color_fill,
                "--fps",
                str(fps),
                "--cap-long-edge",
                str(cap_long_edge),
            ],
            f"{scene.get('id')} 렌더",
        )
        if needs_postprocess:
            source_width, source_height = image_size(image)
            scale = min(1.0, cap_long_edge / max(source_width, source_height))
            output_width = max(1, round(source_width * scale))
            output_height = max(1, round(source_height * scale))
            command = [
                shutil.which("ffmpeg") or "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-i",
                str(render_target),
            ]
            base_label = "[0:v]"
            filters: list[str] = []
            if motion:
                motion_type = text(motion.get("type"))
                start_scale = float(motion.get("start_scale", 1.0))
                end_scale = float(motion.get("end_scale", 1.05))
                focus_x = float(motion.get("focus_x", 0.5))
                focus_y = float(motion.get("focus_y", 0.5))
                frame_count = max(2, round(float(scene.get("scene_duration_ms", 0)) / 1_000 * fps))
                if motion_type == "punch-in":
                    zoom_frames = max(2, round(fps * 0.18))
                    zoom_expr = f"{start_scale:.4f}+({end_scale - start_scale:.4f})*min(on/{zoom_frames},1)"
                else:
                    zoom_expr = f"{start_scale:.4f}+({end_scale - start_scale:.4f})*on/{frame_count - 1}"
                filters.append(
                    f"[0:v]zoompan=z='{zoom_expr}':x='iw*{focus_x:.4f}-(iw/zoom*{focus_x:.4f})':"
                    f"y='ih*{focus_y:.4f}-(ih/zoom*{focus_y:.4f})':d=1:s={output_width}x{output_height}:fps={fps}[motion]"
                )
                base_label = "[motion]"
            if review_label or caption:
                label_image = temporary_path / "review-label.png"
                run_checked(
                    [
                        str(python),
                        str(Path(__file__).resolve()),
                        "_review-label",
                        "--output",
                        str(label_image),
                        "--width",
                        str(output_width),
                        "--height",
                        str(output_height),
                        "--label",
                        review_label or "",
                        "--caption",
                        caption,
                        "--caption-position",
                        caption_position,
                        "--caption-style",
                        caption_style,
                    ],
                    "검토 영상 표시 이미지 생성",
                )
                command.extend(["-framerate", str(fps), "-loop", "1", "-i", str(label_image)])
                filters.append(f"{base_label}[1:v]overlay=x=0:y=0:shortest=1[v]")
            elif motion:
                filters.append(f"{base_label}null[v]")
            command.extend(
                [
                    "-filter_complex",
                    ";".join(filters),
                    "-map",
                    "[v]",
                    "-shortest",
                    "-an",
                    "-c:v",
                    "libx264",
                    "-pix_fmt",
                    "yuv420p",
                    str(output),
                ]
            )
            run_checked(command, "검토 영상 표시와 장면 줌 합성")
    return output


def media_probe(path: Path) -> dict[str, Any]:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        return {"path": str(path), "probe": "ffprobe-unavailable"}
    result = run_checked(
        [ffprobe, "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
        "렌더 결과 확인",
    )
    payload = require_object(json.loads(result.stdout), "ffprobe 결과")
    streams = require_list(payload.get("streams", []), "ffprobe streams")
    video = next((item for item in streams if isinstance(item, dict) and item.get("codec_type") == "video"), {})
    audio = next((item for item in streams if isinstance(item, dict) and item.get("codec_type") == "audio"), None)
    return {
        "path": str(path),
        "sha256": sha256_for(path),
        "width": video.get("width"),
        "height": video.get("height"),
        "video_codec": video.get("codec_name"),
        "frame_rate": video.get("avg_frame_rate"),
        "has_audio": audio is not None,
        "audio_codec": audio.get("codec_name") if isinstance(audio, dict) else "",
        "audio_sample_rate": audio.get("sample_rate") if isinstance(audio, dict) else "",
        "audio_channels": audio.get("channels") if isinstance(audio, dict) else 0,
        "duration_seconds": require_object(payload.get("format", {}), "ffprobe format").get("duration"),
    }


def verify_render_probe(probe: dict[str, Any], warnings: list[str], *, expected_audio: bool) -> None:
    if probe.get("probe") == "ffprobe-unavailable":
        warnings.append("ffprobe가 없어 렌더 파일의 해상도와 코덱을 확인하지 못했습니다.")
        return
    if (probe.get("width"), probe.get("height")) != (1080, 1920):
        raise WhiteboardShortsError(
            f"렌더 결과 해상도가 1080x1920이 아닙니다: {probe.get('width')}x{probe.get('height')}"
        )
    if probe.get("video_codec") != "h264":
        raise WhiteboardShortsError(f"렌더 결과 비디오 코덱이 H.264가 아닙니다: {probe.get('video_codec')}")
    if probe.get("frame_rate") not in {"30/1", "30"}:
        raise WhiteboardShortsError(f"렌더 결과 프레임률이 30 FPS가 아닙니다: {probe.get('frame_rate')}")
    if expected_audio:
        if probe.get("has_audio") is not True or probe.get("audio_codec") != "aac":
            raise WhiteboardShortsError("배경음 사용 결과에는 AAC 오디오 스트림이 필요합니다.")
    elif probe.get("has_audio") is not False:
        raise WhiteboardShortsError("배경음 미사용 결과에는 오디오 스트림이 없어야 합니다.")


def review_label_for(rights: dict[str, Any], scene: dict[str, Any]) -> str:
    statuses: set[str] = set()
    source = rights.get("source")
    if isinstance(source, dict):
        statuses.add(text(source.get("permission_status")))
    asset = rights_asset(rights, text(scene.get("image")))
    if asset:
        statuses.add(text(asset.get("permission_status")))
    if statuses.issubset(FINAL_RIGHTS_STATUSES):
        return "LOCAL REVIEW"
    return "LOCAL REVIEW - RIGHTS UNCONFIRMED"


CAN_CAN_PATTERN = (
    (78, 1.0), (74, 1.0), (71, 1.0), (69, 1.0),
    (69, 0.5), (76, 0.5), (78, 0.5), (79, 0.5), (78, 0.5), (76, 0.5), (74, 1.0),
    (78, 1.0), (74, 1.0), (71, 1.0), (69, 1.0),
    (68, 0.5), (69, 0.5), (71, 0.5), (73, 0.5), (76, 0.5), (74, 0.5), (74, 1.0),
)


def midi_frequency(note: int) -> float:
    return 440.0 * (2.0 ** ((note - 69) / 12.0))


def create_public_domain_remix(
    path: Path,
    duration: float,
    profile_id: str,
    *,
    bpm: float,
    start_offset: float,
    impact: bool,
) -> None:
    sample_rate = 48_000
    beat_seconds = 60.0 / bpm
    starts: list[float] = []
    note_durations: list[float] = []
    cursor = 0.0
    for _, beats in CAN_CAN_PATTERN:
        starts.append(cursor)
        note_duration = beats * beat_seconds
        note_durations.append(note_duration)
        cursor += note_duration
    cycle_seconds = cursor
    profile_gain = {
        "gentle": 0.58,
        "tender": 0.66,
        "tension": 0.76,
        "relief": 0.9,
        "playful": 1.0,
    }[profile_id]
    frames = bytearray()
    frame_count = max(1, round(duration * sample_rate))
    for frame in range(frame_count):
        local_t = frame / sample_rate
        absolute_t = start_offset + local_t
        motif_t = absolute_t % cycle_seconds
        note_index = max(0, bisect_right(starts, motif_t) - 1)
        note, _ = CAN_CAN_PATTERN[note_index]
        note_t = motif_t - starts[note_index]
        note_duration = note_durations[note_index]
        note_envelope = min(1.0, note_t / 0.012) * math.exp(-2.7 * note_t / note_duration)
        frequency = midi_frequency(note)
        melody_left = (
            math.sin(2 * math.pi * frequency * absolute_t)
            + 0.38 * math.sin(4 * math.pi * frequency * absolute_t)
            + 0.14 * math.sin(6 * math.pi * frequency * absolute_t)
        ) * note_envelope * 0.2 * profile_gain
        detuned = frequency * 1.003
        melody_right = (
            math.sin(2 * math.pi * detuned * absolute_t)
            + 0.38 * math.sin(4 * math.pi * detuned * absolute_t)
            + 0.14 * math.sin(6 * math.pi * detuned * absolute_t)
        ) * note_envelope * 0.2 * profile_gain

        beat_phase = absolute_t % beat_seconds
        beat_index = int(absolute_t / beat_seconds)
        kick_frequency = 48.0 + 72.0 * math.exp(-28.0 * beat_phase)
        kick = 0.34 * math.sin(2 * math.pi * kick_frequency * beat_phase) * math.exp(-15.0 * beat_phase)
        bass_frequency = 73.42 if (beat_index // 4) % 2 == 0 else 55.0
        bass = (
            math.sin(2 * math.pi * bass_frequency * absolute_t)
            + 0.3 * math.sin(4 * math.pi * bass_frequency * absolute_t)
        ) * math.exp(-4.5 * beat_phase) * 0.15 * profile_gain

        clap_phase = beat_phase if beat_index % 4 in {1, 3} else beat_seconds
        clap_noise = math.sin(2 * math.pi * 2_911 * absolute_t) * math.sin(2 * math.pi * 4_273 * absolute_t)
        clap = 0.15 * clap_noise * math.exp(-22.0 * clap_phase) if clap_phase < 0.18 else 0.0
        half_beat = beat_seconds / 2
        hat_phase = absolute_t % half_beat
        hat_noise = math.sin(2 * math.pi * 8_109 * absolute_t) * math.sin(2 * math.pi * 11_173 * absolute_t)
        hat = 0.055 * hat_noise * math.exp(-38.0 * hat_phase)

        impact_hit = 0.0
        if impact and local_t < 0.42:
            impact_hit = (
                0.42 * math.sin(2 * math.pi * (62.0 + 115.0 * math.exp(-9.0 * local_t)) * local_t)
                + 0.12 * math.sin(2 * math.pi * 1_800 * local_t)
            ) * math.exp(-7.5 * local_t)
        riser = 0.0
        if profile_id == "tension" and duration - local_t < 0.38:
            riser_phase = max(0.0, (local_t - (duration - 0.38)) / 0.38)
            riser = 0.09 * riser_phase * math.sin(2 * math.pi * (380.0 + 1_250.0 * riser_phase**2) * local_t)

        left = math.tanh((melody_left + bass + kick + 0.82 * clap + hat + impact_hit + riser) * 1.22) * 0.86
        right = math.tanh((melody_right + bass + kick + clap + 0.82 * hat + impact_hit + riser) * 1.22) * 0.86
        frames.extend(struct.pack("<hh", round(left * 32767), round(right * 32767)))
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as output:
        output.setnchannels(2)
        output.setsampwidth(2)
        output.setframerate(sample_rate)
        output.writeframes(frames)


def create_mood_bed(
    path: Path,
    duration: float,
    profile_id: str,
    *,
    music: dict[str, Any],
    start_offset: float,
    impact: bool,
) -> None:
    if profile_id not in MUSIC_PROFILES:
        raise WhiteboardShortsError(f"지원하지 않는 음악 프로필입니다: {profile_id}")
    if text(music.get("mode")) == "synthetic_public_domain_remix":
        create_public_domain_remix(
            path,
            duration,
            profile_id,
            bpm=float(music.get("bpm", PUBLIC_DOMAIN_MELODIES["can-can"]["default_bpm"])),
            start_offset=start_offset,
            impact=impact,
        )
        return
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
        amplitude = "0.045"
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
        "무보컬 배경음 구간 생성",
    )


def concatenate_mood_beds(paths: list[Path], destination: Path) -> None:
    if not paths:
        raise WhiteboardShortsError("이어 붙일 배경음 구간이 없습니다.")
    concat_file = paths[0].parent / "concat.txt"
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


def build_music_bed(
    project_dir: Path,
    rights: dict[str, Any],
    scenes: list[dict[str, Any]],
    music: dict[str, Any],
    *,
    overwrite: bool,
) -> Path:
    asset_path = resolve_project_path(project_dir, text(music.get("asset_path")), must_exist=False)
    existing_asset = rights_asset(rights, text(music.get("asset_path")))
    if text(music.get("mode")) == "licensed_catalog":
        if not asset_path.is_file():
            raise WhiteboardShortsError("카탈로그 음원이 없습니다. 먼저 music-fetch를 실행하세요.")
        if existing_asset is None:
            raise WhiteboardShortsError("카탈로그 음원의 rights-manifest 기록이 없습니다.")
        recorded_hash = text(existing_asset.get("sha256"))
        if not recorded_hash or sha256_for(asset_path) != recorded_hash:
            raise WhiteboardShortsError("카탈로그 음원 파일 해시가 rights-manifest와 다릅니다.")
        return asset_path
    if asset_path.is_file() and not overwrite:
        if existing_asset and text(existing_asset.get("sha256")) == sha256_for(asset_path):
            return asset_path
        raise WhiteboardShortsError(f"기존 배경음은 --overwrite 없이 덮어쓸 수 없습니다: {asset_path}")
    protect_output(asset_path, overwrite)
    segment_records = {
        text(value.get("scene_id")): value
        for value in require_list(music.get("segments"), "post-production.music.segments")
        if isinstance(value, dict)
    }
    with tempfile.TemporaryDirectory(prefix="whiteboard-music-") as temporary:
        temporary_path = Path(temporary)
        segments: list[Path] = []
        start_offset = 0.0
        for index, scene in enumerate(scenes, start=1):
            scene_id = text(scene.get("id"))
            segment = temporary_path / f"segment-{index:02d}.wav"
            duration = float(scene.get("scene_duration_ms", 0)) / 1_000
            segment_record = require_object(segment_records[scene_id], f"music segment {scene_id}")
            create_mood_bed(
                segment,
                duration,
                text(segment_record.get("profile_id")),
                music=music,
                start_offset=start_offset,
                impact=segment_record.get("impact") is True,
            )
            segments.append(segment)
            start_offset += duration
        concatenate_mood_beds(segments, asset_path)
    asset = existing_asset
    if asset is None:
        raise WhiteboardShortsError("생성 배경음 권리 기록을 찾을 수 없습니다.")
    asset["sha256"] = sha256_for(asset_path)
    asset["generated_at"] = iso_now()
    asset["generation_provider"] = "Whiteboard Shorts original recording generator"
    asset["music_mode"] = text(music.get("mode"))
    asset["melody_id"] = text(music.get("melody_id"))
    asset["arrangement"] = text(music.get("arrangement"))
    write_json(project_dir / "rights-manifest.json", rights)
    return asset_path


def mix_background_music(
    video: Path,
    audio: Path,
    output: Path,
    *,
    duration: float,
    volume: float,
    fade_in: float,
    fade_out: float,
    loudness_target: float | None = None,
    true_peak: float = -1.5,
    audio_start_seconds: float = 0.0,
) -> None:
    filters = [f"volume={volume:.3f}"]
    if loudness_target is not None:
        filters.append(f"loudnorm=I={loudness_target:.1f}:TP={true_peak:.1f}:LRA=7")
    if fade_in > 0:
        filters.append(f"afade=t=in:st=0:d={fade_in:.3f}")
    if fade_out > 0:
        filters.append(f"afade=t=out:st={max(0.0, duration - fade_out):.3f}:d={fade_out:.3f}")
    command = [
        shutil.which("ffmpeg") or "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(video),
    ]
    if audio_start_seconds > 0:
        command.extend(["-ss", f"{audio_start_seconds:.3f}"])
    command.extend(
        [
            "-i",
            str(audio),
            "-filter_complex",
            f"[1:a]{','.join(filters)}[bgm]",
            "-map",
            "0:v:0",
            "-map",
            "[bgm]",
            "-t",
            f"{duration:.3f}",
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
        ]
    )
    run_checked(command, "무보컬 배경음 합성")


def write_delivery_note(project_dir: Path, music: dict[str, Any] | None) -> Path | None:
    if music is None or text(music.get("mode")) != "licensed_catalog":
        return None
    delivery_note = project_dir / "delivery-note.md"
    delivery_note.write_text(
        "\n".join(
            [
                "# 게시 전 음원 확인",
                "",
                f"- 사용 음원: {text(music.get('title'))} — {text(music.get('artist'))}",
                f"- 필수 크레딧: {text(music.get('attribution'))}",
                f"- 음원 출처: {text(music.get('source_page'))}",
                f"- 라이선스: {text(music.get('license_name'))} ({text(music.get('license_url'))})",
                "",
                "설명란에 필수 크레딧을 그대로 넣으세요. 플랫폼의 상업 음원을 쓰고 싶다면 파일에 직접 섞지 말고, 업로드 뒤 YouTube Shorts 공식 음악 선택기에서 추가하세요.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return delivery_note


def command_preview(args: argparse.Namespace) -> int:
    project_dir = Path(args.project_dir).resolve()
    _, _, rights, scene = scene_by_id(project_dir, args.scene)
    postproduction = postproduction_plan(project_dir)
    errors, _ = validate_project(
        project_dir,
        render_ready=True,
        final=False,
        selected_scene_ids={args.scene},
    )
    if errors:
        raise WhiteboardShortsError("미리보기 준비 오류:\n- " + "\n- ".join(errors))
    preview_python = Path(sys.executable) if importlib.util.find_spec("PIL") else require_runtime()
    image = resolve_project_path(project_dir, text(scene.get("image")))
    annotation = resolve_project_path(project_dir, text(scene.get("annotation")))
    region_output = project_dir / "previews" / f"{args.scene}-regions.png"
    protect_output(region_output, args.overwrite)
    run_checked(
        [
            str(preview_python),
            str(Path(__file__).resolve()),
            "_region-preview",
            "--image",
            str(image),
            "--annotation",
            str(annotation),
            "--output",
            str(region_output),
        ],
        "영역 확인 이미지 생성",
    )
    outputs = [str(region_output)]
    if not args.regions_only:
        python = require_runtime()
        video_output = project_dir / "previews" / f"{args.scene}.mp4"
        caption, caption_position, caption_style = caption_for_scene(postproduction, args.scene)
        render_scene(
            python,
            project_dir,
            scene,
            video_output,
            fps=15,
            cap_long_edge=960,
            ink_path=args.ink_path,
            color_fill=args.color_fill,
            overwrite=args.overwrite,
            review_label=review_label_for(rights, scene),
            caption=caption,
            caption_position=caption_position,
            caption_style=caption_style,
            motion=motion_for_scene(postproduction, args.scene),
        )
        outputs.append(str(video_output))
    print(json.dumps({"scene": args.scene, "outputs": outputs, "proof": "local-review"}, ensure_ascii=False, indent=2))
    return 0


def command_render(args: argparse.Namespace) -> int:
    project_dir = Path(args.project_dir).resolve()
    project, plan, rights = project_package(project_dir)
    if args.hide_review_label:
        if not args.draft:
            raise WhiteboardShortsError("--hide-review-label은 로컬 draft에서만 사용할 수 있습니다.")
        news_source = project.get("news2shorts_source")
        if not isinstance(news_source, dict) or news_source.get("publish_blocked") is not True:
            raise WhiteboardShortsError(
                "--hide-review-label은 publish_blocked가 기록된 news2shorts Whiteboard 프로젝트만 지원합니다."
            )
    postproduction = postproduction_plan(project_dir)
    music = music_plan(postproduction)
    scenes = scene_records(project_dir, plan)
    selected = scenes if args.all else [next((item for item in scenes if text(item.get("id")) == args.scene), None)]
    if selected == [None]:
        raise WhiteboardShortsError(f"장면을 찾을 수 없습니다: {args.scene}")
    errors, warnings = validate_project(
        project_dir,
        render_ready=True,
        final=not args.draft,
        selected_scene_ids=None if args.all else {args.scene},
    )
    if errors:
        raise WhiteboardShortsError("렌더 준비 오류:\n- " + "\n- ".join(errors))
    python = require_runtime()
    rendered: list[Path] = []
    for raw_scene in selected:
        scene = require_object(raw_scene, "selected scene")
        scene_id = text(scene.get("id"))
        name = f"{scene_id}-draft.mp4" if args.draft else f"{scene_id}.mp4"
        output = project_dir / "renders" / name
        caption, caption_position, caption_style = caption_for_scene(postproduction, scene_id)
        render_scene(
            python,
            project_dir,
            scene,
            output,
            fps=30,
            cap_long_edge=1920,
            ink_path=args.ink_path,
            color_fill=args.color_fill,
            overwrite=args.overwrite,
            review_label=(
                None
                if args.hide_review_label
                else review_label_for(rights, scene) if args.draft else None
            ),
            caption=caption,
            caption_position=caption_position,
            caption_style=caption_style,
            motion=motion_for_scene(postproduction, scene_id),
        )
        rendered.append(output)

    final_output: Path | None = None
    if args.all:
        final_output = project_dir / "outputs" / ("preview.mp4" if args.draft else "final.mp4")
        protect_output(final_output, args.overwrite)
        if music is None:
            run_checked(
                [
                    str(python),
                    str(VENDOR_SCRIPTS / "merge_scenes.py"),
                    "--inputs",
                    *[str(path) for path in rendered],
                    "--output",
                    str(final_output),
                ],
                "장면 병합",
            )
        else:
            with tempfile.TemporaryDirectory(prefix="whiteboard-merge-") as temporary:
                merged_video = Path(temporary) / "video-only.mp4"
                run_checked(
                    [
                        str(python),
                        str(VENDOR_SCRIPTS / "merge_scenes.py"),
                        "--inputs",
                        *[str(path) for path in rendered],
                        "--output",
                        str(merged_video),
                    ],
                    "장면 병합",
                )
                background_music = build_music_bed(
                    project_dir,
                    rights,
                    selected,
                    music,
                    overwrite=args.overwrite,
                )
                duration = sum(float(scene.get("scene_duration_ms", 0)) for scene in selected) / 1_000
                mix_background_music(
                    merged_video,
                    background_music,
                    final_output,
                    duration=duration,
                    volume=float(music.get("volume", 0.24)),
                    fade_in=float(music.get("fade_in_seconds", 0.25)),
                    fade_out=float(music.get("fade_out_seconds", 0.45)),
                    loudness_target=(
                        float(music["loudness_target_lufs"])
                        if isinstance(music.get("loudness_target_lufs"), (int, float))
                        and not isinstance(music.get("loudness_target_lufs"), bool)
                        else None
                    ),
                    true_peak=float(music.get("true_peak_db", -1.5)),
                    audio_start_seconds=float(music.get("start_seconds", 0.0)),
                )

    cta_report: dict[str, Any] = {"enabled": False}
    if final_output is not None:
        base_probe = media_probe(final_output)
        source_duration = float(base_probe.get("duration_seconds") or 0)
        with tempfile.TemporaryDirectory(prefix=".whiteboard-cta-", dir=project_dir) as temporary:
            cta_output = Path(temporary) / "cta-appended.mp4"
            try:
                cta_report = append_cta_tail(
                    final_output,
                    cta_output,
                    width=int(base_probe.get("width") or 1080),
                    height=int(base_probe.get("height") or 1920),
                    source_duration=source_duration,
                    has_audio=bool(base_probe.get("has_audio")),
                    font_path=find_font(),
                    headline="다음 반전도 계속",
                    prompt="구독 · 좋아요",
                    ffmpeg=shutil.which("ffmpeg") or "ffmpeg",
                )
            except YouTubeDeliveryError as exc:
                raise WhiteboardShortsError(str(exc)) from exc
            cta_output.replace(final_output)

    probed = [media_probe(path) for path in ([final_output] if final_output else rendered) if path is not None]
    for probe in probed:
        verify_render_probe(probe, warnings, expected_audio=bool(args.all))
    delivery_note = write_delivery_note(project_dir, music if args.all else None)
    report = {
        "version": 1,
        "rendered_at": iso_now(),
        "mode": "draft" if args.draft else "final",
        "scenes": [text(require_object(item, "scene").get("id")) for item in selected],
        "ink_path": args.ink_path,
        "color_fill": args.color_fill,
        "visible_review_label": bool(args.draft and not args.hide_review_label),
        "review_state_in_metadata": bool(args.draft),
        "publish_blocked": bool(args.draft),
        "cta_tail": cta_report,
        "post_production": {
            "captions": bool(isinstance(postproduction.get("captions"), dict) and postproduction["captions"].get("enabled") is True),
            "caption_style": text(postproduction.get("captions", {}).get("style")) if isinstance(postproduction.get("captions"), dict) else "",
            "music": text(music.get("mode")) if music else "none",
            "music_asset": text(music.get("asset_path")) if music and args.all else "",
            "track_id": text(music.get("track_id")) if music else "",
            "track_title": text(music.get("title")) if music else "",
            "track_artist": text(music.get("artist")) if music else "",
            "melody_id": text(music.get("melody_id")) if music else "",
            "arrangement": text(music.get("arrangement")) if music else "",
            "loudness_target_lufs": music.get("loudness_target_lufs") if music else None,
            "true_peak_db": music.get("true_peak_db") if music else None,
            "license_name": text(music.get("license_name")) if music else "",
            "license_url": text(music.get("license_url")) if music else "",
            "source_page": text(music.get("source_page")) if music else "",
            "attribution": text(music.get("attribution")) if music else "",
            "delivery_note": str(delivery_note.relative_to(project_dir)) if delivery_note else "",
            "motion_scenes": [
                text(value.get("scene_id"))
                for value in postproduction.get("motion", {}).get("items", [])
                if isinstance(value, dict)
            ]
            if isinstance(postproduction.get("motion"), dict)
            else [],
        },
        "upstream_commit": UPSTREAM_COMMIT,
        "outputs": probed,
        "warnings": warnings,
        "proof_note": "로컬 렌더 성공은 게시 권리, 사실 정확성, 플랫폼 승인 또는 수익화를 증명하지 않습니다.",
    }
    if final_output is not None:
        rights_source = require_object(rights.get("source"), "rights-manifest.source")
        rights_status = text(rights_source.get("permission_status")) or "unknown"
        title = text(project.get("title")) or "Whiteboard Shorts"
        upload_json, upload_md, _ = write_upload_package(
            project_dir,
            video_path=str(final_output.relative_to(project_dir)),
            title=title,
            description=(
                f"{title}\n\n검토된 장면 근거를 손그림 애니메이션과 반전 자막으로 재구성한 쇼츠입니다.\n"
                f"권리 상태: {rights_status}\n\n#화이트보드 #Shorts"
            ),
            tags=["화이트보드", "애니메이션", "Shorts"],
            thumbnail_note="CTA 직전 반전 장면에서 선화와 결론 자막이 함께 완성된 프레임",
            playlist="Whiteboard Shorts",
            category="Film & Animation",
            language="ko",
            pinned_comment=f"{title}에서 가장 기억에 남은 반전 장면은 무엇인가요?",
            rights_status=rights_status,
            synthetic_elements=True,
            generated_at=report["rendered_at"],
        )
        report["youtube_upload"] = {
            "json": str(upload_json.relative_to(project_dir)),
            "markdown": str(upload_md.relative_to(project_dir)),
            "upload_performed": False,
        }
    write_json(project_dir / "render-report.json", report)
    project["status"] = "draft_rendered" if args.draft else "rendered"
    project["updated_at"] = iso_now()
    project["last_render"] = {
        "mode": report["mode"],
        "rendered_at": report["rendered_at"],
        "output": str((final_output or rendered[0]).relative_to(project_dir)),
        "report": "render-report.json",
    }
    write_json(project_dir / "project.json", project)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


def command_upload_package(args: argparse.Namespace) -> int:
    project_dir = Path(args.project_dir).expanduser().resolve()
    try:
        _, markdown = read_upload_package(project_dir / "youtube-upload.json")
    except YouTubeDeliveryError as exc:
        raise WhiteboardShortsError(str(exc)) from exc
    print(markdown, end="")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="SRT와 9:16 장면 이미지를 로컬 화이트보드 쇼츠로 렌더링합니다.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor = subparsers.add_parser("doctor", help="환경과 업스트림 파일을 읽기 전용으로 확인합니다.")
    doctor.add_argument("--json", action="store_true")
    doctor.set_defaults(handler=command_doctor)

    setup = subparsers.add_parser("setup", help="격리 렌더 환경을 명시적으로 준비합니다.")
    setup.add_argument("--check", action="store_true", help="설치하지 않고 기존 격리 환경만 확인합니다.")
    setup.set_defaults(handler=command_setup)

    preflight = subparsers.add_parser("preflight", help="TikTok 원본의 화이트보드 변환 적합성을 가져오기 전에 확인합니다.")
    preflight.add_argument("--source-project", required=True, help="검토가 끝난 tiktok2shorts 프로젝트 폴더")
    preflight.set_defaults(handler=command_preflight)

    init = subparsers.add_parser("init", help="TikTok2Shorts 프로젝트 또는 로컬 SRT에서 장면 계획을 생성합니다.")
    init.add_argument("--project-dir", required=True)
    source_input = init.add_mutually_exclusive_group(required=True)
    source_input.add_argument("--source-project", help="선택·다운로드·검토된 tiktok2shorts 프로젝트 폴더")
    source_input.add_argument("--srt", help="호환용 로컬 SRT 파일")
    init.add_argument("--title", default="")
    init.add_argument("--rights-status", choices=sorted(KNOWN_RIGHTS_STATUSES))
    init.add_argument("--rights-reference", default="")
    init.add_argument("--target-sec", type=float, default=30.0)
    init.add_argument("--min-sec", type=float, default=25.0)
    init.add_argument("--max-sec", type=float, default=35.0)
    init.set_defaults(handler=command_init)

    validate = subparsers.add_parser("validate", help="프로젝트, annotation, 권리와 승인 상태를 검사합니다.")
    validate.add_argument("--project-dir", required=True)
    validate.add_argument("--render-ready", action="store_true")
    validate.add_argument("--final", action="store_true")
    validate.set_defaults(handler=command_validate)

    music_fetch = subparsers.add_parser("music-fetch", help="검증된 쇼츠 음원을 공식 제공처에서 프로젝트로 받습니다.")
    music_fetch.add_argument("--project-dir", required=True)
    music_fetch.add_argument("--track", default="", help="post-production.json track_id 확인용")
    music_fetch.add_argument("--overwrite", action="store_true")
    music_fetch.set_defaults(handler=command_music_fetch)

    preview = subparsers.add_parser("preview", help="영역 확인 이미지와 저해상도 로컬 검토 영상을 만듭니다.")
    preview.add_argument("--project-dir", required=True)
    preview.add_argument("--scene", required=True)
    preview.add_argument("--regions-only", action="store_true")
    preview.add_argument("--ink-path", choices=("grid", "skeleton"), default="grid")
    preview.add_argument("--color-fill", choices=("contour-wipe", "brush"), default="contour-wipe")
    preview.add_argument("--overwrite", action="store_true")
    preview.set_defaults(handler=command_preview)

    render = subparsers.add_parser("render", help="확인된 장면을 최종 크기로 렌더링하고 선택적으로 병합합니다.")
    render.add_argument("--project-dir", required=True)
    selection = render.add_mutually_exclusive_group(required=True)
    selection.add_argument("--scene")
    selection.add_argument("--all", action="store_true")
    render.add_argument("--draft", action="store_true")
    render.add_argument("--ink-path", choices=("grid", "skeleton"), default="grid")
    render.add_argument("--color-fill", choices=("contour-wipe", "brush"), default="contour-wipe")
    render.add_argument("--overwrite", action="store_true")
    render.add_argument(
        "--hide-review-label",
        action="store_true",
        help="publish_blocked news2shorts Whiteboard draft에서 화면 검토 배지만 숨깁니다.",
    )
    render.set_defaults(handler=command_render)

    upload_package = subparsers.add_parser("upload-package", help="전체 렌더 결과의 YouTube 업로드 정보를 출력합니다.")
    upload_package.add_argument("--project-dir", required=True)
    upload_package.set_defaults(handler=command_upload_package)

    return parser


def main() -> int:
    try:
        if sys.argv[1:2] == ["_region-preview"]:
            internal = argparse.ArgumentParser(add_help=False)
            internal.add_argument("--image", required=True)
            internal.add_argument("--annotation", required=True)
            internal.add_argument("--output", required=True)
            args = internal.parse_args(sys.argv[2:])
            return command_region_preview(args)
        if sys.argv[1:2] == ["_review-label"]:
            internal = argparse.ArgumentParser(add_help=False)
            internal.add_argument("--output", required=True)
            internal.add_argument("--width", required=True, type=int)
            internal.add_argument("--height", required=True, type=int)
            internal.add_argument("--label", required=True)
            internal.add_argument("--caption", default="")
            internal.add_argument("--caption-position", choices=sorted(CAPTION_POSITIONS), default="bottom")
            internal.add_argument("--caption-style", choices=sorted(CAPTION_STYLES), default="comic-observation")
            args = internal.parse_args(sys.argv[2:])
            return command_review_label(args)
        args = build_parser().parse_args()
        return int(args.handler(args))
    except WhiteboardShortsError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
