from __future__ import annotations

import hashlib
import json
import mimetypes
import os
import re
import shutil
import tempfile
import unicodedata
import zipfile
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any, Iterable
from urllib.parse import urlparse, urlunparse
from xml.etree import ElementTree


SCHEMA_VERSION = "careerfill-index-v1"
try:
    PLUGIN_VERSION = str(
        json.loads(
            (Path(__file__).resolve().parents[1] / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
        )["version"]
    )
except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
    PLUGIN_VERSION = "0.4.0"
MAX_FILE_BYTES = 50 * 1024 * 1024
MAX_ARCHIVE_BYTES = 120 * 1024 * 1024
MAX_ARCHIVE_MEMBERS = 2_000
MAX_TEXT_CHARS = 2_000_000
DEFAULT_MAX_FILES = 2_000
SUPPORTED_SUFFIXES = {
    ".pdf",
    ".docx",
    ".hwpx",
    ".md",
    ".txt",
    ".yaml",
    ".yml",
    ".jpg",
    ".jpeg",
    ".png",
}
EXCLUDED_DIRECTORIES = {"90_private", ".git", ".careerfill", "node_modules"}
SENSITIVITY_ORDER = {"S0": 0, "S1": 1, "S2": 2, "S3": 3}
PRIVATE_MARKERS = (
    "90_private",
    "주민등록",
    "신분증",
    "여권",
    "급여",
    "연봉계약",
    "통장",
    "계좌",
    "병적",
    "병역",
    "군복무",
    "증명사진",
    "프로필사진",
    "신분사진",
    "resident-id",
    "passport",
    "payroll",
    "bank",
)
S2_MARKERS = (
    "자격증",
    "자격",
    "국가기술자격",
    "기능사",
    "정보처리기사",
    "정보보안산업기사",
    "컴퓨터활용능력",
    "컴활",
    "itq",
    "gtq",
    "dasp",
    "데이터아키텍처",
    "리눅스마스터",
    "네트워크관리사",
    "certificate",
    "재직증명",
    "경력증명",
    "employment",
    "졸업증명",
    "학위",
    "award",
    "수상",
)
CLAIM_KEYWORDS = {
    "experience": ("경력", "근무", "담당", "운영", "구축", "설계", "개발", "관리"),
    "project": ("프로젝트", "project", "서비스", "시스템", "플랫폼", "마이그레이션"),
    "achievement": ("성과", "개선", "감소", "증가", "달성", "최적화", "%"),
    "collaboration": ("협업", "조율", "커뮤니케이션", "팀", "리드", "지원"),
    "education": ("학력", "대학교", "대학원", "전공", "졸업", "교육"),
    "certification": ("자격", "certification", "certificate", "기사"),
}
SKILL_TERMS = (
    "AWS",
    "Azure",
    "GCP",
    "Docker",
    "Kubernetes",
    "Python",
    "Java",
    "JavaScript",
    "TypeScript",
    "React",
    "Vue",
    "SQL",
    "PostgreSQL",
    "MySQL",
    "Redis",
    "Linux",
    "Nginx",
    "Traefik",
    "Terraform",
    "Ansible",
    "GitHub",
    "Jenkins",
)
MANUAL_FIELD_MARKERS = (
    "희망 연봉",
    "장애",
    "보훈",
    "병역",
    "성별",
    "종교",
    "전과",
    "징계",
    "법적",
    "입사 가능일",
    "개인정보",
    "사실 확인",
    "동의",
    "서약",
)


class CareerFillError(ValueError):
    pass


def utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def data_root() -> Path:
    configured = os.environ.get("CAREERFILL_DATA") or os.environ.get("PLUGIN_DATA")
    if configured:
        return Path(configured).expanduser().resolve()
    return (Path.home() / ".codex" / "careerfill").resolve()


def _ensure_data_root() -> Path:
    root = data_root()
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    return root


def _atomic_json_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CareerFillError(f"Required CareerFill data is missing: {path.name}") from exc
    except json.JSONDecodeError as exc:
        raise CareerFillError(f"CareerFill data is invalid JSON: {path.name}") from exc
    if not isinstance(payload, dict):
        raise CareerFillError(f"CareerFill data must be an object: {path.name}")
    return payload


def _config_path() -> Path:
    return data_root() / "config.json"


def _index_path() -> Path:
    return data_root() / "index.json"


def _visual_root(document_id: str) -> Path:
    if not re.fullmatch(r"doc_[0-9a-f]{16}", document_id):
        raise CareerFillError("invalid document_id")
    return data_root() / "visual-reviews" / document_id


def validate_vault_path(raw_path: str) -> Path:
    if not isinstance(raw_path, str) or not raw_path.strip():
        raise CareerFillError("vault_path must be a non-empty path")
    expanded = Path(raw_path.strip()).expanduser()
    if not expanded.is_absolute():
        raise CareerFillError("vault_path must be absolute (or start with ~)")
    if expanded.is_symlink():
        raise CareerFillError("CareerVault root cannot be a symbolic link")
    try:
        resolved = expanded.resolve(strict=True)
    except FileNotFoundError as exc:
        raise CareerFillError("CareerVault path does not exist") from exc
    if not resolved.is_dir():
        raise CareerFillError("CareerVault path must be a directory")
    forbidden = {Path(resolved.anchor).resolve(), Path.home().resolve()}
    if resolved in forbidden:
        raise CareerFillError("CareerVault cannot be a filesystem root or the whole home directory")
    return resolved


def configure_vault(vault_path: str) -> dict[str, Any]:
    root = validate_vault_path(vault_path)
    payload = {
        "schema_version": "careerfill-config-v1",
        "vault_path": str(root),
        "configured_at": utc_now(),
        "source_write_allowed": False,
        "database_used": False,
    }
    _atomic_json_write(_ensure_data_root() / "config.json", payload)
    return payload


def load_config() -> dict[str, Any]:
    return _load_json(_config_path())


def _configured_vault(explicit_path: str | None) -> Path:
    if explicit_path:
        return validate_vault_path(explicit_path)
    config = load_config()
    path = config.get("vault_path")
    if not isinstance(path, str):
        raise CareerFillError("CareerVault is not configured")
    return validate_vault_path(path)


def _safe_files(root: Path, max_files: int) -> tuple[list[Path], list[str]]:
    if max_files < 1 or max_files > 10_000:
        raise CareerFillError("max_files must be between 1 and 10000")
    files: list[Path] = []
    warnings: list[str] = []
    pending = [root]
    while pending:
        directory = pending.pop()
        try:
            entries = sorted(os.scandir(directory), key=lambda entry: entry.name.casefold())
        except OSError as exc:
            warnings.append(f"unreadable_directory:{directory.relative_to(root)}:{exc.__class__.__name__}")
            continue
        for entry in entries:
            relative = Path(entry.path).relative_to(root)
            if entry.is_symlink():
                warnings.append(f"symlink_skipped:{relative}")
                continue
            if entry.is_dir(follow_symlinks=False):
                if entry.name.casefold() in EXCLUDED_DIRECTORIES or entry.name.startswith("."):
                    warnings.append(f"directory_excluded:{relative}")
                    continue
                pending.append(Path(entry.path))
                continue
            if not entry.is_file(follow_symlinks=False):
                continue
            if Path(entry.name).suffix.casefold() not in SUPPORTED_SUFFIXES:
                continue
            files.append(Path(entry.path))
            if len(files) > max_files:
                raise CareerFillError(f"CareerVault exceeds max_files={max_files}")
    return sorted(files, key=lambda path: str(path.relative_to(root)).casefold()), warnings


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_zip(path: Path) -> zipfile.ZipFile:
    archive = zipfile.ZipFile(path)
    members = archive.infolist()
    if len(members) > MAX_ARCHIVE_MEMBERS:
        archive.close()
        raise CareerFillError("archive_member_limit_exceeded")
    total = 0
    for member in members:
        member_path = PurePosixPath(member.filename)
        if member_path.is_absolute() or ".." in member_path.parts:
            archive.close()
            raise CareerFillError("archive_path_traversal_detected")
        if member.flag_bits & 0x1:
            archive.close()
            raise CareerFillError("encrypted_archive_not_supported")
        total += member.file_size
        if total > MAX_ARCHIVE_BYTES:
            archive.close()
            raise CareerFillError("archive_uncompressed_limit_exceeded")
        if member.file_size > 10 * 1024 * 1024 and member.compress_size and member.file_size / member.compress_size > 200:
            archive.close()
            raise CareerFillError("archive_compression_ratio_rejected")
    return archive


def _detect_type(path: Path) -> str:
    suffix = path.suffix.casefold()
    with path.open("rb") as stream:
        header = stream.read(16)
    if header.startswith(b"%PDF-"):
        detected = "pdf"
    elif header.startswith(b"PK\x03\x04"):
        with _safe_zip(path) as archive:
            names = set(archive.namelist())
            if "word/document.xml" in names:
                detected = "docx"
            elif any(name.startswith("Contents/section") and name.endswith(".xml") for name in names):
                detected = "hwpx"
            else:
                detected = "zip"
    elif header.startswith(b"\x89PNG\r\n\x1a\n"):
        detected = "png"
    elif header.startswith((b"\xff\xd8\xff",)):
        detected = "jpeg"
    elif b"\x00" not in header:
        detected = "text"
    else:
        detected = "binary"
    expected = {
        ".pdf": "pdf",
        ".docx": "docx",
        ".hwpx": "hwpx",
        ".md": "text",
        ".txt": "text",
        ".yaml": "text",
        ".yml": "text",
        ".png": "png",
        ".jpg": "jpeg",
        ".jpeg": "jpeg",
    }.get(suffix)
    if expected and detected != expected:
        raise CareerFillError(f"mime_mismatch:expected_{expected}:detected_{detected}")
    return detected


def _decode_text(raw: bytes) -> tuple[str, str]:
    for encoding in ("utf-8-sig", "cp949"):
        try:
            return raw.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    raise CareerFillError("text_encoding_not_supported")


def _extract_text_file(path: Path) -> tuple[str, list[dict[str, Any]], dict[str, Any]]:
    text, encoding = _decode_text(path.read_bytes())
    text = text[:MAX_TEXT_CHARS]
    spans = _paragraph_spans(text, "paragraph")
    return text, spans, {"encoding": encoding}


def _xml_text(element: ElementTree.Element) -> str:
    return "".join(part for part in element.itertext() if part)


def _extract_docx(path: Path) -> tuple[str, list[dict[str, Any]], dict[str, Any]]:
    with _safe_zip(path) as archive:
        root = ElementTree.fromstring(archive.read("word/document.xml"))
    paragraphs: list[str] = []
    for element in root.iter():
        if element.tag.endswith("}p"):
            value = _xml_text(element).strip()
            if value:
                paragraphs.append(value)
    text = "\n\n".join(paragraphs)[:MAX_TEXT_CHARS]
    return text, _paragraph_spans(text, "paragraph"), {"paragraphs": len(paragraphs)}


def _extract_hwpx(path: Path) -> tuple[str, list[dict[str, Any]], dict[str, Any]]:
    sections: list[tuple[str, str]] = []
    with _safe_zip(path) as archive:
        names = sorted(
            name for name in archive.namelist() if name.startswith("Contents/section") and name.endswith(".xml")
        )
        for name in names:
            root = ElementTree.fromstring(archive.read(name))
            value = _xml_text(root).strip()
            if value:
                sections.append((name, value))
    text = "\n\n".join(value for _, value in sections)[:MAX_TEXT_CHARS]
    spans: list[dict[str, Any]] = []
    for index, (name, value) in enumerate(sections, start=1):
        for span in _paragraph_spans(value, "paragraph"):
            spans.append({**span, "section": index, "archive_member": name})
    return text, spans, {"sections": len(sections)}


def _extract_pdf(path: Path) -> tuple[str, list[dict[str, Any]], dict[str, Any]]:
    try:
        import fitz  # type: ignore
    except ImportError as exc:
        raise CareerFillError("pdf_parser_unavailable:PyMuPDF") from exc
    document = fitz.open(path)
    try:
        if document.needs_pass:
            raise CareerFillError("encrypted_pdf_not_supported")
        pages: list[str] = []
        spans: list[dict[str, Any]] = []
        for page_index, page in enumerate(document, start=1):
            value = page.get_text("text").strip()
            pages.append(value)
            for span in _paragraph_spans(value, "paragraph"):
                spans.append({**span, "page": page_index})
            if sum(len(item) for item in pages) >= MAX_TEXT_CHARS:
                break
        text = "\n\n".join(pages)[:MAX_TEXT_CHARS]
        return text, spans, {"pages": document.page_count}
    finally:
        document.close()


def _paragraph_spans(text: str, unit: str) -> list[dict[str, Any]]:
    parts = [part.strip() for part in re.split(r"\n\s*\n|\r\n\s*\r\n", text) if part.strip()]
    if len(parts) <= 1:
        parts = [part.strip() for part in text.splitlines() if part.strip()]
    spans: list[dict[str, Any]] = []
    for index, value in enumerate(parts[:2_000], start=1):
        spans.append({unit: index, "text": value[:4_000]})
    return spans


def _classify_document(relative_path: str) -> str:
    value = unicodedata.normalize("NFC", relative_path).casefold()
    if "00_profile" in value or "기본정보" in value or "지원조건" in value:
        return "profile"
    if "01_resume" in value or "이력서" in value or "resume" in value:
        return "resume"
    if "02_cover" in value or "자기소개" in value or "cover" in value:
        return "cover_letter"
    if "03_career" in value or "경력기술" in value:
        return "career"
    if "04_portfolio" in value or "포트폴리오" in value or "portfolio" in value:
        return "portfolio"
    if "05_evidence" in value or any(
        unicodedata.normalize("NFC", marker).casefold() in value for marker in S2_MARKERS
    ):
        return "evidence"
    return "other"


def _sensitivity(relative_path: str, document_type: str) -> str:
    value = unicodedata.normalize("NFC", relative_path).casefold()
    if any(unicodedata.normalize("NFC", marker).casefold() in value for marker in PRIVATE_MARKERS):
        return "S3"
    if document_type == "evidence" or any(
        unicodedata.normalize("NFC", marker).casefold() in value for marker in S2_MARKERS
    ):
        return "S2"
    return "S1"


def _contains_direct_identifier(text: str) -> bool:
    return bool(
        re.search(r"\b\d{6}[- ]?[1-4]\d{6}\b", text)
        or re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", text)
        or re.search(r"\b01[016789][ -]?\d{3,4}[ -]?\d{4}\b", text)
    )


def _redact_direct_identifiers(text: str) -> str:
    redacted = re.sub(r"\b\d{6}[- ]?[1-4]\d{6}\b", "[REDACTED_ID]", text)
    redacted = re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "[REDACTED_EMAIL]", redacted)
    return re.sub(r"\b01[016789][ -]?\d{3,4}[ -]?\d{4}\b", "[REDACTED_PHONE]", redacted)


