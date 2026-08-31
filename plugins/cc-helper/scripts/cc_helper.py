#!/usr/bin/env python3
"""Prepare source-backed, editable CapCut drafts from a fixed local template."""

from __future__ import annotations

import argparse
import copy
import csv
import datetime as dt
import hashlib
import json
import math
import mimetypes
import os
import random
import re
import shutil
import ssl
import struct
import subprocess
import sys
import tempfile
import time
import unicodedata
import uuid
import wave
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterable
from urllib import error, parse, request


VERSION = 1
SCENE_COUNT = 15
NARRATION_HOLD_MODE = "narration-hold"
SUPPORTED_PACING_MODES = {"", NARRATION_HOLD_MODE}
NARRATION_FLOW_MODE = "conversational-chain"
SUPPORTED_NARRATION_FLOW_MODES = {"", NARRATION_FLOW_MODE}
NARRATION_PERFORMANCE_MODE = "reviewed-external"
SUPPORTED_NARRATION_PERFORMANCE_MODES = {"", NARRATION_PERFORMANCE_MODE}
NARRATION_FLOW_ROLES = (
    "hook",
    "setup",
    "trigger",
    "explanation",
    "reaction",
    "response",
    "consequence",
    "resolution",
    "aftermath",
)
CAPTION_SYNC_MODE = "clause"
SUPPORTED_CAPTION_SYNC_MODES = {"", CAPTION_SYNC_MODE}
EVIDENCE_FIRST_MODE = "evidence-first"
SUPPORTED_VISUAL_VALIDATION_MODES = {"", EVIDENCE_FIRST_MODE}
DISPLAY_VALIDATION_MODE = "short-preview"
SUPPORTED_DISPLAY_VALIDATION_MODES = {"", DISPLAY_VALIDATION_MODE}
DISPLAY_FOCUS_VALUES = {"subject", "source_text", "mixed"}
FINAL_VISUAL_REVIEW_MODE = "player-check"
SUPPORTED_FINAL_VISUAL_REVIEW_MODES = {"", FINAL_VISUAL_REVIEW_MODE}
PERSON_VISUAL_MODE = "stylize-or-remove"
SUPPORTED_PERSON_VISUAL_MODES = {"", PERSON_VISUAL_MODE}
PUBLIC_FIGURE_STYLE_MODE = "obvious-editorial-eye-band"
SUPPORTED_PUBLIC_FIGURE_STYLE_MODES = {"", PUBLIC_FIGURE_STYLE_MODE}
PERSON_MOTION_MODE = "subtle-deterministic"
SUPPORTED_PERSON_MOTION_MODES = {"", PERSON_MOTION_MODE}
YOUTUBE_UPLOAD_MODE = "copy-handoff"
SUPPORTED_YOUTUBE_UPLOAD_MODES = {"", YOUTUBE_UPLOAD_MODE}
YOUTUBE_CATEGORIES = {
    "people_and_blogs",
    "news_and_politics",
    "entertainment",
    "sports",
}
PORTRAIT_STYLE_STRENGTH = "obvious-editorial"
PORTRAIT_EYE_MOTIF = "editorial-ruler-eye-band"
NARRATION_SILENCE_THRESHOLD_DB = -40.0
NARRATION_SILENCE_MIN_SECONDS = 0.08
NARRATION_PAUSE_MEASUREMENT_TOLERANCE_SECONDS = 0.04
PEOPLE_TREATMENTS = {
    "none_visible",
    "editorial_animation",
    "cropped_out",
    "non_identifying",
}
EVIDENCE_ROLES = {
    "unreviewed",
    "incident_evidence",
    "official_evidence",
    "source_capture",
    "source_photo",
    "context",
    "editorial_animation",
    "non_identifying_fallback",
}
VISUAL_REQUIREMENTS = {
    "direct_incident",
    "direct_subject",
    "contextual",
    "symbolic_allowed",
}
REQUIREMENT_EVIDENCE_ROLES = {
    "direct_incident": {"incident_evidence", "official_evidence", "source_capture"},
    "direct_subject": {"editorial_animation", "non_identifying_fallback"},
    "contextual": {
        "incident_evidence",
        "official_evidence",
        "source_capture",
        "context",
        "editorial_animation",
        "non_identifying_fallback",
    },
    "symbolic_allowed": EVIDENCE_ROLES - {"unreviewed", "source_photo"},
}
PORTRAIT_STYLE = "editorial-animation"
PRIVATE_PERSON_CLASSES = {"private_person", "minor", "victim"}
QUALITY_REVIEW_MIN_LONG_SIDE = 720
QUALITY_REVIEW_MIN_PIXELS = 250_000
GENERAL_FOREGROUND_MIN_WIDTH_RATIO = 0.55
GENERAL_FOREGROUND_MIN_HEIGHT_RATIO = 0.28
GENERAL_FOREGROUND_MIN_AREA_RATIO = 0.22
TEXT_FOREGROUND_MIN_HEIGHT_RATIO = 0.35
TEXT_FOREGROUND_MIN_AREA_RATIO = 0.30
DEFAULT_NORMALIZATION_MODE = "default"
COMMUNITY_CAPTURE_NORMALIZATION_MODE = "community-capture-safe"
COMMUNITY_CAPTURE_MAX_WIDTH = 1000
COMMUNITY_CAPTURE_MAX_HEIGHT = 1056
COMMUNITY_HOST_SUFFIXES = {
    "clien.net",
    "dcinside.com",
    "etoland.co.kr",
    "fmkorea.com",
    "inven.co.kr",
    "instiz.net",
    "ppomppu.co.kr",
    "ruliweb.com",
    "slrclub.com",
    "theqoo.net",
    "todayhumor.co.kr",
}
CAPCUT_CLONE_REUSE_POLICY = "reuse-existing"
LEGACY_SCENE_MAX_SECONDS = 4.0
HOLD_SCENE_MAX_SECONDS = 7.0
CAPTION_TARGET_MIN_SECONDS = 1.3
CAPTION_TARGET_MAX_SECONDS = 3.2
CAPTION_HARD_MAX_SECONDS = 4.5
HUMANIZED_CAPTION_HARD_MAX_SECONDS = 6.0
CAPTION_ONSET_POLICY = "strong_speech"
CAPTION_FRAME_RATE = 30.0
AUDIO_DURATION_TOLERANCE_SECONDS = 0.15
CANVAS_WIDTH = 1080
CANVAS_HEIGHT = 1920
DEFAULT_CAPCUT_ROOT = (
    Path.home() / "Movies/CapCut/User Data/Projects/com.lveditor.draft"
)
DEFAULT_BASE_DRAFT = DEFAULT_CAPCUT_ROOT / "news2shorts"
DEFAULT_PROJECTS_ROOT = Path.cwd() / "projects/cc-helper"
MAX_HTML_BYTES = 8 * 1024 * 1024
MAX_IMAGE_BYTES = 30 * 1024 * 1024
MAX_VIDEO_BYTES = 200 * 1024 * 1024
USER_AGENT = "cc-helper/0.1.2 (+local editorial draft)"
VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".webm"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
IMAGE_MIME_EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}
VIDEO_MIME_EXTENSIONS = {
    "video/mp4": ".mp4",
    "video/quicktime": ".mov",
    "video/webm": ".webm",
}
ASSET_PENALTIES = (
    "advert",
    "banner",
    "emoji",
    "favicon",
    "icon",
    "logo",
    "profile",
    "sprite",
    "tracking",
)


class CCHelperError(RuntimeError):
    pass


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CCHelperError(f"파일을 찾을 수 없습니다: {path}") from exc
    except json.JSONDecodeError as exc:
        raise CCHelperError(f"JSON 형식이 올바르지 않습니다: {path}: {exc}") from exc


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.cc-helper.tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def is_community_source_url(value: str) -> bool:
    hostname = (parse.urlsplit(value).hostname or "").lower().rstrip(".")
    return any(
        hostname == suffix or hostname.endswith(f".{suffix}")
        for suffix in COMMUNITY_HOST_SUFFIXES
    )


def narration_contract_sha256(storyboard: dict[str, Any]) -> str:
    beats = storyboard.get("beats") if isinstance(storyboard.get("beats"), list) else []
    payload = [
        {
            "id": str(beat.get("id") or ""),
            "narration": str(beat.get("narration") or "").strip(),
        }
        for beat in beats
        if isinstance(beat, dict)
    ]
    return sha256_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    )


def tree_hash(root: Path) -> str:
    digest = hashlib.sha256()
    if not root.is_dir():
        raise CCHelperError(f"폴더를 찾을 수 없습니다: {root}")
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    return digest.hexdigest()


def project_path(project_dir: Path, relative: str, *, must_exist: bool = True) -> Path:
    if not relative:
        raise CCHelperError("빈 프로젝트 파일 경로는 사용할 수 없습니다.")
    project_root = project_dir.resolve()
    candidate = (project_dir / relative).resolve()
    try:
        candidate.relative_to(project_root)
    except ValueError as exc:
        raise CCHelperError(f"프로젝트 밖의 파일은 사용할 수 없습니다: {relative}") from exc
    if must_exist and not candidate.is_file():
        raise CCHelperError(f"프로젝트 파일을 찾을 수 없습니다: {relative}")
    return candidate


def relative_to_project(project_dir: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(project_dir.resolve()).as_posix()
    except ValueError as exc:
        raise CCHelperError(f"프로젝트 밖의 파일은 기록할 수 없습니다: {path}") from exc


def resolve_capcut_material_path(value: str, draft_dir: Path) -> Path:
    match = re.fullmatch(r"##_draftpath_placeholder_[^/]+_##/(.+)", value)
    if not match:
        return Path(value)
    candidate = (draft_dir / match.group(1)).resolve()
    try:
        candidate.relative_to(draft_dir.resolve())
    except ValueError:
        return Path(value)
    return candidate


def uses_formal_narration_ending(value: str) -> bool:
    return bool(
        re.search(
            r"(?:합니다|입니다|됩니다|랍니다|습니다|합니까|입니까|됩니까)(?:[.!?…]+|$)",
            value,
        )
    )


def narration_ending_family(value: object) -> str:
    tokens = normalized_word_tokens(value)
    if not tokens:
        return ""
    last = tokens[-1]
    if last.endswith(("는데", "인데")):
        return "de"
    if last == "함" or last.endswith(("다고함", "라고함")):
        return "ham"
    return ""


def validate_narration_flow(storyboard: dict[str, Any], beats: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    mode = str(storyboard.get("narration_flow_mode") or "").strip()
    if mode not in SUPPORTED_NARRATION_FLOW_MODES:
        return [f"지원하지 않는 narration_flow_mode입니다: {mode}"]
    if mode != NARRATION_FLOW_MODE or not beats:
        return errors

    ranks = {role: index for index, role in enumerate(NARRATION_FLOW_ROLES)}
    roles: list[str] = []
    for beat in beats:
        beat_id = str(beat.get("id") or "?")
        role = str(beat.get("flow_role") or "").strip()
        roles.append(role)
        if role not in ranks:
            errors.append(
                f"{beat_id} flow_role이 필요합니다: {list(NARRATION_FLOW_ROLES)}"
            )
    if any(role not in ranks for role in roles):
        return errors
    if roles[0] != "hook":
        errors.append("conversational-chain의 첫 beat flow_role은 hook이어야 합니다.")
    if roles[-1] not in {"resolution", "aftermath"}:
        errors.append("conversational-chain의 마지막 beat는 resolution 또는 aftermath여야 합니다.")
    for required in ("trigger", "resolution"):
        if required not in roles:
            errors.append(f"conversational-chain에는 {required} flow_role이 필요합니다.")
    for left, right in zip(roles, roles[1:]):
        if ranks[right] < ranks[left]:
            errors.append(f"대화형 내레이션 흐름이 역행합니다: {left} -> {right}")

    endings = [narration_ending_family(beat.get("narration")) for beat in beats]
    for index, (left, right) in enumerate(zip(endings, endings[1:]), start=1):
        if left == right == "de":
            errors.append(
                f"인접 beat-{index:02d}/beat-{index + 1:02d}에 ~데/~는데 종결을 연속 사용할 수 없습니다."
            )
    if len(endings) >= 2 and endings[-2:] == ["ham", "ham"]:
        errors.append("마지막 두 beat에 ~함 종결을 연속 사용할 수 없습니다.")
    return errors


def normalize_caption_match(value: object) -> str:
    normalized = unicodedata.normalize("NFKC", str(value or "")).casefold()
    return "".join(character for character in normalized if character.isalnum())


def normalized_word_tokens(value: object) -> list[str]:
    normalized = unicodedata.normalize("NFKC", str(value or "")).casefold()
    return [
        token
        for raw in re.findall(r"[^\W_]+", normalized, flags=re.UNICODE)
        if (token := normalize_caption_match(raw))
    ]


def caption_anchor_word_index(value: object, anchor: object) -> int | None:
    normalized_anchor = normalize_caption_match(anchor)
    if not normalized_anchor:
        return None
    tokens = normalized_word_tokens(value)
    for index in range(len(tokens)):
        if "".join(tokens[index:]).startswith(normalized_anchor):
            return index
    return None


def wav_duration_seconds(path: Path) -> float:
    try:
        with wave.open(str(path), "rb") as opened:
            return opened.getnframes() / float(opened.getframerate())
    except (wave.Error, OSError, ZeroDivisionError) as exc:
        raise CCHelperError(f"WAV 음원 정보를 읽을 수 없습니다: {path}") from exc


def copy_values_preserving_ids(target: dict[str, Any], source: dict[str, Any]) -> None:
    for key in list(target):
        if key != "id" and key not in source:
            target.pop(key, None)
    for key, value in source.items():
        if key == "id":
            continue
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            copy_values_preserving_ids(target[key], value)
        else:
            target[key] = copy.deepcopy(value)


def copy_visual_values(target: dict[str, Any], source: dict[str, Any]) -> None:
    for key in ("clip", "crop", "uniform_scale"):
        if key not in source:
            target.pop(key, None)
            continue
        source_value = source.get(key)
        if isinstance(source_value, dict):
            target_value = target.get(key)
            if not isinstance(target_value, dict):
                target_value = {}
                target[key] = target_value
            copy_values_preserving_ids(target_value, source_value)
        else:
            target[key] = copy.deepcopy(source_value)
    for key in ("crop_ratio", "crop_scale", "common_keyframes"):
        if key in source:
            target[key] = copy.deepcopy(source[key])
        else:
            target.pop(key, None)


def visual_values(source: dict[str, Any]) -> dict[str, Any]:
    return {
        key: copy.deepcopy(source.get(key))
        for key in ("clip", "crop", "crop_ratio", "crop_scale", "uniform_scale", "common_keyframes")
        if key in source
    }


def static_visual_value_snapshot(container: dict[str, Any]) -> str:
    payload = visual_values(container)
    payload.pop("common_keyframes", None)
    clip = payload.get("clip")
    if isinstance(clip, dict):
        clip.pop("scale", None)
        clip.pop("transform", None)
    return visual_value_snapshot(payload)


def stable_motion_uuid(*parts: object) -> str:
    value = ":".join(str(part) for part in parts)
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"cc-helper-motion:{value}")).upper()


def interpolate_motion(start: float, end: float, progress: float) -> float:
    return start + (end - start) * progress


def attach_person_motion_plans(
    scene_mappings: list[dict[str, Any]],
    storyboard: dict[str, Any],
    manifest: dict[str, Any],
) -> None:
    if storyboard.get("person_motion_mode") != PERSON_MOTION_MODE:
        return
    assets = {str(item.get("id") or ""): item for item in manifest.get("assets", [])}
    runs: list[list[dict[str, Any]]] = []
    for item in scene_mappings:
        if runs and runs[-1][0].get("beat_id") == item.get("beat_id"):
            runs[-1].append(item)
        else:
            runs.append([item])
    patterns = ("zoom_in", "zoom_out", "pan_lr", "zoom_in_pan", "pan_rl")
    previous_pattern = ""
    for run in runs:
        leader = run[0]
        asset = assets.get(str(leader.get("asset_id") or "")) or {}
        if asset.get("evidence_role") != "editorial_animation":
            continue
        digest = hashlib.sha256(
            f"{leader.get('asset_id')}:{leader.get('beat_id')}".encode("utf-8")
        ).digest()
        pattern_index = int.from_bytes(digest[:2], "big") % len(patterns)
        pattern = patterns[pattern_index]
        if pattern == previous_pattern:
            pattern = patterns[(pattern_index + 1) % len(patterns)]
        previous_pattern = pattern
        template_visual = leader.get("template_segment_visual") or {}
        clip = template_visual.get("clip") if isinstance(template_visual, dict) else {}
        scale = clip.get("scale") if isinstance(clip, dict) else {}
        transform = clip.get("transform") if isinstance(clip, dict) else {}
        base_scale = float((scale or {}).get("x") or 1.0)
        base_x = float((transform or {}).get("x") or 0.0)
        base_y = float((transform or {}).get("y") or 0.0)
        if pattern == "zoom_in":
            start_values = (base_scale, base_x, base_y)
            end_values = (base_scale * 1.04, base_x, base_y)
        elif pattern == "zoom_out":
            start_values = (base_scale * 1.04, base_x, base_y)
            end_values = (base_scale, base_x, base_y)
        elif pattern == "pan_lr":
            start_values = (base_scale * 1.04, base_x - 0.015, base_y)
            end_values = (base_scale * 1.04, base_x + 0.015, base_y)
        elif pattern == "pan_rl":
            start_values = (base_scale * 1.04, base_x + 0.015, base_y)
            end_values = (base_scale * 1.04, base_x - 0.015, base_y)
        else:
            start_values = (base_scale, base_x - 0.005, base_y)
            end_values = (base_scale * 1.035, base_x + 0.01, base_y)
        total_duration = sum(int(item.get("duration_us") or 0) for item in run)
        elapsed = 0
        for item in run:
            duration = int(item.get("duration_us") or 0)
            start_progress = elapsed / total_duration if total_duration else 0.0
            elapsed += duration
            end_progress = elapsed / total_duration if total_duration else 1.0
            item["motion_plan"] = {
                "mode": PERSON_MOTION_MODE,
                "pattern": pattern,
                "beat_id": item.get("beat_id"),
                "start_scale": interpolate_motion(start_values[0], end_values[0], start_progress),
                "end_scale": interpolate_motion(start_values[0], end_values[0], end_progress),
                "start_x": interpolate_motion(start_values[1], end_values[1], start_progress),
                "end_x": interpolate_motion(start_values[1], end_values[1], end_progress),
                "start_y": interpolate_motion(start_values[2], end_values[2], start_progress),
                "end_y": interpolate_motion(start_values[2], end_values[2], end_progress),
                "duration_us": duration,
                "end_offset_us": max(0, duration - int(1_000_000 / CAPTION_FRAME_RATE)),
            }


def root_motion_keyframes(scene_id: str, plan: dict[str, Any]) -> list[dict[str, Any]]:
    end_offset = int(plan.get("end_offset_us") or 0)
    properties = (
        ("KFTypePositionX", [float(plan["start_x"]), float(plan["end_x"])]),
        ("KFTypePositionY", [float(plan["start_y"]), float(plan["end_y"])]),
        ("KFTypeScaleX", [float(plan["start_scale"]), float(plan["end_scale"])]),
    )
    groups = []
    for property_type, values in properties:
        points = []
        for index, (time_offset, value) in enumerate(((0, values[0]), (end_offset, values[1]))):
            points.append(
                {
                    "id": stable_motion_uuid(scene_id, property_type, index),
                    "curveType": "Line",
                    "time_offset": time_offset,
                    "left_control": {"x": 0.0, "y": 0.0},
                    "right_control": {"x": 0.0, "y": 0.0},
                    "values": [value],
                    "string_value": "",
                    "graphID": "",
                }
            )
        groups.append(
            {
                "id": stable_motion_uuid(scene_id, property_type),
                "material_id": "",
                "property_type": property_type,
                "keyframe_list": points,
            }
        )
    groups.append(
        {
            "id": stable_motion_uuid(scene_id, "KFTypeRotation"),
            "material_id": "",
            "property_type": "KFTypeRotation",
            "keyframe_list": [
                {
                    "id": stable_motion_uuid(scene_id, "KFTypeRotation", 0),
                    "curveType": "Line",
                    "time_offset": 0,
                    "left_control": {"x": 0.0, "y": 0.0},
                    "right_control": {"x": 0.0, "y": 0.0},
                    "values": [0.0],
                    "string_value": "",
                    "graphID": "",
                }
            ],
        }
    )
    return groups


def mini_motion_keyframes(scene_id: str, plan: dict[str, Any]) -> list[dict[str, Any]]:
    result = []
    for group in root_motion_keyframes(scene_id, plan):
        result.append(
            {
                "id": group["id"],
                "material_id": "",
                "property_type": group["property_type"],
                "keyframe_list": [
                    {
                        "id": point["id"],
                        "curveType": 0,
                        "graph": None,
                        "time_offset": point["time_offset"],
                        "values": point["values"],
                        "string_value": "",
                    }
                    for point in group["keyframe_list"]
                ],
            }
        )
    return result


def apply_motion_plan(segment: dict[str, Any], scene_id: str, plan: dict[str, Any], *, mini: bool) -> None:
    clip = segment.get("clip")
    if not isinstance(clip, dict):
        raise CCHelperError(f"{scene_id} motion segment clip이 없습니다.")
    scale = clip.get("scale")
    transform = clip.get("transform")
    if not isinstance(scale, dict) or not isinstance(transform, dict):
        raise CCHelperError(f"{scene_id} motion scale/transform이 없습니다.")
    scale["x"] = float(plan["end_scale"])
    scale["y"] = float(plan["end_scale"])
    transform["x"] = float(plan["end_x"])
    transform["y"] = float(plan["end_y"])
    segment["common_keyframes"] = (
        mini_motion_keyframes(scene_id, plan) if mini else root_motion_keyframes(scene_id, plan)
    )


def reset_full_frame_geometry(segment: dict[str, Any]) -> None:
    clip = segment.get("clip")
    if isinstance(clip, dict):
        scale = clip.get("scale")
        if isinstance(scale, dict):
            scale["x"] = 1.0
            scale["y"] = 1.0
        transform = clip.get("transform")
        if isinstance(transform, dict):
            transform["x"] = 0.0
            transform["y"] = 0.0
        flip = clip.get("flip")
        if isinstance(flip, dict):
            flip["horizontal"] = False
            flip["vertical"] = False
        clip["rotation"] = 0.0
        if "alpha" in clip:
            clip["alpha"] = 1.0
    if "alpha" in segment:
        segment["alpha"] = 1.0
    crop = segment.get("crop")
    if isinstance(crop, dict):
        crop.update(
            {
                "upper_left_x": 0.0,
                "upper_left_y": 0.0,
                "upper_right_x": 1.0,
                "upper_right_y": 0.0,
                "lower_left_x": 0.0,
                "lower_left_y": 1.0,
                "lower_right_x": 1.0,
                "lower_right_y": 1.0,
            }
        )
    if "crop_ratio" in segment:
        segment["crop_ratio"] = 0
    if "crop_scale" in segment:
        segment["crop_scale"] = 1.0
    uniform_scale = segment.get("uniform_scale")
    if isinstance(uniform_scale, dict):
        uniform_scale["on"] = True
        uniform_scale["value"] = 1.0
    if "common_keyframes" in segment:
        segment["common_keyframes"] = []


def is_full_frame_geometry(segment: dict[str, Any]) -> bool:
    normalized = copy.deepcopy(segment)
    reset_full_frame_geometry(normalized)
    return visual_value_snapshot(segment) == visual_value_snapshot(normalized)


