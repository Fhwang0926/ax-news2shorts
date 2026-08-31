#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import functools
import getpass
import json
import os
import re
import shutil
import ssl
import subprocess
import sys
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen


PLUGIN_VERSION = "0.1.0"
SCHEMA_VERSION = 1
PLUGIN_ROOT = Path(__file__).resolve().parents[1]
YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"
YOUTUBE_KEYCHAIN_SERVICE = "shorts-suite.youtube-data-api-key"
YOUTUBE_KEYCHAIN_LABEL = "Shorts Suite YouTube Data API key"
LEGACY_YOUTUBE_KEYCHAIN_SERVICE = "senior-shorts.youtube-data-api-key"
YOUTUBE_ENVIRONMENT_VARIABLE = "YOUTUBE_API_KEY"
PLATFORMS = {
    "youtube",
    "tiktok",
    "instagram",
    "x",
    "reddit",
    "news",
    "community",
    "official",
    "other",
}
CHECK_STATUSES = {"ok", "blocked", "unavailable"}
CANDIDATE_TYPES = {"video_signal", "story_event"}
COLLECTION_METHODS = {"browser_or_public_web", "hybrid_youtube_api_browser"}
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
    "viral_momentum": 0.15,
    "hook": 0.15,
    "story_twist": 0.10,
    "explainability": 0.10,
    "visual_clarity": 0.10,
    "editability": 0.05,
    "entertainment_value": 0.10,
}
PACKAGE_FEATURE_WEIGHTS = {
    "subject_recognition": 0.18,
    "conflict_abnormality": 0.15,
    "payoff_clarity": 0.15,
    "twist_strength": 0.12,
    "asset_readiness": 0.12,
    "freshness": 0.10,
    "comment_signal": 0.08,
    "evidence_strength": 0.06,
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


def youtube_setup_command(command: str) -> str:
    script = PLUGIN_ROOT / "scripts" / "discover.py"
    return f'python3 -B "{script}" {command}'


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
        raise ScoutError(
            "YouTube Data API 키가 없습니다. "
            f"`{youtube_setup_command('configure-youtube')}`를 먼저 실행하세요."
        )
    url = f"{YOUTUBE_API_BASE}/{resource}?{urlencode(params, doseq=True)}"
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "shorts-suite-discovery/0.1",
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
            detail = clean_text((payload.get("error") or {}).get("message"))
        except (UnicodeDecodeError, json.JSONDecodeError, AttributeError):
            detail = ""
        suffix = f": {detail}" if detail else ""
        raise ScoutError(f"YouTube Data API 요청 실패 ({exc.code}){suffix}") from exc
    except (URLError, TimeoutError) as exc:
        raise ScoutError(f"YouTube Data API 연결 실패: {exc}") from exc
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ScoutError("YouTube Data API JSON 응답을 읽을 수 없습니다.") from exc
    if not isinstance(payload, dict):
        raise ScoutError("YouTube Data API 응답 형식이 올바르지 않습니다.")
    return payload


def validate_youtube_api_key(api_key: str | None = None) -> None:
    youtube_request(
        "i18nRegions",
        {"part": "snippet", "hl": "ko", "fields": "items(id)"},
        api_key=api_key,
        timeout=15,
    )


def parse_youtube_duration(value: Any) -> float:
    match = re.fullmatch(
        r"P(?:(?P<days>\d+)D)?T(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?",
        clean_text(value),
    )
    if not match:
        return 0.0
    return (
        int(match.group("days") or 0) * 86400
        + int(match.group("hours") or 0) * 3600
        + int(match.group("minutes") or 0) * 60
        + int(match.group("seconds") or 0)
    )


def public_count(value: Any) -> int:
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError):
        return 0


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

    candidate_type = clean_text(raw.get("candidate_type") or "video_signal").lower()
    if candidate_type not in CANDIDATE_TYPES:
        raise ScoutError(f"{label}.candidate_type is unsupported: {candidate_type}")

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
    packageable_value = inspection_raw.get("packageable_with_public_evidence")
    inspection["packageable_with_public_evidence"] = (
        require_bool(
            packageable_value,
            f"{label}.inspection.packageable_with_public_evidence",
        )
        if packageable_value is not None
        else inspection["short_form_or_clippable"]
    )

    feature_raw = require_object(raw.get("features"), f"{label}.features")
    reason_raw = require_object(raw.get("feature_reasons"), f"{label}.feature_reasons")
    features = {
        key: require_integer(
            feature_raw.get(key), f"{label}.features.{key}", maximum=100
        )
        for key in FEATURE_WEIGHTS
        if key != "entertainment_value"
    }
    feature_reasons = {
        key: require_string(
            reason_raw.get(key), f"{label}.feature_reasons.{key}", minimum=12
        )
        for key in FEATURE_WEIGHTS
        if key != "entertainment_value"
    }
    if feature_raw.get("entertainment_value") is None:
        features["entertainment_value"] = round(
            (
                features["hook"]
                + features["story_twist"]
                + features["visual_clarity"]
            )
            / 3
        )
        feature_reasons["entertainment_value"] = (
            "Derived from hook, story twist, and visual clarity for legacy inputs."
        )
    else:
        features["entertainment_value"] = require_integer(
            feature_raw.get("entertainment_value"),
            f"{label}.features.entertainment_value",
            maximum=100,
        )
        feature_reasons["entertainment_value"] = require_string(
            reason_raw.get("entertainment_value"),
            f"{label}.feature_reasons.entertainment_value",
            minimum=12,
        )

    package_feature_raw = raw.get("package_features")
    package_reason_raw = raw.get("package_feature_reasons")
    package_score: dict[str, Any] | None = None
    if package_feature_raw is not None or candidate_type == "story_event":
        package_feature_raw = require_object(
            package_feature_raw, f"{label}.package_features"
        )
        package_reason_raw = require_object(
            package_reason_raw, f"{label}.package_feature_reasons"
        )
        package_features = {
            key: require_integer(
                package_feature_raw.get(key),
                f"{label}.package_features.{key}",
                maximum=100,
            )
            for key in PACKAGE_FEATURE_WEIGHTS
        }
        package_feature_reasons = {
            key: require_string(
                package_reason_raw.get(key),
                f"{label}.package_feature_reasons.{key}",
                minimum=12,
            )
            for key in PACKAGE_FEATURE_WEIGHTS
        }
        package_score = {
            "components": package_features,
            "reasons": package_feature_reasons,
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
    if package_score is not None:
        package_weighted = sum(
            package_score["components"][key] * weight
            for key, weight in PACKAGE_FEATURE_WEIGHTS.items()
        )
        package_weighted += korean_gap["score"] * 0.04
        package_score["components"]["korean_gap_opportunity"] = korean_gap["score"]
        package_score["overall"] = round(max(0.0, min(100.0, package_weighted)), 1)
    ranking_score = (
        round(overall_score * 0.60 + package_score["overall"] * 0.40, 1)
        if candidate_type == "story_event" and package_score is not None
        else overall_score
    )

    exclusion_reasons: list[str] = []
    if not inspection["publicly_visible"]:
        exclusion_reasons.append("The source post is not publicly inspectable.")
    if not inspection["content_observed"]:
        exclusion_reasons.append("The candidate action was not directly observed.")
    if candidate_type == "video_signal" and not inspection["short_form_or_clippable"]:
        exclusion_reasons.append("The source is not short-form or cleanly clippable.")
    if candidate_type == "story_event" and not inspection["packageable_with_public_evidence"]:
        exclusion_reasons.append(
            "The story event cannot be packaged from the inspected public evidence."
        )
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
        "candidate_type": candidate_type,
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
        "subject": (
            require_string(raw.get("subject"), f"{label}.subject", minimum=2)
            if candidate_type == "story_event"
            else clean_text(raw.get("subject"))
        ),
        "event": (
            require_string(raw.get("event"), f"{label}.event", minimum=8)
            if candidate_type == "story_event"
            else clean_text(raw.get("event"))
        ),
        "one_line_payoff": (
            require_string(
                raw.get("one_line_payoff"), f"{label}.one_line_payoff", minimum=8
            )
            if candidate_type == "story_event"
            else clean_text(raw.get("one_line_payoff"))
        ),
        "story_cluster_id": clean_text(raw.get("story_cluster_id")),
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
        "package_score": package_score,
        "ranking_score": ranking_score,
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
    raw: dict[str, Any], *, top_k: int, max_age_hours: int, min_youtube: int
) -> dict[str, Any]:
    if raw.get("schema_version") != SCHEMA_VERSION:
        raise ScoutError(f"schema_version must be {SCHEMA_VERSION}")
    collection_method = clean_text(raw.get("collection_method"))
    if collection_method not in COLLECTION_METHODS:
        raise ScoutError(
            "collection_method must be browser_or_public_web or hybrid_youtube_api_browser"
        )
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
        key=lambda item: (-item["ranking_score"], item["id"]),
    )
    kept: list[dict[str, Any]] = []
    duplicates: list[dict[str, Any]] = []
    seen_urls: dict[str, str] = {}
    seen_fingerprints: dict[str, str] = {}
    seen_clusters: dict[str, str] = {}
    for item in ordered:
        duplicate_of = seen_urls.get(item["canonical_url"])
        cluster_id = compact_fingerprint(item["story_cluster_id"])
        if duplicate_of is None and cluster_id:
            duplicate_of = seen_clusters.get(cluster_id)
        fingerprint = compact_fingerprint(item["content_fingerprint"])
        if duplicate_of is None and fingerprint:
            duplicate_of = seen_fingerprints.get(fingerprint)
        if duplicate_of is not None:
            duplicates.append({"id": item["id"], "duplicate_of": duplicate_of})
            continue
        kept.append(item)
        seen_urls[item["canonical_url"]] = item["id"]
        if cluster_id:
            seen_clusters[cluster_id] = item["id"]
        if fingerprint:
            seen_fingerprints[fingerprint] = item["id"]

    eligible = [item for item in kept if item["eligible"]]
    youtube_candidates = [item for item in eligible if item["platform"] == "youtube"]
    reserved_youtube = youtube_candidates[: min(min_youtube, top_k)]
    reserved_ids = {item["id"] for item in reserved_youtube}
    shortlist = reserved_youtube + [
        item for item in eligible if item["id"] not in reserved_ids
    ][: max(0, top_k - len(reserved_youtube))]
    shortlist.sort(key=lambda item: (-item["ranking_score"], item["id"]))
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
        "collection_method": collection_method,
        "collected_at": collected_at.isoformat(),
        "topic": topic,
        "max_age_hours": max_age_hours,
        "min_youtube": min_youtube,
        "youtube_eligible_count": len(youtube_candidates),
        "youtube_shortfall": max(0, min_youtube - len(youtube_candidates)),
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
        f"- YouTube 최소 슬롯: {payload['min_youtube']} / 적격 {payload['youtube_eligible_count']} / 부족 {payload['youtube_shortfall']}",
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
                f"- 후보 유형: {item['candidate_type']}",
                f"- 정렬 점수: **{item['ranking_score']} / 100**",
                f"- Discovery 점수: {breakdown['overall']} / 100",
                f"- 재미 점수: {item['features']['entertainment_value']} / 100",
                *(
                    [f"- Package 점수: {item['package_score']['overall']} / 100"]
                    if item["package_score"] is not None
                    else []
                ),
                f"- 플랫폼 / 제작자: {item['platform']} / {item['creator']}",
                f"- URL: {item['url']}",
                f"- 게시 후 경과: {item['age_hours']}시간",
                f"- 공개 지표: {metrics_text(item['metrics'])}",
                f"- 관찰 장면: {item['observed_action']}",
                f"- 이야기 패턴: {item['story_pattern']}",
                *(
                    [
                        f"- 대상: {item['subject']}",
                        f"- 사건: {item['event']}",
                        f"- 한 문장 결말: {item['one_line_payoff']}",
                    ]
                    if item["candidate_type"] == "story_event"
                    else []
                ),
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
    parser.add_argument(
        "--min-youtube",
        type=int,
        default=0,
        help="Reserve up to this many shortlist slots for eligible YouTube candidates",
    )


