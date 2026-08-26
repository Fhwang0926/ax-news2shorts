#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit


PLUGIN_VERSION = "0.1.0+codex.20260826121842"
SCHEMA_VERSION = 1
PLATFORMS = {"youtube", "tiktok", "instagram", "x", "reddit", "other"}
CHECK_STATUSES = {"ok", "blocked", "unavailable"}
STORY_PATTERNS = {
    "result-curiosity",
    "unexpected-ability",
    "culture-gap",
    "hidden-principle",
    "backstory",
    "other",
}
SOURCE_SCORES = {
    "verified_original": 100,
    "probable_original": 70,
    "repost_only": 30,
    "unknown": 0,
}
RIGHTS_STATUSES = {
    "owned",
    "licensed",
    "permission_confirmed",
    "unknown",
    "not_permitted",
}
FEATURE_WEIGHTS = {
    "viral_momentum": 0.20,
    "hook": 0.15,
    "story_twist": 0.15,
    "explainability": 0.10,
    "visual_clarity": 0.10,
    "editability": 0.05,
}
PENALTIES = {
    "tv_film": 25,
    "sports_broadcast": 20,
    "source_unknown": 15,
    "korean_saturated": 20,
    "long_interview": 10,
    "promotional": 10,
    "context_misleading": 15,
    "sensitive": 20,
}


class ScoutError(ValueError):
    pass


def clean_text(value: Any) -> str:
    return " ".join(str(value or "").split())


def require_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ScoutError(f"{label} must be an object")
    return value


def require_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise ScoutError(f"{label} must be an array")
    return value


def require_string(value: Any, label: str, *, minimum: int = 1) -> str:
    text = clean_text(value)
    if len(text) < minimum:
        raise ScoutError(f"{label} must contain at least {minimum} characters")
    return text


def require_string_list(value: Any, label: str, *, minimum: int = 1) -> list[str]:
    items = require_list(value, label)
    result = [require_string(item, f"{label}[{index}]", minimum=2) for index, item in enumerate(items)]
    if len(result) < minimum:
        raise ScoutError(f"{label} must contain at least {minimum} item(s)")
    return result


def require_bool(value: Any, label: str) -> bool:
    if not isinstance(value, bool):
        raise ScoutError(f"{label} must be true or false")
    return value


def require_integer(
    value: Any,
    label: str,
    *,
    minimum: int = 0,
    maximum: int | None = None,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ScoutError(f"{label} must be an integer")
    if value < minimum or (maximum is not None and value > maximum):
        suffix = f" and at most {maximum}" if maximum is not None else ""
        raise ScoutError(f"{label} must be at least {minimum}{suffix}")
    return value


def parse_timestamp(value: Any, label: str) -> dt.datetime:
    text = require_string(value, label, minimum=10)
    try:
        parsed = dt.datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ScoutError(f"{label} must be an ISO 8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ScoutError(f"{label} must include a timezone")
    return parsed


def require_url(value: Any, label: str) -> str:
    url = require_string(value, label, minimum=8)
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ScoutError(f"{label} must be an absolute HTTP(S) URL")
    return url


def canonical_url(value: str) -> str:
    parsed = urlsplit(value)
    path = parsed.path.rstrip("/") or "/"
    return urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), path, "", ""))


def compact_fingerprint(value: Any) -> str:
    return re.sub(r"[^0-9a-z가-힣]+", "", clean_text(value).lower())


def gap_score(similar_results_count: int) -> int:
    if similar_results_count == 0:
        return 100
    if similar_results_count <= 3:
        return 80
    if similar_results_count <= 10:
        return 50
    return 20


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return require_object(json.load(handle), str(path))


def normalize_platform_checks(value: Any) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, raw in enumerate(require_list(value, "platform_checks")):
        label = f"platform_checks[{index}]"
        item = require_object(raw, label)
        platform = require_string(item.get("platform"), f"{label}.platform").lower()
        if platform not in PLATFORMS:
            raise ScoutError(f"{label}.platform is unsupported: {platform}")
        if platform in seen:
            raise ScoutError(f"{label}.platform must be unique")
        seen.add(platform)
        status = require_string(item.get("status"), f"{label}.status").lower()
        if status not in CHECK_STATUSES:
            raise ScoutError(f"{label}.status must be ok, blocked, or unavailable")
        checks.append(
            {
                "platform": platform,
                "status": status,
                "query": require_string(item.get("query"), f"{label}.query", minimum=2),
                "evidence": require_string_list(item.get("evidence"), f"{label}.evidence"),
            }
        )
    if not checks:
        raise ScoutError("platform_checks must contain at least one inspected platform")
    return checks


