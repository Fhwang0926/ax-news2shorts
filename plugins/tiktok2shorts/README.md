# TikTok2Shorts — 동물 상황극형 Shorts

TikTok에서 이미 바이럴된 **동물 원본만** 선별하고, 확인 가능한 행동을 사람 사는 하소연에 빗댄 한국어 상황극 세로 MP4로 만드는 로컬 전용 플러그인입니다.

참조한 [동물 쇼츠](https://www.youtube.com/shorts/LRno_GdZ6Ys)의 상단 정보·중앙 원본 화면·하단 큰 서사 자막 구조를 바탕으로, 채널명·로고·문구를 복제하지 않은 `animal-emotion-story-v1` 템플릿을 사용합니다.

## 제공 기능

- TikTok URL·동물 카테고리·종·실제 행동 근거가 갖춰진 후보만 순위에 포함
- 확인된 100만 이상 조회수와 참여 지표를 기준으로 동물 후보 최대 3개 비교
- 화이트보드 대상일 때 첫 2초 훅·행동 다양성·단순화 후 결말·윤곽 명확성을 별도 검증
- 사용자가 고른 원본의 다운로드·해시·원본 링크·권리 상태 보존
- 장면별 실제 행동과 한국어 상황극 자막의 근거 연결
- `관찰` · `보호자 설명` · `행동 해석`과 실제 행동 근거는 프로젝트 문서에 보존하고 영상 화면의 분석 배지는 제거
- 실제 위치와 행동에 맞춰 동물마다 한 번 정한 사람 역할을 마지막까지 유지
- 상단에는 원본 TikTok 채널명만 일반 텍스트로 고정하고 `원본 채널` 배지는 제거하며, 역할명·대사·하소연은 하단에만 표시
- 원본에 영어 등 외국어 내장 자막이 있으면 검토한 자막 영역만 블러하고, 같은 뜻을 첫 하단 한국어 상황극 자막에 통합해 하나의 읽기 흐름으로 정리
- 블러 좌표·크기·강도를 장면 데이터와 편집 지시서에 기록하고, 원본 워터마크·채널 정보·동물 얼굴은 블러 대상에서 제외
- 장면별 흐름에 맞춘 생성 무보컬 배경음 또는 공식 출처·재사용 라이선스·필수 출처 문구·파일 해시가 모두 기록된 로컬 무보컬 음원
- 움직이는 원본을 연속으로 사용할 때 `no_scene_transition`으로 장면 사이 페이드·이미지 전환 효과 제거
- 마지막 `conclusion`에는 `hold_last_frame`으로 실제 마지막 유효 프레임을 짧게 고정해 검은 종료 화면 방지
- 상단 고정 채널 정보·중앙 원본 장면·하단 역할 및 서사 자막 템플릿으로 720x1280 H.264/AAC MP4 렌더
- 원본 링크, 별도 시나리오, 감정 해석 근거, 음악 프로필을 `delivery-note.md`로 함께 전달

기본값은 렌더러가 새로 만든 무보컬 음악입니다. 별도 음원은 검증된 라이선스와 출처를 프로젝트에 기록한 경우에만 사용할 수 있습니다. TTS·보컬·실제 업로드 기능은 포함하지 않습니다.

## 후보 조건

`score`는 다음을 모두 만족한 TikTok 동물 후보만 추천합니다.

- canonical TikTok HTTPS URL, 제작자, 게시 시각, 수집 경로, 지표 출처
- `category`: `animals`, `pets`, `wildlife` 등 동물 카테고리
- `animal.species`와 영상에서 보이는 `animal.observable_behavior`
- 실제 장면 요약과 하나 이상의 시점이 있는 조회수 지표
- 100만 이상 조회수 및 대규모 도달·공유·상호작용·참여율 중 하나의 보조 근거

확인되지 않은 조회수, 재업로드, 사람 중심 영상, 동물 여부가 불명확한 영상은 추천하지 않습니다. 후보는 최대 3개만 비교하고 사용자가 직접 하나를 선택합니다.

화이트보드 제작은 `format_fit.whiteboard` 근거를 채우고 `--target-format whiteboard`로 점수화합니다. 총점 70점과 훅·결말·구도·행동 수 하한을 모두 통과한 후보만 추천합니다.

## 플러그인으로 사용

Codex에서 `$tiktok2shorts`만 선택하거나 `화이트보드용 동물 영상 찾아줘`라고 짧게 요청하면 후보 조사를 바로 시작합니다. 사용자가 조회수·적합도·권리·후보 수 조건을 다시 적을 필요가 없습니다.

단독 호출에는 다음 기본값이 자동 적용됩니다.

- 검증된 조회수 100만 이상과 보조 참여 지표가 있는 TikTok 동물 원본
- 화이트보드 적합도 총점과 모든 필수 하한 통과
- 후보 최대 3개, 출처 링크와 권리 상태 표시
- 사용자 선택 전 다운로드·프로젝트 생성 금지

후보가 나오면 `1번`처럼 번호만 답하면 됩니다. 선택은 로컬 다운로드, 프레임 검토, 분석과 요청된 화이트보드 프로젝트 인계까지 진행한다는 뜻으로 처리하며, 접근 제한·설치 승인·사전 검사 실패 같은 실제 중단 사유가 없으면 같은 진행 확인을 반복하지 않습니다.

## 빠른 시작

    python3 scripts/tiktok2shorts.py doctor

    python3 scripts/tiktok2shorts.py score \
      --input examples/candidates.sample.json \
      --output /tmp/tiktok-animal-candidates.json \
      --target-format whiteboard

    python3 scripts/tiktok2shorts.py init \
      --candidates /tmp/tiktok-animal-candidates.json \
      --candidate-id animal-rescue-001

    python3 scripts/tiktok2shorts.py download \
      --project-dir outputs/tiktok2shorts/YYYY-MM-DD/<project-slug>

    python3 scripts/tiktok2shorts.py preview \
      --project-dir outputs/tiktok2shorts/YYYY-MM-DD/<project-slug>

프레임을 검토한 뒤 `viral-analysis.json`, `script.json`, `storyboard.json`, `music-plan.json`, `rights-manifest.json`을 채웁니다. 장면마다 실제 행동을 적은 `source_evidence`와 다음 구조를 넣어야 합니다.

    "animal_emotion": {
      "label": "낯선 공간을 경계하는 모습",
      "confidence": "inference",
      "evidence": ["꼬리를 내린 채 보호자 쪽을 바라봄"],
      "music_mood": "tension"
    }

`confidence`는 `observed`, `caregiver_report`, `inference` 중 하나입니다. 이 정보는 검증 문서와 전달 문서에 남기되 영상 화면에는 `동물 해설`, `행동 해석`, `근거` 배지를 표시하지 않습니다. `project.template.channel_label`은 상단에 고정되는 실제 원본 채널명이며 별도 `원본 채널` 배지는 붙이지 않습니다. 장면별 `headline`과 `korean_caption`은 모두 하단에 표시되며, 동물별 역할은 실제 동작과 위치에 맞춰 처음부터 끝까지 유지합니다.

원본 프레임에 외국어 자막이 박혀 있으면 `project.template.source_caption_handling`을 작성합니다. 반복되는 한 문장이라면 검토한 자막 영역만 블러하고 첫 장면의 큰 한국어 자막이 원문의 핵심 뜻과 상황극 훅을 함께 전달하게 합니다. 이후 장면은 실제 동작에 맞는 상황극만 이어 갑니다. 원문과 무관한 한국어 훅을 동시에 보여 주거나, 같은 번역을 작은 줄로 한 번 더 쌓지 않습니다.

영향받는 원본 영상 장면에는 `source_caption_blur`와 `source_caption_blur_region`을 적용합니다. 좌표와 크기는 원본 프레임 기준 0~1 비율이고, `radius`는 4~40입니다. 고정 자막은 연속 장면에 같은 값을 사용하며, 대표·경계 프레임에서 문자가 읽히지 않고 워터마크와 핵심 행동이 남는지 확인합니다.

    "source_caption_handling": {
      "mode": "blur_and_localize_bottom",
      "detected": true,
      "language": "en",
      "bridges": [
        {
          "scene_id": "scene-01-hook",
          "source_text": "Nobody wants to pet Gilbert even though he's got his best bow tie on.",
          "korean_text": "나비넥타이까지 했는데 아무도 쓰다듬어 주지 않음"
        }
      ]
    }

    "edit_actions": ["source_caption_blur"],
    "source_caption_blur_region": {
      "x": 0.08,
      "y": 0.60,
      "width": 0.84,
      "height": 0.17,
      "radius": 24
    }

원본 영상의 움직임을 끊지 않고 자막만 다음 이야기 비트로 바꾸려면 해당 영상 장면의 `edit_actions`에 `no_scene_transition`을 넣습니다. 이 옵션은 장면 사이 페이드나 별도 이미지 전환을 만들지 않습니다.

마지막 장면이 끝난 뒤 검게 비어 보이지 않게 하려면 최종 `conclusion` 장면에 `hold_last_frame`과 `hold_last_frame_seconds`를 넣습니다. 권장값은 0.5~1초입니다. 원본 끝에도 검은 프레임이 있으면 `hold_last_frame_source_offset_seconds`로 끝에서 0~1초 앞선 검토 프레임을 선택합니다. 장면 `duration`은 원본 사용 시간에서 이 오프셋을 뺀 뒤 고정 시간을 더한 값으로 기록합니다. 별도 검은 카드나 새 이미지를 만들지 않고 선택한 원본 프레임을 그대로 유지합니다.

    "duration": 3.55,
    "source_clip_seconds": 3.0,
    "edit_actions": ["no_scene_transition", "hold_last_frame"],
    "hold_last_frame_seconds": 0.8,
    "hold_last_frame_source_offset_seconds": 0.25

    python3 scripts/tiktok2shorts.py edit-plan \
      --project-dir outputs/tiktok2shorts/YYYY-MM-DD/<project-slug>

    python3 scripts/tiktok2shorts.py validate \
      --project-dir outputs/tiktok2shorts/YYYY-MM-DD/<project-slug> \
      --final

    python3 scripts/tiktok2shorts.py render \
      --project-dir outputs/tiktok2shorts/YYYY-MM-DD/<project-slug>

최종 렌더는 결론 뒤에 1.8초 무음 `구독 · 좋아요` CTA 샷을 한 번 붙이고 `outputs/short.mp4`, `render-report.json`, `delivery-note.md`, `edit-plan.md`, `youtube-upload.json`, `youtube-upload.md`를 만듭니다. `render-report.json`은 선택한 음악 모드와 출처를, `delivery-note.md`는 TikTok 원본 링크, 동물 행동·감정 해석 근거, 필요한 음악 출처 표기를 기록합니다.

    python3 scripts/tiktok2shorts.py upload-package --project-dir <project>

업로드 패키지는 제목·설명·태그·썸네일·고정 댓글·설정을 제공하되, 시청자층·합성 콘텐츠·프로모션·연령 제한·미확정 권리는 검토 대상으로 남기고 실제 업로드는 하지 않습니다.

## 안전·권리 경계

- 공개 TikTok은 재사용 허가가 아닙니다. `unknown` 권리 상태는 그대로 유지하며 로컬 검토용으로만 취급합니다.
- 원본 워터마크·채널 정보를 지우거나 원본 전체를 재업로드하지 않습니다. 외국어 내장 자막 블러는 검토한 자막 영역에만 적용하고 원문·한국어 연결 기록은 보존합니다.
- 학대, 구조, 질병, 사망, 미성년자, 치료 등 민감한 동물 복지 장면은 독립적인 출처를 확인하고, 확인되지 않은 감정·원인·의도를 단정하지 않습니다.
- 외부 업로드, 게시 예약, 저작권 판정, 수익화 판단은 이 플러그인의 범위 밖입니다.
