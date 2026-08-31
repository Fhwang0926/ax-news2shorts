import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image


SCRIPT = Path(__file__).parents[1] / "scripts" / "cc_helper.py"
SPEC = importlib.util.spec_from_file_location("cc_helper_evidence", SCRIPT)
cc_helper = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(cc_helper)


class EvidenceFirstVisualValidationTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.project = Path(self.temporary.name)
        (self.project / "research.json").write_text(
            json.dumps(
                {
                    "facts": [
                        {
                            "id": "fact-01",
                            "claim": "직접 확인된 사건",
                            "source_ids": ["source-01"],
                        }
                    ]
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    def make_asset(
        self,
        asset_id,
        *,
        synthetic=False,
        evidence_role="incident_evidence",
        person_class="none",
        media_type=None,
        derived_from="",
        size=(800, 600),
        approved=True,
        non_identifying=False,
        fallback_reason="",
        portrait=False,
    ):
        folder = "generated" if synthetic else "source"
        source = self.project / "assets" / folder / f"{asset_id}.png"
        source.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", size, "navy").save(source)
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        normalized = self.project / "assets" / "normalized" / f"{asset_id}.png"
        normalized.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (1080, 1920), "navy").save(normalized)
        return {
            "id": asset_id,
            "sha256": digest,
            "width": size[0],
            "height": size[1],
            "media_type": media_type or ("illustration" if synthetic else "image"),
            "source_method": "generated_file" if synthetic else "web_page",
            "source_path": source.relative_to(self.project).as_posix(),
            "normalized_path": normalized.relative_to(self.project).as_posix(),
            "synthetic": synthetic,
            "derived_from": derived_from,
            "person_class": person_class,
            "evidence_role": evidence_role,
            "review": {
                "content": "approved" if approved else "review_required",
                "quality": "approved" if approved else "review_required",
                "reviewed_at": "2026-08-28T00:00:00+00:00" if approved else "",
                "asset_sha256": digest if approved else "",
                "fact_ids": ["fact-01"],
                "content_description": "현재 장면과 직접 연결되는 화면",
                "main_subject_visible": True,
                "crop_safe": True,
                "non_identifying": non_identifying,
            },
            "fallback_reason": fallback_reason,
            "portrait_style": "editorial-animation" if portrait else "",
            "portrait_review": {
                "identity_preserved": portrait,
                "clothing_preserved": portrait,
                "context_preserved": portrait,
            },
            "visual_text": "none" if synthetic else "source_original",
            "rights_status": "unreviewed",
        }

    def validate(
        self,
        assets,
        *,
        requirement="direct_incident",
        fact_ids=None,
        person_visual_mode="",
        public_figure_style_mode="",
        display_validation=False,
    ):
        storyboard = {
            "visual_validation_mode": "evidence-first",
            "scenes": [
                {
                    "id": "scene-01",
                    "beat_id": "beat-01",
                    "asset_id": assets[-1]["id"],
                    "fact_ids": ["fact-01"] if fact_ids is None else fact_ids,
                    "visual_requirement": requirement,
                }
            ],
        }
        if person_visual_mode:
            storyboard["person_visual_mode"] = person_visual_mode
        if public_figure_style_mode:
            storyboard["public_figure_style_mode"] = public_figure_style_mode
        if display_validation:
            storyboard["display_validation_mode"] = cc_helper.DISPLAY_VALIDATION_MODE
        return cc_helper.validate_evidence_first_visuals(
            self.project,
            storyboard,
            {"assets": assets},
        )

    def add_display_review(self, asset, *, focus="subject"):
        normalized = self.project / asset["normalized_path"]
        normalized_sha = hashlib.sha256(normalized.read_bytes()).hexdigest()
        asset["normalization"] = {
            **cc_helper.image_normalization_layout(asset["width"], asset["height"]),
            "normalized_sha256": normalized_sha,
        }
        asset["review"].update(
            {
                "display_focus": focus,
                "preview_checked": True,
                "evidence_readable": focus in {"source_text", "mixed"},
                "visual_anchor_terms": ["핵심 문구"]
                if focus in {"source_text", "mixed"}
                else [],
                "normalized_sha256": normalized_sha,
            }
        )
        return asset

    def test_accepts_real_incident_evidence(self):
        errors, _warnings = self.validate([self.make_asset("asset-real")])
        self.assertEqual(errors, [])

    def test_rejects_synthetic_claiming_direct_incident(self):
        asset = self.make_asset("asset-fake", synthetic=True)
        errors, _warnings = self.validate([asset])
        self.assertTrue(any("합성 이미지는 실제 사건" in error for error in errors))

    def test_keeps_low_resolution_real_evidence_with_warning(self):
        asset = self.make_asset("asset-small", size=(120, 150))
        errors, warnings = self.validate([asset])
        self.assertEqual(errors, [])
        self.assertTrue(any("해상도가 낮습니다" in warning for warning in warnings))

    def test_accepts_general_widescreen_layout_above_display_thresholds(self):
        asset = self.add_display_review(
            self.make_asset("asset-widescreen", size=(1600, 900))
        )

        errors, _warnings = self.validate([asset], display_validation=True)

        self.assertEqual(errors, [])

    def test_rejects_small_source_text_layout(self):
        asset = self.add_display_review(
            self.make_asset("asset-small-text", size=(930, 430)),
            focus="source_text",
        )

        errors, _warnings = self.validate([asset], display_validation=True)

        self.assertTrue(
            any("텍스트 증거가 모바일 화면에서 너무 작습니다" in error for error in errors)
        )

    def test_accepts_readable_vertical_source_text_composite(self):
        asset = self.add_display_review(
            self.make_asset("asset-readable-composite", size=(1080, 1920)),
            focus="source_text",
        )

        errors, _warnings = self.validate([asset], display_validation=True)

        self.assertEqual(errors, [])

    def test_rejects_changed_normalized_image_sha(self):
        asset = self.add_display_review(
            self.make_asset("asset-changed-normalized", size=(1080, 1920)),
            focus="source_text",
        )
        normalized = self.project / asset["normalized_path"]
        Image.new("RGB", (1080, 1920), "maroon").save(normalized)

        errors, _warnings = self.validate([asset], display_validation=True)

        self.assertTrue(any("정규화 이미지가 바뀌어" in error for error in errors))
        self.assertTrue(any("최종 표시 검수 SHA-256" in error for error in errors))

    def test_rejects_missing_content_and_quality_review(self):
        asset = self.make_asset("asset-pending", approved=False)
        errors, _warnings = self.validate([asset])
        self.assertTrue(any("내용 검수가 approved" in error for error in errors))
        self.assertTrue(any("품질 검수가 approved" in error for error in errors))

    def test_accepts_public_figure_editorial_animation_from_real_photo(self):
        parent = self.make_asset(
            "asset-parent",
            evidence_role="source_photo",
            person_class="public_figure",
        )
        derivative = self.make_asset(
            "asset-animation",
            synthetic=True,
            evidence_role="editorial_animation",
            person_class="public_figure",
            derived_from=parent["id"],
            portrait=True,
        )
        errors, _warnings = self.validate(
            [parent, derivative], requirement="direct_subject"
        )
        self.assertEqual(errors, [])

    def test_accepts_public_figure_editorial_animation_from_source_capture(self):
        parent = self.make_asset(
            "asset-parent",
            evidence_role="source_capture",
            person_class="public_figure",
        )
        derivative = self.make_asset(
            "asset-animation",
            synthetic=True,
            evidence_role="editorial_animation",
            person_class="public_figure",
            derived_from=parent["id"],
            portrait=True,
        )
        errors, _warnings = self.validate(
            [parent, derivative], requirement="direct_subject"
        )
        self.assertEqual(errors, [])

    def test_accepts_obvious_editorial_eye_band_contract(self):
        parent = self.make_asset(
            "asset-parent",
            evidence_role="source_photo",
            person_class="public_figure",
        )
        derivative = self.make_asset(
            "asset-animation",
            synthetic=True,
            evidence_role="editorial_animation",
            person_class="public_figure",
            derived_from=parent["id"],
            portrait=True,
        )
        derivative["portrait_style_strength"] = cc_helper.PORTRAIT_STYLE_STRENGTH
        derivative["portrait_eye_motif"] = cc_helper.PORTRAIT_EYE_MOTIF
        derivative["portrait_review"].update(
            {
                "style_obvious_at_preview": True,
                "eye_motif_present": True,
                "ruler_ticks_visible": True,
                "eye_motif_editorial_only": True,
            }
        )

        errors, _warnings = self.validate(
            [parent, derivative],
            requirement="direct_subject",
            public_figure_style_mode=cc_helper.PUBLIC_FIGURE_STYLE_MODE,
        )

        self.assertEqual(errors, [])

    def test_rejects_eye_band_without_obvious_style_and_editorial_only_review(self):
        parent = self.make_asset(
            "asset-parent",
            evidence_role="source_photo",
            person_class="public_figure",
        )
        derivative = self.make_asset(
            "asset-animation",
            synthetic=True,
            evidence_role="editorial_animation",
            person_class="public_figure",
            derived_from=parent["id"],
            portrait=True,
        )
        derivative["review"]["non_identifying"] = True

        errors, _warnings = self.validate(
            [parent, derivative],
            requirement="direct_subject",
            public_figure_style_mode=cc_helper.PUBLIC_FIGURE_STYLE_MODE,
        )

        self.assertTrue(any("화풍 강도" in error for error in errors))
        self.assertTrue(any("editorial ruler eye-band가 없습니다" in error for error in errors))
        self.assertTrue(any("비식별 처리로 기록할 수 없습니다" in error for error in errors))

    def test_rejects_eye_band_on_non_identifying_private_person_fallback(self):
        asset = self.make_asset(
            "asset-private",
            synthetic=True,
            evidence_role="non_identifying_fallback",
            person_class="private_person",
            non_identifying=True,
            fallback_reason="직접 자료는 개인정보 노출 위험이 있음",
        )
        asset["portrait_eye_motif"] = cc_helper.PORTRAIT_EYE_MOTIF

        errors, _warnings = self.validate([asset], requirement="contextual")

        self.assertTrue(any("눈가림 바만으로 비식별 처리할 수 없습니다" in error for error in errors))
        self.assertTrue(any("비식별 대체 화면에는 editorial ruler eye-band" in error for error in errors))

    def test_rejects_editorial_animation_from_synthetic_source_capture(self):
        parent = self.make_asset(
            "asset-parent",
            synthetic=True,
            evidence_role="source_capture",
            person_class="public_figure",
        )
        derivative = self.make_asset(
            "asset-animation",
            synthetic=True,
            evidence_role="editorial_animation",
            person_class="public_figure",
            derived_from=parent["id"],
            portrait=True,
        )
        errors, _warnings = self.validate(
            [parent, derivative], requirement="direct_subject"
        )
        self.assertTrue(
            any("검수된 실제 인물 자료에서 한 번만 파생" in error for error in errors)
        )

    def test_rejects_editorial_animation_from_private_person_source_capture(self):
        parent = self.make_asset(
            "asset-parent",
            evidence_role="source_capture",
            person_class="private_person",
        )
        derivative = self.make_asset(
            "asset-animation",
            synthetic=True,
            evidence_role="editorial_animation",
            person_class="public_figure",
            derived_from=parent["id"],
            portrait=True,
        )
        errors, _warnings = self.validate(
            [parent, derivative], requirement="direct_subject"
        )
        self.assertTrue(
            any("공개 인물 실제 사진이어야" in error for error in errors)
        )

    def test_rejects_editorial_animation_without_real_parent(self):
        derivative = self.make_asset(
            "asset-animation",
            synthetic=True,
            evidence_role="editorial_animation",
            person_class="public_figure",
            derived_from="asset-missing",
            portrait=True,
        )
        errors, _warnings = self.validate([derivative], requirement="direct_subject")
        self.assertTrue(any("실제 인물 원본" in error for error in errors))

    def test_rejects_editorial_animation_as_incident_evidence(self):
        parent = self.make_asset(
            "asset-parent",
            evidence_role="source_photo",
            person_class="public_figure",
        )
        derivative = self.make_asset(
            "asset-animation",
            synthetic=True,
            evidence_role="editorial_animation",
            person_class="public_figure",
            derived_from=parent["id"],
            portrait=True,
        )
        errors, _warnings = self.validate([parent, derivative])
        self.assertTrue(any("direct_incident" in error for error in errors))

    def test_accepts_non_identifying_private_person_fallback(self):
        asset = self.make_asset(
            "asset-private",
            synthetic=True,
            evidence_role="non_identifying_fallback",
            person_class="private_person",
            non_identifying=True,
            fallback_reason="직접 자료는 개인정보 노출 위험이 있음",
        )
        errors, warnings = self.validate([asset], requirement="contextual")
        self.assertEqual(errors, [])
        self.assertTrue(any("비식별 대체 화면" in warning for warning in warnings))

    def test_rejects_selected_real_asset_without_people_treatment(self):
        asset = self.make_asset("asset-real")
        errors, _warnings = self.validate(
            [asset],
            person_visual_mode="stylize-or-remove",
        )
        self.assertTrue(any("화면 속 사람 처리 검수가 필요" in error for error in errors))

    def test_accepts_selected_real_asset_with_people_cropped_out(self):
        asset = self.make_asset("asset-real")
        asset["review"]["people_visible"] = False
        asset["review"]["people_treatment"] = "cropped_out"
        errors, _warnings = self.validate(
            [asset],
            person_visual_mode="stylize-or-remove",
        )
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
