from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
import wave
from pathlib import Path

from PIL import Image, ImageDraw


PLUGIN_ROOT = Path(__file__).resolve().parents[2]
CLI = PLUGIN_ROOT / "scripts" / "romance.py"


class ShortsStudioTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="shorts-suite-romance-tests-")
        self.root = Path(self.temp.name)
        self.audio = self.root / "typecast.wav"
        self._make_audio(self.audio, 10.0)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _make_audio(self, path: Path, duration: float) -> None:
        sample_rate = 48_000
        with wave.open(str(path), "wb") as handle:
            handle.setnchannels(1)
            handle.setsampwidth(2)
            handle.setframerate(sample_rate)
            frames = bytearray()
            for index in range(int(sample_rate * duration)):
                value = 1800 if (index // 240) % 2 else -1800
                frames += int(value).to_bytes(2, "little", signed=True)
            handle.writeframes(frames)

    def _make_image(self, path: Path, color: str, text: str) -> None:
        image = Image.new("RGB", (720, 1280), color)
        draw = ImageDraw.Draw(image)
        draw.rectangle((80, 450, 640, 830), fill="#FFFFFF")
        draw.text((120, 610), text, fill="#111111")
        image.save(path)

    def _run(self, *arguments: str, ok: bool = True) -> subprocess.CompletedProcess[str]:
        result = subprocess.run([sys.executable, str(CLI), *arguments], text=True, capture_output=True)
        if ok and result.returncode != 0:
            self.fail(f"command failed: {' '.join(arguments)}\nstdout={result.stdout}\nstderr={result.stderr}")
        if not ok and result.returncode == 0:
            self.fail(f"command unexpectedly passed: {' '.join(arguments)}")
        return result

    def _write_input(self) -> Path:
        common = {
            "schema_version": 1,
            "slug": "fixture-romance",
            "title": "답장이 늦을 때 보이는 신호",
            "rights": {"status": "owned", "permission_reference": "fixture-owned"},
            "audio": {"path": self.audio.name, "provider": "typecast"},
        }
        first = self.root / "romance-a.png"
        second = self.root / "romance-b.png"
        self._make_image(first, "#3D345E", "A")
        self._make_image(second, "#68405D", "B")
        common["scenes"] = [
            {"duration": 1, "visual": first.name, "rights_status": "owned", "synthetic": True, "speaker": "다은", "dialogue": "왜 답장이 늦었어?", "caption": "왜 답장이 늦었어?", "narration": "왜 답장이 늦었어?"},
            {"duration": 1, "visual": second.name, "rights_status": "owned", "synthetic": True, "speaker": "필재", "dialogue": "답을 고르고 있었어.", "caption": "답을 고르고 있었어", "narration": "답을 고르고 있었어."},
        ]
        target = self.root / "romance.json"
        target.write_text(json.dumps(common, ensure_ascii=False, indent=2), encoding="utf-8")
        return target

    def _full_flow(self) -> Path:
        source = self._write_input()
        project = self.root / "projects" / "romance"
        self._run("romance", "init", "--input", str(source), "--project-dir", str(project))
        self._run("romance", "approve", "--project-dir", str(project), "--stage", "assets", "--confirm-assets")
        self._run("romance", "approve", "--project-dir", str(project), "--stage", "content", "--confirm-content", "--confirm-synthetic-disclosure")
        self._run("romance", "render", "--project-dir", str(project), "--draft", "--no-tts")
        self._run("romance", "approve", "--project-dir", str(project), "--stage", "publish", "--confirm-publish")
        self._run("romance", "validate", "--project-dir", str(project), "--publish-ready")
        self._run("romance", "render", "--project-dir", str(project), "--final")
        self._run("romance", "upload-package", "--project-dir", str(project))
        return project

    def test_romance_render_and_package(self) -> None:
        project = self._full_flow()
        self.assertTrue((project / "outputs" / "review.mp4").is_file())
        self.assertTrue((project / "outputs" / "short.mp4").is_file())
        self.assertTrue((project / "thumbnail.jpg").is_file())
        self.assertTrue((project / "captions.srt").is_file())
        self.assertTrue((project / "youtube-upload.json").is_file())
        report = json.loads((project / "render-report.json").read_text(encoding="utf-8"))
        video = next(item for item in report["media"]["streams"] if item["codec_type"] == "video")
        audio = next(item for item in report["media"]["streams"] if item["codec_type"] == "audio")
        self.assertEqual((video["width"], video["height"], video["codec_name"]), (720, 1280, "h264"))
        self.assertEqual(audio["codec_name"], "aac")
        review_probe = subprocess.run([
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=width,height", "-of", "json",
            str(project / "outputs" / "review.mp4"),
        ], check=True, text=True, capture_output=True)
        review_stream = json.loads(review_probe.stdout)["streams"][0]
        self.assertEqual((review_stream["width"], review_stream["height"]), (540, 960))
        final_path = project / "outputs" / "short.mp4"
        black = subprocess.run([
            "ffmpeg", "-v", "info", "-i", str(final_path),
            "-vf", "blackdetect=d=0.20:pic_th=0.98", "-an", "-f", "null", "-",
        ], check=True, text=True, capture_output=True)
        self.assertNotIn("black_start", black.stderr)
        silence = subprocess.run([
            "ffmpeg", "-v", "info", "-i", str(final_path),
            "-af", "silencedetect=n=-45dB:d=0.50", "-vn", "-f", "null", "-",
        ], check=True, text=True, capture_output=True)
        self.assertNotIn("silence_start", silence.stderr)

    def test_removed_modes_are_not_registered(self) -> None:
        for mode in ("story", "price"):
            with self.subTest(mode=mode):
                result = self._run(mode, "init", "--input", "unused.json", "--project-dir", "unused", ok=False)
                self.assertIn("invalid choice", result.stderr)

    def test_legacy_input_is_rejected(self) -> None:
        source = self._write_input()
        payload = json.loads(source.read_text(encoding="utf-8"))
        payload["plugin"] = "romance-drama-shorts"
        source.write_text(json.dumps(payload), encoding="utf-8")
        result = self._run("romance", "init", "--input", str(source), "--project-dir", str(self.root / "legacy"), ok=False)
        self.assertIn("호환하거나 가져오지 않습니다", result.stderr)

    def test_review_rights_and_missing_typecast_block_publish(self) -> None:
        source = self._write_input()
        payload = json.loads(source.read_text(encoding="utf-8"))
        payload["rights"]["status"] = "review_required"
        payload["audio"]["provider"] = "local"
        source.write_text(json.dumps(payload), encoding="utf-8")
        project = self.root / "blocked"
        self._run("romance", "init", "--input", str(source), "--project-dir", str(project))
        self._run("romance", "approve", "--project-dir", str(project), "--stage", "assets", "--confirm-assets")
        self._run("romance", "approve", "--project-dir", str(project), "--stage", "content", "--confirm-content", "--confirm-synthetic-disclosure")
        self._run("romance", "render", "--project-dir", str(project), "--draft", "--no-tts")
        result = self._run("romance", "approve", "--project-dir", str(project), "--stage", "publish", "--confirm-publish", ok=False)
        self.assertIn("게시 가능한", result.stderr)


if __name__ == "__main__":
    unittest.main()