def normalize_metrics(value: Any, label: str) -> dict[str, int | None]:
    raw = require_object(value, label)
    result: dict[str, int | None] = {}
    for key in ("views", "likes", "comments", "shares"):
        current = raw.get(key)
        result[key] = None if current is None else require_integer(current, f"{label}.{key}")
    return result


def normalize_story_pattern(value: Any, label: str) -> str:
    pattern = require_string(value, f"{label}.story_pattern").lower()
    if pattern not in STORY_PATTERNS:
        raise ScoutError(f"{label}.story_pattern is unsupported: {pattern}")
    return pattern


def normalize_candidate(
    value: Any,
    index: int,
    *,
    collected_at: dt.datetime,
    max_age_hours: int,
) -> dict[str, Any]:
    label = f"candidates[{index}]"
    raw = require_object(value, label)
    candidate_id = require_string(raw.get("id"), f"{label}.id")
    if not re.fullmatch(r"[0-9A-Za-z][0-9A-Za-z._-]{0,79}", candidate_id):
        raise ScoutError(f"{label}.id must be a safe 1-80 character identifier")

    platform = require_string(raw.get("platform"), f"{label}.platform").lower()
    if platform not in PLATFORMS:
        raise ScoutError(f"{label}.platform is unsupported: {platform}")
    url = require_url(raw.get("url"), f"{label}.url")
    published_at = parse_timestamp(raw.get("published_at"), f"{label}.published_at")
    age_hours = (
        collected_at.astimezone(dt.timezone.utc)
        - published_at.astimezone(dt.timezone.utc)
    ).total_seconds() / 3600
    if age_hours < -1:
        raise ScoutError(f"{label}.published_at is later than collected_at")
    age_hours = max(0.0, age_hours)

    metrics = normalize_metrics(raw.get("metrics"), f"{label}.metrics")
    metric_evidence = require_string_list(
        raw.get("metric_evidence"), f"{label}.metric_evidence"
    )
    evidence_urls = [
        require_url(item, f"{label}.evidence_urls[{i}]")
        for i, item in enumerate(
            require_list(raw.get("evidence_urls"), f"{label}.evidence_urls")
        )
    ]
    if not evidence_urls:
        raise ScoutError(f"{label}.evidence_urls must contain at least one URL")

    inspection_raw = require_object(raw.get("inspection"), f"{label}.inspection")
    inspection = {
        key: require_bool(inspection_raw.get(key), f"{label}.inspection.{key}")
        for key in ("publicly_visible", "content_observed", "short_form_or_clippable")
    }

    feature_raw = require_object(raw.get("features"), f"{label}.features")
    reason_raw = require_object(raw.get("feature_reasons"), f"{label}.feature_reasons")
    features = {
        key: require_integer(
            feature_raw.get(key), f"{label}.features.{key}", maximum=100
        )
        for key in FEATURE_WEIGHTS
    }
    feature_reasons = {
        key: require_string(
            reason_raw.get(key), f"{label}.feature_reasons.{key}", minimum=12
        )
        for key in FEATURE_WEIGHTS
    }

    gap_raw = require_object(raw.get("korean_gap"), f"{label}.korean_gap")
    similar_results_count = require_integer(
        gap_raw.get("similar_results_count"),
        f"{label}.korean_gap.similar_results_count",
    )
    korean_gap = {
        "queries": require_string_list(
            gap_raw.get("queries"), f"{label}.korean_gap.queries", minimum=2
        ),
        "similar_results_count": similar_results_count,
        "score": gap_score(similar_results_count),
        "evidence": require_string_list(
            gap_raw.get("evidence"), f"{label}.korean_gap.evidence"
        ),
    }

    source_raw = require_object(raw.get("source_trace"), f"{label}.source_trace")
    source_status = require_string(
        source_raw.get("status"), f"{label}.source_trace.status"
    ).lower()
    if source_status not in SOURCE_SCORES:
        raise ScoutError(
            f"{label}.source_trace.status is unsupported: {source_status}"
        )
    probable_url_value = source_raw.get("probable_original_url")
    probable_url = (
        None
        if probable_url_value in {None, ""}
        else require_url(
            probable_url_value, f"{label}.source_trace.probable_original_url"
        )
    )
    if source_status in {"verified_original", "probable_original"} and probable_url is None:
        raise ScoutError(
            f"{label}.source_trace.probable_original_url is required for {source_status}"
        )
    source_trace = {
        "status": source_status,
        "confidence": require_integer(
            source_raw.get("confidence"),
            f"{label}.source_trace.confidence",
            maximum=100,
        ),
        "probable_original_url": probable_url,
        "score": SOURCE_SCORES[source_status],
        "evidence": require_string_list(
            source_raw.get("evidence"), f"{label}.source_trace.evidence"
        ),
    }

    rights_raw = require_object(raw.get("rights"), f"{label}.rights")
    rights_status = require_string(
        rights_raw.get("status"), f"{label}.rights.status"
    ).lower()
    if rights_status not in RIGHTS_STATUSES:
        raise ScoutError(f"{label}.rights.status is unsupported: {rights_status}")
    rights = {
        "status": rights_status,
        "evidence": require_string_list(
            rights_raw.get("evidence"), f"{label}.rights.evidence"
        ),
    }

    flags = [
        require_string(item, f"{label}.risk_flags[{i}]").lower()
        for i, item in enumerate(
            require_list(raw.get("risk_flags", []), f"{label}.risk_flags")
        )
    ]
    invalid_flags = sorted(set(flags) - set(PENALTIES))
    if invalid_flags:
        raise ScoutError(
            f"{label}.risk_flags contains unsupported values: {invalid_flags}"
        )
    if source_status == "unknown":
        flags.append("source_unknown")
    if similar_results_count > 10:
        flags.append("korean_saturated")
    flags = list(dict.fromkeys(flags))

    component_scores = {
        **features,
        "korean_gap": korean_gap["score"],
        "source_traceability": source_trace["score"],
    }
    weighted_score = sum(
        features[key] * weight for key, weight in FEATURE_WEIGHTS.items()
    )
    weighted_score += korean_gap["score"] * 0.15
    weighted_score += source_trace["score"] * 0.10
    penalty_total = sum(PENALTIES[flag] for flag in flags)
    overall_score = round(
        max(0.0, min(100.0, weighted_score - penalty_total)), 1
    )

    exclusion_reasons: list[str] = []
    if not inspection["publicly_visible"]:
        exclusion_reasons.append("The source post is not publicly inspectable.")
    if not inspection["content_observed"]:
        exclusion_reasons.append("The candidate action was not directly observed.")
    if not inspection["short_form_or_clippable"]:
        exclusion_reasons.append("The source is not short-form or cleanly clippable.")
    if not any(current is not None for current in metrics.values()):
        exclusion_reasons.append("No exact public metric was recorded.")
    if max_age_hours > 0 and age_hours > max_age_hours:
        exclusion_reasons.append(
            f"The source is older than the {max_age_hours}-hour discovery window."
        )
    if rights_status == "not_permitted":
        exclusion_reasons.append("The recorded rights status is not_permitted.")

    views = metrics["views"] or 0
    early_viral = (
        age_hours <= 24
        and features["viral_momentum"] >= 80
        and views >= 50_000
    )
    return {
        "id": candidate_id,
        "platform": platform,
        "url": url,
        "canonical_url": canonical_url(url),
        "title": require_string(raw.get("title"), f"{label}.title", minimum=3),
        "creator": require_string(
            raw.get("creator"), f"{label}.creator", minimum=2
        ),
        "published_at": published_at.isoformat(),
        "age_hours": round(age_hours, 2),
        "summary": require_string(
            raw.get("summary"), f"{label}.summary", minimum=20
        ),
        "observed_action": require_string(
            raw.get("observed_action"), f"{label}.observed_action", minimum=20
        ),
        "story_pattern": normalize_story_pattern(raw.get("story_pattern"), label),
        "content_fingerprint": clean_text(raw.get("content_fingerprint")),
        "metrics": metrics,
        "metric_evidence": metric_evidence,
        "evidence_urls": evidence_urls,
        "research_evidence": require_string_list(
            raw.get("research_evidence"), f"{label}.research_evidence"
        ),
        "inspection": inspection,
        "features": features,
        "feature_reasons": feature_reasons,
        "korean_gap": korean_gap,
        "source_trace": source_trace,
        "rights": rights,
        "risk_flags": flags,
        "score_breakdown": {
            "components": component_scores,
            "weighted_score": round(weighted_score, 1),
            "penalties": {flag: PENALTIES[flag] for flag in flags},
            "penalty_total": penalty_total,
            "overall": overall_score,
        },
        "early_viral": early_viral,
        "local_review_only": rights_status
        not in {"owned", "licensed", "permission_confirmed"},
        "publication_ready": False,
        "recommendation_reason": require_string(
            raw.get("recommendation_reason"),
            f"{label}.recommendation_reason",
            minimum=20,
        ),
        "eligible": not exclusion_reasons,
        "exclusion_reasons": exclusion_reasons,
    }


