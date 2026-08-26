# Candidate input

The root is either an array or an object with candidates. Each candidate requires:

    {
      "id": "stable-id",
      "platform": "tiktok",
      "canonical_url": "https://www.tiktok.com/@creator/video/1234567890",
      "video_id": "1234567890",
      "creator": "@creator",
      "published_at": "2026-08-01T12:00:00+09:00",
      "collected_at": "2026-08-19T10:00:00+09:00",
      "collector": "public canonical page review",
      "metric_source_url": "https://www.tiktok.com/@creator/video/1234567890",
      "scene_summary": "처음에는 장애물을 피하던 개가 다시 돌아와 뛰어넘는다.",
      "content_explanation": {
        "story_flow": "개가 장애물 앞에서 멈추고 뒤로 물러난다. 잠시 뒤 다시 달려와 장애물을 뛰어넘는 장면으로 끝난다.",
        "appeal": "첫 실패 뒤 재시도가 바로 이어져 성공 여부를 확인하게 만든다.",
        "adaptation_note": "재도전과 성공이 분명해 짧은 도전형 이야기로 재구성할 수 있다.",
        "limitations": "실패와 성공 외의 관계 변화는 적어 긴 이야기로 늘리기 어렵다."
      },
      "animal": {
        "species": "dog",
        "observable_behavior": ["장애물 앞에서 멈춤", "뒤로 물러난 뒤 뛰어넘음"]
      },
      "state_changes": ["멈춤", "재시도", "성공"],
      "metrics": {
        "views": 5000000,
        "likes": 300000,
        "comments": 8000,
        "shares": 25000
      },
      "sensitive": {
        "is_sensitive": false,
        "categories": [],
        "welfare_note": ""
      },
      "rights": {
        "status": "unknown",
        "evidence": "public page only"
      },
      "editorial_fit": {
        "first_frame_hook": 18,
        "state_change_density": 17,
        "payoff_clarity": 19,
        "event_completeness": 14,
        "relationship_roles": 7,
        "vertical_edit_fit": 9,
        "korean_context_fit": 4
      },
      "penalties": {
        "explanation_over_5s": false,
        "static_over_10s": false,
        "text_translation_only": false,
        "missing_resolution": false,
        "near_full_reupload": false
      }
    }

platform is tiktok or youtube_shorts. YouTube canonical URLs must use youtube.com/shorts/<id>.

Candidate scores are editorial comparisons, not predicted views. Do not tune a component merely to promote a preferred result.

`content_explanation` is required for newly researched candidates. Describe visible events and editing potential, not assumed animal emotion or intent. `story_flow` explains the opening through payoff, `appeal` identifies the observable retention mechanism, `adaptation_note` states a grounded transformation direction, and `limitations` records thin source material, unclear payoff, rights, welfare, age, or other practical constraints. Older candidate files without this object remain readable; their ranked Markdown marks missing explanations explicitly.
