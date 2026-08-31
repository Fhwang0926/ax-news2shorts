# news2shorts version 17 중간 구독 CTA

## 완료 내용

- 새 프로젝트를 version 17로 올리고 `mid_cta.mode`에 `auto`, `enabled`, `disabled` 사용자 설정을 추가했다.
- `init --mid-cta-mode`로 생성 시점에 중간 CTA 자동 선택·강제 포함·제외를 기록할 수 있게 했다.
- 20초 이상 continuous-flow의 40~60% 구간에서 50%에 가장 가까운 `rehook` 또는 `turn` 장면 뒤에 CTA를 한 번 배치한다.
- 프로젝트가 선택한 Typecast 보이스와 `verdict` 전달로 1.5~2.0초의 짧은 구독 요청을 생성한다.
- 카드 문구는 중앙에 두고 화살표만 YouTube Shorts 하단 왼쪽 채널 영역의 정규화 좌표 `(0.34, 0.86)`으로 이동시킨다.
- 클릭되지 않는 가짜 구독 버튼과 별도 SRT를 만들지 않고, 검증되지 않은 조회수·시청자 수·구독률 표현을 차단한다.
- 민감 뉴스는 `잠깐만요 / 구독은 아직 / 채널명 옆 구독, 한 번만` 문구로 자동 완화한다.
- 중간 CTA가 렌더되면 마지막 구독 CTA를 0.8초 음성 없는 `뉴스한면 / 다음 소식도 바로` 브랜드 마감으로 교체한다.
- 편집 패키지에 `scenes/mid-cta.mp4`, `audio/mid-cta.wav`, `timeline.csv`의 `kind=mid-cta` 행을 추가했다.
- version 16 이하 프로젝트와 `mid_cta.mode=disabled` 프로젝트는 기존 CTA 동작을 유지한다.

## 변경 파일

- `plugins/news2shorts/scripts/news2shorts.py`
  - 설정·검증, 자동 위치 선택, Typecast·화살표·효과음 렌더, 타임라인 이동, 브랜드 마감, 편집 패키지와 렌더 보고서를 구현했다.
- `plugins/news2shorts/tests/test_retention_v16.py`
  - version 17 기본값, 사용자 제외, 중앙 재후킹 선택, 화살표 프레임, 브랜드 마감 호환성을 검사한다.
- `plugins/news2shorts/skills/news2shorts/templates/project.template.json`
  - version 17과 기본 `mid_cta` 계약을 추가했다.
- `plugins/news2shorts/skills/news2shorts/SKILL.md`
  - 사용자 설정, 적용 조건, 민감 뉴스 문구, YouTube UI 방향과 중복 CTA 방지 규칙을 추가했다.
- `plugins/news2shorts/skills/news2shorts/references/output-contract.md`
  - 프로젝트·렌더 보고서·편집 패키지 계약을 문서화했다.
- `plugins/news2shorts/README.md`
  - CLI 설정과 렌더 동작을 추가했다.
- `plugins/news2shorts/.codex-plugin/plugin.json`
  - 캐시버스터를 `0.36.5+codex.20260830043558`로 갱신했다.
- `projects/2026-08-30-2am-police-door-check/project.json`
  - version 17과 사용자 선택 `mid_cta.mode=enabled`를 적용했다.
- `projects/2026-08-30-2am-police-door-check/script.md`
  - scene-04 뒤 중간 CTA와 Typecast 사용 범위를 기록했다.

## 확인 결과

- Python 문법 검사 통과.
- news2shorts 단위 테스트 15개 통과.
- Skill·Plugin 구조 검증 통과.
- 현재 경찰 영상에서 scene-04 뒤 12.302초에 중간 CTA가 선택됐다.
- Typecast Seohyeon 음성 포함 실제 중간 CTA 길이는 1.792초다.
- 중간 CTA 이후 장면 시각만 이동하고 첫 답변·truth guard는 2.25초로 유지됐다.
- 중간 CTA SRT는 생성되지 않았고 편집 패키지 MP4·WAV·타임라인이 생성됐다.
- 마지막 CTA는 0.8초 `brand-close`로 전환됐다.
- 최종 검토본은 26.213초, 720x1280 H.264/AAC이며 SHA-256은 `2fb835269011c528c0f807c74ea1fd8c7bf26f31e1875462faf1df7d4716b05e`다.

## 남은 제한

- YouTube Shorts UI 좌표는 앱·기기·실험군에 따라 바뀔 수 있어 실제 게시 전 모바일 비공개 미리보기 확인이 필요하다.
- 제공 원영상 권리는 계속 `review_required`이며 게시 가능한 최종본을 의미하지 않는다.
