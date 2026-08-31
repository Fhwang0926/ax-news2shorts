import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "cc_helper.py"
SPEC = importlib.util.spec_from_file_location("cc_helper_youtube_upload", SCRIPT)
cc_helper = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(cc_helper)


class YouTubeUploadHandoffTest(unittest.TestCase):
    def build_fixture(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        project_dir = Path(temporary.name)
        (project_dir / "handoff").mkdir()
        (project_dir / "research.json").write_text(
            json.dumps(
                {
                    "sources": [
                        {
                            "id": "source-01",
                            "publisher": "공식 기관",
                            "title": "공식 자료",
                            "url": "https://example.com/source",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        storyboard = {"title": {"white": "논란 뒤 인물이", "yellow": "내려놓은 자리"}}
        project = {
            "status": "local_review_only",
            "publish_blocked": True,
            "youtube_upload_mode": cc_helper.YOUTUBE_UPLOAD_MODE,
            "youtube_upload": {
                "status": "copy_ready",
                "title": "논란 뒤 공식 자리에서 물러난 인물",
                "description": "공개 자료를 바탕으로 정리한 이슈 해설입니다.",
                "hashtags": ["#이슈정리", "#쇼츠"],
                "tags": ["이슈 정리", "쇼츠"],
                "pinned_comment": "여러분은 이 상황 어떻게 봄?",
                "category": "people_and_blogs",
                "language": "ko",
                "audience": "not_made_for_kids",
                "altered_content": True,
                "altered_content_reason": "편집용 AI 일러스트를 사용함.",
                "recommended_visibility": "private",
                "thumbnail": storyboard["title"],
                "source_ids": ["source-01"],
            },
        }
        return project_dir, project, storyboard

    def test_validates_and_writes_copy_ready_upload_handoff(self):
        project_dir, project, storyboard = self.build_fixture()

        errors, warnings = cc_helper.validate_youtube_upload(
            project_dir, project, storyboard
        )
        cc_helper.write_youtube_upload_handoff(project_dir, project, storyboard)

        self.assertEqual(errors, [])
        self.assertTrue(any("권리 검토 전 게시" in warning for warning in warnings))
        payload = json.loads(
            (project_dir / "handoff" / "youtube-upload.json").read_text(
                encoding="utf-8"
            )
        )
        markdown = (project_dir / "handoff" / "youtube-upload.md").read_text(
            encoding="utf-8"
        )
        self.assertEqual(payload["recommended_visibility"], "private")
        self.assertEqual(payload["sources"][0]["id"], "source-01")
        self.assertIn(project["youtube_upload"]["title"], markdown)
        self.assertIn(project["youtube_upload"]["pinned_comment"], markdown)

    def test_rejects_public_visibility_and_unknown_source_when_publish_blocked(self):
        project_dir, project, storyboard = self.build_fixture()
        project["youtube_upload"]["recommended_visibility"] = "public"
        project["youtube_upload"]["source_ids"] = ["source-missing"]

        errors, _warnings = cc_helper.validate_youtube_upload(
            project_dir, project, storyboard
        )

        self.assertTrue(any("private" in error for error in errors))
        self.assertTrue(any("research.json과 연결되지 않습니다" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
