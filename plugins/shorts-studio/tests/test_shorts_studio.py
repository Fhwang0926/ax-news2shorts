from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
import wave
from pathlib import Path

from PIL import Image, ImageDraw


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
CLI = PLUGIN_ROOT / "scripts" / "shorts_studio.py"
SPEC = importlib.util.spec_from_file_location("shorts_studio", CLI)
assert SPEC and SPEC.loader
STUDIO = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(STUDIO)


class ShortsStudioTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="shorts-studio-tests-")
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

    def _make_video(self, path: Path) -> None:
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=0x356A8A:s=720x1280:r=30:d=3",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", str(path),
        ], check=True, capture_output=True)

    def _run(self, *arguments: str, ok: bool = True) -> subprocess.CompletedProcess[str]:
        result = subprocess.run([sys.executable, str(CLI), *arguments], text=True, capture_output=True)
        if ok and result.returncode != 0:
            self.fail(f"command failed: {' '.join(arguments)}\nstdout={result.stdout}\nstderr={result.stderr}")
        if not ok and result.returncode == 0:
            self.fail(f"command unexpectedly passed: {' '.join(arguments)}")
        return result

    def _write_input(self, mode: str) -> Path:
        common = {
            "schema_version": 1,
            "slug": f"fixture-{mode}",
            "title": {"story": "강아지가 문 앞에서 멈춘 이유", "romance": "답장이 늦을 때 보이는 신호", "price": "한 그릇 가격을 다시 계산했습니다"}[mode],
            "rights": {"status": "owned", "permission_reference": "fixture-owned"},
            "audio": {"path": self.audio.name, "provider": "typecast"},
        }
        if mode == "story":
            source = self.root / "source.mp4"
            self._make_video(source)
            common.update({
                "source_video": source.name,
                "source_rights": "owned",
                "scenes": [
                    {"source_start": 0, "source_end": 1, "observed_action": "강아지가 문 앞에서 고개를 든다", "headline": "갑자기 멈춘 강아지", "caption": "문밖에서 소리가 났다", "narration": "문밖에서 작은 소리가 들렸습니다."},
                    {"source_start": 1, "source_end": 2, "observed_action": "강아지가 꼬리를 흔들며 문을 바라본다", "headline": "기다리던 사람이 왔다", "caption": "꼬리가 먼저 알아봤다", "narration": "꼬리가 먼저 반가운 사람을 알아봤습니다."},
                ],
            })
        elif mode == "romance":
            first = self.root / "romance-a.png"
            second = self.root / "romance-b.png"
            self._make_image(first, "#3D345E", "A")
            self._make_image(second, "#68405D", "B")
            common["scenes"] = [
                {"duration": 1, "visual": first.name, "rights_status": "owned", "synthetic": True, "speaker": "다은", "dialogue": "왜 답장이 늦었어?", "caption": "왜 답장이 늦었어?", "narration": "왜 답장이 늦었어?"},
                {"duration": 1, "visual": second.name, "rights_status": "owned", "synthetic": True, "speaker": "필재", "dialogue": "답을 고르고 있었어.", "caption": "답을 고르고 있었어", "narration": "답을 고르고 있었어."},
            ]
        else:
            evidence = self.root / "price.png"
            self._make_image(evidence, "#E9D894", "PRICE")
            common.update({
                "menu_price": "8000",
                "components": [
                    {"name": "면", "package_price": "3000", "package_quantity": "1000", "quantity_used": "200", "unit": "g", "delivery_fee": "0", "applied_discounts": []},
                    {"name": "소스", "package_price": "5000", "package_quantity": "500", "quantity_used": "50", "unit": "g", "delivery_fee": "3000", "delivery_unavoidable": True, "applied_discounts": []},
                ],
                "evidence": [
                    {"id": "evidence-01", "source": "fixture price page", "captured_at": "2026-08-26T12:00:00+09:00", "price_conditions_visible": True, "rights_status": "owned", "path": evidence.name, "synthetic": True}
                ],
            })
        target = self.root / f"{mode}.json"
        target.write_text(json.dumps(common, ensure_ascii=False, indent=2), encoding="utf-8")
        return target

    def _full_flow(self, mode: str) -> Path:
        source = self._write_input(mode)
        project = self.root / "projects" / mode
        self._run(mode, "init", "--input", str(source), "--project-dir", str(project))
        self._run(mode, "approve", "--project-dir", str(project), "--stage", "assets", "--confirm-assets")
        content_args = [mode, "approve", "--project-dir", str(project), "--stage", "content", "--confirm-content"]
        if mode == "romance":
            content_args.append("--confirm-synthetic-disclosure")
        self._run(*content_args)
        self._run(mode, "render", "--project-dir", str(project), "--draft", "--no-tts")
        self._run(mode, "approve", "--project-dir", str(project), "--stage", "publish", "--confirm-publish")
        self._run(mode, "validate", "--project-dir", str(project), "--publish-ready")
        self._run(mode, "render", "--project-dir", str(project), "--final")
        self._run(mode, "upload-package", "--project-dir", str(project))
        return project

    def test_three_mode_render_and_package(self) -> None:
        for mode in ("story", "romance", "price"):
            with self.subTest(mode=mode):
                project = self._full_flow(mode)
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

    def test_price_decimal_delivery_rounding_and_coupon_rejection(self) -> None:
        result = STUDIO.calculate_price({
            "menu_price": "8000",
            "components": [{
                "name": "면", "package_price": "3000", "package_quantity": "1", "quantity_used": "0.2",
                "unit": "kg", "used_unit": "kg", "delivery_fee": "3000", "delivery_unavoidable": True,
                "applied_discounts": [],
            }],
        })
        self.assertEqual(result["exact_material_cost"], "3600.00")
        self.assertEqual(result["display_material_cost"], "3600")
        with self.assertRaises(STUDIO.ShortsStudioError):
            STUDIO.calculate_price({
                "menu_price": "8000",
                "components": [{
                    "name": "면", "package_price": "3000", "package_quantity": "1", "quantity_used": "0.2",
                    "unit": "kg", "applied_discounts": ["coupon"],
                }],
            })

    def test_legacy_input_is_rejected(self) -> None:
        source = self._write_input("story")
        payload = json.loads(source.read_text(encoding="utf-8"))
        payload["plugin"] = "story2short"
        source.write_text(json.dumps(payload), encoding="utf-8")
        result = self._run("story", "init", "--input", str(source), "--project-dir", str(self.root / "legacy"), ok=False)
        self.assertIn("호환하거나 가져오지 않습니다", result.stderr)

    def test_review_rights_and_missing_typecast_block_publish(self) -> None:
        source = self._write_input("story")
        payload = json.loads(source.read_text(encoding="utf-8"))
        payload["rights"]["status"] = "review_required"
        payload["source_rights"] = "review_required"
        payload["audio"]["provider"] = "local"
        source.write_text(json.dumps(payload), encoding="utf-8")
        project = self.root / "blocked"
        self._run("story", "init", "--input", str(source), "--project-dir", str(project))
        self._run("story", "approve", "--project-dir", str(project), "--stage", "assets", "--confirm-assets")
        self._run("story", "approve", "--project-dir", str(project), "--stage", "content", "--confirm-content")
        self._run("story", "render", "--project-dir", str(project), "--draft", "--no-tts")
        result = self._run("story", "approve", "--project-dir", str(project), "--stage", "publish", "--confirm-publish", ok=False)
        self.assertIn("게시 가능한", result.stderr)


if __name__ == "__main__":
    unittest.main()
