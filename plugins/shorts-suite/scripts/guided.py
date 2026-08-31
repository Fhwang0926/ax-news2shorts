#!/usr/bin/env python3
"""Five-stage, approval-gated coordinator for new Shorts Suite projects."""

from __future__ import annotations

import argparse
import getpass
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo


KST = ZoneInfo("Asia/Seoul")
SCHEMA_VERSION = 1
STAGES = ("source", "script", "image", "voice", "render")
STAGE_STATUSES = {
    "pending",
    "options_ready",
    "selected",
    "result_ready",
    "approved",
    "revision_required",
    "invalidated",
}
MODES = ("auto", "whiteboard", "senior", "animal", "healing", "romance", "globalize")
PUBLISHABLE_RIGHTS = {
    "owned",
    "licensed",
    "permission_confirmed",
    "public_domain",
    "official_press_asset",
}
RIGHTS_STATUSES = PUBLISHABLE_RIGHTS | {
    "transformative_review",
    "review_required",
    "unknown",
    "unreviewed",
    "not_permitted",
}
TYPECAST_VOICES = (
    {
        "id": "typecast-daeun",
        "label": "Typecast Daeun",
        "description": "따뜻하고 또렷한 한국어 이야기 내레이터",
        "voice_id": "tc_692799c46508f6b9468c54c7",
        "best_for": "힐링·시니어·설명형 내레이션",
    },
    {
        "id": "typecast-moonjung",
        "label": "Typecast Moonjung",
        "description": "차분한 연장자 캐릭터용 한국어 음성",
        "voice_id": "tc_68f9c6a72f0f04a417bb136f",
        "best_for": "시니어 인물 대사와 대화형 사연",
    },
    {
        "id": "typecast-romance-default",
        "label": "Typecast Romance Default",
        "description": "기존 2인 로맨스 제작 역할의 기본 음성",
        "voice_id": "tc_68257f68bc6e3c161ab5078d",
        "best_for": "로맨스 드라마 내레이션",
    },
)
MODE_DETAILS = {
    "whiteboard": {
        "label": "Whiteboard",
        "description": "검토된 장면을 선화·손그림 애니메이션으로 렌더링",
        "best_for": "행동이 분명하고 단순화 가능한 소스",
    },
    "senior": {
        "label": "Senior Storytoon",
        "description": "창작 시니어 사연을 일관된 캐릭터 이미지와 Pan/Zoom으로 제작",
        "best_for": "55~75세 대상 감정·갈등·반전 이야기",
    },
    "animal": {
        "label": "Animal",
        "description": "실제 동물 행동 근거를 한국어 스토리와 음악으로 재구성",
        "best_for": "검증 가능한 동물 원본",
    },
    "healing": {
        "label": "Healing",
        "description": "대사가 오가는 창작·재구성 사연과 음식 영상을 결합",
        "best_for": "40~45초 따뜻한 대화형 이야기",
    },
    "romance": {
        "label": "Romance",
        "description": "승인된 2인 로맨스 대본과 장면 자산을 세로 드라마로 제작",
        "best_for": "두 인물 중심 감정 전환",
    },
    "globalize": {
        "label": "Global Reframe",
        "description": "한국 Shorts 신호를 독립 출처 기반 영어권 원작 패키지로 재구성",
        "best_for": "렌더보다 조사·대본·편집 인계가 목적일 때",
    },
}


class GuidedError(RuntimeError):
    pass


def now_iso() -> str:
    return datetime.now(KST).isoformat(timespec="seconds")


def clean(value: Any) -> str:
    return " ".join(str(value or "").split())


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise GuidedError(f"파일을 찾을 수 없습니다: {path}") from exc
    except json.JSONDecodeError as exc:
        raise GuidedError(f"JSON 형식이 올바르지 않습니다: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise GuidedError(f"JSON 최상위 값은 객체여야 합니다: {path}")
    return value


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, suffix=".tmp", delete=False
    ) as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        temporary = Path(handle.name)
    os.replace(temporary, path)


