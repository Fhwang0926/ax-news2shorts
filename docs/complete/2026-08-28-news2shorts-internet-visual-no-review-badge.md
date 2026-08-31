# news2shorts 인터넷 이미지·Whiteboard 배지 옵션 개선 완료

## 완료 내용

- `news2shorts collect-internet-visual` 명령을 추가했다.
- 사용자가 게시 전에 권리를 확인하거나 별도 확보할 인터넷 이미지를 공개 HTTPS 직접 URL에서 로컬 PNG로 수집할 수 있다.
- 수집 시 다음 정보를 프로젝트에 보존한다.
  - canonical 원본·기사 페이지
  - 최종 다운로드 URL
  - 제작자·매체·표시 문구
  - 검색어와 장면 ID
  - 파일 SHA-256
  - 기사 연관성·Whiteboard 문자 영역 검토
  - 현재 permission status와 게시 전 사용자 확인 예정 상태
- 이미지 URL과 redirect는 공개 HTTPS 호스트만 허용하고 private·loopback·link-local·reserved 주소를 거부한다.
- 이미지 응답만 허용하고 25 MiB·5천만 픽셀 상한을 적용한다.
- 로그인·쿠키·캡차·유료벽·DRM·워터마크 제거는 지원하지 않는다.
- `owned`, `licensed`, `permission_confirmed`와 증빙이 없으면 기본적으로 `unreviewed`, `approved: false`, `local_review_only: true`로 등록한다.
- Whiteboard draft 화면의 검토 배지를 숨기는 옵션을 추가했다.
  - `whiteboard-shorts render --hide-review-label`
  - `news2shorts_source.publish_blocked: true` 프로젝트의 draft에서만 허용한다.
  - 일반 Whiteboard 프로젝트는 기존 검토 표시를 유지한다.
  - 표시를 숨겨도 `publish_blocked`, `local_review_only`, 권리 대기 상태, 원본 URL과 render-report 기록은 유지한다.
- `news2shorts render --visual-mode whiteboard --draft --confirm-whiteboard-review`는 자동으로 배지 없는 draft를 요청한다.

## 사용 흐름

```text
news2shorts collect-internet-visual
  -> 기사 연관성·문자 영역 확인
  -> news2shorts prepare-whiteboard
  -> 장면 이미지·annotation 사용자 확인
  -> news2shorts render --visual-mode whiteboard --draft --confirm-whiteboard-review
  -> 사용자가 게시 전에 이미지 권리 확인·확보
```

## 변경 파일

- `plugins/news2shorts/scripts/news2shorts.py`
  - 안전한 공개 HTTPS 이미지 수집·등록 명령 추가
  - Whiteboard 프로젝트에 화면 배지 없음·게시 차단·사용자 권리 확인 예정 기록 추가
- `plugins/news2shorts/skills/news2shorts/SKILL.md`
  - 인터넷 이미지 수집과 배지 없는 검토 흐름 추가
- `plugins/news2shorts/skills/news2shorts/references/rights-policy.md`
  - 인터넷 수집 보안·출처·권리 대기 규칙 추가
- `plugins/news2shorts/skills/news2shorts/references/output-contract.md`
  - 배지 없는 draft와 게시 차단 메타데이터 계약 추가
- `plugins/news2shorts/README.md`
  - 명령 예시 추가
- `plugins/whiteboard-shorts/scripts/whiteboard_shorts.py`
  - 제한된 `--hide-review-label` 옵션과 render-report 증거 필드 추가
- `plugins/whiteboard-shorts/skills/whiteboard-shorts/SKILL.md`
  - news2shorts compatibility 조건 추가
- `plugins/whiteboard-shorts/skills/whiteboard-shorts/references/rights-policy.md`
  - 배지 제거와 권리 메타데이터 분리 규칙 추가
- `plugins/whiteboard-shorts/skills/whiteboard-shorts/references/output-contract.md`
  - news2shorts draft 예외 계약 추가
- `plugins/whiteboard-shorts/README.md`
  - 배지 없는 draft 명령 추가

## 설치 및 검증

- `news2shorts@news2shorts-local`: `0.36.5+codex.20260828060224`
- `whiteboard-shorts@news2shorts-local`: `0.6.1+codex.20260828060224`
- 두 Plugin validator: 통과
- 두 Skill validator: 통과
- `collect-internet-visual`, news render, Whiteboard render 도움말 로딩: 통과
- 변경 파일 공백 검사: 통과

자동화 테스트, 프론트엔드 빌드, 실제 인터넷 이미지 다운로드, 영상 렌더, DB 작업과 업로드는 수행하지 않았다.

## 게시 경계

- 화면에 검토 배지가 없다는 사실은 게시 가능 여부를 의미하지 않는다.
- 인터넷 이미지의 권리를 사용자가 게시 전에 확인·확보해야 한다.
- 권리 대기 이미지는 clean final 자격과 승인된 실사 비율에 포함되지 않는다.
- `not_permitted` 자산은 검토본에도 사용할 수 없다.