def validate_args(args: argparse.Namespace) -> None:
    if args.max_age_hours < 0:
        raise ScoutError("--max-age-hours must be 0 or greater")
    if not 1 <= args.top_k <= 10:
        raise ScoutError("--top-k must be between 1 and 10")
    if not 0 <= args.min_youtube <= args.top_k:
        raise ScoutError("--min-youtube must be between 0 and --top-k")


def command_configure_youtube(args: argparse.Namespace) -> int:
    del args
    if sys.platform != "darwin":
        raise ScoutError(
            "macOS 키체인은 이 운영체제에서 사용할 수 없습니다. "
            f"{YOUTUBE_ENVIRONMENT_VARIABLE} 환경변수를 사용하세요."
        )
    security = shutil.which("security")
    if not security:
        raise ScoutError("macOS security 명령을 찾을 수 없습니다.")
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
        raise ScoutError(f"macOS 키체인 실행 실패: {exc}") from exc
    if result.returncode != 0:
        raise ScoutError("YouTube Data API 키를 macOS 키체인에 저장하지 못했습니다.")
    youtube_api_key_record.cache_clear()
    stored_key, source = youtube_api_key_record()
    if not stored_key or source != "keychain":
        raise ScoutError("저장 후 YouTube Data API 키를 키체인에서 확인하지 못했습니다.")
    try:
        validate_youtube_api_key(stored_key)
    except ScoutError as exc:
        raise ScoutError(
            "키는 키체인에 저장했지만 YouTube Data API 검증에 실패했습니다. "
            "Google Cloud에서 YouTube Data API v3 활성화와 API 제한을 확인하세요. "
            f"원인: {exc}"
        ) from exc
    print("YouTube Data API 키를 키체인에 저장하고 공개 데이터 조회를 확인했습니다.")
    return 0