def build_batch(
    raw: dict[str, Any], *, top_k: int, max_age_hours: int
) -> dict[str, Any]:
    if raw.get("schema_version") != SCHEMA_VERSION:
        raise ScoutError(f"schema_version must be {SCHEMA_VERSION}")
    if raw.get("collection_method") != "browser_or_public_web":
        raise ScoutError("collection_method must be browser_or_public_web")
    collected_at = parse_timestamp(raw.get("collected_at"), "collected_at")
    topic = require_string(raw.get("topic"), "topic", minimum=2)
    checks = normalize_platform_checks(raw.get("platform_checks"))
    candidates = [
        normalize_candidate(
            item,
            index,
            collected_at=collected_at,
            max_age_hours=max_age_hours,
        )
        for index, item in enumerate(
            require_list(raw.get("candidates"), "candidates")
        )
    ]

    ordered = sorted(
        candidates,
        key=lambda item: (-item["score_breakdown"]["overall"], item["id"]),
    )
    kept: list[dict[str, Any]] = []
    duplicates: list[dict[str, Any]] = []
    seen_urls: dict[str, str] = {}
    seen_fingerprints: dict[str, str] = {}
    for item in ordered:
        duplicate_of = seen_urls.get(item["canonical_url"])
        fingerprint = compact_fingerprint(item["content_fingerprint"])
        if duplicate_of is None and fingerprint:
            duplicate_of = seen_fingerprints.get(fingerprint)
        if duplicate_of is not None:
            duplicates.append({"id": item["id"], "duplicate_of": duplicate_of})
            continue
        kept.append(item)
        seen_urls[item["canonical_url"]] = item["id"]
        if fingerprint:
            seen_fingerprints[fingerprint] = item["id"]

    eligible = [item for item in kept if item["eligible"]]
    shortlist = eligible[:top_k]
    for rank, item in enumerate(shortlist, start=1):
        item["rank"] = rank
    excluded = [
        {
            "id": item["id"],
            "title": item["title"],
            "url": item["url"],
            "reasons": item["exclusion_reasons"],
        }
        for item in kept
        if not item["eligible"]
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "plugin_version": PLUGIN_VERSION,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "collection_method": "browser_or_public_web",
        "collected_at": collected_at.isoformat(),
        "topic": topic,
        "max_age_hours": max_age_hours,
        "platform_checks": checks,
        "candidate_count": len(candidates),
        "eligible_count": len(eligible),
        "selection_status": "awaiting_user_selection",
        "automatic_selection": False,
        "research_only": True,
        "publication_ready": False,
        "candidates": shortlist,
        "duplicates": duplicates,
        "excluded": excluded,
        "caveats": [
            "Scores prioritize editorial review and do not predict future views.",
            "A probable or verified source does not establish reuse permission.",
            "Rights marked unknown remain local-review only.",
        ],
    }


