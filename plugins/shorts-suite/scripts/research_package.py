#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit


PLUGIN_VERSION = "0.1.0"
SCHEMA_VERSION = 1
SAFE_ID = re.compile(r"[0-9A-Za-z][0-9A-Za-z._-]{0,79}")
CLAIM_STATUSES = {
    "verified",
    "likely",
    "unconfirmed",
    "contradicted",
    "opinion",
    "reaction_only",
}
RIGHTS_STATUSES = {
    "owned",
    "licensed",
    "permission_confirmed",
    "public_domain",
    "official_press_asset",
    "transformative_review",
    "unknown",
    "unreviewed",
    "not_permitted",
}
LOCAL_REVIEW_RIGHTS = {"transformative_review", "unknown", "unreviewed"}
REQUIRED_JSON_FILES = (
    "project.json",
    "source-graph.json",
    "claim-sheet.json",
    "asset-manifest.json",
    "comments.json",
    "story.json",
    "timeline.json",
)
REQUIRED_TEXT_FILES = ("narration.md", "subtitles.srt", "report.md")
REQUIRED_DIRS = (
    "sources",
    "evidence",
    "assets/raw",
    "assets/derived",
    "comments/raw",
    "comments/production",
    "scenes",
    "review",
)


class PackageError(ValueError):
    pass


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def clean_text(value: Any) -> str:
    return " ".join(str(value or "").split())