def command_youtube_signals(args: argparse.Namespace) -> int:
    if not 1 <= args.hours <= 8760:
        raise ScoutError("--hours must be between 1 and 8760")
    if not 1 <= args.per_query <= 50:
        raise ScoutError("--per-query must be between 1 and 50")
    if not 1 <= args.max_signals <= 100:
        raise ScoutError("--max-signals must be between 1 and 100")
    if not 15 <= args.max_duration <= 180:
        raise ScoutError("--max-duration must be between 15 and 180 seconds")
    region_code = clean_text(args.region_code).upper()
    if not re.fullmatch(r"[A-Z]{2}", region_code):
        raise ScoutError("--region-code must be a two-letter country code")
    language = clean_text(args.relevance_language)
    if not re.fullmatch(r"[A-Za-z]{2,3}(?:-[A-Za-z]{2,8})?", language):
        raise ScoutError("--relevance-language must be a language code")
    queries = list(dict.fromkeys(clean_text(query) for query in args.query))
    queries = [query for query in queries if query]
    if not queries:
        raise ScoutError("At least one --query is required")
    api_key, key_source = youtube_api_key_record()
    if not api_key:
        raise ScoutError(
            "YouTube Data API 키가 없습니다. "
            f"`{youtube_setup_command('configure-youtube')}`를 먼저 실행하세요."
        )

    collected_at = dt.datetime.now(dt.timezone.utc)
    published_after = (collected_at - dt.timedelta(hours=args.hours)).isoformat(
        timespec="seconds"
    ).replace("+00:00", "Z")
    matches: dict[str, dict[str, Any]] = {}
    search_calls = 0
    for query in queries:
        search_calls += 1
        response = youtube_request(
            "search",
            {
                "part": "snippet",
                "q": query,
                "type": "video",
                "order": args.order,
                "videoDuration": "short",
                "publishedAfter": published_after,
                "regionCode": region_code,
                "relevanceLanguage": language,
                "safeSearch": args.safe_search,
                "maxResults": args.per_query,
                "fields": "items(id/videoId,snippet(title,channelId,channelTitle,publishedAt,thumbnails/high/url))",
            },
            api_key=api_key,
        )
        for item in response.get("items") or []:
            video_id = clean_text((item.get("id") or {}).get("videoId"))
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
            video_id = clean_text(item.get("id"))
            matched = matches.get(video_id)
            if not matched:
                continue
            duration = parse_youtube_duration(
                (item.get("contentDetails") or {}).get("duration")
            )
            if not duration or duration > args.max_duration:
                continue
            snippet = item.get("snippet") or matched["search_snippet"]
            statistics = item.get("statistics") or {}
            status = item.get("status") or {}
            if clean_text(status.get("privacyStatus")) not in {"", "public"}:
                continue
            published_at = clean_text(snippet.get("publishedAt"))
            try:
                published = parse_timestamp(published_at, "youtube.published_at")
            except ScoutError:
                continue
            age_hours = max(
                0.01,
                (
                    collected_at
                    - published.astimezone(dt.timezone.utc)
                ).total_seconds()
                / 3600,
            )
            views = public_count(statistics.get("viewCount"))
            likes = public_count(statistics.get("likeCount"))
            comments = public_count(statistics.get("commentCount"))
            signals.append(
                {
                    "signal_id": f"yt-{video_id}",
                    "candidate_status": "discovery_lead",
                    "platform": "youtube",
                    "video_id": video_id,
                    "canonical_url": f"https://www.youtube.com/watch?v={video_id}",
                    "shorts_url": f"https://www.youtube.com/shorts/{video_id}",
                    "title": clean_text(snippet.get("title")),
                    "channel_id": clean_text(snippet.get("channelId")),
                    "channel_title": clean_text(snippet.get("channelTitle")),
                    "published_at": published.isoformat(),
                    "age_hours": round(age_hours, 2),
                    "duration_seconds": round(duration, 3),
                    "metrics": {
                        "views": views,
                        "likes": likes,
                        "comments": comments,
                        "shares": None,
                    },
                    "signal_metrics": {
                        "views_per_hour": round(views / age_hours, 2),
                        "like_rate": round(likes / max(views, 1), 6),
                        "comment_rate": round(comments / max(views, 1), 6),
                    },
                    "thumbnail_url": clean_text(
                        ((snippet.get("thumbnails") or {}).get("high") or {}).get("url")
                    ),
                    "matched_queries": matched["matched_queries"],
                    "public_status": clean_text(status.get("privacyStatus")) or "public",
                    "embeddable": bool(status.get("embeddable")),
                    "metric_evidence": [
                        "YouTube Data API v3 videos.list public metadata captured "
                        f"at {collected_at.isoformat()}."
                    ],
                    "browser_verification_required": True,
                    "rights": {
                        "status": "unknown",
                        "evidence": [
                            "Public metadata does not establish reuse permission."
                        ],
                    },
                    "reuse_allowed": False,
                }
            )

    signals.sort(
        key=lambda item: (
            -item["signal_metrics"]["views_per_hour"],
            -item["metrics"]["views"],
            item["signal_id"],
        )
    )
    signals = signals[: args.max_signals]
    if not signals:
        raise ScoutError("조건에 맞는 YouTube 공개 메타데이터 신호를 찾지 못했습니다.")
    output = (
        Path(args.output).expanduser().resolve()
        if args.output
        else Path.cwd()
        / "outputs"
        / "shorts-suite"
        / "discovery"
        / collected_at.strftime("%Y%m%d_%H%M%S")
        / "youtube-api-signals.json"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "generated_at": collected_at.isoformat(),
        "source": "youtube_data_api_v3",
        "collection_method": "youtube_data_api_v3",
        "api_key_source": key_source,
        "window_hours": args.hours,
        "published_after": published_after,
        "region_code": region_code,
        "relevance_language": language,
        "queries": queries,
        "request_calls": {
            "search_list": search_calls,
            "videos_list": videos_calls,
            "pagination": False,
            "note": "Quota limits use Google Cloud project buckets. This command requests one search page per query.",
        },
        "selection_required": True,
        "production_allowed": False,
        "browser_verification_required": True,
        "rights_policy": "API metadata is a discovery signal and does not grant media reuse rights.",
        "signals": signals,
    }
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "output": str(output),
                "signals": len(signals),
                "search_list_calls": search_calls,
                "videos_list_calls": videos_calls,
                "browser_verification_required": True,
                "selection_required": True,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def command_doctor(args: argparse.Namespace) -> int:
    youtube_key, youtube_key_source = youtube_api_key_record()
    youtube_check_limited = youtube_key_source is None and youtube_keychain_check_limited()
    youtube_api_reachable: bool | None = None
    youtube_api_error = ""
    if args.check_youtube and youtube_key:
        try:
            validate_youtube_api_key(youtube_key)
            youtube_api_reachable = True
        except ScoutError as exc:
            youtube_api_reachable = False
            youtube_api_error = str(exc)
    payload = {
        "plugin": "shorts-suite:discover",
        "version": PLUGIN_VERSION,
        "python": sys.version.split()[0],
        "standard_library_only": True,
        "platform_credentials_required": False,
        "database_required": False,
        "youtube_api": {
            "optional": True,
            "configured": youtube_key_source is not None,
            "source": youtube_key_source,
            "keychain_check_limited": youtube_check_limited,
            "checked": bool(args.check_youtube),
            "reachable": youtube_api_reachable,
            "error": youtube_api_error,
            "setup_command": (
                "" if youtube_key_source else youtube_setup_command("configure-youtube")
            ),
            "ssl_ca_file": trusted_ca_file(),
            "ssl_verification_enabled": True,
        },
        "ready_for_youtube_api": bool(
            youtube_key_source and youtube_api_reachable is not False
        ),
        "ready": sys.version_info >= (3, 10),
    }
    print(
        json.dumps(payload, ensure_ascii=False, indent=2)
        if args.json
        else "Shorts Suite discovery is ready."
    )
    return 0 if payload["ready"] else 1


