import copy
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).parents[1] / "scripts" / "cc_helper.py"
SPEC = importlib.util.spec_from_file_location("cc_helper_media_contracts", SCRIPT)
cc_helper = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(cc_helper)


class NarrationPerformanceValidationTest(unittest.TestCase):
    def build_fixture(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        project_dir = Path(temporary.name)
        handoff = project_dir / "handoff"
        audio_dir = project_dir / "assets" / "audio"
        handoff.mkdir()
        audio_dir.mkdir(parents=True)

        script_path = handoff / "narration-typecast.txt"
        audio_path = audio_dir / "voice.wav"
        timing_path = handoff / "narration-timing.json"
        script_path.write_text("첫 문장이라고 함.\n다음 문장이라는데~\n", encoding="utf-8")
        audio_path.write_bytes(b"reviewed external voice")
        timing_path.write_text(
            json.dumps(
                {
                    "source": "typecast_timestamp_review",
                    "beats": [
                        {"beat_id": "beat-01", "start_seconds": 0.0, "end_seconds": 1.0},
                        {"beat_id": "beat-02", "start_seconds": 1.0, "end_seconds": 2.0},
                    ],
                }
            ),
            encoding="utf-8",
        )

        hashes = {
            "script": hashlib.sha256(script_path.read_bytes()).hexdigest(),
            "audio": hashlib.sha256(audio_path.read_bytes()).hexdigest(),
            "timing": hashlib.sha256(timing_path.read_bytes()).hexdigest(),
        }
        project = {
            "narration_audio": {
                "path": "assets/audio/voice.wav",
                "sha256": hashes["audio"],
            }
        }
        storyboard = {
            "narration_performance_mode": cc_helper.NARRATION_PERFORMANCE_MODE,
            "beats": [
                {"id": "beat-01", "narration": "첫 문장이라고 함."},
                {"id": "beat-02", "narration": "다음 문장이라는데~"},
            ],
        }
        performance = {
            "source": "external_tts_review",
            "storyboard_narration_sha256": cc_helper.narration_contract_sha256(storyboard),
            "script": {
                "path": "handoff/narration-typecast.txt",
                "sha256": hashes["script"],
            },
            "audio": {
                "path": "assets/audio/voice.wav",
                "sha256": hashes["audio"],
            },
            "timing": {
                "path": "handoff/narration-timing.json",
                "sha256": hashes["timing"],
                "source": "typecast_timestamp_review",
            },
            "beats": [
                {
                    "beat_id": "beat-01",
                    "emotion_type": "smart",
                    "emotion_preset": "",
                    "tempo": 1.0,
                    "pause_after_seconds": 0.22,
                    "measured_pause_after_seconds": 0.21,
                },
                {
                    "beat_id": "beat-02",
                    "emotion_type": "preset",
                    "emotion_preset": "tonedown",
                    "tempo": 0.98,
                    "pause_after_seconds": 0.0,
                    "measured_pause_after_seconds": 0.0,
                },
            ],
            "audio_analysis": {
                "integrated_lufs": -16.0,
                "true_peak_dbtp": -1.5,
                "silence_threshold_db": cc_helper.NARRATION_SILENCE_THRESHOLD_DB,
                "minimum_silence_seconds": cc_helper.NARRATION_SILENCE_MIN_SECONDS,
            },
            "listening_review": {
                "status": "approved",
                "reviewer_kind": "human",
                "checks": {
                    "naturalness": True,
                    "dynamics": True,
                    "breathing": True,
                    "pronunciation": True,
                    "pace": True,
                    "no_audio_artifacts": True,
                },
                "script_sha256": hashes["script"],
                "audio_sha256": hashes["audio"],
                "timing_sha256": hashes["timing"],
                "storyboard_narration_sha256": cc_helper.narration_contract_sha256(storyboard),
            },
        }
        performance_path = handoff / "narration-performance.json"
        performance_path.write_text(json.dumps(performance), encoding="utf-8")
        return project_dir, project, storyboard, performance, performance_path, script_path

    def validate(self, project_dir, project, storyboard):
        with mock.patch.object(
            cc_helper, "wav_loudness_metrics", return_value=(-16.0, -1.5)
        ), mock.patch.object(
            cc_helper,
            "wav_silence_intervals",
            return_value=[(0.78, 1.0, 0.22)],
        ):
            return cc_helper.validate_narration_performance(
                project_dir, project, storyboard
            )

    def test_accepts_reviewed_external_performance_with_varied_profiles(self):
        project_dir, project, storyboard, _performance, _path, _script = (
            self.build_fixture()
        )

        errors, warnings = self.validate(project_dir, project, storyboard)

        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_rejects_stale_script_and_listening_approval_hashes(self):
        project_dir, project, storyboard, _performance, _path, script_path = (
            self.build_fixture()
        )
        script_path.write_text("수정된 문장이라고 함.\n", encoding="utf-8")

        errors, _warnings = self.validate(project_dir, project, storyboard)

        self.assertTrue(any("script SHA-256" in error for error in errors))
        self.assertTrue(any("청취 승인 script SHA-256이 stale" in error for error in errors))

    def test_rejects_storyboard_narration_change_without_regenerated_audio(self):
        project_dir, project, storyboard, _performance, _path, _script = (
            self.build_fixture()
        )
        storyboard["beats"][0]["narration"] = "바뀐 첫 문장이라고 함."

        errors, _warnings = self.validate(project_dir, project, storyboard)

        self.assertTrue(any("storyboard 내레이션과 stale" in error for error in errors))
        self.assertTrue(any("성능 검수가 현재 storyboard" in error for error in errors))

    def test_accepts_automated_performance_review_with_human_listening_warning(self):
        project_dir, project, storyboard, performance, path, _script = (
            self.build_fixture()
        )
        performance["listening_review"].update(
            {
                "status": "automated_reviewed",
                "reviewer_kind": "automated",
                "checks": {
                    "profile_variety": True,
                    "measured_pauses": True,
                    "timestamp_alignment": True,
                    "loudness": True,
                    "true_peak": True,
                },
            }
        )
        path.write_text(json.dumps(performance), encoding="utf-8")

        errors, warnings = self.validate(project_dir, project, storyboard)

        self.assertEqual(errors, [])
        self.assertTrue(any("사람 청취 승인" in warning for warning in warnings))

    def test_rejects_unsafe_tempo_pause_and_incomplete_listening_review(self):
        project_dir, project, storyboard, performance, path, _script = (
            self.build_fixture()
        )
        performance["beats"][0].update(
            {
                "tempo": 1.2,
                "pause_after_seconds": 0.5,
                "measured_pause_after_seconds": 0.2,
            }
        )
        performance["listening_review"]["checks"]["dynamics"] = False
        path.write_text(json.dumps(performance), encoding="utf-8")

        errors, _warnings = self.validate(project_dir, project, storyboard)

        self.assertTrue(any("tempo는 0.90~1.10" in error for error in errors))
        self.assertTrue(any("pause는 0.12~0.40초" in error for error in errors))
        self.assertTrue(any("계획 pause와 실제 WAV pause" in error for error in errors))
        self.assertTrue(any("청취 검수 실패: dynamics" in error for error in errors))


class PersonMotionContractTest(unittest.TestCase):
    @staticmethod
    def mapping(scene_id, beat_id, asset_id, duration_us):
        return {
            "scene_id": scene_id,
            "beat_id": beat_id,
            "asset_id": asset_id,
            "duration_us": duration_us,
            "template_segment_visual": {
                "clip": {
                    "scale": {"x": 1.0, "y": 1.0},
                    "transform": {"x": 0.0, "y": 0.0},
                },
                "common_keyframes": [],
            },
        }

    def build_motion_fixture(self):
        mappings = [
            self.mapping("scene-01", "beat-01", "asset-person", 2_000_000),
            self.mapping("scene-02", "beat-01", "asset-person", 3_000_000),
            self.mapping("scene-03", "beat-02", "asset-source-text", 2_500_000),
        ]
        storyboard = {"person_motion_mode": cc_helper.PERSON_MOTION_MODE}
        manifest = {
            "assets": [
                {"id": "asset-person", "evidence_role": "editorial_animation"},
                {"id": "asset-source-text", "evidence_role": "official_evidence"},
            ]
        }
        return mappings, storyboard, manifest

    def test_motion_is_deterministic_continuous_across_split_beat_and_skips_source_text(self):
        mappings, storyboard, manifest = self.build_motion_fixture()
        repeated = copy.deepcopy(mappings)

        cc_helper.attach_person_motion_plans(mappings, storyboard, manifest)
        cc_helper.attach_person_motion_plans(repeated, storyboard, manifest)

        first = mappings[0]["motion_plan"]
        second = mappings[1]["motion_plan"]
        self.assertEqual(first, repeated[0]["motion_plan"])
        self.assertEqual(second, repeated[1]["motion_plan"])
        self.assertEqual(first["pattern"], second["pattern"])
        self.assertAlmostEqual(first["end_scale"], second["start_scale"])
        self.assertAlmostEqual(first["end_x"], second["start_x"])
        self.assertAlmostEqual(first["end_y"], second["start_y"])
        self.assertNotIn("motion_plan", mappings[2])

    def test_root_and_mini_keyframe_schemas_preserve_same_motion_values(self):
        mappings, storyboard, manifest = self.build_motion_fixture()
        cc_helper.attach_person_motion_plans(mappings, storyboard, manifest)
        plan = mappings[0]["motion_plan"]
        root_segment = copy.deepcopy(mappings[0]["template_segment_visual"])
        mini_segment = copy.deepcopy(mappings[0]["template_segment_visual"])

        cc_helper.apply_motion_plan(
            root_segment, mappings[0]["scene_id"], plan, mini=False
        )
        cc_helper.apply_motion_plan(
            mini_segment, mappings[0]["scene_id"], plan, mini=True
        )

        root_groups = {
            group["property_type"]: group
            for group in root_segment["common_keyframes"]
        }
        mini_groups = {
            group["property_type"]: group
            for group in mini_segment["common_keyframes"]
        }
        self.assertEqual(
            set(root_groups),
            {"KFTypePositionX", "KFTypePositionY", "KFTypeScaleX", "KFTypeRotation"},
        )
        self.assertEqual(set(root_groups), set(mini_groups))
        for property_type in root_groups:
            root_points = root_groups[property_type]["keyframe_list"]
            mini_points = mini_groups[property_type]["keyframe_list"]
            self.assertEqual([point["values"] for point in root_points], [point["values"] for point in mini_points])
            self.assertTrue(all(point["curveType"] == "Line" for point in root_points))
            self.assertTrue(all("left_control" in point and "right_control" in point for point in root_points))
            self.assertTrue(all(point["curveType"] == 0 for point in mini_points))
            self.assertTrue(all(point["graph"] is None for point in mini_points))

        self.assertAlmostEqual(root_segment["clip"]["scale"]["x"], plan["end_scale"])
        self.assertAlmostEqual(root_segment["clip"]["scale"]["y"], plan["end_scale"])
        self.assertAlmostEqual(root_segment["clip"]["transform"]["x"], plan["end_x"])
        self.assertAlmostEqual(root_segment["clip"]["transform"]["y"], plan["end_y"])
        self.assertEqual(root_segment["clip"], mini_segment["clip"])


if __name__ == "__main__":
    unittest.main()