def print_json(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def json_digest(value: dict[str, Any]) -> str:
    return sha256_bytes(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    )


def verify_embedded_digest(value: dict[str, Any], expected: str, label: str) -> None:
    payload = dict(value)
    embedded = clean(payload.pop("sha256", ""))
    actual = json_digest(payload)
    if not embedded or embedded != expected or actual != expected:
        raise GuidedError(f"{label} 내용이 기록된 SHA-256과 다릅니다.")


def project_dir(value: str) -> Path:
    return Path(value).expanduser().resolve()


def load_workflow(root: Path) -> dict[str, Any]:
    workflow = read_json(root / "workflow.json")
    if workflow.get("schema_version") != SCHEMA_VERSION:
        raise GuidedError("지원하지 않는 guided workflow schema_version입니다.")
    stages = workflow.get("stages")
    if not isinstance(stages, dict) or tuple(stages) != STAGES:
        raise GuidedError("workflow.json의 5단계 순서가 올바르지 않습니다.")
    for stage in STAGES:
        status = (stages.get(stage) or {}).get("status")
        if status not in STAGE_STATUSES:
            raise GuidedError(f"지원하지 않는 단계 상태입니다: {stage}: {status}")
    return workflow


def save_workflow(root: Path, workflow: dict[str, Any]) -> None:
    workflow["updated_at"] = now_iso()
    write_json(root / "workflow.json", workflow)


def archive_workflow(root: Path, workflow: dict[str, Any], reason: str) -> None:
    stamp = datetime.now(KST).strftime("%Y%m%d_%H%M%S_%f")
    payload = dict(workflow)
    payload["archive_reason"] = reason
    payload["archived_at"] = now_iso()
    write_json(root / "revisions" / f"{stamp}-workflow.json", payload)


def stage_index(stage: str) -> int:
    try:
        return STAGES.index(stage)
    except ValueError as exc:
        raise GuidedError(f"지원하지 않는 단계입니다: {stage}") from exc


def previous_approved(workflow: dict[str, Any], stage: str) -> bool:
    index = stage_index(stage)
    if index == 0:
        return True
    previous = workflow["stages"][STAGES[index - 1]]
    return previous.get("status") == "approved"


def invalidate_downstream(workflow: dict[str, Any], stage: str, reason: str) -> None:
    for name in STAGES[stage_index(stage) + 1 :]:
        current = workflow["stages"][name]
        if current.get("status") != "pending":
            current["status"] = "invalidated"
            current["invalidated_at"] = now_iso()
            current["invalidation_reason"] = reason


def option(
    option_id: str,
    label: str,
    description: str,
    *,
    best_for: str,
    tradeoffs: str,
    required_inputs: list[str] | None = None,
    estimated_time: str = "role-dependent",
    external_cost: str = "none or provider-dependent",
    rights_impact: str = "별도 권리 검토 필요",
    recommended: bool = False,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "id": option_id,
        "label": label,
        "description": description,
        "best_for": best_for,
        "tradeoffs": tradeoffs,
        "required_inputs": required_inputs or [],
        "estimated_time": estimated_time,
        "external_cost": external_cost,
        "rights_impact": rights_impact,
        "recommended": recommended,
        "metadata": metadata or {},
    }


def group(group_id: str, label: str, description: str, values: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "id": group_id,
        "label": label,
        "description": description,
        "required": True,
        "multi_select": False,
        "options": values,
    }


def candidate_values(payload: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    raw: Any = None
    for key in ("shortlist", "candidates", "signals", "items"):
        if isinstance(payload.get(key), list):
            raw = payload[key]
            break
    if not isinstance(raw, list):
        return [], []
    selectable: list[dict[str, Any]] = []
    unavailable: list[dict[str, Any]] = []
    for index, item in enumerate(raw, 1):
        if not isinstance(item, dict):
            unavailable.append({"id": f"invalid-{index}", "reason": "객체가 아닌 후보"})
            continue
        option_id = clean(
            item.get("candidate_id") or item.get("id") or item.get("signal_id") or f"candidate-{index}"
        )
        title = clean(item.get("title") or item.get("label") or item.get("logline") or option_id)
        rights = item.get("rights") if isinstance(item.get("rights"), dict) else {}
        rights_status = clean(rights.get("status") or item.get("rights_status") or "unknown")
        excluded = item.get("eligible") is False or rights_status == "not_permitted"
        exclusion_reason = clean(
            item.get("exclusion_reason")
            or item.get("reason")
            or ("권리 상태 not_permitted" if rights_status == "not_permitted" else "")
        )
        if excluded:
            unavailable.append({"id": option_id, "label": title, "reason": exclusion_reason})
            continue
        summary = clean(
            item.get("summary")
            or item.get("content_explanation")
            or item.get("logline")
            or item.get("hook")
            or title
        )
        selectable.append(
            option(
                option_id,
                title,
                summary,
                best_for=clean(item.get("best_for") or "후보의 실제 화면·출처 검토 후 판단"),
                tradeoffs=clean(item.get("tradeoffs") or "점수는 추천 신호일 뿐 선택이나 권리 허가가 아님"),
                required_inputs=["후보 URL 또는 로컬 소스", "화면 확인", "권리 상태"],
                rights_impact=f"현재 권리 상태: {rights_status}",
                recommended=bool(item.get("recommended") or item.get("best")),
                metadata={
                    "platform": item.get("platform"),
                    "url": item.get("canonical_url") or item.get("url"),
                    "score": item.get("ranking_score") or item.get("score"),
                    "rights_status": rights_status,
                },
            )
        )
    return selectable, unavailable


def source_options(input_payload: dict[str, Any] | None) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    groups = [
        group(
            "production_mode",
            "제작 역할",
            "선택한 소스와 결과 목적에 맞는 Shorts Suite 역할",
            [
                option(
                    mode,
                    details["label"],
                    details["description"],
                    best_for=details["best_for"],
                    tradeoffs="역할별 프로젝트 스키마와 렌더러가 다름",
                    recommended=mode in {"whiteboard", "senior"},
                    rights_impact="원본을 쓰는 역할은 별도 사용 권리 필요",
                )
                for mode, details in MODE_DETAILS.items()
            ],
        ),
        group(
            "source_input",
            "소스 입력 방식",
            "탐색·사용자가 제공한 입력·독립 창작 중 하나를 선택",
            [
                option(
                    "youtube-public",
                    "YouTube 공개 후보",
                    "YouTube Data API와 브라우저로 공개 후보를 찾고 실제 화면을 검토",
                    best_for="최근 공개 영상 신호",
                    tradeoffs="API 메타데이터만으로 내용·원출처·권리를 확정할 수 없음",
                    required_inputs=["YouTube API 또는 공개 브라우저"],
                ),
                option(
                    "public-web",
                    "공개 웹 후보",
                    "공식 페이지·뉴스·커뮤니티를 탐색 신호로 사용",
                    best_for="영상 외 사건·스토리 소재",
                    tradeoffs="원문 복제 금지, 독립 검증 필요",
                ),
                option(
                    "user-url",
                    "사용자 URL",
                    "사용자가 선택한 정확한 URL을 검토",
                    best_for="이미 정한 공개 소스",
                    tradeoffs="공개 URL은 재사용 허가가 아님",
                    required_inputs=["정확한 URL"],
                ),
                option(
                    "local-file",
                    "사용자 로컬 파일",
                    "권한 있는 로컬 영상·이미지·SRT를 프로젝트로 연결",
                    best_for="사용자가 보유하거나 허가받은 소스",
                    tradeoffs="권리 근거와 원본 해시 확인 필요",
                    required_inputs=["읽을 수 있는 로컬 파일", "권리 상태"],
                ),
                option(
                    "original-senior-signal",
                    "시니어 독립 창작",
                    "공개 메타데이터는 수요 신호로만 쓰고 인물·사건·결말을 새로 작성",
                    best_for="시니어 사연툰",
                    tradeoffs="실화로 표시할 수 없고 합성·창작 고지 필요",
                    rights_impact="새로 생성한 자산의 제공자 조건을 기록",
                    recommended=True,
                ),
            ],
        ),
    ]
    unavailable: list[dict[str, Any]] = []
    if input_payload is not None:
        values, unavailable = candidate_values(input_payload)
        if values:
            if len(values) > 10:
                unavailable.extend(
                    {
                        "id": item["id"],
                        "label": item["label"],
                        "reason": "현재 소스 탐색 기본 한도 10개 초과",
                    }
                    for item in values[10:]
                )
                values = values[:10]
            groups.append(
                group(
                    "candidate",
                    "검증 가능 후보",
                    "현재 탐색 실행에서 실제 선택 가능한 모든 후보",
                    values,
                )
            )
    return groups, unavailable


SCRIPT_PRESETS = {
    "whiteboard": (
        ("five-beat-observation", "5비트 관찰", "훅·설정·재훅·상승·결말"),
        ("quick-reveal", "빠른 반전", "짧은 오해 뒤 실제 행동을 공개"),
        ("punch-reversal", "펀치 반전", "강한 중간 재훅과 짧은 결말"),
    ),
    "senior": (
        ("moral-reckoning", "도덕적 책임", "과거 선택의 대가와 현재 행동으로 회수"),
        ("family-consequence", "가족 갈등", "구체적 손실과 주인공의 선택을 중심으로 전개"),
        ("emotional-mystery", "감정 미스터리", "오해를 행동과 단서로 누적한 뒤 관계 반전"),
    ),
    "animal": (
        ("observation-contrast-v1", "관찰 대비", "실제 행동의 오해와 관찰 근거를 대비"),
        ("animal-viral-card-v1", "바이럴 카드", "기존 카드형 4비트 호환 구성"),
    ),
    "healing": (
        ("dialogue-healing", "대화형 힐링", "내레이터 연결과 인물 직접 대사 중심"),
        ("fictionalized-dialogue", "창작 대화", "창작·재구성을 명시한 감정 회수형"),
    ),
    "romance": (("two-person-dialogue", "2인 대화극", "두 인물의 신호·갈등·회수"),),
    "globalize": (("research-reframe", "독립 영문 재구성", "Research→Reframe→Rewrite"),),
}


def selected_mode(workflow: dict[str, Any]) -> str:
    source = workflow["stages"]["source"].get("selection") or {}
    mode = clean((source.get("options") or {}).get("production_mode"))
    if mode:
        return mode
    configured = clean(workflow.get("mode"))
    return "senior" if configured == "auto" else configured


def script_options(workflow: dict[str, Any], input_payload: dict[str, Any] | None) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    mode = selected_mode(workflow)
    if input_payload is not None:
        values, unavailable = candidate_values(input_payload)
        if values:
            return [group("script_direction", "대본 방향", "역할이 생성한 모든 유효 대본 안", values)], unavailable
    presets = SCRIPT_PRESETS.get(mode) or (("source-explainer", "소스 설명형", "근거와 결론을 분리"),)
    return [
        group(
            "script_direction",
            "대본 방향",
            "선택된 역할이 지원하는 대본 구조",
            [
                option(
                    item_id,
                    label,
                    description,
                    best_for=MODE_DETAILS.get(mode, {}).get("best_for", "선택 소스"),
                    tradeoffs="선택 후 전체 대본·스토리보드가 생성되며 승인 전 다음 단계 금지",
                    required_inputs=["승인된 소스 결과"],
                    recommended=index == 0,
                )
                for index, (item_id, label, description) in enumerate(presets)
            ],
        )
    ], []


def image_options(workflow: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    mode = selected_mode(workflow)
    if mode == "whiteboard":
        return [
            group(
                "visual_provider",
                "시각 입력",
                "화이트보드 장면 이미지 제공 방식",
                [
                    option("source-frames", "검토 원본 프레임", "실제 화면을 단순화", best_for="관찰 근거 유지", tradeoffs="권리와 텍스트 영역 검토 필요"),
                    option("user-assets", "사용자 장면 이미지", "사용자 승인 이미지를 사용", best_for="권리 확정 자산", tradeoffs="9:16·선화 적합도 확인 필요"),
                ],
            ),
            group(
                "ink_path",
                "선화 방식",
                "그리기 경로 생성 방식",
                [
                    option("grid", "Grid", "격자 기반 안정적 선화", best_for="대부분의 장면", tradeoffs="세부 윤곽이 단순해질 수 있음", recommended=True),
                    option("skeleton", "Skeleton", "중심선 기반 빠른 드로잉", best_for="가늘고 분리된 피사체", tradeoffs="복잡한 윤곽에서 불안정할 수 있음"),
                ],
            ),
            group(
                "color_fill",
                "색 채움",
                "선화 뒤 제한 색상 적용 방식",
                [
                    option("contour-wipe", "Contour Wipe", "윤곽을 따라 색상을 공개", best_for="반전·결말", tradeoffs="윤곽 품질에 민감", recommended=True),
                    option("brush", "Brush", "브러시처럼 색상을 채움", best_for="감성적 장면", tradeoffs="채움 시간이 길 수 있음"),
                ],
            ),
        ], []
    if mode == "senior":
        return [
            group(
                "visual_provider",
                "이미지 제공자",
                "선택한 제공자 외 자동 대체 없음",
                [
                    option("builtin-imagegen", "Built-in ImageGen", "Codex 내장 이미지 생성", best_for="빠른 캐릭터·장면 제작", tradeoffs="장면별 인물 일관성 검토 필요", external_cost="product-managed", recommended=True),
                    option("comfyui", "ComfyUI", "사용자 API workflow로 로컬 이미지 생성", best_for="로컬 모델·시드 제어", tradeoffs="실행 중인 서버와 노드 ID 필요", required_inputs=["API workflow", "node IDs"], external_cost="local GPU"),
                    option("user-assets", "사용자 이미지", "승인된 장면별 파일 사용", best_for="직접 제작·권리 확정 이미지", tradeoffs="파일 수·비율·캐릭터 연속성 확인 필요"),
                ],
            ),
            group(
                "visual_style",
                "시각 스타일",
                "Senior 역할의 현재 지원 스타일",
                [option("korean-senior-storytoon-v1", "Korean Senior Storytoon", "따뜻한 한국 웹툰형 시니어 인물극", best_for="감정·갈등·반전 사연", tradeoffs="합성 콘텐츠 고지 필요", recommended=True)],
            ),
        ], []
    presets = {
        "animal": [
            option("observation-contrast-v1", "Observation Contrast", "관찰 근거 대비형", best_for="동물 행동 쇼츠", tradeoffs="실제 프레임 검토 필수", recommended=True),
            option("animal-viral-card-v1", "Animal Viral Card", "기존 카드형 호환", best_for="레거시 프로젝트", tradeoffs="정보 밀도가 높음"),
        ],
        "healing": [option("food-background", "Food Background", "음식 조리 영상 위 대화형 사연", best_for="힐링 사연", tradeoffs="사용 권리·화면 문자 검토 필요", recommended=True)],
        "romance": [
            option("generated-scenes", "Generated Scenes", "승인된 캐릭터 장면 이미지", best_for="2인 로맨스", tradeoffs="얼굴·의상 연속성 검토 필요", recommended=True),
            option("user-assets", "User Assets", "사용자 제공 장면 자산", best_for="직접 제작 이미지", tradeoffs="파일·권리 확인 필요"),
        ],
        "globalize": [option("asset-search-plan", "Asset Search Plan", "렌더러 중립 에셋 검색 계획만 생성", best_for="CapCut 인계", tradeoffs="이 단계에서 이미지를 생성하지 않음", recommended=True)],
    }
    return [group("visual_mode", "시각 방식", "선택 역할과 호환되는 모든 시각 옵션", presets.get(mode, []))], []


def korean_macos_voices() -> list[dict[str, Any]]:
    if sys.platform != "darwin" or not shutil.which("say"):
        return []
    completed = subprocess.run(
        [shutil.which("say") or "say", "-v", "?"],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    if completed.returncode != 0:
        return []
    result = []
    for line in completed.stdout.splitlines():
        if "ko_KR" not in line and "ko-KR" not in line:
            continue
        name = line.split()[0]
        result.append(
            option(
                f"macos-{name.lower()}",
                f"macOS {name}",
                "현재 Mac에 설치된 한국어 시스템 음성",
                best_for="비공개 로컬 검토",
                tradeoffs="플랫폼 상업 사용 권리를 별도로 확인",
                external_cost="none",
                rights_impact="macOS 음성 사용 조건 확인 필요",
                metadata={"provider": "macos", "voice": name, "language": "ko-KR"},
            )
        )
    return result


def typecast_available() -> tuple[bool, str]:
    try:
        from core.typecast import api_key_record, keychain_check_limited

        _, source = api_key_record()
        if source:
            return True, source
        if keychain_check_limited():
            return False, "keychain-check-limited"
    except Exception:
        pass
    return False, "not-configured"


def voice_options(workflow: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    mode = selected_mode(workflow)
    values: list[dict[str, Any]] = []
    unavailable: list[dict[str, Any]] = []
    typecast_ok, typecast_source = typecast_available()
    for record in TYPECAST_VOICES:
        item = option(
            record["id"],
            record["label"],
            record["description"],
            best_for=record["best_for"],
            tradeoffs="외부 API 사용량과 키 설정 필요; 실패 시 자동 대체 없음",
            external_cost="Typecast plan-dependent",
            rights_impact="합성 음성 고지 필요",
            metadata={"provider": "typecast", "voice_id": record["voice_id"], "key_source": typecast_source},
        )
        if typecast_ok:
            values.append(item)
        else:
            unavailable.append({"id": record["id"], "label": record["label"], "reason": typecast_source})
    values.extend(korean_macos_voices())
    values.append(
        option("user-files", "사용자 제공 음성", "장면별 또는 연속 음성 파일 사용", best_for="직접 녹음·허가받은 TTS", tradeoffs="길이와 화자 매핑 필요", required_inputs=["WAV/AIFF/MP3/M4A"], rights_impact="제공 음성 권리 확인 필요")
    )
    if mode in {"whiteboard", "animal", "healing", "globalize"}:
        values.append(
            option("source-audio", "권리 확인된 소스 음성", "원본 음성을 유지", best_for="실제 행동·ASMR·대화 보존", tradeoffs="편집·오버레이 허가 확인 필요", rights_impact="voice_overlay_allowed 또는 동등 권리 필요")
        )
    if mode in {"whiteboard", "animal", "globalize"}:
        values.append(
            option("none", "음성 없음", "내레이션 없이 자막·음악 또는 무음으로 구성", best_for="원래 음성이 불필요한 형식", tradeoffs="검토본을 최종 음성 포함 결과로 설명할 수 없음", rights_impact="합성 음성 없음")
        )
    if not values:
        raise GuidedError("현재 환경과 역할에서 선택 가능한 음성 옵션이 없습니다.")
    return [group("voice", "음성 옵션", "현재 환경에서 실제 선택 가능한 모든 음성 방식", values)], unavailable


def render_options(workflow: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    mode = selected_mode(workflow)
    renderer = {
        "whiteboard": option("whiteboard", "Whiteboard Renderer", "선화·색 채움·줌 기반 1080×1920 렌더", best_for="화이트보드 장면", tradeoffs="annotation 검토 필요", recommended=True),
        "senior": option("senior-panzoom", "Senior Pan/Zoom", "이미지·큰 자막·장면 음성 기반 1080×1920 렌더", best_for="시니어 사연툰", tradeoffs="캐릭터·음성 연속성 검토 필요", recommended=True),
        "animal": option("animal-source-edit", "Animal Source Edit", "검토된 원본 행동과 자막·음악·효과음 합성", best_for="동물 쇼츠", tradeoffs="권리와 실제 프레임 근거 필요", recommended=True),
        "healing": option("healing-food-video", "Healing Food Video", "음식 영상과 화자별 음성·자막 합성", best_for="대화형 힐링", tradeoffs="소스 영상 권리 필요", recommended=True),
        "romance": option("romance-scenes", "Romance Scene Renderer", "승인 장면과 Typecast 음성 합성", best_for="2인 로맨스", tradeoffs="최종 음성은 Typecast 필요", recommended=True),
        "globalize": option("package-only", "Package Only", "MP4 대신 편집 패키지와 인계 자료 생성", best_for="CapCut 후편집", tradeoffs="깨끗한 최종 MP4는 별도 렌더러 필요", recommended=True),
    }[mode]
    return [
        group("renderer", "렌더러", "선택 역할에 맞는 렌더 방식", [renderer]),
        group(
            "pacing",
            "편집 속도",
            "장면 유지 시간과 전환 밀도",
            [
                option("calm", "Calm", "긴 호흡과 적은 전환", best_for="힐링·시니어", tradeoffs="초반 이탈 가능성"),
                option("standard", "Standard", "내용 이해와 유지율 균형", best_for="대부분의 쇼츠", tradeoffs="극단적 장르감은 약함", recommended=True),
                option("dynamic", "Dynamic", "짧은 장면과 강한 재훅", best_for="동물·반전", tradeoffs="시니어 가독성 저하 가능"),
            ],
        ),
        group(
            "caption",
            "자막 스타일",
            "현재 역할과 호환되는 큰 2줄 자막",
            [
                option("comic-observation", "Comic Observation", "차분한 관찰형 자막", best_for="Whiteboard·동물", tradeoffs="충격 훅은 약함"),
                option("viral-punch", "Viral Punch", "노란 핵심어와 강한 대비", best_for="재훅·반전", tradeoffs="감성물에서는 과해질 수 있음"),
                option("senior-large-highlight", "Senior Large Highlight", "중앙 하단 큰 글자와 긴 노출", best_for="시니어 사연", tradeoffs="화면 피사체 여백 필요", recommended=mode == "senior"),
            ],
        ),
        group(
            "music",
            "음악",
            "실제 지원 가능한 음악 경로",
            [
                option("none", "음악 없음", "음성·원본음만 사용", best_for="대사 중심", tradeoffs="감정 리듬이 약할 수 있음"),
                option("synthetic", "안전한 생성 음악", "무보컬 자체 생성 배경음", best_for="권리 단순화", tradeoffs="유명 트랙 효과 없음", rights_impact="owned synthetic", recommended=True),
                option("licensed", "검증 라이선스 음악", "공식 제공처와 라이선스·크레딧을 기록", best_for="익숙한 편집 리듬", tradeoffs="라이선스 조건과 파일 확보 필요", required_inputs=["license reference", "official audio"]),
            ],
        ),
        group(
            "review_profile",
            "검토 해상도",
            "사용자 확인용 출력 크기",
            [
                option("540x960", "540×960", "빠른 저해상도 검토", best_for="초기 장면·음성 확인", tradeoffs="최종 선명도 판단 제한", recommended=True),
                option("720x1280", "720×1280", "중간 품질 검토", best_for="자막과 편집 리듬", tradeoffs="렌더 시간이 증가"),
                option("1080x1920", "1080×1920", "최종 해상도 검토", best_for="세부 품질 확인", tradeoffs="가장 느리고 용량이 큼"),
            ],
        ),
    ], []


def options_for_stage(
    workflow: dict[str, Any], stage: str, input_payload: dict[str, Any] | None
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if stage == "source":
        return source_options(input_payload)
    if stage == "script":
        return script_options(workflow, input_payload)
    if stage == "image":
        return image_options(workflow)
    if stage == "voice":
        return voice_options(workflow)
    return render_options(workflow)


def resolve_artifact(root: Path, value: str) -> Path:
    candidate = (root / value).resolve() if not Path(value).is_absolute() else Path(value).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise GuidedError(f"프로젝트 밖의 결과물은 등록할 수 없습니다: {value}") from exc
    if not candidate.is_file():
        raise GuidedError(f"결과물 파일을 찾을 수 없습니다: {candidate}")
    return candidate


def command_init(args: argparse.Namespace) -> None:
    root = project_dir(args.project_dir)
    if root.exists() and any(root.iterdir()):
        raise GuidedError("guided init은 비어 있는 새 프로젝트 디렉터리만 사용할 수 있습니다.")
    root.mkdir(parents=True, exist_ok=True)
    for name in ("options", "results", "revisions", "role-project", "final"):
        (root / name).mkdir(parents=True, exist_ok=True)
    workflow = {
        "schema_version": SCHEMA_VERSION,
        "workflow_id": root.name,
        "plugin": "shorts-suite",
        "title": args.title,
        "mode": args.mode,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "current_stage": "source",
        "finalized": False,
        "policy": {
            "publish_blocked": True,
            "synthetic_disclosure_reviewed": False,
            "upload_performed": False,
        },
        "stages": {
            stage: {
                "status": "pending",
                "revision": 0,
                "options": None,
                "selection": None,
                "result": None,
                "approval": None,
            }
            for stage in STAGES
        },
    }
    write_json(root / "workflow.json", workflow)
    print_json({"project_dir": str(root), "current_stage": "source", "next": "guided options --stage source"})


def command_options(args: argparse.Namespace) -> None:
    root = project_dir(args.project_dir)
    workflow = load_workflow(root)
    stage = args.stage
    if not previous_approved(workflow, stage):
        raise GuidedError(f"이전 단계 승인 전에는 {stage} 옵션을 만들 수 없습니다.")
    current = workflow["stages"][stage]
    if current["status"] not in {"pending", "invalidated", "revision_required", "options_ready"}:
        archive_workflow(root, workflow, f"regenerate-{stage}-options")
        invalidate_downstream(workflow, stage, f"{stage} 옵션 재생성")
    input_payload = read_json(Path(args.input).expanduser().resolve()) if args.input else None
    groups, unavailable = options_for_stage(workflow, stage, input_payload)
    if not groups or any(not item.get("options") for item in groups):
        raise GuidedError(f"{stage} 단계에 선택 가능한 옵션이 없습니다.")
    revision = int(current.get("revision") or 0) + 1
    payload = {
        "schema_version": SCHEMA_VERSION,
        "stage": stage,
        "revision": revision,
        "generated_at": now_iso(),
        "explanation": "모든 실제 선택 가능 옵션과 단계별 설명입니다. recommended는 자동 선택이 아닙니다.",
        "groups": groups,
        "unavailable": unavailable,
        "input_reference": str(Path(args.input).expanduser().resolve()) if args.input else "",
    }
    payload["sha256"] = json_digest(payload)
    path = root / "options" / f"{stage}-r{revision}.json"
    write_json(path, payload)
    current.update(
        {
            "status": "options_ready",
            "revision": revision,
            "options": {"path": str(path.relative_to(root)), "sha256": payload["sha256"]},
            "selection": None,
            "result": None,
            "approval": None,
        }
    )
    workflow["current_stage"] = stage
    save_workflow(root, workflow)
    print_json(payload)


def parse_selections(values: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for value in values:
        if "=" not in value:
            raise GuidedError("--option은 group=id 형식이어야 합니다.")
        group_id, option_id = value.split("=", 1)
        group_id, option_id = clean(group_id), clean(option_id)
        if not group_id or not option_id or group_id in result:
            raise GuidedError(f"잘못되거나 중복된 옵션 선택입니다: {value}")
        result[group_id] = option_id
    return result


def command_select(args: argparse.Namespace) -> None:
    root = project_dir(args.project_dir)
    workflow = load_workflow(root)
    stage = args.stage
    current = workflow["stages"][stage]
    if current.get("status") != "options_ready":
        raise GuidedError(f"{stage} 단계는 options_ready 상태에서만 선택할 수 있습니다.")
    options_record = current.get("options") or {}
    options_path = root / clean(options_record.get("path"))
    payload = read_json(options_path)
    verify_embedded_digest(payload, clean(options_record.get("sha256")), "옵션 파일")
    selected = parse_selections(args.option)
    expected_groups = {clean(item.get("id")): item for item in payload.get("groups") or []}
    if set(selected) != set(expected_groups):
        missing = sorted(set(expected_groups) - set(selected))
        extra = sorted(set(selected) - set(expected_groups))
        raise GuidedError(f"모든 옵션 그룹에서 하나씩 선택해야 합니다. missing={missing}, extra={extra}")
    for group_id, option_id in selected.items():
        valid = {clean(item.get("id")) for item in expected_groups[group_id].get("options") or []}
        if option_id not in valid:
            raise GuidedError(f"목록에 없는 옵션입니다: {group_id}={option_id}")
    archive_workflow(root, workflow, f"select-{stage}")
    invalidate_downstream(workflow, stage, f"{stage} 옵션 선택 변경")
    selection = {
        "selected_at": now_iso(),
        "options": selected,
        "options_sha256": options_record["sha256"],
    }
    selection["sha256"] = json_digest(selection)
    current.update(
        {"status": "selected", "selection": selection, "result": None, "approval": None}
    )
    workflow["current_stage"] = stage
    save_workflow(root, workflow)
    print_json({"stage": stage, "status": "selected", "selection": selection})


def command_produce(args: argparse.Namespace) -> None:
    root = project_dir(args.project_dir)
    workflow = load_workflow(root)
    stage = args.stage
    current = workflow["stages"][stage]
    if current.get("status") not in {"selected", "revision_required"}:
        raise GuidedError(f"{stage} 단계는 선택 후에만 결과를 등록할 수 있습니다.")
    if not previous_approved(workflow, stage):
        raise GuidedError(f"이전 단계 승인 전에는 {stage} 결과를 등록할 수 없습니다.")
    artifacts = [resolve_artifact(root, value) for value in args.artifact]
    if not artifacts:
        raise GuidedError("produce에는 하나 이상의 --artifact가 필요합니다.")
    archive_workflow(root, workflow, f"produce-{stage}")
    invalidate_downstream(workflow, stage, f"{stage} 결과 변경")
    records = [
        {
            "path": str(path.relative_to(root)),
            "sha256": sha256_file(path),
            "size": path.stat().st_size,
        }
        for path in artifacts
    ]
    result = {
        "stage": stage,
        "revision": current["revision"],
        "produced_at": now_iso(),
        "producer_role": args.producer_role,
        "selection_sha256": (current.get("selection") or {}).get("sha256"),
        "artifacts": records,
        "metadata": {
            "rights_status": args.rights_status,
            "synthetic": bool(args.synthetic),
            "note": args.note,
        },
    }
    result["sha256"] = json_digest(result)
    path = root / "results" / stage / f"result-r{current['revision']}.json"
    write_json(path, result)
    current.update(
        {
            "status": "result_ready",
            "result": {"path": str(path.relative_to(root)), "sha256": result["sha256"]},
            "approval": None,
        }
    )
    workflow["current_stage"] = stage
    save_workflow(root, workflow)
    print_json(result)


def command_approve(args: argparse.Namespace) -> None:
    root = project_dir(args.project_dir)
    workflow = load_workflow(root)
    stage = args.stage
    current = workflow["stages"][stage]
    if current.get("status") != "result_ready":
        raise GuidedError(f"{stage} 결과가 result_ready일 때만 승인 결정을 기록할 수 있습니다.")
    result_record = current.get("result") or {}
    if args.result_sha256 != result_record.get("sha256"):
        raise GuidedError("승인 대상 결과 해시가 현재 결과와 다릅니다.")
    result = read_json(root / clean(result_record.get("path")))
    verify_embedded_digest(result, clean(result_record.get("sha256")), "결과 파일")
    if (
        args.decision == "approve"
        and stage == "image"
        and (result.get("metadata") or {}).get("synthetic")
        and not args.confirm_synthetic_disclosure
    ):
        raise GuidedError("합성 이미지 승인에는 --confirm-synthetic-disclosure가 필요합니다.")
    archive_workflow(root, workflow, f"approve-{stage}-{args.decision}")
    if args.decision == "revise":
        current["status"] = "revision_required"
        current["approval"] = {
            "decision": "revise",
            "decided_at": now_iso(),
            "note": args.note,
            "result_sha256": args.result_sha256,
        }
        workflow["current_stage"] = stage
    else:
        if stage == "image" and (result.get("metadata") or {}).get("synthetic"):
            workflow["policy"]["synthetic_disclosure_reviewed"] = True
        current["status"] = "approved"
        current["approval"] = {
            "decision": "approve",
            "decided_at": now_iso(),
            "note": args.note,
            "result_sha256": args.result_sha256,
            "synthetic_disclosure_confirmed": bool(args.confirm_synthetic_disclosure),
        }
        index = stage_index(stage)
        workflow["current_stage"] = STAGES[index + 1] if index + 1 < len(STAGES) else "complete"
    save_workflow(root, workflow)
    print_json(
        {
            "stage": stage,
            "status": current["status"],
            "approval": current["approval"],
            "next_stage": workflow["current_stage"],
        }
    )


def source_rights(workflow: dict[str, Any], root: Path) -> str:
    result_record = workflow["stages"]["source"].get("result") or {}
    if not result_record:
        return "unknown"
    result = read_json(root / clean(result_record.get("path")))
    return clean((result.get("metadata") or {}).get("rights_status") or "unknown")


def media_probe(path: Path) -> dict[str, Any]:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        return {"checked": False, "reason": "ffprobe unavailable"}
    completed = subprocess.run(
        [ffprobe, "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode != 0:
        raise GuidedError(f"최종 미디어 검사 실패: {clean(completed.stderr)}")
    value = json.loads(completed.stdout)
    streams = value.get("streams") or []
    video = next((item for item in streams if item.get("codec_type") == "video"), None)
    audio = next((item for item in streams if item.get("codec_type") == "audio"), None)
    if not video:
        raise GuidedError("최종 MP4에 영상 스트림이 없습니다.")
    width, height = int(video.get("width") or 0), int(video.get("height") or 0)
    if not width or not height or height <= width:
        raise GuidedError(f"최종 영상은 세로형이어야 합니다: {width}x{height}")
    return {
        "checked": True,
        "width": width,
        "height": height,
        "video_codec": video.get("codec_name"),
        "audio_present": bool(audio),
        "audio_codec": audio.get("codec_name") if audio else None,
        "duration": (value.get("format") or {}).get("duration"),
    }


def command_finalize(args: argparse.Namespace) -> None:
    root = project_dir(args.project_dir)
    workflow = load_workflow(root)
    render_stage = workflow["stages"]["render"]
    if render_stage.get("status") != "approved":
        raise GuidedError("렌더 결과 승인 전에는 최종본을 확정할 수 없습니다.")
    if not args.confirm_clean_render:
        raise GuidedError("검토 표시가 없는 역할 최종본임을 --confirm-clean-render로 확인하세요.")
    rights_status = source_rights(workflow, root)
    if rights_status not in PUBLISHABLE_RIGHTS:
        raise GuidedError(
            f"현재 소스 권리 상태에서는 깨끗한 최종본을 만들 수 없습니다: {rights_status}"
        )
    any_synthetic = False
    for stage in STAGES:
        record = workflow["stages"][stage].get("result") or {}
        if not record:
            continue
        result = read_json(root / clean(record.get("path")))
        any_synthetic = any_synthetic or bool((result.get("metadata") or {}).get("synthetic"))
    if any_synthetic and not workflow["policy"].get("synthetic_disclosure_reviewed"):
        raise GuidedError("합성 자산이 있어 합성 콘텐츠 고지 승인이 필요합니다.")
    if not args.artifact:
        raise GuidedError(
            "역할 렌더러로 검토 표시 없는 MP4를 만든 뒤 --artifact <project-relative-final.mp4>를 지정하세요."
        )
    final_path = resolve_artifact(root, args.artifact)
    if final_path.suffix.lower() != ".mp4":
        raise GuidedError("최종 산출물은 MP4여야 합니다.")
    report = {
        "schema_version": SCHEMA_VERSION,
        "finalized_at": now_iso(),
        "artifact": {
            "path": str(final_path.relative_to(root)),
            "sha256": sha256_file(final_path),
            "size": final_path.stat().st_size,
        },
        "media": media_probe(final_path),
        "rights_status": rights_status,
        "synthetic_disclosure_reviewed": workflow["policy"].get(
            "synthetic_disclosure_reviewed"
        ),
        "upload_performed": False,
        "proof_note": "로컬 최종 미디어 검증은 플랫폼 승인·수익화·게시를 증명하지 않습니다.",
    }
    write_json(root / "final" / "finalization.json", report)
    workflow["finalized"] = True
    workflow["final_artifact"] = report["artifact"]
    workflow["policy"]["publish_blocked"] = False
    save_workflow(root, workflow)
    print_json(report)


def command_status(args: argparse.Namespace) -> None:
    root = project_dir(args.project_dir)
    workflow = load_workflow(root)
    print_json(
        {
            "project_dir": str(root),
            "workflow_id": workflow.get("workflow_id"),
            "mode": workflow.get("mode"),
            "selected_mode": selected_mode(workflow),
            "current_stage": workflow.get("current_stage"),
            "finalized": workflow.get("finalized"),
            "policy": workflow.get("policy"),
            "stages": {
                stage: {
                    "status": workflow["stages"][stage].get("status"),
                    "revision": workflow["stages"][stage].get("revision"),
                    "options": workflow["stages"][stage].get("options"),
                    "selection": workflow["stages"][stage].get("selection"),
                    "result": workflow["stages"][stage].get("result"),
                    "approval": workflow["stages"][stage].get("approval"),
                }
                for stage in STAGES
            },
        }
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    init = commands.add_parser("init", help="새 5단계 승인 프로젝트를 초기화합니다.")
    init.add_argument("--project-dir", required=True)
    init.add_argument("--title", default="")
    init.add_argument("--mode", choices=MODES, default="auto")
    init.set_defaults(handler=command_init)

    options = commands.add_parser("options", help="현재 단계의 모든 선택 가능 옵션과 설명을 만듭니다.")
    options.add_argument("--project-dir", required=True)
    options.add_argument("--stage", choices=STAGES, required=True)
    options.add_argument("--input", help="후보·대본 옵션 JSON")
    options.set_defaults(handler=command_options)

    select = commands.add_parser("select", help="사용자가 고른 옵션 ID를 기록합니다.")
    select.add_argument("--project-dir", required=True)
    select.add_argument("--stage", choices=STAGES, required=True)
    select.add_argument("--option", action="append", required=True, help="group=id; 그룹별 한 번")
    select.set_defaults(handler=command_select)

    produce = commands.add_parser("produce", help="선택 옵션으로 만든 단계 결과물과 해시를 등록합니다.")
    produce.add_argument("--project-dir", required=True)
    produce.add_argument("--stage", choices=STAGES, required=True)
    produce.add_argument("--artifact", action="append", required=True, help="프로젝트 내부 결과물 파일")
    produce.add_argument("--producer-role", required=True, choices=MODES[1:])
    produce.add_argument("--rights-status", choices=sorted(RIGHTS_STATUSES), default="unknown")
    produce.add_argument("--synthetic", action="store_true")
    produce.add_argument("--note", default="")
    produce.set_defaults(handler=command_produce)

    approve = commands.add_parser("approve", help="현재 결과 해시에 대한 사용자 결정을 기록합니다.")
    approve.add_argument("--project-dir", required=True)
    approve.add_argument("--stage", choices=STAGES, required=True)
    approve.add_argument("--decision", choices=("approve", "revise"), required=True)
    approve.add_argument("--result-sha256", required=True)
    approve.add_argument("--note", default="")
    approve.add_argument("--confirm-synthetic-disclosure", action="store_true")
    approve.set_defaults(handler=command_approve)

    status = commands.add_parser("status", help="단계·옵션·선택·승인 상태를 확인합니다.")
    status.add_argument("--project-dir", required=True)
    status.set_defaults(handler=command_status)

    finalize = commands.add_parser("finalize", help="렌더 승인 후 깨끗한 최종 MP4를 검증·확정합니다.")
    finalize.add_argument("--project-dir", required=True)
    finalize.add_argument("--artifact", help="역할 렌더러가 만든 프로젝트 내부 MP4")
    finalize.add_argument("--confirm-clean-render", action="store_true")
    finalize.set_defaults(handler=command_finalize)
    return parser


def main() -> int:
    try:
        args = build_parser().parse_args()
        args.handler(args)
    except GuidedError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
