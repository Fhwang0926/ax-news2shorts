from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from unittest import mock
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "news2shorts.py"
SPEC = importlib.util.spec_from_file_location("news2shorts_module", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class RetentionV16Tests(unittest.TestCase):
    def init_project(
        self,
        *,
        delivery_mode: str,
        duration: int | None = None,
        mid_cta_mode: str | None = None,
    ) -> dict:
        with tempfile.TemporaryDirectory() as temp_name:
            project_dir = Path(temp_name) / "project"
            arguments = [
                "init",
                "--title",
                "유지율 테스트",
                "--project-dir",
                str(project_dir),
                "--delivery-mode",
                delivery_mode,
                "--format-reason",
                "유지율 계약을 확인하는 테스트 프로젝트입니다.",
                "--format-confidence",
                "high",
            ]
            if duration is not None:
                arguments.extend(["--duration", str(duration)])
            if mid_cta_mode is not None:
                arguments.extend(["--mid-cta-mode", mid_cta_mode])
            args = MODULE.build_parser().parse_args(arguments)
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(args.handler(args), 0)
            return json.loads((project_dir / "project.json").read_text(encoding="utf-8"))

    def test_continuous_flow_defaults_to_twenty_seconds_and_corner_logo(self) -> None:
        project = self.init_project(delivery_mode=MODULE.CONTINUOUS_FLOW_MODE)
        self.assertEqual(project["version"], 17)
        self.assertEqual(project["target_duration_seconds"], 20)
        self.assertEqual(project["brand_intro"]["mode"], MODULE.BRAND_MODE_CORNER_LOGO)
        self.assertFalse(project["audio_bed"]["enabled"])
        self.assertEqual(project["cta_tail"]["duration"], 2.0)
        self.assertEqual(project["mid_cta"]["mode"], "auto")

    def test_kangil_is_the_main_automatic_typecast_voice(self) -> None:
        self.assertEqual(MODULE.TYPECAST_VOICE_NAME, "Kangil")
        self.assertEqual(MODULE.TYPECAST_VOICE_ID, "tc_68d4b115f0486108a7eefb37")
        self.assertEqual(MODULE.TYPECAST_DEFAULT_VOICE_BUCKETS.count("kangil"), 8)
        self.assertEqual(MODULE.TYPECAST_DEFAULT_VOICE_BUCKETS.count("daeun"), 2)

    def test_user_can_disable_mid_cta_at_init(self) -> None:
        project = self.init_project(
            delivery_mode=MODULE.CONTINUOUS_FLOW_MODE,
            mid_cta_mode="disabled",
        )
        self.assertEqual(project["mid_cta"]["mode"], "disabled")

    def test_continuous_flow_accepts_twelve_seconds(self) -> None:
        project = self.init_project(delivery_mode=MODULE.CONTINUOUS_FLOW_MODE, duration=12)
        self.assertEqual(project["target_duration_seconds"], 12)

    def test_visual_first_defaults_to_music_and_no_cta_voice(self) -> None:
        project = self.init_project(delivery_mode=MODULE.VISUAL_FIRST_MODE)
        self.assertEqual(project["target_duration_seconds"], 12)
        self.assertTrue(project["audio_bed"]["enabled"])
        self.assertEqual(project["audio_bed"]["profile"], MODULE.VISUAL_FIRST_AUDIO_PROFILE)
        self.assertFalse(project["cta_tail"]["voice_enabled"])

    def test_legacy_intro_keeps_lead_in_and_v16_corner_logo_does_not(self) -> None:
        legacy = {"version": 15, "brand_intro": {"enabled": True, "transition_duration": 0.25}}
        current = {"version": 16, "brand_intro": {"enabled": True, "mode": "corner-logo"}}
        self.assertAlmostEqual(MODULE.brand_intro_lead_in_seconds(legacy), 2.9, places=3)
        self.assertEqual(MODULE.brand_intro_lead_in_seconds(current), 0.0)

    def test_retention_report_uses_actual_scene_timeline(self) -> None:
        project = {
            "version": 16,
            "delivery_mode": MODULE.VISUAL_FIRST_MODE,
            "brand_intro": {"enabled": True, "mode": "corner-logo"},
            "shorts_profile": {
                "first_answer_scene_id": "scene-02",
                "truth_guard": "전부 반영 가정",
                "truth_guard_scene_id": "scene-01",
            },
        }
        report = MODULE.retention_timing_report(
            project,
            [
                {"id": "scene-01", "timeline_start": 0.0},
                {"id": "scene-02", "timeline_start": 1.0},
            ],
        )
        self.assertTrue(report["passed"])
        self.assertEqual(report["events"]["first_answer"]["actual_start"], 1.0)
        self.assertEqual(report["events"]["truth_guard"]["actual_start"], 0.0)

    def test_mid_cta_selects_rehook_closest_to_middle(self) -> None:
        project = {
            "version": 17,
            "delivery_mode": MODULE.CONTINUOUS_FLOW_MODE,
            "target_duration_seconds": 30,
            "sensitive_topic": True,
            "mid_cta": {
                "mode": "enabled",
                "placement": MODULE.MID_CTA_PLACEMENT,
            },
        }
        scenes = [
            {"id": "scene-01", "beat": "hook"},
            {"id": "scene-02", "beat": "turn"},
            {"id": "scene-03", "beat": "evidence"},
            {"id": "scene-04", "beat": "rehook"},
            {"id": "scene-05", "beat": "payoff"},
        ]
        reports = [
            {"timeline_end": 2.5},
            {"timeline_end": 7.0},
            {"timeline_end": 10.0},
            {"timeline_end": 12.0},
            {"timeline_end": 24.0},
        ]
        selection = MODULE.select_mid_cta(project, scenes, reports)
        self.assertTrue(selection["enabled"])
        self.assertEqual(selection["insert_after_scene_id"], "scene-04")
        self.assertEqual(selection["headline"], "잠깐만요")
        self.assertAlmostEqual(selection["boundary_ratio"], 0.5)

    def test_mid_cta_splits_continuous_tts_at_complete_scene_boundary(self) -> None:
        project = {
            "version": 17,
            "delivery_mode": MODULE.CONTINUOUS_FLOW_MODE,
            "target_duration_seconds": 24,
            "sensitive_topic": True,
            "mid_cta": {
                "mode": "enabled",
                "placement": MODULE.MID_CTA_PLACEMENT,
            },
        }
        scenes = [
            {"id": "scene-01", "beat": "hook", "duration": 2.4, "narration": "첫 문장입니다."},
            {"id": "scene-02", "beat": "context", "duration": 3.7, "narration": "둘째 문장입니다."},
            {"id": "scene-03", "beat": "rehook", "duration": 3.7, "narration": "셋째 문장입니다."},
            {"id": "scene-04", "beat": "turn", "duration": 4.0, "narration": "넷째 문장입니다."},
            {"id": "scene-05", "beat": "impact", "duration": 3.8, "narration": "다섯째 문장입니다."},
            {"id": "scene-06", "beat": "payoff", "duration": 4.0, "narration": "여섯째 문장입니다."},
        ]
        selection = MODULE.select_mid_cta(
            project,
            scenes,
            MODULE.estimated_continuous_flow_scene_reports(project, scenes),
        )
        self.assertTrue(selection["enabled"])
        self.assertEqual(selection["insert_after_scene_id"], "scene-03")
        self.assertEqual(
            MODULE.continuous_flow_audio_group_ranges(len(scenes), selection),
            [(0, 3), (3, 6)],
        )

    def test_mid_cta_body_requests_use_distinct_audio_paths(self) -> None:
        scenes = [{"duration": 2.0, "narration": "완전한 문장입니다."}]
        with tempfile.TemporaryDirectory() as temp_name:
            work_dir = Path(temp_name)
            with mock.patch.object(MODULE, "create_silent_audio") as create_silent:
                before, _, _ = MODULE.continuous_flow_audio(
                    scenes,
                    work_dir,
                    no_tts=True,
                    tts_provider="typecast",
                    voice="",
                    rate=180,
                    typecast_voice_id="voice",
                    typecast_tempo=1.0,
                    output_stem="continuous-flow-mid-cta-part-1",
                )
                after, _, _ = MODULE.continuous_flow_audio(
                    scenes,
                    work_dir,
                    no_tts=True,
                    tts_provider="typecast",
                    voice="",
                    rate=180,
                    typecast_voice_id="voice",
                    typecast_tempo=1.0,
                    output_stem="continuous-flow-mid-cta-part-2",
                )
            self.assertNotEqual(before, after)
            self.assertEqual(create_silent.call_count, 2)

    def test_mid_cta_audio_boundary_validation_rejects_one_body_request(self) -> None:
        unsafe_report = {
            "delivery_mode": MODULE.CONTINUOUS_FLOW_MODE,
            "tts_provider": "typecast",
            "mid_cta": {"enabled": True},
            "continuous_flow": {
                "body_tts_requests": 1,
                "mid_cta_two_part": False,
                "boundary_preserves_complete_utterances": False,
            },
        }
        self.assertTrue(MODULE.validate_mid_cta_audio_boundary(unsafe_report))

        safe_report = {
            "delivery_mode": MODULE.CONTINUOUS_FLOW_MODE,
            "tts_provider": "typecast",
            "mid_cta": {
                "enabled": True,
                "boundary_preserves_complete_utterances": True,
            },
            "continuous_flow": {
                "body_tts_requests": 2,
                "mid_cta_two_part": True,
                "boundary_preserves_complete_utterances": True,
            },
        }
        self.assertFalse(MODULE.validate_mid_cta_audio_boundary(safe_report))

    def test_mid_cta_disabled_mode_preserves_legacy_tail(self) -> None:
        selection = MODULE.select_mid_cta(
            {
                "version": 17,
                "delivery_mode": MODULE.CONTINUOUS_FLOW_MODE,
                "mid_cta": {"mode": "disabled"},
            },
            [{"id": "scene-01", "beat": "rehook"}],
            [{"timeline_end": 20.0}],
        )
        self.assertFalse(selection["enabled"])
        self.assertIn("제외", selection["reason"])

    def test_mid_cta_renders_native_ui_arrow_frames(self) -> None:
        selection = {
            "enabled": True,
            "mode": "enabled",
            "placement": MODULE.MID_CTA_PLACEMENT,
            "insert_after_scene_id": "scene-04",
            "insert_after_scene_index": 4,
            "headline": "보고 계신데...",
            "emphasis": "구독은 아직이네요",
            "subline": "채널명 옆 구독, 한 번만",
            "narration": "구독은 아직이네요.",
            "min_duration": 1.5,
            "max_duration": 2.0,
            "style": MODULE.MID_CTA_STYLE,
            "voice_enabled": True,
            "voice_delivery": "verdict",
            "sfx_enabled": True,
            "ui_target_profile": MODULE.MID_CTA_UI_TARGET_PROFILE,
            "arrow_target": {"x": 0.34, "y": 0.86},
        }
        with tempfile.TemporaryDirectory() as temp_name:
            temp_dir = Path(temp_name)
            frame_count = MODULE.render_mid_cta_frames(
                selection,
                temp_dir / "frames",
                1.5,
            )
            self.assertEqual(frame_count, 45)
            self.assertTrue((temp_dir / "frames" / "0000.png").is_file())
            self.assertTrue((temp_dir / "frames" / "0044.png").is_file())

    def test_mid_cta_switches_tail_to_brand_close(self) -> None:
        selection = MODULE.brand_close_selection({"insert_after_scene_id": "scene-04"})
        self.assertEqual(selection["variant"], "brand-close")
        self.assertEqual(selection["duration"], MODULE.BRAND_CLOSE_DURATION)
        self.assertFalse(selection["voice_enabled"])

    def test_source_dialogue_match_detects_missing_tail(self) -> None:
        match = MODULE.source_dialogue_match(
            "저기요. 경찰이에요, 경찰.",
            "저기요",
        )
        self.assertFalse(match["passed"])
        self.assertLess(match["expected_coverage"], MODULE.SOURCE_TRANSCRIPT_COVERAGE_THRESHOLD)

    def test_source_audio_scene_review_passes_complete_timestamped_dialogue(self) -> None:
        review = MODULE.build_source_audio_scene_review(
            {
                "id": "scene-01",
                "video": "assets/source.mp4",
                "video_start": 1.0,
                "duration": 2.5,
                "audio_mode": MODULE.SOURCE_VIDEO_AUDIO_MODE,
                "narration": "저기요. 경찰이에요, 경찰.",
            },
            source_path="assets/source.mp4",
            source_sha256="abc",
            transcript={
                "text": "저기요 경찰이에요 경찰",
                "segments": [
                    {"start": 0.3, "end": 1.0, "text": "저기요"},
                    {"start": 1.2, "end": 2.2, "text": "경찰이에요 경찰"},
                ],
            },
            timing_confirmed=False,
        )
        self.assertEqual(review["status"], "passed")
        self.assertFalse(review["edge_cut_risk"])

    def test_source_audio_scene_review_flags_cut_boundary(self) -> None:
        review = MODULE.build_source_audio_scene_review(
            {
                "id": "scene-01",
                "video": "assets/source.mp4",
                "duration": 2.5,
                "audio_mode": MODULE.SOURCE_VIDEO_AUDIO_MODE,
                "narration": "경찰이에요 경찰",
            },
            source_path="assets/source.mp4",
            source_sha256="abc",
            transcript={
                "text": "경찰이에요 경찰",
                "segments": [{"start": 1.2, "end": 2.45, "text": "경찰이에요 경찰"}],
            },
            timing_confirmed=False,
        )
        self.assertEqual(review["status"], "mismatch")
        self.assertTrue(review["edge_cut_risk"])

    def test_source_audio_review_is_warning_for_draft_and_error_for_final(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            project_dir = Path(temp_name)
            source = project_dir / "assets" / "source.mp4"
            source.parent.mkdir(parents=True)
            source.write_bytes(b"source")
            scenes = [
                {
                    "id": "scene-01",
                    "video": "assets/source.mp4",
                    "duration": 2.5,
                    "audio_mode": MODULE.SOURCE_VIDEO_AUDIO_MODE,
                    "narration": "저기요",
                }
            ]
            draft_errors, draft_warnings = MODULE.validate_source_audio_review(
                project_dir,
                scenes,
                final=False,
            )
            final_errors, final_warnings = MODULE.validate_source_audio_review(
                project_dir,
                scenes,
                final=True,
            )
            self.assertFalse(draft_errors)
            self.assertTrue(draft_warnings)
            self.assertTrue(final_errors)
            self.assertFalse(final_warnings)

    def test_source_audio_review_passes_then_becomes_stale_after_timing_change(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            project_dir = Path(temp_name)
            source = project_dir / "assets" / "source.mp4"
            source.parent.mkdir(parents=True)
            source.write_bytes(b"source")
            scene = {
                "id": "scene-01",
                "video": "assets/source.mp4",
                "video_start": 0,
                "duration": 2.5,
                "audio_mode": MODULE.SOURCE_VIDEO_AUDIO_MODE,
                "narration": "경찰이에요 경찰",
            }
            review = MODULE.build_source_audio_scene_review(
                scene,
                source_path=scene["video"],
                source_sha256=MODULE.file_sha256(source),
                transcript={
                    "text": "경찰이에요 경찰",
                    "segments": [{"start": 0.3, "end": 2.1, "text": "경찰이에요 경찰"}],
                },
                timing_confirmed=False,
            )
            MODULE.write_json(
                project_dir / MODULE.SOURCE_AUDIO_REVIEW_FILENAME,
                {
                    "version": MODULE.SOURCE_AUDIO_REVIEW_VERSION,
                    "status": "passed",
                    "scenes": [review],
                },
            )
            errors, warnings = MODULE.validate_source_audio_review(
                project_dir,
                [scene],
                final=True,
            )
            self.assertFalse(errors)
            self.assertFalse(warnings)
            scene["duration"] = 3.0
            errors, _ = MODULE.validate_source_audio_review(
                project_dir,
                [scene],
                final=True,
            )
            self.assertTrue(any("컷 시작점 또는 길이" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