def _content_term_hashes(text: str) -> list[str]:
    terms = re.findall(r"[가-힣A-Za-z][가-힣A-Za-z0-9+#.-]{1,40}", text.casefold())
    counts: dict[str, int] = {}
    for term in terms:
        if _contains_direct_identifier(term) or term in {"그리고", "하지만", "대한", "통해", "위해", "the", "and", "with"}:
            continue
        counts[term] = counts.get(term, 0) + 1
    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:300]
    return [hashlib.sha256(term.encode()).hexdigest()[:16] for term, _ in ranked]


def _claim_category(statement: str) -> str:
    lowered = statement.casefold()
    scores = {
        category: sum(1 for keyword in keywords if keyword.casefold() in lowered)
        for category, keywords in CLAIM_KEYWORDS.items()
    }
    best = max(scores, key=scores.get)
    return best if scores[best] else "other"


def _period_tokens(statement: str) -> list[str]:
    tokens = re.findall(r"(?:19|20)\d{2}(?:[./-](?:0?[1-9]|1[0-2]))?", statement)
    return list(dict.fromkeys(tokens))[:4]


def _claim_candidates(document: dict[str, Any], spans: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if document["document_type"] in {"profile", "evidence"}:
        return []
    claims: list[dict[str, Any]] = []
    for span in spans[:800]:
        raw = str(span.get("text", ""))
        sentences = re.split(r"(?<=[.!?])\s+|\n+", raw)
        for sentence in sentences:
            statement = re.sub(r"\s+", " ", sentence).strip(" -•\t")
            if len(statement) < 20 or len(statement) > 700 or _contains_direct_identifier(statement):
                continue
            category = _claim_category(statement)
            if category == "other" and len(statement) < 45:
                continue
            source = {key: value for key, value in span.items() if key != "text"}
            source.update({"file": document["relative_path"], "source_hash": document["sha256"]})
            seed = f"{document['sha256']}:{json.dumps(source, sort_keys=True)}:{statement}"
            claim_id = f"claim_{hashlib.sha256(seed.encode()).hexdigest()[:16]}"
            skills = [term for term in SKILL_TERMS if term.casefold() in statement.casefold()]
            claims.append(
                {
                    "claim_id": claim_id,
                    "category": category,
                    "statement": statement,
                    "skills": skills,
                    "period_tokens": _period_tokens(statement),
                    "source_refs": [source],
                    "verification": {"status": "review_required", "verified_at": None},
                }
            )
            if len(claims) >= 600:
                return claims
    return claims


def _flatten_mapping(value: Any, prefix: str = "") -> Iterable[tuple[str, Any]]:
    if isinstance(value, dict):
        for key, item in value.items():
            next_prefix = f"{prefix}.{key}" if prefix else str(key)
            yield from _flatten_mapping(item, next_prefix)
    elif isinstance(value, list):
        yield prefix, value
    elif prefix:
        yield prefix, value


def _structured_profile(text: str, relative_path: str) -> dict[str, Any] | None:
    if Path(relative_path).suffix.casefold() not in {".yaml", ".yml"}:
        return None
    try:
        import yaml  # type: ignore
    except ImportError:
        return None
    try:
        payload = yaml.safe_load(text)
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def _build_profile(profile_sources: list[dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    candidates: dict[str, list[dict[str, Any]]] = {}
    for source in profile_sources:
        mapping = source.get("mapping")
        if not isinstance(mapping, dict):
            continue
        for field, value in _flatten_mapping(mapping):
            if value in (None, "", []):
                continue
            candidates.setdefault(field, []).append({"value": value, "source": source["relative_path"]})
    profile: dict[str, Any] = {}
    conflicts: list[dict[str, Any]] = []
    for field, values in sorted(candidates.items()):
        unique: dict[str, dict[str, Any]] = {}
        for item in values:
            key = json.dumps(item["value"], ensure_ascii=False, sort_keys=True)
            unique.setdefault(key, item)
        if len(unique) == 1:
            profile[field] = next(iter(unique.values()))
        else:
            conflicts.append({"type": "profile_value_conflict", "field": field, "candidates": list(unique.values())})
    return profile, conflicts


def scan_vault(vault_path: str | None = None, max_files: int = DEFAULT_MAX_FILES) -> dict[str, Any]:
    root = _configured_vault(vault_path)
    previous_verification: dict[str, dict[str, Any]] = {}
    previous_visual_reviews: dict[str, dict[str, Any]] = {}
    previous_evidence_visual: dict[str, dict[str, Any]] = {}
    previous_visual_claims: list[dict[str, Any]] = []
    previous_notion_sources: list[dict[str, Any]] = []
    previous_notion_claims: list[dict[str, Any]] = []
    if _index_path().exists():
        try:
            previous = load_index()
            previous_verification = {
                item["claim_id"]: item.get("verification", {})
                for item in previous.get("claims", [])
                if isinstance(item, dict) and isinstance(item.get("claim_id"), str)
            }
            previous_visual_reviews = {
                item["document_id"]: item["visual_review"]
                for item in previous.get("documents", [])
                if isinstance(item, dict)
                and isinstance(item.get("document_id"), str)
                and isinstance(item.get("visual_review"), dict)
            }
            previous_evidence_visual = {
                item["evidence_id"]: item["visual_review"]
                for item in previous.get("evidence", [])
                if isinstance(item, dict)
                and isinstance(item.get("evidence_id"), str)
                and isinstance(item.get("visual_review"), dict)
            }
            previous_visual_claims = [
                item
                for item in previous.get("claims", [])
                if isinstance(item, dict)
                and any(
                    isinstance(ref, dict) and ref.get("source_type") == "visual_review"
                    for ref in item.get("source_refs", [])
                )
            ]
            previous_notion_sources = [
                item for item in previous.get("notion_sources", []) if isinstance(item, dict)
            ]
            previous_notion_claims = [
                item
                for item in previous.get("claims", [])
                if isinstance(item, dict)
                and any(
                    isinstance(ref, dict) and ref.get("source_type") == "notion_snapshot"
                    for ref in item.get("source_refs", [])
                )
            ]
        except CareerFillError:
            previous_verification = {}
            previous_visual_reviews = {}
            previous_evidence_visual = {}
            previous_visual_claims = []
            previous_notion_sources = []
            previous_notion_claims = []
    paths, warnings = _safe_files(root, max_files)
    documents: list[dict[str, Any]] = []
    claims: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []
    profile_sources: list[dict[str, Any]] = []
    for path in paths:
        relative = str(path.relative_to(root))
        stat = path.stat()
        document_type = _classify_document(relative)
        sensitivity = _sensitivity(relative, document_type)
        document: dict[str, Any] = {
            "document_id": "",
            "relative_path": relative,
            "suffix": path.suffix.casefold(),
            "document_type": document_type,
            "size_bytes": stat.st_size,
            "sha256": "",
            "mime_type": mimetypes.guess_type(path.name)[0] or "application/octet-stream",
            "sensitivity": sensitivity,
            "extraction": {"status": "pending", "details": {}},
        }
        try:
            if stat.st_size > MAX_FILE_BYTES:
                raise CareerFillError("file_size_limit_exceeded")
            detected = _detect_type(path)
            digest = _sha256(path)
            document["sha256"] = digest
            document["document_id"] = f"doc_{digest[:16]}"
            if document["document_id"] in previous_visual_reviews:
                document["visual_review"] = previous_visual_reviews[document["document_id"]]
            text = ""
            spans: list[dict[str, Any]] = []
            details: dict[str, Any] = {}
            if detected == "pdf":
                text, spans, details = _extract_pdf(path)
            elif detected == "docx":
                text, spans, details = _extract_docx(path)
            elif detected == "hwpx":
                text, spans, details = _extract_hwpx(path)
            elif detected == "text":
                text, spans, details = _extract_text_file(path)
            else:
                details = {"catalog_only": True, "reason": "image_ocr_out_of_scope"}
            document["extraction"] = {
                "status": "extracted" if text else "catalog_only",
                "text_sha256": hashlib.sha256(text.encode()).hexdigest() if text else None,
                "character_count": len(text),
                "details": details,
            }
            if sensitivity != "S3":
                claims.extend(_claim_candidates(document, spans))
            mapping = _structured_profile(text, relative)
            if mapping is not None and sensitivity != "S3":
                profile_sources.append({"relative_path": relative, "mapping": mapping})
            if document_type in {"resume", "career", "portfolio", "evidence"}:
                evidence_id = f"evidence_{digest[:16]}"
                evidence.append(
                    {
                        "evidence_id": evidence_id,
                        "file": relative,
                        "document_type": document_type,
                        "mime_type": document["mime_type"],
                        "size_bytes": stat.st_size,
                        "sensitivity": sensitivity,
                        "content_verified": False,
                        "content_term_hashes": _content_term_hashes(text) if text else [],
                        "hash": f"sha256:{digest}",
                        "status": "candidate_only",
                    }
                )
                if evidence_id in previous_evidence_visual:
                    evidence[-1]["visual_review"] = previous_evidence_visual[evidence_id]
        except Exception as exc:
            document["extraction"] = {"status": "error", "error": str(exc)[:240], "details": {}}
            warnings.append(f"file_error:{relative}:{exc}")
        documents.append(document)
    profile, conflicts = _build_profile(profile_sources)
    current_hashes = {item.get("sha256") for item in documents if item.get("sha256")}
    for claim in previous_visual_claims:
        if any(
            isinstance(ref, dict) and ref.get("source_hash") in current_hashes
            for ref in claim.get("source_refs", [])
        ):
            claims.append(claim)
    claims.extend(previous_notion_claims)
    unique_claims = {claim["claim_id"]: claim for claim in claims}
    for claim_id, claim in unique_claims.items():
        if claim_id in previous_verification:
            claim["verification"] = previous_verification[claim_id]
    index = {
        "schema_version": SCHEMA_VERSION,
        "plugin_version": PLUGIN_VERSION,
        "vault_path": str(root),
        "scanned_at": utc_now(),
        "source_write_performed": False,
        "database_used": False,
        "documents": documents,
        "profile": profile,
        "claims": list(unique_claims.values()),
        "evidence": evidence,
        "notion_sources": previous_notion_sources,
        "conflicts": conflicts,
        "warnings": warnings,
        "stats": {
            "documents": len(documents),
            "extracted": sum(1 for item in documents if item["extraction"]["status"] == "extracted"),
            "catalog_only": sum(1 for item in documents if item["extraction"]["status"] == "catalog_only"),
            "errors": sum(1 for item in documents if item["extraction"]["status"] == "error"),
            "claims_review_required": sum(
                1 for item in unique_claims.values() if item.get("verification", {}).get("status") == "review_required"
            ),
            "claims_verified": sum(
                1 for item in unique_claims.values() if item.get("verification", {}).get("status") == "verified"
            ),
            "claims_rejected": sum(
                1 for item in unique_claims.values() if item.get("verification", {}).get("status") == "rejected"
            ),
            "evidence_candidates": len(evidence),
            "visual_reviews": sum(1 for item in documents if isinstance(item.get("visual_review"), dict)),
            "notion_sources": len(previous_notion_sources),
            "notion_blocks": sum(
                len(item.get("blocks", [])) for item in previous_notion_sources if isinstance(item.get("blocks"), list)
            ),
            "conflicts": len(conflicts),
        },
    }
    _atomic_json_write(_ensure_data_root() / "index.json", index)
    if vault_path:
        configure_vault(str(root))
    return {"schema_version": SCHEMA_VERSION, "vault_path": str(root), **index["stats"], "warnings": warnings[:50]}


def load_index() -> dict[str, Any]:
    payload = _load_json(_index_path())
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise CareerFillError("CareerFill index schema is not supported")
    return payload


def _empty_index() -> dict[str, Any]:
    vault_path = None
    if _config_path().exists():
        try:
            configured = _load_json(_config_path()).get("vault_path")
            vault_path = configured if isinstance(configured, str) else None
        except CareerFillError:
            vault_path = None
    return {
        "schema_version": SCHEMA_VERSION,
        "plugin_version": PLUGIN_VERSION,
        "vault_path": vault_path,
        "scanned_at": None,
        "source_write_performed": False,
        "database_used": False,
        "documents": [],
        "profile": {},
        "claims": [],
        "evidence": [],
        "notion_sources": [],
        "conflicts": [],
        "warnings": [],
        "stats": {
            "documents": 0,
            "extracted": 0,
            "catalog_only": 0,
            "errors": 0,
            "claims_review_required": 0,
            "claims_verified": 0,
            "claims_rejected": 0,
            "evidence_candidates": 0,
            "visual_reviews": 0,
            "notion_sources": 0,
            "notion_blocks": 0,
            "conflicts": 0,
        },
    }


def _load_or_empty_index() -> dict[str, Any]:
    return load_index() if _index_path().exists() else _empty_index()


def vault_status() -> dict[str, Any]:
    config = _load_json(_config_path()) if _config_path().exists() else None
    index = _load_json(_index_path()) if _index_path().exists() else None
    notion_count = len(index.get("notion_sources", [])) if index else 0
    document_count = len(index.get("documents", [])) if index else 0
    return {
        "configured": config is not None,
        "indexed": index is not None,
        "sources_ready": bool(document_count or notion_count),
        "vault_path": config.get("vault_path") if config else None,
        "notion_sources": notion_count,
        "scanned_at": index.get("scanned_at") if index else None,
        "stats": index.get("stats") if index else None,
        "source_write_allowed": False,
        "database_used": False,
    }


def _canonical_notion_url(raw_url: str) -> str:
    if not isinstance(raw_url, str) or not raw_url.strip():
        raise CareerFillError("notion_url must be a non-empty URL")
    parsed = urlparse(raw_url.strip())
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise CareerFillError("Notion sources require a normal https URL without embedded credentials")
    host = parsed.hostname.casefold().rstrip(".")
    allowed = (
        host in {"notion.so", "www.notion.so", "notion.site", "notion.com", "www.notion.com"}
        or host.endswith(".notion.so")
        or host.endswith(".notion.site")
        or host.endswith(".notion.com")
    )
    if not allowed:
        raise CareerFillError("Notion URL host must be notion.so, notion.site, or notion.com")
    try:
        if parsed.port not in (None, 443):
            raise CareerFillError("Notion URL cannot use a custom port")
    except ValueError as exc:
        raise CareerFillError("Notion URL contains an invalid port") from exc
    path = re.sub(r"/{2,}", "/", parsed.path or "/")
    if path != "/":
        path = path.rstrip("/")
    return urlunparse(("https", host, path, "", "", ""))


def _notion_page_id(canonical_url: str) -> str | None:
    compact = re.sub(r"[^0-9a-fA-F]", "", urlparse(canonical_url).path)
    matches = re.findall(r"[0-9a-fA-F]{32}", compact)
    return matches[-1].casefold() if matches else None


def _normalize_notion_blocks(blocks: list[Any]) -> list[dict[str, Any]]:
    if not isinstance(blocks, list) or not blocks or len(blocks) > 2_000:
        raise CareerFillError("notion blocks must contain 1-2000 items")
    normalized: list[dict[str, Any]] = []
    total_characters = 0
    used_ids: set[str] = set()
    for position, block in enumerate(blocks, start=1):
        if not isinstance(block, dict):
            raise CareerFillError("each Notion block must be an object")
        text = _redact_direct_identifiers(str(block.get("text") or "").strip())
        if len(text) > 20_000:
            raise CareerFillError("a Notion block exceeds 20000 characters")
        total_characters += len(text)
        if total_characters > MAX_TEXT_CHARS:
            raise CareerFillError("Notion snapshot exceeds the text limit")
        block_type = str(block.get("type") or "paragraph")[:60]
        provided_id = str(block.get("block_id") or "").strip()[:200]
        seed = f"{position}:{block_type}:{text}"
        block_id = provided_id or f"block_{position}_{hashlib.sha256(seed.encode()).hexdigest()[:12]}"
        if block_id in used_ids:
            block_id = f"{block_id}_{position}"
        used_ids.add(block_id)
        screenshot_sha256 = str(block.get("screenshot_sha256") or "")
        if screenshot_sha256 and not re.fullmatch(r"(?:sha256:)?[0-9a-fA-F]{64}", screenshot_sha256):
            raise CareerFillError("Notion block screenshot_sha256 must be a SHA-256 value")
        normalized.append(
            {
                "block_id": block_id,
                "index": position,
                "type": block_type,
                "text": text,
                "screenshot_sha256": screenshot_sha256 or None,
            }
        )
    return normalized


def _notion_claim_candidates(source: dict[str, Any]) -> list[dict[str, Any]]:
    claims: list[dict[str, Any]] = []
    for block in source.get("blocks", []):
        raw = str(block.get("text") or "")
        for sentence in re.split(r"(?<=[.!?])\s+|\n+", raw):
            statement = re.sub(r"\s+", " ", sentence).strip(" -•\t")
            if (
                len(statement) < 20
                or len(statement) > 700
                or _contains_direct_identifier(statement)
                or "[REDACTED_" in statement
            ):
                continue
            category = _claim_category(statement)
            if category == "other" and len(statement) < 45:
                continue
            source_ref = {
                "source_type": "notion_snapshot",
                "notion_source_id": source["source_id"],
                "url": source["url"],
                "page_id": source.get("page_id"),
                "block_id": block["block_id"],
                "block_index": block["index"],
                "source_hash": source["source_hash"],
            }
            if block.get("screenshot_sha256"):
                source_ref["screenshot_sha256"] = block["screenshot_sha256"]
            seed = f"{source['source_hash']}:{block['block_id']}:{statement}"
            claims.append(
                {
                    "claim_id": f"claim_{hashlib.sha256(seed.encode()).hexdigest()[:16]}",
                    "category": category,
                    "statement": statement,
                    "skills": [term for term in SKILL_TERMS if term.casefold() in statement.casefold()],
                    "period_tokens": _period_tokens(statement),
                    "source_refs": [source_ref],
                    "verification": {"status": "review_required", "verified_at": None},
                }
            )
            if len(claims) >= 1_000:
                return claims
    return claims


def _recompute_source_stats(index: dict[str, Any]) -> None:
    claims = [item for item in index.get("claims", []) if isinstance(item, dict)]
    notion_sources = [item for item in index.get("notion_sources", []) if isinstance(item, dict)]
    stats = index.setdefault("stats", {})
    stats["claims_review_required"] = sum(
        1 for item in claims if item.get("verification", {}).get("status") == "review_required"
    )
    stats["claims_verified"] = sum(
        1 for item in claims if item.get("verification", {}).get("status") == "verified"
    )
    stats["claims_rejected"] = sum(
        1 for item in claims if item.get("verification", {}).get("status") == "rejected"
    )
    stats["notion_sources"] = len(notion_sources)
    stats["notion_blocks"] = sum(
        len(item.get("blocks", [])) for item in notion_sources if isinstance(item.get("blocks"), list)
    )


def register_notion_snapshot(
    notion_url: str,
    title: str,
    blocks: list[Any],
    retrieved_via: str,
    sensitivity: str = "S1",
) -> dict[str, Any]:
    canonical_url = _canonical_notion_url(notion_url)
    normalized_title = re.sub(r"\s+", " ", str(title or "")).strip()
    if not normalized_title or len(normalized_title) > 500:
        raise CareerFillError("Notion title must be 1-500 characters")
    if retrieved_via not in {"notion_plugin", "chrome"}:
        raise CareerFillError("retrieved_via must be notion_plugin or chrome")
    if sensitivity not in {"S1", "S2"}:
        raise CareerFillError("Notion sensitivity must be S1 or S2; S3 snapshots are not accepted")
    normalized_blocks = _normalize_notion_blocks(blocks)
    source_id = f"notion_{hashlib.sha256(canonical_url.encode()).hexdigest()[:16]}"
    hash_payload = json.dumps(
        {"url": canonical_url, "title": normalized_title, "blocks": normalized_blocks},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    source_hash = hashlib.sha256(hash_payload.encode()).hexdigest()
    source = {
        "source_id": source_id,
        "url": canonical_url,
        "title": normalized_title,
        "page_id": _notion_page_id(canonical_url),
        "captured_at": utc_now(),
        "retrieved_via": retrieved_via,
        "sensitivity": sensitivity,
        "source_hash": source_hash,
        "status": "snapshot_review_required",
        "blocks": normalized_blocks,
        "notion_write_allowed": False,
    }
    index = _load_or_empty_index()
    previous_claims = {
        item["claim_id"]: item
        for item in index.get("claims", [])
        if isinstance(item, dict) and isinstance(item.get("claim_id"), str)
    }
    retained_claims = [
        item
        for item in previous_claims.values()
        if not any(
            isinstance(ref, dict)
            and ref.get("source_type") == "notion_snapshot"
            and ref.get("notion_source_id") == source_id
            for ref in item.get("source_refs", [])
        )
    ]
    generated_claims = _notion_claim_candidates(source)
    for claim in generated_claims:
        previous = previous_claims.get(claim["claim_id"])
        if previous:
            claim["verification"] = previous.get("verification", claim["verification"])
    index["claims"] = retained_claims + generated_claims
    sources = [
        item for item in index.get("notion_sources", []) if isinstance(item, dict) and item.get("source_id") != source_id
    ]
    sources.append(source)
    index["notion_sources"] = sorted(sources, key=lambda item: item["source_id"])
    index["plugin_version"] = PLUGIN_VERSION
    _recompute_source_stats(index)
    _atomic_json_write(_ensure_data_root() / "index.json", index)
    return {
        "source_id": source_id,
        "url": canonical_url,
        "title": normalized_title,
        "retrieved_via": retrieved_via,
        "sensitivity": sensitivity,
        "source_hash": source_hash,
        "block_count": len(normalized_blocks),
        "claim_candidates": len(generated_claims),
        "status": "snapshot_review_required",
        "notion_write_performed": False,
    }


def list_notion_sources() -> dict[str, Any]:
    index = _load_or_empty_index()
    claims = index.get("claims", [])
    sources: list[dict[str, Any]] = []
    for source in index.get("notion_sources", []):
        if not isinstance(source, dict):
            continue
        source_id = source.get("source_id")
        claim_count = sum(
            1
            for claim in claims
            if isinstance(claim, dict)
            and any(
                isinstance(ref, dict) and ref.get("notion_source_id") == source_id
                for ref in claim.get("source_refs", [])
            )
        )
        sources.append(
            {
                "source_id": source_id,
                "url": source.get("url"),
                "title": source.get("title"),
                "captured_at": source.get("captured_at"),
                "retrieved_via": source.get("retrieved_via"),
                "sensitivity": source.get("sensitivity"),
                "source_hash": source.get("source_hash"),
                "block_count": len(source.get("blocks", [])),
                "claim_count": claim_count,
                "status": source.get("status"),
            }
        )
    return {"sources": sources, "count": len(sources), "notion_write_allowed": False}


def search_notion_blocks(query: str, source_id: str | None = None, limit: int = 20) -> dict[str, Any]:
    terms = _query_terms(query)
    if not terms:
        raise CareerFillError("query must contain at least one searchable term")
    if limit < 1 or limit > 100:
        raise CareerFillError("limit must be between 1 and 100")
    index = _load_or_empty_index()
    ranked: list[tuple[int, dict[str, Any]]] = []
    for source in index.get("notion_sources", []):
        if not isinstance(source, dict) or (source_id and source.get("source_id") != source_id):
            continue
        for block in source.get("blocks", []):
            if not isinstance(block, dict):
                continue
            text = str(block.get("text") or "")
            haystack = text.casefold()
            score = sum(haystack.count(term) for term in terms)
            if score:
                ranked.append(
                    (
                        score,
                        {
                            "source_id": source.get("source_id"),
                            "url": source.get("url"),
                            "title": source.get("title"),
                            "block_id": block.get("block_id"),
                            "block_index": block.get("index"),
                            "type": block.get("type"),
                            "text": text[:4_000],
                            "screenshot_sha256": block.get("screenshot_sha256"),
                            "source_hash": source.get("source_hash"),
                        },
                    )
                )
    ranked.sort(key=lambda item: (-item[0], str(item[1].get("source_id")), int(item[1].get("block_index") or 0)))
    return {"query": query, "source_id": source_id, "blocks": [item[1] for item in ranked[:limit]]}


def _query_terms(query: str) -> list[str]:
    return [term for term in re.split(r"\s+", query.casefold().strip()) if len(term) > 1]


def search_claims(query: str, limit: int = 20, verified_only: bool = False) -> dict[str, Any]:
    if limit < 1 or limit > 100:
        raise CareerFillError("limit must be between 1 and 100")
    index = load_index()
    terms = _query_terms(query)
    ranked: list[tuple[int, dict[str, Any]]] = []
    for claim in index.get("claims", []):
        if verified_only and claim.get("verification", {}).get("status") != "verified":
            continue
        haystack = " ".join(
            [str(claim.get("statement", "")), str(claim.get("category", "")), " ".join(claim.get("skills", []))]
        ).casefold()
        score = sum(3 if term in str(claim.get("statement", "")).casefold() else 1 for term in terms if term in haystack)
        if not terms or score:
            ranked.append((score, claim))
    ranked.sort(key=lambda item: (-item[0], item[1]["claim_id"]))
    return {"query": query, "verified_only": verified_only, "claims": [item[1] for item in ranked[:limit]]}


def review_claim(claim_id: str, status: str, note: str | None = None) -> dict[str, Any]:
    if status not in {"verified", "rejected", "review_required"}:
        raise CareerFillError("status must be verified, rejected, or review_required")
    index = load_index()
    claim = next((item for item in index.get("claims", []) if item.get("claim_id") == claim_id), None)
    if claim is None:
        raise CareerFillError("claim_id was not found")
    claim["verification"] = {
        "status": status,
        "verified_at": utc_now() if status == "verified" else None,
        "review_note": note[:500] if isinstance(note, str) else None,
    }
    _recompute_source_stats(index)
    _atomic_json_write(_ensure_data_root() / "index.json", index)
    return claim


def list_conflicts() -> dict[str, Any]:
    index = load_index()
    return {"conflicts": index.get("conflicts", []), "count": len(index.get("conflicts", []))}


def get_profile() -> dict[str, Any]:
    index = load_index()
    return {"profile": index.get("profile", {}), "conflicts": index.get("conflicts", [])}


def search_evidence(query: str, max_sensitivity: str = "S1", limit: int = 20) -> dict[str, Any]:
    if max_sensitivity not in {"S0", "S1", "S2"}:
        raise CareerFillError("max_sensitivity must be S0, S1, or S2; S3 is never searchable")
    if limit < 1 or limit > 100:
        raise CareerFillError("limit must be between 1 and 100")
    index = load_index()
    terms = _query_terms(query)
    ranked: list[tuple[int, dict[str, Any]]] = []
    for evidence in index.get("evidence", []):
        sensitivity = evidence.get("sensitivity", "S3")
        if sensitivity == "S3":
            continue
        if SENSITIVITY_ORDER.get(sensitivity, 3) > SENSITIVITY_ORDER[max_sensitivity]:
            continue
        haystack = f"{evidence.get('file', '')} {evidence.get('document_type', '')}".casefold()
        content_hashes = set(evidence.get("content_term_hashes", []))
        filename_matches = sum(1 for term in terms if term in haystack)
        content_matches = sum(1 for term in terms if hashlib.sha256(term.encode()).hexdigest()[:16] in content_hashes)
        score = filename_matches * 2 + content_matches
        if not terms or score:
            public_evidence = {key: value for key, value in evidence.items() if key != "content_term_hashes"}
            public_evidence["match_basis"] = {
                "filename_or_type_terms": filename_matches,
                "content_terms": content_matches,
            }
            ranked.append((score, public_evidence))
    ranked.sort(key=lambda item: (-item[0], item[1]["evidence_id"]))
    return {
        "query": query,
        "max_sensitivity": max_sensitivity,
        "attachment_allowed": False,
        "evidence": [item[1] for item in ranked[:limit]],
    }


def _indexed_source(document_id: str) -> tuple[dict[str, Any], dict[str, Any], Path]:
    index = load_index()
    document = next(
        (item for item in index.get("documents", []) if item.get("document_id") == document_id),
        None,
    )
    if not isinstance(document, dict):
        raise CareerFillError("document_id was not found")
    if document.get("sensitivity") == "S3":
        raise CareerFillError("S3 documents cannot be prepared for visual review")
    root = validate_vault_path(str(index.get("vault_path") or ""))
    relative = Path(str(document.get("relative_path") or ""))
    if relative.is_absolute() or ".." in relative.parts:
        raise CareerFillError("indexed document path is unsafe")
    candidate = root
    for part in relative.parts:
        candidate = candidate / part
        if candidate.is_symlink():
            raise CareerFillError("indexed document path now contains a symbolic link")
    try:
        source = candidate.resolve(strict=True)
        source.relative_to(root)
    except (FileNotFoundError, ValueError) as exc:
        raise CareerFillError("indexed document is missing or outside CareerVault") from exc
    expected_hash = document.get("sha256")
    if not isinstance(expected_hash, str) or not expected_hash:
        raise CareerFillError("indexed document has no verified source hash")
    if _sha256(source) != expected_hash:
        raise CareerFillError("document changed after indexing; scan CareerVault again")
    return index, document, source


def prepare_document_visuals(document_id: str, pages: list[int] | None = None) -> dict[str, Any]:
    _, document, source = _indexed_source(document_id)
    suffix = str(document.get("suffix") or "").casefold()
    if suffix not in {".pdf", ".jpg", ".jpeg", ".png"}:
        raise CareerFillError("visual preparation supports PDF, JPG, JPEG, and PNG only")
    output_root = _visual_root(document_id)
    output_root.mkdir(mode=0o700, parents=True, exist_ok=True)
    staged: list[dict[str, Any]] = []
    if suffix == ".pdf":
        try:
            import fitz  # type: ignore
        except ImportError as exc:
            raise CareerFillError("pdf_visual_renderer_unavailable:PyMuPDF") from exc
        pdf = fitz.open(source)
        try:
            if pdf.needs_pass:
                raise CareerFillError("encrypted_pdf_not_supported")
            if pages is None or pages == []:
                selected = list(range(1, min(pdf.page_count, 6) + 1))
            else:
                if not isinstance(pages, list) or len(pages) > 12:
                    raise CareerFillError("pages must contain at most 12 page numbers")
                if any(isinstance(page, bool) or not isinstance(page, int) for page in pages):
                    raise CareerFillError("pages must contain integers")
                selected = sorted(set(pages))
            if not selected or any(page < 1 or page > pdf.page_count for page in selected):
                raise CareerFillError("requested PDF page is outside the document")
            for page_number in selected:
                output = output_root / f"page-{page_number:04d}.png"
                pixmap = pdf.load_page(page_number - 1).get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
                pixmap.save(str(output))
                os.chmod(output, 0o600)
                staged.append(
                    {
                        "page": page_number,
                        "path": str(output),
                        "sha256": _sha256(output),
                        "width": pixmap.width,
                        "height": pixmap.height,
                    }
                )
            page_count = pdf.page_count
        finally:
            pdf.close()
    else:
        if pages not in (None, [], [1]):
            raise CareerFillError("image documents only support page 1")
        output = output_root / f"source{suffix}"
        shutil.copyfile(source, output)
        os.chmod(output, 0o600)
        staged.append({"page": 1, "path": str(output), "sha256": _sha256(output)})
        page_count = 1
    manifest = {
        "schema_version": "careerfill-visual-set-v1",
        "document_id": document_id,
        "relative_path": document.get("relative_path"),
        "source_sha256": document.get("sha256"),
        "prepared_at": utc_now(),
        "page_count": page_count,
        "files": staged,
        "local_only": True,
        "upload_allowed": False,
    }
    _atomic_json_write(output_root / "manifest.json", manifest)
    return manifest


def _normalize_document_visual_observations(
    document: dict[str, Any], manifest: dict[str, Any], observations: list[Any]
) -> list[dict[str, Any]]:
    if not isinstance(observations, list) or not observations or len(observations) > 100:
        raise CareerFillError("observations must contain 1-100 items")
    allowed_pages = {item.get("page") for item in manifest.get("files", []) if isinstance(item, dict)}
    normalized: list[dict[str, Any]] = []
    for position, observation in enumerate(observations, start=1):
        if not isinstance(observation, dict):
            raise CareerFillError("each visual observation must be an object")
        description = re.sub(r"\s+", " ", str(observation.get("description") or "")).strip()
        if not description or len(description) > 1_000:
            raise CareerFillError("visual observation description must be 1-1000 characters")
        page = _optional_int(observation.get("page", 1))
        if page is None or page < 1:
            raise CareerFillError("visual observation page must be a positive integer")
        if page not in allowed_pages:
            raise CareerFillError("visual observation references a page that was not prepared")
        try:
            confidence = float(observation.get("confidence", 0.5))
        except (TypeError, ValueError) as exc:
            raise CareerFillError("visual observation confidence must be numeric") from exc
        if confidence < 0 or confidence > 1:
            raise CareerFillError("visual observation confidence must be between 0 and 1")
        kind = str(observation.get("kind") or "other")[:60]
        seed = f"{document['sha256']}:{page}:{kind}:{description}:{position}"
        normalized.append(
            {
                "observation_id": f"visual_{hashlib.sha256(seed.encode()).hexdigest()[:16]}",
                "page": page,
                "kind": kind,
                "description": description,
                "confidence": confidence,
                "text_corroborated": bool(observation.get("text_corroborated", False)),
                "status": "review_required",
            }
        )
    return normalized


def record_document_visual_review(
    document_id: str,
    observations: list[Any],
    claim_candidates: list[Any] | None = None,
) -> dict[str, Any]:
    index, document, _ = _indexed_source(document_id)
    manifest_path = _visual_root(document_id) / "manifest.json"
    manifest = _load_json(manifest_path)
    if manifest.get("source_sha256") != document.get("sha256"):
        raise CareerFillError("visual set is stale; prepare document visuals again")
    output_root = _visual_root(document_id).resolve()
    for item in manifest.get("files", []):
        if not isinstance(item, dict):
            raise CareerFillError("visual manifest contains an invalid file record")
        try:
            prepared = Path(str(item.get("path") or "")).resolve(strict=True)
            prepared.relative_to(output_root)
        except (FileNotFoundError, ValueError) as exc:
            raise CareerFillError("prepared visual is missing or outside CareerFill data") from exc
        if _sha256(prepared) != item.get("sha256"):
            raise CareerFillError("prepared visual changed after rendering")
    normalized_observations = _normalize_document_visual_observations(document, manifest, observations)
    candidates = claim_candidates or []
    if not isinstance(candidates, list) or len(candidates) > 100:
        raise CareerFillError("claim_candidates must be an array with at most 100 items")
    existing_claims = {
        item["claim_id"]: item
        for item in index.get("claims", [])
        if isinstance(item, dict) and isinstance(item.get("claim_id"), str)
    }
    created_claims: list[dict[str, Any]] = []
    for candidate in candidates:
        if not isinstance(candidate, dict):
            raise CareerFillError("each visual claim candidate must be an object")
        statement = re.sub(r"\s+", " ", str(candidate.get("statement") or "")).strip()
        if len(statement) < 20 or len(statement) > 700 or _contains_direct_identifier(statement):
            raise CareerFillError("visual claim statement must be 20-700 characters and exclude direct identifiers")
        page = _optional_int(candidate.get("page", 1))
        if page is None or page < 1:
            raise CareerFillError("visual claim page must be a positive integer")
        referenced = candidate.get("observation_indexes")
        if not isinstance(referenced, list) or not referenced:
            raise CareerFillError("visual claim must reference at least one 1-based observation_index")
        try:
            indexes = [int(item) for item in referenced[:20]]
        except (TypeError, ValueError) as exc:
            raise CareerFillError("observation_indexes must contain integers") from exc
        if any(item < 1 or item > len(normalized_observations) for item in indexes):
            raise CareerFillError("visual claim references an unknown observation_index")
        referenced_observations = [normalized_observations[item - 1] for item in indexes]
        referenced_ids = [item["observation_id"] for item in referenced_observations]
        if page not in {item["page"] for item in referenced_observations}:
            raise CareerFillError("visual claim page must match a referenced observation page")
        source = {
            "file": document["relative_path"],
            "source_hash": document["sha256"],
            "source_type": "visual_review",
            "page": page,
            "visual_observation_ids": referenced_ids,
        }
        seed = f"{document['sha256']}:{page}:{statement}:{','.join(referenced_ids)}"
        claim_id = f"claim_{hashlib.sha256(seed.encode()).hexdigest()[:16]}"
        previous = existing_claims.get(claim_id)
        claim = {
            "claim_id": claim_id,
            "category": str(candidate.get("category") or _claim_category(statement))[:60],
            "statement": statement,
            "skills": [term for term in SKILL_TERMS if term.casefold() in statement.casefold()],
            "period_tokens": _period_tokens(statement),
            "source_refs": [source],
            "verification": previous.get("verification", {})
            if previous
            else {"status": "review_required", "verified_at": None},
        }
        existing_claims[claim_id] = claim
        created_claims.append(claim)
    visual_review = {
        "schema_version": "careerfill-document-visual-review-v1",
        "recorded_at": utc_now(),
        "source_sha256": document["sha256"],
        "status": "review_required",
        "observations": normalized_observations,
    }
    document["visual_review"] = visual_review
    index["plugin_version"] = PLUGIN_VERSION
    index["claims"] = list(existing_claims.values())
    for evidence in index.get("evidence", []):
        if evidence.get("hash") == f"sha256:{document['sha256']}":
            evidence["visual_review"] = {
                "status": "review_required",
                "observation_count": len(normalized_observations),
                "recorded_at": visual_review["recorded_at"],
            }
    stats = index.setdefault("stats", {})
    stats["visual_reviews"] = sum(
        1 for item in index.get("documents", []) if isinstance(item.get("visual_review"), dict)
    )
    stats["claims_review_required"] = sum(
        1 for item in existing_claims.values() if item.get("verification", {}).get("status") == "review_required"
    )
    stats["claims_verified"] = sum(
        1 for item in existing_claims.values() if item.get("verification", {}).get("status") == "verified"
    )
    stats["claims_rejected"] = sum(
        1 for item in existing_claims.values() if item.get("verification", {}).get("status") == "rejected"
    )
    _atomic_json_write(_ensure_data_root() / "index.json", index)
    return {
        "document_id": document_id,
        "status": "review_required",
        "observations": normalized_observations,
        "claim_candidates": created_claims,
        "source_write_performed": False,
    }


def _validate_tab_lock(tab_lock: dict[str, Any]) -> dict[str, Any]:
    required = ("provider_tab_id", "url", "title", "origin", "page_fingerprint")
    missing = [field for field in required if not isinstance(tab_lock.get(field), str) or not tab_lock[field].strip()]
    if missing:
        raise CareerFillError(f"tab_lock missing required fields: {', '.join(missing)}")
    limits = {"provider_tab_id": 500, "url": 4_000, "title": 500, "origin": 2_000, "page_fingerprint": 71}
    oversized = [field for field, limit in limits.items() if len(tab_lock[field]) > limit]
    if oversized:
        raise CareerFillError(f"tab_lock fields exceed size limits: {', '.join(oversized)}")
    fingerprint = tab_lock["page_fingerprint"]
    if not re.fullmatch(r"(?:sha256:)?[0-9a-fA-F]{64}", fingerprint):
        raise CareerFillError("tab_lock.page_fingerprint must be a SHA-256 value")
    parsed_url = urlparse(tab_lock["url"])
    parsed_origin = urlparse(tab_lock["origin"])
    if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
        raise CareerFillError("tab_lock.url must be an http(s) URL")
    expected_origin = f"{parsed_url.scheme}://{parsed_url.netloc}"
    if f"{parsed_origin.scheme}://{parsed_origin.netloc}" != expected_origin:
        raise CareerFillError("tab_lock.origin must match tab_lock.url")
    return {field: tab_lock[field] for field in required}


def _optional_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return number if number >= 0 else None


def _application_path(session_id: str) -> Path:
    if not re.fullmatch(r"app_[0-9a-f]{20}", session_id):
        raise CareerFillError("invalid application session_id")
    return data_root() / "applications" / f"{session_id}.json"


def _normalize_application_visual_observations(observations: list[Any] | None) -> list[dict[str, Any]]:
    values = observations or []
    if not isinstance(values, list) or not values or len(values) > 100:
        raise CareerFillError("visual_observations must contain 1-100 screenshot observations")
    normalized: list[dict[str, Any]] = []
    for position, observation in enumerate(values, start=1):
        if not isinstance(observation, dict):
            raise CareerFillError("each application visual observation must be an object")
        description = re.sub(r"\s+", " ", str(observation.get("description") or "")).strip()
        if not description or len(description) > 1_000:
            raise CareerFillError("application visual description must be 1-1000 characters")
        severity = str(observation.get("severity") or "info")
        if severity not in {"info", "warning", "blocking"}:
            raise CareerFillError("visual severity must be info, warning, or blocking")
        try:
            confidence = float(observation.get("confidence", 0.5))
        except (TypeError, ValueError) as exc:
            raise CareerFillError("application visual confidence must be numeric") from exc
        if confidence < 0 or confidence > 1:
            raise CareerFillError("application visual confidence must be between 0 and 1")
        screenshot_sha256 = str(observation.get("screenshot_sha256") or "")
        if not screenshot_sha256 or not re.fullmatch(r"(?:sha256:)?[0-9a-fA-F]{64}", screenshot_sha256):
            raise CareerFillError("screenshot_sha256 must be a SHA-256 value")
        scope = str(observation.get("scope") or "page")[:200]
        kind = str(observation.get("kind") or "other")[:60]
        seed = f"{scope}:{kind}:{description}:{screenshot_sha256}:{position}"
        normalized.append(
            {
                "observation_id": f"appvisual_{hashlib.sha256(seed.encode()).hexdigest()[:16]}",
                "scope": scope,
                "kind": kind,
                "description": description,
                "severity": severity,
                "confidence": confidence,
                "dom_corroborated": bool(observation.get("dom_corroborated", False)),
                "screenshot_sha256": screenshot_sha256 or None,
                "resolved": bool(observation.get("resolved", False)),
            }
        )
    return normalized


def create_application_session(
    tab_lock: dict[str, Any],
    job: dict[str, Any],
    fields: list[dict[str, Any]],
    visual_observations: list[Any] | None = None,
) -> dict[str, Any]:
    lock = _validate_tab_lock(tab_lock)
    if not isinstance(job, dict) or not isinstance(fields, list):
        raise CareerFillError("job must be an object and fields must be an array")
    if len(fields) > 500:
        raise CareerFillError("application field limit exceeded")
    if not str(job.get("company") or "").strip() or not str(job.get("role") or "").strip():
        raise CareerFillError("job.company and job.role must be confirmed before saving a session")
    normalized_visuals = _normalize_application_visual_observations(visual_observations)
    seed = f"{lock['provider_tab_id']}:{lock['url']}:{lock['page_fingerprint']}:{utc_now()}"
    session_id = f"app_{hashlib.sha256(seed.encode()).hexdigest()[:20]}"
    normalized_fields: list[dict[str, Any]] = []
    for index, field in enumerate(fields, start=1):
        if not isinstance(field, dict):
            raise CareerFillError("each field must be an object")
        normalized_fields.append(
            {
                "field_id": str(field.get("field_id") or f"field_{index}"),
                "label": str(field.get("label") or "")[:500],
                "type": str(field.get("type") or "unknown")[:100],
                "required": bool(field.get("required", False)),
                "min_length": _optional_int(field.get("min_length")),
                "max_length": _optional_int(field.get("max_length")),
                "length_unit": str(field.get("length_unit") or "characters"),
                "helper_text": str(field.get("helper_text") or "")[:1_000],
                "current_value_present": bool(field.get("current_value")),
            }
        )
    payload = {
        "schema_version": "careerfill-application-v1",
        "session_id": session_id,
        "created_at": utc_now(),
        "stage": "analyzed",
        "tab_lock": lock,
        "job": {
            "company": str(job.get("company") or "")[:300],
            "role": str(job.get("role") or "")[:300],
            "posting_url": str(job.get("posting_url") or lock["url"])[:4_000],
        },
        "fields": normalized_fields,
        "visual_observations": normalized_visuals,
        "draft": None,
        "browser_write_allowed": False,
        "attachment_allowed": False,
        "submission_allowed": False,
    }
    path = _application_path(session_id)
    _atomic_json_write(path, payload)
    return {
        "session_id": session_id,
        "stage": "analyzed",
        "field_count": len(normalized_fields),
        "visual_observation_count": len(normalized_visuals),
        "job": payload["job"],
    }


def get_application_session(session_id: str) -> dict[str, Any]:
    return _load_json(_application_path(session_id))


def _length(text: str, unit: str) -> int:
    if unit == "utf8_bytes":
        return len(text.encode("utf-8"))
    return len(text)


def _normalize_answers(answers: list[Any]) -> list[dict[str, Any]]:
    def string_list(value: Any, item_limit: int) -> list[str]:
        if not isinstance(value, list):
            return []
        return [str(item)[:item_limit] for item in value[:100]]

    normalized: list[dict[str, Any]] = []
    for answer in answers:
        if not isinstance(answer, dict):
            raise CareerFillError("each answer must be an object")
        text = str(answer.get("answer") or "")
        if len(text) > 50_000:
            raise CareerFillError("answer text exceeds 50000 characters")
        normalized.append(
            {
                "field_id": str(answer.get("field_id") or "")[:200],
                "kind": str(answer.get("kind") or "narrative")[:30],
                "answer": text,
                "used_claims": string_list(answer.get("used_claims"), 200),
                "source_keys": string_list(answer.get("source_keys"), 500),
                "unsupported_claims": string_list(answer.get("unsupported_claims"), 500),
            }
        )
    return normalized


def _draft_issues(session: dict[str, Any], answers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    index = load_index()
    claims = {item["claim_id"]: item for item in index.get("claims", [])}
    fields = {item["field_id"]: item for item in session.get("fields", [])}
    issues: list[dict[str, Any]] = []
    seen_fields: set[str] = set()
    claim_usage: dict[str, list[str]] = {}
    for observation in session.get("visual_observations", []):
        if not isinstance(observation, dict):
            continue
        if observation.get("severity") == "blocking" and not observation.get("resolved", False):
            issues.append(
                {
                    "type": "visual_blocker_unresolved",
                    "observation_id": observation.get("observation_id"),
                    "scope": observation.get("scope"),
                    "description": observation.get("description"),
                }
            )
        if observation.get("severity") in {"warning", "blocking"} and not observation.get("dom_corroborated", False):
            issues.append(
                {
                    "type": "visual_state_not_dom_corroborated",
                    "observation_id": observation.get("observation_id"),
                    "scope": observation.get("scope"),
                }
            )
    for answer in answers:
        field_id = str(answer.get("field_id") or "")
        if field_id not in fields:
            issues.append({"type": "unknown_field", "field_id": field_id})
            continue
        if field_id in seen_fields:
            issues.append({"type": "duplicate_field_answer", "field_id": field_id})
        seen_fields.add(field_id)
        field = fields[field_id]
        text = str(answer.get("answer") or "")
        kind = str(answer.get("kind") or "narrative")
        used_claims = answer.get("used_claims") if isinstance(answer.get("used_claims"), list) else []
        source_keys = answer.get("source_keys") if isinstance(answer.get("source_keys"), list) else []
        unsupported = answer.get("unsupported_claims") if isinstance(answer.get("unsupported_claims"), list) else []
        if field.get("required") and not text.strip():
            issues.append({"type": "required_field_empty", "field_id": field_id})
        if kind not in {"factual", "narrative", "manual"}:
            issues.append({"type": "unknown_answer_kind", "field_id": field_id, "kind": kind})
        if kind == "manual":
            issues.append({"type": "manual_answer_requires_user_action", "field_id": field_id})
        if kind == "narrative" and not used_claims:
            issues.append({"type": "narrative_without_claim", "field_id": field_id})
        if kind == "factual" and not source_keys:
            issues.append({"type": "factual_without_profile_source", "field_id": field_id})
        for claim_id in used_claims:
            claim = claims.get(str(claim_id))
            if not claim:
                issues.append({"type": "claim_not_found", "field_id": field_id, "claim_id": claim_id})
            elif claim.get("verification", {}).get("status") != "verified":
                issues.append({"type": "claim_not_verified", "field_id": field_id, "claim_id": claim_id})
            claim_usage.setdefault(str(claim_id), []).append(field_id)
        if unsupported:
            issues.append({"type": "unsupported_claims_present", "field_id": field_id, "items": unsupported})
        unit = field.get("length_unit") or "characters"
        actual = _length(text, unit)
        minimum = field.get("min_length")
        maximum = field.get("max_length")
        if isinstance(minimum, int) and actual < minimum:
            issues.append({"type": "below_min_length", "field_id": field_id, "actual": actual, "minimum": minimum, "unit": unit})
        if isinstance(maximum, int) and actual > maximum:
            issues.append({"type": "above_max_length", "field_id": field_id, "actual": actual, "maximum": maximum, "unit": unit})
        elif isinstance(maximum, int) and maximum > 100 and actual > int(maximum * 0.98):
            issues.append({"type": "near_max_length", "field_id": field_id, "actual": actual, "maximum": maximum, "unit": unit})
        label = f"{field.get('label', '')} {field.get('helper_text', '')}"
        if any(marker in label for marker in MANUAL_FIELD_MARKERS):
            issues.append({"type": "manual_sensitive_or_legal_field", "field_id": field_id})
    for field in fields.values():
        if field.get("required") and field["field_id"] not in seen_fields:
            issues.append({"type": "required_field_missing", "field_id": field["field_id"]})
    for claim_id, field_ids in claim_usage.items():
        if len(set(field_ids)) > 1:
            issues.append({"type": "claim_reused_across_answers", "claim_id": claim_id, "field_ids": sorted(set(field_ids))})
    return issues


def save_application_draft(
    session_id: str, tab_fingerprint: str, answers: list[dict[str, Any]]
) -> dict[str, Any]:
    session = get_application_session(session_id)
    if tab_fingerprint != session.get("tab_lock", {}).get("page_fingerprint"):
        raise CareerFillError("tab fingerprint changed; create a new read-only analysis session")
    if not isinstance(answers, list):
        raise CareerFillError("answers must be an array")
    if len(answers) > 500:
        raise CareerFillError("application answer limit exceeded")
    normalized_answers = _normalize_answers(answers)
    issues = _draft_issues(session, normalized_answers)
    session["stage"] = "drafted"
    session["draft"] = {
        "saved_at": utc_now(),
        "answers": normalized_answers,
        "issues": issues,
        "ready_for_browser_write": False,
    }
    _atomic_json_write(_application_path(session_id), session)
    return {"session_id": session_id, "stage": "drafted", "answer_count": len(normalized_answers), "issues": issues, "ready_for_browser_write": False}


def review_application_draft(session_id: str) -> dict[str, Any]:
    session = get_application_session(session_id)
    draft = session.get("draft")
    if not isinstance(draft, dict):
        raise CareerFillError("application draft has not been saved")
    answers = draft.get("answers") if isinstance(draft.get("answers"), list) else []
    issues = _draft_issues(session, answers)
    return {
        "session_id": session_id,
        "job": session.get("job"),
        "answer_count": len(answers),
        "visual_observation_count": len(session.get("visual_observations", [])),
        "issues": issues,
        "passed": not issues,
        "browser_write_allowed": False,
        "attachment_allowed": False,
        "submission_allowed": False,
    }


def doctor() -> dict[str, Any]:
    modules: dict[str, bool] = {}
    for module in ("fitz", "yaml"):
        try:
            __import__(module)
            modules[module] = True
        except ImportError:
            modules[module] = False
    return {
        "plugin": "careerfill",
        "version": PLUGIN_VERSION,
        "python": os.sys.version.split()[0],
        "data_root": str(data_root()),
        "optional_modules": modules,
        "formats": {
            "pdf": "text_and_visual_available" if modules["fitz"] else "catalog_only",
            "docx": "text_and_structure_available",
            "hwpx": "text_and_structure_available",
            "md_txt": "available",
            "jpg_png": "local_visual_review_available_no_external_ocr",
        },
        "visual_analysis": {
            "documents": ["pdf", "jpg", "jpeg", "png"],
            "application": "chrome_dom_plus_screenshot",
            "automatic_verification": False,
        },
        "notion": {
            "accepted_hosts": ["notion.so", "notion.site", "notion.com"],
            "retrieval": ["notion_plugin", "chrome"],
            "direct_network_fetch": False,
            "write_allowed": False,
        },
        "database_used": False,
        "browser_write_allowed": True,
        "browser_write_scope": "explicit_user_request_fields_only",
        "browser_write_requires_confirmation_policy": True,
        "attachment_allowed": False,
        "save_submit_allowed": False,
        "submission_allowed": False,
    }
