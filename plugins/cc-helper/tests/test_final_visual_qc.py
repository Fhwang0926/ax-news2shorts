import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "cc_helper.py"
SPEC = importlib.util.spec_from_file_location("cc_helper_final_visual_qc", SCRIPT)
cc_helper = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(cc_helper)


class FinalVisualQCValidationTest(unittest.TestCase):
    def build_fixture(self):
        temporary = tempfile.TemporaryDirectory()
        project = Path(temporary.name) / "project"
        destination = Path(temporary.name) / "draft"
        handoff = project / "handoff"
        project.mkdir()
        destination.mkdir()
        handoff.mkdir()

        scene_file = destination / "scene.png"
        scene_file.write_bytes(b"current scene image")
        screenshot = handoff / "scene-01-midpoint.png"
        screenshot.write_bytes(b"approved CapCut player screenshot")

        storyboard = {
            "final_visual_review_mode": cc_helper.FINAL_VISUAL_REVIEW_MODE,
            "beats": [{"id": "beat-01", "narration": "한 문장이라고 함."}],
            "scenes": [
                {
                    "id": "scene-01",
                    "beat_id": "beat-01",
                    "duration": 1.0,
                    "asset_id": "asset-01",
                    "caption": "",
                }
            ],
        }
        storyboard_path = project / "storyboard.json"
        storyboard_path.write_text(
            json.dumps(storyboard, ensure_ascii=False), encoding="utf-8"
        )
        (project / "asset-manifest.json").write_text(
            json.dumps(
                {
                    "assets": [
                        {
                            "id": "asset-01",
                            "review": {"display_focus": "subject"},
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        mapping = {}
        mapping_path = project / "capcut-map.json"
        mapping_path.write_text(json.dumps(mapping), encoding="utf-8")

        scene_segments = [
            {
                "id": f"scene-segment-{index:02d}",
                "material_id": f"scene-material-{index:02d}",
                "target_timerange": {"start": index * 1_000_000, "duration": 1_000_000},
                "visible": True,
            }
            for index in range(15)
        ]
        title_segments = [
            {
                "id": f"title-segment-{index}",
                "material_id": f"title-material-{index}",
                "target_timerange": {"start": 0, "duration": 1_000_000},
                "visible": True,
            }
            for index in range(2)
        ]
        caption_segments = [
            {
                "id": f"caption-segment-{index:02d}",
                "material_id": f"caption-material-{index:02d}",
                "target_timerange": {"start": index * 1_000_000, "duration": 1_000_000},
                "visible": True,
            }
            for index in range(14)
        ]
        draft = {
            "id": "timeline-01",
            "duration": 15_000_000,
            "fps": 30.0,
            "canvas_config": {"width": 1080, "height": 1920},
            "tracks": [
                {"type": "video", "segments": scene_segments},
                {"type": "text", "segments": [title_segments[0]]},
                {"type": "text", "segments": [title_segments[1]]},
                {"type": "text", "segments": caption_segments},
            ],
            "materials": {
                "videos": [
                    {
                        "id": f"scene-material-{index:02d}",
                        "path": str(scene_file),
                    }
                    for index in range(15)
                ],
                "texts": [
                    {
                        "id": f"title-material-{index}",
                        "content": json.dumps({"text": f"title {index}"}),
                    }
                    for index in range(2)
                ]
                + [
                    {
                        "id": f"caption-material-{index:02d}",
                        "content": json.dumps({"text": f"caption {index}"}),
                    }
                    for index in range(14)
                ],
            },
        }
        return temporary, project, destination, draft, mapping, storyboard, screenshot

    def write_approved_qc(
        self, project, destination, draft, storyboard, screenshot, *, fingerprint=None
    ):
        qc = {
            "source": "capcut_player_review",
            "status": "approved",
            "visual_timeline_sha256": fingerprint
            or cc_helper.visual_timeline_fingerprint(draft, destination),
            "capcut_map_sha256": cc_helper.sha256_file(project / "capcut-map.json"),
            "storyboard_sha256": cc_helper.sha256_file(project / "storyboard.json"),
            "timeline_id": draft["id"],
            "samples": [
                {
                    "beat_id": "beat-01",
                    "scene_id": "scene-01",
                    "time_us": 500_000,
                    "screenshot_path": "handoff/scene-01-midpoint.png",
                    "screenshot_sha256": cc_helper.sha256_file(screenshot),
                    "automatic": {
                        "not_blank": True,
                        "white_title_present": True,
                        "yellow_title_present": True,
                        "header_background_clear": True,
                    },
                    "manual": {
                        "correct_visual": True,
                        "caption_matches": True,
                        "no_clipping_or_overlap": True,
                    },
                    "approved": True,
                }
            ],
        }
        (project / "handoff" / "final-visual-qc.json").write_text(
            json.dumps(qc, ensure_ascii=False), encoding="utf-8"
        )

    def test_requires_qc_file_when_player_check_mode_is_enabled(self):
        temporary, project, destination, draft, mapping, storyboard, _screenshot = (
            self.build_fixture()
        )
        self.addCleanup(temporary.cleanup)

        errors = cc_helper.validate_final_visual_qc(
            project, destination, draft, mapping, storyboard
        )

        self.assertTrue(any("final-visual-qc.json" in error for error in errors))

    def test_rejects_stale_visual_timeline_fingerprint(self):
        temporary, project, destination, draft, mapping, storyboard, screenshot = (
            self.build_fixture()
        )
        self.addCleanup(temporary.cleanup)
        self.write_approved_qc(
            project,
            destination,
            draft,
            storyboard,
            screenshot,
            fingerprint="0" * 64,
        )

        errors = cc_helper.validate_final_visual_qc(
            project, destination, draft, mapping, storyboard
        )

        self.assertTrue(any("시각 타임라인" in error for error in errors))

    def test_accepts_one_beat_with_one_approved_midpoint_sample(self):
        temporary, project, destination, draft, mapping, storyboard, screenshot = (
            self.build_fixture()
        )
        self.addCleanup(temporary.cleanup)
        self.write_approved_qc(
            project, destination, draft, storyboard, screenshot
        )

        errors = cc_helper.validate_final_visual_qc(
            project, destination, draft, mapping, storyboard
        )

        self.assertEqual(errors, [])

    def test_motion_scene_requires_start_end_player_evidence(self):
        temporary, project, destination, draft, mapping, storyboard, screenshot = (
            self.build_fixture()
        )
        self.addCleanup(temporary.cleanup)
        mapping["scene_mappings"] = [
            {
                "scene_id": "scene-01",
                "beat_id": "beat-01",
                "motion_plan": {"mode": cc_helper.PERSON_MOTION_MODE},
            }
        ]
        (project / "capcut-map.json").write_text(json.dumps(mapping), encoding="utf-8")
        self.write_approved_qc(
            project, destination, draft, storyboard, screenshot
        )

        errors = cc_helper.validate_final_visual_qc(
            project, destination, draft, mapping, storyboard
        )

        self.assertTrue(any("motion 시작·끝 player 검수" in error for error in errors))
        self.assertTrue(any("motion player 검수 실패" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
