# news2shorts 배지 없는 결론·인물 줌·강한 질문 어조 개선 완료

## 완료 내용

- 편집형 결론 카드 위의 노란 장식선과 `결론` 배지를 제거했다.
- 카드가 검증된 결론 문장부터 바로 시작하도록 여백과 문장 간격을 다시 배치했다.
- 반응 문장을 짧게 정리하고 마지막 질문을 더 큰 노란 글자로 분리해 시각적 어색함을 줄였다.
- 사용자가 강한 마무리를 요청하면 사실 결론 뒤에 `아니, 주제로… 이게 맞나?`처럼 짧게 따져 묻는 내레이션을 사용하도록 Skill을 보강했다.
- Typecast에 지원 여부가 확인되지 않은 임의 감정 파라미터는 추가하지 않고, 실제 내레이션의 구어체·쉼표·말줄임표·질문형 문장으로 Smart Emotion 억양을 유도한다.
- 정지 이미지 장면에 `zoom_scale`을 추가했다. 허용 범위는 `1.0`-`1.25`, 일반 기본값은 `1.055`, 얼굴 중심 인물 사진 권장값은 `1.10`-`1.16`이다.
- 기존 정지 이미지 반복 방식에서 줌 상태가 거의 누적되지 않던 수식을 입력 프레임 기준 누적 방식으로 수정했다.
- 기존 프로젝트에 `zoom_scale`이 없으면 기본값을 사용해 호환성을 유지한다.

## 현재 버스하우스 프로젝트 반영

- 인물 자료사진 장면을 얼굴 중심 `zoom-in`, `focus_y: 0.34`, `zoom_scale: 1.14`로 변경했다.
- 결론 카드를 다음 구성으로 정리했다.
  - 결론: `비판 뒤 철회된 개인 제안입니다`
  - 반응: `비판이 이어지자 게시물을 삭제하고 사과했습니다`
  - 질문: `청년 주거 대책으로, 이게 맞나?`
- 마지막 음성은 `결론은 확정 정책이 아니라 비판 뒤 철회된 개인 제안입니다. 아니, 청년 주거 대책으로… 이게 맞나?`로 적용했다.
- Typecast 서현 보이스로 최신 검토본 `preview-v4.mp4`를 생성했다.

## 변경 파일

- `plugins/news2shorts/scripts/news2shorts.py`: 배지 없는 카드 재배치, 질문 강조, `zoom_scale` 검증·렌더·보고, 누적 줌 수식 수정
- `plugins/news2shorts/skills/news2shorts/SKILL.md`: 인물 줌 강도와 강한 질문 어조 규칙
- `plugins/news2shorts/skills/news2shorts/references/output-contract.md`: `zoom_scale`과 렌더 보고서 계약
- `plugins/news2shorts/skills/news2shorts/references/shorts-playbook.md`: 얼굴 중심 줌과 사용자 요청 시 따져 묻는 마무리 규칙
- `plugins/news2shorts/skills/news2shorts/references/visual-style.md`: 배지·상단 장식 제거, 카드 계층, 인물 줌 기준
- `plugins/news2shorts/skills/news2shorts/templates/storyboard.template.json`: `zoom_scale` 기본값
- `plugins/news2shorts/README.md`: 새 결론 카드·인물 줌·Smart Emotion 사용 설명
- `plugins/news2shorts/.codex-plugin/plugin.json`: 버전 `0.11.0+codex.20260817`
- `projects/2026-08-17-hwang-hee-bus-house-quick-reveal/storyboard.json`: 카드 문구, 질문 어조, 인물 줌 설정
- `projects/2026-08-17-hwang-hee-bus-house-quick-reveal/script.md`: 강한 질문 내레이션과 사실 보호 메모
- `projects/2026-08-17-hwang-hee-bus-house-quick-reveal/project.json`: 최신 검토본 상태
- `projects/2026-08-17-hwang-hee-bus-house-quick-reveal/render-report.json`: 음성·영상·줌 렌더 결과
- `projects/2026-08-17-hwang-hee-bus-house-quick-reveal/preview-v4.mp4`: 최신 검토 영상

## 검증

- CLI 도움말, 프로젝트 일반 검증, JSON 파싱, Skill Creator `quick_validate.py` 통과
- 프로젝트 검증: 오류 0건, 경고 0건
- 결론 카드 실제 프레임에서 배지·상단 장식이 없고 제목·반응·질문·출처가 겹치거나 잘리지 않음을 육안 확인
- 인물 장면 시작·끝 프레임에서 얼굴 중심 확대가 분명하고 안전하게 유지됨을 육안 확인
- 인물 장면 시작·끝 프레임 SSIM `0.614415`로 실제 화면 변화 확인
- `preview-v4.mp4`: 720x1280, H.264/AAC, 24.106초, Typecast 서현, 렌더 경고 0건
- 설치본 `news2shorts@news2shorts-local` 버전 `0.11.0+codex.20260817`, installed/enabled 확인
- 원본과 설치 캐시의 CLI·Skill SHA-256 일치 확인

## 미실행 범위

- 정치 소재의 사용자 편집 승인 전이므로 최종 `short.mp4`는 생성하지 않았다.
- 업로드·게시, 프론트엔드 빌드, DB 작업은 수행하지 않았다.
