from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "globalize.py"
SPEC = importlib.util.spec_from_file_location("shorts_suite_globalize", SCRIPT_PATH)
assert SPEC and SPEC.loader
sg = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sg)
FIXTURES = Path(__file__).resolve().parent / "fixtures"


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class ShortsGlobalizerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_workspace_root_prefers_the_local_marketplace_checkout(self) -> None:
        workspace = self.root / "workspace"
        plugin_root = workspace / "plugins" / "shorts-suite"
        (workspace / ".agents" / "plugins").mkdir(parents=True)
        plugin_root.mkdir(parents=True)
        (workspace / ".agents" / "plugins" / "marketplace.json").write_text(
            "{}\n", encoding="utf-8"
        )
        nested = workspace / "projects" / "shorts-suite" / "globalize"
        nested.mkdir(parents=True)
        self.assertEqual(sg.find_workspace_root(nested, plugin_root), workspace.resolve())

    def make_research_project(self, *, sensitive: bool = False) -> Path:
        project_dir = self.root / "project"
        project_dir.mkdir()
        project = {
            "schema_version": 1,
            "plugin": "shorts-suite:globalize",
            "plugin_version": "0.1.0",
            "id": "AbCdEfGhI12",
            "status": "ingested",
            "created_at": "2026-08-27T00:00:00+00:00",
            "updated_at": "2026-08-27T00:00:00+00:00",
            "locale": "en-US",
            "source_url": "https://www.youtube.com/shorts/AbCdEfGhI12",
            "approvals": {
                "topic": {"approved": True, "approved_at": "2026-08-27T00:00:00+00:00"},
                "research": {"approved": False, "approved_at": None},
                "script": {"approved": False, "approved_at": None},
                "preview": {"approved": False, "approved_at": None},
            },
            "publish_blocked": True,
        }
        source = {
            "schema_version": 1,
            "video_id": "AbCdEfGhI12",
            "url": "https://www.youtube.com/shorts/AbCdEfGhI12",
            "role": "signal_only_not_fact_source",
            "video_downloaded": False,
        }
        reasons = ["accident"] if sensitive else []
        analysis = {
            "schema_version": 1,
            "video_id": "AbCdEfGhI12",
            "source_url": source["url"],
            "transcript_available": True,
            "topic": {
                "summary": "A Korean safety design became a useful public discussion.",
                "who": "Local transit staff and passengers",
                "event": "A small design choice changed passenger behavior.",
                "cause": "The old layout caused repeated confusion.",
                "result": "The revised layout made the safer action easier.",
                "controversy": "No material controversy was found.",
                "viral_reason": "The before and after contrast is immediately visual.",
                "origin": "KR_ORIGINAL",
            },
            "structure": {
                "hook": "A familiar object appears to work differently.",
                "context": "The location and routine are introduced.",
                "problem": "The everyday safety problem is shown.",
                "twist": "A small design choice changes the outcome.",
                "reaction": "Passengers adopt the safer behavior.",
                "ending": "The design principle becomes the takeaway.",
            },
            "source_claim_order": ["claim-01", "claim-02", "claim-03"],
            "source_beat_order": ["hook", "context", "problem", "twist", "reaction", "ending"],
            "sensitive_topic": sensitive,
            "sensitive_reasons": reasons,
            "global_score_input": {
                "features": {
                    key: {"score": 90, "reason": "The verified material supports this score clearly."}
                    for key in sg.FEATURE_WEIGHTS
                },
                "penalties": {
                    key: {"applied": False, "reason": ""}
                    for key in sg.PENALTIES
                },
            },
            "updated_at": "2026-08-27T00:00:00+00:00",
        }
        sources = [
            {
                "id": "source-01",
                "url": "https://agency.example/report",
                "title": "Official safety report",
                "publisher": "Public Safety Agency",
                "published_at": "2026-08-20",
                "source_type": "official" if sensitive else "independent",
            },
            {
                "id": "source-02",
                "url": "https://daily.example/story",
                "title": "Independent reporting",
                "publisher": "Daily Example",
                "published_at": "2026-08-21",
                "source_type": "independent",
            },
        ]
        if sensitive:
            sources.append(
                {
                    "id": "source-03",
                    "url": "https://journal.example/analysis",
                    "title": "Independent analysis",
                    "publisher": "Example Journal",
                    "published_at": "2026-08-22",
                    "source_type": "independent",
                }
            )
        source_ids = [item["id"] for item in sources]
        facts = {
            "schema_version": 1,
            "sensitive_topic": sensitive,
            "claims": [
                {
                    "id": f"claim-{index:02d}",
                    "statement": statement,
                    "core": True,
                    "status": "confirmed",
                    "confidence": "high",
                    "source_ids": source_ids,
                }
                for index, statement in enumerate(
                    (
                        "The original layout created a recurring safety problem.",
                        "The revised design made the safer action easier to notice.",
                        "Independent reports described a measurable behavior change.",
                    ),
                    start=1,
                )
            ],
        }
        write_json(project_dir / "project.json", project)
        write_json(project_dir / "source.json", source)
        (project_dir / "transcript.txt").write_text(
            "이 자막은 사건의 맥락과 문제, 변화, 반응, 결론을 충분한 길이로 설명합니다.\n",
            encoding="utf-8",
        )
        write_json(project_dir / "source-analysis.json", analysis)
        write_json(project_dir / "sources.json", {"schema_version": 1, "sources": sources})
        write_json(project_dir / "fact-sheet.json", facts)
        write_json(project_dir / "content-en.json", sg.load_template("content-en.template.json"))
        write_json(project_dir / "storyboard.json", sg.load_template("storyboard.template.json"))
        write_json(project_dir / "originality.json", sg.load_template("originality.template.json"))
        return project_dir

    def fill_script(self, project_dir: Path) -> None:
        narration = [
            "A quiet Korean station hid a clever safety idea in plain sight.",
            "The original layout repeatedly pushed distracted passengers toward one risky choice.",
            "Reports from separate sources confirmed the confusion was more than anecdotal.",
            "Then designers changed one ordinary detail instead of adding loud warnings.",
            "The safer action suddenly became the easiest option for everyday riders.",
            "That shift changed behavior without asking people to study new rules.",
            "The surprise is not advanced technology but thoughtful placement and timing.",
            "Good design can protect people before they even notice the lesson.",
        ]
        claim_order = [
            "claim-02",
            "claim-03",
            "claim-01",
            "claim-02",
            "claim-03",
            "claim-01",
            "claim-02",
            "claim-03",
        ]
        content = {
            "schema_version": 1,
            "locale": "en-US",
            "angles": [
                {"id": "angle-01", "angle": "Invisible safety design", "rationale": "It turns a local detail into a universal design lesson."},
                {"id": "angle-02", "angle": "Behavior before rules", "rationale": "It explains why easier choices can outperform instructions."},
                {"id": "angle-03", "angle": "Small change, broad effect", "rationale": "It emphasizes a visual transformation with practical stakes."},
            ],
            "selected_angle_id": "angle-01",
            "titles": [
                "The Safety Trick Hidden in Plain Sight",
                "Why This Tiny Design Change Worked",
                "A Smarter Way to Guide a Crowd",
                "The Station Detail Everyone Missed",
                "Good Design Changed Their Behavior",
            ],
            "selected_title": "The Safety Trick Hidden in Plain Sight",
            "title_lines": ["THE HIDDEN", "SAFETY TRICK"],
            "hooks": [
                {"id": "hook-01", "text": "This ordinary detail quietly changed what people did.", "rationale": "It creates curiosity without revealing the payoff too early."},
                {"id": "hook-02", "text": "One tiny station change made the safer choice automatic.", "rationale": "It leads with a concrete result and visible setting."},
                {"id": "hook-03", "text": "The best safety feature here is almost invisible.", "rationale": "It frames the design as an unexpected discovery."},
            ],
            "selected_hook_id": "hook-01",
            "selection_reasons": {
                "angle": "This angle carries the verified lesson across cultural contexts.",
                "title": "This title creates curiosity without claiming more than the evidence.",
                "hook": "This hook changes the reveal order and states no unverified fact.",
            },
            "script_paragraphs": [
                {"id": f"paragraph-{index:02d}", "text": text, "claim_ids": [claim_order[index - 1]]}
                for index, text in enumerate(narration, start=1)
            ],
            "script_text": " ".join(narration),
        }
        roles = ["hook", "context", "evidence", "event", "impact", "problem", "twist", "payoff"]
        storyboard = {
            "schema_version": 1,
            "scenes": [
                {
                    "id": f"scene-{index:02d}",
                    "role": roles[index - 1],
                    "narration": text,
                    "caption": f"Scene {index} normal caption",
                    "highlight": f"Scene {index} highlight",
                    "duration_seconds": 4.0,
                    "claim_ids": [claim_order[index - 1]],
                    "asset": {
                        "type": "BROLL",
                        "preferred_source": "Licensed stock library",
                        "search_queries": [f"station safety design scene {index}"],
                        "rights_status": "YELLOW",
                        "status": "planned",
                        "asset_path": "",
                    },
                }
                for index, text in enumerate(narration, start=1)
            ],
        }
        originality = {
            "schema_version": 1,
            "source_claim_order": ["claim-01", "claim-02", "claim-03"],
            "output_claim_order": ["claim-02", "claim-03", "claim-01"],
            "source_beat_order": ["hook", "context", "problem", "twist", "reaction", "ending"],
            "output_beat_order": roles,
            "claim_order_similarity_percent": 66.7,
            "beat_order_similarity_percent": 50.0,
            "structure_similarity_percent": 66.7,
            "hook_function_same": False,
            "payoff_function_same": False,
            "lexical_check": {
                "status": "not_applicable_cross_language",
                "reason": "Korean-to-English lexical overlap is not a meaningful originality measure.",
            },
            "semantic_review": {
                "decision": "PASS",
                "hook": "The output opens with a design mystery, not the source reveal.",
                "conclusion": "The output ends on a universal principle instead of a reaction.",
                "information_order": "Evidence precedes the design reveal and changes the source sequence.",
                "expression": "The analogies and phrasing were written independently in English.",
            },
            "decision": "PASS",
        }
        write_json(project_dir / "content-en.json", content)
        write_json(project_dir / "storyboard.json", storyboard)
        write_json(project_dir / "originality.json", originality)
        project = json.loads((project_dir / "project.json").read_text(encoding="utf-8"))
        project["status"] = "script_drafted"
        write_json(project_dir / "project.json", project)

    def test_url_normalization_playlist_and_path_safety(self) -> None:
        video_id = "AbCdEfGhI12"
        self.assertEqual(sg.extract_video_id(f"https://www.youtube.com/shorts/{video_id}"), video_id)
        self.assertEqual(sg.extract_video_id(f"https://youtu.be/{video_id}"), video_id)
        self.assertEqual(sg.extract_video_id(f"https://youtube.com/watch?v={video_id}"), video_id)
        with self.assertRaises(sg.GlobalizerError):
            sg.extract_video_id(f"https://youtube.com/watch?v={video_id}&list=PL123")
        with self.assertRaises(sg.GlobalizerError):
            sg.project_destination(projects_root=self.root / "projects", video_id=video_id, project_dir=str(self.root / "outside"))
        existing = self.root / "projects" / "2026-08-27" / video_id
        existing.mkdir(parents=True)
        with self.assertRaises(sg.GlobalizerError):
            sg.project_destination(projects_root=self.root / "projects", video_id=video_id, project_dir=str(existing))

    def test_caption_fixtures_and_authorized_transcript(self) -> None:
        cases = json.loads((FIXTURES / "caption-cases.json").read_text(encoding="utf-8"))
        manual = sg.choose_caption_track(cases["manual_and_automatic"])
        self.assertEqual(manual["kind"], "manual")
        automatic = sg.choose_caption_track(cases["automatic_only"])
        self.assertEqual(automatic["kind"], "automatic")
        self.assertIsNone(sg.choose_caption_track(cases["none"]))
        transcript = sg.read_transcript_file(str(FIXTURES / "authorized-transcript-ko.txt"))
        self.assertIn("권한 있는 한국어 자막", transcript)
        vtt = "WEBVTT\n\n00:00:00.000 --> 00:00:01.000\n첫 문장\n\n00:00:01.000 --> 00:00:02.000\n둘째 문장\n"
        self.assertEqual(sg.caption_text_from_vtt(vtt), "첫 문장 둘째 문장")

    def test_caption_tls_uses_certifi_fallback_without_disabling_verification(self) -> None:
        verify_paths = SimpleNamespace(cafile=None, capath=None)
        fallback = self.root / "certifi.pem"
        with mock.patch.object(sg.ssl, "get_default_verify_paths", return_value=verify_paths), mock.patch.object(
            sg, "certifi_ca_file", return_value=fallback
        ):
            configuration = sg.caption_tls_configuration()
        self.assertTrue(configuration["available"])
        self.assertEqual(configuration["mode"], "certifi-fallback")
        self.assertEqual(configuration["cafile"], str(fallback))

        class Response:
            def __enter__(self) -> "Response":
                return self

            def __exit__(self, *_args: object) -> None:
                return None

            def read(self, _limit: int) -> bytes:
                return b"WEBVTT\n\n00:00:00.000 --> 00:00:01.000\ncaption text\n"

        context = mock.Mock(spec=sg.ssl.SSLContext)
        with mock.patch.object(sg, "caption_ssl_context", return_value=context), mock.patch.object(
            sg.urllib.request, "urlopen", return_value=Response()
        ) as urlopen:
            transcript = sg.fetch_caption(
                {"url": "https://captions.example/ko.vtt", "ext": "vtt"}
            )
        self.assertEqual(transcript, "caption text")
        self.assertIs(urlopen.call_args.kwargs["context"], context)

    def test_brainbulb_discovery_reads_only_the_shorts_tab(self) -> None:
        fixture = (FIXTURES / "brainbulb-shorts.jsonl").read_text(encoding="utf-8")
        completed = SimpleNamespace(returncode=0, stdout=fixture, stderr="")
        with mock.patch.object(sg, "yt_dlp_available", return_value=True), mock.patch.object(
            sg.subprocess, "run", return_value=completed
        ) as run:
            payload = sg.discover_brainbulb_shorts(3)

        command = run.call_args.args[0]
        self.assertIn("--flat-playlist", command)
        self.assertIn("--skip-download", command)
        self.assertNotIn("--cookies", command)
        self.assertEqual(command[-1], sg.BRAINBULB_CHANNEL["shorts_url"])
        self.assertEqual(payload["source"]["channel_id"], "UCbr855WAFQvAX-An7IcHFXg")
        self.assertTrue(payload["selection_required"])
        self.assertFalse(payload["monitoring_enabled"])
        self.assertEqual(len(payload["candidates"]), 3)
        self.assertEqual(payload["candidates"][0]["candidate_id"], "candidate-01")
        self.assertEqual(
            payload["candidates"][0]["url"],
            "https://www.youtube.com/shorts/jc_BRabpPfc",
        )

    def test_brainbulb_discovery_rejects_bad_limits_and_other_channels(self) -> None:
        for limit in (0, 11):
            with self.assertRaises(sg.GlobalizerError):
                sg.discover_brainbulb_shorts(limit)

        fixture = (FIXTURES / "brainbulb-shorts.jsonl").read_text(encoding="utf-8")
        fixture = fixture.replace("UCbr855WAFQvAX-An7IcHFXg", "UC00000000000000000000", 1)
        completed = SimpleNamespace(returncode=0, stdout=fixture, stderr="")
        with mock.patch.object(sg, "yt_dlp_available", return_value=True), mock.patch.object(
            sg.subprocess, "run", return_value=completed
        ):
            with self.assertRaises(sg.GlobalizerError):
                sg.discover_brainbulb_shorts(3)

        args = sg.build_parser().parse_args(["discover"])
        self.assertEqual(args.limit, 3)

    def test_init_caption_and_transcript_fixtures(self) -> None:
        cases = json.loads((FIXTURES / "caption-cases.json").read_text(encoding="utf-8"))
        base_metadata = {
            "id": "AbCdEfGhI12",
            "title": "Fixture Short",
            "channel": "Fixture Channel",
            "duration": 34,
            "description": "Fixture metadata",
            "view_count": 100,
        }

        def args_for(name: str, transcript_file: str = "") -> SimpleNamespace:
            return SimpleNamespace(
                url="https://www.youtube.com/shorts/AbCdEfGhI12",
                transcript_file=transcript_file,
                project_dir="",
                projects_root=str(self.root / name),
            )

        for name, case, expected_kind in (
            ("manual", cases["manual_and_automatic"], "manual"),
            ("automatic", cases["automatic_only"], "automatic"),
        ):
            metadata = {**base_metadata, **case}
            with mock.patch.object(sg, "extract_youtube_metadata", return_value=metadata), mock.patch.object(
                sg, "fetch_caption", return_value="충분한 길이의 fixture 한국어 자막이 정상적으로 수집되었습니다."
            ):
                result = sg.initialize_project(args_for(name))
            self.assertEqual(result["status"], "ingested")
            self.assertEqual(result["transcript_source"], expected_kind)

        with mock.patch.object(
            sg, "extract_youtube_metadata", return_value={**base_metadata, **cases["none"]}
        ):
            pending = sg.initialize_project(args_for("none"))
        self.assertEqual(pending["status"], "transcript_pending")
        self.assertEqual(pending["transcript_source"], "unavailable")
        self.assertFalse(pending["resumed"])

        resume_metadata = {**base_metadata, **cases["automatic_only"]}
        with mock.patch.object(
            sg, "extract_youtube_metadata", return_value=resume_metadata
        ), mock.patch.object(
            sg, "fetch_caption", return_value="인증서 복구 후 같은 프로젝트에서 자막 수집을 안전하게 재개했습니다."
        ):
            resumed = sg.initialize_project(args_for("none"))
        self.assertEqual(resumed["status"], "ingested")
        self.assertEqual(resumed["transcript_source"], "automatic")
        self.assertTrue(resumed["resumed"])
        resumed_dir = Path(resumed["project_dir"])
        resumed_project = json.loads((resumed_dir / "project.json").read_text(encoding="utf-8"))
        self.assertEqual(resumed_project["status"], "ingested")
        self.assertIn("안전하게 재개", (resumed_dir / "transcript.txt").read_text(encoding="utf-8"))
        with mock.patch.object(
            sg, "extract_youtube_metadata", return_value=resume_metadata
        ), mock.patch.object(
            sg, "fetch_caption", return_value="이미 완료된 프로젝트를 덮어쓰면 안 됩니다."
        ):
            with self.assertRaises(sg.GlobalizerError):
                sg.initialize_project(args_for("none"))

        transcript_path = FIXTURES / "authorized-transcript-ko.txt"
        with mock.patch.object(
            sg, "extract_youtube_metadata", return_value={**base_metadata, **cases["none"]}
        ):
            provided = sg.initialize_project(args_for("provided", str(transcript_path)))
        self.assertEqual(provided["status"], "ingested")
        self.assertEqual(provided["transcript_source"], "user_provided")

    def test_score_boundaries_and_origin_overrides(self) -> None:
        self.assertEqual([sg.decision_for(value) for value in (80, 65, 50, 49)], ["MAKE", "REVIEW", "HOLD", "SKIP"])
        project_dir = self.make_research_project()
        analysis = json.loads((project_dir / "source-analysis.json").read_text(encoding="utf-8"))
        analysis["topic"]["origin"] = "GLOBAL_REPOST"
        self.assertEqual(sg.compute_global_score(analysis)["decision"], "SKIP")
        analysis["topic"]["origin"] = "UNKNOWN"
        self.assertEqual(sg.compute_global_score(analysis)["decision"], "REVIEW")

    def test_research_contract_and_sensitive_source_gate(self) -> None:
        ordinary = self.make_research_project()
        errors, _warnings = sg.validate_research(ordinary)
        self.assertEqual(errors, [])
        sources = json.loads((ordinary / "sources.json").read_text(encoding="utf-8"))
        sources["sources"][1]["url"] = "https://agency.example/second-report"
        write_json(ordinary / "sources.json", sources)
        errors, _warnings = sg.validate_research(ordinary)
        self.assertTrue(any("independent source domains" in error for error in errors))

        self.temporary_directory.cleanup()
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        sensitive = self.make_research_project(sensitive=True)
        errors, _warnings = sg.validate_research(sensitive)
        self.assertEqual(errors, [])
        sources = json.loads((sensitive / "sources.json").read_text(encoding="utf-8"))
        sources["sources"][0]["source_type"] = "independent"
        write_json(sensitive / "sources.json", sources)
        errors, _warnings = sg.validate_research(sensitive)
        self.assertTrue(any("official or primary" in error for error in errors))

    def test_review_and_sensitive_projects_require_research_approval(self) -> None:
        project_dir = self.make_research_project(sensitive=True)
        score = sg.score_project(project_dir)
        self.assertEqual(score["decision"], "MAKE")
        self.fill_script(project_dir)
        errors, _warnings = sg.validate_script(project_dir)
        self.assertTrue(any("Research approval is required" in error for error in errors))
        with self.assertRaises(sg.GlobalizerError):
            sg.approve_stage(project_dir, "script")
        sg.approve_stage(project_dir, "research")
        errors, _warnings = sg.validate_script(project_dir)
        self.assertEqual(errors, [])

    def test_signal_short_cannot_be_fact_source_through_watch_url(self) -> None:
        project_dir = self.make_research_project()
        sources = json.loads((project_dir / "sources.json").read_text(encoding="utf-8"))
        sources["sources"][0]["url"] = "https://youtube.com/watch?v=AbCdEfGhI12"
        write_json(project_dir / "sources.json", sources)
        errors, _warnings = sg.validate_research(project_dir)
        self.assertTrue(any("alternate YouTube URL" in error for error in errors))

    def test_originality_similarity_thresholds(self) -> None:
        source = list("abcdefghij")
        seventy_percent = list("abcdefgxyz")
        self.assertEqual(sg.structure_similarity(source, seventy_percent), 70.0)
        self.assertEqual(sg.structure_similarity(["a", "b", "c"], ["b", "c", "a"]), 66.7)

    def test_full_package_flow_requires_script_approval(self) -> None:
        project_dir = self.make_research_project()
        score = sg.score_project(project_dir)
        self.assertEqual(score["decision"], "MAKE")
        self.fill_script(project_dir)
        script_errors, _warnings = sg.validate_script(project_dir)
        self.assertEqual(script_errors, [])
        with self.assertRaises(sg.GlobalizerError):
            sg.package_project(project_dir)
        approval = sg.approve_stage(project_dir, "script")
        self.assertEqual(approval["status"], "script_approved")
        packaged = sg.package_project(project_dir)
        self.assertFalse(packaged["preview_approved"])
        self.assertTrue(packaged["publish_blocked"])
        package_errors, _warnings = sg.validate_package(project_dir)
        self.assertEqual(package_errors, [])
        manifest = json.loads((project_dir / "capcut-manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["template"], "global-short-v1")
        self.assertEqual(manifest["scenes"][0]["slot"], "MEDIA_01")
        self.assertTrue(all(scene["asset_status"] == "planned" and scene["asset_path"] == "" for scene in manifest["scenes"]))
        self.assertTrue(all(scene["caption"] and scene["search_queries"] and scene["rights_status"] for scene in manifest["scenes"]))
        ranges = sg.parse_srt_ranges((project_dir / "subtitles.srt").read_text(encoding="utf-8"))
        self.assertEqual(len(ranges), 8)
        self.assertTrue(all(end > start for start, end in ranges))
        self.assertFalse(any(path.suffix.lower() in sg.MEDIA_SUFFIXES for path in project_dir.rglob("*")))
        with self.assertRaises(sg.GlobalizerError):
            sg.package_project(project_dir)
        (project_dir / "subtitles.srt").write_text(
            "1\n00:00:04,000 --> 00:00:05,000\nFirst\n\n2\n00:00:03,000 --> 00:00:06,000\nSecond\n",
            encoding="utf-8",
        )
        package_errors, _warnings = sg.validate_package(project_dir)
        self.assertTrue(any("SRT" in error for error in package_errors))

    def test_word_scene_duration_and_originality_failures_block_script(self) -> None:
        project_dir = self.make_research_project()
        sg.score_project(project_dir)
        self.fill_script(project_dir)
        content = json.loads((project_dir / "content-en.json").read_text(encoding="utf-8"))
        content["script_text"] = "Too short."
        write_json(project_dir / "content-en.json", content)
        errors, _warnings = sg.validate_script(project_dir)
        self.assertTrue(any("80-120 words" in error for error in errors))

        self.fill_script(project_dir)
        storyboard = json.loads((project_dir / "storyboard.json").read_text(encoding="utf-8"))
        storyboard["scenes"] = storyboard["scenes"][:7]
        write_json(project_dir / "storyboard.json", storyboard)
        errors, _warnings = sg.validate_script(project_dir)
        self.assertTrue(any("8-10 scenes" in error for error in errors))

        self.fill_script(project_dir)
        storyboard = json.loads((project_dir / "storyboard.json").read_text(encoding="utf-8"))
        for scene in storyboard["scenes"]:
            scene["duration_seconds"] = 3.0
        write_json(project_dir / "storyboard.json", storyboard)
        errors, _warnings = sg.validate_script(project_dir)
        self.assertTrue(any("30-40 seconds" in error for error in errors))

        self.fill_script(project_dir)
        originality = json.loads((project_dir / "originality.json").read_text(encoding="utf-8"))
        originality["source_claim_order"] = ["claim-02", "claim-03", "claim-01"]
        originality["claim_order_similarity_percent"] = 100
        originality["structure_similarity_percent"] = 100
        originality["decision"] = "REWRITE_REQUIRED"
        analysis = json.loads((project_dir / "source-analysis.json").read_text(encoding="utf-8"))
        analysis["source_claim_order"] = ["claim-02", "claim-03", "claim-01"]
        write_json(project_dir / "source-analysis.json", analysis)
        write_json(project_dir / "originality.json", originality)
        errors, _warnings = sg.validate_script(project_dir)
        self.assertTrue(any("requires a rewrite" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
