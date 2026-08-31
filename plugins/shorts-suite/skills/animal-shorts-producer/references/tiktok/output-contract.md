# 동물 감정 해설형 프로젝트 계약

`init`은 하나의 `local_only` 동물 Shorts 프로젝트를 만듭니다.

| 파일 | 목적 |
| --- | --- |
| project.json | `animal-emotion-explainer`, 템플릿, 로컬 렌더 설정, 사람 검토 상태 |
| source.json | TikTok 원본 URL, 제작자, 후보 스냅샷, 권리 상태, 내려받은 원본, 해시와 취득 방식 |
| viral-analysis.json | 검토된 원문, 종, 실제 행동, 복지·안전 메모, 한국어 설명 |
| commentary-plan.json | 실제 동작과 사람 상황 비유를 연결하는 편집 비트 |
| script.json | 영상에는 넣지 않는 한국어 시나리오와 화면 문구 오버라이드 |
| storyboard.json | 시간·원본 구간·화면 문구·행동 근거·동물 감정·음악 큐 |
| music-plan.json | 생성 무보컬 음악 또는 검증된 라이선스 음원의 선택·믹스·권리 기록 |
| rights-manifest.json | 사용 원본과 보조 자산의 출처·권리 정보 |
| publish.json | 제목·설명·출처·공개 고지 메타데이터만 보관하며 업로드 상태는 없음 |
| preview.json | 검토용 시간별 원본 프레임 |
| edit-plan.md | 장면별 원본 범위, 자막, 감정 근거, 음악 큐 |
| delivery-note.md | 원본 TikTok 링크, 별도 시나리오, 감정 해석, 음악 프로필 |
| outputs/short.mp4 | 완성 로컬 720x1280 H.264/AAC MP4 |
| render-report.json | 장면·적용 편집·생성 음악·출력 기술 정보 |
| youtube-upload.json | 제목·설명·태그·썸네일 제안과 검토가 필요한 업로드 설정 |
| youtube-upload.md | 최종 응답에 그대로 제공할 YouTube 업로드 정보 |

## `storyboard.json` 장면 필수 구조

최종 장면마다 실제 원본 구간 또는 출처가 기록된 `visual_path`, 짧은 한국어 `headline`/`korean_caption`, `script_segment_id`, `source_evidence`, `edit_actions`, `animal_emotion`이 필요합니다.

```json
{
  "id": "scene-03",
  "role": "evidence",
  "duration": 4.5,
  "source_clip_id": "source-video-01",
  "source_start_seconds": 12.5,
  "source_clip_seconds": 2.5,
  "headline": "문 앞에서 보호자를 바라본다",
  "korean_caption": "꼬리를 낮춘 채 사람의 움직임을 계속 살핀다",
  "script_segment_id": "segment-03",
  "source_evidence": {
    "observed_action": "개가 꼬리를 낮춘 채 문 앞에서 보호자를 바라본다",
    "keywords": ["꼬리", "보호자"]
  },
  "animal_emotion": {
    "label": "낯선 상황을 경계하는 모습",
    "confidence": "inference",
    "evidence": ["꼬리를 낮춘 채 보호자를 바라봄"],
    "music_mood": "tension"
  },
  "edit_actions": ["crop_9_16", "reframe_subject", "source_audio_duck", "korean_caption_safe_area"]
}
```

`animal_emotion.confidence`는 `observed`, `caregiver_report`, `inference` 중 하나여야 합니다. `evidence`에는 `source_evidence.keywords` 중 하나 이상을 포함해 감정 표기가 실제 행동에 연결되도록 합니다. `music_mood`는 `gentle`, `tender`, `tension`, `relief`, `playful` 중 하나입니다.

`project.template.channel_label`은 검증된 원본 제작자 또는 사용자가 명시한 권한 있는 채널 정보여야 하며 모든 장면의 상단에 배지나 알약 모양 없이 같은 일반 텍스트로 표시됩니다. 장면별 `headline`과 `korean_caption`은 모두 하단에 표시합니다. 여러 동물을 의인화할 때는 `script.json`에 역할 관계를 정하고 결론까지 바꾸지 않습니다.

원본 영상에 외국어 내장 자막이 보이면 `project.template.source_caption_handling`을 기록합니다. 허용 모드는 `not_detected`, `preserve`, `preserve_and_localize_bottom`, `blur_and_localize_bottom`입니다. 기본 권장 모드는 검토한 원본 자막 영역만 블러하고 첫 하단 한국어 자막에 뜻을 통합하는 `blur_and_localize_bottom`입니다. 이 모드의 `bridges`는 `scene_id`, `source_text`, `korean_text`를 가지며, 연결된 장면의 `korean_caption`은 `korean_text`와 같아야 합니다. 반복되는 고정 원문은 첫 장면에만 연결하고, 바뀌는 원문은 해당 장면마다 연결합니다.