def metrics_text(metrics: dict[str, int | None]) -> str:
    return ", ".join(
        f"{key}={value:,}" for key, value in metrics.items() if value is not None
    ) or "no exact metric"


def build_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# 쇼츠 후보 찾기 결과",
        "",
        f"- 주제: {payload['topic']}",
        f"- 수집 시각: {payload['collected_at']}",
        f"- 시간 범위: {'비교 모드' if payload['max_age_hours'] == 0 else str(payload['max_age_hours']) + '시간'}",
        "- 상태: 사용자 Candidate ID 선택 대기",
        "- 자동 선택: 하지 않음",
        "- 게시 준비: 아님",
        "",
    ]
    if not payload["candidates"]:
        lines.extend(["조건을 충족한 후보가 없습니다.", ""])
    for item in payload["candidates"]:
        breakdown = item["score_breakdown"]
        lines.extend(
            [
                f"## {item['rank']}. {item['title']}",
                "",
                f"- Candidate ID: `{item['id']}`",
                f"- 점수: **{breakdown['overall']} / 100**",
                f"- 플랫폼 / 제작자: {item['platform']} / {item['creator']}",
                f"- URL: {item['url']}",
                f"- 게시 후 경과: {item['age_hours']}시간",
                f"- 공개 지표: {metrics_text(item['metrics'])}",
                f"- 관찰 장면: {item['observed_action']}",
                f"- 이야기 패턴: {item['story_pattern']}",
                f"- 추천 이유: {item['recommendation_reason']}",
                f"- Early Viral 검토 태그: {'해당' if item['early_viral'] else '해당 없음'}",
                f"- Korean Gap: {item['korean_gap']['score']} / 유사 한국 결과 {item['korean_gap']['similar_results_count']}개",
                f"- 한국어 검색어: {' / '.join(item['korean_gap']['queries'])}",
                f"- 원출처: {item['source_trace']['status']} / 신뢰도 {item['source_trace']['confidence']}%",
                f"- 원출처 후보 URL: {item['source_trace']['probable_original_url'] or '미확인'}",
                f"- 권리 상태: {item['rights']['status']}",
                f"- 구성 점수: {json.dumps(breakdown['components'], ensure_ascii=False)}",
                f"- 감점: {json.dumps(breakdown['penalties'], ensure_ascii=False)}",
                "",
            ]
        )
    lines.extend(
        [
            "사용자가 Candidate ID를 명시적으로 선택하기 전에는 다운로드, 대본, 제작, 렌더링 또는 업로드를 진행하지 않습니다.",
            "점수와 출처 추적 결과는 저작권 허가, 공정 이용, 수익화, 조회수 또는 게시 가능성을 보장하지 않습니다.",
            "",
        ]
    )
    return "\n".join(lines)


