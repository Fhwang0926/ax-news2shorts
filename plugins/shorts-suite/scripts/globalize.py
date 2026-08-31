#!/usr/bin/env python3
"""Build source-backed English Shorts production drafts from Korean signal videos."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import html
import importlib.util
import json
import os
import re
import ssl
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import parse_qs, urlsplit, urlunsplit
from zoneinfo import ZoneInfo


def find_workspace_root(start: Path, plugin_root: Path) -> Path:
    resolved_start = start.resolve()
    for candidate in (resolved_start, *resolved_start.parents):
        if (candidate / ".agents" / "plugins" / "marketplace.json").is_file() and (
            candidate / "plugins" / "shorts-suite"
        ).is_dir():
            return candidate
    source_root = plugin_root.parents[1]
    if (source_root / ".agents" / "plugins" / "marketplace.json").is_file() and (
        source_root / "plugins" / "shorts-suite"
    ).resolve() == plugin_root:
        return source_root
    return resolved_start


VERSION = "0.1.0"
SCHEMA_VERSION = 1
PLUGIN_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = find_workspace_root(Path.cwd(), PLUGIN_ROOT)
DEFAULT_PROJECTS_ROOT = WORKSPACE_ROOT / "projects" / "shorts-suite" / "globalize"
TEMPLATE_ROOT = PLUGIN_ROOT / "skills" / "global-shorts-producer" / "templates"
SEOUL = ZoneInfo("Asia/Seoul")
BRAINBULB_CHANNEL = {
    "name": "뇌전구",
    "channel_id": "UCbr855WAFQvAX-An7IcHFXg",
    "shorts_url": "https://www.youtube.com/channel/UCbr855WAFQvAX-An7IcHFXg/shorts",
}
MAX_DISCOVERY_LIMIT = 10

PROJECT_STATUSES = {
    "initialized",
    "transcript_pending",
    "ingested",
    "researched",
    "scored",
    "review_required",
    "script_drafted",
    "script_approved",
    "packaged",
    "blocked",
}
ORIGINS = {
    "KR_ORIGINAL",
    "GLOBAL_ORIGINAL",
    "KPOP",
    "KOREAN_CULTURE",
    "GLOBAL_REPOST",
    "UNKNOWN",
}
SOURCE_TYPES = {"official", "primary", "independent"}
CLAIM_STATUSES = {"confirmed", "attributed", "disputed", "unknown"}
CLAIM_CONFIDENCE = {"high", "medium", "low"}
USABLE_CLAIM_STATUSES = {"confirmed", "attributed"}
ASSET_TYPES = {
    "NEWS_IMAGE",
    "PUBLIC_PHOTO",
    "SOCIAL_POST",
    "SCREENSHOT",
    "BROLL",
    "MAP",
    "INFOGRAPHIC",
    "AI_IMAGE",
    "TEXT_CARD",
}
ASSET_RIGHTS = {"GREEN", "YELLOW", "RED"}
SCENE_ROLES = {
    "hook",
    "context",
    "event",
    "evidence",
    "problem",
    "impact",
    "twist",
    "reaction",
    "payoff",
}
FEATURE_WEIGHTS = {
    "visual_impact": 20,
    "curiosity": 20,
    "universal_understanding": 15,
    "korea_uniqueness": 15,
    "emotion": 10,
    "surprise": 10,
    "freshness": 10,
}
PENALTIES = {
    "korean_person_only": 20,
    "domestic_politics_context": 30,
    "background_knowledge_required": 15,
    "already_global_viral": 40,
    "facts_unverifiable": 50,
}
SENSITIVE_REASONS = {
    "death",
    "accident",
    "crime",
    "named_criticism",
    "corporate_controversy",
    "politics",
    "medical",
}
PACKAGE_FILES = {
    "script_en.md",
    "narration.txt",
    "subtitles.srt",
    "highlights.json",
    "scenes.json",
    "assets.csv",
    "asset-search.md",
    "capcut-manifest.json",
}
MEDIA_SUFFIXES = {
    ".mp4",
    ".mov",
    ".mkv",
    ".webm",
    ".mp3",
    ".wav",
    ".m4a",
    ".aac",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".avif",
}


class GlobalizerError(ValueError):
    pass


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def clean_text(value: Any) -> str:
    return " ".join(str(value or "").split())


def require_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise GlobalizerError(f"{label} must be an object")
    return value


def require_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise GlobalizerError(f"{label} must be an array")
    return value


def require_text(value: Any, label: str, *, minimum: int = 1) -> str:
    text = clean_text(value)
    if len(text) < minimum:
        raise GlobalizerError(f"{label} must contain at least {minimum} character(s)")
    return text


def require_number(
    value: Any,
    label: str,
    *,
    minimum: float | None = None,
    maximum: float | None = None,
) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise GlobalizerError(f"{label} must be a number")
    number = float(value)
    if minimum is not None and number < minimum:
        raise GlobalizerError(f"{label} must be at least {minimum}")
    if maximum is not None and number > maximum:
        raise GlobalizerError(f"{label} must be at most {maximum}")
    return number


def require_http_url(value: Any, label: str) -> str:
    url = require_text(value, label, minimum=8)
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise GlobalizerError(f"{label} must be an absolute HTTP(S) URL")
    return url


def load_json(path: Path) -> dict[str, Any]:
    try:
        with path.open(encoding="utf-8") as handle:
            return require_object(json.load(handle), str(path))
    except FileNotFoundError as exc:
        raise GlobalizerError(f"Required file is missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise GlobalizerError(f"Invalid JSON: {path}: {exc}") from exc


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, delete=False
    ) as handle:
        handle.write(serialized)
        temp_path = Path(handle.name)
    temp_path.replace(path)


def print_json(payload: Any) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def ensure_schema(payload: dict[str, Any], label: str) -> None:
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise GlobalizerError(f"{label}.schema_version must be {SCHEMA_VERSION}")


def canonical_web_url(url: str) -> str:
    parsed = urlsplit(url)
    path = parsed.path.rstrip("/") or "/"
    return urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), path, "", ""))


def extract_video_id(url: str) -> str:
    value = require_http_url(url, "url")
    parsed = urlsplit(value)
    host = parsed.netloc.lower().split(":", 1)[0]
    if host.startswith("www."):
        host = host[4:]
    query = parse_qs(parsed.query)
    if "list" in query:
        raise GlobalizerError("Playlist URLs are not supported")
    video_id = ""
    parts = [part for part in parsed.path.split("/") if part]
    if host == "youtu.be" and len(parts) == 1:
        video_id = parts[0]
    elif host in {"youtube.com", "m.youtube.com"}:
        if len(parts) == 2 and parts[0] == "shorts":
            video_id = parts[1]
        elif parsed.path == "/watch":
            values = query.get("v", [])
            video_id = values[0] if len(values) == 1 else ""
    if not re.fullmatch(r"[0-9A-Za-z_-]{11}", video_id):
        raise GlobalizerError("A single YouTube Shorts video URL is required")
    return video_id


def canonical_shorts_url(video_id: str) -> str:
    if not re.fullmatch(r"[0-9A-Za-z_-]{11}", video_id):
        raise GlobalizerError("Invalid YouTube video ID")
    return f"https://www.youtube.com/shorts/{video_id}"


def project_destination(
    *,
    projects_root: Path,
    video_id: str,
    project_dir: str,
    allow_existing: bool = False,
) -> Path:
    root = projects_root.expanduser().resolve()
    candidate = (
        Path(project_dir).expanduser().resolve()
        if project_dir
        else root / dt.datetime.now(SEOUL).date().isoformat() / video_id
    )
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise GlobalizerError("Project directory must stay under the projects root") from exc
    if candidate.exists() and not allow_existing:
        raise GlobalizerError(f"Project directory already exists: {candidate}")
    return candidate


def yt_dlp_available() -> bool:
    return importlib.util.find_spec("yt_dlp") is not None


def certifi_ca_file() -> Path | None:
    if importlib.util.find_spec("certifi") is None:
        return None
    try:
        import certifi

        path = Path(certifi.where()).resolve()
    except (ImportError, OSError):
        return None
    return path if path.is_file() else None


def caption_tls_configuration() -> dict[str, Any]:
    paths = ssl.get_default_verify_paths()
    default_cafile = Path(paths.cafile).resolve() if paths.cafile else None
    default_capath = Path(paths.capath).resolve() if paths.capath else None
    if default_cafile and default_cafile.is_file():
        return {
            "available": True,
            "mode": "python-default",
            "cafile": str(default_cafile),
        }
    if default_capath and default_capath.is_dir():
        return {
            "available": True,
            "mode": "python-default-capath",
            "cafile": "",
        }
    fallback = certifi_ca_file()
    if fallback:
        return {
            "available": True,
            "mode": "certifi-fallback",
            "cafile": str(fallback),
        }
    return {
        "available": False,
        "mode": "unavailable",
        "cafile": "",
    }


def caption_ssl_context() -> ssl.SSLContext:
    configuration = caption_tls_configuration()
    if not configuration["available"]:
        raise GlobalizerError(
            "No trusted CA bundle is available for caption TLS verification; "
            "install Python certificates or set SSL_CERT_FILE"
        )
    try:
        if configuration["mode"] == "certifi-fallback":
            return ssl.create_default_context(cafile=configuration["cafile"])
        return ssl.create_default_context()
    except (OSError, ssl.SSLError) as exc:
        raise GlobalizerError(f"Caption TLS context setup failed: {exc}") from exc


def extract_youtube_metadata(url: str) -> dict[str, Any]:
    if not yt_dlp_available():
        raise GlobalizerError("The installed yt_dlp module is required")
    command = [
        sys.executable,
        "-m",
        "yt_dlp",
        "--ignore-config",
        "--no-playlist",
        "--skip-download",
        "--dump-single-json",
        "--no-warnings",
        url,
    ]
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise GlobalizerError(f"YouTube metadata collection failed: {exc}") from exc
    if result.returncode != 0:
        detail = clean_text(result.stderr) or "yt_dlp returned an error"
        raise GlobalizerError(f"YouTube metadata collection failed: {detail}")
    try:
        return require_object(json.loads(result.stdout), "yt_dlp metadata")
    except json.JSONDecodeError as exc:
        raise GlobalizerError("yt_dlp did not return valid metadata JSON") from exc


def discover_brainbulb_shorts(limit: int = 3) -> dict[str, Any]:
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= MAX_DISCOVERY_LIMIT:
        raise GlobalizerError(f"Discovery limit must be an integer from 1 to {MAX_DISCOVERY_LIMIT}")
    if not yt_dlp_available():
        raise GlobalizerError("The installed yt_dlp module is required")
    command = [
        sys.executable,
        "-m",
        "yt_dlp",
        "--ignore-config",
        "--flat-playlist",
        "--playlist-end",
        str(limit),
        "--skip-download",
        "--dump-json",
        "--no-warnings",
        BRAINBULB_CHANNEL["shorts_url"],
    ]
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise GlobalizerError(f"Brainbulb Shorts discovery failed: {exc}") from exc
    if result.returncode != 0:
        detail = clean_text(result.stderr) or "yt_dlp returned an error"
        raise GlobalizerError(f"Brainbulb Shorts discovery failed: {detail}")

    candidates: list[dict[str, Any]] = []
    for raw_line in result.stdout.splitlines():
        if not raw_line.strip():
            continue
        try:
            item = require_object(json.loads(raw_line), "yt_dlp Shorts entry")
        except json.JSONDecodeError as exc:
            raise GlobalizerError("yt_dlp returned invalid Shorts JSON") from exc
        channel_id = clean_text(item.get("playlist_channel_id") or item.get("playlist_id"))
        if channel_id != BRAINBULB_CHANNEL["channel_id"]:
            raise GlobalizerError("YouTube returned a Shorts entry from a different channel")
        video_id = clean_text(item.get("id"))
        if not re.fullmatch(r"[0-9A-Za-z_-]{11}", video_id):
            raise GlobalizerError("YouTube returned an invalid Shorts video ID")
        candidates.append(
            {
                "candidate_id": f"candidate-{len(candidates) + 1:02d}",
                "video_id": video_id,
                "title": clean_text(item.get("title")),
                "url": canonical_shorts_url(video_id),
                "views": item.get("view_count"),
                "channel": BRAINBULB_CHANNEL["name"],
                "channel_id": BRAINBULB_CHANNEL["channel_id"],
                "shorts_tab_index": item.get("playlist_index"),
            }
        )
    if not candidates:
        raise GlobalizerError("The Brainbulb Shorts tab returned no public candidates")
    return {
        "schema_version": SCHEMA_VERSION,
        "source": dict(BRAINBULB_CHANNEL),
        "retrieved_at": now_iso(),
        "selection_required": True,
        "monitoring_enabled": False,
        "candidates": candidates,
    }


def caption_language_priority(language: str) -> tuple[int, str]:
    lowered = language.lower()
    if lowered == "ko":
        return (0, lowered)
    if lowered in {"ko-kr", "ko_korean"}:
        return (1, lowered)
    if lowered.startswith("ko"):
        return (2, lowered)
    return (10, lowered)


def choose_caption_track(metadata: dict[str, Any]) -> dict[str, Any] | None:
    extension_rank = {"vtt": 0, "json3": 1, "srv3": 2, "ttml": 3}
    for field, kind in (("subtitles", "manual"), ("automatic_captions", "automatic")):
        groups = metadata.get(field)
        if not isinstance(groups, dict):
            continue
        korean_languages = sorted(
            (key for key in groups if caption_language_priority(str(key))[0] < 10),
            key=lambda key: caption_language_priority(str(key)),
        )
        for language in korean_languages:
            formats = groups.get(language)
            if not isinstance(formats, list):
                continue
            candidates = [
                item
                for item in formats
                if isinstance(item, dict)
                and item.get("url")
                and str(item.get("ext") or "").lower() in extension_rank
            ]
            candidates.sort(key=lambda item: extension_rank[str(item.get("ext")).lower()])
            if candidates:
                selected = dict(candidates[0])
                selected.update({"language": str(language), "kind": kind})
                return selected
    return None


def strip_caption_tags(value: str) -> str:
    text = re.sub(r"<[^>]+>", "", html.unescape(value))
    return clean_text(text.replace("\u200b", ""))


def caption_text_from_vtt(value: str) -> str:
    lines: list[str] = []
    skip_block = False
    for raw in value.replace("\ufeff", "").splitlines():
        line = raw.strip()
        if not line:
            skip_block = False
            continue
        if line.startswith(("WEBVTT", "Kind:", "Language:")):
            continue
        if line.startswith(("NOTE", "STYLE", "REGION")):
            skip_block = True
            continue
        if skip_block or "-->" in line or re.fullmatch(r"\d+", line):
            continue
        cleaned = strip_caption_tags(line)
        if cleaned and (not lines or cleaned != lines[-1]):
            lines.append(cleaned)
    return clean_text(" ".join(lines))


def caption_text_from_json3(value: str) -> str:
    try:
        payload = json.loads(value)
    except json.JSONDecodeError as exc:
        raise GlobalizerError("Caption JSON is invalid") from exc
    texts: list[str] = []
    for event in payload.get("events", []):
        if not isinstance(event, dict):
            continue
        text = "".join(
            str(segment.get("utf8") or "")
            for segment in event.get("segs", [])
            if isinstance(segment, dict)
        )
        cleaned = strip_caption_tags(text)
        if cleaned and (not texts or cleaned != texts[-1]):
            texts.append(cleaned)
    return clean_text(" ".join(texts))


def caption_text_from_ttml(value: str) -> str:
    try:
        root = ET.fromstring(value)
    except ET.ParseError as exc:
        raise GlobalizerError("Caption XML is invalid") from exc
    texts: list[str] = []
    for element in root.iter():
        if element.tag.rsplit("}", 1)[-1] != "p":
            continue
        cleaned = strip_caption_tags("".join(element.itertext()))
        if cleaned and (not texts or cleaned != texts[-1]):
            texts.append(cleaned)
    return clean_text(" ".join(texts))


def fetch_caption(track: dict[str, Any]) -> str:
    url = require_http_url(track.get("url"), "caption URL")
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    context = caption_ssl_context()
    try:
        with urllib.request.urlopen(request, timeout=30, context=context) as response:
            data = response.read(5 * 1024 * 1024 + 1)
    except (OSError, urllib.error.URLError) as exc:
        raise GlobalizerError(f"Caption download failed: {exc}") from exc
    if len(data) > 5 * 1024 * 1024:
        raise GlobalizerError("Caption response is unexpectedly large")
    value = data.decode("utf-8", errors="replace")
    extension = str(track.get("ext") or "").lower()
    if extension == "json3":
        transcript = caption_text_from_json3(value)
    elif extension in {"srv3", "ttml"}:
        transcript = caption_text_from_ttml(value)
    else:
        transcript = caption_text_from_vtt(value)
    if not transcript:
        raise GlobalizerError("The selected caption track contained no readable text")
    return transcript


def read_transcript_file(path_value: str) -> str:
    path = Path(path_value).expanduser().resolve()
    if not path.is_file():
        raise GlobalizerError(f"Transcript file does not exist: {path}")
    if path.stat().st_size > 2 * 1024 * 1024:
        raise GlobalizerError("Transcript file must be 2 MiB or smaller")
    transcript = clean_text(path.read_text(encoding="utf-8"))
    if len(transcript) < 20:
        raise GlobalizerError("Transcript file does not contain enough text")
    return transcript


def published_at(metadata: dict[str, Any]) -> str:
    timestamp = metadata.get("timestamp") or metadata.get("release_timestamp")
    if isinstance(timestamp, (int, float)):
        return dt.datetime.fromtimestamp(timestamp, tz=dt.timezone.utc).isoformat()
    upload_date = clean_text(metadata.get("upload_date") or metadata.get("release_date"))
    if re.fullmatch(r"\d{8}", upload_date):
        parsed = dt.datetime.strptime(upload_date, "%Y%m%d").replace(tzinfo=dt.timezone.utc)
        return parsed.isoformat()
    return ""


def load_template(name: str) -> dict[str, Any]:
    return load_json(TEMPLATE_ROOT / name)


def resume_pending_project(
    *,
    destination: Path,
    video_id: str,
    canonical_url: str,
    metadata: dict[str, Any],
    transcript: str,
    transcript_source: dict[str, Any],
) -> dict[str, Any]:
    project, source = load_project(destination)
    if project.get("status") != "transcript_pending":
        raise GlobalizerError(f"Project directory already exists: {destination}")
    if project.get("id") != video_id or source.get("video_id") != video_id:
        raise GlobalizerError("Existing pending project belongs to a different video")
    if project.get("source_url") != canonical_url or source.get("url") != canonical_url:
        raise GlobalizerError("Existing pending project URL does not match the requested Short")
    approvals = require_object(project.get("approvals"), "project.approvals")
    if any(
        approvals.get(stage, {}).get("approved") is True
        for stage in ("research", "script", "preview")
    ):
        raise GlobalizerError("An approved project cannot be resumed as transcript_pending")
    transcript_path = destination / "transcript.txt"
    if not transcript_path.is_file() or clean_text(transcript_path.read_text(encoding="utf-8")):
        raise GlobalizerError("Pending resume requires an existing empty transcript.txt")
    if not transcript:
        raise GlobalizerError(
            "The existing project is still transcript_pending; provide an authorized transcript "
            "or restore trusted CA certificates"
        )
    timestamp = now_iso()
    project["plugin_version"] = VERSION
    project["status"] = "ingested"
    project["updated_at"] = timestamp
    project["publish_blocked"] = True
    source.update(
        {
            "channel": clean_text(metadata.get("channel") or metadata.get("uploader")),
            "channel_id": clean_text(metadata.get("channel_id") or metadata.get("uploader_id")),
            "title": clean_text(metadata.get("title")),
            "published_at": published_at(metadata),
            "duration_seconds": metadata.get("duration"),
            "description": clean_text(metadata.get("description")),
            "metrics": {
                "views": metadata.get("view_count"),
                "likes": metadata.get("like_count"),
                "comments": metadata.get("comment_count"),
            },
            "captured_at": timestamp,
            "transcript": transcript_source,
            "caption_error": "",
            "video_downloaded": False,
        }
    )
    analysis = load_json(destination / "source-analysis.json")
    ensure_schema(analysis, "source-analysis.json")
    analysis["transcript_available"] = True
    analysis["updated_at"] = timestamp
    transcript_path.write_text(transcript + "\n", encoding="utf-8")
    write_json(destination / "project.json", project)
    write_json(destination / "source.json", source)
    write_json(destination / "source-analysis.json", analysis)
    return {
        "status": "ingested",
        "project_dir": str(destination),
        "video_id": video_id,
        "transcript_source": transcript_source["kind"],
        "caption_error": "",
        "resumed": True,
    }


def initialize_project(args: argparse.Namespace) -> dict[str, Any]:
    video_id = extract_video_id(args.url)
    canonical_url = canonical_shorts_url(video_id)
    metadata = extract_youtube_metadata(canonical_url)
    metadata_id = clean_text(metadata.get("id"))
    if metadata_id and metadata_id != video_id:
        raise GlobalizerError("YouTube metadata resolved to a different video")
    if metadata.get("playlist_count") not in {None, 0, 1}:
        raise GlobalizerError("Playlist inputs are not supported")

    transcript = ""
    transcript_source: dict[str, Any]
    caption_error = ""
    if args.transcript_file:
        transcript = read_transcript_file(args.transcript_file)
        transcript_source = {
            "kind": "user_provided",
            "language": "ko",
            "source_path": str(Path(args.transcript_file).expanduser().resolve()),
            "authorization_basis": "user_supplied_cli_file",
        }
    else:
        track = choose_caption_track(metadata)
        if track is None:
            transcript_source = {"kind": "unavailable", "language": "", "source_path": ""}
        else:
            try:
                transcript = fetch_caption(track)
                transcript_source = {
                    "kind": track["kind"],
                    "language": track["language"],
                    "format": track["ext"],
                    "source_path": "",
                }
            except GlobalizerError as exc:
                caption_error = str(exc)
                transcript_source = {
                    "kind": "unavailable",
                    "language": str(track.get("language") or ""),
                    "source_path": "",
                }

    projects_root = Path(args.projects_root).expanduser().resolve()
    destination = project_destination(
        projects_root=projects_root,
        video_id=video_id,
        project_dir=args.project_dir,
        allow_existing=True,
    )
    if destination.exists():
        return resume_pending_project(
            destination=destination,
            video_id=video_id,
            canonical_url=canonical_url,
            metadata=metadata,
            transcript=transcript,
            transcript_source=transcript_source,
        )
    destination.mkdir(parents=True)
    timestamp = now_iso()
    status = "ingested" if transcript else "transcript_pending"
    project = {
        "schema_version": SCHEMA_VERSION,
        "plugin": "shorts-suite:globalize",
        "plugin_version": VERSION,
        "id": video_id,
        "status": status,
        "created_at": timestamp,
        "updated_at": timestamp,
        "locale": "en-US",
        "source_url": canonical_url,
        "approvals": {
            "topic": {"approved": True, "approved_at": timestamp, "basis": "direct_url"},
            "research": {"approved": False, "approved_at": None},
            "script": {"approved": False, "approved_at": None},
            "preview": {"approved": False, "approved_at": None},
        },
        "publish_blocked": True,
    }
    source = {
        "schema_version": SCHEMA_VERSION,
        "video_id": video_id,
        "url": canonical_url,
        "channel": clean_text(metadata.get("channel") or metadata.get("uploader")),
        "channel_id": clean_text(metadata.get("channel_id") or metadata.get("uploader_id")),
        "title": clean_text(metadata.get("title")),
        "published_at": published_at(metadata),
        "duration_seconds": metadata.get("duration"),
        "description": clean_text(metadata.get("description")),
        "metrics": {
            "views": metadata.get("view_count"),
            "likes": metadata.get("like_count"),
            "comments": metadata.get("comment_count"),
        },
        "captured_at": timestamp,
        "transcript": transcript_source,
        "caption_error": caption_error,
        "role": "signal_only_not_fact_source",
        "video_downloaded": False,
    }
    analysis = load_template("source-analysis.template.json")
    analysis["video_id"] = video_id
    analysis["source_url"] = canonical_url
    analysis["transcript_available"] = bool(transcript)
    analysis["updated_at"] = timestamp
    sources = {"schema_version": SCHEMA_VERSION, "sources": []}
    facts = {
        "schema_version": SCHEMA_VERSION,
        "sensitive_topic": False,
        "claims": [],
    }
    content = load_template("content-en.template.json")
    storyboard = load_template("storyboard.template.json")
    originality = load_template("originality.template.json")

    write_json(destination / "project.json", project)
    write_json(destination / "source.json", source)
    (destination / "transcript.txt").write_text(transcript + ("\n" if transcript else ""), encoding="utf-8")
    write_json(destination / "source-analysis.json", analysis)
    write_json(destination / "sources.json", sources)
    write_json(destination / "fact-sheet.json", facts)
    write_json(destination / "content-en.json", content)
    write_json(destination / "storyboard.json", storyboard)
    write_json(destination / "originality.json", originality)
    return {
        "status": status,
        "project_dir": str(destination),
        "video_id": video_id,
        "transcript_source": transcript_source["kind"],
        "caption_error": caption_error,
        "resumed": False,
    }


def load_project(project_dir: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    project = load_json(project_dir / "project.json")
    source = load_json(project_dir / "source.json")
    ensure_schema(project, "project.json")
    ensure_schema(source, "source.json")
    if project.get("plugin") not in {"shorts-suite:globalize", "shorts-globalizer"}:
        raise GlobalizerError("This is not a Shorts Suite globalize project")
    if project.get("status") not in PROJECT_STATUSES:
        raise GlobalizerError(f"Unsupported project status: {project.get('status')}")
    return project, source


def append_error(errors: list[str], function: Any) -> Any:
    try:
        return function()
    except GlobalizerError as exc:
        errors.append(str(exc))
        return None


def validate_ingest(project_dir: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    project, source = load_project(project_dir)
    video_id = append_error(errors, lambda: extract_video_id(source.get("url")))
    if video_id and video_id != source.get("video_id"):
        errors.append("source.json video_id does not match its URL")
    if source.get("role") != "signal_only_not_fact_source":
        errors.append("The source Short must remain signal_only_not_fact_source")
    if source.get("video_downloaded") is not False:
        errors.append("v0.1 must not download the source video")
    transcript_path = project_dir / "transcript.txt"
    if not transcript_path.is_file():
        errors.append("transcript.txt is missing")
    else:
        transcript = clean_text(transcript_path.read_text(encoding="utf-8"))
        if not transcript:
            errors.append("Transcript is pending; provide an authorized transcript file")
        elif len(transcript) < 20:
            errors.append("Transcript is too short for analysis")
    if project.get("publish_blocked") is not True:
        errors.append("v0.1 projects must remain publish_blocked")
    preview = require_object(project.get("approvals", {}).get("preview"), "approvals.preview")
    if preview.get("approved") is not False:
        errors.append("v0.1 cannot approve a preview because it does not render one")
    return errors, warnings


def source_domain(url: str) -> str:
    host = urlsplit(url).netloc.lower().split(":", 1)[0]
    return host.removeprefix("www.")


def validate_research(project_dir: Path) -> tuple[list[str], list[str]]:
    errors, warnings = validate_ingest(project_dir)
    _project, signal = load_project(project_dir)
    analysis = load_json(project_dir / "source-analysis.json")
    sources_payload = load_json(project_dir / "sources.json")
    facts = load_json(project_dir / "fact-sheet.json")
    for label, payload in (
        ("source-analysis.json", analysis),
        ("sources.json", sources_payload),
        ("fact-sheet.json", facts),
    ):
        append_error(errors, lambda payload=payload, label=label: ensure_schema(payload, label))

    topic = require_object(analysis.get("topic"), "source-analysis.topic")
    for field in ("summary", "who", "event", "cause", "result", "controversy", "viral_reason"):
        if not clean_text(topic.get(field)):
            errors.append(f"source-analysis.topic.{field} is required")
    origin = clean_text(topic.get("origin"))
    if origin not in ORIGINS:
        errors.append(f"Unsupported source origin: {origin or 'empty'}")
    structure = require_object(analysis.get("structure"), "source-analysis.structure")
    for field in ("hook", "context", "problem", "twist", "reaction", "ending"):
        if not clean_text(structure.get(field)):
            errors.append(f"source-analysis.structure.{field} is required")

    sensitive = analysis.get("sensitive_topic")
    if not isinstance(sensitive, bool):
        errors.append("source-analysis.sensitive_topic must be true or false")
        sensitive = False
    reasons = analysis.get("sensitive_reasons", [])
    if not isinstance(reasons, list):
        errors.append("source-analysis.sensitive_reasons must be an array")
        reasons = []
    invalid_reasons = sorted({clean_text(value) for value in reasons} - SENSITIVE_REASONS)
    if invalid_reasons:
        errors.append(f"Unsupported sensitive reasons: {invalid_reasons}")
    if sensitive and not reasons:
        errors.append("Sensitive topics must record at least one sensitive reason")
    if facts.get("sensitive_topic") is not sensitive:
        errors.append("fact-sheet sensitive_topic must match source-analysis")

    source_items = sources_payload.get("sources")
    if not isinstance(source_items, list):
        errors.append("sources.json sources must be an array")
        source_items = []
    source_by_id: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(source_items):
        if not isinstance(raw, dict):
            errors.append(f"sources[{index}] must be an object")
            continue
        source_id = clean_text(raw.get("id"))
        if not re.fullmatch(r"source-[0-9]{2}", source_id):
            errors.append(f"Invalid source ID: {source_id or 'empty'}")
            continue
        if source_id in source_by_id:
            errors.append(f"Duplicate source ID: {source_id}")
            continue
        source_type = clean_text(raw.get("source_type"))
        if source_type not in SOURCE_TYPES:
            errors.append(f"Unsupported source type for {source_id}: {source_type}")
        try:
            url = require_http_url(raw.get("url"), f"{source_id}.url")
            if canonical_web_url(url) == canonical_web_url(str(signal.get("url") or "")):
                errors.append("The signal Short cannot be reused as a fact source")
            try:
                linked_video_id = extract_video_id(url)
            except GlobalizerError:
                linked_video_id = ""
            if linked_video_id and linked_video_id == signal.get("video_id"):
                errors.append("The signal Short cannot be reused through an alternate YouTube URL")
        except GlobalizerError as exc:
            errors.append(str(exc))
            url = ""
        if not clean_text(raw.get("publisher")):
            errors.append(f"{source_id}.publisher is required")
        if not clean_text(raw.get("title")):
            errors.append(f"{source_id}.title is required")
        if not clean_text(raw.get("published_at")):
            errors.append(f"{source_id}.published_at is required")
        source_by_id[source_id] = {**raw, "url": url}

    domains = {source_domain(item["url"]) for item in source_by_id.values() if item.get("url")}
    required_domains = 3 if sensitive else 2
    if len(domains) < required_domains:
        errors.append(f"Not enough independent source domains: {len(domains)}/{required_domains}")
    if sensitive and not any(
        clean_text(item.get("source_type")) in {"official", "primary"}
        for item in source_by_id.values()
    ):
        errors.append("Sensitive topics require an official or primary source")
    if sensitive:
        independent_domains = {
            source_domain(item["url"])
            for item in source_by_id.values()
            if item.get("url") and clean_text(item.get("source_type")) == "independent"
        }
        if len(independent_domains) < 2:
            errors.append("Sensitive topics require two independent source domains")

    claim_items = facts.get("claims")
    if not isinstance(claim_items, list):
        errors.append("fact-sheet claims must be an array")
        claim_items = []
    claim_by_id: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(claim_items):
        if not isinstance(raw, dict):
            errors.append(f"claims[{index}] must be an object")
            continue
        claim_id = clean_text(raw.get("id"))
        if not re.fullmatch(r"claim-[0-9]{2}", claim_id):
            errors.append(f"Invalid claim ID: {claim_id or 'empty'}")
            continue
        if claim_id in claim_by_id:
            errors.append(f"Duplicate claim ID: {claim_id}")
            continue
        if not clean_text(raw.get("statement")):
            errors.append(f"{claim_id}.statement is required")
        status = clean_text(raw.get("status"))
        if status not in CLAIM_STATUSES:
            errors.append(f"Unsupported claim status for {claim_id}: {status}")
        confidence = clean_text(raw.get("confidence"))
        if confidence not in CLAIM_CONFIDENCE:
            errors.append(f"Unsupported claim confidence for {claim_id}: {confidence}")
        source_ids = raw.get("source_ids")
        if not isinstance(source_ids, list) or not source_ids:
            errors.append(f"{claim_id}.source_ids must contain at least one source")
            source_ids = []
        missing = {clean_text(value) for value in source_ids} - set(source_by_id)
        if missing:
            errors.append(f"{claim_id} references missing sources: {sorted(missing)}")
        if raw.get("core") is True:
            claim_domains = {
                source_domain(source_by_id[source_id]["url"])
                for source_id in source_ids
                if source_id in source_by_id and source_by_id[source_id].get("url")
            }
            needed = 3 if sensitive else 2
            if len(claim_domains) < needed:
                errors.append(f"Core {claim_id} needs {needed} independent source domains")
            if sensitive and not any(
                clean_text(source_by_id[source_id].get("source_type")) in {"official", "primary"}
                for source_id in source_ids
                if source_id in source_by_id
            ):
                errors.append(f"Sensitive core {claim_id} needs an official or primary source")
            if sensitive:
                independent_claim_domains = {
                    source_domain(source_by_id[source_id]["url"])
                    for source_id in source_ids
                    if source_id in source_by_id
                    and source_by_id[source_id].get("url")
                    and clean_text(source_by_id[source_id].get("source_type")) == "independent"
                }
                if len(independent_claim_domains) < 2:
                    errors.append(
                        f"Sensitive core {claim_id} needs two independent source domains"
                    )
        claim_by_id[claim_id] = raw
    if not claim_by_id:
        errors.append("At least one fact claim is required")
    if claim_by_id and not any(item.get("core") is True for item in claim_by_id.values()):
        errors.append("At least one core claim is required")

    claim_order = analysis.get("source_claim_order")
    if not isinstance(claim_order, list) or not claim_order:
        errors.append("source_claim_order must contain the source information order")
        claim_order = []
    missing_order = {clean_text(value) for value in claim_order} - set(claim_by_id)
    if missing_order:
        errors.append(f"source_claim_order references missing claims: {sorted(missing_order)}")
    beat_order = analysis.get("source_beat_order")
    if not isinstance(beat_order, list) or len(beat_order) < 3:
        errors.append("source_beat_order must contain at least three functional beats")

    score_input = analysis.get("global_score_input")
    if not isinstance(score_input, dict):
        errors.append("global_score_input is required")
    else:
        features = score_input.get("features")
        penalties = score_input.get("penalties")
        if not isinstance(features, dict):
            errors.append("global_score_input.features must be an object")
            features = {}
        if not isinstance(penalties, dict):
            errors.append("global_score_input.penalties must be an object")
            penalties = {}
        for key in FEATURE_WEIGHTS:
            item = features.get(key)
            if not isinstance(item, dict):
                errors.append(f"Missing score feature: {key}")
                continue
            try:
                require_number(item.get("score"), f"features.{key}.score", minimum=0, maximum=100)
            except GlobalizerError as exc:
                errors.append(str(exc))
            if len(clean_text(item.get("reason"))) < 10:
                errors.append(f"features.{key}.reason must explain the score")
        for key in PENALTIES:
            item = penalties.get(key)
            if not isinstance(item, dict):
                errors.append(f"Missing penalty field: {key}")
                continue
            if not isinstance(item.get("applied"), bool):
                errors.append(f"penalties.{key}.applied must be true or false")
            if item.get("applied") and len(clean_text(item.get("reason"))) < 10:
                errors.append(f"penalties.{key}.reason must explain the penalty")
    return errors, warnings


def decision_for(score: float) -> str:
    if score >= 80:
        return "MAKE"
    if score >= 65:
        return "REVIEW"
    if score >= 50:
        return "HOLD"
    return "SKIP"


def compute_global_score(analysis: dict[str, Any]) -> dict[str, Any]:
    topic = require_object(analysis.get("topic"), "source-analysis.topic")
    origin = require_text(topic.get("origin"), "source-analysis.topic.origin")
    score_input = require_object(analysis.get("global_score_input"), "global_score_input")
    features = require_object(score_input.get("features"), "global_score_input.features")
    penalties = require_object(score_input.get("penalties"), "global_score_input.penalties")
    components: dict[str, Any] = {}
    weighted_total = 0.0
    for key, weight in FEATURE_WEIGHTS.items():
        item = require_object(features.get(key), f"features.{key}")
        score = require_number(item.get("score"), f"features.{key}.score", minimum=0, maximum=100)
        weighted = score * weight / 100
        weighted_total += weighted
        components[key] = {
            "score": score,
            "weight": weight,
            "weighted": round(weighted, 2),
            "reason": clean_text(item.get("reason")),
        }
    applied_penalties: dict[str, Any] = {}
    penalty_total = 0
    for key, value in PENALTIES.items():
        item = require_object(penalties.get(key), f"penalties.{key}")
        if item.get("applied") is True:
            penalty_total += value
            applied_penalties[key] = {
                "points": value,
                "reason": clean_text(item.get("reason")),
            }
    score = round(max(0.0, min(100.0, weighted_total - penalty_total)), 1)
    decision = decision_for(score)
    forced_reason = ""
    if origin == "GLOBAL_REPOST":
        decision = "SKIP"
        forced_reason = "GLOBAL_REPOST is always skipped"
    elif origin == "UNKNOWN" and decision == "MAKE":
        decision = "REVIEW"
        forced_reason = "UNKNOWN origin cannot exceed REVIEW"
    return {
        "schema_version": SCHEMA_VERSION,
        "scored_at": now_iso(),
        "origin": origin,
        "components": components,
        "weighted_total": round(weighted_total, 2),
        "penalties": applied_penalties,
        "penalty_total": penalty_total,
        "total": score,
        "decision": decision,
        "forced_reason": forced_reason,
        "publication_ready": False,
    }


def score_project(project_dir: Path) -> dict[str, Any]:
    errors, _warnings = validate_research(project_dir)
    if errors:
        raise GlobalizerError("Research validation failed:\n- " + "\n- ".join(errors))
    project, _source = load_project(project_dir)
    analysis = load_json(project_dir / "source-analysis.json")
    score = compute_global_score(analysis)
    write_json(project_dir / "global-score.json", score)
    project["updated_at"] = now_iso()
    if score["decision"] == "SKIP":
        project["status"] = "blocked"
    elif score["decision"] in {"REVIEW", "HOLD"} or analysis.get("sensitive_topic") is True:
        project["status"] = "review_required"
    else:
        project["status"] = "scored"
    write_json(project_dir / "project.json", project)
    return score


def ordered_unique(values: Iterable[Any]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = clean_text(value)
        if text and text not in seen:
            result.append(text)
            seen.add(text)
    return result


def lcs_length(first: list[str], second: list[str]) -> int:
    if not first or not second:
        return 0
    previous = [0] * (len(second) + 1)
    for left in first:
        current = [0]
        for index, right in enumerate(second, start=1):
            if left == right:
                current.append(previous[index - 1] + 1)
            else:
                current.append(max(previous[index], current[-1]))
        previous = current
    return previous[-1]


def structure_similarity(first: list[str], second: list[str]) -> float:
    denominator = max(len(first), len(second))
    if denominator == 0:
        return 0.0
    return round(lcs_length(first, second) / denominator * 100, 1)


def english_word_count(value: str) -> int:
    return len(re.findall(r"[A-Za-z0-9]+(?:['’-][A-Za-z0-9]+)*", value))


def validate_claim_references(
    values: Any,
    *,
    label: str,
    claims: dict[str, dict[str, Any]],
    errors: list[str],
) -> list[str]:
    if not isinstance(values, list) or not values:
        errors.append(f"{label} must contain at least one claim ID")
        return []
    normalized = ordered_unique(values)
    missing = set(normalized) - set(claims)
    if missing:
        errors.append(f"{label} references missing claims: {sorted(missing)}")
    unusable = [
        claim_id
        for claim_id in normalized
        if claim_id in claims and clean_text(claims[claim_id].get("status")) not in USABLE_CLAIM_STATUSES
    ]
    if unusable:
        errors.append(f"{label} uses disputed or unknown claims: {unusable}")
    return normalized


def validate_script(project_dir: Path) -> tuple[list[str], list[str]]:
    errors, warnings = validate_research(project_dir)
    project, _source = load_project(project_dir)
    try:
        score = load_json(project_dir / "global-score.json")
        ensure_schema(score, "global-score.json")
    except GlobalizerError as exc:
        errors.append(str(exc))
        score = {}
    analysis = load_json(project_dir / "source-analysis.json")
    facts = load_json(project_dir / "fact-sheet.json")
    content = load_json(project_dir / "content-en.json")
    storyboard = load_json(project_dir / "storyboard.json")
    originality = load_json(project_dir / "originality.json")
    for label, payload in (
        ("content-en.json", content),
        ("storyboard.json", storyboard),
        ("originality.json", originality),
    ):
        append_error(errors, lambda payload=payload, label=label: ensure_schema(payload, label))

    decision = clean_text(score.get("decision"))
    if decision == "SKIP":
        errors.append("SKIP projects cannot create an English script")
    research_approved = bool(project.get("approvals", {}).get("research", {}).get("approved"))
    if decision in {"REVIEW", "HOLD"} or analysis.get("sensitive_topic") is True:
        if not research_approved:
            errors.append("Research approval is required before drafting this script")

    claims = {
        clean_text(item.get("id")): item
        for item in facts.get("claims", [])
        if isinstance(item, dict) and clean_text(item.get("id"))
    }
    if content.get("locale") != "en-US":
        errors.append("content-en locale must be en-US")
    angles = content.get("angles")
    if not isinstance(angles, list) or len(angles) != 3:
        errors.append("content-en must contain exactly three angles")
        angles = []
    angle_ids = set()
    for index, item in enumerate(angles):
        if not isinstance(item, dict):
            errors.append(f"angles[{index}] must be an object")
            continue
        angle_id = clean_text(item.get("id"))
        if not angle_id or angle_id in angle_ids:
            errors.append(f"angles[{index}].id must be unique")
        angle_ids.add(angle_id)
        if not clean_text(item.get("angle")) or len(clean_text(item.get("rationale"))) < 10:
            errors.append(f"angles[{index}] needs an angle and rationale")
    if clean_text(content.get("selected_angle_id")) not in angle_ids:
        errors.append("selected_angle_id must reference one of the three angles")

    titles = content.get("titles")
    if not isinstance(titles, list) or len(titles) != 5 or len(set(map(clean_text, titles))) != 5:
        errors.append("content-en must contain exactly five unique titles")
        titles = []
    selected_title = clean_text(content.get("selected_title"))
    if selected_title not in {clean_text(item) for item in titles}:
        errors.append("selected_title must be one of the five titles")
    title_lines = content.get("title_lines")
    if not isinstance(title_lines, list) or len(title_lines) != 2 or not all(clean_text(item) for item in title_lines):
        errors.append("title_lines must contain two non-empty display lines")

    hooks = content.get("hooks")
    if not isinstance(hooks, list) or len(hooks) != 3:
        errors.append("content-en must contain exactly three hooks")
        hooks = []
    hook_ids = set()
    for index, item in enumerate(hooks):
        if not isinstance(item, dict):
            errors.append(f"hooks[{index}] must be an object")
            continue
        hook_id = clean_text(item.get("id"))
        hook_ids.add(hook_id)
        if not hook_id or not clean_text(item.get("text")) or len(clean_text(item.get("rationale"))) < 10:
            errors.append(f"hooks[{index}] needs a unique id, text, and rationale")
    if len(hook_ids) != len(hooks):
        errors.append("Hook IDs must be unique")
    if clean_text(content.get("selected_hook_id")) not in hook_ids:
        errors.append("selected_hook_id must reference one of the three hooks")
    selection_reasons = content.get("selection_reasons")
    if not isinstance(selection_reasons, dict):
        errors.append("selection_reasons must contain angle, title, and hook reasons")
        selection_reasons = {}
    for field in ("angle", "title", "hook"):
        if len(clean_text(selection_reasons.get(field))) < 10:
            errors.append(f"selection_reasons.{field} must explain the selection")

    paragraphs = content.get("script_paragraphs")
    if not isinstance(paragraphs, list) or not paragraphs:
        errors.append("script_paragraphs must be a non-empty array")
        paragraphs = []
    paragraph_texts: list[str] = []
    output_claim_order: list[str] = []
    paragraph_ids: set[str] = set()
    for index, item in enumerate(paragraphs):
        if not isinstance(item, dict):
            errors.append(f"script_paragraphs[{index}] must be an object")
            continue
        paragraph_id = clean_text(item.get("id"))
        if not paragraph_id or paragraph_id in paragraph_ids:
            errors.append(f"script_paragraphs[{index}].id must be unique")
        paragraph_ids.add(paragraph_id)
        text = clean_text(item.get("text"))
        if not text:
            errors.append(f"script_paragraphs[{index}].text is required")
        paragraph_texts.append(text)
        output_claim_order.extend(
            validate_claim_references(
                item.get("claim_ids"),
                label=f"script_paragraphs[{index}].claim_ids",
                claims=claims,
                errors=errors,
            )
        )
    script_text = clean_text(content.get("script_text"))
    if script_text != clean_text(" ".join(paragraph_texts)):
        errors.append("script_text must equal the ordered script paragraphs")
    word_count = english_word_count(script_text)
    if not 80 <= word_count <= 120:
        errors.append(f"English script must contain 80-120 words; found {word_count}")

    scenes = storyboard.get("scenes")
    if not isinstance(scenes, list) or not 8 <= len(scenes) <= 10:
        errors.append("storyboard must contain 8-10 scenes")
        scenes = []
    scene_narration: list[str] = []
    scene_claim_order: list[str] = []
    output_beat_order: list[str] = []
    total_duration = 0.0
    for index, item in enumerate(scenes, start=1):
        if not isinstance(item, dict):
            errors.append(f"scenes[{index - 1}] must be an object")
            continue
        expected_id = f"scene-{index:02d}"
        if item.get("id") != expected_id:
            errors.append(f"Expected scene id {expected_id}")
        role = clean_text(item.get("role"))
        if role not in SCENE_ROLES:
            errors.append(f"Unsupported scene role for {expected_id}: {role}")
        output_beat_order.append(role)
        try:
            duration = require_number(
                item.get("duration_seconds"),
                f"{expected_id}.duration_seconds",
                minimum=0.5,
                maximum=8.0,
            )
            total_duration += duration
        except GlobalizerError as exc:
            errors.append(str(exc))
        narration = clean_text(item.get("narration"))
        caption = clean_text(item.get("caption"))
        highlight = clean_text(item.get("highlight"))
        if not narration or not caption or not highlight:
            errors.append(f"{expected_id} needs narration, caption, and highlight")
        scene_narration.append(narration)
        scene_claim_order.extend(
            validate_claim_references(
                item.get("claim_ids"),
                label=f"{expected_id}.claim_ids",
                claims=claims,
                errors=errors,
            )
        )
        asset = item.get("asset")
        if not isinstance(asset, dict):
            errors.append(f"{expected_id}.asset must be an object")
            continue
        if clean_text(asset.get("type")) not in ASSET_TYPES:
            errors.append(f"Unsupported asset type for {expected_id}")
        if not clean_text(asset.get("preferred_source")):
            errors.append(f"{expected_id}.asset.preferred_source is required")
        queries = asset.get("search_queries")
        if not isinstance(queries, list) or not queries or not all(clean_text(item) for item in queries):
            errors.append(f"{expected_id}.asset.search_queries must not be empty")
        if clean_text(asset.get("rights_status")) not in ASSET_RIGHTS:
            errors.append(f"Unsupported asset rights status for {expected_id}")
        if asset.get("status") != "planned":
            errors.append(f"{expected_id}.asset.status must remain planned in v0.1")
        if asset.get("asset_path") not in {None, ""}:
            errors.append(f"{expected_id}.asset_path must be empty in v0.1")
    if not 30.0 <= total_duration <= 40.0:
        errors.append(f"Storyboard duration must be 30-40 seconds; found {total_duration:.3f}")
    if clean_text(" ".join(scene_narration)) != script_text:
        errors.append("Scene narration must equal the English script")
    if ordered_unique(scene_claim_order) != ordered_unique(output_claim_order):
        warnings.append("Scene claim order differs from the paragraph claim order")

    source_claim_order = ordered_unique(analysis.get("source_claim_order", []))
    output_claim_order = ordered_unique(output_claim_order)
    source_beat_order = [
        clean_text(value) for value in analysis.get("source_beat_order", []) if clean_text(value)
    ]
    claim_similarity = structure_similarity(source_claim_order, output_claim_order)
    beat_similarity = structure_similarity(source_beat_order, output_beat_order)
    computed_similarity = max(claim_similarity, beat_similarity)
    if originality.get("lexical_check", {}).get("status") != "not_applicable_cross_language":
        errors.append("Cross-language lexical_check must be not_applicable_cross_language")
    if originality.get("source_claim_order") != source_claim_order:
        errors.append("originality source_claim_order does not match source analysis")
    if originality.get("output_claim_order") != output_claim_order:
        errors.append("originality output_claim_order does not match the English script")
    if originality.get("source_beat_order") != source_beat_order:
        errors.append("originality source_beat_order does not match source analysis")
    if originality.get("output_beat_order") != output_beat_order:
        errors.append("originality output_beat_order does not match the storyboard")
    for field, computed in (
        ("claim_order_similarity_percent", claim_similarity),
        ("beat_order_similarity_percent", beat_similarity),
        ("structure_similarity_percent", computed_similarity),
    ):
        try:
            recorded_similarity = require_number(
                originality.get(field),
                f"originality.{field}",
                minimum=0,
                maximum=100,
            )
            if abs(recorded_similarity - computed) > 0.05:
                errors.append(
                    f"Originality {field} must be {computed}, not {recorded_similarity}"
                )
        except GlobalizerError as exc:
            errors.append(str(exc))
    hook_same = originality.get("hook_function_same")
    payoff_same = originality.get("payoff_function_same")
    if not isinstance(hook_same, bool) or not isinstance(payoff_same, bool):
        errors.append("Originality hook/payoff function comparisons must be boolean")
    semantic = originality.get("semantic_review")
    if not isinstance(semantic, dict):
        errors.append("originality.semantic_review must be an object")
        semantic = {}
    semantic_decision = clean_text(semantic.get("decision"))
    if semantic_decision not in {"PASS", "REWRITE_REQUIRED"}:
        errors.append("semantic_review.decision must be PASS or REWRITE_REQUIRED")
    for field in ("hook", "conclusion", "information_order", "expression"):
        if len(clean_text(semantic.get(field))) < 10:
            errors.append(f"semantic_review.{field} must contain a concrete comparison")
    deterministic_rewrite = computed_similarity >= 70 or (
        hook_same is True and payoff_same is True and computed_similarity >= 60
    )
    expected_decision = (
        "REWRITE_REQUIRED"
        if deterministic_rewrite or semantic_decision == "REWRITE_REQUIRED"
        else "PASS"
    )
    if originality.get("decision") != expected_decision:
        errors.append(f"originality decision must be {expected_decision}")
    if expected_decision != "PASS":
        errors.append("Originality guard requires a rewrite before approval or packaging")
    return errors, warnings


def research_gate_satisfied(project: dict[str, Any], score: dict[str, Any], analysis: dict[str, Any]) -> bool:
    if score.get("decision") == "SKIP":
        return False
    if score.get("decision") in {"REVIEW", "HOLD"} or analysis.get("sensitive_topic") is True:
        return bool(project.get("approvals", {}).get("research", {}).get("approved"))
    return True


def approve_stage(project_dir: Path, stage: str) -> dict[str, Any]:
    project, _source = load_project(project_dir)
    score = load_json(project_dir / "global-score.json")
    analysis = load_json(project_dir / "source-analysis.json")
    if score.get("decision") == "SKIP":
        raise GlobalizerError("SKIP projects cannot be approved for production")
    timestamp = now_iso()
    approvals = require_object(project.get("approvals"), "project.approvals")
    if stage == "research":
        errors, _warnings = validate_research(project_dir)
        if errors:
            raise GlobalizerError("Research validation failed:\n- " + "\n- ".join(errors))
        approvals["research"] = {"approved": True, "approved_at": timestamp}
        project["status"] = "scored"
    else:
        if not research_gate_satisfied(project, score, analysis):
            raise GlobalizerError("Research approval is required before script approval")
        errors, _warnings = validate_script(project_dir)
        if errors:
            raise GlobalizerError("Script validation failed:\n- " + "\n- ".join(errors))
        approvals["script"] = {"approved": True, "approved_at": timestamp}
        project["status"] = "script_approved"
    project["updated_at"] = timestamp
    write_json(project_dir / "project.json", project)
    return {"stage": stage, "approved": True, "approved_at": timestamp, "status": project["status"]}


def format_srt_time(seconds: float) -> str:
    milliseconds = int(round(seconds * 1000))
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def build_package_payloads(project_dir: Path) -> dict[str, str | dict[str, Any] | list[Any]]:
    project, source = load_project(project_dir)
    content = load_json(project_dir / "content-en.json")
    storyboard = load_json(project_dir / "storyboard.json")
    score = load_json(project_dir / "global-score.json")
    originality = load_json(project_dir / "originality.json")
    scenes = storyboard["scenes"]
    selected_angle = next(
        item for item in content["angles"] if item["id"] == content["selected_angle_id"]
    )
    selected_hook = next(
        item for item in content["hooks"] if item["id"] == content["selected_hook_id"]
    )
    start = 0.0
    packaged_scenes: list[dict[str, Any]] = []
    highlights: list[dict[str, Any]] = []
    srt_lines: list[str] = []
    asset_rows: list[list[str]] = []
    asset_sections: list[str] = ["# Asset search plan", ""]
    for index, scene in enumerate(scenes, start=1):
        duration = float(scene["duration_seconds"])
        end = start + duration
        slot = f"MEDIA_{index:02d}"
        asset = scene["asset"]
        packaged = {
            "id": scene["id"],
            "slot": slot,
            "start_seconds": round(start, 3),
            "end_seconds": round(end, 3),
            "duration_seconds": duration,
            "role": scene["role"],
            "narration": clean_text(scene["narration"]),
            "caption": clean_text(scene["caption"]),
            "highlight": clean_text(scene["highlight"]),
            "claim_ids": scene["claim_ids"],
            "asset": asset,
        }
        packaged_scenes.append(packaged)
        highlights.append(
            {
                "scene_id": scene["id"],
                "start_seconds": round(start, 3),
                "end_seconds": round(end, 3),
                "text": clean_text(scene["highlight"]),
            }
        )
        srt_lines.extend(
            [
                str(index),
                f"{format_srt_time(start)} --> {format_srt_time(end)}",
                clean_text(scene["narration"]),
                "",
            ]
        )
        asset_rows.append(
            [
                scene["id"],
                slot,
                asset["type"],
                clean_text(asset["preferred_source"]),
                " | ".join(clean_text(item) for item in asset["search_queries"]),
                asset["rights_status"],
                "planned",
                "",
            ]
        )
        asset_sections.extend(
            [
                f"## {scene['id']} · {slot}",
                "",
                f"- Type: {asset['type']}",
                f"- Preferred source: {clean_text(asset['preferred_source'])}",
                f"- Rights: {asset['rights_status']} / planned",
                "- Queries:",
                *[f"  - {clean_text(query)}" for query in asset["search_queries"]],
                "",
            ]
        )
        start = end

    script_markdown = "\n".join(
        [
            f"# {content['selected_title']}",
            "",
            f"- Source signal: {source['url']}",
            f"- Origin: {score['origin']}",
            f"- Global score: {score['total']} / {score['decision']}",
            f"- Selected angle: {selected_angle['angle']}",
            f"- Selected hook: {selected_hook['text']}",
            "- Status: editable production draft; preview and publication blocked",
            "",
            "## Script",
            "",
            *[clean_text(item["text"]) + "\n" for item in content["script_paragraphs"]],
            "## Claim map",
            "",
            *[
                f"- {item['id']}: {', '.join(item['claim_ids'])}"
                for item in content["script_paragraphs"]
            ],
            "",
        ]
    )
    capcut_manifest = {
        "schema_version": SCHEMA_VERSION,
        "template": "global-short-v1",
        "locale": "en-US",
        "project_id": project["id"],
        "title": content["selected_title"],
        "title_line_1": content["title_lines"][0],
        "title_line_2": content["title_lines"][1],
        "highlight": packaged_scenes[0]["highlight"],
        "narration_file": "narration.txt",
        "subtitle_file": "subtitles.srt",
        "scenes_file": "scenes.json",
        "assets_file": "assets.csv",
        "duration_seconds": round(start, 3),
        "scenes": [
            {
                "slot": item["slot"],
                "duration_seconds": item["duration_seconds"],
                "caption": item["caption"],
                "highlight": item["highlight"],
                "asset_type": item["asset"]["type"],
                "search_queries": item["asset"]["search_queries"],
                "rights_status": item["asset"]["rights_status"],
                "asset_status": "planned",
                "asset_path": "",
            }
            for item in packaged_scenes
        ],
        "originality": originality["decision"],
        "preview_approved": False,
        "publish_blocked": True,
        "render_supported": False,
        "upload_supported": False,
    }
    return {
        "script_en.md": script_markdown,
        "narration.txt": clean_text(content["script_text"]) + "\n",
        "subtitles.srt": "\n".join(srt_lines),
        "highlights.json": {"schema_version": SCHEMA_VERSION, "highlights": highlights},
        "scenes.json": {"schema_version": SCHEMA_VERSION, "scenes": packaged_scenes},
        "asset_rows": asset_rows,
        "asset-search.md": "\n".join(asset_sections),
        "capcut-manifest.json": capcut_manifest,
    }


def package_project(project_dir: Path) -> dict[str, Any]:
    errors, _warnings = validate_script(project_dir)
    if errors:
        raise GlobalizerError("Script validation failed:\n- " + "\n- ".join(errors))
    project, _source = load_project(project_dir)
    if not project.get("approvals", {}).get("script", {}).get("approved"):
        raise GlobalizerError("Explicit script approval is required before packaging")
    existing = sorted(name for name in PACKAGE_FILES if (project_dir / name).exists())
    if existing:
        raise GlobalizerError(f"Package files already exist and will not be overwritten: {existing}")
    payloads = build_package_payloads(project_dir)
    for name in ("script_en.md", "narration.txt", "subtitles.srt", "asset-search.md"):
        (project_dir / name).write_text(str(payloads[name]), encoding="utf-8")
    for name in ("highlights.json", "scenes.json", "capcut-manifest.json"):
        write_json(project_dir / name, payloads[name])
    with (project_dir / "assets.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "scene_id",
                "slot",
                "asset_type",
                "preferred_source",
                "search_queries",
                "rights_status",
                "status",
                "asset_path",
            ]
        )
        writer.writerows(payloads["asset_rows"])
    project["status"] = "packaged"
    project["updated_at"] = now_iso()
    project["publish_blocked"] = True
    write_json(project_dir / "project.json", project)
    return {
        "status": "packaged",
        "project_dir": str(project_dir),
        "files": sorted(PACKAGE_FILES),
        "preview_approved": False,
        "publish_blocked": True,
    }


def parse_srt_ranges(value: str) -> list[tuple[int, int]]:
    result: list[tuple[int, int]] = []
    pattern = re.compile(
        r"(?P<sh>\d{2}):(?P<sm>\d{2}):(?P<ss>\d{2}),(?P<sms>\d{3})\s+-->\s+"
        r"(?P<eh>\d{2}):(?P<em>\d{2}):(?P<es>\d{2}),(?P<ems>\d{3})"
    )
    for match in pattern.finditer(value):
        start = (
            int(match["sh"]) * 3_600_000
            + int(match["sm"]) * 60_000
            + int(match["ss"]) * 1000
            + int(match["sms"])
        )
        end = (
            int(match["eh"]) * 3_600_000
            + int(match["em"]) * 60_000
            + int(match["es"]) * 1000
            + int(match["ems"])
        )
        result.append((start, end))
    return result


def validate_package(project_dir: Path) -> tuple[list[str], list[str]]:
    errors, warnings = validate_script(project_dir)
    project, _source = load_project(project_dir)
    if project.get("status") != "packaged":
        errors.append("Project status must be packaged")
    if not project.get("approvals", {}).get("script", {}).get("approved"):
        errors.append("Script approval is missing")
    missing = sorted(name for name in PACKAGE_FILES if not (project_dir / name).is_file())
    if missing:
        errors.append(f"Package files are missing: {missing}")
        return errors, warnings
    manifest = load_json(project_dir / "capcut-manifest.json")
    if manifest.get("template") != "global-short-v1":
        errors.append("CapCut manifest template must be global-short-v1")
    if manifest.get("preview_approved") is not False or manifest.get("publish_blocked") is not True:
        errors.append("Package must remain preview-unapproved and publication-blocked")
    if manifest.get("render_supported") is not False or manifest.get("upload_supported") is not False:
        errors.append("v0.1 must not advertise render or upload support")
    for item in manifest.get("scenes", []):
        if item.get("asset_status") != "planned" or item.get("asset_path") != "":
            errors.append("CapCut manifest asset slots must remain planned with empty paths")
        if not clean_text(item.get("caption")) or not clean_text(item.get("highlight")):
            errors.append("CapCut manifest asset slots must contain both caption forms")
        if not isinstance(item.get("search_queries"), list) or not item.get("search_queries"):
            errors.append("CapCut manifest asset slots must contain search queries")
        if clean_text(item.get("rights_status")) not in ASSET_RIGHTS:
            errors.append("CapCut manifest asset slots must contain a valid rights status")
    ranges = parse_srt_ranges((project_dir / "subtitles.srt").read_text(encoding="utf-8"))
    if len(ranges) != len(manifest.get("scenes", [])):
        errors.append("SRT cue count must match the scene count")
    previous_end = 0
    for start, end in ranges:
        if start < previous_end or end <= start:
            errors.append("SRT time ranges must be monotonic and positive")
            break
        previous_end = end
    media_files = [
        str(path.relative_to(project_dir))
        for path in project_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in MEDIA_SUFFIXES
    ]
    if media_files:
        errors.append(f"v0.1 package must not contain media or TTS files: {media_files}")
    draft_files = [
        str(path.relative_to(project_dir))
        for path in project_dir.rglob("*")
        if path.is_file() and path.name in {"draft_info.json", "draft_meta_info.json"}
    ]
    if draft_files:
        errors.append(f"v0.1 package must not contain CapCut draft files: {draft_files}")
    return errors, warnings


def validation_payload(project_dir: Path, stage: str) -> dict[str, Any]:
    if stage == "ingest":
        errors, warnings = validate_ingest(project_dir)
    elif stage == "research":
        errors, warnings = validate_research(project_dir)
    elif stage == "script":
        errors, warnings = validate_script(project_dir)
    else:
        errors, warnings = validate_package(project_dir)
    return {
        "stage": stage,
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "project_dir": str(project_dir),
    }


def command_doctor(args: argparse.Namespace) -> int:
    root = Path(args.projects_root).expanduser().resolve()
    parent = root if root.exists() else root.parent
    caption_tls = caption_tls_configuration()
    payload = {
        "plugin": "shorts-suite:globalize",
        "version": VERSION,
        "python": sys.version.split()[0],
        "yt_dlp": "python-module" if yt_dlp_available() else None,
        "projects_root": str(root),
        "projects_root_writable": os.access(parent, os.W_OK),
        "caption_tls": caption_tls,
        "discovery_source": dict(BRAINBULB_CHANNEL),
        "channel_monitoring": False,
        "database_required": False,
        "video_download": False,
        "tts": False,
        "render": False,
        "capcut_draft_edit": False,
        "upload": False,
        "ready": (
            sys.version_info >= (3, 10)
            and yt_dlp_available()
            and caption_tls["available"]
            and os.access(parent, os.W_OK)
        ),
    }
    print_json(payload) if args.json else print("Shorts Suite globalize is ready." if payload["ready"] else "Shorts Suite globalize is not ready.")
    return 0 if payload["ready"] else 1


def command_init(args: argparse.Namespace) -> int:
    print_json(initialize_project(args))
    return 0


def command_discover(args: argparse.Namespace) -> int:
    print_json(discover_brainbulb_shorts(args.limit))
    return 0


def command_score(args: argparse.Namespace) -> int:
    project_dir = Path(args.project_dir).expanduser().resolve()
    print_json(score_project(project_dir))
    return 0


def command_approve(args: argparse.Namespace) -> int:
    if not args.confirm:
        raise GlobalizerError("Approval requires --confirm")
    project_dir = Path(args.project_dir).expanduser().resolve()
    print_json(approve_stage(project_dir, args.stage))
    return 0


def command_validate(args: argparse.Namespace) -> int:
    project_dir = Path(args.project_dir).expanduser().resolve()
    payload = validation_payload(project_dir, args.stage)
    print_json(payload)
    return 0 if payload["valid"] else 1


def command_package(args: argparse.Namespace) -> int:
    project_dir = Path(args.project_dir).expanduser().resolve()
    print_json(package_project(project_dir))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="globalize.py",
        description="Turn one Korean YouTube Shorts signal into a verified English production draft.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor = subparsers.add_parser("doctor", help="Check the local v0.1 runtime")
    doctor.add_argument("--json", action="store_true")
    doctor.add_argument("--projects-root", default=str(DEFAULT_PROJECTS_ROOT))
    doctor.set_defaults(handler=command_doctor)

    discover = subparsers.add_parser(
        "discover",
        help="List selectable candidates from the Brainbulb channel Shorts tab",
    )
    discover.add_argument("--limit", type=int, choices=range(1, MAX_DISCOVERY_LIMIT + 1), default=3)
    discover.set_defaults(handler=command_discover)

    init = subparsers.add_parser("init", help="Create a project from one YouTube Shorts URL")
    init.add_argument("--url", required=True)
    init.add_argument("--transcript-file", default="")
    init.add_argument("--project-dir", default="")
    init.add_argument("--projects-root", default=str(DEFAULT_PROJECTS_ROOT))
    init.set_defaults(handler=command_init)

    score = subparsers.add_parser("score", help="Calculate the Global Potential Score")
    score.add_argument("--project-dir", required=True)
    score.set_defaults(handler=command_score)

    approve = subparsers.add_parser("approve", help="Record explicit research or script approval")
    approve.add_argument("--project-dir", required=True)
    approve.add_argument("--stage", choices=("research", "script"), required=True)
    approve.add_argument("--confirm", action="store_true")
    approve.set_defaults(handler=command_approve)

    validate = subparsers.add_parser("validate", help="Validate a project stage")
    validate.add_argument("--project-dir", required=True)
    validate.add_argument("--stage", choices=("ingest", "research", "script", "package"), required=True)
    validate.set_defaults(handler=command_validate)

    package = subparsers.add_parser("package", help="Write the approved editable production package")
    package.add_argument("--project-dir", required=True)
    package.set_defaults(handler=command_package)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        code = args.handler(args)
    except GlobalizerError as exc:
        print(f"shorts-suite globalize error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    raise SystemExit(code)


if __name__ == "__main__":
    main()
