import importlib.util
import hashlib
import json
import tempfile
import unittest
import wave
from pathlib import Path

from PIL import Image


SCRIPT = Path(__file__).parents[1] / "scripts" / "cc_helper.py"
SPEC = importlib.util.spec_from_file_location("cc_helper", SCRIPT)
cc_helper = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(cc_helper)


class TextFreeVisualValidationTest(unittest.TestCase):
    def build_project(self, visual_text):
        temporary = tempfile.TemporaryDirectory()
        project = Path(temporary.name)
        normalized = project / "assets" / "normalized" / "scene.png"
        normalized.parent.mkdir(parents=True)
        Image.new("RGB", (1080, 1920), "navy").save(normalized)

        (project / "research.json").write_text(
            json.dumps(
                {
                    "selected_candidate_id": "candidate-01",
                    "candidates": [{"id": "candidate-01"}],
                    "sources": [{"id": "source-01", "url": "https://example.com/source"}],
                    "facts": [{"claim": "verified fact", "source_ids": ["source-01"]}],
                }
            ),
            encoding="utf-8",
        )
        beats = [{"id": f"beat-{index}", "narration": "narration"} for index in range(1, 8)]
        scenes = []
        assets = []
        for index in range(1, 16):
            asset_id = f"asset-{index:02d}"
            scenes.append(
                {
                    "id": f"scene-{index:02d}",
                    "beat_id": f"beat-{min(index, 7)}",
                    "duration": 2,
                    "caption": "" if index == 1 else "caption",
                    "asset_id": asset_id,
                }
            )
            record = {
                "id": asset_id,
                "normalized_path": "assets/normalized/scene.png",
                "synthetic": index == 2,
                "rights_status": "unreviewed",
            }
            if index == 2 and visual_text is not None:
                record["visual_text"] = visual_text
            assets.append(record)

        (project / "storyboard.json").write_text(
            json.dumps(
                {
                    "title": {"white": "흰색 제목", "yellow": "노란 제목"},
                    "message": "message",
                    "beats": beats,
                    "scenes": scenes,
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        (project / "asset-manifest.json").write_text(
            json.dumps({"assets": assets}), encoding="utf-8"
        )
        (project / "project.json").write_text(json.dumps({}), encoding="utf-8")
        return temporary, project

    def enable_narration_hold(self, project):
        storyboard_path = project / "storyboard.json"
        storyboard = json.loads(storyboard_path.read_text(encoding="utf-8"))
        storyboard["pacing_mode"] = "narration-hold"
        storyboard["caption_sync_mode"] = "clause"
        beat_ids = (
            "beat-01",
            "beat-02", "beat-02",
            "beat-03", "beat-03",
            "beat-04",
            "beat-05",
            "beat-06", "beat-06",
            "beat-07", "beat-07",
            "beat-08", "beat-08",
            "beat-09", "beat-09",
        )
        run_counts = {beat_id: beat_ids.count(beat_id) for beat_id in set(beat_ids)}
        storyboard["beats"] = []
        for index in range(1, 10):
            beat_id = f"beat-{index:02d}"
            narration = "전달했다고 함." if run_counts[beat_id] == 1 else "전달 했다고 함."
            storyboard["beats"].append({"id": beat_id, "narration": narration})
        for index, (scene, beat_id) in enumerate(zip(storyboard["scenes"], beat_ids), start=1):
            scene["beat_id"] = beat_id
            first_in_beat = index == 1 or beat_id != beat_ids[index - 2]
            if run_counts[beat_id] == 1:
                scene["narration"] = "전달했다고 함."
            elif first_in_beat:
                scene["narration"] = "전달"
            else:
                scene["narration"] = "했다고 함."
            if index == 1:
                scene["caption"] = ""
                scene["caption_anchor"] = ""
            else:
                scene["caption_anchor"] = "전달" if first_in_beat else "했다고"
                scene["caption"] = scene["narration"].rstrip(".")
            if not first_in_beat:
                scene["asset_id"] = storyboard["scenes"][index - 2]["asset_id"]
        storyboard_path.write_text(
            json.dumps(storyboard, ensure_ascii=False), encoding="utf-8"
        )
        return storyboard

    def test_rejects_unconfirmed_synthetic_visual(self):
        temporary, project = self.build_project(None)
        self.addCleanup(temporary.cleanup)
        errors, _warnings = cc_helper.validate_assets(project)
        self.assertTrue(any("text-free" in error for error in errors))

    def test_accepts_confirmed_text_free_synthetic_visual(self):
        temporary, project = self.build_project("none")
        self.addCleanup(temporary.cleanup)
        errors, _warnings = cc_helper.validate_assets(project)
        self.assertFalse(any("text-free" in error for error in errors))

    def test_rejects_formal_narration_in_project(self):
        temporary, project = self.build_project("none")
        self.addCleanup(temporary.cleanup)
        storyboard_path = project / "storyboard.json"
        storyboard = json.loads(storyboard_path.read_text(encoding="utf-8"))
        storyboard["beats"][0]["narration"] = "사임 의사를 전달했습니다."
        storyboard_path.write_text(
            json.dumps(storyboard, ensure_ascii=False),
            encoding="utf-8",
        )

        errors, _warnings = cc_helper.validate_assets(project)

        self.assertTrue(any("친구 설명형 구어체" in error for error in errors))

    def test_accepts_narration_hold_pairs(self):
        temporary, project = self.build_project("none")
        self.addCleanup(temporary.cleanup)
        self.enable_narration_hold(project)

        errors, _warnings = cc_helper.validate_assets(project)

        self.assertFalse(any("에셋" in error or "caption_anchor" in error for error in errors))

    def test_rejects_narration_hold_reuse_across_beats(self):
        temporary, project = self.build_project("none")
        self.addCleanup(temporary.cleanup)
        storyboard = self.enable_narration_hold(project)
        storyboard["scenes"][-1]["asset_id"] = storyboard["scenes"][0]["asset_id"]
        (project / "storyboard.json").write_text(
            json.dumps(storyboard, ensure_ascii=False), encoding="utf-8"
        )

        errors, _warnings = cc_helper.validate_assets(project)

        self.assertTrue(
            any("다른 beat의 에셋" in error or "asset_id를 유지" in error for error in errors)
        )

    def test_rejects_noncontiguous_beat(self):
        temporary, project = self.build_project("none")
        self.addCleanup(temporary.cleanup)
        storyboard = self.enable_narration_hold(project)
        storyboard["scenes"][6]["beat_id"] = "beat-03"
        (project / "storyboard.json").write_text(
            json.dumps(storyboard, ensure_ascii=False), encoding="utf-8"
        )

        errors, _warnings = cc_helper.validate_assets(project)

        self.assertTrue(any("비연속" in error or "구간 순서" in error for error in errors))

    def test_rejects_missing_caption_anchor(self):
        temporary, project = self.build_project("none")
        self.addCleanup(temporary.cleanup)
        storyboard = self.enable_narration_hold(project)
        storyboard["scenes"][1]["caption_anchor"] = ""
        (project / "storyboard.json").write_text(
            json.dumps(storyboard, ensure_ascii=False), encoding="utf-8"
        )

        errors, _warnings = cc_helper.validate_assets(project)

        self.assertTrue(any("caption_anchor가 비어" in error for error in errors))

    def test_rejects_punctuation_only_caption_anchor(self):
        temporary, project = self.build_project("none")
        self.addCleanup(temporary.cleanup)
        storyboard = self.enable_narration_hold(project)
        storyboard["scenes"][1]["caption_anchor"] = "?!"
        storyboard["scenes"][1]["caption"] = "?!"
        (project / "storyboard.json").write_text(
            json.dumps(storyboard, ensure_ascii=False), encoding="utf-8"
        )

        errors, _warnings = cc_helper.validate_assets(project)

        self.assertTrue(any("글자나 숫자" in error for error in errors))

    def test_rejects_caption_anchor_after_first_two_words(self):
        temporary, project = self.build_project("none")
        self.addCleanup(temporary.cleanup)
        storyboard = self.enable_narration_hold(project)
        scene = storyboard["scenes"][1]
        scene["narration"] = "당일 밤 공식 명단에서는 박위를 손절했다고 함."
        scene["caption"] = "공식 명단에서는 박위를 손절했다고 함"
        scene["caption_anchor"] = "공식 명단"
        (project / "storyboard.json").write_text(
            json.dumps(storyboard, ensure_ascii=False), encoding="utf-8"
        )

        errors, _warnings = cc_helper.validate_assets(project)

        self.assertTrue(any("첫 두 어절" in error for error in errors))

    def test_rejects_caption_text_before_opening_anchor(self):
        temporary, project = self.build_project("none")
        self.addCleanup(temporary.cleanup)
        storyboard = self.enable_narration_hold(project)
        scene = storyboard["scenes"][1]
        scene["narration"] = "서울시는 후속 절차를 예고했고."
        scene["caption"] = "결국 서울시는 후속 절차를 예고했고"
        scene["caption_anchor"] = "서울시"
        (project / "storyboard.json").write_text(
            json.dumps(storyboard, ensure_ascii=False), encoding="utf-8"
        )

        errors, _warnings = cc_helper.validate_assets(project)

        self.assertTrue(any("opening caption_anchor" in error for error in errors))

    def test_allows_one_word_before_opening_anchor(self):
        temporary, project = self.build_project("none")
        self.addCleanup(temporary.cleanup)
        storyboard = self.enable_narration_hold(project)
        scene = storyboard["scenes"][1]
        scene["narration"] = "박위는 영상을 삭제하고."
        scene["caption"] = "영상을 삭제하고"
        scene["caption_anchor"] = "영상"
        (project / "storyboard.json").write_text(
            json.dumps(storyboard, ensure_ascii=False), encoding="utf-8"
        )

        errors, _warnings = cc_helper.validate_assets(project)

        self.assertFalse(any("첫 두 어절" in error or "opening caption_anchor" in error for error in errors))

    def test_rejects_caption_that_drops_spoken_ending(self):
        temporary, project = self.build_project("none")
        self.addCleanup(temporary.cleanup)
        storyboard = self.enable_narration_hold(project)
        scene = storyboard["scenes"][1]
        scene["narration"] = "서울시는 후속 절차를 예고했고."
        scene["caption"] = "서울시는 후속 절차 예고"
        scene["caption_anchor"] = "서울시"
        (project / "storyboard.json").write_text(
            json.dumps(storyboard, ensure_ascii=False), encoding="utf-8"
        )

        errors, _warnings = cc_helper.validate_assets(project)

        self.assertTrue(any("마지막 연결어" in error for error in errors))

    def test_rejects_scene_narration_that_differs_from_voice_beat(self):
        temporary, project = self.build_project("none")
        self.addCleanup(temporary.cleanup)
        storyboard = self.enable_narration_hold(project)
        storyboard["scenes"][2]["narration"] = "다른 이야기"
        storyboard["scenes"][2]["caption"] = "다른 이야기"
        storyboard["scenes"][2]["caption_anchor"] = "다른"
        (project / "storyboard.json").write_text(
            json.dumps(storyboard, ensure_ascii=False), encoding="utf-8"
        )

        errors, _warnings = cc_helper.validate_assets(project)

        self.assertTrue(any("실제 beat narration과 다릅니다" in error for error in errors))

    def test_dynamic_hold_mapping_uses_previous_scene_path(self):
        temporary, project = self.build_project("none")
        self.addCleanup(temporary.cleanup)
        storyboard = self.enable_narration_hold(project)
        manifest = json.loads((project / "asset-manifest.json").read_text(encoding="utf-8"))
        draft = {
            "duration": 30_000_000,
            "fps": 30.0,
            "canvas_config": {"width": 1080, "height": 1920},
            "tracks": [
                {
                    "type": "video",
                    "segments": [
                        {"id": f"segment-{index:02d}", "material_id": f"material-{index:02d}"}
                        for index in range(1, 16)
                    ],
                },
                {"type": "text", "segments": [{"id": "title-1", "material_id": "text-title-1"}]},
                {"type": "text", "segments": [{"id": "title-2", "material_id": "text-title-2"}]},
                {
                    "type": "text",
                    "segments": [
                        {"id": f"caption-{index:02d}", "material_id": f"text-caption-{index:02d}"}
                        for index in range(1, 15)
                    ],
                },
            ],
            "materials": {
                "videos": [
                    {"id": f"material-{index:02d}", "path": f"old-{index:02d}.png"}
                    for index in range(1, 16)
                ],
                "texts": [
                    {"id": "text-title-1"},
                    {"id": "text-title-2"},
                    *[
                        {"id": f"text-caption-{index:02d}"}
                        for index in range(1, 15)
                    ],
                ],
            },
        }

        scene_mappings, _titles, _captions = cc_helper.build_content_mappings(
            draft, storyboard, manifest
        )

        self.assertEqual(scene_mappings[2]["hold_source_scene_id"], "scene-02")
        self.assertEqual(
            scene_mappings[2]["target_relative_path"],
            scene_mappings[1]["target_relative_path"],
        )
        self.assertEqual(scene_mappings[6]["hold_source_scene_id"], "")
        self.assertEqual(scene_mappings[14]["hold_source_scene_id"], "scene-14")

    def test_narration_hold_allows_seven_second_scene(self):
        temporary, project = self.build_project("none")
        self.addCleanup(temporary.cleanup)
        storyboard = self.enable_narration_hold(project)
        storyboard["scenes"][0]["duration"] = 7
        storyboard["scenes"][1]["duration"] = 1
        storyboard["scenes"][2]["duration"] = 1
        (project / "storyboard.json").write_text(
            json.dumps(storyboard, ensure_ascii=False), encoding="utf-8"
        )

        errors, _warnings = cc_helper.validate_assets(project)

        self.assertFalse(any("scene-01 길이" in error for error in errors))

    def test_narration_timing_rejects_audio_hash_change(self):
        temporary, project = self.build_project("none")
        self.addCleanup(temporary.cleanup)
        storyboard = self.enable_narration_hold(project)
        audio_path = project / "assets" / "audio" / "voice.wav"
        audio_path.parent.mkdir(parents=True)
        with wave.open(str(audio_path), "wb") as output:
            output.setnchannels(1)
            output.setsampwidth(2)
            output.setframerate(1000)
            output.writeframes(b"\0\0" * 30_000)
        actual_sha = hashlib.sha256(audio_path.read_bytes()).hexdigest()
        (project / "project.json").write_text(
            json.dumps(
                {
                    "narration_audio": {
                        "path": "assets/audio/voice.wav",
                        "sha256": actual_sha,
                        "duration_seconds": 30.0,
                        "capcut_duration_us": 30_000_000,
                    }
                }
            ),
            encoding="utf-8",
        )
        times = cc_helper.scene_times(storyboard)
        beat_ranges = []
        for beat in storyboard["beats"]:
            linked = [
                (scene, timing)
                for scene, timing in zip(storyboard["scenes"], times)
                if scene["beat_id"] == beat["id"]
            ]
            beat_ranges.append(
                {
                    "beat_id": beat["id"],
                    "start_seconds": linked[0][1]["start"] / 1_000_000,
                    "end_seconds": (linked[-1][1]["start"] + linked[-1][1]["duration"]) / 1_000_000,
                }
            )
        timing = {
            "version": 1,
            "source": "capcut_waveform_review",
            "audio": {
                "path": "assets/audio/voice.wav",
                "sha256": "changed",
                "duration_seconds": 30.0,
            },
            "beats": beat_ranges,
            "scenes": [
                {
                    "scene_id": scene["id"],
                    "start_seconds": item["start"] / 1_000_000,
                    "end_seconds": (item["start"] + item["duration"]) / 1_000_000,
                }
                for scene, item in zip(storyboard["scenes"], times)
            ],
        }
        handoff = project / "handoff"
        handoff.mkdir()
        (handoff / "narration-timing.json").write_text(
            json.dumps(timing), encoding="utf-8"
        )

        errors, _warnings = cc_helper.validate_assets(project)

        self.assertTrue(any("SHA-256" in error for error in errors))


class CapCutMaterialPathTest(unittest.TestCase):
    def test_updates_audio_duration_without_changing_identity(self):
        project = {
            "narration_audio": {
                "capcut_material_id": "audio-material",
                "capcut_segment_id": "audio-segment",
                "capcut_duration_us": 44_966_666,
            }
        }
        draft = {
            "materials": {
                "audios": [
                    {
                        "id": "audio-material",
                        "path": "/tmp/voice.wav",
                        "duration": 41_400_000,
                    }
                ]
            },
            "tracks": [
                {
                    "id": "audio-track",
                    "type": "audio",
                    "segments": [
                        {
                            "id": "audio-segment",
                            "material_id": "audio-material",
                            "target_timerange": {"start": 0, "duration": 41_400_000},
                            "source_timerange": {"start": 0, "duration": 41_400_000},
                            "volume": 1.0,
                        }
                    ],
                }
            ],
        }
        before = cc_helper.narration_audio_identity(draft, project)

        cc_helper.sync_narration_audio_duration(draft, project)

        self.assertEqual(before, cc_helper.narration_audio_identity(draft, project))
        segment = draft["tracks"][0]["segments"][0]
        self.assertEqual(segment["target_timerange"]["duration"], 44_966_666)
        self.assertEqual(segment["source_timerange"]["duration"], 44_966_666)
        self.assertEqual(draft["materials"]["audios"][0]["duration"], 44_966_666)

    def test_resolves_draft_placeholder_to_existing_asset(self):
        with tempfile.TemporaryDirectory() as directory:
            draft = Path(directory)
            asset = draft / "cc-helper-assets" / "visuals" / "scene-01.png"
            asset.parent.mkdir(parents=True)
            asset.touch()
            placeholder = (
                "##_draftpath_placeholder_0E685133-18CE-45ED-8CB8-2904A212EC80_##/"
                "cc-helper-assets/visuals/scene-01.png"
            )

            self.assertEqual(
                cc_helper.resolve_capcut_material_path(placeholder, draft),
                asset.resolve(),
            )

    def test_keeps_absolute_material_path(self):
        absolute = Path("/tmp/scene-01.png")
        self.assertEqual(
            cc_helper.resolve_capcut_material_path(str(absolute), Path("/draft")),
            absolute,
        )

    def test_visual_copy_preserves_nested_ids(self):
        leader = {
            "clip": {
                "id": "leader-clip",
                "scale": {"id": "leader-scale", "x": 1.2, "y": 1.2},
                "transform": {"id": "leader-transform", "x": 0.1, "y": -0.2},
            },
            "crop": {"id": "leader-crop", "upper_left_y": 0.25},
            "uniform_scale": {"id": "leader-uniform", "on": True, "value": 1.2},
        }
        follower = {
            "clip": {
                "id": "follower-clip",
                "scale": {"id": "follower-scale", "x": 1.0, "y": 1.0},
                "transform": {"id": "follower-transform", "x": 0.0, "y": 0.0},
            },
            "crop": {"id": "follower-crop", "upper_left_y": 0.1},
            "uniform_scale": {"id": "follower-uniform", "on": False, "value": 1.0},
        }

        cc_helper.copy_visual_values(follower, leader)

        self.assertEqual(follower["clip"]["id"], "follower-clip")
        self.assertEqual(follower["clip"]["scale"]["id"], "follower-scale")
        self.assertEqual(follower["clip"]["scale"]["x"], 1.2)
        self.assertEqual(follower["crop"]["id"], "follower-crop")
        self.assertEqual(follower["crop"]["upper_left_y"], 0.25)
        self.assertEqual(follower["uniform_scale"]["id"], "follower-uniform")

    def test_apply_root_draft_restores_template_geometry_and_hold_material_crop(self):
        def segment_visual(transform_y):
            return {
                "clip": {
                    "scale": {"x": 1.0, "y": 1.0},
                    "rotation": 0.0,
                    "transform": {"x": 0.0, "y": transform_y},
                    "flip": {"vertical": False, "horizontal": False},
                    "alpha": 1.0,
                },
                "uniform_scale": {"on": True, "value": 1.0},
                "common_keyframes": [],
            }

        def material_visual(upper_y, lower_y):
            return {
                "crop": {
                    "upper_left_x": 0.0,
                    "upper_left_y": upper_y,
                    "upper_right_x": 1.0,
                    "upper_right_y": upper_y,
                    "lower_left_x": 0.0,
                    "lower_left_y": lower_y,
                    "lower_right_x": 1.0,
                    "lower_right_y": lower_y,
                },
                "crop_ratio": "free",
                "crop_scale": 1.0,
            }

        scene_segments = []
        video_materials = []
        scene_mappings = []
        for index in range(1, 16):
            segment_id = f"segment-{index:02d}"
            material_id = f"material-{index:02d}"
            scene_id = f"scene-{index:02d}"
            scene_segments.append(
                {
                    "id": segment_id,
                    "material_id": material_id,
                    "clip": {
                        "scale": {"x": 1.0, "y": 1.0},
                        "transform": {"x": 0.0, "y": 0.0},
                    },
                    "uniform_scale": {"on": True, "value": 1.0},
                    "common_keyframes": [],
                    "target_timerange": {"start": 0, "duration": 1},
                    "source_timerange": {"start": 0, "duration": 1},
                }
            )
            video_materials.append(
                {
                    "id": material_id,
                    "path": f"old-{index:02d}.png",
                    **material_visual(0.0, 1.0),
                }
            )
            scene_mappings.append(
                {
                    "scene_id": scene_id,
                    "segment_id": segment_id,
                    "material_id": material_id,
                    "target_relative_path": f"visuals/{scene_id}.png",
                    "hold_source_scene_id": "scene-02" if index == 3 else "",
                    "template_segment_visual": segment_visual(-0.31 - index / 100),
                    "template_material_visual": material_visual(
                        0.21 if index == 2 else 0.34 if index == 3 else 0.18,
                        0.82 if index == 2 else 0.73 if index == 3 else 0.84,
                    ),
                    "start_us": (index - 1) * 1_000_000,
                    "duration_us": 1_000_000,
                }
            )

        draft = {
            "duration": 1,
            "fps": 30.0,
            "canvas_config": {"width": 1080, "height": 1920},
            "tracks": [
                {"type": "video", "segments": scene_segments},
                {
                    "type": "text",
                    "segments": [{"id": "title-1", "material_id": "text-title-1"}],
                },
                {
                    "type": "text",
                    "segments": [{"id": "title-2", "material_id": "text-title-2"}],
                },
                {
                    "type": "text",
                    "segments": [
                        {"id": f"caption-{index:02d}", "material_id": f"text-caption-{index:02d}"}
                        for index in range(1, 15)
                    ],
                },
            ],
            "materials": {
                "videos": video_materials,
                "texts": [
                    {"id": "text-title-1"},
                    {"id": "text-title-2"},
                    *[
                        {"id": f"text-caption-{index:02d}"}
                        for index in range(1, 15)
                    ],
                ],
            },
        }
        mapping = {
            "total_duration_us": 15_000_000,
            "scene_mappings": scene_mappings,
            "title_mappings": [
                {"segment_id": "title-1", "material_id": "text-title-1", "value": "흰 제목"},
                {"segment_id": "title-2", "material_id": "text-title-2", "value": "노란 제목"},
            ],
            "caption_mappings": [
                {
                    "segment_id": f"caption-{index:02d}",
                    "material_id": f"text-caption-{index:02d}",
                    "value": f"자막 {index}",
                    "start_us": index * 1_000_000,
                    "duration_us": 1_000_000,
                }
                for index in range(1, 15)
            ],
        }

        cc_helper.apply_root_draft(draft, mapping, Path("/draft"))

        parts = cc_helper.find_template_parts(draft)
        first_segment = parts["scene_segments"][0]
        first_material = parts["videos"][first_segment["material_id"]]
        leader_segment = parts["scene_segments"][1]
        leader_material = parts["videos"][leader_segment["material_id"]]
        follower_segment = parts["scene_segments"][2]
        follower_material = parts["videos"][follower_segment["material_id"]]
        self.assertEqual(first_segment["clip"]["transform"]["y"], -0.32)
        self.assertEqual(first_material["crop"]["upper_left_y"], 0.18)
        self.assertEqual(first_material["crop"]["lower_left_y"], 0.84)
        self.assertEqual(
            cc_helper.visual_value_snapshot(follower_segment),
            cc_helper.visual_value_snapshot(leader_segment),
        )
        self.assertEqual(follower_material["crop"]["upper_left_y"], 0.21)
        self.assertEqual(follower_material["crop"]["lower_left_y"], 0.82)
        self.assertEqual(
            cc_helper.visual_value_snapshot(follower_material),
            cc_helper.visual_value_snapshot(leader_material),
        )

    def test_full_frame_reset_preserves_nested_ids(self):
        segment = {
            "clip": {
                "id": "clip-id",
                "scale": {"id": "scale-id", "x": 1.4, "y": 0.8},
                "transform": {"id": "transform-id", "x": 0.2, "y": -0.3},
                "flip": {"id": "flip-id", "horizontal": True, "vertical": True},
                "rotation": 15.0,
                "alpha": 0.4,
            },
            "alpha": 0.5,
            "crop": {
                "id": "crop-id",
                "upper_left_x": 0.1,
                "upper_left_y": 0.2,
                "upper_right_x": 0.9,
                "upper_right_y": 0.2,
                "lower_left_x": 0.1,
                "lower_left_y": 0.8,
                "lower_right_x": 0.9,
                "lower_right_y": 0.8,
            },
            "crop_ratio": 3,
            "crop_scale": 1.7,
            "uniform_scale": {"id": "uniform-id", "on": False, "value": 1.5},
            "common_keyframes": [{"id": "keyframe-id"}],
        }

        cc_helper.reset_full_frame_geometry(segment)

        self.assertEqual(segment["clip"]["id"], "clip-id")
        self.assertEqual(segment["clip"]["scale"]["id"], "scale-id")
        self.assertEqual(segment["clip"]["transform"]["id"], "transform-id")
        self.assertEqual(segment["clip"]["flip"]["id"], "flip-id")
        self.assertEqual(segment["crop"]["id"], "crop-id")
        self.assertEqual(segment["uniform_scale"]["id"], "uniform-id")
        self.assertEqual(segment["clip"]["scale"]["x"], 1.0)
        self.assertEqual(segment["clip"]["scale"]["y"], 1.0)
        self.assertEqual(segment["clip"]["transform"]["x"], 0.0)
        self.assertEqual(segment["clip"]["transform"]["y"], 0.0)
        self.assertFalse(segment["clip"]["flip"]["horizontal"])
        self.assertFalse(segment["clip"]["flip"]["vertical"])
        self.assertEqual(segment["clip"]["rotation"], 0.0)
        self.assertEqual(segment["clip"]["alpha"], 1.0)
        self.assertEqual(segment["alpha"], 1.0)
        self.assertEqual(
            {
                key: value
                for key, value in segment["crop"].items()
                if key != "id"
            },
            {
                "upper_left_x": 0.0,
                "upper_left_y": 0.0,
                "upper_right_x": 1.0,
                "upper_right_y": 0.0,
                "lower_left_x": 0.0,
                "lower_left_y": 1.0,
                "lower_right_x": 1.0,
                "lower_right_y": 1.0,
            },
        )
        self.assertEqual(segment["crop_ratio"], 0)
        self.assertEqual(segment["crop_scale"], 1.0)
        self.assertTrue(segment["uniform_scale"]["on"])
        self.assertEqual(segment["uniform_scale"]["value"], 1.0)
        self.assertEqual(segment["common_keyframes"], [])
        self.assertTrue(cc_helper.is_full_frame_geometry(segment))

    def test_project_prerender_cache_path_is_project_scoped(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            user_data = root / "User Data"
            capcut_root = user_data / "Projects" / "com.lveditor.draft"
            destination = capcut_root / "draft-01"
            timeline_id = "C4293950-AAB0-407C-9888-26828A01D90C"
            (destination / "Timelines" / timeline_id).mkdir(parents=True)

            cache_path = cc_helper.project_prerender_cache_path(
                capcut_root, destination, timeline_id
            )

            self.assertEqual(
                cache_path,
                (user_data / "Cache" / "prerender" / timeline_id).resolve(),
            )
            with self.assertRaises(cc_helper.CCHelperError):
                cc_helper.project_prerender_cache_path(
                    capcut_root, destination, "../outside"
                )

    def test_prerender_backup_invalidate_restore_preserves_sibling(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            timeline_id = "C4293950-AAB0-407C-9888-26828A01D90C"
            cache_root = root / "Cache" / "prerender"
            cache_path = cache_root / timeline_id
            rendered = cache_path / "render" / "0_116.mp4"
            rendered.parent.mkdir(parents=True)
            rendered.write_bytes(b"stale project prerender")
            (cache_path / "preRenderSetting.json").write_text(
                '{"width": 1080, "height": 1920}', encoding="utf-8"
            )
            sibling = cache_root / "OTHER-TIMELINE"
            sibling.mkdir(parents=True)
            sibling_file = sibling / "keep.bin"
            sibling_file.write_bytes(b"keep sibling cache")
            backup = root / "backup"

            backup_path = cc_helper.backup_prerender_cache(cache_path, backup)

            self.assertIsNotNone(backup_path)
            self.assertTrue(cache_path.is_dir())
            self.assertEqual(
                cc_helper.tree_hash(cache_path), cc_helper.tree_hash(backup_path)
            )
            self.assertTrue(cc_helper.invalidate_prerender_cache(cache_path))
            self.assertFalse(cache_path.exists())
            self.assertEqual(sibling_file.read_bytes(), b"keep sibling cache")
            self.assertFalse(cc_helper.invalidate_prerender_cache(cache_path))

            cc_helper.restore_prerender_cache(cache_path, backup_path)

            self.assertEqual(rendered.read_bytes(), b"stale project prerender")
            self.assertEqual(sibling_file.read_bytes(), b"keep sibling cache")
            self.assertEqual(
                cc_helper.tree_hash(cache_path), cc_helper.tree_hash(backup_path)
            )

    def test_active_mirrors_exclude_backup_files(self):
        with tempfile.TemporaryDirectory() as directory:
            draft = Path(directory)
            timeline = draft / "Timelines" / "timeline-01"
            timeline.mkdir(parents=True)
            for path in (
                draft / "draft_info.json",
                draft / "template-2.tmp",
                timeline / "draft_info.json",
                timeline / "template-2.tmp",
                draft / "draft_info.json.bak",
                timeline / "draft_info.json.bak",
            ):
                path.write_text("{}", encoding="utf-8")

            paths = cc_helper.active_draft_mirror_paths(draft)

            self.assertEqual(len(paths), 4)
            self.assertFalse(any(path.name.endswith(".bak") for path in paths))

    def test_active_cover_paths_include_only_current_covers(self):
        with tempfile.TemporaryDirectory() as directory:
            draft = Path(directory)
            timeline = draft / "Timelines" / "timeline-01"
            timeline.mkdir(parents=True)
            current = [draft / "draft_cover.jpg", timeline / "draft_cover.jpg"]
            for path in [*current, timeline / "draft_cover.jpg.bak"]:
                path.write_bytes(b"cover")

            self.assertEqual(cc_helper.active_cover_paths(draft), current)

    def test_sync_retime_visuals_replaces_slot_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / "project"
            draft = root / "draft"
            source = project / "assets" / "normalized" / "source.png"
            source.parent.mkdir(parents=True)
            Image.new("RGB", (1080, 1920), "purple").save(source)
            target = draft / "cc-helper-assets" / "visuals" / "scene-02.png"
            target.parent.mkdir(parents=True)
            Image.new("RGB", (1080, 1920), "orange").save(target)
            mappings = [
                {
                    "source_path": "assets/normalized/source.png",
                    "target_relative_path": "cc-helper-assets/visuals/scene-02.png",
                },
                {
                    "source_path": "assets/normalized/source.png",
                    "target_relative_path": "cc-helper-assets/visuals/scene-02.png",
                },
            ]

            cc_helper.sync_retime_visuals(project, draft, mappings)

            self.assertEqual(cc_helper.sha256_file(source), cc_helper.sha256_file(target))


class NarrationToneValidationTest(unittest.TestCase):
    def test_detects_formal_report_ending(self):
        self.assertTrue(cc_helper.uses_formal_narration_ending("사임 의사를 전달했습니다."))

    def test_accepts_friend_explainer_ending(self):
        self.assertFalse(cc_helper.uses_formal_narration_ending("사임 의사를 전달했다고 함."))


class NarrationFlowValidationTest(unittest.TestCase):
    def valid_beats(self):
        return [
            {"id": "beat-01", "flow_role": "hook", "narration": "결국 자리까지 내려놨다는데."},
            {"id": "beat-02", "flow_role": "setup", "narration": "홍보대사로 위촉됐고."},
            {"id": "beat-03", "flow_role": "trigger", "narration": "시작은 공개한 영상이었음."},
            {"id": "beat-04", "flow_role": "explanation", "narration": "사고 예방 목적이라고 했지만."},
            {"id": "beat-05", "flow_role": "reaction", "narration": "커뮤니티가 난리였고."},
            {"id": "beat-06", "flow_role": "response", "narration": "영상을 내리고 사과했지만."},
            {"id": "beat-07", "flow_role": "consequence", "narration": "강연까지 취소됐고."},
            {"id": "beat-08", "flow_role": "resolution", "narration": "사임 뜻을 전한 거고."},
            {"id": "beat-09", "flow_role": "aftermath", "narration": "공식 명단에서 손절했다고 함."},
        ]

    def test_legacy_storyboard_skips_narration_flow_validation(self):
        beats = [
            {"id": "beat-01", "narration": "첫 문장인데."},
            {"id": "beat-02", "narration": "두 번째 문장인데."},
        ]

        self.assertEqual(cc_helper.validate_narration_flow({}, beats), [])

    def test_accepts_valid_conversational_chain(self):
        storyboard = {"narration_flow_mode": "conversational-chain"}

        self.assertEqual(
            cc_helper.validate_narration_flow(storyboard, self.valid_beats()),
            [],
        )

    def test_rejects_flow_role_regression(self):
        storyboard = {"narration_flow_mode": "conversational-chain"}
        beats = self.valid_beats()
        beats[5]["flow_role"] = "trigger"

        errors = cc_helper.validate_narration_flow(storyboard, beats)

        self.assertTrue(any("역행" in error for error in errors))

    def test_rejects_adjacent_de_endings(self):
        storyboard = {"narration_flow_mode": "conversational-chain"}
        beats = self.valid_beats()
        beats[1]["narration"] = "홍보대사로 위촉됐는데."

        errors = cc_helper.validate_narration_flow(storyboard, beats)

        self.assertTrue(any("~데/~는데" in error for error in errors))

    def test_rejects_consecutive_final_ham_endings(self):
        storyboard = {"narration_flow_mode": "conversational-chain"}
        beats = self.valid_beats()
        beats[-2]["narration"] = "사임 뜻을 전했다고 함."

        errors = cc_helper.validate_narration_flow(storyboard, beats)

        self.assertTrue(any("마지막 두 beat" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
