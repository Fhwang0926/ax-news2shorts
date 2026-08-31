# cc-helper 커뮤니티 캡처·CapCut 복제본 재사용 개선 완료

## 요청

- 커뮤니티에서 캡처한 사진이 CapCut 템플릿 크롭으로 깨지지 않게 처리
- 한 번 복제한 CapCut 초안이 있으면 같은 초안을 계속 사용하고 `v2`, `v3` 폴더를 추가 생성하지 않음

## 반영 내용

### 커뮤니티 캡처

- 클리앙 등 알려진 커뮤니티 URL을 자동 감지한다.
- 자동 감지되지 않는 커뮤니티나 로컬 캡처는 `collect-assets --community-capture`로 지정한다.
- `community-capture-safe` 정규화는 1080×1920 화면 중앙의 최대 1000×1056 영역 안에 원본 전체를 비율 유지로 배치한다.
- 세로 캡처에 `portrait_fill`을 적용하지 않아 상·하단이 잘리지 않는다.
- 기존 에셋을 안전 모드로 다시 수집하면 정규화 PNG만 재생성하고 품질·가독성 승인을 다시 요구한다.
- 알려진 커뮤니티 이미지가 일반 크롭 방식으로 남아 있으면 에셋 검증을 실패시켜 재수집을 강제한다.

### CapCut 복제본 재사용

- 최초 복제 성공 시 폴더명을 `project.json.capcut.active_destination_name`에 고정한다.
- 이후 `prepare-capcut --dry-run`은 새 버전 이름을 받아도 기존 폴더를 선택하고 `reuse_existing: true`를 반환한다.
- 재사용 상태의 `clone-capcut --confirm`은 파일을 쓰지 않고 기존 경로와 `retime-capcut --confirm-existing`을 안내한다.
- 이미지·자막·타이밍 변경은 기존 자동 백업을 생성하는 `retime-capcut`로만 반영한다.

## 변경 파일

- `plugins/cc-helper/scripts/cc_helper.py`
- `plugins/cc-helper/skills/cc-helper/SKILL.md`
- `plugins/cc-helper/skills/cc-helper/references/workflow.md`
- `plugins/cc-helper/skills/cc-helper/references/project-contract.md`
- `plugins/cc-helper/.codex-plugin/plugin.json`

## 검증·설치

- Python 문법 검사 통과
- cc-helper 스킬 정적 검증 통과
- 플러그인 매니페스트 검증 통과
- 사용자 지침에 따라 테스트·빌드는 실행하지 않음
- 설치 버전: `0.1.2+codex.20260831055535`
- 설치 경로: `/Users/hdh/.codex/plugins/cache/news2shorts-local/cc-helper/0.1.2+codex.20260831055535`
- 소스·설치본 `cc_helper.py` SHA-256 일치: `d27c858e4b127cd38cd8dc779a8a67b853803c4d3e6bab8b01b07f2fa58ccf35`
