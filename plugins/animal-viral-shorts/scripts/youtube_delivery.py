from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

CTA_TAIL_SECONDS = 1.8


class YouTubeDeliveryError(RuntimeError):
    pass


def _centered_text(draw: Any, xy_y: int, value: str, font: Any, fill: str, width: int) -> None:
    box = draw.textbbox((0, 0), value, font=font)
    draw.text(((width - (box[2] - box[0])) / 2, xy_y), value, font=font, fill=fill)


def append_cta_tail(
    input_path: Path,
    output_path: Path,
    *,
    width: int,
    height: int,
    source_duration: float,
    has_audio: bool,
    font_path: Path | None,
    headline: str,
    prompt: str,
    ffmpeg: str,
    duration: float = CTA_TAIL_SECONDS,
) -> dict[str, Any]:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as exc:
        raise YouTubeDeliveryError("CTA 샷 생성에는 Pillow가 필요합니다.") from exc
    frame = output_path.with_suffix(".png")
    image = Image.new("RGB", (width, height), "#07090D")
    draw = ImageDraw.Draw(image)
    headline_font = ImageFont.truetype(str(font_path), max(42, round(width * 0.072))) if font_path else ImageFont.load_default()
    prompt_font = ImageFont.truetype(str(font_path), max(52, round(width * 0.098))) if font_path else ImageFont.load_default()
    accent = "#FFD83D"
    line_y = round(height * 0.37)
    draw.rounded_rectangle((round(width * 0.28), line_y, round(width * 0.72), line_y + max(8, round(height * 0.008))), radius=8, fill=accent)
    _centered_text(draw, round(height * 0.43), headline, headline_font, "#F5F7FA", width)
    _centered_text(draw, round(height * 0.53), prompt, prompt_font, accent, width)
    image.save(frame, format="PNG", optimize=True)

    command = [ffmpeg, "-hide_banner", "-loglevel", "error", "-i", str(input_path), "-loop", "1", "-framerate", "30", "-t", f"{duration:.3f}", "-i", str(frame)]
    if has_audio:
        command.extend(["-f", "lavfi", "-t", f"{duration:.3f}", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000"])
        base_audio, cta_audio = "[0:a]", "[2:a]"
    else:
        command.extend(["-f", "lavfi", "-t", f"{source_duration:.3f}", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000", "-f", "lavfi", "-t", f"{duration:.3f}", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000"])
        base_audio, cta_audio = "[2:a]", "[3:a]"
    filters = (
        f"[0:v]fps=30,scale={width}:{height},setsar=1,format=yuv420p,setpts=PTS-STARTPTS[v0];"
        f"{base_audio}atrim=duration={source_duration:.3f},aresample=48000,aformat=channel_layouts=stereo,asetpts=PTS-STARTPTS[a0];"
        f"[1:v]fps=30,scale={width}:{height},trim=duration={duration:.3f},setsar=1,format=yuv420p[v1];"
        f"{cta_audio}atrim=duration={duration:.3f},aresample=48000,aformat=channel_layouts=stereo,asetpts=PTS-STARTPTS[a1];"
        "[v0][a0][v1][a1]concat=n=2:v=1:a=1[v][a]"
    )
    command.extend(["-filter_complex", filters, "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-r", "30", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2", "-movflags", "+faststart", "-y", str(output_path)])
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, check=False)
    frame.unlink(missing_ok=True)
    if result.returncode or not output_path.is_file():
        raise YouTubeDeliveryError(f"CTA 샷 연결 실패: {result.stdout[-1000:]}")
    return {"enabled": True, "duration_seconds": duration, "headline": headline, "prompt": prompt, "audio": "silent", "placement": "after_conclusion_once"}


def format_upload_package(payload: dict[str, Any]) -> str:
    settings = payload["upload_settings"]
    tags = ", ".join(payload.get("tags", [])) or "미작성"
    review = payload.get("review_required", [])
    return "\n".join([
        "## YouTube 업로드 정보",
        "",
        f"- 영상: {payload['video_path']}",
        f"- 제목 ({len(payload['title'])}/100): {payload['title']}",
        f"- 태그: {tags}",
        f"- 썸네일: {payload['thumbnail_note']}",
        f"- 재생목록: {settings['playlist']}",
        f"- 시청자층: {settings['audience']}",
        f"- 카테고리: {settings['category']}",
        f"- 영상 언어: {settings['video_language']}",
        f"- 변경·합성 콘텐츠: {settings['altered_content']}",
        f"- 유료 프로모션: {settings['paid_promotion']}",
        f"- 연령 제한: {settings['age_restriction']}",
        f"- 댓글: {settings['comments']}",
        f"- 공개 상태: {settings['visibility']}",
        f"- 예약 시간: {settings['schedule_at'] or '미설정'}",
        "",
        f"### 설명 ({len(payload['description'])}/5000)",
        "",
        payload["description"],
        "",
        "### 고정 댓글",
        "",
        payload["pinned_comment"],
        "",
        "### 게시 전 검토",
        "",
        *(f"- {item}" for item in review),
    ]) + "\n"


def write_upload_package(
    project_dir: Path,
    *,
    video_path: str,
    title: str,
    description: str,
    tags: list[str],
    thumbnail_note: str,
    playlist: str,
    category: str,
    language: str,
    pinned_comment: str,
    rights_status: str,
    synthetic_elements: bool,
    generated_at: str,
    output_dir: Path | None = None,
    preserve_existing_description: bool = True,
) -> tuple[Path, Path, dict[str, Any]]:
    target = output_dir or project_dir
    target.mkdir(parents=True, exist_ok=True)
    json_path = target / "youtube-upload.json"
    md_path = target / "youtube-upload.md"
    review = ["시청자층을 최종 확인하세요.", "변경·합성 콘텐츠 공개 여부를 최종 확인하세요.", "유료 프로모션과 연령 제한을 최종 확인하세요."]
    if rights_status not in {"owned", "licensed", "permission_confirmed", "public_domain"}:
        review.insert(0, f"원본 권리 상태가 {rights_status or 'unknown'}입니다. 게시 권리를 확인하세요.")
    defaults: dict[str, Any] = {
        "version": 1,
        "generated_at": generated_at,
        "video_path": video_path,
        "title": (title.strip() or "YouTube Shorts")[:100],
        "description": description.strip()[:5000],
        "tags": [value.strip() for value in tags if value.strip()],
        "thumbnail_note": thumbnail_note.strip(),
        "pinned_comment": pinned_comment.strip(),
        "rights_status": rights_status or "unknown",
        "synthetic_elements": bool(synthetic_elements),
        "upload_settings": {
            "playlist": playlist,
            "audience": "검토 필요",
            "category": category,
            "video_language": language,
            "altered_content": "검토 필요",
            "paid_promotion": "검토 필요",
            "age_restriction": "검토 필요",
            "comments": "허용",
            "visibility": "비공개",
            "schedule_at": "",
        },
        "review_required": review,
        "upload_performed": False,
    }
    if json_path.is_file():
        try:
            existing = json.loads(json_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            existing = None
        if isinstance(existing, dict):
            for key in ("title", "description", "tags", "thumbnail_note", "pinned_comment"):
                if key == "description" and not preserve_existing_description:
                    continue
                if existing.get(key):
                    defaults[key] = existing[key]
            if isinstance(existing.get("upload_settings"), dict):
                defaults["upload_settings"].update(existing["upload_settings"])
    json_path.write_text(json.dumps(defaults, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(format_upload_package(defaults), encoding="utf-8")
    return json_path, md_path, defaults


def read_upload_package(path: Path) -> tuple[dict[str, Any], str]:
    if not path.is_file():
        raise YouTubeDeliveryError(f"YouTube 업로드 정보가 없습니다: {path}. 먼저 영상을 렌더링하세요.")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise YouTubeDeliveryError(f"YouTube 업로드 정보를 읽을 수 없습니다: {path}") from exc
    if not isinstance(payload, dict):
        raise YouTubeDeliveryError("YouTube 업로드 정보의 최상위 값은 객체여야 합니다.")
    return payload, format_upload_package(payload)
