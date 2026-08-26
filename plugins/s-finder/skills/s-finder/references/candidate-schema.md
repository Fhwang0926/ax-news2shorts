# Candidate input contract

Create one JSON document for each research batch. Timestamps must be ISO 8601 values with a timezone. Public counts must be exact non-negative integers or `null`.

```json
{
  "schema_version": 1,
  "collection_method": "browser_or_public_web",
  "collected_at": "2026-08-26T20:00:00+09:00",
  "topic": "unusual skills",
  "platform_checks": [
    {
      "platform": "youtube",
      "status": "ok",
      "query": "unexpected skilled worker shorts",
      "evidence": [
        "The public Shorts result and video page were inspected."
      ]
    },
    {
      "platform": "tiktok",
      "status": "blocked",
      "query": "unexpected skill",
      "evidence": [
        "The public result page did not expose verifiable post metrics."
      ]
    }
  ],
  "candidates": [
    {
      "id": "youtube-skill-001",
      "platform": "youtube",
      "url": "https://www.youtube.com/shorts/example01",
      "title": "Public title",
      "creator": "Visible creator name",
      "published_at": "2026-08-26T08:30:00+00:00",
      "summary": "A worker uses an unfamiliar method and reveals why it is faster at the end.",
      "observed_action": "The worker changes the tool angle, repeats one motion, and reveals the finished result.",
      "story_pattern": "hidden-principle",
      "content_fingerprint": "worker-tool-angle-finished-result",
      "metrics": {
        "views": 1800000,
        "likes": 94000,
        "comments": 7400,
        "shares": null
      },
      "metric_evidence": [
        "The public post displayed 1,800,000 views, 94,000 likes, and 7,400 comments at collection time."
      ],
      "evidence_urls": [
        "https://www.youtube.com/shorts/example01"
      ],
      "research_evidence": [
        "The public post was playable and the described action was visible."
      ],
      "inspection": {
        "publicly_visible": true,
        "content_observed": true,
        "short_form_or_clippable": true
      },
      "features": {
        "viral_momentum": 95,
        "hook": 92,
        "story_twist": 88,
        "explainability": 94,
        "visual_clarity": 90,
        "editability": 84
      },
      "feature_reasons": {
        "viral_momentum": "The exact public reach is high relative to the short upload age.",
        "hook": "The unfamiliar tool angle creates a clear first-screen question.",
        "story_twist": "The finished result resolves why the strange motion was used.",
        "explainability": "Korean narration can explain the technique and its purpose.",
        "visual_clarity": "The action and result remain understandable without the original language.",
        "editability": "The subject stays centered and the setup-to-payoff sequence is concise."
      },
      "korean_gap": {
        "queries": [
          "특이한 공구 각도 작업 기술",
          "작업자가 도구를 기울여 쓰는 이유"
        ],
        "similar_results_count": 2,
        "evidence": [
          "Two genuinely similar Korean videos were found across the focused queries."
        ]
      },
      "source_trace": {
        "status": "probable_original",
        "confidence": 82,
        "probable_original_url": "https://www.youtube.com/shorts/example01",
        "evidence": [
          "The visible handle matches the uploader.",
          "Located reposts point back to this account."
        ]
      },
      "rights": {
        "status": "unknown",
        "evidence": [
          "No reuse permission was located during public research."
        ]
      },
      "risk_flags": [],
      "recommendation_reason": "The visible action raises an immediate question and Korean explanation adds useful technical context."
    }
  ]
}
```

## Allowed values

- `platform`: `youtube`, `tiktok`, `instagram`, `x`, `reddit`, `other`
- platform check `status`: `ok`, `blocked`, `unavailable`
- `story_pattern`: `result-curiosity`, `unexpected-ability`, `culture-gap`, `hidden-principle`, `backstory`, `other`
- `source_trace.status`: `verified_original`, `probable_original`, `repost_only`, `unknown`
- `rights.status`: `owned`, `licensed`, `permission_confirmed`, `unknown`, `not_permitted`
- `risk_flags`: values listed in [scoring.md](scoring.md), except the two automatically derived flags may be omitted

Use `content_fingerprint` only when visible evidence supports that records show the same underlying event. Do not use a broad topic label as a fingerprint.
