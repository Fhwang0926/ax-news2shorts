# 45도 에어컨 팩트체크 쇼츠 v2 재생성 완료

## 제작 결과

- 변경된 `news2shorts` 0.7.0 규칙으로 기존 28.75초 퀵리빌을 별도 프로젝트에서 다시 생성했다.
- 최종본은 28.83초, 720x1280, H.264/AAC, 하드 컷 구성이다.
- 이전 영상과 대본은 유지하고, 기존 생성 이미지 7장은 모두 제외했다.
- 실제 에어컨·실외기 사진 4장과 새 평면 근거 그래픽 3장을 장면별로 다르게 사용했다.
- 실제 사진은 Wikimedia Commons의 CC0 또는 퍼블릭 도메인 원본만 사용하고 권리, 원본 URL, 제작자, 해시, 기사 연관성을 기록했다.
- AI 이미지 생성은 사용하지 않았다. 수치 설명 장면은 Pillow 기반 자체 제작 그래픽으로 만들고 육안 품질 확인을 기록했다.
- 모든 장면 하단에 작은 뉴스 출처를 표시하고 `sources.json`의 근거 ID와 연결했다.
- 마지막 장면에 `결론` 배지와 `45℃는 고장선 아님 · 모델 한계와 열 배출 확인` 문구를 표시했다.
- 현재 Typecast 키가 감지되지 않아 API를 재호출하지 않고, 기존 승인된 동일 대본·Voice ID의 Typecast 내레이션을 장면별 WAV로 분리해 재사용했다.

## 산출물

- 프로젝트: `projects/2026-08-17-aircon-45c-factcheck-v2/`
- 최종본: `projects/2026-08-17-aircon-45c-factcheck-v2/short.mp4`
- 검토본: `projects/2026-08-17-aircon-45c-factcheck-v2/preview.mp4`
- 전체 장면 확인표: `projects/2026-08-17-aircon-45c-factcheck-v2/contact-sheet.png`
- 마지막 장면 확인: `projects/2026-08-17-aircon-45c-factcheck-v2/final-frame.png`
- 사진·권리 기록: `projects/2026-08-17-aircon-45c-factcheck-v2/rights-manifest.json`
- 오디오 출처 기록: `projects/2026-08-17-aircon-45c-factcheck-v2/audio/provenance.json`

## 확인 결과

- 초안 및 최종 검증 오류 0건
- 실제 뉴스 사진 필수 게이트 통과
- 모든 이미지 경로와 SHA-256이 서로 다름
- 생성형 AI 이미지 없음, 화면 합성 미디어 표시 불필요
- 사진 크롭, 그래픽 깨짐, 상단 헤드라인, 자막, 크레딧, 뉴스 출처, 결론 배지를 전체 장면과 마지막 프레임에서 육안 확인
- 최종 MP4: 28.832초, 720x1280, H.264/AAC, 오디오 포함
- 알려진 경고: 발행일이 명시되지 않은 국가 기준 문서와 한국에너지공단 가이드 2건은 `published_at`을 비워 두었다.

## 변경 파일

- `projects/2026-08-17-aircon-45c-factcheck-v2/project.json`: 새 플러그인 표시·권리 옵션과 승인 상태
- `projects/2026-08-17-aircon-45c-factcheck-v2/sources.json`: 팩트 출처 5건
- `projects/2026-08-17-aircon-45c-factcheck-v2/fact-sheet.json`: 검증 주장과 한계
- `projects/2026-08-17-aircon-45c-factcheck-v2/script.md`: 유지한 후크·내레이션과 새 시각물 검증 메모
- `projects/2026-08-17-aircon-45c-factcheck-v2/storyboard.json`: 장면별 고유 이미지, 줌, 결론, 출처, 오디오
- `projects/2026-08-17-aircon-45c-factcheck-v2/rights-manifest.json`: 검색, 사진 권리, 연관성, 그래픽 품질 기록
- `projects/2026-08-17-aircon-45c-factcheck-v2/publish.json`: 게시용 문구와 사진 라이선스 고지
- `projects/2026-08-17-aircon-45c-factcheck-v2/assets/`: 실제 사진 4장과 새 그래픽 3장
- `projects/2026-08-17-aircon-45c-factcheck-v2/audio/`: 재사용 Typecast 장면 오디오와 출처 기록
- `projects/2026-08-17-aircon-45c-factcheck-v2/preview.mp4`, `short.mp4`, `contact-sheet.png`, `final-frame.png`: 검토·최종 결과물

## 범위

- 기존 `projects/2026-08-16-aircon-45c-factcheck/` 프로젝트와 영상은 수정하지 않았다.
- KBS 원본 영상, 음원, 썸네일, 자막과 제조사 페이지 이미지는 사용하지 않았다.
- YouTube 업로드와 게시 작업은 수행하지 않았다.