def add_common_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--input", required=True, help="Path to research-candidates.json"
    )
    parser.add_argument(
        "--max-age-hours",
        type=int,
        default=48,
        help="Use 0 to disable the recency gate",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=10,
        help="Number of candidates to return, from 1 to 10",
    )


def validate_args(args: argparse.Namespace) -> None:
    if args.max_age_hours < 0:
        raise ScoutError("--max-age-hours must be 0 or greater")
    if not 1 <= args.top_k <= 10:
        raise ScoutError("--top-k must be between 1 and 10")


def command_doctor(args: argparse.Namespace) -> int:
    payload = {
        "plugin": "s-finder",
        "version": PLUGIN_VERSION,
        "python": sys.version.split()[0],
        "standard_library_only": True,
        "platform_credentials_required": False,
        "database_required": False,
        "ready": sys.version_info >= (3, 10),
    }
    print(
        json.dumps(payload, ensure_ascii=False, indent=2)
        if args.json
        else "s-finder is ready."
    )
    return 0 if payload["ready"] else 1


def command_validate(args: argparse.Namespace) -> int:
    validate_args(args)
    payload = build_batch(
        load_json(Path(args.input).expanduser().resolve()),
        top_k=args.top_k,
        max_age_hours=args.max_age_hours,
    )
    print(
        json.dumps(
            {
                "valid": True,
                "candidate_count": payload["candidate_count"],
                "eligible_count": payload["eligible_count"],
                "shortlist_count": len(payload["candidates"]),
                "duplicates": len(payload["duplicates"]),
                "excluded": len(payload["excluded"]),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def command_rank(args: argparse.Namespace) -> int:
    validate_args(args)
    payload = build_batch(
        load_json(Path(args.input).expanduser().resolve()),
        top_k=args.top_k,
        max_age_hours=args.max_age_hours,
    )
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "shortlist.json"
    markdown_path = output_dir / "shortlist.md"
    json_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    markdown_path.write_text(build_markdown(payload), encoding="utf-8")
    print(
        json.dumps(
            {
                "shortlist_json": str(json_path),
                "shortlist_markdown": str(markdown_path),
                "eligible_count": payload["eligible_count"],
                "shortlist_count": len(payload["candidates"]),
                "selection_status": payload["selection_status"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate and rank evidence-backed s-finder video candidates."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor = subparsers.add_parser("doctor", help="Report local requirements")
    doctor.add_argument("--json", action="store_true")
    doctor.set_defaults(func=command_doctor)

    validate = subparsers.add_parser(
        "validate", help="Validate and score evidence without writing output"
    )
    add_common_arguments(validate)
    validate.set_defaults(func=command_validate)

    rank = subparsers.add_parser(
        "rank", help="Write a ranked JSON and Markdown shortlist"
    )
    add_common_arguments(rank)
    rank.add_argument("--output-dir", required=True)
    rank.set_defaults(func=command_rank)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except (ScoutError, FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