`blur_and_localize_bottom`은 영향받는 원본 영상 장면의 `edit_actions`에 `source_caption_blur`를 추가하고 `source_caption_blur_region`에 원본 프레임 기준 0~1 비율의 `x`, `y`, `width`, `height`와 4~40의 `radius`를 기록합니다. 렌더러는 그 사각 영역만 블러합니다. 고정 자막은 연속 장면에 같은 값을 사용하고 대표·경계 프레임에서 문자가 읽히지 않는지, 워터마크와 동물 얼굴이 보존되는지 확인합니다. `source_caption_safe_reframe`과 함께 사용하지 않습니다.

움직이는 원본을 연속 구간으로 이어 쓰면서 자막만 바꿀 때는 각 영상 장면의 `edit_actions`에 `no_scene_transition`을 넣습니다. 렌더러는 해당 장면의 시작·끝 페이드를 적용하지 않으며 별도 이미지 전환을 만들지 않습니다.

마지막 화면이 검게 비어 보이지 않게 하려면 최종 `conclusion` 원본 장면에만 `hold_last_frame`을 추가하고 `hold_last_frame_seconds`를 0.2~2초로 기록합니다. 원본 자체의 끝이 검다면 `hold_last_frame_source_offset_seconds`를 0~1초로 기록해 끝에서 그만큼 앞선 마지막 검토 프레임을 선택합니다. 해당 장면의 `duration`은 `source_clip_seconds - hold_last_frame_source_offset_seconds + hold_last_frame_seconds`와 같아야 합니다. 렌더러는 검은 카드나 별도 이미지를 만들지 않고 선택한 실제 원본 프레임을 복제해 고정합니다.

## 최종 로컬 렌더 준비 조건

1. `distribution_mode`는 `local_only`, `production_mode`는 `animal-emotion-explainer`, 템플릿은 `animal-emotion-story-v1`이다.
2. source의 TikTok URL, 제작자, 실제 권리 상태, 동물 후보 스냅샷이 있다. `not_permitted`는 거절한다.
   공식 공개 플레이어 폴백을 사용했다면 격리된 임시 프로필, 인증 없음, 공식 플레이어 URL, 다운로드 도구와 파일 해시가 기록되어야 하며 권리 상태를 상향하지 않는다.
3. 원문 검토, 시각 요약, 한국어 설명, 종, 두 개 이상의 관찰 행동, 복지·안전 메모가 있다.
4. 별도 한국어 시나리오가 3개 이상이며, 4개 이상 본문 장면이 15초 이상이고 CTA를 합친 최종본은 60초 이하이다. 마지막 원본 장면은 실제 결과를 보여 주는 `conclusion`이며, 종료 화면 고정을 사용한다면 실제 마지막 프레임만 0.2~2초 유지한다. 그 뒤 1.8초 무음 구독·좋아요 CTA 샷을 정확히 한 번 붙인다.
5. 각 장면에는 실제 행동 근거, 하단 화면 문구, 내부 감정 구분, 감정 근거, 음악 큐가 있다. 상단 채널 정보는 장면마다 바뀌지 않는다. 감정은 프로젝트 문서에서 확정 사실이 아닌 관찰·보호자 설명·행동 해석으로 기록하며 렌더 화면에는 분석 배지와 근거 줄을 표시하지 않는다.
   외국어 내장 자막이 확인되면 원문·언어·연결 장면·한국어 통합 문구·검토한 블러 영역이 기록되고, 연결 장면의 큰 하단 자막과 일치한다.
6. 원본 클립은 장면별 8초 이하, 합계 18초 이하이다.
7. `music-plan.json`은 무보컬 `synthetic_ambient` 또는 `licensed_track`이다. 생성 음악은 `owned`로 기록한다. 라이선스 음원은 로컬 파일, 곡명, 제작자, 공식 원본 URL, 라이선스명·URL, 필수 출처 문구, 시작 지점과 음량을 기록하고, `rights-manifest.json`에는 같은 파일의 `licensed` 또는 `permission_confirmed` 상태와 SHA-256을 남긴다. 유명하거나 무료로 내려받을 수 있다는 사실만으로 사용하지 않는다.
8. `edit-plan.md`, 원본 미디어, 출처 기록, 필요한 사람 검토가 있다.

`render`는 장면 영상의 원본 오디오를 낮게 유지하고, 그 위에 생성 무보컬 음악 또는 검증된 라이선스 무보컬 음원을 섞습니다. TTS·보컬·출처와 라이선스가 불완전한 음원은 허용하지 않습니다.

렌더는 `youtube-upload.json`과 `youtube-upload.md`도 생성합니다. 시청자층, 합성 콘텐츠, 프로모션, 연령 제한과 미확정 권리는 검토 대상으로 남기며 업로드는 수행하지 않습니다. 기술 검증은 로컬 MP4의 H.264/AAC, 720x1280, 영상·오디오 스트림, 길이만 확인합니다. 이것은 저작권 허가, 공정 이용, 플랫폼 승인, 수익화, 사실성, 동물 복지 전문 판단을 보장하지 않습니다.
