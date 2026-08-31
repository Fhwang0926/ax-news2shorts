# 새벽 2시 경찰 방문 영상 전사 검토 재렌더

## 완료 내용

- 사용자 제공 39.124초 원본을 프로젝트 자산으로 보존하고 로컬 OpenAI Whisper `small` 모델로 전체 음성을 전사했다.
- 전체 전사 시간표를 기준으로 `audio_mode: "source-video"` 장면 네 개의 대사 시작·종료점을 다시 지정했다.
- 첫 장면을 원본 `7.80~10.05초`로 조정해 `저기요`와 `저 경찰이에요, 경찰`을 함께 포함하고, 다음 개인 이름 자막이 시작되는 프레임은 제외했다.
- 문 열기 요청 장면은 내부 공백이 없는 원본 `31.38~33.65초` 발화만 사용했다.
- 원본에서 특히 작은 장면 1·4 음성만 22dB 높인 프로젝트용 파생 영상을 만들고, 다른 원본 대화와 Typecast 음량은 유지했다.
- 장면 2·6과 CTA만 Typecast Seohyeon을 사용하고 원본 영상 장면에는 뉴스 자막을 추가하지 않았다.
- `source-audio-review.json`은 네 장면 모두 `passed`이며 편집 패키지 metadata에도 포함됐다.
- 최종 검토본 `preview.mp4`, 별도 `thumbnail.jpg`, CapCut/Vrew 편집 패키지와 업로드 정보를 다시 생성했다.

## 변경 파일과 자산

- `projects/2026-08-30-2am-police-door-check/storyboard.json`
  - 원본 기준 대사 구간, 실제 대사, 장면 길이와 음량 보정 파생 자산을 반영했다.
- `projects/2026-08-30-2am-police-door-check/script.md`
  - 원본 음성 대사를 실제 사용 구간과 일치시켰다.
- `projects/2026-08-30-2am-police-door-check/rights-manifest.json`
  - 원본 전체 영상과 두 음량 보정 파생 영상의 출처, SHA-256, 시작점, 보정량을 기록했다.
- `projects/2026-08-30-2am-police-door-check/source-transcript.json`
  - 원본 전체 로컬 전사에서 공개 장면 네 개만 상대 시간으로 추출했다.
- `projects/2026-08-30-2am-police-door-check/source-audio-review.json`
  - 장면별 예상 대사, 전사 대사, 파일 해시와 컷 여백 검사를 기록했다.
- `projects/2026-08-30-2am-police-door-check/assets/collected/threads-source-full.mp4`
  - 사용자 제공 원본 전체 영상의 프로젝트 보존본이다.
- `projects/2026-08-30-2am-police-door-check/assets/collected/scene-01-threads-dialogue-boosted.mp4`
  - 개인 이름 구간을 제외한 첫 대사 구간이며 원본 음성을 22dB 보정했다.
- `projects/2026-08-30-2am-police-door-check/assets/collected/scene-04-threads-open-request-boosted.mp4`
  - 문 열기 요청 발화만 사용하고 원본 음성을 22dB 보정했다.
- `projects/2026-08-30-2am-police-door-check/preview.mp4`
  - 25.704초, 720x1280, H.264/AAC 검토본이다.

## 확인 결과

- `source-audio-review.json`: 장면 1·3·4·5 모두 `passed`.
- 장면 1 컷 여백: 앞 0.22초, 뒤 0.15초.
- 장면 3 컷 여백: 앞 0.17초, 뒤 0.21초.
- 장면 4 컷 여백: 앞 0.18초, 뒤 0.17초.
- 장면 5 컷 여백: 앞 0.17초, 뒤 0.19초.
- 완성 영상과 장면 1 MP4의 영상·음성 시작점은 모두 `0.000000`이다.
- 장면 1 음량은 평균 -49.9dB에서 -27.5dB, 장면 4는 -47.6dB에서 -25.1dB로 보정됐다.
- 원본 영상 장면은 `external_caption: false`, `render_text_overlay: false`이며 외부 SRT에는 Typecast 장면 2·6과 CTA만 있다.
- 첫 장면 프레임에 저장 경로나 개인 이름이 보이지 않고 `저기요`, `경찰이에요 경찰` 원본 자막과 Threads 출처가 표시된다.
- 0.5초 이상 검은 구간 하나는 원본의 어두운 현관 장면이며 전환 프레임이 아니다.
- 검토본 SHA-256: `ef4e98c89920eeade73c4df49e687cbfc0a7f3df5f1e33127226f035ae12afa8`.

## 남은 제한

- 제공 영상의 게시 권리 증빙이 없어 결과는 로컬 검토 전용이며 `short.mp4` 최종본은 만들지 않았다.
- 자동 전사의 고유명사 인식은 사실 근거로 사용하지 않았으며, 방문자의 실제 신분은 영상만으로 확정하지 않았다.