def load_object(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise PackageError(f"JSON object required: {path}")
    return value


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def require_id(value: Any, label: str) -> str:
    result = clean_text(value)
    if not SAFE_ID.fullmatch(result):
        raise PackageError(f"{label} must be a safe 1-80 character identifier")
    return result


def is_url(value: Any) -> bool:
    parsed = urlsplit(clean_text(value))
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def require_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise PackageError(f"{label} must be an array")
    return value


def require_bool(value: Any, label: str) -> bool:
    if not isinstance(value, bool):
        raise PackageError(f"{label} must be true or false")
    return value


def selected_candidate(shortlist: dict[str, Any], candidate_id: str) -> dict[str, Any]:
    candidates = require_list(shortlist.get("candidates"), "shortlist.candidates")
    matches = [
        item
        for item in candidates
        if isinstance(item, dict) and clean_text(item.get("id")) == candidate_id
    ]
    if len(matches) != 1:
        raise PackageError(f"Candidate ID not found exactly once: {candidate_id}")
    candidate = matches[0]
    if candidate.get("eligible") is False:
        raise PackageError(f"Excluded candidate cannot be packaged: {candidate_id}")
    return candidate


def ensure_new_project_dir(project_dir: Path) -> None:
    if project_dir.exists() and any(project_dir.iterdir()):
        raise PackageError(f"Project directory is not empty: {project_dir}")
    project_dir.mkdir(parents=True, exist_ok=True)
    for relative in REQUIRED_DIRS:
        (project_dir / relative).mkdir(parents=True, exist_ok=True)


def source_seed(candidate: dict[str, Any], created_at: str) -> dict[str, Any]:
    source_trace = candidate.get("source_trace")
    source_trace = source_trace if isinstance(source_trace, dict) else {}
    rights = candidate.get("rights")
    rights = rights if isinstance(rights, dict) else {}
    source_url = clean_text(source_trace.get("probable_original_url"))
    if not is_url(source_url):
        source_url = clean_text(candidate.get("canonical_url") or candidate.get("url"))
    evidence: list[str] = []
    for field in (source_trace.get("evidence"), candidate.get("research_evidence")):
        if isinstance(field, list):
            evidence.extend(clean_text(item) for item in field if clean_text(item))
    return {
        "id": "source-001",
        "url": source_url,
        "canonical_url": source_url,
        "publisher": clean_text(candidate.get("creator")),
        "source_type": "candidate_post",
        "published_at": clean_text(candidate.get("published_at")),
        "collected_at": created_at,
        "origin_status": clean_text(source_trace.get("status") or "unknown"),
        "reliability": None,
        "content_sha256": "",
        "archived_files": [],
        "rights_status": clean_text(rights.get("status") or "unknown"),
        "evidence": list(dict.fromkeys(evidence)),
    }


def command_init(args: argparse.Namespace) -> int:
    shortlist_path = Path(args.shortlist).expanduser().resolve()
    project_dir = Path(args.project_dir).expanduser().resolve()
    candidate_id = require_id(args.candidate_id, "--candidate-id")
    shortlist = load_object(shortlist_path)
    candidate = selected_candidate(shortlist, candidate_id)
    ensure_new_project_dir(project_dir)
    created_at = now_iso()
    reference_channels = [clean_text(value) for value in args.reference_channel]
    reference_channels = [value for value in reference_channels if value]
    invalid_channels = [value for value in reference_channels if not is_url(value)]
    if invalid_channels:
        raise PackageError(f"Invalid reference-channel URL: {invalid_channels[0]}")
    source = source_seed(candidate, created_at)
    subject = clean_text(candidate.get("subject") or candidate.get("creator"))
    event = clean_text(candidate.get("event") or candidate.get("summary"))
    payoff = clean_text(candidate.get("one_line_payoff"))

    write_json(
        project_dir / "project.json",
        {
            "schema_version": SCHEMA_VERSION,
            "plugin_version": PLUGIN_VERSION,
            "candidate_id": candidate_id,
            "candidate_type": clean_text(candidate.get("candidate_type") or "video_signal"),
            "created_at": created_at,
            "updated_at": created_at,
            "status": "research_initialized",
            "reference_channels": reference_channels,
            "candidate_snapshot": candidate,
            "selection": {
                "confirmed": True,
                "selected_candidate_id": candidate_id,
                "confirmed_at": created_at,
            },
            "reviews": {
                "facts_reviewed": False,
                "rights_reviewed": False,
            },
            "readiness": {
                "research_ready": False,
                "local_review_ready": False,
                "render_handoff_ready": False,
                "publish_ready": False,
                "publish_blocked": True,
            },
        },
    )
    write_json(
        project_dir / "source-graph.json",
        {
            "schema_version": SCHEMA_VERSION,
            "origin": {
                "status": source["origin_status"],
                "earliest_known_source_id": "source-001",
                "alternative_source_ids": [],
            },
            "nodes": [source],
            "edges": [],
        },
    )
    write_json(
        project_dir / "claim-sheet.json",
        {"schema_version": SCHEMA_VERSION, "claims": []},
    )
    write_json(
        project_dir / "asset-manifest.json",
        {"schema_version": SCHEMA_VERSION, "assets": []},
    )
    write_json(
        project_dir / "comments.json",
        {"schema_version": SCHEMA_VERSION, "comments": []},
    )
    write_json(
        project_dir / "story.json",
        {
            "schema_version": SCHEMA_VERSION,
            "story_id": candidate_id,
            "subject": subject,
            "event": event,
            "story_type": clean_text(candidate.get("story_pattern") or "other"),
            "one_line_payoff": payoff,
            "title_variants": [],
            "narration_segments": [],
        },
    )
    write_json(
        project_dir / "timeline.json",
        {
            "schema_version": SCHEMA_VERSION,
            "renderer_neutral": True,
            "canvas": {"width": 1080, "height": 1920, "fps": 30},
            "scenes": [],
        },
    )
    (project_dir / "narration.md").write_text(
        f"# 내레이션\n\n- Candidate ID: `{candidate_id}`\n\n",
        encoding="utf-8",
    )
    (project_dir / "subtitles.srt").write_text("", encoding="utf-8")
    (project_dir / "report.md").write_text(
        "\n".join(
            [
                "# 쇼츠 리서치 패키지",
                "",
                f"- Candidate ID: `{candidate_id}`",
                f"- 대상: {subject}",
                f"- 사건: {event}",
                f"- 한 문장 결말: {payoff or '조사 필요'}",
                "- 상태: 심층 조사 초기화",
                "",
                "출처·주장·에셋·댓글을 검증한 뒤 `validate --stage research`를 실행합니다.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "project_dir": str(project_dir),
                "candidate_id": candidate_id,
                "status": "research_initialized",
                "publish_blocked": True,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def load_project_files(project_dir: Path) -> dict[str, dict[str, Any]]:
    missing = [name for name in REQUIRED_JSON_FILES if not (project_dir / name).is_file()]
    missing.extend(name for name in REQUIRED_TEXT_FILES if not (project_dir / name).is_file())
    missing.extend(name for name in REQUIRED_DIRS if not (project_dir / name).is_dir())
    if missing:
        raise PackageError(f"Missing package paths: {sorted(missing)}")
    return {name: load_object(project_dir / name) for name in REQUIRED_JSON_FILES}


def collect_ids(
    items: Any,
    label: str,
    errors: list[str],
) -> tuple[list[dict[str, Any]], set[str]]:
    if not isinstance(items, list):
        errors.append(f"{label} must be an array")
        return [], set()
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            errors.append(f"{label}[{index}] must be an object")
            continue
        item_id = clean_text(item.get("id"))
        if not SAFE_ID.fullmatch(item_id):
            errors.append(f"{label}[{index}].id is invalid")
            continue
        if item_id in seen:
            errors.append(f"Duplicate {label} id: {item_id}")
            continue
        seen.add(item_id)
        result.append(item)
    return result, seen


def string_ids(value: Any, label: str, errors: list[str]) -> set[str]:
    if not isinstance(value, list):
        errors.append(f"{label} must be an array")
        return set()
    result: set[str] = set()
    for item in value:
        item_id = clean_text(item)
        if not SAFE_ID.fullmatch(item_id):
            errors.append(f"{label} contains an invalid id")
            continue
        result.add(item_id)
    return result


def existing_relative_file(project_dir: Path, value: Any) -> bool:
    relative = clean_text(value)
    if not relative:
        return False
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts:
        return False
    return (project_dir / path).is_file()


def validate_package(project_dir: Path, stage: str) -> dict[str, Any]:
    loaded = load_project_files(project_dir)
    errors: list[str] = []
    warnings: list[str] = []
    project = loaded["project.json"]
    source_graph = loaded["source-graph.json"]
    claim_sheet = loaded["claim-sheet.json"]
    asset_manifest = loaded["asset-manifest.json"]
    comments_doc = loaded["comments.json"]
    story = loaded["story.json"]
    timeline = loaded["timeline.json"]
    if timeline.get("renderer_neutral") is not True:
        errors.append("timeline.renderer_neutral must be true")

    if project.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"project.json schema_version must be {SCHEMA_VERSION}")
    try:
        candidate_id = require_id(project.get("candidate_id"), "project.candidate_id")
    except PackageError as exc:
        errors.append(str(exc))
        candidate_id = ""
    selection = project.get("selection")
    if not isinstance(selection, dict) or selection.get("confirmed") is not True:
        errors.append("Candidate selection must be explicitly confirmed")
    elif clean_text(selection.get("selected_candidate_id")) != candidate_id:
        errors.append("Selected Candidate ID does not match project.candidate_id")

    sources, source_ids = collect_ids(source_graph.get("nodes"), "sources", errors)
    if not sources:
        errors.append("At least one source node is required")
    for source in sources:
        source_id = clean_text(source.get("id"))
        if not is_url(source.get("url")):
            errors.append(f"Source URL is invalid: {source_id}")
        rights_status = clean_text(source.get("rights_status") or "unknown")
        if rights_status not in RIGHTS_STATUSES:
            errors.append(f"Unsupported source rights status: {source_id}: {rights_status}")
    origin = source_graph.get("origin")
    if not isinstance(origin, dict):
        errors.append("source-graph.origin must be an object")
    else:
        earliest = clean_text(origin.get("earliest_known_source_id"))
        if earliest and earliest not in source_ids:
            errors.append(f"Origin references missing source: {earliest}")
        alternatives = string_ids(
            origin.get("alternative_source_ids", []),
            "source-graph.origin.alternative_source_ids",
            errors,
        )
        missing = alternatives - source_ids
        if missing:
            errors.append(f"Origin alternatives reference missing sources: {sorted(missing)}")
    edges = source_graph.get("edges")
    if not isinstance(edges, list):
        errors.append("source-graph.edges must be an array")
    else:
        for index, edge in enumerate(edges):
            if not isinstance(edge, dict):
                errors.append(f"source-graph.edges[{index}] must be an object")
                continue
            from_id = clean_text(edge.get("from_source_id"))
            to_id = clean_text(edge.get("to_source_id"))
            if from_id not in source_ids or to_id not in source_ids:
                errors.append(f"Source edge references missing nodes: {index}")
            if not clean_text(edge.get("relationship")):
                errors.append(f"Source edge relationship is empty: {index}")

    claims, claim_ids = collect_ids(claim_sheet.get("claims"), "claims", errors)
    if not claims:
        errors.append("At least one source-linked claim is required")
    claim_status_by_id: dict[str, str] = {}
    for claim in claims:
        claim_id = clean_text(claim.get("id"))
        statement = clean_text(claim.get("statement"))
        if not statement:
            errors.append(f"Claim statement is empty: {claim_id}")
        status = clean_text(claim.get("status"))
        claim_status_by_id[claim_id] = status
        if status not in CLAIM_STATUSES:
            errors.append(f"Unsupported claim status: {claim_id}: {status}")
        confidence = claim.get("confidence")
        if (
            isinstance(confidence, bool)
            or not isinstance(confidence, (int, float))
            or not 0 <= confidence <= 1
        ):
            errors.append(f"Claim confidence must be between 0 and 1: {claim_id}")
        supporting = string_ids(
            claim.get("supporting_source_ids", []),
            f"claims.{claim_id}.supporting_source_ids",
            errors,
        )
        missing = supporting - source_ids
        if missing:
            errors.append(f"Claim references missing sources: {claim_id}: {sorted(missing)}")
        if status in {"verified", "likely"} and not supporting:
            errors.append(f"Usable claim has no supporting source: {claim_id}")
        if status == "reaction_only" and claim.get("usable_in_narration") is True:
            errors.append(f"Reaction-only claim cannot be used in narration: {claim_id}")

    assets, asset_ids = collect_ids(asset_manifest.get("assets"), "assets", errors)
    asset_by_id = {clean_text(item.get("id")): item for item in assets}
    for asset in assets:
        asset_id = clean_text(asset.get("id"))
        linked_sources = string_ids(
            asset.get("source_ids", []), f"assets.{asset_id}.source_ids", errors
        )
        missing = linked_sources - source_ids
        if missing:
            errors.append(f"Asset references missing sources: {asset_id}: {sorted(missing)}")
        if not linked_sources:
            errors.append(f"Asset has no source IDs: {asset_id}")
        rights_status = clean_text(asset.get("rights_status") or "unreviewed")
        if rights_status not in RIGHTS_STATUSES:
            errors.append(f"Unsupported asset rights status: {asset_id}: {rights_status}")

    comments, comment_ids = collect_ids(comments_doc.get("comments"), "comments", errors)
    comment_by_id = {clean_text(item.get("id")): item for item in comments}
    for comment in comments:
        comment_id = clean_text(comment.get("id"))
        source_id = clean_text(comment.get("source_id"))
        if source_id not in source_ids:
            errors.append(f"Comment references missing source: {comment_id}: {source_id}")
        if clean_text(comment.get("claim_status") or "reaction_only") != "reaction_only":
            errors.append(f"Comments must remain reaction_only: {comment_id}")

    segments, segment_ids = collect_ids(
        story.get("narration_segments"), "narration_segments", errors
    )
    for segment in segments:
        segment_id = clean_text(segment.get("id"))
        if not clean_text(segment.get("text")):
            errors.append(f"Narration segment text is empty: {segment_id}")
        linked_claims = string_ids(
            segment.get("claim_ids", []),
            f"narration_segments.{segment_id}.claim_ids",
            errors,
        )
        if stage == "handoff" and not linked_claims:
            errors.append(f"Handoff narration segment has no claim IDs: {segment_id}")
        missing = linked_claims - claim_ids
        if missing:
            errors.append(
                f"Narration segment references missing claims: {segment_id}: {sorted(missing)}"
            )
        unusable = {
            claim_id
            for claim_id in linked_claims
            if claim_status_by_id.get(claim_id) not in {"verified", "likely"}
        }
        if unusable:
            errors.append(
                f"Narration segment uses unverified claims: {segment_id}: {sorted(unusable)}"
            )

    scenes, scene_ids = collect_ids(timeline.get("scenes"), "scenes", errors)
    del scene_ids
    used_asset_ids: set[str] = set()
    used_comment_ids: set[str] = set()
    for scene in scenes:
        scene_id = clean_text(scene.get("id"))
        scene_asset_ids: set[str] = set()
        scene_links: dict[str, set[str]] = {}
        duration_ms = scene.get("duration_ms")
        if isinstance(duration_ms, bool) or not isinstance(duration_ms, int) or duration_ms <= 0:
            errors.append(f"Scene duration_ms must be a positive integer: {scene_id}")
        for field, known in (
            ("narration_segment_ids", segment_ids),
            ("claim_ids", claim_ids),
            ("source_ids", source_ids),
            ("asset_ids", asset_ids),
            ("comment_ids", comment_ids),
        ):
            linked = string_ids(scene.get(field, []), f"scenes.{scene_id}.{field}", errors)
            missing = linked - known
            if missing:
                errors.append(f"Scene references missing {field}: {scene_id}: {sorted(missing)}")
            if field == "asset_ids":
                used_asset_ids.update(linked)
                scene_asset_ids.update(linked)
            elif field == "comment_ids":
                used_comment_ids.update(linked)
            scene_links[field] = linked
        if stage == "handoff" and not scene_asset_ids:
            errors.append(f"Handoff scene has no asset IDs: {scene_id}")
        if stage == "handoff":
            for field in ("narration_segment_ids", "claim_ids", "source_ids"):
                if not scene_links.get(field):
                    errors.append(f"Handoff scene has no {field}: {scene_id}")

    local_review_only = False
    for asset_id in used_asset_ids:
        asset = asset_by_id.get(asset_id, {})
        rights_status = clean_text(asset.get("rights_status") or "unreviewed")
        if rights_status == "not_permitted":
            errors.append(f"A not_permitted asset is used by the timeline: {asset_id}")
        if rights_status in LOCAL_REVIEW_RIGHTS:
            local_review_only = True
        if stage == "handoff" and not existing_relative_file(
            project_dir, asset.get("normalized_path") or asset.get("raw_path")
        ):
            errors.append(f"Used asset file is missing or unsafe: {asset_id}")
    for comment_id in used_comment_ids:
        comment = comment_by_id.get(comment_id, {})
        if stage == "handoff" and not existing_relative_file(
            project_dir, comment.get("production_path")
        ):
            errors.append(f"Used production comment capture is missing: {comment_id}")

    reviews = project.get("reviews")
    if not isinstance(reviews, dict):
        errors.append("project.reviews must be an object")
        reviews = {}
    for key in ("facts_reviewed", "rights_reviewed"):
        if key in reviews:
            try:
                require_bool(reviews[key], f"project.reviews.{key}")
            except PackageError as exc:
                errors.append(str(exc))
    if stage == "handoff":
        if not clean_text(story.get("one_line_payoff")):
            errors.append("Handoff requires story.one_line_payoff")
        if not segments:
            errors.append("Handoff requires narration segments")
        if not scenes:
            errors.append("Handoff requires timeline scenes")
        if not used_asset_ids:
            errors.append("Handoff requires at least one timeline asset")
        if not (project_dir / "subtitles.srt").read_text(encoding="utf-8").strip():
            errors.append("Handoff requires non-empty subtitles.srt")
        if reviews.get("facts_reviewed") is not True:
            errors.append("Handoff requires facts_reviewed=true")
        if reviews.get("rights_reviewed") is not True:
            errors.append("Handoff requires rights_reviewed=true")

    if not comments:
        warnings.append("No comments were captured; this is allowed when comments add no story value")
    if local_review_only:
        warnings.append("Used assets include review-only rights; publication remains blocked")
    valid = not errors
    return {
        "valid": valid,
        "stage": stage,
        "candidate_id": candidate_id,
        "research_ready": valid and bool(claims),
        "local_review_ready": valid and stage == "handoff",
        "render_handoff_ready": valid and stage == "handoff",
        "local_review_only": local_review_only,
        "publish_ready": False,
        "publish_blocked": True,
        "counts": {
            "sources": len(sources),
            "claims": len(claims),
            "assets": len(assets),
            "comments": len(comments),
            "narration_segments": len(segments),
            "scenes": len(scenes),
        },
        "errors": errors,
        "warnings": warnings,
    }


def command_validate(args: argparse.Namespace) -> int:
    project_dir = Path(args.project_dir).expanduser().resolve()
    payload = validate_package(project_dir, args.stage)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["valid"] else 2


def command_doctor(args: argparse.Namespace) -> int:
    payload = {
        "plugin": "shorts-suite:research-package",
        "version": PLUGIN_VERSION,
        "python": sys.version.split()[0],
        "standard_library_only": True,
        "database_required": False,
        "platform_credentials_required": False,
        "browser_collection": "agent_skill_only",
        "ready": sys.version_info >= (3, 10),
    }
    print(
        json.dumps(payload, ensure_ascii=False, indent=2)
        if args.json
        else "Shorts research packager is ready."
    )
    return 0 if payload["ready"] else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Initialize and validate a selected Shorts research package."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor = subparsers.add_parser("doctor", help="Report local requirements")
    doctor.add_argument("--json", action="store_true")
    doctor.set_defaults(func=command_doctor)

    init = subparsers.add_parser(
        "init", help="Create a renderer-neutral package from one selected candidate"
    )
    init.add_argument("--shortlist", required=True)
    init.add_argument("--candidate-id", required=True)
    init.add_argument("--project-dir", required=True)
    init.add_argument("--reference-channel", action="append", default=[])
    init.set_defaults(func=command_init)

    validate = subparsers.add_parser(
        "validate", help="Validate research or renderer-handoff readiness"
    )
    validate.add_argument("--project-dir", required=True)
    validate.add_argument("--stage", choices=("research", "handoff"), default="research")
    validate.set_defaults(func=command_validate)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        return args.func(args)
    except (PackageError, FileNotFoundError, json.JSONDecodeError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
