# news2shorts 행정 식별번호 억제·합성 이미지 배지 제거 완료

## 완료 내용

- `의안 2217144`, 사건번호, 문서번호처럼 시청자가 들을 필요가 없는 긴 행정 식별번호를 화면 문구와 음성에서 자연어로 바꾸도록 했다.
  - 예: `의안 2217144가 통과돼야 합니다` → `해당 의안이 통과돼야 합니다`
  - 날짜, 온도, 제품 수처럼 뉴스 의미에 필요한 일반 숫자는 유지한다.
- 렌더 시 프로젝트 제목·후크·자막·결론·내레이션·크레딧·게시 문구를 정리하고, Typecast 본문과 Smart Emotion 앞뒤 문맥에도 동일한 처리를 적용한다.
- 정확한 식별번호는 검증에 필요하므로 `sources.json`, `fact-sheet.json`, `rights-manifest.json`과 원문 URL에는 유지한다.
- 모든 렌더 템플릿에서 화면의 `AI 재현 이미지` 배지를 제거했다.
- 합성 여부는 `project.json`, `rights-manifest.json`, `publish.json`, `render-report.json`에 계속 기록한다.
- 화면 배지가 없으므로 실제 사건 사진으로 오인될 수 있는 현실적 재현은 제외하고 설명형 픽토그램·도표를 우선하도록 제작 규칙을 보강했다.

## 현재 로봇청소기 프로젝트 반영

- 장면 자막·내레이션·결론·대본·게시 설명에서 의안번호를 `해당 개정안`으로 교체했다.
- 개정안 상태 설명 그래픽 안의 `의안 2217144` 문구도 `개정안 심사 현황`으로 바꾸고 720x1280 PNG를 다시 만들었다.
- 숫자 식별번호와 합성 이미지 배지가 없는 새 영상 `short-v3.mp4`를 생성했다.
- 원래 `short.mp4`와 `preview.mp4`는 덮어쓰지 않았다.

## 변경 파일

- `plugins/news2shorts/scripts/news2shorts.py`: 식별번호 자연어 치환, 화면·로컬 TTS·Typecast TTS 적용, 합성 이미지 배지 제거, 렌더 보고서 기록
- `plugins/news2shorts/skills/news2shorts/SKILL.md`: 번호 사용 범위와 배지 없는 합성 이미지 운용 규칙
- `plugins/news2shorts/skills/news2shorts/references/shorts-playbook.md`: 대사·화면 문구의 행정 식별번호 제외 규칙
- `plugins/news2shorts/skills/news2shorts/references/rights-policy.md`: 배지 대신 메타데이터를 유지하는 합성 이미지 정책
- `plugins/news2shorts/skills/news2shorts/references/visual-style.md`: 화면 배지 제거와 설명형 생성 이미지 기준
- `plugins/news2shorts/skills/news2shorts/references/output-contract.md`: 렌더 보고서의 억제 결과·배지 상태 계약
- `plugins/news2shorts/README.md`: 사용자 동작과 제한 사항 설명
- `plugins/news2shorts/.codex-plugin/plugin.json`: 버전 `0.9.2+codex.20260817`
- `projects/2026-08-16-robot-vacuum-security-bill/`: 스토리보드, 대본, 게시 문구, 설명 그래픽, 새 영상 반영

## 검증

- 숫자 치환 단위 검사 통과: 의안번호·사건번호는 치환되고 온도·제품 수는 유지됨
- Typecast 요청 본문과 Smart Emotion 앞뒤 문맥 치환 검사 통과
- 공백·문장부호·마지막 줄바꿈 보존 검사 통과
- 현재 프로젝트 공개 문구의 행정 식별번호 검사 통과
- 합성 장면 프레임에서 `AI 재현 이미지` 배지가 사라진 것을 육안 확인
- 전환 장면과 결론 장면에서 의안번호가 보이지 않는 것을 육안 확인
- `short-v3.mp4`: 720x1280, H.264/AAC, 27.391초
- 서현 보이스 자동 선택과 Typecast 음성 생성 성공
- Skill 구조 검사와 최종 프로젝트 검증 통과: 오류 0건, 경고 0건
- 설치본과 작업본의 CLI·Skill SHA-256 일치 확인
- `news2shorts@news2shorts-local` 설치본을 `0.9.2+codex.20260817`로 갱신 완료

## 미실행 범위

- 프론트엔드 빌드와 DB 작업은 수행하지 않았다.
- 영상 업로드·게시 작업은 수행하지 않았다.
