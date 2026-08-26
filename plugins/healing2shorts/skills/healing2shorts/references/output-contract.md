# Project output contract

```text
<project-dir>/
├── project.json
├── story-source.json
├── video-source.json
├── storyboard.json
├── rights-manifest.json
├── script.md
├── publish.json
├── assets/
│   ├── source/
│   ├── narration/
│   └── rights/
├── previews/
│   ├── contact-sheet.jpg
│   └── crop-preview.jpg
├── outputs/
│   ├── review.mp4
│   └── short.mp4
├── edit-package/
│   ├── clips/
│   ├── audio/
│   ├── metadata/
│   ├── captions.srt
│   └── edit-manifest.json
├── render-report.json
├── youtube-upload.json
└── youtube-upload.md
```

## Storyboard

`storyboard.json`이 유일한 렌더 타임라인입니다. 신규 대화형 story contract v3는 `cold_open`, `setup`, `problem`, `clue`, `escalation`, `reveal`, `afterglow`의 정확히 7개 장면과 10~14개 대사를 사용하며 전체는 40~45초입니다. 콜드 오픈은 2–3초, 나머지는 각각 3–8초입니다. 기존 v2 사건형 7개 장면과 v1의 6–8개 장면도 다시 열 수 있습니다.

`story-source.json`에는 선택된 후보의 `story_score`와 `recommendation.best_candidate_id`, `recommendation.best_candidate_reason`, `recommendation.selected_was_best`를 보존합니다. BEST가 아닌 후보도 사용자가 선택할 수 있습니다.

각 장면 필드:

- `id`, `beat`, `duration`
- `source_start_seconds`, `source_duration_seconds`
- `source_text_status`: `none`, `non_chinese_only`, `chinese_present`, `unknown`
- `caption`, `narration`
- v3 필수 `dialogue_turn_ids`: 해당 장면에 포함된 대사 ID
- 선택적 프로젝트 상대 경로 `narration_audio`

화면 자막은 렌더 시 최대 2줄로 감쌉니다. 장면은 서로 다른 원본 구간을 사용하고 원본보다 긴 내레이션은 마지막 프레임 유지로 맞춥니다.

v3 프로젝트의 기본 `project.json presentation.style`은 `dialogue_clean`, `header_style`은 `curiosity_band`입니다. 상단 약 20%를 불투명한 주제 여백으로 확보하고 구체적인 인물·반복을 담은 `topic_title`, 아직 답을 밝히지 않는 `topic_hook`을 표시합니다. 별도의 작은 분류 문구는 표시하지 않습니다. `topic_hook`은 반전이나 결말을 먼저 말하지 않고 평소와 달라진 한 가지를 질문으로 남깁니다. 현재 발화는 화자 라벨 없이 화면 중앙에 배경 상자 없는 외곽선 글자로 표시하고 해당 Typecast 발화 길이에 맞춰 다음 문구로 교체합니다. 기존 프로젝트의 `legacy_card`와 `header_style=overlay`는 유지합니다. `narration.speaker_voices`가 있으면 내레이터와 인물별 Typecast voice ID를 연결하고, 한 장면에서 내레이터의 연결 뒤에 인물의 직접 인용이 나오면 대사 순서대로 서로 다른 음성을 합칩니다.

`presentation`의 v3 기본 필드는 `title_position: top_band`, `caption_position: center`, `caption_background: false`, `topic_title`, `topic_hook`입니다. 명시하지 않은 `topic_title`은 프로젝트 제목, `topic_hook`은 스토리의 `central_question`을 사용합니다. 상단 밴드와 중앙 자막 사이에는 투명 영역을 유지해 음식 영상이 바로 시작된 것처럼 보여야 합니다.

`chinese_present` 장면은 검토·최종 렌더 모두 차단하고 다른 원본 구간으로 교체합니다. `unknown`은 검토본 경고, 게시 준비 오류입니다. 플러그인은 원본 문자나 워터마크를 삭제·블러·가림 처리하지 않습니다.

## Rights gates

- `not_permitted`: 검토·최종 렌더 모두 차단
- `negotiation_pending`: 검토 렌더와 편집 패키지만 허용, `publish_blocked=true`
- `owned`, `licensed`, `permission_confirmed`: 권리 증빙과 검토 승인이 있으면 최종 렌더 가능
- 민감 주제가 있으면 `sensitive_reviewed=true`가 필요

최종 검증에는 `story_reviewed`, `visual_reviewed`, `rights_reviewed`, `upload_reviewed`가 모두 필요합니다. Typecast를 사용할 때 실제 API 키와 음성 생성 성공을 별도로 확인합니다.

## Render contract

- 검토본 `outputs/review.mp4`: 540x960, 30fps, H.264/AAC, v3는 40–45초, 기존 계약은 30–45초, CRF 23
- 최종본 `outputs/short.mp4`: 720x1280, 30fps, H.264/AAC, v3는 40–45초, 기존 계약은 30–45초, CRF 20
- 편집 패키지 장면 클립: 720x1280
- 원본 음악은 기본 음소거
- 신규 v3 기본 BGM은 잔잔한 단조 화음의 `synthetic_melancholy`, 권리 표시는 `synthetic_original`, 시작 `bgm_volume`은 0.90입니다. `continuous_bgm=true`이면 전체 길이 BGM WAV 하나를 편집 패키지에 기록하고 장면 경계에서 재시작하지 않습니다. 실제 렌더 음량을 확인해 대사를 덮으면 낮춥니다.
- 허가된 ASMR만 낮게 혼합
- Typecast 내레이션 또는 명시적 `--no-tts` 기술 검토
- 검은 마지막 프레임 없음
- 실제 업로드 없음
- 권리 확인 HTTPS 직접 원본만 자동 가져오기, 도우인 페이지·CDN 자동 다운로드 없음

`validate --publish-ready`와 최종 MP4 성공은 기록된 입력 기준의 로컬 준비 상태입니다. 법률 판단, 플랫폼 승인, 수익화 보장이 아닙니다.