def command_validate(args: argparse.Namespace) -> int:
    validate_args(args)
    payload = build_batch(
        load_json(Path(args.input).expanduser().resolve()),
        top_k=args.top_k,
        max_age_hours=args.max_age_hours,
        min_youtube=args.min_youtube,
    )
    print(
        json.dumps(
            {
                "valid": True,
                "candidate_count": payload["candidate_count"],
                "eligible_count": payload["eligible_count"],
                "shortlist_count": len(payload["candidates"]),
                "youtube_eligible_count": payload["youtube_eligible_count"],
                "youtube_shortfall": payload["youtube_shortfall"],
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
        min_youtube=args.min_youtube,
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
                "youtube_eligible_count": payload["youtube_eligible_count"],
                "youtube_shortfall": payload["youtube_shortfall"],
                "selection_status": payload["selection_status"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Collect optional YouTube metadata leads, then validate and rank evidence-backed Shorts candidates."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor = subparsers.add_parser("doctor", help="Report local requirements")
    doctor.add_argument(
        "--check-youtube",
        action="store_true",
        help="Validate the configured YouTube Data API key with a public read request",
    )
    doctor.add_argument("--json", action="store_true")
    doctor.set_defaults(func=command_doctor)

    configure_youtube = subparsers.add_parser(
        "configure-youtube",
        help="Store a YouTube Data API key in the macOS Keychain",
    )
    configure_youtube.set_defaults(func=command_configure_youtube)

    youtube_signals = subparsers.add_parser(
        "youtube-signals",
        help="Collect public YouTube metadata leads for later browser verification",
    )
    youtube_signals.add_argument(
        "--query", action="append", required=True, help="Repeat for multiple searches"
    )
    youtube_signals.add_argument("--hours", type=int, default=48)
    youtube_signals.add_argument("--per-query", type=int, default=10)
    youtube_signals.add_argument("--max-signals", type=int, default=30)
    youtube_signals.add_argument("--max-duration", type=int, default=180)
    youtube_signals.add_argument("--region-code", default="US")
    youtube_signals.add_argument("--relevance-language", default="en")
    youtube_signals.add_argument(
        "--order", choices=("date", "relevance", "viewCount"), default="viewCount"
    )
    youtube_signals.add_argument(
        "--safe-search", choices=("moderate", "strict"), default="moderate"
    )
    youtube_signals.add_argument("--output")
    youtube_signals.set_defaults(func=command_youtube_signals)

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
