#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import getpass
import hashlib
import json
import os
import shutil
import ssl
import subprocess
import sys
import tempfile
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any
from urllib import error, request

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:  # pragma: no cover - reported by doctor
    Image = ImageDraw = ImageFont = None  # type: ignore[assignment]


MODES = ("story", "romance", "price")
PUBLISHABLE_RIGHTS = {"owned", "licensed", "permission_confirmed"}
REVIEW_RIGHTS = PUBLISHABLE_RIGHTS | {"unknown", "review_required"}
ALL_RIGHTS = REVIEW_RIGHTS | {"not_permitted"}
OLD_PLUGINS = {"story2short", "romance-drama-shorts", "price-breakdown-shorts"}
KST = dt.timezone(dt.timedelta(hours=9))
WIDTH = 720
HEIGHT = 1280
REVIEW_WIDTH = 540
REVIEW_HEIGHT = 960
FPS = 30
FONT_CANDIDATES = (
    Path("/System/Library/Fonts/AppleSDGothicNeo.ttc"),
    Path("/System/Library/Fonts/Supplemental/AppleGothic.ttf"),
    Path("/Library/Fonts/NotoSansKR-Regular.otf"),
    Path("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
)
UNIT_FACTORS = {
    "g": (Decimal("1"), "g"),
    "kg": (Decimal("1000"), "g"),
    "ml": (Decimal("1"), "ml"),
    "l": (Decimal("1000"), "ml"),
    "개": (Decimal("1"), "count"),
    "count": (Decimal("1"), "count"),
}
FORBIDDEN_DISCOUNTS = {"coupon", "member", "first_purchase", "points"}
FORBIDDEN_PRICE_CLAIMS = ("폭리", "실제 원가", "순이익", "마진을 남겨")
TYPECAST_TTS_URL = "https://api.typecast.ai/v1/text-to-speech"
TYPECAST_MODEL = "ssfm-v30"
TYPECAST_DEFAULT_VOICE_ID = "tc_68257f68bc6e3c161ab5078d"
TYPECAST_KEYCHAIN_SERVICE = "news2shorts.typecast.api-key"


class ShortsStudioError(RuntimeError):
    pass


def now_iso() -> str:
    return dt.datetime.now(KST).isoformat(timespec="seconds")


def clean(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def decimal(value: object, label: str) -> Decimal:
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ShortsStudioError(f"{label}은 숫자여야 합니다.") from None
    if number < 0:
        raise ShortsStudioError(f"{label}은 음수일 수 없습니다.")
    return number


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ShortsStudioError(f"JSON을 읽을 수 없습니다: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ShortsStudioError(f"JSON 최상위 값은 객체여야 합니다: {path}")
    return value


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def find_font() -> Path:
    for path in FONT_CANDIDATES:
        if path.is_file():
            return path
    raise ShortsStudioError("한글 렌더용 글꼴을 찾을 수 없습니다.")


def tool(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise ShortsStudioError(f"필수 도구를 찾을 수 없습니다: {name}")
    return path


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    if result.returncode:
        detail = (result.stderr or result.stdout).strip()
        raise ShortsStudioError(f"명령 실행에 실패했습니다: {command[0]}: {detail[-1200:]}")
    return result


def resolve_input_file(input_file: Path, raw: object, label: str) -> Path:
    value = clean(raw)
    if not value:
        raise ShortsStudioError(f"{label} 경로가 필요합니다.")
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = (input_file.parent / path).resolve()
    if not path.is_file():
        raise ShortsStudioError(f"{label} 파일이 없습니다: {path}")
    return path


def copy_asset(source: Path, destination: Path) -> str:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return destination.as_posix()


def rights_status(value: object, label: str) -> str:
    status = clean(value)
    if status not in ALL_RIGHTS:
        raise ShortsStudioError(f"{label} 권리 상태가 잘못되었습니다: {status or 'empty'}")
    if status == "not_permitted":
        raise ShortsStudioError(f"사용이 허용되지 않은 자산입니다: {label}")
    return status


def normalize_audio(input_file: Path, project_dir: Path, payload: dict[str, Any]) -> dict[str, Any]:
    raw = payload.get("audio")
    if not isinstance(raw, dict) or not clean(raw.get("path")):
        return {
            "path": None,
            "provider": clean(raw.get("provider")) if isinstance(raw, dict) else None,
            "voice_id": clean(raw.get("voice_id")) if isinstance(raw, dict) else TYPECAST_DEFAULT_VOICE_ID,
            "tempo": float(raw.get("tempo") or 1.0) if isinstance(raw, dict) else 1.0,
        }
    source = resolve_input_file(input_file, raw.get("path"), "audio.path")
    destination = project_dir / "assets" / "audio" / f"voice{source.suffix.lower() or '.wav'}"
    copy_asset(source, destination)
    return {
        "path": destination.relative_to(project_dir).as_posix(),
        "provider": clean(raw.get("provider")),
        "voice_id": clean(raw.get("voice_id")) or TYPECAST_DEFAULT_VOICE_ID,
        "tempo": float(raw.get("tempo") or 1.0),
        "sha256": sha256(destination),
    }


def typecast_api_key_record() -> tuple[str, str | None]:
    environment_key = os.environ.get("TYPECAST_API_KEY", "").strip()
    if environment_key:
        return environment_key, "environment"
    security = shutil.which("security")
    if not security:
        return "", None
    result = subprocess.run(
        [security, "find-generic-password", "-a", getpass.getuser(), "-s", TYPECAST_KEYCHAIN_SERVICE, "-w"],
        check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
    )
    key = result.stdout.strip() if result.returncode == 0 else ""
    return (key, "keychain") if key else ("", None)


def ensure_typecast_audio(project_dir: Path, project: dict[str, Any]) -> None:
    audio = project.get("audio") or {}
    relative = clean(audio.get("path"))
    if relative and (project_dir / relative).is_file():
        return
    if clean(audio.get("provider")) != "typecast":
        raise ShortsStudioError("최종 음성은 Typecast만 사용할 수 있습니다.")
    api_key, key_source = typecast_api_key_record()
    if not api_key:
        raise ShortsStudioError(
            "Typecast API 키가 없습니다. news2shorts.typecast.api-key 키체인 항목 또는 "
            "TYPECAST_API_KEY를 설정하세요. 로컬 TTS로 자동 대체하지 않습니다."
        )
    narration = " ".join(clean(scene.get("narration")) for scene in project.get("scenes") or []).strip()
    if not narration or len(narration) > 2000:
        raise ShortsStudioError("Typecast 연속 내레이션은 1~2,000자여야 합니다.")
    tempo = min(2.0, max(0.5, float(audio.get("tempo") or 1.0)))
    payload = {
        "voice_id": clean(audio.get("voice_id")) or TYPECAST_DEFAULT_VOICE_ID,
        "text": narration,
        "model": TYPECAST_MODEL,
        "language": "kor",
        "prompt": {"emotion_type": "smart", "previous_text": "", "next_text": ""},
        "output": {"target_lufs": -14.0, "audio_pitch": 0, "audio_tempo": tempo, "audio_format": "wav"},
        "seed": 42,
    }
    req = request.Request(
        TYPECAST_TTS_URL,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"X-API-KEY": api_key, "Content-Type": "application/json", "User-Agent": "shorts-studio/0.1"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=60, context=ssl.create_default_context()) as response:
            content = response.read()
    except error.HTTPError as exc:
        detail = {401: "API 키", 402: "사용량 또는 결제 상태", 429: "요청 한도"}.get(exc.code, "요청 설정")
        raise ShortsStudioError(f"Typecast TTS 요청 실패: HTTP {exc.code}. {detail}를 확인하세요.") from exc
    except error.URLError as exc:
        raise ShortsStudioError(f"Typecast TTS 연결 실패: {exc.reason}") from exc
    if len(content) < 12 or content[:4] != b"RIFF" or content[8:12] != b"WAVE":
        raise ShortsStudioError("Typecast 응답이 WAV 오디오가 아닙니다.")
    target = project_dir / "assets" / "audio" / "voice.wav"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)
    audio.update({
        "path": target.relative_to(project_dir).as_posix(),
        "provider": "typecast",
        "key_source": key_source,
        "sha256": sha256(target),
    })
    project["audio"] = audio


def normalize_story(input_file: Path, project_dir: Path, payload: dict[str, Any], project_rights: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    source = resolve_input_file(input_file, payload.get("source_video"), "source_video")
    source_rights = rights_status(payload.get("source_rights") or project_rights, "source_video")
    destination = project_dir / "assets" / "source" / f"source{source.suffix.lower()}"
    copy_asset(source, destination)
    scenes_raw = payload.get("scenes")
    if not isinstance(scenes_raw, list) or not scenes_raw:
        raise ShortsStudioError("story 모드는 scenes가 필요합니다.")
    scenes: list[dict[str, Any]] = []
    for index, raw in enumerate(scenes_raw, start=1):
        if not isinstance(raw, dict):
            raise ShortsStudioError(f"story scene {index}가 객체가 아닙니다.")
        start = float(decimal(raw.get("source_start"), f"scene {index} source_start"))
        end = float(decimal(raw.get("source_end"), f"scene {index} source_end"))
        if end <= start:
            raise ShortsStudioError(f"story scene {index} source_end는 source_start보다 커야 합니다.")
        observed = clean(raw.get("observed_action"))
        if len(observed) < 4:
            raise ShortsStudioError(f"story scene {index} observed_action을 구체적으로 기록하세요.")
        scenes.append({
            "id": clean(raw.get("id")) or f"scene-{index:02d}",
            "duration": round(end - start, 3),
            "source_start": start,
            "source_end": end,
            "visual": destination.relative_to(project_dir).as_posix(),
            "visual_type": "video",
            "headline": clean(raw.get("headline")) or clean(payload.get("title")),
            "caption": clean(raw.get("caption")),
            "narration": clean(raw.get("narration")),
            "observed_action": observed,
        })
    asset = {
        "id": "source-video",
        "path": destination.relative_to(project_dir).as_posix(),
        "rights_status": source_rights,
        "sha256": sha256(destination),
        "synthetic": False,
    }
    return scenes, [asset], {"source_video": asset["path"], "grounding_required": True}


def normalize_romance(input_file: Path, project_dir: Path, payload: dict[str, Any], project_rights: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    scenes_raw = payload.get("scenes")
    if not isinstance(scenes_raw, list) or not scenes_raw:
        raise ShortsStudioError("romance 모드는 scenes가 필요합니다.")
    scenes: list[dict[str, Any]] = []
    assets: list[dict[str, Any]] = []
    for index, raw in enumerate(scenes_raw, start=1):
        if not isinstance(raw, dict):
            raise ShortsStudioError(f"romance scene {index}가 객체가 아닙니다.")
        source = resolve_input_file(input_file, raw.get("visual"), f"scene {index} visual")
        suffix = source.suffix.lower()
        destination = project_dir / "assets" / "visuals" / f"scene-{index:02d}{suffix}"
        copy_asset(source, destination)
        status = rights_status(raw.get("rights_status") or project_rights, f"scene {index} visual")
        synthetic = bool(raw.get("synthetic"))
        asset_id = f"visual-{index:02d}"
        assets.append({
            "id": asset_id,
            "path": destination.relative_to(project_dir).as_posix(),
            "rights_status": status,
            "sha256": sha256(destination),
            "synthetic": synthetic,
        })
        scenes.append({
            "id": clean(raw.get("id")) or f"scene-{index:02d}",
            "duration": float(decimal(raw.get("duration"), f"scene {index} duration")),
            "visual": destination.relative_to(project_dir).as_posix(),
            "visual_type": "video" if suffix in {".mp4", ".mov", ".m4v", ".webm"} else "image",
            "headline": clean(raw.get("headline")) or clean(payload.get("title")),
            "speaker": clean(raw.get("speaker")),
            "dialogue": clean(raw.get("dialogue")),
            "caption": clean(raw.get("caption")) or clean(raw.get("dialogue")),
            "narration": clean(raw.get("narration")) or clean(raw.get("dialogue")),
            "asset_id": asset_id,
        })
    if any(not scene["speaker"] or not scene["dialogue"] for scene in scenes):
        raise ShortsStudioError("romance 장면에는 speaker와 dialogue가 필요합니다.")
    return scenes, assets, {"synthetic_media": any(item["synthetic"] for item in assets), "lip_sync": False}


def normalize_unit(quantity: object, unit: object, label: str) -> tuple[Decimal, str]:
    unit_name = clean(unit).lower()
    if unit_name not in UNIT_FACTORS:
        raise ShortsStudioError(f"{label} 단위를 지원하지 않습니다: {unit_name}")
    value = decimal(quantity, label)
    factor, base = UNIT_FACTORS[unit_name]
    return value * factor, base


def calculate_price(payload: dict[str, Any]) -> dict[str, Any]:
    menu_price = decimal(payload.get("menu_price"), "menu_price")
    components_raw = payload.get("components")
    if not isinstance(components_raw, list) or not components_raw:
        raise ShortsStudioError("price 모드는 components가 필요합니다.")
    components: list[dict[str, Any]] = []
    total = Decimal("0")
    for index, raw in enumerate(components_raw, start=1):
        if not isinstance(raw, dict):
            raise ShortsStudioError(f"component {index}가 객체가 아닙니다.")
        discounts = raw.get("applied_discounts") or []
        if not isinstance(discounts, list):
            raise ShortsStudioError(f"component {index} applied_discounts는 배열이어야 합니다.")
        blocked = FORBIDDEN_DISCOUNTS & {clean(item).lower() for item in discounts}
        if blocked:
            raise ShortsStudioError(f"계산에 사용할 수 없는 할인이 포함됐습니다: {', '.join(sorted(blocked))}")
        package_quantity, package_unit = normalize_unit(raw.get("package_quantity"), raw.get("unit"), f"component {index} package_quantity")
        used_quantity, used_unit = normalize_unit(raw.get("quantity_used"), raw.get("used_unit") or raw.get("unit"), f"component {index} quantity_used")
        if package_unit != used_unit or package_quantity == 0:
            raise ShortsStudioError(f"component {index} 포장 단위와 사용 단위가 맞지 않습니다.")
        package_price = decimal(raw.get("package_price"), f"component {index} package_price")
        delivery = decimal(raw.get("delivery_fee") or 0, f"component {index} delivery_fee")
        if delivery and not bool(raw.get("delivery_unavoidable")):
            delivery = Decimal("0")
        exact_cost = package_price * used_quantity / package_quantity + delivery
        total += exact_cost
        components.append({
            "name": clean(raw.get("name")) or f"항목 {index}",
            "package_price": str(package_price),
            "package_quantity_base": str(package_quantity),
            "quantity_used_base": str(used_quantity),
            "base_unit": package_unit,
            "delivery_fee_included": str(delivery),
            "exact_cost": str(exact_cost.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
            "display_cost": str(exact_cost.quantize(Decimal("100"), rounding=ROUND_HALF_UP)),
        })
    display_total = total.quantize(Decimal("100"), rounding=ROUND_HALF_UP)
    ratio = (total / menu_price * Decimal("100")) if menu_price else Decimal("0")
    return {
        "menu_price": str(menu_price),
        "components": components,
        "exact_material_cost": str(total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
        "display_material_cost": str(display_total),
        "material_to_menu_percent": str(ratio.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)),
    }


def normalize_price(input_file: Path, project_dir: Path, payload: dict[str, Any], project_rights: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    calculation = calculate_price(payload)
    evidence_raw = payload.get("evidence")
    if not isinstance(evidence_raw, list) or not evidence_raw:
        raise ShortsStudioError("price 모드는 evidence가 필요합니다.")
    assets: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []
    for index, raw in enumerate(evidence_raw, start=1):
        if not isinstance(raw, dict):
            raise ShortsStudioError(f"evidence {index}가 객체가 아닙니다.")
        status = rights_status(raw.get("rights_status") or project_rights, f"evidence {index}")
        item: dict[str, Any] = {
            "id": clean(raw.get("id")) or f"evidence-{index:02d}",
            "source": clean(raw.get("source")),
            "captured_at": clean(raw.get("captured_at")),
            "price_conditions_visible": bool(raw.get("price_conditions_visible")),
            "rights_status": status,
        }
        if not item["source"] or not item["captured_at"]:
            raise ShortsStudioError(f"evidence {index}에는 source와 captured_at이 필요합니다.")
        if clean(raw.get("path")):
            source = resolve_input_file(input_file, raw.get("path"), f"evidence {index} path")
            destination = project_dir / "assets" / "evidence" / f"evidence-{index:02d}{source.suffix.lower()}"
            copy_asset(source, destination)
            item["path"] = destination.relative_to(project_dir).as_posix()
            assets.append({
                "id": item["id"], "path": item["path"], "rights_status": status,
                "sha256": sha256(destination), "synthetic": bool(raw.get("synthetic")),
            })
        evidence.append(item)
    title = clean(payload.get("title"))
    components = calculation["components"]
    scenes: list[dict[str, Any]] = [{
        "id": "scene-01", "duration": 2.0, "headline": title,
        "caption": f"메뉴 가격 {int(Decimal(calculation['menu_price'])):,}원",
        "narration": f"확인한 메뉴 가격은 {int(Decimal(calculation['menu_price'])):,}원입니다.",
        "visual_type": "card", "card_kind": "menu",
    }]
    for index, item in enumerate(components, start=2):
        scenes.append({
            "id": f"scene-{index:02d}", "duration": 2.4,
            "headline": item["name"],
            "caption": f"사용분 약 {int(Decimal(item['display_cost'])):,}원",
            "narration": f"{item['name']} 사용분은 약 {int(Decimal(item['display_cost'])):,}원입니다.",
            "visual_type": "card", "card_kind": "component",
        })
    scenes.append({
        "id": f"scene-{len(scenes) + 1:02d}", "duration": 3.0,
        "headline": "재료값만 다시 계산하면",
        "caption": f"약 {int(Decimal(calculation['display_material_cost'])):,}원",
        "narration": f"피할 수 없는 배송비를 포함한 재료 합계는 약 {int(Decimal(calculation['display_material_cost'])):,}원입니다.",
        "visual_type": "card", "card_kind": "conclusion",
    })
    return scenes, assets, {"calculation": calculation, "evidence": evidence}


def init_project(args: argparse.Namespace) -> None:
    input_file = Path(args.input).expanduser().resolve()
    payload = read_json(input_file)
    if clean(payload.get("plugin")) in OLD_PLUGINS or int(payload.get("schema_version") or 1) != 1:
        raise ShortsStudioError("기존 플러그인 프로젝트는 호환하거나 가져오지 않습니다. Shorts Studio v1 입력을 사용하세요.")
    title = clean(payload.get("title"))
    if not title:
        raise ShortsStudioError("title이 필요합니다.")
    raw_rights = payload.get("rights")
    if not isinstance(raw_rights, dict):
        raise ShortsStudioError("rights 객체가 필요합니다.")
    project_rights = rights_status(raw_rights.get("status"), "project")
    project_dir = Path(args.project_dir).expanduser().resolve()
    if project_dir.exists() and any(project_dir.iterdir()):
        raise ShortsStudioError(f"비어 있지 않은 프로젝트는 덮어쓰지 않습니다: {project_dir}")
    project_dir.mkdir(parents=True, exist_ok=True)
    audio = normalize_audio(input_file, project_dir, payload)
    if args.mode == "story":
        scenes, assets, mode_data = normalize_story(input_file, project_dir, payload, project_rights)
    elif args.mode == "romance":
        scenes, assets, mode_data = normalize_romance(input_file, project_dir, payload, project_rights)
    else:
        scenes, assets, mode_data = normalize_price(input_file, project_dir, payload, project_rights)
    project = {
        "plugin": "shorts-studio",
        "schema_version": 1,
        "mode": args.mode,
        "slug": clean(payload.get("slug")) or project_dir.name,
        "title": title,
        "status": "initialized",
        "created_at": now_iso(),
        "rights": {"status": project_rights, "permission_reference": clean(raw_rights.get("permission_reference"))},
        "approvals": {"assets": False, "content": False, "publish": False, "synthetic_disclosure": False},
        "audio": audio,
        "assets": assets,
        "scenes": scenes,
        "mode_data": mode_data,
        "outputs": {"review": None, "final": None, "upload_package": False},
    }
    write_json(project_dir / "project.json", project)
    write_json(project_dir / "input.snapshot.json", payload)
    write_rights_manifest(project_dir, project)
    print(json.dumps({"project_dir": str(project_dir), "mode": args.mode, "status": project["status"]}, ensure_ascii=False, indent=2))


def load_project(mode: str, project_dir: Path) -> dict[str, Any]:
    project = read_json(project_dir / "project.json")
    if project.get("plugin") != "shorts-studio" or project.get("schema_version") != 1:
        raise ShortsStudioError("기존 플러그인 프로젝트는 지원하지 않습니다.")
    if project.get("mode") != mode:
        raise ShortsStudioError(f"프로젝트 모드가 명령과 다릅니다: {project.get('mode')}/{mode}")
    return project


def write_rights_manifest(project_dir: Path, project: dict[str, Any]) -> None:
    write_json(project_dir / "rights-manifest.json", {
        "plugin": "shorts-studio",
        "mode": project["mode"],
        "project_rights": project["rights"],
        "assets": project["assets"],
        "publication_ready": bool(project["approvals"].get("publish")),
        "updated_at": now_iso(),
    })


def project_errors(project_dir: Path, project: dict[str, Any], publish_ready: bool) -> list[str]:
    errors: list[str] = []
    if project.get("mode") not in MODES:
        errors.append("지원하지 않는 mode입니다.")
    scenes = project.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        errors.append("scenes가 비어 있습니다.")
        scenes = []
    for scene in scenes:
        if not isinstance(scene, dict) or float(scene.get("duration") or 0) <= 0:
            errors.append("모든 장면에는 양수 duration이 필요합니다.")
            continue
        if not clean(scene.get("caption")) or not clean(scene.get("narration")):
            errors.append(f"장면 caption/narration이 필요합니다: {scene.get('id')}")
        if project["mode"] == "story" and len(clean(scene.get("observed_action"))) < 4:
            errors.append(f"story 장면의 실제 행동 근거가 부족합니다: {scene.get('id')}")
        if project["mode"] == "romance" and (not clean(scene.get("speaker")) or not clean(scene.get("dialogue"))):
            errors.append(f"romance 장면의 화자·대사가 부족합니다: {scene.get('id')}")
    for asset in project.get("assets") or []:
        path = project_dir / clean(asset.get("path"))
        if not path.is_file():
            errors.append(f"자산 파일이 없습니다: {asset.get('path')}")
        elif clean(asset.get("sha256")) != sha256(path):
            errors.append(f"자산 해시가 다릅니다: {asset.get('path')}")
    status = clean(project.get("rights", {}).get("status"))
    if status == "not_permitted":
        errors.append("프로젝트 권리가 not_permitted입니다.")
    if publish_ready:
        approvals = project.get("approvals") or {}
        for stage in ("assets", "content", "publish"):
            if approvals.get(stage) is not True:
                errors.append(f"{stage} 승인이 필요합니다.")
        if status not in PUBLISHABLE_RIGHTS:
            errors.append(f"최종 게시 가능한 프로젝트 권리가 아닙니다: {status}")
        for asset in project.get("assets") or []:
            if clean(asset.get("rights_status")) not in PUBLISHABLE_RIGHTS:
                errors.append(f"최종 게시 가능한 자산 권리가 아닙니다: {asset.get('id')}")
        if project["mode"] == "romance" and project.get("mode_data", {}).get("synthetic_media") and not approvals.get("synthetic_disclosure"):
            errors.append("합성 콘텐츠 표시 검토가 필요합니다.")
        audio = project.get("audio") or {}
        if clean(audio.get("provider")) != "typecast":
            errors.append("최종본 audio.provider는 typecast여야 합니다.")
        audio_path = project_dir / clean(audio.get("path")) if clean(audio.get("path")) else None
        if not audio_path or not audio_path.is_file():
            errors.append("최종본 Typecast 연속 음성 파일이 필요합니다.")
    if project["mode"] == "price":
        for phrase in FORBIDDEN_PRICE_CLAIMS:
            if phrase in clean(project.get("title")) or any(phrase in clean(scene.get("caption")) for scene in scenes):
                errors.append(f"가격 단정 표현을 사용할 수 없습니다: {phrase}")
        evidence = project.get("mode_data", {}).get("evidence") or []
        if not evidence:
            errors.append("가격 근거가 필요합니다.")
        if publish_ready and any(item.get("price_conditions_visible") is not True for item in evidence):
            errors.append("최종본은 모든 가격 조건 노출 검토가 필요합니다.")
    return sorted(set(errors))


def validate_command(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir).expanduser().resolve()
    project = load_project(args.mode, project_dir)
    errors = project_errors(project_dir, project, bool(args.publish_ready))
    result = {"ok": not errors, "mode": args.mode, "status": project.get("status"), "errors": errors}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if errors:
        raise ShortsStudioError("프로젝트 검증에 실패했습니다.")


def approve_command(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir).expanduser().resolve()
    project = load_project(args.mode, project_dir)
    stage = args.stage
    approvals = project["approvals"]
    if stage == "assets":
        if project["status"] != "initialized" or not args.confirm_assets:
            raise ShortsStudioError("assets 승인은 initialized 상태와 --confirm-assets가 필요합니다.")
        approvals["assets"] = True
        project["status"] = "assets_reviewed"
    elif stage == "content":
        if project["status"] != "assets_reviewed" or not args.confirm_content:
            raise ShortsStudioError("content 승인은 assets_reviewed 상태와 --confirm-content가 필요합니다.")
        if args.mode == "romance" and project.get("mode_data", {}).get("synthetic_media"):
            if not args.confirm_synthetic_disclosure:
                raise ShortsStudioError("합성 장면은 --confirm-synthetic-disclosure가 필요합니다.")
            approvals["synthetic_disclosure"] = True
        approvals["content"] = True
        project["status"] = "content_approved"
    else:
        if project["status"] != "draft_rendered" or not args.confirm_publish:
            raise ShortsStudioError("publish 승인은 draft_rendered 상태와 --confirm-publish가 필요합니다.")
        ensure_typecast_audio(project_dir, project)
        approvals["publish"] = True
        project["status"] = "publish_ready"
        errors = project_errors(project_dir, project, True)
        if errors:
            approvals["publish"] = False
            project["status"] = "draft_rendered"
            raise ShortsStudioError("publish 승인 조건을 충족하지 못했습니다: " + "; ".join(errors))
    write_json(project_dir / "project.json", project)
    write_rights_manifest(project_dir, project)
    print(json.dumps({"stage": stage, "status": project["status"], "approvals": approvals}, ensure_ascii=False, indent=2))


def wrap_text(draw: Any, value: str, font: Any, max_width: int, max_lines: int = 3) -> list[str]:
    words = value.split()
    if not words:
        return []
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
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1].rstrip("…") + "…"
    return lines


def render_overlay(project: dict[str, Any], scene: dict[str, Any], target: Path, width: int, height: int) -> None:
    if Image is None:
        raise ShortsStudioError("Pillow가 필요합니다.")
    price_card = project["mode"] == "price"
    image = Image.new("RGBA", (width, height), (31, 36, 45, 255) if price_card else (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    font_path = find_font()
    scale = width / WIDTH
    headline_font = ImageFont.truetype(str(font_path), max(28, int(52 * scale)), index=0)
    caption_font = ImageFont.truetype(str(font_path), max(34, int(66 * scale)), index=0)
    small_font = ImageFont.truetype(str(font_path), max(20, int(30 * scale)), index=0)
    margin = int(42 * scale)
    if price_card:
        draw.rounded_rectangle((margin, int(80 * scale), width - margin, int(210 * scale)), radius=int(22 * scale), fill="#FFD84D")
        draw.text((margin + int(24 * scale), int(112 * scale)), "SHORTS STUDIO · PRICE", font=small_font, fill="#191919")
        draw.rounded_rectangle((margin, int(300 * scale), width - margin, height - int(230 * scale)), radius=int(30 * scale), fill="#FFFFFF")
        headline_color = "#1E2530"
        caption_color = "#D5242F"
        headline_y = int(385 * scale)
        caption_y = int(650 * scale)
    else:
        draw.rectangle((0, 0, width, int(230 * scale)), fill=(0, 0, 0, 178))
        draw.rectangle((0, height - int(330 * scale), width, height), fill=(0, 0, 0, 190))
        headline_color = "#FFFFFF"
        caption_color = "#FFD84D"
        headline_y = int(55 * scale)
        caption_y = height - int(260 * scale)
    headline_lines = wrap_text(draw, clean(scene.get("headline")), headline_font, width - margin * 2, 3)
    for line in headline_lines:
        draw.text((margin, headline_y), line, font=headline_font, fill=headline_color, stroke_width=max(1, int(2 * scale)), stroke_fill="#000000")
        headline_y += int(66 * scale)
    caption_lines = wrap_text(draw, clean(scene.get("caption")), caption_font, width - margin * 2, 3)
    for line in caption_lines:
        draw.text((margin, caption_y), line, font=caption_font, fill=caption_color, stroke_width=max(2, int(4 * scale)), stroke_fill="#000000")
        caption_y += int(82 * scale)
    if project["mode"] == "romance" and clean(scene.get("speaker")):
        draw.text((margin, height - int(315 * scale)), clean(scene.get("speaker")), font=small_font, fill="#FFFFFF")
    image.save(target, format="PNG", optimize=True)


def create_scene_clip(project_dir: Path, project: dict[str, Any], scene: dict[str, Any], clip: Path, width: int, height: int) -> None:
    overlay = clip.with_suffix(".png")
    render_overlay(project, scene, overlay, width, height)
    duration = float(scene["duration"])
    visual = project_dir / clean(scene.get("visual")) if clean(scene.get("visual")) else None
    base_filter = f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},setsar=1"
    if visual and visual.is_file() and scene.get("visual_type") == "video":
        command = [tool("ffmpeg"), "-y", "-ss", str(float(scene.get("source_start") or 0)), "-i", str(visual), "-loop", "1", "-i", str(overlay), "-t", f"{duration:.3f}"]
        complex_filter = f"[0:v]{base_filter}[base];[base][1:v]overlay=0:0:format=auto,format=yuv420p[v]"
    elif visual and visual.is_file():
        command = [tool("ffmpeg"), "-y", "-loop", "1", "-i", str(visual), "-loop", "1", "-i", str(overlay), "-t", f"{duration:.3f}"]
        complex_filter = f"[0:v]{base_filter}[base];[base][1:v]overlay=0:0:format=auto,format=yuv420p[v]"
    else:
        command = [tool("ffmpeg"), "-y", "-loop", "1", "-i", str(overlay), "-t", f"{duration:.3f}"]
        complex_filter = "[0:v]format=yuv420p[v]"
    command += ["-filter_complex", complex_filter, "-map", "[v]", "-an", "-r", str(FPS), "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p", str(clip)]
    run(command)


def write_srt(project_dir: Path, scenes: list[dict[str, Any]]) -> Path:
    def stamp(seconds: float) -> str:
        millis = int(round(seconds * 1000))
        hours, millis = divmod(millis, 3_600_000)
        minutes, millis = divmod(millis, 60_000)
        secs, millis = divmod(millis, 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    elapsed = 0.0
    lines: list[str] = []
    for index, scene in enumerate(scenes, start=1):
        end = elapsed + float(scene["duration"])
        lines += [str(index), f"{stamp(elapsed)} --> {stamp(end)}", clean(scene.get("caption")), ""]
        elapsed = end
    target = project_dir / "captions.srt"
    target.write_text("\n".join(lines), encoding="utf-8")
    return target


def probe_media(path: Path) -> dict[str, Any]:
    result = run([tool("ffprobe"), "-v", "error", "-show_entries", "stream=codec_type,codec_name,width,height,r_frame_rate,sample_rate,channels:format=duration", "-of", "json", str(path)])
    return json.loads(result.stdout)


def create_thumbnail(project_dir: Path, project: dict[str, Any]) -> Path:
    if Image is None:
        raise ShortsStudioError("Pillow가 필요합니다.")
    target = project_dir / "thumbnail.jpg"
    canvas = Image.new("RGB", (WIDTH, HEIGHT), "#1F2630")
    draw = ImageDraw.Draw(canvas)
    font_path = find_font()
    label = ImageFont.truetype(str(font_path), 34, index=0)
    title_font = ImageFont.truetype(str(font_path), 74, index=0)
    draw.rounded_rectangle((48, 90, 672, 190), radius=24, fill="#FFD84D")
    draw.text((78, 120), f"SHORTS STUDIO · {project['mode'].upper()}", font=label, fill="#171717")
    y = 360
    for line in wrap_text(draw, project["title"], title_font, 620, 5):
        draw.text((50, y), line, font=title_font, fill="#FFFFFF", stroke_width=3, stroke_fill="#000000")
        y += 105
    canvas.save(target, format="JPEG", quality=92, optimize=True)
    return target


def render_command(args: argparse.Namespace) -> None:
    if args.draft == args.final:
        raise ShortsStudioError("--draft 또는 --final 중 하나만 선택하세요.")
    if args.no_tts and not args.draft:
        raise ShortsStudioError("--no-tts는 검토본에만 사용할 수 있습니다.")
    project_dir = Path(args.project_dir).expanduser().resolve()
    project = load_project(args.mode, project_dir)
    if args.draft and project["status"] not in {"content_approved", "draft_rendered"}:
        raise ShortsStudioError("검토 렌더는 content_approved 상태에서만 가능합니다.")
    if args.final and project["status"] != "publish_ready":
        raise ShortsStudioError("최종 렌더는 publish_ready 상태에서만 가능합니다.")
    errors = project_errors(project_dir, project, args.final)
    if errors:
        raise ShortsStudioError("렌더 전 검증에 실패했습니다: " + "; ".join(errors))
    audio = project.get("audio") or {}
    audio_path = project_dir / clean(audio.get("path")) if clean(audio.get("path")) else None
    if not args.no_tts and (not audio_path or not audio_path.is_file()):
        raise ShortsStudioError("음성 파일이 없습니다. 검토본은 --no-tts를 명시할 수 있습니다.")
    width, height = (REVIEW_WIDTH, REVIEW_HEIGHT) if args.draft else (WIDTH, HEIGHT)
    outputs = project_dir / "outputs"
    outputs.mkdir(parents=True, exist_ok=True)
    output = outputs / ("review.mp4" if args.draft else "short.mp4")
    work_dir = Path(tempfile.mkdtemp(prefix="shorts-studio-", dir=str(project_dir)))
    try:
        clips: list[Path] = []
        for index, scene in enumerate(project["scenes"], start=1):
            clip = work_dir / f"scene-{index:02d}.mp4"
            create_scene_clip(project_dir, project, scene, clip, width, height)
            clips.append(clip)
        concat_file = work_dir / "clips.txt"
        concat_file.write_text("\n".join(f"file '{path.as_posix()}'" for path in clips) + "\n", encoding="utf-8")
        silent_video = work_dir / "video.mp4"
        run([tool("ffmpeg"), "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c", "copy", str(silent_video)])
        total = sum(float(scene["duration"]) for scene in project["scenes"])
        if args.no_tts:
            run([tool("ffmpeg"), "-y", "-i", str(silent_video), "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-t", f"{total:.3f}", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", str(output)])
        else:
            run([tool("ffmpeg"), "-y", "-i", str(silent_video), "-i", str(audio_path), "-filter:a", f"apad,atrim=0:{total:.3f}", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", str(output)])
        edit_dir = project_dir / "edit-package"
        edit_scenes = edit_dir / "scenes"
        edit_scenes.mkdir(parents=True, exist_ok=True)
        for index, clip in enumerate(clips, start=1):
            shutil.copy2(clip, edit_scenes / f"scene-{index:02d}.mp4")
        srt = write_srt(project_dir, project["scenes"])
        shutil.copy2(srt, edit_dir / "captions.srt")
        if audio_path and audio_path.is_file():
            shutil.copy2(audio_path, edit_dir / f"voice{audio_path.suffix.lower()}")
        create_thumbnail(project_dir, project)
        media = probe_media(output)
        report = {
            "plugin": "shorts-studio", "mode": args.mode, "draft": args.draft,
            "output": output.relative_to(project_dir).as_posix(), "duration_planned": total,
            "media": media, "no_tts": bool(args.no_tts), "created_at": now_iso(),
        }
        write_json(project_dir / "render-report.json", report)
        project["status"] = "draft_rendered" if args.draft else "rendered"
        project["outputs"]["review" if args.draft else "final"] = output.relative_to(project_dir).as_posix()
        write_json(project_dir / "project.json", project)
        write_rights_manifest(project_dir, project)
        print(json.dumps({"output": str(output), "status": project["status"], "media": media}, ensure_ascii=False, indent=2))
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


def upload_package_command(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_dir).expanduser().resolve()
    project = load_project(args.mode, project_dir)
    if project["status"] != "rendered" or not (project_dir / "outputs" / "short.mp4").is_file():
        raise ShortsStudioError("최종 렌더가 완료된 프로젝트만 업로드 패키지를 만들 수 있습니다.")
    payload = {
        "title": project["title"][:100],
        "description": "제작 및 권리 검토가 완료된 Shorts Studio 영상입니다.",
        "tags": ["쇼츠", project["mode"]],
        "thumbnail": "thumbnail.jpg",
        "video": "outputs/short.mp4",
        "privacy_status": "review_required",
        "altered_content": "reviewed" if project["approvals"].get("synthetic_disclosure") else "not_declared",
        "upload_performed": False,
    }
    write_json(project_dir / "youtube-upload.json", payload)
    lines = [
        "# YouTube 업로드 정보", "", f"- 제목: {payload['title']}",
        f"- 영상: {payload['video']}", f"- 썸네일: {payload['thumbnail']}",
        "- 실제 업로드: 수행하지 않음", "- 공개 상태와 플랫폼 설정은 업로드 전에 사람이 확인",
    ]
    (project_dir / "youtube-upload.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    project["outputs"]["upload_package"] = True
    write_json(project_dir / "project.json", project)
    print(json.dumps({"youtube_upload_json": str(project_dir / 'youtube-upload.json'), "upload_performed": False}, ensure_ascii=False, indent=2))


def doctor_command(args: argparse.Namespace) -> None:
    font = next((path for path in FONT_CANDIDATES if path.is_file()), None)
    _, typecast_source = typecast_api_key_record()
    result = {
        "ok": bool(shutil.which("ffmpeg") and shutil.which("ffprobe") and Image is not None and font),
        "plugin": "shorts-studio",
        "modes": list(MODES),
        "ffmpeg": shutil.which("ffmpeg"),
        "ffprobe": shutil.which("ffprobe"),
        "pillow": Image is not None,
        "font": str(font) if font else None,
        "typecast_api_key_configured": bool(typecast_source),
        "typecast_api_key_source": typecast_source,
        "youtube_upload_supported": False,
        "legacy_project_import_supported": False,
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for key, value in result.items():
            print(f"{key}: {value}")
    if not result["ok"]:
        raise ShortsStudioError("필수 렌더 환경이 준비되지 않았습니다.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Approved-input Korean Shorts production studio")
    subparsers = parser.add_subparsers(dest="command", required=True)
    doctor = subparsers.add_parser("doctor")
    doctor.add_argument("--json", action="store_true")
    doctor.set_defaults(handler=doctor_command)
    for mode in MODES:
        mode_parser = subparsers.add_parser(mode)
        commands = mode_parser.add_subparsers(dest="mode_command", required=True)
        init = commands.add_parser("init")
        init.add_argument("--input", required=True)
        init.add_argument("--project-dir", required=True)
        init.set_defaults(handler=init_project, mode=mode)
        approve = commands.add_parser("approve")
        approve.add_argument("--project-dir", required=True)
        approve.add_argument("--stage", required=True, choices=("assets", "content", "publish"))
        approve.add_argument("--confirm-assets", action="store_true")
        approve.add_argument("--confirm-content", action="store_true")
        approve.add_argument("--confirm-publish", action="store_true")
        approve.add_argument("--confirm-synthetic-disclosure", action="store_true")
        approve.set_defaults(handler=approve_command, mode=mode)
        validate = commands.add_parser("validate")
        validate.add_argument("--project-dir", required=True)
        validate.add_argument("--publish-ready", action="store_true")
        validate.set_defaults(handler=validate_command, mode=mode)
        render = commands.add_parser("render")
        render.add_argument("--project-dir", required=True)
        render.add_argument("--draft", action="store_true")
        render.add_argument("--final", action="store_true")
        render.add_argument("--no-tts", action="store_true")
        render.set_defaults(handler=render_command, mode=mode)
        package = commands.add_parser("upload-package")
        package.add_argument("--project-dir", required=True)
        package.set_defaults(handler=upload_package_command, mode=mode)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.handler(args)
    except ShortsStudioError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