def audio_snapshot(draft: dict[str, Any]) -> str:
    materials = draft.get("materials") or {}
    payload = {
        "audios": materials.get("audios", []),
        "audio_tracks": [
            track for track in draft.get("tracks", []) if track.get("type") == "audio"
        ],
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def active_draft_mirror_paths(destination: Path) -> list[Path]:
    candidates = [destination / "draft_info.json", destination / "template-2.tmp"]
    for timeline in sorted((destination / "Timelines").glob("*")):
        candidates.extend([timeline / "draft_info.json", timeline / "template-2.tmp"])
    return [path for path in candidates if path.is_file()]


def active_template_paths(destination: Path) -> list[Path]:
    candidates = [destination / "template.json"]
    candidates.extend(sorted((destination / "Timelines").glob("*/template.json")))
    return [path for path in candidates if path.is_file()]


def active_mini_draft_paths(destination: Path) -> list[Path]:
    return sorted((destination / "Timelines").glob("*/attachment/patch/mini_draft.json"))


def active_cover_paths(destination: Path) -> list[Path]:
    candidates = [destination / "draft_cover.jpg"]
    candidates.extend(sorted(destination.glob("Timelines/*/draft_cover.jpg")))
    return [path for path in candidates if path.is_file()]


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii").lower()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text).strip("-")
    if slug:
        return slug[:48]
    return f"issue-{hashlib.sha256(value.encode('utf-8')).hexdigest()[:8]}"


def capcut_running() -> bool:
    if sys.platform != "darwin":
        return False
    try:
        result = subprocess.run(
            ["pgrep", "-f", "/CapCut.app/"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except OSError:
        return False
    return result.returncode == 0


def executable_available(name: str) -> bool:
    return shutil.which(name) is not None


def pillow_available() -> bool:
    try:
        import PIL  # noqa: F401
    except ImportError:
        return False
    return True


def verified_ssl_context() -> ssl.SSLContext:
    certificate = Path("/etc/ssl/cert.pem")
    if certificate.is_file():
        return ssl.create_default_context(cafile=str(certificate))
    return ssl.create_default_context()


def print_json(payload: Any) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def find_template_parts(draft: dict[str, Any]) -> dict[str, Any]:
    tracks = draft.get("tracks")
    if not isinstance(tracks, list):
        raise CCHelperError("캡컷 draft_info.json에 tracks 배열이 없습니다.")

    video_tracks = [
        (index, track)
        for index, track in enumerate(tracks)
        if track.get("type") == "video" and len(track.get("segments", [])) == SCENE_COUNT
    ]
    one_text_tracks = [
        (index, track)
        for index, track in enumerate(tracks)
        if track.get("type") == "text" and len(track.get("segments", [])) == 1
    ]
    caption_tracks = [
        (index, track)
        for index, track in enumerate(tracks)
        if track.get("type") == "text" and len(track.get("segments", [])) == SCENE_COUNT - 1
    ]
    if len(video_tracks) != 1:
        raise CCHelperError("15개 장면이 있는 영상 트랙을 하나만 찾을 수 있어야 합니다.")
    if len(one_text_tracks) != 2:
        raise CCHelperError("상단 제목용 단일 텍스트 트랙이 정확히 2개여야 합니다.")
    if len(caption_tracks) != 1:
        raise CCHelperError("14개 하단 자막 트랙을 하나만 찾을 수 있어야 합니다.")

    materials = draft.get("materials", {})
    videos = {
        item.get("id"): item
        for item in materials.get("videos", [])
        if isinstance(item, dict) and item.get("id")
    }
    texts = {
        item.get("id"): item
        for item in materials.get("texts", [])
        if isinstance(item, dict) and item.get("id")
    }
    scene_segments = video_tracks[0][1].get("segments", [])
    if any(segment.get("material_id") not in videos for segment in scene_segments):
        raise CCHelperError("장면 트랙이 존재하지 않는 영상 소재를 참조합니다.")
    text_segments = [track.get("segments", [])[0] for _, track in one_text_tracks]
    if any(segment.get("material_id") not in texts for segment in text_segments):
        raise CCHelperError("상단 제목 트랙이 존재하지 않는 텍스트 소재를 참조합니다.")
    caption_segments = caption_tracks[0][1].get("segments", [])
    if any(segment.get("material_id") not in texts for segment in caption_segments):
        raise CCHelperError("하단 자막 트랙이 존재하지 않는 텍스트 소재를 참조합니다.")

    canvas = draft.get("canvas_config") or {}
    if (canvas.get("width"), canvas.get("height")) != (CANVAS_WIDTH, CANVAS_HEIGHT):
        raise CCHelperError("템플릿 캔버스가 1080x1920이 아닙니다.")
    if float(draft.get("fps") or 0) != 30.0:
        raise CCHelperError("템플릿 프레임 속도가 30fps가 아닙니다.")

    return {
        "scene_track_index": video_tracks[0][0],
        "scene_segments": scene_segments,
        "title_track_indexes": [item[0] for item in one_text_tracks],
        "title_segments": text_segments,
        "caption_track_index": caption_tracks[0][0],
        "caption_segments": caption_segments,
        "videos": videos,
        "texts": texts,
    }


def inspect_template(base_draft: Path) -> dict[str, Any]:
    draft_path = base_draft / "draft_info.json"
    result: dict[str, Any] = {
        "path": str(base_draft),
        "exists": base_draft.is_dir(),
        "valid": False,
        "errors": [],
    }
    if not base_draft.is_dir():
        result["errors"].append("템플릿 폴더가 없습니다.")
        return result
    try:
        draft = read_json(draft_path)
        parts = find_template_parts(draft)
    except CCHelperError as exc:
        result["errors"].append(str(exc))
        return result
    result.update(
        {
            "valid": True,
            "duration_seconds": round(float(draft.get("duration", 0)) / 1_000_000, 3),
            "fps": draft.get("fps"),
            "canvas": draft.get("canvas_config"),
            "track_count": len(draft.get("tracks", [])),
            "scene_count": len(parts["scene_segments"]),
            "caption_count": len(parts["caption_segments"]),
            "title_track_count": len(parts["title_segments"]),
            "audio_material_count": len(draft.get("materials", {}).get("audios", [])),
        }
    )
    return result


def generate_sfx(path: Path, *, frequency: float, duration: float, noise: float = 0.0) -> None:
    sample_rate = 44_100
    count = int(sample_rate * duration)
    rng = random.Random(f"{path.name}:{frequency}:{duration}:{noise}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(sample_rate)
        frames = bytearray()
        for index in range(count):
            progress = index / max(1, count - 1)
            envelope = math.sin(math.pi * progress) ** 1.5
            tone = math.sin(2 * math.pi * frequency * index / sample_rate)
            grit = rng.uniform(-1.0, 1.0) * noise
            sample = max(-1.0, min(1.0, (tone * (1.0 - noise) + grit) * envelope))
            frames.extend(struct.pack("<h", int(sample * 14_000)))
        output.writeframes(bytes(frames))


def create_sfx_presets(project_dir: Path) -> None:
    presets = {
        "hook-impact": (120.0, 0.28, 0.22),
        "pop": (620.0, 0.12, 0.05),
        "click": (980.0, 0.08, 0.02),
        "tick": (780.0, 0.10, 0.04),
        "turn": (240.0, 0.24, 0.12),
        "reveal": (430.0, 0.32, 0.06),
        "ending": (180.0, 0.36, 0.10),
    }
    for name, (frequency, duration, noise) in presets.items():
        generate_sfx(
            project_dir / "assets" / "sfx" / f"{name}.wav",
            frequency=frequency,
            duration=duration,
            noise=noise,
        )


def default_scene_duration(index: int) -> float:
    if index == 1:
        return 2.0
    if index in {2, 3}:
        return 2.5
    return 3.0


def init_project(args: argparse.Namespace) -> None:
    title = args.title.strip()
    if not title:
        raise CCHelperError("--title은 비워둘 수 없습니다.")
    timestamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    slug = slugify(args.slug or title)
    if args.project_dir:
        project_dir = Path(args.project_dir).expanduser().resolve()
    else:
        projects_root = Path(args.projects_root).expanduser().resolve()
        project_dir = projects_root / dt.date.today().isoformat() / f"{timestamp}-{slug}"
    if project_dir.exists():
        raise CCHelperError(f"프로젝트 폴더가 이미 존재합니다: {project_dir}")

    for relative in (
        "assets/source",
        "assets/normalized",
        "assets/videos",
        "assets/generated",
        "assets/sfx",
        "assets/audio",
        "handoff",
    ):
        (project_dir / relative).mkdir(parents=True, exist_ok=True)
    create_sfx_presets(project_dir)

    destination_name = f"cc-{timestamp}-{slug}"
    project = {
        "version": VERSION,
        "status": "local_review_only",
        "publish_blocked": True,
        "youtube_upload_mode": YOUTUBE_UPLOAD_MODE,
        "title": title,
        "slug": slug,
        "created_at": now_iso(),
        "candidate_id": args.candidate_id,
        "capcut": {
            "destination_name": destination_name,
            "draft_name": f"[CC] {title}",
            "reuse_policy": CAPCUT_CLONE_REUSE_POLICY,
            "active_destination_name": "",
        },
        "bgm": {"mode": "none", "path": ""},
        "youtube_upload": {
            "status": "draft",
            "title": "",
            "description": "",
            "hashtags": [],
            "tags": [],
            "pinned_comment": "",
            "category": "people_and_blogs",
            "language": "ko",
            "audience": "review_required",
            "altered_content": False,
            "altered_content_reason": "",
            "recommended_visibility": "private",
            "thumbnail": {"white": "", "yellow": ""},
            "source_ids": [],
        },
    }
    if args.bgm_file:
        bgm_source = Path(args.bgm_file).expanduser().resolve()
        if not bgm_source.is_file():
            raise CCHelperError(f"BGM 파일을 찾을 수 없습니다: {bgm_source}")
        bgm_target = project_dir / "assets" / "audio" / f"bgm{bgm_source.suffix.lower()}"
        shutil.copy2(bgm_source, bgm_target)
        project["bgm"] = {
            "mode": "local_file",
            "path": relative_to_project(project_dir, bgm_target),
        }
    write_json(project_dir / "project.json", project)

    sources = []
    for index, url in enumerate(args.source_url or [], start=1):
        sources.append(
            {
                "id": f"source-{index:02d}",
                "url": url,
                "publisher": "",
                "title": "",
                "captured_at": "",
            }
        )
    research = {
        "version": VERSION,
        "window_hours": 48,
        "max_candidates": 3,
        "candidates": [
            {
                "id": args.candidate_id,
                "title": title,
                "category": args.category,
                "who": "",
                "what_happened": "",
                "why_people_react": "",
                "surprise_or_tension": "",
                "visual_availability": "",
                "selected": True,
            }
        ],
        "selected_candidate_id": args.candidate_id,
        "sources": sources,
        "facts": [],
    }
    write_json(project_dir / "research.json", research)

    scenes = []
    roles = (
        ["hook"]
        + ["incident"] * 2
        + ["background"] * 4
        + ["core"] * 4
        + ["outcome"] * 4
    )
    for index in range(1, SCENE_COUNT + 1):
        scenes.append(
            {
                "id": f"scene-{index:02d}",
                "beat_id": "",
                "role": roles[index - 1],
                "duration": default_scene_duration(index),
                "narration": "",
                "caption": "",
                "caption_anchor": "",
                "fact_ids": [],
                "visual_requirement": "",
                "asset_id": "",
                "source_label": "",
                "sfx": "",
            }
        )
    storyboard = {
        "version": VERSION,
        "pacing_mode": NARRATION_HOLD_MODE,
        "narration_flow_mode": NARRATION_FLOW_MODE,
        "narration_performance_mode": NARRATION_PERFORMANCE_MODE,
        "caption_sync_mode": CAPTION_SYNC_MODE,
        "visual_validation_mode": EVIDENCE_FIRST_MODE,
        "display_validation_mode": DISPLAY_VALIDATION_MODE,
        "final_visual_review_mode": FINAL_VISUAL_REVIEW_MODE,
        "person_visual_mode": PERSON_VISUAL_MODE,
        "public_figure_style_mode": PUBLIC_FIGURE_STYLE_MODE,
        "person_motion_mode": PERSON_MOTION_MODE,
        "message": "",
        "title": {"white": "", "yellow": ""},
        "beats": [],
        "scenes": scenes,
    }
    write_json(project_dir / "storyboard.json", storyboard)
    write_json(
        project_dir / "asset-manifest.json",
        {"version": VERSION, "status": "local_review_only", "searches": [], "assets": []},
    )
    write_json(
        project_dir / "capcut-map.json",
        {"version": VERSION, "status": "not_prepared", "project_dir": str(project_dir)},
    )
    print_json({"project_dir": str(project_dir), "status": "initialized"})


class PageAssetParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.candidates: list[dict[str, Any]] = []
        self.figure_depth = 0
        self._json_ld = False
        self._json_buffer: list[str] = []

    @staticmethod
    def _attrs(attrs: list[tuple[str, str | None]]) -> dict[str, str]:
        return {key.lower(): value or "" for key, value in attrs}

    def add(
        self,
        url: str,
        kind: str,
        *,
        alt: str = "",
        width: str = "",
        height: str = "",
    ) -> None:
        if not url or url.startswith(("data:", "blob:", "javascript:")):
            return
        self.candidates.append(
            {
                "url": url.strip(),
                "kind": kind,
                "alt": alt.strip(),
                "width": integer_or_zero(width),
                "height": integer_or_zero(height),
            }
        )

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = self._attrs(attrs)
        if tag == "figure":
            self.figure_depth += 1
        if tag == "meta":
            key = (values.get("property") or values.get("name") or "").lower()
            content = values.get("content", "")
            if key in {"og:image", "og:image:url", "og:image:secure_url"}:
                self.add(content, "og-image")
            elif key in {"twitter:image", "twitter:image:src"}:
                self.add(content, "twitter-image")
        elif tag == "link":
            rel = values.get("rel", "").lower()
            if "image_src" in rel or "preload" in rel and values.get("as") == "image":
                self.add(values.get("href", ""), "link-image")
        elif tag == "img":
            kind = "figure-image" if self.figure_depth else "body-image"
            for key in ("data-original", "data-lazy-src", "data-src", "src"):
                if values.get(key):
                    self.add(
                        values[key],
                        kind,
                        alt=values.get("alt", ""),
                        width=values.get("width", ""),
                        height=values.get("height", ""),
                    )
            srcset = values.get("data-srcset") or values.get("srcset")
            if srcset:
                selected = largest_srcset_url(srcset)
                self.add(
                    selected,
                    f"{kind}-srcset",
                    alt=values.get("alt", ""),
                    width=values.get("width", ""),
                    height=values.get("height", ""),
                )
        elif tag == "script" and "ld+json" in values.get("type", "").lower():
            self._json_ld = True
            self._json_buffer = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "figure" and self.figure_depth:
            self.figure_depth -= 1
        if tag == "script" and self._json_ld:
            self._json_ld = False
            raw = "".join(self._json_buffer).strip()
            if raw:
                try:
                    payload = json.loads(raw)
                except json.JSONDecodeError:
                    return
                for url in json_ld_images(payload):
                    self.add(url, "json-ld-image")

    def handle_data(self, data: str) -> None:
        if self._json_ld:
            self._json_buffer.append(data)


def integer_or_zero(value: Any) -> int:
    match = re.search(r"\d+", str(value or ""))
    return int(match.group(0)) if match else 0


def largest_srcset_url(srcset: str) -> str:
    choices = []
    for item in srcset.split(","):
        fields = item.strip().split()
        if not fields:
            continue
        score = integer_or_zero(fields[1]) if len(fields) > 1 else 0
        choices.append((score, fields[0]))
    return max(choices, default=(0, ""))[1]


def json_ld_images(payload: Any) -> Iterable[str]:
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key.lower() in {"image", "thumbnailurl", "contenturl"}:
                if isinstance(value, str):
                    yield value
                elif isinstance(value, dict):
                    for nested_key in ("url", "contentUrl"):
                        nested = value.get(nested_key)
                        if isinstance(nested, str):
                            yield nested
                elif isinstance(value, list):
                    for item in value:
                        yield from json_ld_images({"image": item})
            else:
                yield from json_ld_images(value)
    elif isinstance(payload, list):
        for item in payload:
            yield from json_ld_images(item)


def asset_score(candidate: dict[str, Any]) -> int:
    bases = {
        "og-image": 110,
        "twitter-image": 105,
        "json-ld-image": 100,
        "figure-image-srcset": 95,
        "figure-image": 90,
        "link-image": 80,
        "body-image-srcset": 75,
        "body-image": 65,
    }
    score = bases.get(candidate.get("kind"), 50)
    width = int(candidate.get("width") or 0)
    height = int(candidate.get("height") or 0)
    if width >= 1000 or height >= 1000:
        score += 15
    elif width and height and (width < 320 or height < 240):
        score -= 45
    searchable = f"{candidate.get('url', '')} {candidate.get('alt', '')}".lower()
    if any(token in searchable for token in ASSET_PENALTIES):
        score -= 70
    if parse.urlsplit(str(candidate.get("url", ""))).path.lower().endswith(".svg"):
        score -= 100
    return score


def ranked_page_assets(page_url: str, html: str) -> list[dict[str, Any]]:
    parser = PageAssetParser()
    parser.feed(html)
    deduped: dict[str, dict[str, Any]] = {}
    for item in parser.candidates:
        absolute = parse.urljoin(page_url, item["url"])
        clean, _fragment = parse.urldefrag(absolute)
        item = {**item, "url": clean}
        item["score"] = asset_score(item)
        previous = deduped.get(clean)
        if previous is None or item["score"] > previous["score"]:
            deduped[clean] = item
    return sorted(deduped.values(), key=lambda value: (-value["score"], value["url"]))


def fetch_bytes(url: str, *, referer: str = "", limit: int) -> tuple[bytes, str, str]:
    headers = {"User-Agent": USER_AGENT, "Accept": "*/*"}
    if referer:
        headers["Referer"] = referer
    req = request.Request(url, headers=headers)
    try:
        with request.urlopen(req, timeout=30, context=verified_ssl_context()) as response:
            content_type = response.headers.get_content_type().lower()
            content_length = integer_or_zero(response.headers.get("Content-Length"))
            if content_length and content_length > limit:
                raise CCHelperError(f"파일이 허용 크기를 초과합니다: {url}")
            data = response.read(limit + 1)
            if len(data) > limit:
                raise CCHelperError(f"파일이 허용 크기를 초과합니다: {url}")
            return data, content_type, response.geturl()
    except error.HTTPError as exc:
        raise CCHelperError(f"자료 요청 실패: HTTP {exc.code}: {url}") from exc
    except error.URLError as exc:
        raise CCHelperError(f"자료 연결 실패: {exc.reason}: {url}") from exc


def fetch_page(url: str) -> tuple[str, str]:
    data, content_type, final_url = fetch_bytes(url, limit=MAX_HTML_BYTES)
    if content_type not in {"text/html", "application/xhtml+xml", "text/plain"}:
        raise CCHelperError(f"HTML 페이지가 아닙니다({content_type}): {url}")
    for encoding in ("utf-8", "cp949", "euc-kr"):
        try:
            return data.decode(encoding), final_url
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace"), final_url


def extension_for(content_type: str, url: str) -> str:
    content_type = content_type.split(";", 1)[0].lower()
    if content_type in IMAGE_MIME_EXTENSIONS:
        return IMAGE_MIME_EXTENSIONS[content_type]
    if content_type in VIDEO_MIME_EXTENSIONS:
        return VIDEO_MIME_EXTENSIONS[content_type]
    suffix = Path(parse.urlsplit(url).path).suffix.lower()
    if suffix in IMAGE_EXTENSIONS | VIDEO_EXTENSIONS:
        return suffix
    guessed = mimetypes.guess_extension(content_type) if content_type else None
    return guessed or ".bin"


def image_normalization_layout(
    width: int,
    height: int,
    *,
    mode: str = DEFAULT_NORMALIZATION_MODE,
) -> dict[str, Any]:
    if width <= 0 or height <= 0:
        raise CCHelperError("이미지 크기는 1px 이상이어야 합니다.")
    if mode not in {DEFAULT_NORMALIZATION_MODE, COMMUNITY_CAPTURE_NORMALIZATION_MODE}:
        raise CCHelperError(f"지원하지 않는 이미지 정규화 모드입니다: {mode}")
    ratio = width / height
    if mode == COMMUNITY_CAPTURE_NORMALIZATION_MODE:
        scale = min(
            COMMUNITY_CAPTURE_MAX_WIDTH / width,
            COMMUNITY_CAPTURE_MAX_HEIGHT / height,
        )
        if width < 720 or height < 720:
            scale = min(scale, 1.5)
        foreground_width = max(1, int(width * scale))
        foreground_height = max(1, int(height * scale))
        foreground = {
            "x": (CANVAS_WIDTH - foreground_width) // 2,
            "y": (CANVAS_HEIGHT - foreground_height) // 2,
            "width": foreground_width,
            "height": foreground_height,
        }
        strategy = COMMUNITY_CAPTURE_NORMALIZATION_MODE
    elif 0.48 <= ratio <= 0.66 and width >= 720 and height >= 1280:
        foreground = {"x": 0, "y": 0, "width": CANVAS_WIDTH, "height": CANVAS_HEIGHT}
        strategy = "portrait_fill"
    else:
        scale = min(1000 / width, 1500 / height)
        if width < 720 or height < 720:
            scale = min(scale, 1.5)
        foreground_width = max(1, int(width * scale))
        foreground_height = max(1, int(height * scale))
        foreground = {
            "x": (CANVAS_WIDTH - foreground_width) // 2,
            "y": (CANVAS_HEIGHT - foreground_height) // 2,
            "width": foreground_width,
            "height": foreground_height,
        }
        strategy = "blur_fit"
    return {
        "mode": mode,
        "strategy": strategy,
        "foreground_box": foreground,
        "foreground_width_ratio": foreground["width"] / CANVAS_WIDTH,
        "foreground_height_ratio": foreground["height"] / CANVAS_HEIGHT,
        "foreground_area_ratio": (
            foreground["width"] * foreground["height"] / (CANVAS_WIDTH * CANVAS_HEIGHT)
        ),
    }


def normalize_image(
    source_path: Path,
    target_path: Path,
    *,
    mode: str = DEFAULT_NORMALIZATION_MODE,
) -> tuple[int, int]:
    try:
        from PIL import Image, ImageFilter, ImageOps
    except ImportError as exc:
        raise CCHelperError("이미지 정규화에는 Pillow가 필요합니다.") from exc

    try:
        with Image.open(source_path) as opened:
            source = ImageOps.exif_transpose(opened).convert("RGB")
    except Exception as exc:  # Pillow raises format-specific exceptions.
        raise CCHelperError(f"이미지 파일을 열 수 없습니다: {source_path}") from exc
    width, height = source.size
    if width < 240 or height < 180 or width * height < 120_000:
        raise CCHelperError(f"이미지가 너무 작습니다({width}x{height}): {source_path.name}")

    layout = image_normalization_layout(width, height, mode=mode)
    if layout["strategy"] == "portrait_fill":
        canvas = ImageOps.fit(
            source,
            (CANVAS_WIDTH, CANVAS_HEIGHT),
            method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.5),
        )
    else:
        canvas = ImageOps.fit(
            source,
            (CANVAS_WIDTH, CANVAS_HEIGHT),
            method=Image.Resampling.LANCZOS,
        ).filter(ImageFilter.GaussianBlur(radius=28))
        canvas = Image.blend(canvas, Image.new("RGB", canvas.size, "#101010"), 0.22)
        box = layout["foreground_box"]
        foreground_size = (box["width"], box["height"])
        foreground = source.resize(foreground_size, Image.Resampling.LANCZOS)
        canvas.paste(foreground, (box["x"], box["y"]))
    target_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(target_path, "PNG", optimize=True)
    return width, height


def parse_readable_panel(value: str) -> tuple[tuple[int, int, int, int], tuple[int, int, int, int]]:
    match = re.fullmatch(
        r"(\d+),(\d+),(\d+),(\d+):(\d+),(\d+),(\d+),(\d+)", value.strip()
    )
    if not match:
        raise CCHelperError(
            "--panel은 source_x,source_y,width,height:target_x,target_y,width,height 형식이어야 합니다."
        )
    numbers = [int(item) for item in match.groups()]
    source_box = tuple(numbers[:4])
    target_box = tuple(numbers[4:])
    if any(number < 0 for number in numbers) or any(number <= 0 for number in (*source_box[2:], *target_box[2:])):
        raise CCHelperError("--panel 좌표와 크기는 음수가 아니며 폭·높이는 1 이상이어야 합니다.")
    return source_box, target_box


def compose_readable_source(args: argparse.Namespace) -> None:
    try:
        from PIL import Image, ImageOps
    except ImportError as exc:
        raise CCHelperError("readable source 합성에는 Pillow가 필요합니다.") from exc
    source_path = Path(args.source_file).expanduser().resolve()
    output_path = Path(args.output_file).expanduser().resolve()
    if not source_path.is_file() or source_path.suffix.lower() not in IMAGE_EXTENSIONS:
        raise CCHelperError(f"readable source 원본 이미지를 찾을 수 없습니다: {source_path}")
    if output_path.suffix.lower() != ".png" or output_path == source_path:
        raise CCHelperError("readable source 출력은 원본과 다른 PNG 경로여야 합니다.")
    panels = [parse_readable_panel(value) for value in args.panel]
    if not panels:
        raise CCHelperError("readable source에는 하나 이상의 --panel이 필요합니다.")
    with Image.open(source_path) as opened:
        source = ImageOps.exif_transpose(opened).convert("RGB")
    canvas = Image.new("RGB", (1000, 720), "white")
    for source_box, target_box in panels:
        sx, sy, sw, sh = source_box
        tx, ty, tw, th = target_box
        if sx + sw > source.width or sy + sh > source.height:
            raise CCHelperError(f"readable source panel이 원본 범위를 벗어납니다: {source_box}")
        if tx + tw > canvas.width or ty + th > canvas.height:
            raise CCHelperError(f"readable source panel이 1000x720 출력을 벗어납니다: {target_box}")
        panel = source.crop((sx, sy, sx + sw, sy + sh)).resize(
            (tw, th), Image.Resampling.LANCZOS
        )
        canvas.paste(panel, (tx, ty))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path, "PNG", optimize=True)
    print_json(
        {
            "status": "composed",
            "source_path": str(source_path),
            "output_path": str(output_path),
            "sha256": sha256_file(output_path),
            "width": 1000,
            "height": 720,
            "panels": len(panels),
        }
    )


def extract_video_frame(video_path: Path, frame_path: Path) -> None:
    if not executable_available("ffmpeg"):
        raise CCHelperError("영상 대표 프레임 추출에는 ffmpeg가 필요합니다.")
    frame_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-ss",
        "0.5",
        "-i",
        str(video_path),
        "-frames:v",
        "1",
        str(frame_path),
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0 or not frame_path.is_file():
        raise CCHelperError(f"영상 대표 프레임 추출 실패: {result.stderr.strip()}")


def load_manifest(project_dir: Path) -> dict[str, Any]:
    manifest = read_json(project_dir / "asset-manifest.json")
    manifest.setdefault("searches", [])
    manifest.setdefault("assets", [])
    return manifest


def manifest_asset_by_sha(manifest: dict[str, Any], digest: str) -> dict[str, Any] | None:
    return next((item for item in manifest.get("assets", []) if item.get("sha256") == digest), None)


def ingest_local_asset(
    project_dir: Path,
    manifest: dict[str, Any],
    source_path: Path,
    *,
    source_page_url: str,
    asset_url: str,
    source_method: str,
    synthetic: bool,
    derived_from: str,
    person_class: str,
    relevance: str,
    visual_text: str,
    normalization_mode: str = DEFAULT_NORMALIZATION_MODE,
) -> dict[str, Any]:
    if not source_path.is_file():
        raise CCHelperError(f"에셋 파일을 찾을 수 없습니다: {source_path}")
    suffix = source_path.suffix.lower()
    if suffix not in IMAGE_EXTENSIONS | VIDEO_EXTENSIONS:
        raise CCHelperError(f"지원하지 않는 에셋 형식입니다: {source_path.suffix}")
    digest = sha256_file(source_path)
    duplicate = manifest_asset_by_sha(manifest, digest)
    if duplicate:
        if (
            normalization_mode == COMMUNITY_CAPTURE_NORMALIZATION_MODE
            and suffix in IMAGE_EXTENSIONS
            and duplicate.get("normalization_mode") != normalization_mode
        ):
            normalized = project_path(
                project_dir, str(duplicate.get("normalized_path") or "")
            )
            width, height = normalize_image(
                source_path,
                normalized,
                mode=normalization_mode,
            )
            duplicate["width"] = width
            duplicate["height"] = height
            duplicate["normalization_mode"] = normalization_mode
            duplicate["normalization"] = {
                **image_normalization_layout(
                    width,
                    height,
                    mode=normalization_mode,
                ),
                "normalized_sha256": sha256_file(normalized),
            }
            review = duplicate.get("review")
            if isinstance(review, dict):
                review["quality"] = "review_required"
                review["preview_checked"] = False
                review["evidence_readable"] = False
                review["normalized_sha256"] = ""
        return duplicate

    asset_id = f"asset-{digest[:12]}"
    retrieved_at = now_iso()
    if suffix in VIDEO_EXTENSIONS:
        copied = project_dir / "assets" / "videos" / f"{asset_id}{suffix}"
        shutil.copy2(source_path, copied)
        raw_frame = project_dir / "assets" / "normalized" / f"{asset_id}-frame-source.png"
        normalized = project_dir / "assets" / "normalized" / f"{asset_id}.png"
        try:
            extract_video_frame(copied, raw_frame)
            width, height = normalize_image(
                raw_frame,
                normalized,
                mode=normalization_mode,
            )
        except Exception:
            copied.unlink(missing_ok=True)
            normalized.unlink(missing_ok=True)
            raise
        finally:
            raw_frame.unlink(missing_ok=True)
        media_type = "video"
        source_relative = relative_to_project(project_dir, copied)
    else:
        copied = project_dir / "assets" / ("generated" if synthetic else "source") / f"{asset_id}{suffix}"
        shutil.copy2(source_path, copied)
        normalized = project_dir / "assets" / "normalized" / f"{asset_id}.png"
        width, height = normalize_image(
            copied,
            normalized,
            mode=normalization_mode,
        )
        media_type = "illustration" if synthetic else "image"
        source_relative = relative_to_project(project_dir, copied)

    record = {
        "id": asset_id,
        "source_page_url": source_page_url,
        "asset_url": asset_url,
        "retrieved_at": retrieved_at,
        "sha256": digest,
        "width": width,
        "height": height,
        "media_type": media_type,
        "source_method": source_method,
        "normalization_mode": normalization_mode,
        "source_path": source_relative,
        "normalized_path": relative_to_project(project_dir, normalized),
        "normalization": {
            **image_normalization_layout(
                width,
                height,
                mode=normalization_mode,
            ),
            "normalized_sha256": sha256_file(normalized),
        },
        "synthetic": synthetic,
        "derived_from": derived_from,
        "person_class": person_class,
        "relevance": relevance,
        "evidence_role": "unreviewed",
        "review": {
            "content": "review_required",
            "quality": "review_required",
            "reviewed_at": "",
            "asset_sha256": "",
            "fact_ids": [],
            "content_description": "",
            "main_subject_visible": False,
            "crop_safe": False,
            "non_identifying": False,
            "display_focus": "",
            "preview_checked": False,
            "evidence_readable": False,
            "visual_anchor_terms": [],
            "normalized_sha256": "",
        },
        "fallback_reason": "",
        "portrait_style": "",
        "portrait_style_strength": "",
        "portrait_eye_motif": "",
        "portrait_review": {
            "identity_preserved": False,
            "clothing_preserved": False,
            "context_preserved": False,
            "style_obvious_at_preview": False,
            "eye_motif_present": False,
            "ruler_ticks_visible": False,
            "eye_motif_editorial_only": False,
        },
        "visual_text": visual_text,
        "rights_status": "unreviewed",
        "watermark_removed": False,
    }
    manifest["assets"].append(record)
    return record


def add_research_source(project_dir: Path, source_url: str) -> None:
    research_path = project_dir / "research.json"
    research = read_json(research_path)
    sources = research.setdefault("sources", [])
    if any(item.get("url") == source_url for item in sources):
        return
    sources.append(
        {
            "id": f"source-{len(sources) + 1:02d}",
            "url": source_url,
            "publisher": "",
            "title": "",
            "captured_at": now_iso(),
        }
    )
    write_json(research_path, research)


def collect_assets(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir).expanduser().resolve()
    if not (project_dir / "project.json").is_file():
        raise CCHelperError(f"cc_helper 프로젝트가 아닙니다: {project_dir}")
    if args.synthetic and args.local_file and not args.text_free:
        raise CCHelperError(
            "합성 에셋은 이미지 내부에 편집 문구가 없음을 확인한 --text-free가 필요합니다."
        )
    if args.text_free and not args.synthetic:
        raise CCHelperError("--text-free는 --synthetic과 함께 사용해야 합니다.")
    if args.community_capture and args.synthetic:
        raise CCHelperError("커뮤니티 캡처는 실제 원본에만 사용할 수 있습니다.")
    manifest = load_manifest(project_dir)
    results: list[dict[str, Any]] = []
    warnings: list[str] = []

    def normalization_mode_for(source_url: str) -> str:
        if args.community_capture or is_community_source_url(source_url):
            return COMMUNITY_CAPTURE_NORMALIZATION_MODE
        return DEFAULT_NORMALIZATION_MODE

    for local_value in args.local_file or []:
        source_page_url = args.source_url[0] if args.source_url else ""
        record = ingest_local_asset(
            project_dir,
            manifest,
            Path(local_value).expanduser().resolve(),
            source_page_url=source_page_url,
            asset_url="",
            source_method="generated_file" if args.synthetic else "local_file",
            synthetic=args.synthetic,
            derived_from=args.derived_from,
            person_class=args.person_class,
            relevance=args.relevance,
            visual_text="none" if args.synthetic else "source_original",
            normalization_mode=normalization_mode_for(source_page_url),
        )
        results.append(record)

    explicit_urls = list(args.asset_url or [])
    page_candidates: list[tuple[str, dict[str, Any]]] = []
    for source_url in args.source_url or []:
        add_research_source(project_dir, source_url)
        try:
            html, final_url = fetch_page(source_url)
            candidates = ranked_page_assets(final_url, html)
        except CCHelperError as exc:
            warnings.append(str(exc))
            candidates = []
            final_url = source_url
        manifest["searches"].append(
            {
                "source_page_url": final_url,
                "searched_at": now_iso(),
                "candidate_count": len(candidates),
                "selected_asset_urls": [],
            }
        )
        page_candidates.extend((final_url, candidate) for candidate in candidates)

    if args.list_only:
        write_json(project_dir / "asset-manifest.json", manifest)
        print_json(
            {
                "candidates": [
                    {"source_page_url": page, **candidate}
                    for page, candidate in page_candidates[: args.max_assets]
                ],
                "warnings": warnings,
            }
        )
        return

    download_targets: list[tuple[str, str]] = []
    if explicit_urls:
        referer = args.source_url[0] if args.source_url else ""
        download_targets.extend((referer, url) for url in explicit_urls)
    else:
        download_targets.extend(
            (page, candidate["url"])
            for page, candidate in page_candidates[: args.max_assets]
            if candidate.get("score", 0) > 0
        )

    for referer, asset_url in download_targets:
        try:
            limit = MAX_VIDEO_BYTES if Path(parse.urlsplit(asset_url).path).suffix.lower() in VIDEO_EXTENSIONS else MAX_IMAGE_BYTES
            data, content_type, final_url = fetch_bytes(asset_url, referer=referer, limit=limit)
            suffix = extension_for(content_type, final_url)
            if suffix not in IMAGE_EXTENSIONS | VIDEO_EXTENSIONS:
                raise CCHelperError(f"지원하지 않는 MIME 형식입니다({content_type}): {asset_url}")
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temporary:
                temporary.write(data)
                temporary_path = Path(temporary.name)
            try:
                record = ingest_local_asset(
                    project_dir,
                    manifest,
                    temporary_path,
                    source_page_url=referer,
                    asset_url=final_url,
                    source_method="web_page",
                    synthetic=False,
                    derived_from="",
                    person_class=args.person_class,
                    relevance=args.relevance,
                    visual_text="source_original",
                    normalization_mode=normalization_mode_for(referer),
                )
                results.append(record)
                for search in reversed(manifest["searches"]):
                    if search.get("source_page_url") == referer:
                        search["selected_asset_urls"].append(final_url)
                        break
            finally:
                temporary_path.unlink(missing_ok=True)
        except CCHelperError as exc:
            warnings.append(str(exc))

    write_json(project_dir / "asset-manifest.json", manifest)
    print_json({"assets": results, "warnings": warnings})


def review_asset(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir).expanduser().resolve()
    manifest = load_manifest(project_dir)
    record = next(
        (item for item in manifest.get("assets", []) if item.get("id") == args.asset_id),
        None,
    )
    if not isinstance(record, dict):
        raise CCHelperError(f"검수할 에셋을 찾을 수 없습니다: {args.asset_id}")

    source = project_path(project_dir, str(record.get("source_path") or ""))
    actual_sha = sha256_file(source)
    if actual_sha != str(record.get("sha256") or ""):
        raise CCHelperError("에셋 원본 SHA-256이 manifest와 다릅니다. 다시 수집하세요.")

    research = read_json(project_dir / "research.json")
    known_fact_ids = {
        str(item.get("id") or "")
        for item in research.get("facts", [])
        if str(item.get("id") or "")
    }
    fact_ids = list(dict.fromkeys(args.fact_id or []))
    unknown_fact_ids = sorted(set(fact_ids) - known_fact_ids)
    if unknown_fact_ids:
        raise CCHelperError(f"research.json에 없는 fact ID입니다: {unknown_fact_ids}")
    if args.approve_content and (not fact_ids or not args.content_description.strip()):
        raise CCHelperError("내용 승인에는 --fact-id와 --content-description이 필요합니다.")
    if args.approve_quality and not (args.main_subject_visible and args.crop_safe):
        raise CCHelperError(
            "품질 승인에는 --main-subject-visible과 --crop-safe 확인이 필요합니다."
        )
    storyboard = read_json(project_dir / "storyboard.json")
    display_validation = (
        str(storyboard.get("display_validation_mode") or "").strip()
        == DISPLAY_VALIDATION_MODE
    )
    public_figure_style_mode = str(
        storyboard.get("public_figure_style_mode") or ""
    ).strip()
    if args.approve_quality and display_validation:
        if args.display_focus not in DISPLAY_FOCUS_VALUES:
            raise CCHelperError("최종 표시 검수에는 --display-focus가 필요합니다.")
        if not args.preview_checked:
            raise CCHelperError("최종 표시 품질 승인에는 --preview-checked가 필요합니다.")
        if args.display_focus in {"source_text", "mixed"}:
            if not args.evidence_readable:
                raise CCHelperError("텍스트 증거 화면은 --evidence-readable 확인이 필요합니다.")
            if not args.visual_anchor_term:
                raise CCHelperError("텍스트 증거 화면에는 --visual-anchor-term이 필요합니다.")
    if args.evidence_role == "editorial_animation":
        if args.non_identifying:
            raise CCHelperError("editorial_animation의 눈가림 모티프를 비식별 처리로 승인할 수 없습니다.")
        if record.get("person_class") != "public_figure":
            raise CCHelperError("editorial_animation은 검수된 공개 인물에만 사용할 수 있습니다.")
        if not args.people_visible or args.people_treatment != "editorial_animation":
            raise CCHelperError("editorial_animation은 식별 가능한 공개 인물 표시로 검수해야 합니다.")
        if record.get("portrait_style") not in {"", PORTRAIT_STYLE} and not args.portrait_style:
            raise CCHelperError(f"지원하지 않는 인물 화풍입니다: {record.get('portrait_style')}")
        if (args.portrait_style or PORTRAIT_STYLE) != PORTRAIT_STYLE:
            raise CCHelperError(f"인물 화풍은 {PORTRAIT_STYLE}이어야 합니다.")
        if not str(record.get("derived_from") or ""):
            raise CCHelperError("editorial_animation에는 검수된 실제 인물 자료 derived_from이 필요합니다.")
        if not (args.approve_identity and args.approve_clothing and args.approve_context):
            raise CCHelperError("인물 파생본은 신원·의상·사실 맥락 보존 승인이 모두 필요합니다.")
        if public_figure_style_mode == PUBLIC_FIGURE_STYLE_MODE:
            if args.portrait_style_strength != PORTRAIT_STYLE_STRENGTH:
                raise CCHelperError(f"공개 인물 화풍 강도는 {PORTRAIT_STYLE_STRENGTH}이어야 합니다.")
            if args.portrait_eye_motif != PORTRAIT_EYE_MOTIF:
                raise CCHelperError(f"공개 인물 눈가림 모티프는 {PORTRAIT_EYE_MOTIF}여야 합니다.")
            if not (
                args.approve_style_obvious
                and args.approve_eye_motif
                and args.approve_ruler_ticks
                and args.confirm_eye_motif_editorial_only
            ):
                raise CCHelperError(
                    "강한 화풍·눈가림 표시·눈금 표시·권리 비식별 효과 없음 확인이 모두 필요합니다."
                )
    if args.evidence_role == "non_identifying_fallback":
        if not args.non_identifying:
            raise CCHelperError("비식별 대체 화면은 --non-identifying 확인이 필요합니다.")
        if not args.fallback_reason.strip():
            raise CCHelperError("비식별 대체 화면에는 --fallback-reason이 필요합니다.")

    record["evidence_role"] = args.evidence_role
    normalized_path = project_path(project_dir, str(record.get("normalized_path") or ""))
    normalization_mode = str(
        record.get("normalization_mode") or DEFAULT_NORMALIZATION_MODE
    )
    record["normalization"] = {
        **image_normalization_layout(
            integer_or_zero(record.get("width")),
            integer_or_zero(record.get("height")),
            mode=normalization_mode,
        ),
        "normalized_sha256": sha256_file(normalized_path),
    }
    record["review"] = {
        "content": "approved" if args.approve_content else "review_required",
        "quality": "approved" if args.approve_quality else "review_required",
        "reviewed_at": now_iso(),
        "asset_sha256": actual_sha,
        "fact_ids": fact_ids,
        "content_description": args.content_description.strip(),
        "main_subject_visible": bool(args.main_subject_visible),
        "crop_safe": bool(args.crop_safe),
        "non_identifying": bool(args.non_identifying),
        "people_visible": bool(args.people_visible),
        "people_treatment": args.people_treatment,
        "display_focus": args.display_focus,
        "preview_checked": bool(args.preview_checked),
        "evidence_readable": bool(args.evidence_readable),
        "visual_anchor_terms": list(dict.fromkeys(args.visual_anchor_term or [])),
        "normalized_sha256": sha256_file(normalized_path),
    }
    record["fallback_reason"] = args.fallback_reason.strip()
    record["portrait_style"] = (
        PORTRAIT_STYLE if args.evidence_role == "editorial_animation" else ""
    )
    record["portrait_style_strength"] = (
        args.portrait_style_strength if args.evidence_role == "editorial_animation" else ""
    )
    record["portrait_eye_motif"] = (
        args.portrait_eye_motif if args.evidence_role == "editorial_animation" else ""
    )
    record["portrait_review"] = {
        "identity_preserved": bool(args.approve_identity),
        "clothing_preserved": bool(args.approve_clothing),
        "context_preserved": bool(args.approve_context),
        "style_obvious_at_preview": bool(args.approve_style_obvious),
        "eye_motif_present": bool(args.approve_eye_motif),
        "ruler_ticks_visible": bool(args.approve_ruler_ticks),
        "eye_motif_editorial_only": bool(args.confirm_eye_motif_editorial_only),
    }
    write_json(project_dir / "asset-manifest.json", manifest)
    print_json({"asset": record})


def validate_research(project_dir: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    research = read_json(project_dir / "research.json")
    candidates = research.get("candidates")
    selected_id = str(research.get("selected_candidate_id") or "")
    if not isinstance(candidates, list) or not 1 <= len(candidates) <= 3:
        errors.append("research.json 후보는 1~3개여야 합니다.")
        candidates = []
    if not selected_id or not any(item.get("id") == selected_id for item in candidates):
        errors.append("선택된 Candidate ID가 후보 목록과 일치하지 않습니다.")
    sources = research.get("sources")
    if not isinstance(sources, list) or not sources:
        errors.append("최소 1개의 조사 출처가 필요합니다.")
        sources = []
    source_ids = {item.get("id") for item in sources if item.get("id") and item.get("url")}
    if len(source_ids) != len(sources):
        errors.append("모든 조사 출처에 고유 ID와 URL이 필요합니다.")
    facts = research.get("facts")
    if not isinstance(facts, list) or not facts:
        errors.append("최소 1개의 사실과 출처 연결이 필요합니다.")
        facts = []
    for index, fact in enumerate(facts, start=1):
        if not str(fact.get("claim") or "").strip():
            errors.append(f"사실 {index}에 claim이 없습니다.")
        linked = fact.get("source_ids")
        if not isinstance(linked, list) or not linked or any(item not in source_ids for item in linked):
            errors.append(f"사실 {index}의 source_ids가 출처 목록과 연결되지 않습니다.")
    if len(sources) == 1:
        warnings.append("출처가 하나뿐입니다. 가능하면 독립 출처로 교차 확인하세요.")
    return errors, warnings


def validate_youtube_upload(
    project_dir: Path,
    project: dict[str, Any],
    storyboard: dict[str, Any],
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    mode = str(project.get("youtube_upload_mode") or "").strip()
    if mode not in SUPPORTED_YOUTUBE_UPLOAD_MODES:
        return [f"지원하지 않는 youtube_upload_mode입니다: {mode}"], warnings
    if mode != YOUTUBE_UPLOAD_MODE:
        return errors, warnings
    upload = project.get("youtube_upload") if isinstance(project, dict) else None
    if not isinstance(upload, dict):
        return ["copy-handoff에는 project.json youtube_upload 정보가 필요합니다."], warnings
    if upload.get("status") != "copy_ready":
        errors.append("youtube_upload status는 copy_ready여야 합니다.")
    title = str(upload.get("title") or "").strip()
    description = str(upload.get("description") or "").strip()
    pinned_comment = str(upload.get("pinned_comment") or "").strip()
    if not 1 <= len(title) <= 100:
        errors.append("유튜브 제목은 1~100자여야 합니다.")
    if not 1 <= len(description) <= 5_000:
        errors.append("유튜브 설명은 1~5000자여야 합니다.")
    if not 1 <= len(pinned_comment) <= 500:
        errors.append("유튜브 고정댓글은 1~500자여야 합니다.")
    hashtags = upload.get("hashtags") if isinstance(upload.get("hashtags"), list) else []
    if not 1 <= len(hashtags) <= 5:
        errors.append("유튜브 해시태그는 1~5개여야 합니다.")
    elif any(not re.fullmatch(r"#[^\s#]{1,30}", str(item)) for item in hashtags):
        errors.append("유튜브 해시태그는 #으로 시작하고 공백 없이 작성해야 합니다.")
    tags = upload.get("tags") if isinstance(upload.get("tags"), list) else []
    if not 1 <= len(tags) <= 15 or any(
        not str(item).strip()
        or len(str(item).strip()) > 100
        or str(item).strip().startswith("#")
        for item in tags
    ):
        errors.append("유튜브 검색 태그는 # 없이 1~15개, 항목당 100자 이하여야 합니다.")
    if str(upload.get("category") or "") not in YOUTUBE_CATEGORIES:
        errors.append(f"유튜브 category는 다음 중 하나여야 합니다: {sorted(YOUTUBE_CATEGORIES)}")
    if str(upload.get("language") or "") != "ko":
        errors.append("한국어 쇼츠의 youtube_upload language는 ko여야 합니다.")
    if str(upload.get("audience") or "") not in {"made_for_kids", "not_made_for_kids"}:
        errors.append("유튜브 audience는 made_for_kids 또는 not_made_for_kids여야 합니다.")
    if not isinstance(upload.get("altered_content"), bool):
        errors.append("유튜브 altered_content는 true 또는 false여야 합니다.")
    elif upload.get("altered_content") and not str(
        upload.get("altered_content_reason") or ""
    ).strip():
        errors.append("altered_content=true에는 공개용 변형 사유가 필요합니다.")
    visibility = str(upload.get("recommended_visibility") or "")
    if visibility not in {"private", "unlisted", "public"}:
        errors.append("유튜브 recommended_visibility가 올바르지 않습니다.")
    if project.get("publish_blocked") is True and visibility != "private":
        errors.append("publish_blocked 프로젝트는 유튜브 공개 범위를 private로 권장해야 합니다.")
    thumbnail = upload.get("thumbnail") if isinstance(upload.get("thumbnail"), dict) else {}
    storyboard_title = storyboard.get("title") if isinstance(storyboard.get("title"), dict) else {}
    for key in ("white", "yellow"):
        if str(thumbnail.get(key) or "") != str(storyboard_title.get(key) or ""):
            errors.append(f"유튜브 thumbnail.{key}가 storyboard 제목과 다릅니다.")
    source_ids = upload.get("source_ids") if isinstance(upload.get("source_ids"), list) else []
    research = read_json(project_dir / "research.json")
    known_source_ids = {
        str(item.get("id") or "")
        for item in research.get("sources", [])
        if isinstance(item, dict)
    }
    if not 1 <= len(source_ids) <= 5:
        errors.append("유튜브 업로드 정보에는 대표 source_ids 1~5개가 필요합니다.")
    else:
        unknown = sorted(str(item) for item in source_ids if str(item) not in known_source_ids)
        if unknown:
            errors.append(f"유튜브 source_ids가 research.json과 연결되지 않습니다: {unknown}")
    if project.get("publish_blocked") is True:
        warnings.append("유튜브 문구는 복사용 초안이며 권리 검토 전 게시할 수 없습니다.")
    return errors, warnings


def validate_narration_timing(
    project_dir: Path,
    project: dict[str, Any],
    storyboard: dict[str, Any],
    times: list[dict[str, int]],
) -> list[str]:
    errors: list[str] = []
    audio = project.get("narration_audio")
    if not isinstance(audio, dict) or not str(audio.get("path") or "").strip():
        return errors

    timing_path = project_dir / "handoff" / "narration-timing.json"
    if not timing_path.is_file():
        return ["narration-hold 음원에는 handoff/narration-timing.json이 필요합니다."]
    try:
        timing = read_json(timing_path)
    except CCHelperError as exc:
        return [str(exc)]
    if timing.get("source") not in {"capcut_waveform_review", "typecast_timestamp_review"}:
        errors.append(
            "narration-timing.json source는 capcut_waveform_review 또는 "
            "typecast_timestamp_review여야 합니다."
        )

    relative_audio = str(audio.get("path") or "")
    try:
        audio_path = project_path(project_dir, relative_audio)
        actual_sha = sha256_file(audio_path)
        actual_duration = wav_duration_seconds(audio_path)
    except CCHelperError as exc:
        errors.append(str(exc))
        return errors

    timing_audio = timing.get("audio")
    if not isinstance(timing_audio, dict):
        errors.append("narration-timing.json audio 정보가 필요합니다.")
        timing_audio = {}
    if timing_audio.get("path") != relative_audio:
        errors.append("narration-timing.json 음원 경로가 project.json과 다릅니다.")
    expected_sha = str(audio.get("sha256") or "")
    timing_sha = str(timing_audio.get("sha256") or "")
    if not expected_sha or expected_sha != actual_sha or timing_sha != actual_sha:
        errors.append("내레이션 음원 SHA-256이 타이밍 기록과 일치하지 않습니다. 재타이밍이 필요합니다.")
    try:
        recorded_duration = float(timing_audio.get("duration_seconds"))
    except (TypeError, ValueError):
        recorded_duration = -1.0
    if abs(recorded_duration - actual_duration) > 0.02:
        errors.append("narration-timing.json 음원 길이가 실제 WAV와 다릅니다.")
    try:
        project_duration = float(audio.get("duration_seconds"))
    except (TypeError, ValueError):
        project_duration = -1.0
    if abs(project_duration - actual_duration) > 0.02:
        errors.append("project.json 내레이션 길이가 실제 WAV와 다릅니다.")

    scene_cues = timing.get("scenes")
    scenes = storyboard.get("scenes") if isinstance(storyboard.get("scenes"), list) else []
    caption_sync = storyboard.get("caption_sync_mode") == CAPTION_SYNC_MODE
    if not isinstance(scene_cues, list) or len(scene_cues) != SCENE_COUNT:
        errors.append("narration-timing.json에는 15개 scene 타이밍이 필요합니다.")
        scene_cues = []
    cue_by_scene: dict[str, tuple[int, int]] = {}
    previous_end = 0
    for index, (cue, scene, calculated) in enumerate(zip(scene_cues, scenes, times), start=1):
        expected_id = f"scene-{index:02d}"
        if cue.get("scene_id") != expected_id or scene.get("id") != expected_id:
            errors.append(f"narration-timing.json 장면 {index} ID가 {expected_id}가 아닙니다.")
            continue
        try:
            start_us = int(round(float(cue.get("start_seconds")) * 1_000_000))
            end_us = int(round(float(cue.get("end_seconds")) * 1_000_000))
        except (TypeError, ValueError):
            errors.append(f"{expected_id} 타이밍이 숫자가 아닙니다.")
            continue
        if start_us != previous_end or end_us <= start_us:
            errors.append(f"{expected_id} 타이밍에 공백, 겹침 또는 역전이 있습니다.")
        if start_us != calculated["start"] or end_us - start_us != calculated["duration"]:
            errors.append(f"{expected_id} 타이밍이 storyboard duration과 다릅니다.")
        previous_scene = scenes[index - 2] if index > 1 else None
        is_hold_follower = (
            caption_sync
            and previous_scene is not None
            and scene.get("beat_id") == previous_scene.get("beat_id")
        )
        if is_hold_follower:
            if cue.get("onset_policy") != CAPTION_ONSET_POLICY:
                errors.append(
                    f"{expected_id} 홀드 자막 경계는 onset_policy={CAPTION_ONSET_POLICY} 검토가 필요합니다."
                )
            spoken_prefix = str(cue.get("spoken_prefix") or "").strip()
            normalized_prefix = normalize_caption_match(spoken_prefix)
            if not normalized_prefix:
                errors.append(f"{expected_id} 홀드 자막 경계에는 spoken_prefix가 필요합니다.")
            else:
                if not normalize_caption_match(scene.get("narration")).startswith(normalized_prefix):
                    errors.append(f"{expected_id} spoken_prefix가 narration 시작과 다릅니다.")
                if not normalize_caption_match(scene.get("caption")).startswith(normalized_prefix):
                    errors.append(f"{expected_id} spoken_prefix가 caption 시작과 다릅니다.")
            try:
                frame_rate = float(cue.get("frame_rate"))
                strong_onset = float(cue.get("strong_speech_onset_seconds"))
            except (TypeError, ValueError):
                errors.append(f"{expected_id} 홀드 자막 경계의 강한 발화 시작 근거가 필요합니다.")
            else:
                if abs(frame_rate - CAPTION_FRAME_RATE) > 0.001:
                    errors.append(f"{expected_id} 파형 검토 frame_rate는 30이어야 합니다.")
                elif abs(strong_onset - start_us / 1_000_000) > 1.0 / frame_rate + 1e-6:
                    errors.append(
                        f"{expected_id} 자막 시작이 strong_speech 발화 시작과 1프레임 넘게 다릅니다."
                    )
        cue_by_scene[expected_id] = (start_us, end_us)
        previous_end = end_us

    beat_cues = timing.get("beats")
    beats = storyboard.get("beats") if isinstance(storyboard.get("beats"), list) else []
    if not isinstance(beat_cues, list) or len(beat_cues) != len(beats):
        errors.append("narration-timing.json beat 타이밍 수가 storyboard와 다릅니다.")
        beat_cues = []
    previous_beat_end = 0
    for cue, beat in zip(beat_cues, beats):
        beat_id = str(beat.get("id") or "")
        if cue.get("beat_id") != beat_id:
            errors.append(f"narration-timing.json beat ID 순서가 다릅니다: {beat_id}")
            continue
        try:
            start_us = int(round(float(cue.get("start_seconds")) * 1_000_000))
            end_us = int(round(float(cue.get("end_seconds")) * 1_000_000))
        except (TypeError, ValueError):
            errors.append(f"{beat_id} 타이밍이 숫자가 아닙니다.")
            continue
        if start_us != previous_beat_end or end_us <= start_us:
            errors.append(f"{beat_id} 타이밍에 공백, 겹침 또는 역전이 있습니다.")
        linked = [scene for scene in scenes if scene.get("beat_id") == beat_id]
        if linked:
            first = cue_by_scene.get(str(linked[0].get("id")))
            last = cue_by_scene.get(str(linked[-1].get("id")))
            if not first or not last or first[0] != start_us or last[1] != end_us:
                errors.append(f"{beat_id} 타이밍이 연결된 장면 범위와 다릅니다.")
        previous_beat_end = end_us

    total_us = sum(item["duration"] for item in times)
    try:
        capcut_duration_us = int(audio.get("capcut_duration_us"))
    except (TypeError, ValueError):
        capcut_duration_us = int(round(actual_duration * 1_000_000))
    if total_us != capcut_duration_us:
        errors.append("storyboard 전체 길이가 project.json CapCut 음원 길이와 다릅니다.")
    if abs(total_us / 1_000_000 - actual_duration) > AUDIO_DURATION_TOLERANCE_SECONDS:
        errors.append("스토리보드 종료가 실제 내레이션 종료와 0.15초 넘게 어긋납니다.")
    return errors


def wav_loudness_metrics(path: Path) -> tuple[float, float]:
    if not executable_available("ffmpeg"):
        raise CCHelperError("내레이션 음량 검증에는 ffmpeg가 필요합니다.")
    result = subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-i",
            str(path),
            "-af",
            "loudnorm=I=-16:TP=-1:LRA=11:print_format=json",
            "-f",
            "null",
            "-",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    matches = re.findall(r"\{\s*\"input_i\"[\s\S]*?\}", result.stderr)
    if result.returncode != 0 or not matches:
        raise CCHelperError("내레이션 LUFS/true peak를 측정할 수 없습니다.")
    try:
        payload = json.loads(matches[-1])
        return float(payload["input_i"]), float(payload["input_tp"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise CCHelperError("내레이션 음량 측정 결과를 해석할 수 없습니다.") from exc


def wav_silence_intervals(path: Path) -> list[tuple[float, float, float]]:
    if not executable_available("ffmpeg"):
        raise CCHelperError("내레이션 pause 검증에는 ffmpeg가 필요합니다.")
    result = subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-nostats",
            "-i",
            str(path),
            "-af",
            (
                f"silencedetect=noise={NARRATION_SILENCE_THRESHOLD_DB:g}dB:"
                f"d={NARRATION_SILENCE_MIN_SECONDS:g}"
            ),
            "-f",
            "null",
            "-",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise CCHelperError("내레이션 pause 구간을 측정할 수 없습니다.")
    intervals: list[tuple[float, float, float]] = []
    current_start: float | None = None
    for line in result.stderr.splitlines():
        start_match = re.search(r"silence_start:\s*([0-9.]+)", line)
        if start_match:
            current_start = float(start_match.group(1))
        end_match = re.search(
            r"silence_end:\s*([0-9.]+)\s*\|\s*silence_duration:\s*([0-9.]+)",
            line,
        )
        if end_match:
            end = float(end_match.group(1))
            duration = float(end_match.group(2))
            start = current_start if current_start is not None else max(0.0, end - duration)
            intervals.append((start, end, duration))
            current_start = None
    return intervals


def measured_pause_at_boundary(
    intervals: list[tuple[float, float, float]], boundary_seconds: float
) -> float | None:
    candidates = [
        interval
        for interval in intervals
        if interval[0] <= boundary_seconds + 0.12
        and interval[1] >= boundary_seconds - 0.40
    ]
    if not candidates:
        return None
    _start, _end, duration = min(
        candidates,
        key=lambda interval: abs(interval[1] - boundary_seconds),
    )
    return duration


def validate_narration_performance(
    project_dir: Path,
    project: dict[str, Any],
    storyboard: dict[str, Any],
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    mode = str(storyboard.get("narration_performance_mode") or "").strip()
    if mode not in SUPPORTED_NARRATION_PERFORMANCE_MODES:
        return [f"지원하지 않는 narration_performance_mode입니다: {mode}"], warnings
    audio = project.get("narration_audio") if isinstance(project, dict) else None
    if mode != NARRATION_PERFORMANCE_MODE or not isinstance(audio, dict):
        return errors, warnings
    performance_path = project_dir / "handoff" / "narration-performance.json"
    if not performance_path.is_file():
        return ["reviewed-external 음원에는 handoff/narration-performance.json이 필요합니다."], warnings
    performance = read_json(performance_path)
    if performance.get("source") != "external_tts_review":
        errors.append("narration-performance source는 external_tts_review여야 합니다.")
    narration_sha = narration_contract_sha256(storyboard)
    if performance.get("storyboard_narration_sha256") != narration_sha:
        errors.append("narration-performance가 현재 storyboard 내레이션과 stale 상태입니다.")

    file_specs = (
        (performance.get("script"), "handoff/narration-typecast.txt", "script"),
        (performance.get("audio"), str(audio.get("path") or ""), "audio"),
        (performance.get("timing"), "handoff/narration-timing.json", "timing"),
    )
    current_hashes: dict[str, str] = {}
    for spec, expected_path, label in file_specs:
        if not isinstance(spec, dict) or spec.get("path") != expected_path:
            errors.append(f"narration-performance {label} 경로가 현재 프로젝트와 다릅니다.")
            continue
        try:
            path = project_path(project_dir, expected_path)
            actual_sha = sha256_file(path)
        except CCHelperError as exc:
            errors.append(str(exc))
            continue
        current_hashes[label] = actual_sha
        if spec.get("sha256") != actual_sha:
            errors.append(f"narration-performance {label} SHA-256이 현재 파일과 다릅니다.")
    if current_hashes.get("audio") and current_hashes["audio"] != str(audio.get("sha256") or ""):
        errors.append("project.json narration_audio SHA-256이 performance 음원과 다릅니다.")
    timing = performance.get("timing") if isinstance(performance.get("timing"), dict) else {}
    if timing.get("source") not in {"capcut_waveform_review", "typecast_timestamp_review"}:
        errors.append("narration-performance timing source가 지원되지 않습니다.")

    beats = storyboard.get("beats") if isinstance(storyboard.get("beats"), list) else []
    profiles = performance.get("beats") if isinstance(performance.get("beats"), list) else []
    if [item.get("beat_id") for item in profiles] != [item.get("id") for item in beats]:
        errors.append("narration-performance beat ID 순서가 storyboard와 다릅니다.")
    measured_pauses: dict[str, float] = {}
    if current_hashes.get("audio") and current_hashes.get("timing"):
        try:
            audio_path = project_path(project_dir, str(audio.get("path") or ""))
            timing_payload = read_json(project_dir / "handoff" / "narration-timing.json")
            silence_intervals = wav_silence_intervals(audio_path)
            timing_beats = (
                timing_payload.get("beats")
                if isinstance(timing_payload.get("beats"), list)
                else []
            )
            for cue in timing_beats[:-1]:
                beat_id = str(cue.get("beat_id") or "")
                boundary = float(cue.get("end_seconds"))
                measured = measured_pause_at_boundary(silence_intervals, boundary)
                if measured is not None:
                    measured_pauses[beat_id] = measured
        except (CCHelperError, TypeError, ValueError) as exc:
            errors.append(str(exc))
    signatures: list[tuple[str, str, float]] = []
    for index, profile in enumerate(profiles):
        beat_id = str(profile.get("beat_id") or f"beat-{index + 1:02d}")
        emotion_type = str(profile.get("emotion_type") or "")
        preset = str(profile.get("emotion_preset") or "")
        if emotion_type not in {"smart", "preset"}:
            errors.append(f"{beat_id} emotion_type은 smart 또는 preset이어야 합니다.")
        if emotion_type == "preset" and preset not in {"normal", "toneup", "tonedown"}:
            errors.append(f"{beat_id} preset은 normal/toneup/tonedown만 사용할 수 있습니다.")
        try:
            tempo = float(profile.get("tempo"))
            planned_pause = float(profile.get("pause_after_seconds"))
            measured_pause = float(profile.get("measured_pause_after_seconds"))
        except (TypeError, ValueError):
            errors.append(f"{beat_id} tempo/pause 값이 숫자가 아닙니다.")
            continue
        if not 0.90 <= tempo <= 1.10:
            errors.append(f"{beat_id} tempo는 0.90~1.10 범위여야 합니다.")
        elif not 0.96 <= tempo <= 1.04:
            warnings.append(f"{beat_id} tempo가 권장 0.96~1.04 범위 밖입니다: {tempo:.2f}")
        is_last = index == len(profiles) - 1
        if is_last:
            if abs(planned_pause) > 0.001 or abs(measured_pause) > 0.001:
                errors.append(f"{beat_id} 마지막 beat 뒤에는 pause를 둘 수 없습니다.")
        else:
            actual_pause = measured_pauses.get(beat_id)
            if actual_pause is None:
                errors.append(f"{beat_id} 경계에서 실제 pause를 측정하지 못했습니다.")
            else:
                if not 0.12 <= planned_pause <= 0.40 or not 0.12 <= actual_pause <= 0.40:
                    errors.append(f"{beat_id} pause는 0.12~0.40초여야 합니다.")
                if abs(planned_pause - actual_pause) > 0.10:
                    errors.append(f"{beat_id} 계획 pause와 실제 WAV pause가 0.10초 넘게 다릅니다.")
                if abs(measured_pause - actual_pause) > NARRATION_PAUSE_MEASUREMENT_TOLERANCE_SECONDS:
                    errors.append(f"{beat_id} 기록된 pause가 실제 WAV 측정값과 다릅니다.")
        signatures.append((emotion_type, preset, round(tempo, 3)))
    if profiles and len(set(signatures)) == 1:
        warnings.append("모든 narration beat가 같은 감정·tempo라 강약 변화가 없습니다.")
    if any(signatures[index:index + 4].count(signatures[index]) == 4 for index in range(max(0, len(signatures) - 3))):
        warnings.append("같은 narration performance profile이 4개 이상 연속됩니다.")

    analysis = performance.get("audio_analysis")
    if not isinstance(analysis, dict):
        errors.append("narration-performance audio_analysis가 필요합니다.")
    elif current_hashes.get("audio"):
        try:
            recorded_threshold = float(analysis.get("silence_threshold_db"))
            recorded_minimum = float(analysis.get("minimum_silence_seconds"))
        except (TypeError, ValueError):
            errors.append("narration-performance silence 측정 기준이 숫자가 아닙니다.")
        else:
            if recorded_threshold != NARRATION_SILENCE_THRESHOLD_DB:
                errors.append("narration-performance silence threshold가 검증 기준과 다릅니다.")
            if abs(recorded_minimum - NARRATION_SILENCE_MIN_SECONDS) > 0.001:
                errors.append("narration-performance minimum silence가 검증 기준과 다릅니다.")
        audio_path = project_path(project_dir, str(audio.get("path") or ""))
        try:
            integrated_lufs, true_peak = wav_loudness_metrics(audio_path)
        except CCHelperError as exc:
            errors.append(str(exc))
        else:
            try:
                recorded_lufs = float(analysis.get("integrated_lufs"))
                recorded_peak = float(analysis.get("true_peak_dbtp"))
            except (TypeError, ValueError):
                errors.append("narration-performance 음량 측정값이 숫자가 아닙니다.")
            else:
                if abs(recorded_lufs - integrated_lufs) > 0.2 or abs(recorded_peak - true_peak) > 0.2:
                    errors.append("narration-performance 음량 측정값이 실제 WAV와 다릅니다.")
                if not -18.0 <= integrated_lufs <= -14.0:
                    errors.append(f"내레이션 integrated loudness는 -18~-14 LUFS여야 합니다: {integrated_lufs:.2f}")
                if true_peak > -1.0:
                    errors.append(f"내레이션 true peak는 -1.0 dBTP 이하여야 합니다: {true_peak:.2f}")

    listening = performance.get("listening_review")
    if not isinstance(listening, dict):
        errors.append("내레이션 성능 검수 기록이 필요합니다.")
    else:
        reviewer_kind = str(listening.get("reviewer_kind") or "")
        checks = listening.get("checks") if isinstance(listening.get("checks"), dict) else {}
        if reviewer_kind == "human":
            if listening.get("status") != "approved":
                errors.append("내레이션 사람 청취 승인이 필요합니다.")
            for key in (
                "naturalness",
                "dynamics",
                "breathing",
                "pronunciation",
                "pace",
                "no_audio_artifacts",
            ):
                if checks.get(key) is not True:
                    errors.append(f"내레이션 청취 검수 실패: {key}")
        elif reviewer_kind == "automated":
            if listening.get("status") != "automated_reviewed":
                errors.append("내레이션 자동 성능 검수 상태가 올바르지 않습니다.")
            for key in (
                "profile_variety",
                "measured_pauses",
                "timestamp_alignment",
                "loudness",
                "true_peak",
            ):
                if checks.get(key) is not True:
                    errors.append(f"내레이션 자동 성능 검수 실패: {key}")
            warnings.append("내레이션은 자동 성능 검수만 완료됐습니다. 게시 전 사람 청취 승인이 필요합니다.")
        else:
            errors.append("내레이션 reviewer_kind는 human 또는 automated여야 합니다.")
        for label in ("script", "audio", "timing"):
            if current_hashes.get(label) and listening.get(f"{label}_sha256") != current_hashes[label]:
                errors.append(f"내레이션 청취 승인 {label} SHA-256이 stale 상태입니다.")
        if listening.get("storyboard_narration_sha256") != narration_sha:
            errors.append("내레이션 성능 검수가 현재 storyboard 내레이션과 stale 상태입니다.")
    return errors, warnings


def validate_evidence_first_visuals(
    project_dir: Path,
    storyboard: dict[str, Any],
    manifest: dict[str, Any],
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    scenes = storyboard.get("scenes") if isinstance(storyboard.get("scenes"), list) else []
    records = {
        str(item.get("id") or ""): item
        for item in manifest.get("assets", [])
        if isinstance(item, dict) and str(item.get("id") or "")
    }
    research = read_json(project_dir / "research.json")
    known_fact_ids = {
        str(item.get("id") or "")
        for item in research.get("facts", [])
        if str(item.get("id") or "")
    }
    checked_quality: set[str] = set()
    unique_roles: dict[str, str] = {}
    person_visual_mode = str(storyboard.get("person_visual_mode") or "").strip()
    display_validation_mode = str(storyboard.get("display_validation_mode") or "").strip()
    public_figure_style_mode = str(
        storyboard.get("public_figure_style_mode") or ""
    ).strip()

    def validate_reviewed_record(
        record: dict[str, Any],
        *,
        label: str,
        required_fact_ids: set[str],
    ) -> None:
        asset_id = str(record.get("id") or label)
        review = record.get("review")
        if not isinstance(review, dict):
            errors.append(f"{label}에는 사진 내용·품질 review 기록이 필요합니다.")
            return
        if review.get("content") != "approved":
            errors.append(f"{label} 사진 내용 검수가 approved가 아닙니다.")
        if review.get("quality") != "approved":
            errors.append(f"{label} 사진 품질 검수가 approved가 아닙니다.")
        if not str(review.get("reviewed_at") or "").strip():
            errors.append(f"{label} 사진 검수 시각이 없습니다.")
        if not str(review.get("content_description") or "").strip():
            errors.append(f"{label} 사진에 실제로 보이는 내용 설명이 없습니다.")
        if not review.get("main_subject_visible") or not review.get("crop_safe"):
            errors.append(f"{label} 핵심 피사체 식별·9:16 크롭 안전 확인이 필요합니다.")
        reviewed_fact_ids = {
            str(item) for item in review.get("fact_ids", []) if str(item).strip()
        }
        if not required_fact_ids.issubset(reviewed_fact_ids):
            errors.append(f"{label} 사진 검수 fact_ids가 현재 장면 사실과 연결되지 않습니다.")
        expected_sha = str(record.get("sha256") or "")
        if str(review.get("asset_sha256") or "") != expected_sha:
            errors.append(f"{label} 사진 검수 SHA-256이 현재 에셋과 다릅니다. 재검수가 필요합니다.")
        try:
            source = project_path(project_dir, str(record.get("source_path") or ""))
            if sha256_file(source) != expected_sha:
                errors.append(f"{label} 원본 파일 SHA-256이 manifest와 다릅니다.")
        except CCHelperError as exc:
            errors.append(str(exc))
        if asset_id not in checked_quality:
            checked_quality.add(asset_id)
            width = integer_or_zero(record.get("width"))
            height = integer_or_zero(record.get("height"))
            if not width or not height:
                errors.append(f"{label} 원본 사진 크기 정보가 없습니다.")
            elif max(width, height) < QUALITY_REVIEW_MIN_LONG_SIDE or width * height < QUALITY_REVIEW_MIN_PIXELS:
                warnings.append(
                    f"{label} 실제 자료 해상도가 낮습니다: {width}x{height}. "
                    "합성으로 대체하지 말고 화면 선명도를 직접 확인하세요."
                )

    for scene in scenes:
        scene_id = str(scene.get("id") or "?")
        requirement = str(scene.get("visual_requirement") or "").strip()
        if requirement not in VISUAL_REQUIREMENTS:
            errors.append(f"{scene_id} visual_requirement가 필요합니다: {sorted(VISUAL_REQUIREMENTS)}")
            continue
        scene_fact_ids = {
            str(item) for item in scene.get("fact_ids", []) if str(item).strip()
        }
        if not scene_fact_ids:
            errors.append(f"{scene_id}에는 사진 내용 검수용 fact_ids가 필요합니다.")
        unknown_fact_ids = sorted(scene_fact_ids - known_fact_ids)
        if unknown_fact_ids:
            errors.append(f"{scene_id} fact_ids가 research.json과 연결되지 않습니다: {unknown_fact_ids}")

        asset_id = str(scene.get("asset_id") or "")
        record = records.get(asset_id)
        if not isinstance(record, dict):
            continue
        role = str(record.get("evidence_role") or "unreviewed")
        unique_roles[asset_id] = role
        if role not in EVIDENCE_ROLES:
            errors.append(f"{scene_id} 에셋 evidence_role을 지원하지 않습니다: {role}")
            continue
        if role not in REQUIREMENT_EVIDENCE_ROLES[requirement]:
            errors.append(
                f"{scene_id}의 {requirement}에는 {role} 에셋을 사용할 수 없습니다."
            )
        validate_reviewed_record(
            record,
            label=f"{scene_id} {asset_id}",
            required_fact_ids=scene_fact_ids,
        )
        review = record.get("review") if isinstance(record.get("review"), dict) else {}
        normalization_mode = str(
            record.get("normalization_mode") or DEFAULT_NORMALIZATION_MODE
        )
        if (
            not record.get("synthetic")
            and record.get("media_type") == "image"
            and is_community_source_url(str(record.get("source_page_url") or ""))
            and normalization_mode != COMMUNITY_CAPTURE_NORMALIZATION_MODE
        ):
            errors.append(
                f"{scene_id} 커뮤니티 캡처는 --community-capture 안전 정규화로 "
                "다시 수집해야 합니다."
            )
        if display_validation_mode == DISPLAY_VALIDATION_MODE:
            normalization = record.get("normalization")
            if not isinstance(normalization, dict):
                errors.append(f"{scene_id}에는 9:16 정규화 전경 비율 기록이 필요합니다.")
            else:
                try:
                    normalized = project_path(
                        project_dir, str(record.get("normalized_path") or "")
                    )
                    normalized_sha = sha256_file(normalized)
                except CCHelperError as exc:
                    errors.append(str(exc))
                    normalized_sha = ""
                if normalized_sha and normalization.get("normalized_sha256") != normalized_sha:
                    errors.append(f"{scene_id} 정규화 이미지가 바뀌어 표시 품질 재검수가 필요합니다.")
                if normalized_sha and review.get("normalized_sha256") != normalized_sha:
                    errors.append(f"{scene_id} 최종 표시 검수 SHA-256이 현재 정규화 이미지와 다릅니다.")
                if normalization_mode == COMMUNITY_CAPTURE_NORMALIZATION_MODE:
                    if normalization.get("strategy") != COMMUNITY_CAPTURE_NORMALIZATION_MODE:
                        errors.append(f"{scene_id} 커뮤니티 캡처 안전 정규화 기록이 다릅니다.")
                    box = normalization.get("foreground_box")
                    if not isinstance(box, dict):
                        errors.append(f"{scene_id} 커뮤니티 캡처 전경 영역 기록이 필요합니다.")
                    else:
                        top = integer_or_zero(box.get("y"))
                        bottom = top + integer_or_zero(box.get("height"))
                        safe_top = (CANVAS_HEIGHT - COMMUNITY_CAPTURE_MAX_HEIGHT) // 2
                        safe_bottom = safe_top + COMMUNITY_CAPTURE_MAX_HEIGHT
                        if top < safe_top or bottom > safe_bottom:
                            errors.append(
                                f"{scene_id} 커뮤니티 캡처가 CapCut 안전 영역을 벗어났습니다."
                            )
                focus = str(review.get("display_focus") or "")
                if focus not in DISPLAY_FOCUS_VALUES:
                    errors.append(f"{scene_id} display_focus 검수가 필요합니다.")
                if not review.get("preview_checked"):
                    errors.append(f"{scene_id} 360x640 최종 표시 미리보기 검수가 필요합니다.")
                width_ratio = float(normalization.get("foreground_width_ratio") or 0.0)
                height_ratio = float(normalization.get("foreground_height_ratio") or 0.0)
                area_ratio = float(normalization.get("foreground_area_ratio") or 0.0)
                if (
                    width_ratio < GENERAL_FOREGROUND_MIN_WIDTH_RATIO
                    or height_ratio < GENERAL_FOREGROUND_MIN_HEIGHT_RATIO
                    or area_ratio < GENERAL_FOREGROUND_MIN_AREA_RATIO
                ):
                    errors.append(
                        f"{scene_id} 핵심 화면이 9:16에서 너무 작습니다: "
                        f"폭 {width_ratio:.1%}, 높이 {height_ratio:.1%}, 면적 {area_ratio:.1%}"
                    )
                if focus in {"source_text", "mixed"}:
                    if (
                        height_ratio < TEXT_FOREGROUND_MIN_HEIGHT_RATIO
                        or area_ratio < TEXT_FOREGROUND_MIN_AREA_RATIO
                    ):
                        errors.append(
                            f"{scene_id} 텍스트 증거가 모바일 화면에서 너무 작습니다: "
                            f"높이 {height_ratio:.1%}, 면적 {area_ratio:.1%}"
                        )
                    if not review.get("evidence_readable"):
                        errors.append(f"{scene_id} 텍스트 증거 가독성 승인이 필요합니다.")
                    if not review.get("visual_anchor_terms"):
                        errors.append(f"{scene_id} 텍스트 증거의 visual_anchor_terms가 필요합니다.")
        if person_visual_mode == PERSON_VISUAL_MODE:
            treatment = str(review.get("people_treatment") or "")
            if treatment not in PEOPLE_TREATMENTS:
                errors.append(f"{scene_id}에는 화면 속 사람 처리 검수가 필요합니다.")
            elif role == "editorial_animation" and treatment != "editorial_animation":
                errors.append(f"{scene_id} 공개 인물 파생본은 editorial_animation 처리여야 합니다.")
            elif role == "non_identifying_fallback" and treatment != "non_identifying":
                errors.append(f"{scene_id} 비식별 대체 화면은 non_identifying 처리여야 합니다.")
            elif role not in {"editorial_animation", "non_identifying_fallback"} and treatment not in {
                "none_visible",
                "cropped_out",
            }:
                errors.append(f"{scene_id} 실제 자료의 사람은 표시 화면에서 크롭 제거해야 합니다.")
            if treatment in {"none_visible", "cropped_out"} and review.get("people_visible"):
                errors.append(f"{scene_id} 사람 제거 처리 뒤에도 사람이 보인다고 기록되어 있습니다.")

        synthetic = bool(record.get("synthetic"))
        if synthetic and role not in {"editorial_animation", "non_identifying_fallback"}:
            errors.append(f"{scene_id} 합성 이미지는 실제 사건·공식 자료라고 표시할 수 없습니다.")
        if not synthetic and role in {"editorial_animation", "non_identifying_fallback"}:
            errors.append(f"{scene_id} {role}은 합성·비식별 파생 이미지여야 합니다.")
        if not synthetic and record.get("visual_text") != "source_original":
            errors.append(f"{scene_id} 실제 자료는 visual_text=source_original이어야 합니다.")
        if role == "source_photo":
            errors.append(f"{scene_id} source_photo는 출처 보존용이며 화면에 직접 사용할 수 없습니다.")
        if (
            not synthetic
            and record.get("person_class") == "public_figure"
            and record.get("media_type") == "image"
            and role == "context"
        ):
            errors.append(
                f"{scene_id} 공개 인물 신원 사진은 실제 원본에서 만든 editorial_animation 파생본을 사용해야 합니다."
            )
        if str(record.get("person_class") or "") in PRIVATE_PERSON_CLASSES:
            if str(record.get("portrait_eye_motif") or ""):
                errors.append(f"{scene_id} 비공개 인물은 눈가림 바만으로 비식별 처리할 수 없습니다.")
            review = record.get("review") if isinstance(record.get("review"), dict) else {}
            if not review.get("non_identifying"):
                errors.append(f"{scene_id} 비공개 인물·미성년자·피해자는 비식별 화면만 사용할 수 있습니다.")

        if role == "non_identifying_fallback":
            if str(record.get("portrait_eye_motif") or ""):
                errors.append(f"{scene_id} 비식별 대체 화면에는 editorial ruler eye-band를 사용할 수 없습니다.")
            if not str(record.get("fallback_reason") or "").strip():
                errors.append(f"{scene_id} 비식별 대체 화면에는 fallback_reason이 필요합니다.")
            warnings.append(f"{scene_id}는 직접 자료 대신 비식별 대체 화면을 사용합니다.")

        if role == "editorial_animation":
            if record.get("person_class") != "public_figure":
                errors.append(f"{scene_id} editorial_animation은 공개 인물에만 사용할 수 있습니다.")
            if record.get("portrait_style") != PORTRAIT_STYLE:
                errors.append(f"{scene_id} 공개 인물 화풍은 {PORTRAIT_STYLE}이어야 합니다.")
            portrait_review = record.get("portrait_review")
            if not isinstance(portrait_review, dict) or not all(
                portrait_review.get(key)
                for key in ("identity_preserved", "clothing_preserved", "context_preserved")
            ):
                errors.append(f"{scene_id} 공개 인물 파생본은 신원·의상·사실 맥락 보존 검수가 필요합니다.")
            if review.get("non_identifying"):
                errors.append(f"{scene_id} editorial ruler eye-band는 비식별 처리로 기록할 수 없습니다.")
            if public_figure_style_mode == PUBLIC_FIGURE_STYLE_MODE:
                if record.get("portrait_style_strength") != PORTRAIT_STYLE_STRENGTH:
                    errors.append(f"{scene_id} 공개 인물 화풍 강도가 명확한 editorial 기준이 아닙니다.")
                if record.get("portrait_eye_motif") != PORTRAIT_EYE_MOTIF:
                    errors.append(f"{scene_id} 공개 인물 editorial ruler eye-band가 없습니다.")
                if not isinstance(portrait_review, dict) or not all(
                    portrait_review.get(key)
                    for key in (
                        "style_obvious_at_preview",
                        "eye_motif_present",
                        "ruler_ticks_visible",
                        "eye_motif_editorial_only",
                    )
                ):
                    errors.append(
                        f"{scene_id} 화풍 강도·눈가림 눈금·권리 효과 없음 검수가 필요합니다."
                    )
            parent_id = str(record.get("derived_from") or "")
            parent = records.get(parent_id)
            if not isinstance(parent, dict):
                errors.append(f"{scene_id} editorial_animation의 실제 인물 원본을 찾을 수 없습니다.")
            else:
                allowed_parent_roles = {"source_photo", "official_evidence", "source_capture"}
                if parent.get("synthetic") or parent.get("evidence_role") not in allowed_parent_roles:
                    errors.append(
                        f"{scene_id} editorial_animation은 검수된 실제 인물 자료에서 한 번만 파생해야 합니다."
                    )
                if parent.get("person_class") != "public_figure" or parent.get("media_type") != "image":
                    errors.append(f"{scene_id} editorial_animation 원본은 공개 인물 실제 사진이어야 합니다.")
                validate_reviewed_record(
                    parent,
                    label=f"{scene_id} 원본 {parent_id}",
                    required_fact_ids=scene_fact_ids,
                )

    non_evidence_roles = {"context", "editorial_animation", "non_identifying_fallback"}
    non_evidence_count = sum(role in non_evidence_roles for role in unique_roles.values())
    if unique_roles and non_evidence_count > len(unique_roles) / 2:
        warnings.append(
            "고유 화면의 절반 이상이 직접 사건 자료가 아닌 맥락·인물 파생·대체 화면입니다."
        )
    return errors, warnings


def validate_assets(project_dir: Path) -> tuple[list[str], list[str]]:
    errors, warnings = validate_research(project_dir)
    project = read_json(project_dir / "project.json") if (project_dir / "project.json").is_file() else {}
    storyboard = read_json(project_dir / "storyboard.json")
    manifest = load_manifest(project_dir)
    pacing_mode = str(storyboard.get("pacing_mode") or "").strip()
    if pacing_mode not in SUPPORTED_PACING_MODES:
        errors.append(f"지원하지 않는 pacing_mode입니다: {pacing_mode}")
    narration_hold = pacing_mode == NARRATION_HOLD_MODE
    narration_performance_mode = str(
        storyboard.get("narration_performance_mode") or ""
    ).strip()
    if narration_performance_mode not in SUPPORTED_NARRATION_PERFORMANCE_MODES:
        errors.append(
            f"지원하지 않는 narration_performance_mode입니다: {narration_performance_mode}"
        )
    caption_sync_mode = str(storyboard.get("caption_sync_mode") or "").strip()
    if caption_sync_mode not in SUPPORTED_CAPTION_SYNC_MODES:
        errors.append(f"지원하지 않는 caption_sync_mode입니다: {caption_sync_mode}")
    caption_sync = caption_sync_mode == CAPTION_SYNC_MODE
    visual_validation_mode = str(storyboard.get("visual_validation_mode") or "").strip()
    if visual_validation_mode not in SUPPORTED_VISUAL_VALIDATION_MODES:
        errors.append(f"지원하지 않는 visual_validation_mode입니다: {visual_validation_mode}")
    evidence_first = visual_validation_mode == EVIDENCE_FIRST_MODE
    display_validation_mode = str(storyboard.get("display_validation_mode") or "").strip()
    if display_validation_mode not in SUPPORTED_DISPLAY_VALIDATION_MODES:
        errors.append(f"지원하지 않는 display_validation_mode입니다: {display_validation_mode}")
    final_visual_review_mode = str(storyboard.get("final_visual_review_mode") or "").strip()
    if final_visual_review_mode not in SUPPORTED_FINAL_VISUAL_REVIEW_MODES:
        errors.append(
            f"지원하지 않는 final_visual_review_mode입니다: {final_visual_review_mode}"
        )
    person_visual_mode = str(storyboard.get("person_visual_mode") or "").strip()
    if person_visual_mode not in SUPPORTED_PERSON_VISUAL_MODES:
        errors.append(f"지원하지 않는 person_visual_mode입니다: {person_visual_mode}")
    public_figure_style_mode = str(
        storyboard.get("public_figure_style_mode") or ""
    ).strip()
    if public_figure_style_mode not in SUPPORTED_PUBLIC_FIGURE_STYLE_MODES:
        errors.append(
            f"지원하지 않는 public_figure_style_mode입니다: {public_figure_style_mode}"
        )
    person_motion_mode = str(storyboard.get("person_motion_mode") or "").strip()
    if person_motion_mode not in SUPPORTED_PERSON_MOTION_MODES:
        errors.append(f"지원하지 않는 person_motion_mode입니다: {person_motion_mode}")
    title = storyboard.get("title") or {}
    for key, label in (("white", "흰색 제목"), ("yellow", "노란색 제목")):
        value = str(title.get(key) or "").strip()
        if not value:
            errors.append(f"{label}이 비어 있습니다.")
        elif len(value) > 16:
            errors.append(f"{label}은 16자 이하여야 합니다: {value}")
    if not str(storyboard.get("message") or "").strip():
        errors.append("영상의 단일 핵심 메시지가 비어 있습니다.")

    beats = storyboard.get("beats")
    if not isinstance(beats, list) or not 7 <= len(beats) <= 10:
        errors.append("대본은 7~10개의 의미 단위여야 합니다.")
        beats = []
    beat_ids = set()
    for beat in beats:
        beat_id = str(beat.get("id") or "")
        if not beat_id or beat_id in beat_ids:
            errors.append("각 대본 의미 단위에는 고유 ID가 필요합니다.")
        beat_ids.add(beat_id)
        narration = str(beat.get("narration") or "").strip()
        if not narration:
            errors.append(f"대본 의미 단위 {beat_id or '?'}의 narration이 비어 있습니다.")
        elif uses_formal_narration_ending(narration):
            errors.append(
                f"대본 의미 단위 {beat_id or '?'}는 친구 설명형 구어체여야 하며 합니다/했습니다 종결을 사용할 수 없습니다."
            )
    errors.extend(validate_narration_flow(storyboard, beats))

    scenes = storyboard.get("scenes")
    if not isinstance(scenes, list) or len(scenes) != SCENE_COUNT:
        errors.append("스토리보드는 정확히 15장면이어야 합니다.")
        scenes = []
    asset_records = {item.get("id"): item for item in manifest.get("assets", [])}
    used_assets: dict[str, int] = {}
    beat_assets: dict[str, str] = {}
    finished_beats: set[str] = set()
    previous_beat_id = ""
    total_duration = 0.0
    sfx_count = 0
    for index, scene in enumerate(scenes, start=1):
        expected_id = f"scene-{index:02d}"
        if scene.get("id") != expected_id:
            errors.append(f"장면 {index}의 ID는 {expected_id}여야 합니다.")
        duration = float(scene.get("duration") or 0)
        total_duration += duration
        max_duration = HOLD_SCENE_MAX_SECONDS if narration_hold else LEGACY_SCENE_MAX_SECONDS
        if not 1.0 <= duration <= max_duration:
            errors.append(f"{expected_id} 길이는 1~{max_duration:g}초 범위여야 합니다.")
        beat_id = str(scene.get("beat_id") or "")
        if beat_id not in beat_ids:
            errors.append(f"{expected_id}의 beat_id가 대본 의미 단위와 연결되지 않습니다.")
        if narration_hold and beat_id != previous_beat_id:
            if beat_id in finished_beats:
                errors.append(f"{expected_id}의 beat_id가 비연속으로 다시 등장합니다: {beat_id}")
            if previous_beat_id:
                finished_beats.add(previous_beat_id)
            previous_beat_id = beat_id
        scene_narration = str(scene.get("narration") or "").strip()
        if scene_narration and uses_formal_narration_ending(scene_narration):
            errors.append(
                f"{expected_id} narration은 친구 설명형 구어체여야 하며 합니다/했습니다 종결을 사용할 수 없습니다."
            )
        caption = str(scene.get("caption") or "")
        if index > 1 and not caption.strip():
            errors.append(f"{expected_id}의 하단 자막이 비어 있습니다.")
        if caption.count("\n") > 1:
            errors.append(f"{expected_id}의 하단 자막은 최대 2줄이어야 합니다.")
        caption_anchor = str(scene.get("caption_anchor") or "").strip()
        if caption_sync and index == 1:
            if caption.strip() or caption_anchor:
                errors.append("scene-01은 고정 상단 제목만 사용하며 하단 자막·caption_anchor를 비워야 합니다.")
        elif caption_sync and index > 1:
            if not scene_narration:
                errors.append(f"{expected_id}의 자막 동기화용 narration이 비어 있습니다.")
            if not caption_anchor:
                errors.append(f"{expected_id}의 caption_anchor가 비어 있습니다.")
            else:
                normalized_anchor = normalize_caption_match(caption_anchor)
                if not normalized_anchor:
                    errors.append(f"{expected_id}의 caption_anchor는 글자나 숫자를 포함해야 합니다.")
                elif normalized_anchor not in normalize_caption_match(scene_narration):
                    errors.append(f"{expected_id} caption_anchor가 현재 narration에 없습니다: {caption_anchor}")
                if normalized_anchor and normalized_anchor not in normalize_caption_match(caption):
                    errors.append(f"{expected_id} caption_anchor가 현재 caption에 없습니다: {caption_anchor}")
                anchor_word_index = caption_anchor_word_index(scene_narration, caption_anchor)
                if normalized_anchor and anchor_word_index not in (0, 1):
                    errors.append(
                        f"{expected_id} caption_anchor는 narration 첫 두 어절 안에서 시작해야 합니다: "
                        f"{caption_anchor}"
                    )
                if normalized_anchor and not normalize_caption_match(caption).startswith(
                    normalized_anchor
                ):
                    errors.append(
                        f"{expected_id} caption은 opening caption_anchor로 시작해야 합니다: "
                        f"{caption_anchor}"
                    )
            narration_tokens = normalized_word_tokens(scene_narration)
            caption_tokens = normalized_word_tokens(caption)
            if narration_tokens and caption_tokens and narration_tokens[-1] != caption_tokens[-1]:
                errors.append(
                    f"{expected_id} caption은 narration의 마지막 연결어·종결어를 유지해야 합니다: "
                    f"{narration_tokens[-1]}"
                )
            caption_hard_max = (
                HUMANIZED_CAPTION_HARD_MAX_SECONDS
                if narration_performance_mode == NARRATION_PERFORMANCE_MODE
                else CAPTION_HARD_MAX_SECONDS
            )
            if duration > caption_hard_max:
                errors.append(f"{expected_id} 자막은 {caption_hard_max:g}초를 넘을 수 없습니다.")
            elif duration > CAPTION_TARGET_MAX_SECONDS:
                warnings.append(
                    f"{expected_id} 자막은 권장 {CAPTION_TARGET_MAX_SECONDS:g}초보다 깁니다: {duration:.3f}초"
                )
            elif duration < CAPTION_TARGET_MIN_SECONDS:
                warnings.append(
                    f"{expected_id} 자막은 권장 {CAPTION_TARGET_MIN_SECONDS:g}초보다 짧습니다: {duration:.3f}초"
                )
        asset_id = str(scene.get("asset_id") or "")
        if not asset_id or asset_id not in asset_records:
            errors.append(f"{expected_id}의 asset_id가 에셋 목록과 연결되지 않습니다.")
        else:
            previous = scenes[index - 2] if index > 1 else None
            is_hold_follower = (
                narration_hold
                and previous is not None
                and beat_id == str(previous.get("beat_id") or "")
            )
            if narration_hold:
                expected_asset = beat_assets.get(beat_id)
                if expected_asset is None:
                    if asset_id in used_assets:
                        errors.append(f"{expected_id}가 다른 beat의 에셋을 반복합니다: {asset_id}")
                    beat_assets[beat_id] = asset_id
                    used_assets[asset_id] = index
                elif asset_id != expected_asset:
                    errors.append(f"{expected_id}는 같은 beat의 asset_id를 유지해야 합니다: {expected_asset}")
                if is_hold_follower and str(scene.get("sfx") or "").strip():
                    errors.append(f"{expected_id} 홀드 후속 장면에는 SFX를 배치할 수 없습니다.")
            else:
                if asset_id in used_assets:
                    errors.append(f"{expected_id}가 이미 사용한 에셋을 반복합니다: {asset_id}")
                used_assets[asset_id] = index
            record = asset_records[asset_id]
            if record.get("synthetic") and record.get("visual_text") != "none":
                errors.append(
                    f"{expected_id}의 합성 에셋은 편집 문구가 없는 text-free 확인이 필요합니다: {asset_id}"
                )
            try:
                normalized = project_path(project_dir, str(record.get("normalized_path") or ""))
                if normalized.suffix.lower() != ".png":
                    errors.append(f"{asset_id} 정규화 파일은 PNG여야 합니다.")
                elif pillow_available():
                    from PIL import Image

                    with Image.open(normalized) as image:
                        if image.size != (CANVAS_WIDTH, CANVAS_HEIGHT):
                            errors.append(f"{asset_id} 정규화 크기가 1080x1920이 아닙니다.")
            except CCHelperError as exc:
                errors.append(str(exc))
        if str(scene.get("sfx") or "").strip():
            sfx_count += 1
            sfx_path = project_dir / "assets" / "sfx" / f"{scene['sfx']}.wav"
            if not sfx_path.is_file():
                errors.append(f"효과음 프리셋 파일이 없습니다: {scene['sfx']}")
    if evidence_first:
        evidence_errors, evidence_warnings = validate_evidence_first_visuals(
            project_dir, storyboard, manifest
        )
        errors.extend(evidence_errors)
        warnings.extend(evidence_warnings)
    upload_errors, upload_warnings = validate_youtube_upload(
        project_dir, project, storyboard
    )
    errors.extend(upload_errors)
    warnings.extend(upload_warnings)
    if narration_performance_mode in SUPPORTED_NARRATION_PERFORMANCE_MODES:
        performance_errors, performance_warnings = validate_narration_performance(
            project_dir, project, storyboard
        )
        errors.extend(performance_errors)
        warnings.extend(performance_warnings)
    if narration_hold:
        beat_runs: list[tuple[str, int]] = []
        for scene in scenes:
            beat_id = str(scene.get("beat_id") or "")
            if beat_runs and beat_runs[-1][0] == beat_id:
                beat_runs[-1] = (beat_id, beat_runs[-1][1] + 1)
            else:
                beat_runs.append((beat_id, 1))
        expected_beat_order = [str(beat.get("id") or "") for beat in beats]
        if [beat_id for beat_id, _count in beat_runs] != expected_beat_order:
            errors.append("scene의 beat_id 구간 순서가 beats 배열 순서와 다릅니다.")
        for beat_id, count in beat_runs:
            if not 1 <= count <= 3:
                errors.append(f"{beat_id}는 1~3개의 연속 자막 슬롯을 사용해야 합니다: 현재 {count}개")
        if scenes and set(beat_assets) != beat_ids:
            missing = sorted(beat_ids - set(beat_assets))
            errors.append(f"모든 narration beat에는 연속된 시각 구간이 필요합니다: 누락 {missing}")
        if scenes and len(used_assets) != len(beat_ids):
            errors.append(
                f"narration-hold는 beat당 한 개의 시각 에셋을 사용해야 합니다: "
                f"beat {len(beat_ids)}개, 에셋 {len(used_assets)}개"
            )
        if caption_sync:
            for beat in beats:
                beat_id = str(beat.get("id") or "")
                linked_narration = " ".join(
                    str(scene.get("narration") or "").strip()
                    for scene in scenes
                    if scene.get("beat_id") == beat_id
                )
                if normalize_caption_match(linked_narration) != normalize_caption_match(
                    beat.get("narration")
                ):
                    errors.append(
                        f"{beat_id}의 scene narration을 합친 내용이 실제 beat narration과 다릅니다."
                    )
        times = scene_times(storyboard) if scenes else []
        errors.extend(validate_narration_timing(project_dir, project, storyboard, times))
        audio = project.get("narration_audio") if isinstance(project, dict) else None
        if not isinstance(audio, dict) or not str(audio.get("path") or "").strip():
            if not 30.0 <= total_duration <= 45.0:
                errors.append(f"음원 없는 전체 길이는 30~45초여야 합니다: {total_duration:.3f}초")
    elif not 30.0 <= total_duration <= 45.0:
        errors.append(f"전체 길이는 30~45초여야 합니다: {total_duration:.3f}초")
    if scenes and not 5 <= sfx_count <= 8:
        warnings.append(f"효과음 큐는 5~8개가 권장됩니다: 현재 {sfx_count}개")
    if any(item.get("rights_status") == "unreviewed" for item in asset_records.values()):
        warnings.append("권리 미검토 에셋이 있어 결과는 local_review_only 상태입니다.")
    return errors, warnings


def set_text_material(material: dict[str, Any], text: str) -> None:
    try:
        content = json.loads(material.get("content") or "{}")
    except json.JSONDecodeError:
        content = {"styles": []}
    content["text"] = text
    for style in content.get("styles", []):
        if isinstance(style, dict) and isinstance(style.get("range"), list):
            style["range"] = [0, len(text)]
    material["content"] = json.dumps(content, ensure_ascii=False, separators=(",", ":"))


def text_material_value(material: dict[str, Any]) -> str:
    try:
        content = json.loads(material.get("content") or "{}")
    except json.JSONDecodeError:
        return ""
    return str(content.get("text") or "")


def scene_times(storyboard: dict[str, Any]) -> list[dict[str, int]]:
    result = []
    narration_hold = storyboard.get("pacing_mode") == NARRATION_HOLD_MODE
    start = 0
    frame_start = 0
    requested_end = 0.0
    for scene in storyboard["scenes"]:
        if narration_hold:
            requested_end += float(scene["duration"])
            frame_end = max(frame_start + 1, int(math.ceil(requested_end * 30.0 - 1e-9)))
            start = frame_start * 1_000_000 // 30
            end = frame_end * 1_000_000 // 30
            result.append({"start": start, "duration": end - start})
            frame_start = frame_end
        else:
            duration = int(round(float(scene["duration"]) * 1_000_000))
            result.append({"start": start, "duration": duration})
            start += duration
    return result


def build_content_mappings(
    draft: dict[str, Any],
    storyboard: dict[str, Any],
    manifest: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    parts = find_template_parts(draft)
    assets = {item["id"]: item for item in manifest["assets"]}
    times = scene_times(storyboard)
    narration_hold = storyboard.get("pacing_mode") == NARRATION_HOLD_MODE
    scene_mappings: list[dict[str, Any]] = []
    for index, (segment, scene, timing) in enumerate(
        zip(parts["scene_segments"], storyboard["scenes"], times), start=1
    ):
        material = parts["videos"][segment["material_id"]]
        asset = assets[scene["asset_id"]]
        previous_scene = storyboard["scenes"][index - 2] if index > 1 else None
        hold_previous = (
            narration_hold
            and previous_scene is not None
            and scene.get("beat_id") == previous_scene.get("beat_id")
        )
        if hold_previous:
            target_relative_path = scene_mappings[-1]["target_relative_path"]
            hold_source_scene_id = scene_mappings[-1]["scene_id"]
        else:
            target_relative_path = f"cc-helper-assets/visuals/scene-{index:02d}.png"
            hold_source_scene_id = ""
        scene_mappings.append(
            {
                "scene_id": scene["id"],
                "beat_id": scene.get("beat_id", ""),
                "segment_id": segment["id"],
                "material_id": segment["material_id"],
                "old_path": material.get("path", ""),
                "asset_id": asset["id"],
                "source_path": asset["normalized_path"],
                "target_relative_path": target_relative_path,
                "hold_source_scene_id": hold_source_scene_id,
                "template_segment_visual": visual_values(segment),
                "template_material_visual": visual_values(material),
                "start_us": timing["start"],
                "duration_us": timing["duration"],
                "caption": scene.get("caption", ""),
                "caption_anchor": scene.get("caption_anchor", ""),
                "sfx": scene.get("sfx", ""),
            }
        )
    title_mappings = [
        {
            "segment_id": segment["id"],
            "material_id": segment["material_id"],
            "value": storyboard["title"][key],
        }
        for segment, key in zip(parts["title_segments"], ("white", "yellow"))
    ]
    caption_mappings = [
        {
            "segment_id": segment["id"],
            "material_id": segment["material_id"],
            "value": scene["caption"],
            "start_us": timing["start"],
            "duration_us": timing["duration"],
        }
        for segment, scene, timing in zip(
            parts["caption_segments"], storyboard["scenes"][1:], times[1:]
        )
    ]
    return scene_mappings, title_mappings, caption_mappings


def attach_template_mini_visuals(
    template_root: Path,
    scene_mappings: list[dict[str, Any]],
) -> None:
    mini_paths = active_mini_draft_paths(template_root)
    if not mini_paths:
        raise CCHelperError("base template mini_draft.json을 찾을 수 없습니다.")
    expected_snapshots: dict[str, tuple[str, str]] | None = None
    selected_segments: dict[str, dict[str, Any]] = {}
    for path in mini_paths:
        payload = read_json(path)
        segments = {
            segment.get("id"): segment
            for segment in (payload.get("mini_draft_data") or {}).get("segments", [])
            if isinstance(segment, dict) and segment.get("id")
        }
        current_snapshots: dict[str, tuple[str, str]] = {}
        for item in scene_mappings:
            segment_id = str(item.get("segment_id") or "")
            segment = segments.get(segment_id)
            if not isinstance(segment, dict) or not isinstance(segment.get("material"), dict):
                raise CCHelperError(f"base template mini scene을 찾을 수 없습니다: {segment_id}")
            current_snapshots[segment_id] = (
                visual_value_snapshot(segment),
                visual_value_snapshot(segment["material"]),
            )
        if expected_snapshots is None:
            expected_snapshots = current_snapshots
            selected_segments = segments
        elif current_snapshots != expected_snapshots:
            raise CCHelperError("base template mini_draft geometry mirror가 서로 다릅니다.")
    for item in scene_mappings:
        segment = selected_segments[str(item["segment_id"])]
        item["template_mini_segment_visual"] = visual_values(segment)
        item["template_mini_material_visual"] = visual_values(segment["material"])


def existing_clone_destination(
    project_dir: Path,
    project: dict[str, Any],
    capcut_root: Path,
    base_draft: Path,
) -> tuple[Path, dict[str, Any]] | None:
    capcut = project.get("capcut") if isinstance(project.get("capcut"), dict) else {}
    previous_mapping: dict[str, Any] = {}
    mapping_path = project_dir / "capcut-map.json"
    if mapping_path.is_file():
        previous_mapping = read_json(mapping_path)

    candidate_names: list[str] = []
    active_name = str(capcut.get("active_destination_name") or "").strip()
    if active_name:
        candidate_names.append(active_name)
    if previous_mapping.get("status") == "cloned":
        mapped_path = Path(str(previous_mapping.get("destination_path") or ""))
        if mapped_path.name:
            candidate_names.append(mapped_path.name)
    configured_name = str(capcut.get("destination_name") or "").strip()
    if configured_name:
        candidate_names.append(configured_name)

    seen: set[str] = set()
    root = capcut_root.resolve()
    base = base_draft.resolve()
    for name in candidate_names:
        if name in seen:
            continue
        seen.add(name)
        if Path(name).name != name or name in {".", ".."}:
            raise CCHelperError("기존 CapCut 목적지 이름은 단일 폴더명이어야 합니다.")
        destination = (root / name).resolve()
        if destination.parent != root or destination == base:
            raise CCHelperError("기존 CapCut 목적지가 안전한 복제 경로가 아닙니다.")
        if destination.is_dir() and not destination.is_symlink():
            return destination, previous_mapping
    return None


def prepare_capcut(args: argparse.Namespace) -> None:
    if not args.dry_run:
        raise CCHelperError("prepare-capcut은 --dry-run과 함께 실행해야 합니다.")
    project_dir = Path(args.project_dir).expanduser().resolve()
    base_draft = Path(args.base_draft).expanduser().resolve()
    capcut_root = Path(args.capcut_root).expanduser().resolve()
    errors, warnings = validate_assets(project_dir)
    if errors:
        raise CCHelperError("에셋 단계 검증 실패:\n- " + "\n- ".join(errors))
    template = read_json(base_draft / "draft_info.json")
    find_template_parts(template)
    project = read_json(project_dir / "project.json")
    storyboard = read_json(project_dir / "storyboard.json")
    manifest = load_manifest(project_dir)
    capcut = project.get("capcut") if isinstance(project.get("capcut"), dict) else {}
    existing = existing_clone_destination(
        project_dir,
        project,
        capcut_root,
        base_draft,
    )
    reuse_existing = existing is not None
    previous_mapping: dict[str, Any] = {}
    if existing:
        destination, previous_mapping = existing
        destination_name = destination.name
        if args.destination_name and args.destination_name != destination_name:
            warnings.append(
                f"기존 CapCut 복제본 {destination_name}을 계속 사용합니다. "
                f"새 목적지 {args.destination_name}은 생성하지 않습니다."
            )
        meta = read_json(destination / "draft_meta_info.json")
        draft_name = args.draft_name or str(meta.get("draft_name") or destination_name)
        capcut["destination_name"] = destination_name
        capcut["active_destination_name"] = destination_name
        capcut["reuse_policy"] = CAPCUT_CLONE_REUSE_POLICY
        capcut["draft_name"] = draft_name
        project["capcut"] = capcut
        write_json(project_dir / "project.json", project)
    else:
        destination_name = args.destination_name or str(capcut.get("destination_name") or "")
        if Path(destination_name).name != destination_name or destination_name in {"", ".", ".."}:
            raise CCHelperError("목적지 이름은 단일 폴더명이어야 합니다.")
        destination = capcut_root / destination_name
        if destination.exists():
            raise CCHelperError(f"목적지 CapCut 경로를 안전하게 재사용할 수 없습니다: {destination}")
        draft_name = args.draft_name or str(capcut.get("draft_name") or destination_name)
    scene_mappings, title_mappings, caption_mappings = build_content_mappings(
        template, storyboard, manifest
    )
    attach_template_mini_visuals(base_draft, scene_mappings)
    attach_person_motion_plans(scene_mappings, storyboard, manifest)
    mapping = {
        "version": VERSION,
        "status": "cloned" if reuse_existing else "prepared",
        "prepared_at": now_iso(),
        "reuse_policy": CAPCUT_CLONE_REUSE_POLICY,
        "reuse_existing": reuse_existing,
        "project_dir": str(project_dir),
        "base_draft": str(base_draft),
        "base_tree_sha256": tree_hash(base_draft),
        "geometry_mode": "base-template-snapshot",
        "template_geometry_source_sha256": sha256_file(base_draft / "draft_info.json"),
        "person_motion_mode": storyboard.get("person_motion_mode", ""),
        "capcut_root": str(capcut_root),
        "destination_name": destination_name,
        "destination_path": str(destination),
        "draft_name": draft_name,
        "total_duration_us": sum(item["duration_us"] for item in scene_mappings),
        "scene_mappings": scene_mappings,
        "title_mappings": title_mappings,
        "caption_mappings": caption_mappings,
        "capcut_running": capcut_running(),
        "next_action": "retime-capcut --confirm-existing" if reuse_existing else "clone-capcut --confirm",
        "warnings": warnings,
    }
    if reuse_existing:
        previous_destination = Path(str(previous_mapping.get("destination_path") or ""))
        if previous_destination.resolve() == destination.resolve():
            for key in ("draft_id", "cloned_at"):
                if previous_mapping.get(key):
                    mapping[key] = previous_mapping[key]
        if not mapping.get("draft_id"):
            mapping["draft_id"] = read_json(destination / "draft_meta_info.json").get("draft_id")
    write_json(project_dir / "capcut-map.json", mapping)
    build_handoff(project_dir, storyboard, manifest)
    print_json(mapping)


def format_srt_time(microseconds: int) -> str:
    milliseconds = microseconds // 1000
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"


def write_youtube_upload_handoff(
    project_dir: Path,
    project: dict[str, Any],
    storyboard: dict[str, Any],
) -> None:
    if project.get("youtube_upload_mode") != YOUTUBE_UPLOAD_MODE:
        return
    upload = copy.deepcopy(project.get("youtube_upload") or {})
    research = read_json(project_dir / "research.json")
    source_ids = {str(item) for item in upload.get("source_ids", [])}
    sources = [
        {
            "id": str(item.get("id") or ""),
            "publisher": str(item.get("publisher") or ""),
            "title": str(item.get("title") or ""),
            "url": str(item.get("url") or ""),
        }
        for item in research.get("sources", [])
        if isinstance(item, dict) and str(item.get("id") or "") in source_ids
    ]
    payload = {
        "version": VERSION,
        "status": upload.get("status"),
        "publish_blocked": bool(project.get("publish_blocked")),
        "project_status": str(project.get("status") or ""),
        "title": str(upload.get("title") or ""),
        "description": str(upload.get("description") or ""),
        "hashtags": upload.get("hashtags") or [],
        "tags": upload.get("tags") or [],
        "pinned_comment": str(upload.get("pinned_comment") or ""),
        "category": str(upload.get("category") or ""),
        "language": str(upload.get("language") or ""),
        "audience": str(upload.get("audience") or ""),
        "altered_content": bool(upload.get("altered_content")),
        "altered_content_reason": str(upload.get("altered_content_reason") or ""),
        "recommended_visibility": str(upload.get("recommended_visibility") or ""),
        "thumbnail": upload.get("thumbnail") or {},
        "sources": sources,
    }
    handoff = project_dir / "handoff"
    write_json(handoff / "youtube-upload.json", payload)
    thumbnail = payload["thumbnail"] if isinstance(payload["thumbnail"], dict) else {}
    source_lines = [
        f"- {item['publisher']} | {item['title']} | {item['url']}" for item in sources
    ] or ["- 대표 출처 미기록"]
    markdown = [
        "# 유튜브 업로드 정보",
        "",
        "## 게시 전 상태",
        "",
        f"- 프로젝트 상태: `{payload['project_status']}`",
        f"- 게시 차단: `{'true' if payload['publish_blocked'] else 'false'}`",
        f"- 권장 공개 범위: `{payload['recommended_visibility']}`",
        "",
        "## 제목",
        "",
        payload["title"],
        "",
        "## 설명",
        "",
        payload["description"],
        "",
        "## 해시태그",
        "",
        " ".join(str(item) for item in payload["hashtags"]),
        "",
        "## 검색 태그",
        "",
        ", ".join(str(item) for item in payload["tags"]),
        "",
        "## 고정댓글",
        "",
        payload["pinned_comment"],
        "",
        "## 업로드 설정",
        "",
        f"- 카테고리: `{payload['category']}`",
        f"- 언어: `{payload['language']}`",
        f"- 시청자층: `{payload['audience']}`",
        f"- 변형·합성 콘텐츠: `{'yes' if payload['altered_content'] else 'no'}`",
        f"- 변형 사유: {payload['altered_content_reason'] or '-'}",
        "",
        "## 썸네일 문구",
        "",
        f"- 흰색: {thumbnail.get('white', '')}",
        f"- 노란색: {thumbnail.get('yellow', '')}",
        "",
        "## 대표 출처",
        "",
        *source_lines,
        "",
        "> 이 파일은 복사용 편집 인계입니다. publish_blocked=true이면 권리 검토 전 게시하지 않습니다.",
        "",
    ]
    (handoff / "youtube-upload.md").write_text("\n".join(markdown), encoding="utf-8")


def build_handoff(
    project_dir: Path,
    storyboard: dict[str, Any],
    manifest: dict[str, Any],
) -> None:
    handoff = project_dir / "handoff"
    handoff.mkdir(parents=True, exist_ok=True)
    beats = storyboard.get("beats", [])
    (handoff / "narration.txt").write_text(
        "\n".join(str(item.get("narration") or "").strip() for item in beats) + "\n",
        encoding="utf-8",
    )
    times = scene_times(storyboard)
    srt_lines = []
    sequence = 1
    for scene, timing in zip(storyboard["scenes"][1:], times[1:]):
        caption = str(scene.get("caption") or "").strip()
        if not caption:
            continue
        srt_lines.extend(
            [
                str(sequence),
                f"{format_srt_time(timing['start'])} --> {format_srt_time(timing['start'] + timing['duration'])}",
                caption,
                "",
            ]
        )
        sequence += 1
    (handoff / "captions.srt").write_text("\n".join(srt_lines), encoding="utf-8")

    with (handoff / "sfx-cues.csv").open("w", encoding="utf-8", newline="") as output:
        writer = csv.writer(output)
        writer.writerow(["start_seconds", "scene_id", "cue", "file"])
        for scene, timing in zip(storyboard["scenes"], times):
            cue = str(scene.get("sfx") or "").strip()
            if cue:
                writer.writerow(
                    [f"{timing['start'] / 1_000_000:.3f}", scene["id"], cue, f"assets/sfx/{cue}.wav"]
                )

    assets = {item.get("id"): item for item in manifest.get("assets", [])}
    with (handoff / "replace-with-video.csv").open("w", encoding="utf-8", newline="") as output:
        writer = csv.writer(output)
        writer.writerow(["scene_id", "asset_id", "video_file", "instruction"])
        for scene in storyboard["scenes"]:
            asset = assets.get(scene.get("asset_id"), {})
            if asset.get("media_type") == "video":
                writer.writerow(
                    [scene["id"], asset["id"], asset.get("source_path", ""), "대표 프레임을 원본 영상으로 교체"]
                )

    project = read_json(project_dir / "project.json")
    write_youtube_upload_handoff(project_dir, project, storyboard)
    audio = project.get("narration_audio") if isinstance(project, dict) else None
    guide_lines = [
        "# cc_helper 편집 인계",
        "",
        "- 이 프로젝트는 권리 미검토 자료를 포함할 수 있는 로컬 검토 초안입니다.",
        "- 상단 흰색·노란색 제목과 하단 자막은 캡컷에서 편집할 수 있습니다.",
        "- `sfx-cues.csv`의 시간에 맞춰 효과음을 배치하세요.",
        "- `replace-with-video.csv`가 있으면 해당 대표 프레임을 원본 영상으로 교체하세요.",
        "- 복제된 초안 안의 효과음·원본 영상은 `cc-helper-assets/project-assets/`에 있습니다.",
        "- BGM 기본값은 없음입니다.",
        "- 유튜브 제목·설명·해시태그·고정댓글·업로드 설정은 `youtube-upload.md`를 사용하세요.",
    ]
    if isinstance(audio, dict) and str(audio.get("path") or "").strip():
        guide_lines.append(
            f"- 내레이션 음원 `{audio['path']}`은 타임라인 0초부터 배치합니다."
        )
        guide_lines.append("- `narration-timing.json`의 검토된 파형 타이밍을 사용합니다.")
    else:
        guide_lines.append("- 내레이션 음원은 사람이 추가합니다.")
    (handoff / "editing-guide.md").write_text("\n".join(guide_lines) + "\n", encoding="utf-8")


def update_timerange(container: dict[str, Any], key: str, start: int, duration: int) -> None:
    timerange = container.get(key)
    if isinstance(timerange, dict):
        timerange["start"] = start
        timerange["duration"] = duration


def apply_root_draft(
    draft: dict[str, Any],
    mapping: dict[str, Any],
    final_destination: Path,
    *,
    relative_paths: bool = False,
) -> dict[str, str]:
    parts = find_template_parts(draft)
    replacements: dict[str, str] = {}
    scene_by_material = {item["material_id"]: item for item in mapping["scene_mappings"]}
    for material_id, item in scene_by_material.items():
        material = parts["videos"][material_id]
        template_material_visual = item.get("template_material_visual")
        if not isinstance(template_material_visual, dict):
            raise CCHelperError(f"{item.get('scene_id')} 템플릿 material geometry가 없습니다.")
        copy_visual_values(material, template_material_visual)
        old_path = str(material.get("path") or "")
        new_path = (
            item["target_relative_path"]
            if relative_paths
            else str(final_destination / item["target_relative_path"])
        )
        if old_path:
            replacements[old_path] = new_path
        material["path"] = new_path
        material["width"] = CANVAS_WIDTH
        material["height"] = CANVAS_HEIGHT

    scene_segment_by_id: dict[str, dict[str, Any]] = {}
    scene_material_by_id: dict[str, dict[str, Any]] = {}
    for segment, item in zip(parts["scene_segments"], mapping["scene_mappings"]):
        update_timerange(segment, "target_timerange", item["start_us"], item["duration_us"])
        update_timerange(segment, "source_timerange", 0, item["duration_us"])
        template_segment_visual = item.get("template_segment_visual")
        if not isinstance(template_segment_visual, dict):
            raise CCHelperError(f"{item.get('scene_id')} 템플릿 segment geometry가 없습니다.")
        copy_visual_values(segment, template_segment_visual)
        material = parts["videos"][segment["material_id"]]
        hold_source = str(item.get("hold_source_scene_id") or "")
        if hold_source and hold_source in scene_segment_by_id:
            copy_visual_values(segment, scene_segment_by_id[hold_source])
            copy_visual_values(material, scene_material_by_id[hold_source])
        scene_segment_by_id[item["scene_id"]] = segment
        scene_material_by_id[item["scene_id"]] = material
    for item in mapping["scene_mappings"]:
        plan = item.get("motion_plan")
        if isinstance(plan, dict):
            apply_motion_plan(
                scene_segment_by_id[item["scene_id"]], item["scene_id"], plan, mini=False
            )
    for segment, item in zip(parts["title_segments"], mapping["title_mappings"]):
        update_timerange(segment, "target_timerange", 0, mapping["total_duration_us"])
        set_text_material(parts["texts"][item["material_id"]], item["value"])
    for segment, item in zip(parts["caption_segments"], mapping["caption_mappings"]):
        update_timerange(segment, "target_timerange", item["start_us"], item["duration_us"])
        set_text_material(parts["texts"][item["material_id"]], item["value"])
    draft["duration"] = mapping["total_duration_us"]

    background_material_ids = []
    for track in draft.get("tracks", []):
        if track.get("type") == "video" and len(track.get("segments", [])) == 1:
            background_material_ids.append(track["segments"][0].get("material_id"))
    for material_id in background_material_ids:
        material = parts["videos"].get(material_id)
        if not material or not material.get("path"):
            continue
        old_path = str(material["path"])
        suffix = Path(old_path).suffix.lower() or ".png"
        name = "background-white" if "white" in Path(old_path).stem.lower() else "background-black"
        relative = f"cc-helper-assets/background/{name}{suffix}"
        new_path = relative if relative_paths else str(final_destination / relative)
        replacements[old_path] = new_path
        material["path"] = new_path
    return replacements


def update_mini_drafts(stage: Path, root_draft: dict[str, Any], mapping: dict[str, Any]) -> None:
    root_parts = find_template_parts(root_draft)
    text_by_segment: dict[str, str] = {}
    timing_by_segment: dict[str, tuple[int, int, bool]] = {}
    scene_item_by_segment: dict[str, dict[str, Any]] = {}
    scene_segment_by_scene_id: dict[str, str] = {}
    for segment, item in zip(root_parts["scene_segments"], mapping["scene_mappings"]):
        timing_by_segment[segment["id"]] = (item["start_us"], item["duration_us"], True)
        scene_item_by_segment[segment["id"]] = item
        scene_segment_by_scene_id[item["scene_id"]] = segment["id"]
    for segment, item in zip(root_parts["title_segments"], mapping["title_mappings"]):
        timing_by_segment[segment["id"]] = (0, mapping["total_duration_us"], False)
        text_by_segment[segment["id"]] = item["value"]
    for segment, item in zip(root_parts["caption_segments"], mapping["caption_mappings"]):
        timing_by_segment[segment["id"]] = (item["start_us"], item["duration_us"], False)
        text_by_segment[segment["id"]] = item["value"]

    for path in stage.rglob("mini_draft.json"):
        payload = read_json(path)
        data = payload.get("mini_draft_data") or {}
        draft = data.get("draft") or {}
        draft["duration"] = mapping["total_duration_us"]
        mini_by_id = {
            segment.get("id"): segment
            for segment in data.get("segments", [])
            if isinstance(segment, dict) and segment.get("id")
        }
        for segment in data.get("segments", []):
            segment_id = segment.get("id")
            timing = timing_by_segment.get(segment_id)
            if timing:
                start, duration, update_source = timing
                update_timerange(segment, "target_time_range", start, duration)
                if update_source:
                    update_timerange(segment, "source_time_range", 0, duration)
            scene_item = scene_item_by_segment.get(segment_id)
            if scene_item and isinstance(segment.get("material"), dict):
                template_segment_visual = scene_item.get("template_mini_segment_visual")
                template_material_visual = scene_item.get("template_mini_material_visual")
                if not isinstance(template_segment_visual, dict) or not isinstance(
                    template_material_visual, dict
                ):
                    raise CCHelperError(f"mini_draft 템플릿 geometry가 없습니다: {segment_id}")
                copy_visual_values(segment, template_segment_visual)
                copy_visual_values(segment["material"], template_material_visual)
                segment["material"]["path"] = str(
                    Path(mapping["destination_path"]) / scene_item["target_relative_path"]
                )
                segment["material"]["width"] = CANVAS_WIDTH
                segment["material"]["height"] = CANVAS_HEIGHT
            if segment_id in text_by_segment and isinstance(segment.get("material"), dict):
                text = text_by_segment[segment_id]
                set_text_material(segment["material"], text)
                segment["material"]["text"] = text
            if segment_id == mapping.get("narration_audio_segment_id"):
                duration = int(mapping.get("narration_audio_duration_us") or 0)
                if duration > 0:
                    update_timerange(segment, "target_time_range", 0, duration)
                    update_timerange(segment, "source_time_range", 0, duration)
                    if isinstance(segment.get("material"), dict):
                        segment["material"]["duration"] = duration
        for item in mapping["scene_mappings"]:
            hold_source = str(item.get("hold_source_scene_id") or "")
            if not hold_source:
                continue
            follower_id = scene_segment_by_scene_id.get(item["scene_id"])
            leader_id = scene_segment_by_scene_id.get(hold_source)
            follower = mini_by_id.get(follower_id)
            leader = mini_by_id.get(leader_id)
            if isinstance(follower, dict) and isinstance(leader, dict):
                copy_visual_values(follower, leader)
                if isinstance(follower.get("material"), dict) and isinstance(
                    leader.get("material"), dict
                ):
                    copy_visual_values(follower["material"], leader["material"])
        for item in mapping["scene_mappings"]:
            plan = item.get("motion_plan")
            segment = mini_by_id.get(item.get("segment_id"))
            if isinstance(plan, dict) and isinstance(segment, dict):
                apply_motion_plan(segment, item["scene_id"], plan, mini=True)
        write_json(path, payload)


def replace_text_in_tree(root: Path, replacements: dict[str, str]) -> None:
    replacements = {key: value for key, value in replacements.items() if key and key != value}
    if not replacements:
        return
    for path in (item for item in root.rglob("*") if item.is_file()):
        if path.stat().st_size > 25 * 1024 * 1024:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        updated = text
        for old, new in replacements.items():
            updated = updated.replace(old, new)
        if updated != text:
            path.write_text(updated, encoding="utf-8")


def copy_clone_assets(
    project_dir: Path,
    base_draft: Path,
    stage: Path,
    final_destination: Path,
    mapping: dict[str, Any],
) -> dict[str, str]:
    asset_root = stage / "cc-helper-assets"
    visual_root = asset_root / "visuals"
    background_root = asset_root / "background"
    handoff_root = asset_root / "handoff"
    visual_root.mkdir(parents=True, exist_ok=True)
    background_root.mkdir(parents=True, exist_ok=True)
    handoff_root.mkdir(parents=True, exist_ok=True)
    copied_visuals: dict[Path, Path] = {}
    for item in mapping["scene_mappings"]:
        source = project_path(project_dir, item["source_path"])
        target = visual_root / Path(item["target_relative_path"]).name
        previous_source = copied_visuals.get(target)
        if previous_source:
            if previous_source != source:
                raise CCHelperError(f"같은 홀드 대상에 서로 다른 에셋이 지정됐습니다: {target.name}")
            continue
        shutil.copy2(source, target)
        copied_visuals[target] = source
    for name in ("project.json", "research.json", "storyboard.json", "asset-manifest.json", "capcut-map.json"):
        shutil.copy2(project_dir / name, handoff_root / name)
    if (project_dir / "handoff").is_dir():
        shutil.copytree(project_dir / "handoff", handoff_root / "files", dirs_exist_ok=True)
    for relative in ("assets/source", "assets/videos", "assets/generated", "assets/sfx", "assets/audio"):
        source = project_dir / relative
        if source.is_dir():
            shutil.copytree(source, asset_root / "project-assets" / Path(relative).name, dirs_exist_ok=True)

    root_draft = read_json(base_draft / "draft_info.json")
    parts = find_template_parts(root_draft)
    replacements: dict[str, str] = {}
    for track in root_draft.get("tracks", []):
        if track.get("type") != "video" or len(track.get("segments", [])) != 1:
            continue
        material_id = track["segments"][0].get("material_id")
        material = parts["videos"].get(material_id)
        if not material:
            continue
        old_path = Path(str(material.get("path") or ""))
        if not old_path.is_file():
            raise CCHelperError(f"템플릿 배경 파일을 찾을 수 없습니다: {old_path}")
        suffix = old_path.suffix.lower() or ".png"
        name = "background-white" if "white" in old_path.stem.lower() else "background-black"
        target = background_root / f"{name}{suffix}"
        shutil.copy2(old_path, target)
        replacements[str(old_path)] = str(final_destination / target.relative_to(stage))
    return replacements


def update_draft_meta(
    path: Path,
    *,
    old_draft_id: str,
    new_draft_id: str,
    draft_name: str,
    final_destination: Path,
) -> None:
    meta = read_json(path)
    now_us = int(time.time() * 1_000_000)
    meta["draft_id"] = new_draft_id
    meta["draft_name"] = draft_name
    meta["draft_fold_path"] = str(final_destination)
    meta["draft_root_path"] = str(final_destination.parent)
    meta["tm_draft_create"] = now_us
    meta["tm_draft_modified"] = now_us
    meta["tm_draft_cloud_entry_id"] = 0
    meta["tm_draft_cloud_parent_entry_id"] = -1
    meta["tm_draft_cloud_space_id"] = 0
    meta["tm_draft_cloud_user_id"] = 0
    meta["tm_draft_cloud_completed"] = "0"
    meta["tm_draft_cloud_modified"] = 0
    meta["cloud_draft_sync"] = False
    meta["cloud_package_completed_time"] = ""
    write_json(path, meta)
    replace_text_in_tree(path.parent, {old_draft_id: new_draft_id})


def update_covers(stage: Path) -> None:
    scene = stage / "cc-helper-assets" / "visuals" / "scene-01.png"
    if not scene.is_file() or not pillow_available():
        return
    from PIL import Image

    with Image.open(scene) as opened:
        cover = opened.convert("RGB")
        for target in [stage / "draft_cover.jpg", *stage.glob("Timelines/*/draft_cover.jpg")]:
            target.parent.mkdir(parents=True, exist_ok=True)
            cover.save(target, "JPEG", quality=90)


def visual_value_snapshot(segment: dict[str, Any]) -> str:
    def without_ids(value: Any) -> Any:
        if isinstance(value, dict):
            return {key: without_ids(item) for key, item in value.items() if key != "id"}
        if isinstance(value, list):
            return [without_ids(item) for item in value]
        return value

    payload = {
        key: without_ids(segment.get(key))
        for key in ("clip", "crop", "crop_ratio", "crop_scale", "uniform_scale", "common_keyframes")
        if key in segment
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def narration_audio_parts(
    draft: dict[str, Any], project: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    audio = project.get("narration_audio")
    if not isinstance(audio, dict):
        raise CCHelperError("project.json narration_audio 정보가 없습니다.")
    material_id = str(audio.get("capcut_material_id") or "")
    segment_id = str(audio.get("capcut_segment_id") or "")
    materials = draft.get("materials") or {}
    material = next(
        (item for item in materials.get("audios", []) if item.get("id") == material_id),
        None,
    )
    for track in draft.get("tracks", []):
        if track.get("type") != "audio":
            continue
        for segment in track.get("segments", []):
            if segment.get("id") == segment_id and segment.get("material_id") == material_id:
                if not isinstance(material, dict):
                    raise CCHelperError("Typecast 오디오 소재를 찾을 수 없습니다.")
                return track, segment, material
    raise CCHelperError("Typecast 오디오 트랙 또는 세그먼트를 찾을 수 없습니다.")


def narration_audio_identity(draft: dict[str, Any], project: dict[str, Any]) -> str:
    track, segment, material = narration_audio_parts(draft, project)
    payload = {
        "track_id": track.get("id"),
        "segment_id": segment.get("id"),
        "segment_material_id": segment.get("material_id"),
        "material_id": material.get("id"),
        "material_path": material.get("path"),
        "target_start": (segment.get("target_timerange") or {}).get("start"),
        "source_start": (segment.get("source_timerange") or {}).get("start"),
        "volume": segment.get("volume"),
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sync_narration_audio_duration(draft: dict[str, Any], project: dict[str, Any]) -> None:
    _track, segment, material = narration_audio_parts(draft, project)
    audio = project["narration_audio"]
    duration = int(audio.get("capcut_duration_us") or 0)
    if duration <= 0:
        raise CCHelperError("project.json narration_audio.capcut_duration_us가 올바르지 않습니다.")
    update_timerange(segment, "target_timerange", 0, duration)
    update_timerange(segment, "source_timerange", 0, duration)
    material["duration"] = duration


def sync_embedded_handoff(project_dir: Path, destination: Path) -> None:
    handoff_root = destination / "cc-helper-assets" / "handoff"
    handoff_root.mkdir(parents=True, exist_ok=True)
    for name in ("project.json", "research.json", "storyboard.json", "asset-manifest.json", "capcut-map.json"):
        source = project_dir / name
        if source.is_file():
            shutil.copy2(source, handoff_root / name)
    if (project_dir / "handoff").is_dir():
        shutil.copytree(project_dir / "handoff", handoff_root / "files", dirs_exist_ok=True)


def sync_retime_visuals(
    project_dir: Path,
    destination: Path,
    scene_mappings: list[dict[str, Any]],
) -> None:
    copied: dict[Path, Path] = {}
    for item in scene_mappings:
        source = project_path(project_dir, str(item.get("source_path") or ""))
        target = (destination / str(item.get("target_relative_path") or "")).resolve()
        previous = copied.get(target)
        if previous:
            if previous != source:
                raise CCHelperError(f"같은 홀드 대상에 서로 다른 에셋이 지정됐습니다: {target}")
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        copied[target] = source


def backup_retime_files(
    project_dir: Path,
    destination: Path,
    paths: list[Path],
) -> tuple[Path, dict[Path, Path]]:
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = project_dir / "backups" / f"capcut-retime-{stamp}"
    if backup.exists():
        raise CCHelperError(f"재타이밍 백업 폴더가 이미 존재합니다: {backup}")
    copied: dict[Path, Path] = {}
    for source in paths:
        if not source.exists():
            continue
        relative = source.relative_to(destination)
        target = backup / "draft" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.is_dir():
            shutil.copytree(source, target)
        else:
            shutil.copy2(source, target)
        copied[source] = target
    shutil.copy2(project_dir / "capcut-map.json", backup / "project-capcut-map.json")
    return backup, copied


def restore_retime_files(copied: dict[Path, Path], project_map: Path, backup: Path) -> None:
    for destination, source in copied.items():
        if source.is_dir():
            shutil.copytree(source, destination, dirs_exist_ok=True)
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
    shutil.copy2(backup / "project-capcut-map.json", project_map)


def project_prerender_cache_path(
    capcut_root: Path,
    destination: Path,
    timeline_id: str,
) -> Path:
    capcut_root = capcut_root.resolve()
    destination = destination.resolve()
    if capcut_root.name != "com.lveditor.draft" or capcut_root.parent.name != "Projects":
        raise CCHelperError("CapCut 프로젝트 루트 구조가 예상과 달라 prerender 캐시를 확인할 수 없습니다.")
    if destination.parent != capcut_root:
        raise CCHelperError("현재 초안이 준비된 CapCut 프로젝트 루트 밖에 있습니다.")
    try:
        parsed = str(uuid.UUID(timeline_id)).upper()
    except (ValueError, AttributeError) as exc:
        raise CCHelperError("CapCut timeline ID가 올바른 UUID가 아닙니다.") from exc
    if parsed != timeline_id.upper() or Path(timeline_id).name != timeline_id:
        raise CCHelperError("CapCut timeline ID가 단일 안전 경로가 아닙니다.")
    timeline_dir = destination / "Timelines" / timeline_id
    if not timeline_dir.is_dir() or timeline_dir.is_symlink():
        raise CCHelperError("현재 timeline 폴더를 안전하게 확인할 수 없습니다.")
    cache_root = (capcut_root.parent.parent / "Cache" / "prerender").resolve()
    cache_path = (cache_root / timeline_id).resolve()
    if cache_path.parent != cache_root or cache_path.is_symlink():
        raise CCHelperError("prerender 캐시 경로를 안전하게 확인할 수 없습니다.")
    return cache_path


def backup_prerender_cache(cache_path: Path, backup: Path) -> Path | None:
    if not cache_path.exists():
        return None
    if not cache_path.is_dir() or cache_path.is_symlink():
        raise CCHelperError("timeline prerender 캐시가 안전한 폴더가 아닙니다.")
    target = backup / "cache" / "prerender" / cache_path.name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(cache_path, target)
    if tree_hash(cache_path) != tree_hash(target):
        raise CCHelperError("timeline prerender 캐시 백업 검증에 실패했습니다.")
    return target


def invalidate_prerender_cache(cache_path: Path) -> bool:
    if not cache_path.exists():
        return False
    if not cache_path.is_dir() or cache_path.is_symlink():
        raise CCHelperError("timeline prerender 캐시를 안전하게 지울 수 없습니다.")
    shutil.rmtree(cache_path)
    return True


def restore_prerender_cache(cache_path: Path, backup_path: Path | None) -> None:
    if backup_path is None:
        return
    if cache_path.exists():
        if not cache_path.is_dir() or cache_path.is_symlink():
            raise CCHelperError("timeline prerender 캐시 복구 대상이 안전한 폴더가 아닙니다.")
        shutil.rmtree(cache_path)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(backup_path, cache_path)
    if tree_hash(cache_path) != tree_hash(backup_path):
        raise CCHelperError("timeline prerender 캐시 복구 검증에 실패했습니다.")


def clone_capcut(args: argparse.Namespace) -> None:
    if not args.confirm:
        raise CCHelperError("복제하려면 --confirm이 필요합니다.")
    project_dir = Path(args.project_dir).expanduser().resolve()
    mapping = read_json(project_dir / "capcut-map.json")
    if mapping.get("status") == "cloned" and mapping.get("reuse_existing"):
        capcut_root = Path(str(mapping.get("capcut_root") or "")).resolve()
        final_destination = Path(str(mapping.get("destination_path") or "")).resolve()
        if (
            not final_destination.is_dir()
            or final_destination.is_symlink()
            or final_destination.parent != capcut_root
        ):
            raise CCHelperError("재사용할 기존 CapCut 초안을 안전하게 확인할 수 없습니다.")
        print_json(
            {
                "status": "reused_existing",
                "destination_path": str(final_destination),
                "draft_id": mapping.get("draft_id", ""),
                "draft_name": mapping.get("draft_name", final_destination.name),
                "next_action": "retime-capcut --confirm-existing",
            }
        )
        return
    if mapping.get("status") != "prepared":
        raise CCHelperError("먼저 prepare-capcut --dry-run을 실행하세요.")
    errors, _warnings = validate_assets(project_dir)
    if errors:
        raise CCHelperError("에셋 단계 검증 실패:\n- " + "\n- ".join(errors))
    if capcut_running():
        raise CCHelperError("CapCut을 완전히 종료한 뒤 다시 실행하세요.")

    base_draft = Path(mapping["base_draft"]).resolve()
    capcut_root = Path(mapping["capcut_root"]).resolve()
    final_destination = Path(mapping["destination_path"]).resolve()
    if final_destination.parent != capcut_root:
        raise CCHelperError("목적지 경로가 준비된 CapCut 루트와 일치하지 않습니다.")
    if final_destination.exists():
        raise CCHelperError(f"목적지 캡컷 프로젝트가 이미 존재합니다: {final_destination}")
    if tree_hash(base_draft) != mapping.get("base_tree_sha256"):
        raise CCHelperError("prepare-capcut 이후 원본 템플릿이 변경되었습니다.")
    capcut_root.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".cc-helper-stage-", dir=str(capcut_root)))
    new_draft_id = str(uuid.uuid4()).upper()
    try:
        shutil.copytree(base_draft, stage, dirs_exist_ok=True)
        background_replacements = copy_clone_assets(
            project_dir, base_draft, stage, final_destination, mapping
        )
        root_draft = read_json(stage / "draft_info.json")
        path_replacements = apply_root_draft(root_draft, mapping, final_destination)
        path_replacements.update(background_replacements)
        mirrored = [
            path
            for path in stage.rglob("*")
            if path.is_file() and path.name in {"draft_info.json", "draft_info.json.bak", "template-2.tmp"}
        ]
        for path in mirrored:
            write_json(path, root_draft)
        update_mini_drafts(stage, root_draft, mapping)
        meta_path = stage / "draft_meta_info.json"
        meta = read_json(meta_path)
        old_draft_id = str(meta.get("draft_id") or "")
        replace_text_in_tree(
            stage,
            {
                **path_replacements,
                str(base_draft): str(final_destination),
                old_draft_id: new_draft_id,
            },
        )
        update_draft_meta(
            meta_path,
            old_draft_id=old_draft_id,
            new_draft_id=new_draft_id,
            draft_name=mapping["draft_name"],
            final_destination=final_destination,
        )
        update_covers(stage)
        stage.rename(final_destination)
    except Exception:
        shutil.rmtree(stage, ignore_errors=True)
        raise

    mapping["status"] = "cloned"
    mapping["cloned_at"] = now_iso()
    mapping["draft_id"] = new_draft_id
    mapping["destination_path"] = str(final_destination)
    mapping["reuse_policy"] = CAPCUT_CLONE_REUSE_POLICY
    mapping["reuse_existing"] = False
    write_json(project_dir / "capcut-map.json", mapping)
    project = read_json(project_dir / "project.json")
    capcut = project.get("capcut") if isinstance(project.get("capcut"), dict) else {}
    capcut["destination_name"] = final_destination.name
    capcut["active_destination_name"] = final_destination.name
    capcut["reuse_policy"] = CAPCUT_CLONE_REUSE_POLICY
    capcut["draft_name"] = mapping["draft_name"]
    project["capcut"] = capcut
    write_json(project_dir / "project.json", project)
    print_json(
        {
            "status": "cloned",
            "destination_path": str(final_destination),
            "draft_id": new_draft_id,
            "draft_name": mapping["draft_name"],
        }
    )


def retime_capcut(args: argparse.Namespace) -> None:
    if not args.confirm_existing:
        raise CCHelperError("기존 초안을 재타이밍하려면 --confirm-existing이 필요합니다.")
    project_dir = Path(args.project_dir).expanduser().resolve()
    mapping_path = project_dir / "capcut-map.json"
    mapping = read_json(mapping_path)
    if mapping.get("status") != "cloned":
        raise CCHelperError("복제 완료된 capcut-map.json만 재타이밍할 수 있습니다.")
    if capcut_running():
        raise CCHelperError("CapCut을 완전히 종료한 뒤 다시 실행하세요.")
    errors, _warnings = validate_assets(project_dir)
    if errors:
        raise CCHelperError("에셋·타이밍 검증 실패:\n- " + "\n- ".join(errors))

    destination = Path(str(mapping.get("destination_path") or "")).resolve()
    capcut_root = Path(str(mapping.get("capcut_root") or destination.parent)).resolve()
    base_draft = Path(str(mapping.get("base_draft") or DEFAULT_BASE_DRAFT)).resolve()
    if not destination.is_dir():
        raise CCHelperError(f"기존 CapCut 초안을 찾을 수 없습니다: {destination}")
    if destination == base_draft or destination.parent != capcut_root:
        raise CCHelperError("원본 템플릿 또는 준비된 CapCut 루트 밖의 초안은 수정할 수 없습니다.")
    meta_path = destination / "draft_meta_info.json"
    meta = read_json(meta_path)
    if Path(str(meta.get("draft_fold_path") or "")).resolve() != destination:
        raise CCHelperError("draft_meta_info.json의 초안 경로가 목적지와 다릅니다.")

    project = read_json(project_dir / "project.json")
    storyboard = read_json(project_dir / "storyboard.json")
    manifest = load_manifest(project_dir)
    root_path = destination / "draft_info.json"
    root_draft = read_json(root_path)
    timeline_project = read_json(destination / "Timelines" / "project.json")
    timeline_id = str(root_draft.get("id") or "")
    if str(timeline_project.get("main_timeline_id") or "") != timeline_id:
        raise CCHelperError("활성 timeline ID가 draft_info.json과 다릅니다.")
    prerender_cache = project_prerender_cache_path(capcut_root, destination, timeline_id)
    before_audio_identity = narration_audio_identity(root_draft, project)
    canonical_draft_path = base_draft / "draft_info.json"
    canonical_draft = read_json(canonical_draft_path)
    scene_mappings, title_mappings, caption_mappings = build_content_mappings(
        canonical_draft, storyboard, manifest
    )
    attach_template_mini_visuals(base_draft, scene_mappings)
    attach_person_motion_plans(scene_mappings, storyboard, manifest)
    previous_scene_mappings = mapping.get("scene_mappings") or []
    if previous_scene_mappings:
        previous_ids = [
            (item.get("segment_id"), item.get("material_id"))
            for item in previous_scene_mappings
        ]
        canonical_ids = [
            (item.get("segment_id"), item.get("material_id")) for item in scene_mappings
        ]
        if previous_ids != canonical_ids:
            raise CCHelperError("기존 초안과 base template의 scene/material ID 구조가 다릅니다.")
    total_duration_us = sum(item["duration_us"] for item in scene_mappings)

    root_meta_path = capcut_root / "root_meta_info.json"
    root_meta_hash = sha256_file(root_meta_path) if root_meta_path.is_file() else ""
    embedded_handoff = destination / "cc-helper-assets" / "handoff"
    visual_targets = sorted(
        {
            (destination / str(item.get("target_relative_path") or "")).resolve()
            for item in scene_mappings
        }
    )
    backup_paths = [
        *active_draft_mirror_paths(destination),
        *active_template_paths(destination),
        *active_mini_draft_paths(destination),
        *active_cover_paths(destination),
        *visual_targets,
        meta_path,
    ]
    if embedded_handoff.is_dir():
        backup_paths.append(embedded_handoff)
    backup, copied = backup_retime_files(project_dir, destination, backup_paths)
    prerender_backup = backup_prerender_cache(prerender_cache, backup)
    prerender_invalidated = False

    mapping.update(
        {
            "status": "cloned",
            "retimed_at": now_iso(),
            "retime_backup_path": str(backup),
            "draft_id": str(meta.get("draft_id") or mapping.get("draft_id") or ""),
            "draft_name": str(meta.get("draft_name") or mapping.get("draft_name") or destination.name),
            "total_duration_us": total_duration_us,
            "scene_mappings": scene_mappings,
            "title_mappings": title_mappings,
            "caption_mappings": caption_mappings,
            "root_meta_info_sha256": root_meta_hash,
            "geometry_mode": "base-template-snapshot",
            "template_geometry_source_sha256": sha256_file(canonical_draft_path),
            "person_motion_mode": storyboard.get("person_motion_mode", ""),
            "narration_audio_segment_id": str(
                (project.get("narration_audio") or {}).get("capcut_segment_id") or ""
            ),
            "narration_audio_duration_us": int(
                (project.get("narration_audio") or {}).get("capcut_duration_us") or 0
            ),
            "full_frame_reset_paths": sorted(
                {str(item.get("target_relative_path") or "") for item in scene_mappings}
            ),
            "prerender_cache_path": str(prerender_cache),
            "prerender_cache_backup_path": str(prerender_backup or ""),
        }
    )

    try:
        prerender_invalidated = invalidate_prerender_cache(prerender_cache)
        mapping["prerender_cache_invalidated"] = prerender_invalidated
        mapping["prerender_cache_invalidated_at"] = now_iso()
        sync_retime_visuals(project_dir, destination, scene_mappings)
        apply_root_draft(root_draft, mapping, destination)
        sync_narration_audio_duration(root_draft, project)
        if narration_audio_identity(root_draft, project) != before_audio_identity:
            raise CCHelperError("재타이밍 중 Typecast 오디오 ID·경로·시작·볼륨이 변경됐습니다.")
        for path in active_draft_mirror_paths(destination):
            write_json(path, root_draft)
        for path in active_template_paths(destination):
            template = read_json(path)
            apply_root_draft(template, mapping, destination, relative_paths=True)
            sync_narration_audio_duration(template, project)
            write_json(path, template)
        update_mini_drafts(destination, root_draft, mapping)
        update_covers(destination)
        mapping["draft_covers_updated_at"] = now_iso()

        meta["tm_duration"] = total_duration_us
        meta["tm_draft_modified"] = int(time.time() * 1_000_000)
        write_json(meta_path, meta)
        write_json(mapping_path, mapping)
        build_handoff(project_dir, storyboard, manifest)
        sync_embedded_handoff(project_dir, destination)

        if root_meta_hash and sha256_file(root_meta_path) != root_meta_hash:
            raise CCHelperError("공유 root_meta_info.json이 변경됐습니다.")
        updated_root = read_json(root_path)
        if narration_audio_identity(updated_root, project) != before_audio_identity:
            raise CCHelperError("저장된 Typecast 오디오 ID·경로·시작·볼륨이 변경됐습니다.")
    except Exception:
        restore_retime_files(copied, mapping_path, backup)
        restore_prerender_cache(prerender_cache, prerender_backup)
        raise

    print_json(
        {
            "status": "retimed",
            "destination_path": str(destination),
            "total_duration_us": total_duration_us,
            "backup_path": str(backup),
            "prerender_cache_invalidated": prerender_invalidated,
        }
    )


def visual_timeline_fingerprint(draft: dict[str, Any], destination: Path) -> str:
    parts = find_template_parts(draft)
    scenes = []
    for segment in parts["scene_segments"]:
        material = parts["videos"].get(segment.get("material_id"), {})
        path = resolve_capcut_material_path(str(material.get("path") or ""), destination)
        scenes.append(
            {
                "segment_id": segment.get("id"),
                "material_id": segment.get("material_id"),
                "target_timerange": segment.get("target_timerange"),
                "visible": segment.get("visible", True),
                "render_index": segment.get("render_index"),
                "segment_visual": json.loads(visual_value_snapshot(segment)),
                "material_visual": json.loads(visual_value_snapshot(material)),
                "path": str(path.resolve()),
                "file_sha256": sha256_file(path) if path.is_file() else "",
            }
        )
    texts = []
    for segment in [*parts["title_segments"], *parts["caption_segments"]]:
        material = parts["texts"].get(segment.get("material_id"), {})
        texts.append(
            {
                "segment_id": segment.get("id"),
                "material_id": segment.get("material_id"),
                "target_timerange": segment.get("target_timerange"),
                "visible": segment.get("visible", True),
                "render_index": segment.get("render_index"),
                "visual": json.loads(visual_value_snapshot(segment)),
                "text": text_material_value(material),
                "font_size": material.get("font_size"),
                "text_size": material.get("text_size"),
            }
        )
    payload = {
        "timeline_id": draft.get("id"),
        "duration": draft.get("duration"),
        "scenes": scenes,
        "texts": texts,
    }
    return sha256_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    )


def validate_final_visual_qc(
    project_dir: Path,
    destination: Path,
    draft: dict[str, Any],
    mapping: dict[str, Any],
    storyboard: dict[str, Any],
) -> list[str]:
    if storyboard.get("final_visual_review_mode") != FINAL_VISUAL_REVIEW_MODE:
        return []
    errors: list[str] = []
    qc_path = project_dir / "handoff" / "final-visual-qc.json"
    if not qc_path.is_file():
        return ["CapCut player 최종 화면 검수 파일 handoff/final-visual-qc.json이 필요합니다."]
    qc = read_json(qc_path)
    if qc.get("source") != "capcut_player_review" or qc.get("status") != "approved":
        errors.append("final-visual-qc는 승인된 CapCut player 검수 기록이어야 합니다.")
    expected_fingerprint = visual_timeline_fingerprint(draft, destination)
    if qc.get("visual_timeline_sha256") != expected_fingerprint:
        errors.append("CapCut 시각 타임라인이 최종 player 검수 이후 변경됐습니다.")
    if qc.get("capcut_map_sha256") != sha256_file(project_dir / "capcut-map.json"):
        errors.append("capcut-map.json이 최종 player 검수 이후 변경됐습니다.")
    if qc.get("storyboard_sha256") != sha256_file(project_dir / "storyboard.json"):
        errors.append("storyboard.json이 최종 player 검수 이후 변경됐습니다.")
    if str(qc.get("timeline_id") or "") != str(draft.get("id") or ""):
        errors.append("final-visual-qc timeline ID가 현재 CapCut timeline과 다릅니다.")

    samples = qc.get("samples") if isinstance(qc.get("samples"), list) else []
    samples_by_beat = {
        str(item.get("beat_id") or ""): item
        for item in samples
        if isinstance(item, dict) and str(item.get("beat_id") or "")
    }
    manifest = load_manifest(project_dir)
    assets = {str(item.get("id") or ""): item for item in manifest.get("assets", [])}
    scene_by_id = {str(item.get("id") or ""): item for item in storyboard.get("scenes", [])}
    mapping_by_scene = {
        str(item.get("scene_id") or ""): item for item in mapping.get("scene_mappings", [])
    }
    times = scene_times(storyboard)
    timing_by_scene = {
        str(scene.get("id") or ""): timing
        for scene, timing in zip(storyboard.get("scenes", []), times)
    }
    for beat in storyboard.get("beats", []):
        beat_id = str(beat.get("id") or "")
        linked = [scene for scene in storyboard.get("scenes", []) if scene.get("beat_id") == beat_id]
        sample = samples_by_beat.get(beat_id)
        if not linked or not isinstance(sample, dict):
            errors.append(f"{beat_id} midpoint player 검수가 없습니다.")
            continue
        scene_id = str(sample.get("scene_id") or "")
        if scene_id not in {str(scene.get("id") or "") for scene in linked}:
            errors.append(f"{beat_id} player 검수 scene이 해당 beat에 속하지 않습니다.")
            continue
        timing = timing_by_scene.get(scene_id) or {}
        start_us = int(timing.get("start") or 0)
        end_us = start_us + int(timing.get("duration") or 0)
        time_us = int(sample.get("time_us") or -1)
        if not start_us < time_us < end_us:
            errors.append(f"{beat_id} player 검수 시각이 scene midpoint 범위가 아닙니다.")
        screenshot_relative = str(sample.get("screenshot_path") or "")
        try:
            screenshot = project_path(project_dir, screenshot_relative)
            if sha256_file(screenshot) != str(sample.get("screenshot_sha256") or ""):
                errors.append(f"{beat_id} player 스크린샷 SHA-256이 다릅니다.")
        except CCHelperError as exc:
            errors.append(str(exc))
        scene = scene_by_id.get(scene_id) or {}
        asset = assets.get(str(scene.get("asset_id") or "")) or {}
        focus = ((asset.get("review") or {}).get("display_focus") or "")
        automatic = sample.get("automatic") if isinstance(sample.get("automatic"), dict) else {}
        manual = sample.get("manual") if isinstance(sample.get("manual"), dict) else {}
        for key in ("not_blank", "white_title_present", "yellow_title_present", "header_background_clear"):
            if automatic.get(key) is not True:
                errors.append(f"{beat_id} player 자동 검수 실패: {key}")
        if scene_id != "scene-01" and automatic.get("caption_present") is not True:
            errors.append(f"{beat_id} player 자동 검수 실패: caption_present")
        for key in ("correct_visual", "caption_matches", "no_clipping_or_overlap"):
            if manual.get(key) is not True:
                errors.append(f"{beat_id} player 수동 검수 실패: {key}")
        if focus in {"source_text", "mixed"} and manual.get("source_content_readable") is not True:
            errors.append(f"{beat_id} 텍스트 증거가 실제 player 크기에서 읽히지 않습니다.")
        if (
            storyboard.get("public_figure_style_mode") == PUBLIC_FIGURE_STYLE_MODE
            and asset.get("evidence_role") == "editorial_animation"
        ):
            if manual.get("portrait_style_obvious_at_player_size") is not True:
                errors.append(f"{beat_id} 공개 인물 화풍이 player 크기에서 명확하지 않습니다.")
            if manual.get("editorial_eye_band_visible") is not True:
                errors.append(f"{beat_id} 공개 인물 editorial eye-band가 player에서 보이지 않습니다.")
            if manual.get("editorial_ruler_ticks_visible") is not True:
                errors.append(f"{beat_id} 공개 인물 eye-band 눈금이 player에서 보이지 않습니다.")
        if (mapping_by_scene.get(scene_id) or {}).get("motion_plan"):
            for key in ("motion_smooth", "motion_face_safe", "motion_avoids_title_caption"):
                if manual.get(key) is not True:
                    errors.append(f"{beat_id} 인물 motion player 검수 실패: {key}")
        if sample.get("approved") is not True:
            errors.append(f"{beat_id} player sample이 approved가 아닙니다.")
    if len(samples_by_beat) != len(storyboard.get("beats", [])):
        errors.append("final-visual-qc sample 수가 narration beat 수와 다릅니다.")

    def validate_evidence_screenshot(
        record: dict[str, Any], path_key: str, sha_key: str, label: str
    ) -> None:
        try:
            screenshot = project_path(project_dir, str(record.get(path_key) or ""))
            if sha256_file(screenshot) != str(record.get(sha_key) or ""):
                errors.append(f"{label} 스크린샷 SHA-256이 다릅니다.")
        except CCHelperError as exc:
            errors.append(str(exc))

    motion_reviews = (
        qc.get("motion_reviews") if isinstance(qc.get("motion_reviews"), list) else []
    )
    motion_reviews_by_beat = {
        str(item.get("beat_id") or ""): item
        for item in motion_reviews
        if isinstance(item, dict) and str(item.get("beat_id") or "")
    }
    expected_motion_beats: dict[str, list[dict[str, Any]]] = {}
    for beat in storyboard.get("beats", []):
        beat_id = str(beat.get("id") or "")
        linked_mappings = [
            item
            for item in mapping.get("scene_mappings", [])
            if item.get("beat_id") == beat_id and isinstance(item.get("motion_plan"), dict)
        ]
        if linked_mappings:
            expected_motion_beats[beat_id] = linked_mappings
    for beat_id, linked_mappings in expected_motion_beats.items():
        review = motion_reviews_by_beat.get(beat_id)
        if not isinstance(review, dict):
            errors.append(f"{beat_id} 인물 motion 시작·끝 player 검수가 없습니다.")
            continue
        first_timing = timing_by_scene.get(str(linked_mappings[0].get("scene_id") or "")) or {}
        last_timing = timing_by_scene.get(str(linked_mappings[-1].get("scene_id") or "")) or {}
        first_start = int(first_timing.get("start") or 0)
        first_end = first_start + int(first_timing.get("duration") or 0)
        last_start = int(last_timing.get("start") or 0)
        last_end = last_start + int(last_timing.get("duration") or 0)
        start_value = review.get("start_time_us")
        end_value = review.get("end_time_us")
        start_time = int(start_value if start_value is not None else -1)
        end_time = int(end_value if end_value is not None else -1)
        if not first_start <= start_time < first_end:
            errors.append(f"{beat_id} motion 시작 검수 시각이 첫 scene 범위가 아닙니다.")
        if not last_start < end_time <= last_end or end_time <= start_time:
            errors.append(f"{beat_id} motion 종료 검수 시각이 마지막 scene 범위가 아닙니다.")
        validate_evidence_screenshot(review, "start_path", "start_sha256", f"{beat_id} motion 시작")
        validate_evidence_screenshot(review, "end_path", "end_sha256", f"{beat_id} motion 종료")
        for key in ("slow_motion_visible", "face_safe", "title_caption_safe"):
            if review.get(key) is not True:
                errors.append(f"{beat_id} motion 시작·끝 검수 실패: {key}")
    if len(motion_reviews_by_beat) != len(expected_motion_beats):
        errors.append("final-visual-qc motion review 수가 실제 motion beat 수와 다릅니다.")

    boundary_records = qc.get("boundaries") if isinstance(qc.get("boundaries"), list) else []
    boundaries_by_pair = {
        (str(item.get("left_scene_id") or ""), str(item.get("right_scene_id") or "")): item
        for item in boundary_records
        if isinstance(item, dict)
    }
    expected_boundaries: list[tuple[dict[str, Any], dict[str, Any]]] = []
    scene_mappings = mapping.get("scene_mappings", [])
    for left, right in zip(scene_mappings, scene_mappings[1:]):
        if (
            right.get("hold_source_scene_id") == left.get("scene_id")
            and right.get("beat_id") == left.get("beat_id")
            and isinstance(right.get("motion_plan"), dict)
        ):
            expected_boundaries.append((left, right))
    for left, right in expected_boundaries:
        pair = (str(left.get("scene_id") or ""), str(right.get("scene_id") or ""))
        record = boundaries_by_pair.get(pair)
        if not isinstance(record, dict):
            errors.append(f"{pair[0]}→{pair[1]} motion 경계 전후 player 검수가 없습니다.")
            continue
        if int(record.get("boundary_time_us") or -1) != int(right.get("start_us") or 0):
            errors.append(f"{pair[0]}→{pair[1]} motion 경계 검수 시각이 다릅니다.")
        validate_evidence_screenshot(record, "before_path", "before_sha256", f"{pair[0]}→{pair[1]} 경계 전")
        validate_evidence_screenshot(record, "after_path", "after_sha256", f"{pair[0]}→{pair[1]} 경계 후")
        for key in ("same_asset", "motion_continuous", "no_black_frame", "no_visual_jump"):
            if record.get(key) is not True:
                errors.append(f"{pair[0]}→{pair[1]} motion 경계 검수 실패: {key}")
    if len(boundaries_by_pair) != len(expected_boundaries):
        errors.append("final-visual-qc boundary review 수가 실제 분할 motion 경계 수와 다릅니다.")
    return errors


def validate_capcut(project_dir: Path) -> tuple[list[str], list[str]]:
    errors, warnings = validate_assets(project_dir)
    mapping = read_json(project_dir / "capcut-map.json")
    destination_value = str(mapping.get("destination_path") or "")
    if not destination_value:
        errors.append("capcut-map.json에 destination_path가 없습니다.")
        return errors, warnings
    destination = Path(destination_value)
    if not destination.is_dir():
        errors.append(f"복제된 캡컷 프로젝트가 없습니다: {destination}")
        return errors, warnings
    try:
        draft = read_json(destination / "draft_info.json")
        parts = find_template_parts(draft)
    except CCHelperError as exc:
        errors.append(str(exc))
        return errors, warnings
    scene_mappings = mapping.get("scene_mappings", [])
    title_mappings = mapping.get("title_mappings", [])
    caption_mappings = mapping.get("caption_mappings", [])
    if len(scene_mappings) != SCENE_COUNT:
        errors.append("capcut-map.json 장면 매핑은 정확히 15개여야 합니다.")
    if len(title_mappings) != 2:
        errors.append("capcut-map.json 제목 매핑은 정확히 2개여야 합니다.")
    if len(caption_mappings) != SCENE_COUNT - 1:
        errors.append("capcut-map.json 자막 매핑은 정확히 14개여야 합니다.")
    mapping_by_scene = {item.get("scene_id"): item for item in scene_mappings}
    if int(draft.get("duration") or 0) != int(mapping.get("total_duration_us") or 0):
        errors.append("복제된 캡컷 프로젝트의 전체 길이가 매핑과 다릅니다.")
    expected_start = 0
    for item, segment in zip(scene_mappings, parts["scene_segments"]):
        material = parts["videos"].get(segment.get("material_id"), {})
        path = resolve_capcut_material_path(
            str(material.get("path") or ""), destination
        )
        expected_path = (destination / str(item.get("target_relative_path") or "")).resolve()
        if not path.is_file():
            errors.append(f"복제 프로젝트 장면 파일이 없습니다: {path}")
        elif path.resolve() != expected_path:
            errors.append(f"{item.get('scene_id')} 장면 경로가 매핑과 다릅니다: {path}")
        else:
            try:
                source = project_path(project_dir, str(item.get("source_path") or ""))
                if sha256_file(source) != sha256_file(path):
                    errors.append(f"{item.get('scene_id')} 장면 이미지 해시가 프로젝트 원본과 다릅니다.")
            except CCHelperError as exc:
                errors.append(str(exc))
        if str(path).startswith(str(DEFAULT_BASE_DRAFT)) or "/Desktop/youtube/asset/" in str(path):
            errors.append(f"기존 외부 에셋 경로가 남아 있습니다: {path}")
        timing = segment.get("target_timerange") or {}
        if timing.get("start") != item.get("start_us") or timing.get("duration") != item.get("duration_us"):
            errors.append(f"{item.get('scene_id')} 타이밍이 매핑과 다릅니다.")
        if timing.get("start") != expected_start:
            errors.append(f"{item.get('scene_id')} 타이밍에 공백 또는 겹침이 있습니다.")
        hold_source = str(item.get("hold_source_scene_id") or "")
        expected_item = mapping_by_scene.get(hold_source) if hold_source else item
        if not isinstance(expected_item, dict):
            errors.append(f"{item.get('scene_id')} 템플릿 geometry 기준을 찾을 수 없습니다.")
        else:
            expected_segment = expected_item.get("template_segment_visual")
            expected_material = expected_item.get("template_material_visual")
            if not isinstance(expected_segment, dict) or not isinstance(expected_material, dict):
                errors.append(f"{item.get('scene_id')} 템플릿 geometry snapshot이 없습니다.")
            else:
                expected_rendered_segment = copy.deepcopy(expected_segment)
                plan = item.get("motion_plan")
                if isinstance(plan, dict):
                    apply_motion_plan(
                        expected_rendered_segment,
                        str(item.get("scene_id") or ""),
                        plan,
                        mini=False,
                    )
                if visual_value_snapshot(segment) != visual_value_snapshot(expected_rendered_segment):
                    errors.append(f"{item.get('scene_id')} segment geometry가 템플릿 기준과 다릅니다.")
                if visual_value_snapshot(material) != visual_value_snapshot(expected_material):
                    errors.append(f"{item.get('scene_id')} material geometry가 템플릿 기준과 다릅니다.")
        expected_start += int(timing.get("duration") or 0)
    if expected_start != int(mapping.get("total_duration_us") or 0):
        errors.append("장면 타임라인 종료가 전체 길이와 다릅니다.")
    for item, segment in zip(title_mappings, parts["title_segments"]):
        actual = text_material_value(parts["texts"].get(segment.get("material_id"), {}))
        if actual != item.get("value"):
            errors.append(f"상단 제목이 매핑과 다릅니다: {item.get('value')}")
        timing = segment.get("target_timerange") or {}
        if segment.get("visible") is False or float((segment.get("clip") or {}).get("alpha", 1.0)) <= 0:
            errors.append(f"상단 제목이 숨겨져 있습니다: {item.get('value')}")
        if timing.get("start") != 0 or timing.get("duration") != mapping.get("total_duration_us"):
            errors.append(f"상단 제목의 표시 구간이 전체 영상과 다릅니다: {item.get('value')}")
        material = parts["texts"].get(segment.get("material_id"), {})
        if float(material.get("font_size") or material.get("text_size") or 0) <= 0:
            errors.append(f"상단 제목 글자 크기가 0입니다: {item.get('value')}")
    for item, segment in zip(caption_mappings, parts["caption_segments"]):
        actual = text_material_value(parts["texts"].get(segment.get("material_id"), {}))
        if actual != item.get("value"):
            errors.append(f"하단 자막이 매핑과 다릅니다: {item.get('segment_id')}")
        if segment.get("visible") is False or float((segment.get("clip") or {}).get("alpha", 1.0)) <= 0:
            errors.append(f"하단 자막이 숨겨져 있습니다: {item.get('segment_id')}")
    storyboard = read_json(project_dir / "storyboard.json")
    if storyboard.get("pacing_mode") == NARRATION_HOLD_MODE:
        scene_segment_by_id = {
            item.get("scene_id"): segment
            for item, segment in zip(scene_mappings, parts["scene_segments"])
        }
        resolved_paths = []
        for item, segment in zip(scene_mappings, parts["scene_segments"]):
            material = parts["videos"].get(segment.get("material_id"), {})
            resolved_paths.append(
                str(resolve_capcut_material_path(str(material.get("path") or ""), destination).resolve())
            )
            hold_source = str(item.get("hold_source_scene_id") or "")
            if not hold_source:
                continue
            leader = scene_segment_by_id.get(hold_source)
            if not leader:
                errors.append(f"{item.get('scene_id')} 홀드 원본 장면을 찾을 수 없습니다.")
                continue
            leader_material = parts["videos"].get(leader.get("material_id"), {})
            follower_material = parts["videos"].get(segment.get("material_id"), {})
            leader_path = resolve_capcut_material_path(str(leader_material.get("path") or ""), destination)
            follower_path = resolve_capcut_material_path(str(follower_material.get("path") or ""), destination)
            if leader_path.resolve() != follower_path.resolve():
                errors.append(f"{item.get('scene_id')} 홀드 장면의 이미지 경로가 원본과 다릅니다.")
            elif leader_path.is_file() and sha256_file(leader_path) != sha256_file(follower_path):
                errors.append(f"{item.get('scene_id')} 홀드 장면의 이미지 해시가 원본과 다릅니다.")
            if item.get("motion_plan"):
                if static_visual_value_snapshot(leader) != static_visual_value_snapshot(segment):
                    errors.append(f"{item.get('scene_id')} 홀드 장면의 정적 geometry가 원본과 다릅니다.")
                leader_item = mapping_by_scene.get(hold_source) or {}
                leader_plan = leader_item.get("motion_plan") or {}
                follower_plan = item.get("motion_plan") or {}
                for left, right, label in (
                    (leader_plan.get("end_scale"), follower_plan.get("start_scale"), "scale"),
                    (leader_plan.get("end_x"), follower_plan.get("start_x"), "x"),
                    (leader_plan.get("end_y"), follower_plan.get("start_y"), "y"),
                ):
                    if left is None or right is None or abs(float(left) - float(right)) > 1e-9:
                        errors.append(f"{item.get('scene_id')} 홀드 motion {label} 경계가 연속되지 않습니다.")
            elif visual_value_snapshot(leader) != visual_value_snapshot(segment):
                errors.append(f"{item.get('scene_id')} 홀드 장면의 크롭·위치·배율이 원본과 다릅니다.")
            if visual_value_snapshot(leader_material) != visual_value_snapshot(follower_material):
                errors.append(f"{item.get('scene_id')} 홀드 material 크롭·배율이 원본과 다릅니다.")
        expected_visuals = len(storyboard.get("beats") or [])
        if len(set(resolved_paths)) != expected_visuals:
            errors.append(
                f"narration-hold의 실제 영상 경로는 beat 수와 같아야 합니다: "
                f"기대 {expected_visuals}개, 현재 {len(set(resolved_paths))}개"
            )
        visible_changes = sum(
            1 for left, right in zip(resolved_paths, resolved_paths[1:]) if left != right
        )
        expected_changes = max(0, expected_visuals - 1)
        if visible_changes != expected_changes:
            errors.append(
                f"narration-hold의 실제 화면 전환은 beat 경계 수와 같아야 합니다: "
                f"기대 {expected_changes}회, 현재 {visible_changes}회"
            )
        for mini_path in active_mini_draft_paths(destination):
            mini = read_json(mini_path)
            mini_segments = {
                item.get("id"): item
                for item in (mini.get("mini_draft_data") or {}).get("segments", [])
                if isinstance(item, dict) and item.get("id")
            }
            for item in scene_mappings:
                current = mini_segments.get(item.get("segment_id"))
                hold_source = str(item.get("hold_source_scene_id") or "")
                expected_item = mapping_by_scene.get(hold_source) if hold_source else item
                if isinstance(current, dict) and isinstance(expected_item, dict):
                    expected_segment = expected_item.get("template_mini_segment_visual")
                    expected_material = expected_item.get("template_mini_material_visual")
                    if not isinstance(expected_segment, dict) or not isinstance(
                        expected_material, dict
                    ):
                        errors.append(
                            f"mini_draft {item.get('scene_id')} 템플릿 geometry snapshot이 없습니다."
                        )
                    else:
                        expected_rendered_segment = copy.deepcopy(expected_segment)
                        plan = item.get("motion_plan")
                        if isinstance(plan, dict):
                            apply_motion_plan(
                                expected_rendered_segment,
                                str(item.get("scene_id") or ""),
                                plan,
                                mini=True,
                            )
                        if visual_value_snapshot(current) != visual_value_snapshot(expected_rendered_segment):
                            errors.append(
                                f"mini_draft {item.get('scene_id')} segment geometry가 템플릿 기준과 다릅니다."
                            )
                        current_material = current.get("material")
                        if not isinstance(current_material, dict) or visual_value_snapshot(
                            current_material
                        ) != visual_value_snapshot(expected_material):
                            errors.append(
                                f"mini_draft {item.get('scene_id')} material geometry가 템플릿 기준과 다릅니다."
                            )
                if not hold_source:
                    continue
                follower = mini_segments.get(item.get("segment_id"))
                leader_item = mapping_by_scene.get(hold_source) or {}
                leader = mini_segments.get(leader_item.get("segment_id"))
                if not isinstance(follower, dict) or not isinstance(leader, dict):
                    errors.append(f"mini_draft 홀드 세그먼트를 찾을 수 없습니다: {item.get('scene_id')}")
                    continue
                if item.get("motion_plan"):
                    if static_visual_value_snapshot(follower) != static_visual_value_snapshot(leader):
                        errors.append(
                            f"mini_draft {item.get('scene_id')} 홀드 정적 geometry가 다릅니다."
                        )
                elif visual_value_snapshot(follower) != visual_value_snapshot(leader):
                    errors.append(f"mini_draft {item.get('scene_id')} 홀드 크롭·위치·배율이 다릅니다.")
                follower_material = follower.get("material")
                leader_material = leader.get("material")
                if not isinstance(follower_material, dict) or not isinstance(
                    leader_material, dict
                ) or visual_value_snapshot(follower_material) != visual_value_snapshot(
                    leader_material
                ):
                    errors.append(
                        f"mini_draft {item.get('scene_id')} 홀드 material 크롭·배율이 다릅니다."
                    )
                follower_path = str((follower.get("material") or {}).get("path") or "")
                leader_path = str((leader.get("material") or {}).get("path") or "")
                if follower_path != leader_path:
                    errors.append(f"mini_draft {item.get('scene_id')} 홀드 이미지 경로가 다릅니다.")

    project = read_json(project_dir / "project.json")
    narration_audio = project.get("narration_audio") if isinstance(project, dict) else None
    if isinstance(narration_audio, dict) and str(narration_audio.get("path") or "").strip():
        try:
            _track, audio_segment, audio_material = narration_audio_parts(draft, project)
            expected_duration = int(narration_audio.get("capcut_duration_us") or 0)
            source_range = audio_segment.get("source_timerange") or {}
            target_range = audio_segment.get("target_timerange") or {}
            if target_range.get("start") != 0 or source_range.get("start") != 0:
                errors.append("Typecast 오디오 트랙은 0초부터 시작해야 합니다.")
            if target_range.get("duration") != expected_duration or source_range.get("duration") != expected_duration:
                errors.append("Typecast 오디오 세그먼트 길이가 project.json과 다릅니다.")
            if float(audio_segment.get("volume") or 0.0) != 1.0:
                errors.append("Typecast 오디오 볼륨은 0dB(volume 1.0)여야 합니다.")
            expected_audio_path = project_path(project_dir, str(narration_audio.get("path") or ""))
            material_path = Path(str(audio_material.get("path") or ""))
            if material_path.resolve() != expected_audio_path.resolve():
                errors.append("Typecast 오디오 소재 경로가 project.json과 다릅니다.")
            elif sha256_file(material_path) != str(narration_audio.get("sha256") or ""):
                errors.append("Typecast 오디오 소재 해시가 project.json과 다릅니다.")
        except (CCHelperError, OSError) as exc:
            errors.append(str(exc))
    meta = read_json(destination / "draft_meta_info.json")
    if meta.get("draft_name") != mapping.get("draft_name"):
        errors.append("캡컷 표시명이 매핑과 다릅니다.")
    if meta.get("draft_fold_path") != str(destination):
        errors.append("draft_fold_path가 새 프로젝트 경로와 다릅니다.")
    if meta.get("draft_id") == read_json(Path(mapping["base_draft"]) / "draft_meta_info.json").get("draft_id"):
        errors.append("원본과 새 프로젝트의 draft_id가 같습니다.")
    mirror_paths = active_draft_mirror_paths(destination)
    if len({sha256_file(path) for path in mirror_paths}) != 1:
        errors.append("현재 draft_info/template-2 미러 스냅샷의 내용이 서로 다릅니다.")
    backup_mirrors = sorted(destination.rglob("draft_info.json.bak"))
    if mirror_paths and any(sha256_file(path) != sha256_file(mirror_paths[0]) for path in backup_mirrors):
        warnings.append("draft_info.json.bak은 복구본이라 현재 미러와 달라도 유지합니다.")
    for path in active_template_paths(destination):
        template = read_json(path)
        if int(template.get("duration") or 0) != int(mapping.get("total_duration_us") or 0):
            errors.append(f"template.json 전체 길이가 매핑과 다릅니다: {path}")
    stale_tokens = []
    for item in mapping.get("scene_mappings", []):
        old_path = str(item.get("old_path") or "")
        if not old_path or old_path.startswith("##_draftpath_placeholder_"):
            continue
        candidate = Path(old_path)
        if candidate.is_absolute():
            try:
                candidate.resolve().relative_to(destination.resolve())
                continue
            except ValueError:
                pass
        stale_tokens.append(old_path)
    stale_tokens.append(str(mapping.get("base_draft") or ""))
    stale_found = False
    current_text_paths = [
        *active_draft_mirror_paths(destination),
        *active_template_paths(destination),
        *active_mini_draft_paths(destination),
        destination / "draft_meta_info.json",
    ]
    for path in (item for item in current_text_paths if item.is_file()):
        if path.stat().st_size > 25 * 1024 * 1024:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if any(token and token in text for token in stale_tokens):
            stale_found = True
            break
    if stale_found:
        errors.append("복제된 프로젝트에 원본 외부 경로가 남아 있습니다.")
    errors.extend(
        validate_final_visual_qc(project_dir, destination, draft, mapping, storyboard)
    )
    return errors, warnings


def validate_command(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir).expanduser().resolve()
    if args.stage == "research":
        errors, warnings = validate_research(project_dir)
    elif args.stage == "assets":
        errors, warnings = validate_assets(project_dir)
    else:
        errors, warnings = validate_capcut(project_dir)
    payload = {
        "stage": args.stage,
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
    }
    print_json(payload)
    if errors:
        raise SystemExit(2)


def doctor(args: argparse.Namespace) -> None:
    base_draft = Path(args.base_draft).expanduser().resolve()
    capcut_root = Path(args.capcut_root).expanduser().resolve()
    payload = {
        "python": sys.version.split()[0],
        "pillow": pillow_available(),
        "ffmpeg": executable_available("ffmpeg"),
        "ffprobe": executable_available("ffprobe"),
        "capcut_root": str(capcut_root),
        "capcut_root_exists": capcut_root.is_dir(),
        "capcut_running": capcut_running(),
        "base_template": inspect_template(base_draft),
    }
    if args.json:
        print_json(payload)
    else:
        for key, value in payload.items():
            print(f"{key}: {value}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cc_helper.py",
        description="이슈 자료를 15장면 캡컷 로컬 초안으로 인계합니다.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor_parser = subparsers.add_parser("doctor", help="실행 환경과 캡컷 템플릿을 확인합니다.")
    doctor_parser.add_argument("--json", action="store_true")
    doctor_parser.add_argument("--base-draft", default=str(DEFAULT_BASE_DRAFT))
    doctor_parser.add_argument("--capcut-root", default=str(DEFAULT_CAPCUT_ROOT))
    doctor_parser.set_defaults(handler=doctor)

    init_parser = subparsers.add_parser("init", help="선택된 이슈의 작업 폴더를 만듭니다.")
    init_parser.add_argument("--title", required=True)
    init_parser.add_argument("--slug", default="")
    init_parser.add_argument("--candidate-id", default="direct-topic")
    init_parser.add_argument("--category", default="other")
    init_parser.add_argument("--source-url", action="append", default=[])
    init_parser.add_argument("--bgm-file", default="")
    init_parser.add_argument("--project-dir", default="")
    init_parser.add_argument("--projects-root", default=str(DEFAULT_PROJECTS_ROOT))
    init_parser.set_defaults(handler=init_project)

    collect_parser = subparsers.add_parser("collect-assets", help="웹·로컬 에셋을 수집하고 세로 화면으로 정규화합니다.")
    collect_parser.add_argument("--project-dir", required=True)
    collect_parser.add_argument("--source-url", action="append", default=[])
    collect_parser.add_argument("--asset-url", action="append", default=[])
    collect_parser.add_argument("--local-file", action="append", default=[])
    collect_parser.add_argument("--max-assets", type=int, default=3)
    collect_parser.add_argument("--list-only", action="store_true")
    collect_parser.add_argument(
        "--community-capture",
        action="store_true",
        help="커뮤니티 캡처 전체를 CapCut 안전 영역 안에 크롭 없이 배치합니다.",
    )
    collect_parser.add_argument("--synthetic", action="store_true")
    collect_parser.add_argument(
        "--text-free",
        action="store_true",
        help="합성 이미지에 편집 문구·날짜·출처 표기가 없음을 눈으로 확인합니다.",
    )
    collect_parser.add_argument("--derived-from", default="")
    collect_parser.add_argument(
        "--person-class",
        choices=("none", "public_figure", "private_person", "minor", "victim"),
        default="none",
    )
    collect_parser.add_argument("--relevance", default="direct")
    collect_parser.set_defaults(handler=collect_assets)

    readable_parser = subparsers.add_parser(
        "compose-readable-source",
        help="원본 글자 픽셀만 crop·확대해 1000x720 가독성 카드로 합성합니다.",
    )
    readable_parser.add_argument("--source-file", required=True)
    readable_parser.add_argument("--output-file", required=True)
    readable_parser.add_argument("--panel", action="append", default=[])
    readable_parser.set_defaults(handler=compose_readable_source)

    review_parser = subparsers.add_parser(
        "review-asset",
        help="수집된 사진의 내용·품질·출처 역할과 공개 인물 파생 상태를 검수합니다.",
    )
    review_parser.add_argument("--project-dir", required=True)
    review_parser.add_argument("--asset-id", required=True)
    review_parser.add_argument("--evidence-role", choices=sorted(EVIDENCE_ROLES), required=True)
    review_parser.add_argument("--fact-id", action="append", default=[])
    review_parser.add_argument("--content-description", default="")
    review_parser.add_argument("--approve-content", action="store_true")
    review_parser.add_argument("--approve-quality", action="store_true")
    review_parser.add_argument("--main-subject-visible", action="store_true")
    review_parser.add_argument("--crop-safe", action="store_true")
    review_parser.add_argument("--fallback-reason", default="")
    review_parser.add_argument("--portrait-style", choices=(PORTRAIT_STYLE,), default="")
    review_parser.add_argument("--approve-identity", action="store_true")
    review_parser.add_argument("--approve-clothing", action="store_true")
    review_parser.add_argument("--approve-context", action="store_true")
    review_parser.add_argument(
        "--portrait-style-strength", choices=(PORTRAIT_STYLE_STRENGTH,), default=""
    )
    review_parser.add_argument(
        "--portrait-eye-motif", choices=(PORTRAIT_EYE_MOTIF,), default=""
    )
    review_parser.add_argument("--approve-style-obvious", action="store_true")
    review_parser.add_argument("--approve-eye-motif", action="store_true")
    review_parser.add_argument("--approve-ruler-ticks", action="store_true")
    review_parser.add_argument("--confirm-eye-motif-editorial-only", action="store_true")
    review_parser.add_argument("--non-identifying", action="store_true")
    review_parser.add_argument("--people-visible", action="store_true")
    review_parser.add_argument("--people-treatment", choices=sorted(PEOPLE_TREATMENTS), default="")
    review_parser.add_argument("--display-focus", choices=sorted(DISPLAY_FOCUS_VALUES), default="")
    review_parser.add_argument("--preview-checked", action="store_true")
    review_parser.add_argument("--evidence-readable", action="store_true")
    review_parser.add_argument("--visual-anchor-term", action="append", default=[])
    review_parser.set_defaults(handler=review_asset)

    prepare_parser = subparsers.add_parser("prepare-capcut", help="캡컷 복제 계획을 생성합니다.")
    prepare_parser.add_argument("--project-dir", required=True)
    prepare_parser.add_argument("--base-draft", default=str(DEFAULT_BASE_DRAFT))
    prepare_parser.add_argument("--capcut-root", default=str(DEFAULT_CAPCUT_ROOT))
    prepare_parser.add_argument("--destination-name", default="")
    prepare_parser.add_argument("--draft-name", default="")
    prepare_parser.add_argument("--dry-run", action="store_true")
    prepare_parser.set_defaults(handler=prepare_capcut)

    clone_parser = subparsers.add_parser("clone-capcut", help="승인된 새 캡컷 초안을 복제합니다.")
    clone_parser.add_argument("--project-dir", required=True)
    clone_parser.add_argument("--confirm", action="store_true")
    clone_parser.set_defaults(handler=clone_capcut)

    retime_parser = subparsers.add_parser(
        "retime-capcut", help="복제된 기존 CapCut 초안을 내레이션 타이밍에 맞춥니다."
    )
    retime_parser.add_argument("--project-dir", required=True)
    retime_parser.add_argument("--confirm-existing", action="store_true")
    retime_parser.set_defaults(handler=retime_capcut)

    validate_parser = subparsers.add_parser("validate", help="프로젝트 단계를 검증합니다.")
    validate_parser.add_argument("--project-dir", required=True)
    validate_parser.add_argument("--stage", choices=("research", "assets", "capcut"), required=True)
    validate_parser.set_defaults(handler=validate_command)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.handler(args)
    except CCHelperError as exc:
        print(f"cc_helper 오류: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
