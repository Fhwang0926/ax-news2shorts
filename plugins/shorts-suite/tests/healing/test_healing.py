from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS))
SCRIPT = SCRIPTS / "healing.py"
SPEC = importlib.util.spec_from_file_location("shorts_suite_healing_cli", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class AuthorizedSourcePolicyTest(unittest.TestCase):
    def test_rejects_douyin_page_download(self) -> None:
        with self.assertRaisesRegex(MODULE.HealingShortsError, "도우인"):
            MODULE.authorized_source_url("https://www.douyin.com/video/123")

    def test_rejects_insecure_or_private_source(self) -> None:
        with self.assertRaisesRegex(MODULE.HealingShortsError, "HTTPS"):
            MODULE.authorized_source_url("http://media.example/video.mp4")
        with self.assertRaisesRegex(MODULE.HealingShortsError, "공개 인터넷"):
            MODULE.authorized_source_url("https://127.0.0.1/video.mp4")


class SourceTextPolicyTest(unittest.TestCase):
    def test_chinese_candidate_requires_six_text_free_segments(self) -> None:
        with self.assertRaisesRegex(MODULE.HealingShortsError, "6개 이상"):
            MODULE.video_text_profile(
                {"visual_text_status": "chinese_present", "text_free_segments": []}
            )

    def test_text_free_segments_create_clean_storyboard(self) -> None:
        candidate = {
            "visual_text_status": "chinese_present",
            "text_free_segments": [
                {"start_seconds": index * 2, "duration_seconds": 1.5}
                for index in range(6)
            ],
        }
        beats = [
            {"beat": beat, "caption": beat, "narration": f"{beat} narration"}
            for beat in MODULE.REQUIRED_BEATS
        ]
        storyboard = MODULE.create_storyboard(beats, 20.0, 36.0, candidate)
        self.assertEqual(
            [scene["source_text_status"] for scene in storyboard["scenes"]],
            ["none"] * 6,
        )


def event_candidate() -> dict:
    claims = [
        {"id": f"claim-{index:02d}", "text": f"fact {index}", "source_ids": ["source-01"]}
        for index in range(1, 5)
    ]
    claim_sequence = ["claim-01", "claim-01", "claim-02", "claim-02", "claim-03", "claim-04", "claim-04"]
    beats = [
        {
            "beat": beat,
            "caption": f"{beat} caption",
            "narration": f"{beat} narration",
            "claim_ids": [claim_sequence[index]],
        }
        for index, beat in enumerate(MODULE.EVENT_REQUIRED_BEATS)
    ]
    return {
        "id": "story-event-01",
        "contract_version": 2,
        "mode": "article",
        "title": "도시락이 두 개였던 이유",
        "selection_reason": "구체적인 물건과 새 사실로 반전이 완성됩니다.",
        "emotional_arc": "의문에서 걱정, 안도로 이동",
        "story_engine": "object_mystery",
        "anchor_event": "한 사람에게 도시락 두 개가 건네졌다.",
        "protagonist": "도시락을 전하는 봉사자",
        "central_question": "왜 한 사람에게 도시락이 두 개였을까?",
        "obstacle": "한 사람 몫이라는 선입견",
        "reveal": "집에서 기다리는 가족의 몫이었다.",
        "payoff_object": "두 번째 도시락",
        "sensitive_topics": [],
        "sources": [
            {
                "id": "source-01",
                "kind": "original",
                "publisher": "Fixture Original",
                "url": "https://example.com/event-original",
            },
            {
                "id": "source-02",
                "kind": "independent",
                "publisher": "Fixture Independent",
                "url": "https://example.org/event-independent",
            },
        ],
        "claims": claims,
        "story_score": {
            "total": 88,
            "hook_and_open_loop": 18,
            "character_and_event": 13,
            "tension_and_progression": 17,
            "reveal_and_payoff": 23,
            "spoken_naturalness": 8,
            "food_action_sync": 9,
            "reason": "물건의 의문이 새 사실로 풀리고 음식 동작과도 맞습니다.",
        },
        "beats": beats,
    }


def dialogue_candidate() -> dict:
    candidate = event_candidate()
    turns = [
        ("할머니", "오늘은 빵 하나만 줘요."),
        ("내레이터", "제가 이유를 물어보니, 할머니는 이렇게 말했어요."),
        ("할머니", "이제 기다리는 사람이 없거든."),
        ("내레이터", "혹시 가족분이냐고 다시 여쭤보니,"),
        ("할머니", "아파트 경비 아저씨야."),
        ("내레이터", "매일 빵을 드린 거냐고 묻자,"),
        ("할머니", "야간 근무 때 굶는 걸 봤거든."),
        ("내레이터", "그런데 오늘은 왜 하나만 사는지 물었습니다."),
        ("할머니", "오늘부터 낮 근무래."),
        ("내레이터", "빵 대신 뭘 가져가실 거냐고 묻자,"),
        ("할머니", "따뜻한 국수를 직접 끓여다주려고."),
        ("내레이터", "이러한 이야기를 듣고 싶으면 구독과 좋아요 눌러주세요."),
    ]
    candidate.update(
        {
            "id": "story-dialogue-01",
            "contract_version": 3,
            "mode": "anecdote",
            "title": "할머니가 매일 빵 두 개를 산 이유",
            "sources": [],
            "claims": [],
            "anecdote": {
                "origin_kind": "fictionalized",
                "consent_status": "fictionalized",
                "disclosure": "창작·재구성한 익명 사연입니다.",
                "identity_fields_removed": ["이름", "지역", "가게"],
            },
            "dialogue_turns": [
                {"id": f"turn-{index:02d}", "speaker": speaker, "text": value}
                for index, (speaker, value) in enumerate(turns, start=1)
            ],
            "story_score": {
                "total": 91,
                "hook_and_open_loop": 18,
                "character_and_event": 14,
                "tension_and_progression": 18,
                "reveal_and_payoff": 24,
                "spoken_naturalness": 9,
                "food_action_sync": 8,
                "reason": "두 인물의 대화가 오가며 마지막 행동으로 감정을 회수합니다.",
            },
        }
    )
    beat_dialogue = [
        (["turn-01"], "오늘은 빵 하나만 줘요."),
        (["turn-02", "turn-03"], "제가 이유를 물어보니, 할머니는 이렇게 말했어요. 이제 기다리는 사람이 없거든."),
        (["turn-04", "turn-05"], "혹시 가족분이냐고 다시 여쭤보니, 아파트 경비 아저씨야."),
        (["turn-06", "turn-07"], "매일 빵을 드린 거냐고 묻자, 야간 근무 때 굶는 걸 봤거든."),
        (["turn-08"], "그런데 오늘은 왜 하나만 사는지 물었습니다."),
        (["turn-09", "turn-10"], "오늘부터 낮 근무래. 빵 대신 뭘 가져가실 거냐고 묻자,"),
        (
            ["turn-11", "turn-12"],
            "따뜻한 국수를 직접 끓여다주려고. 이러한 이야기를 듣고 싶으면 구독과 좋아요 눌러주세요.",
        ),
    ]
    for beat, (turn_ids, narration) in zip(candidate["beats"], beat_dialogue):
        beat["claim_ids"] = []
        beat["dialogue_turn_ids"] = turn_ids
        beat["narration"] = narration
    return candidate


class StoryContractV2Test(unittest.TestCase):
    def test_event_story_uses_seven_variable_beats(self) -> None:
        candidate = event_candidate()
        root = {
            "version": 2,
            "selection_required": True,
            "best_candidate_id": candidate["id"],
            "best_candidate_reason": "가장 선명한 사건과 회수가 있습니다.",
            "candidates": [candidate],
        }
        recommendation = MODULE.validate_story_recommendation(root, root["candidates"])
        beats = MODULE.normalize_beats(candidate, contract_version=2)
        durations = MODULE.storyboard_durations(beats, 36.0, contract_version=2)
        self.assertEqual(recommendation["contract_version"], 2)
        self.assertEqual(len(durations), 7)
        self.assertEqual(durations[0], 2.5)
        self.assertAlmostEqual(sum(durations), 36.0, places=3)
        self.assertTrue(all(3.0 <= value <= 8.0 for value in durations[1:]))
        for target in (30.0, 45.0):
            boundary = MODULE.storyboard_durations(beats, target, contract_version=2)
            self.assertAlmostEqual(sum(boundary), target, places=3)
            self.assertTrue(2.0 <= boundary[0] <= 3.0)
            self.assertTrue(all(3.0 <= value <= 8.0 for value in boundary[1:]))

    def test_low_quality_event_story_cannot_be_best(self) -> None:
        candidate = event_candidate()
        candidate["story_score"].update(
            {
                "total": 69,
                "hook_and_open_loop": 10,
                "character_and_event": 10,
                "tension_and_progression": 12,
                "reveal_and_payoff": 17,
                "spoken_naturalness": 10,
                "food_action_sync": 10,
            }
        )
        root = {
            "version": 2,
            "selection_required": True,
            "best_candidate_id": candidate["id"],
            "best_candidate_reason": "임시 후보",
            "candidates": [candidate],
        }
        with self.assertRaisesRegex(MODULE.HealingShortsError, "70점 미만"):
            MODULE.validate_story_recommendation(root, root["candidates"])

    def test_reveal_requires_a_new_claim(self) -> None:
        candidate = event_candidate()
        candidate["beats"][5]["claim_ids"] = ["claim-01"]
        with self.assertRaisesRegex(MODULE.HealingShortsError, "새 claim"):
            MODULE.normalize_beats(candidate, contract_version=2)

    def test_review_and_final_render_profiles_are_separate(self) -> None:
        self.assertEqual(MODULE.render_settings(True), (540, 960, 23))
        self.assertEqual(MODULE.render_settings(False), (720, 1280, 20))

    def test_event_contract_supports_anonymized_anecdotes(self) -> None:
        candidate = event_candidate()
        candidate.update(
            {
                "id": "story-anecdote-event-01",
                "mode": "anecdote",
                "sources": [],
                "claims": [],
                "anecdote": {
                    "origin_kind": "fictionalized",
                    "consent_status": "fictionalized",
                    "disclosure": "사연을 바탕으로 재구성했습니다.",
                    "identity_fields_removed": ["이름", "지역"],
                },
            }
        )
        for beat in candidate["beats"]:
            beat["claim_ids"] = []
        root = {
            "version": 2,
            "selection_required": True,
            "best_candidate_id": candidate["id"],
            "best_candidate_reason": "구체적 사건과 반전이 있습니다.",
            "candidates": [candidate],
        }
        recommendation = MODULE.validate_story_recommendation(root, root["candidates"])
        self.assertEqual(recommendation["best_candidate_id"], candidate["id"])

    def test_legacy_fixture_remains_valid(self) -> None:
        fixture = Path(__file__).resolve().parent / "fixtures" / "article-story-candidates.json"
        root = MODULE.load_json(fixture)
        candidate = MODULE.candidate_by_id(root, root["best_candidate_id"], "story candidates")
        self.assertEqual(len(MODULE.normalize_beats(candidate)), 6)


class StoryContractV3Test(unittest.TestCase):
    def test_dialogue_story_requires_a_real_back_and_forth(self) -> None:
        candidate = dialogue_candidate()
        root = {
            "version": 3,
            "selection_required": True,
            "best_candidate_id": candidate["id"],
            "best_candidate_reason": "대화 왕복과 따뜻한 회수가 가장 선명합니다.",
            "candidates": [candidate],
        }
        recommendation = MODULE.validate_story_recommendation(root, root["candidates"])
        beats = MODULE.normalize_beats(candidate, contract_version=3)
        durations = MODULE.storyboard_durations(beats, 42.0, contract_version=3)
        self.assertEqual(recommendation["contract_version"], 3)
        self.assertEqual(len(beats), 7)
        self.assertEqual(sum(len(beat["dialogue_turn_ids"]) for beat in beats), 12)
        self.assertAlmostEqual(sum(durations), 42.0, places=3)

        storyboard = MODULE.create_storyboard(
            beats,
            42.0,
            42.0,
            {"visual_text_status": "none", "text_free_segments": []},
            contract_version=3,
        )
        errors: list[str] = []
        warnings: list[str] = []
        MODULE.validate_storyboard(
            storyboard,
            42.0,
            errors,
            warnings,
            publish_ready=False,
        )
        self.assertEqual(errors, [])

    def test_dialogue_story_rejects_article_summary_mode(self) -> None:
        candidate = dialogue_candidate()
        candidate["mode"] = "article"
        with self.assertRaisesRegex(MODULE.HealingShortsError, "anecdote"):
            MODULE.normalize_beats(candidate, contract_version=3)

    def test_dialogue_story_rejects_too_few_turns(self) -> None:
        candidate = dialogue_candidate()
        candidate["dialogue_turns"] = candidate["dialogue_turns"][:9]
        with self.assertRaisesRegex(MODULE.HealingShortsError, "10~14"):
            MODULE.normalize_beats(candidate, contract_version=3)

    def test_dialogue_story_rejects_short_runtime(self) -> None:
        candidate = dialogue_candidate()
        beats = MODULE.normalize_beats(candidate, contract_version=3)
        with self.assertRaisesRegex(MODULE.HealingShortsError, "40~45"):
            MODULE.storyboard_durations(beats, 36.0, contract_version=3)

    def test_dialogue_story_rejects_speaker_labels_in_captions(self) -> None:
        candidate = dialogue_candidate()
        candidate["beats"][0]["caption"] = "할머니: 오늘은 빵 하나만 줘요"
        with self.assertRaisesRegex(MODULE.HealingShortsError, "화자 라벨"):
            MODULE.normalize_beats(candidate, contract_version=3)

    def test_clean_dialogue_style_has_curiosity_band_and_no_caption_panel(self) -> None:
        from PIL import Image

        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "overlay.png"
            MODULE.draw_overlay(
                {"caption": "오늘은\n빵 하나만 줘요", "beat": "cold_open"},
                {
                    "title": "할머니가 매일 빵 두 개를 산 이유",
                    "presentation": {
                        "style": "dialogue_clean",
                        "header_style": "curiosity_band",
                        "topic_title": "매일 빵 두 개를 사던 할머니",
                        "topic_hook": "그날은 왜 하나만 샀을까?",
                    },
                },
                {
                    "mode": "anecdote",
                    "central_question": "할머니는 왜 오늘만 빵을 하나 샀을까?",
                    "anecdote": {"disclosure": "창작·재구성한 익명 사연입니다."},
                },
                output,
            )
            with Image.open(output) as image:
                self.assertEqual(image.getpixel((10, 10)), (4, 52, 88, 255))
                self.assertEqual(image.getpixel((10, 447)), (70, 218, 214, 255))
                self.assertEqual(image.getpixel((10, 470))[3], 0)
                self.assertEqual(image.getpixel((60, 1400))[3], 0)

    def test_dialogue_caption_cues_follow_each_voice_duration(self) -> None:
        cues = MODULE.dialogue_caption_cues(
            [
                {
                    "id": "turn-01",
                    "speaker": "내레이터",
                    "text": "먼저 물었습니다.",
                    "duration_seconds": 1.2,
                },
                {
                    "id": "turn-02",
                    "speaker": "할머니",
                    "text": "이렇게 말했어요.",
                    "duration_seconds": 1.5,
                },
            ],
            3.2,
        )
        self.assertEqual(cues[0]["start_seconds"], 0.0)
        self.assertEqual(cues[0]["end_seconds"], 1.38)
        self.assertEqual(cues[1]["start_seconds"], 1.38)
        self.assertEqual(cues[1]["end_seconds"], 3.2)
        self.assertEqual([cue["text"] for cue in cues], ["먼저 물었습니다.", "이렇게 말했어요."])


class EmotionalBackgroundMusicTest(unittest.TestCase):
    def test_melancholy_music_is_one_slow_minor_track(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "bgm.wav"
            with mock.patch.object(MODULE, "run_checked") as run_checked:
                MODULE.create_ambient_audio(
                    destination,
                    42.0,
                    mode="synthetic_melancholy",
                )
            command = run_checked.call_args.args[0]
            self.assertTrue(any("130.81" in value for value in command))
            self.assertTrue(any("d=1.2" in value for value in command))

    def test_emotional_music_uses_scene_chords_and_soft_echo(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "bgm.wav"
            with mock.patch.object(MODULE, "run_checked") as run_checked:
                MODULE.create_ambient_audio(
                    destination,
                    6.0,
                    mode="synthetic_emotional",
                    scene_index=1,
                )
            command = run_checked.call_args.args[0]
            self.assertTrue(any("174.61" in value for value in command))
            self.assertTrue(any("aecho=" in value for value in command))

    def test_unknown_music_mode_is_rejected(self) -> None:
        with self.assertRaisesRegex(MODULE.HealingShortsError, "배경음 모드"):
            MODULE.create_ambient_audio(
                Path("unused.wav"),
                6.0,
                mode="downloaded_track",
            )


if __name__ == "__main__":
    unittest.main()
