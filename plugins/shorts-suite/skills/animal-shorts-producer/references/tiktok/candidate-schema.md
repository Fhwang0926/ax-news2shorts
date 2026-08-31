# TikTok 동물 후보 입력 스키마

`score`는 JSON의 `candidates` 배열 또는 이전 `ranked_candidates`를 읽습니다. TikTok 동물 원본만 추천하며, 동물 여부나 실제 행동 근거가 없는 후보는 거절합니다.

## 필수 필드

| 필드 | 의미 |
| --- | --- |
| id | 안정적인 후보 ID |
| platform | 반드시 `tiktok` |
| url | canonical HTTPS TikTok 원본 URL |
| creator | 원본 업로더 |
| collector | Creative Center, 공개 리서치, 승인된 공급자 등 수집 경로 |
| metrics_source_url | 기록한 지표를 확인한 HTTPS 페이지 또는 export 참조 |
| published_at | 원본 게시 시각 ISO 8601 |
| category | `animals`, `pets`, `wildlife`, `animal-rescue` 등 동물 카테고리 |
| animal.species | 영상의 동물 종 또는 품종 |
| animal.observable_behavior | 영상에 실제로 보이는 행동을 12자 이상으로 설명 |
| title 또는 description | 사람이 읽을 수 있는 주제 |
| content_summary | 실제 핵심 장면을 20자 이상으로 설명 |
| metrics | 하나 이상의 시점이 있는 실제 지표 |

각 `metrics` 항목에는 `collected_at`과 음수가 아닌 `views`가 필요합니다. `likes`, `comments`, `shares`는 실제 출처가 값 자체를 제공하지 않을 때만 0일 수 있습니다.

## 바이럴 및 동물 게이트

후보는 다음을 모두 만족해야 `ranked_candidates`에 들어갑니다.

1. 최신 확인 조회수가 1,000,000 이상이다.
2. 3,000,000 조회, 10,000 공유, 100,000 상호작용, 8% 참여율 중 하나 이상을 확인했다.
3. 표의 모든 출처·동물·행동 필드가 있다.

해시태그 총 조회수, 광고 지표 백분위, 댓글의 추측은 개별 영상 조회수나 동물 행동 근거로 쓰지 않습니다.

## 화이트보드 대상 적합도

`score --target-format whiteboard`를 사용할 때는 후보마다 `format_fit.whiteboard`를 추가합니다. 원본 조회수와 별개로, 실제 장면을 선화로 단순화해도 훅과 결말이 유지되는지 공개 프레임 또는 검토 가능한 미리보기 근거로 평가합니다.

| 필드 | 점수 | 필수 근거 |
| --- | ---: | --- |
| `hook` | 0–20 | 첫 2초 안에 그림으로 인식되는 동물·행동 |
| `distinct_visual_beats` | 최대 20 | 시간 참조와 실제 행동이 다른 장면 3개 이상, 장면당 5점 |
| `abstraction_payoff` | 0–20 | 질감·렌즈 왜곡 없이도 남는 변화·반전·결말 |
| `composition` | 0–10 | 단순한 배경, 분리된 사물, 명확한 윤곽 |
| `disqualifiers` | 통과 조건 | 현실 질감 의존, 음성·자막 의존, 반복 구도 등 부적합 사유가 없어야 함 |

전체 점수는 검증된 바이럴 25, 화이트보드 훅 20, 서로 다른 행동 20, 추상화 후 결말 20, 윤곽·구도 10, 한국 관련성 5입니다. 70점 이상이어야 하며 `hook >= 12`, `abstraction_payoff >= 12`, `composition >= 6`, 서로 다른 행동 3개 이상을 모두 만족해야 합니다. 점수만으로 필수 하한을 대신할 수 없습니다.

```json
{
  "id": "animal-rescue-001",
  "platform": "tiktok",
  "url": "https://www.tiktok.com/@creator/video/123",
  "creator": "creator",
  "collector": "Creative Center export",
  "metrics_source_url": "https://www.tiktok.com/@creator/video/123",
  "published_at": "2026-08-15T09:00:00+09:00",
  "category": "animals",
  "animal": {
    "species": "개 (믹스견)",
    "observable_behavior": "문 앞에서 보호자를 바라보고 꼬리를 낮춘 채 잠시 멈추는 모습이 보입니다.",
    "welfare_risk": false
  },
  "title": "Already viral reunion moment",
  "content_summary": "보호자를 기다리던 개가 문 앞에서 다가오는 사람을 바라보는 핵심 장면입니다.",
  "metrics": [
    {
      "collected_at": "2026-08-15T12:00:00+09:00",
      "views": 5200000,
      "likes": 420000,
      "comments": 18000,
      "shares": 62000
    }
  ],
  "korea_relevance_score": 72,
  "youtube_korea_saturation_score": 26,
  "format_fit": {
    "whiteboard": {
      "hook": {
        "score": 17,
        "evidence": "첫 장면에서 개와 보호자의 손이 분리된 윤곽으로 바로 보입니다."
      },
      "distinct_visual_beats": [
        {
          "time_reference": "0-2s",
          "observed_action": "개가 문 앞에 멈춰 보호자 쪽을 바라봅니다."
        },
        {
          "time_reference": "2-5s",
          "observed_action": "개가 보호자 쪽으로 몇 걸음 다가옵니다."
        },
        {
          "time_reference": "5-8s",
          "observed_action": "개가 내민 손 앞에서 고개를 들어 올립니다."
        },
        {
          "time_reference": "8-11s",
          "observed_action": "개와 보호자의 손이 닿는 결과가 보입니다."
        }
      ],
      "abstraction_payoff": {
        "score": 18,
        "evidence": "다가옴과 손이 닿는 결과가 단순한 위치 변화만으로 전달됩니다."
      },
      "composition": {
        "score": 8,
        "evidence": "개와 손이 배경에서 분리되고 복잡한 문자나 겹친 물체가 없습니다."
      },
      "disqualifiers": []
    }
  },
  "rights": {
    "permission_status": "unknown",
    "permission_reference": ""
  }
}
```

`animal.welfare_risk: true`는 구조, 학대, 질병, 사망 등 복지·안전 민감 장면을 뜻합니다. 최종 설명에는 독립적 사실 출처가 필요하며, 감정과 원인을 단정할 수 없습니다.
