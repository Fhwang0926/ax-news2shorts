# news2shorts 합성 썸네일·제목 해시태그 반영

## 완료 일자

- 2026-08-22

## 반영 범위

- 모든 새 영상 프로젝트의 기본 썸네일 방식을 `file_upload`로 변경했다.
- 권리 승인이 완료된 서로 다른 장면 이미지 2~3장을 사용해 720x1280 `thumbnail.jpg`를 자동 합성한다.
- 썸네일은 검정·노랑·빨강·흰색의 강한 대비, 큰 훅과 보조 훅을 사용하되 확인되지 않은 비난·긴급성·여론은 만들지 않는다.
- 별도 `thumbnail` 명령으로 영상 재렌더 없이 썸네일만 다시 만들 수 있다.
- 렌더 보고서에 썸네일 파일, 크기, 문구, 원본 자산, 합성 구성을 기록한다.
- YouTube 업로드 정보의 제목 뒤에 `publish.tags` 앞쪽 값 중 최대 2개를 해시태그로 자동 추가한다.
- 중복 태그와 허용되지 않은 문자를 제거하고, 합친 제목이 100자를 넘는 태그는 건너뛴다.

## 변경 파일

- `plugins/news2shorts/scripts/news2shorts.py`
  - 썸네일 합성, 권리 승인 이미지 선택, 제목 해시태그 정규화·길이 제한, 업로드 패키지 출력과 관련 검증을 추가했다.
- `plugins/news2shorts/skills/news2shorts/SKILL.md`
  - 영상 제작 시 실제 합성 썸네일과 해시태그가 붙은 제목을 필수 결과물로 반환하도록 제작 절차를 갱신했다.
- `plugins/news2shorts/skills/news2shorts/references/upload-package.md`
  - 제목 해시태그와 실제 썸네일 파일의 업로드 안내 규칙을 문서화했다.
- `plugins/news2shorts/skills/news2shorts/references/output-contract.md`
  - `thumbnail.jpg`, `publish.json` 썸네일 필드, 렌더 보고서 썸네일 기록을 출력 계약에 추가했다.
- `plugins/news2shorts/skills/news2shorts/references/visual-style.md`
  - 고대비 합성 썸네일의 구성과 사실·권리 경계를 추가했다.
- `plugins/news2shorts/README.md`, `README.md`
  - 사용자용 기능과 별도 썸네일 생성 명령을 설명했다.
- `plugins/news2shorts/.codex-plugin/plugin.json`
  - 플러그인 버전을 `0.22.0+codex.20260822`로 올렸다.

## 설계 판단

- 새 썸네일 시스템이나 외부 패키지를 추가하지 않고 기존 Pillow, 스토리보드, 권리 매니페스트, 한글 폰트 함수를 재사용했다.
- 이미지 검색 결과를 임의로 합성하지 않고 이미 장면 사용 승인을 받은 서로 다른 파일만 허용했다.
- `publish.title`은 편집용 기본 제목으로 유지하고 최종 업로드 출력에서 태그를 보완해 기존 프로젝트와의 호환성을 유지했다.

## 검증 결과

- Python AST와 플러그인 매니페스트 JSON 파싱 성공
- Skill 구조 검사 성공
- 제목 태그 2개 추가, 중복 제거, 100자 한도 경계 검사 성공
- 기존 720x1280 프로젝트 복사본에서 권리 승인 이미지 3장 합성 썸네일 생성 성공
- 생성 결과를 육안 확인해 문구 잘림, 패널 겹침, 화면 밖 배치를 발견하지 못함
- 샘플 업로드 패키지에서 태그가 붙은 제목의 정확한 글자 수와 `thumbnail.jpg` 파일 안내 확인
- 샘플 프로젝트 정적 검증 성공
- `git diff --check` 성공
- 로컬 플러그인 `news2shorts@news2shorts-local` 0.22.0 설치·활성화 확인
- 설치 캐시의 렌더러와 Skill SHA-256이 소스와 일치함을 확인

## 수행하지 않은 작업

- 새 뉴스 영상과 MP4는 제작하지 않았다.
- YouTube 업로드·게시와 Typecast 유료 호출은 수행하지 않았다.
- DB 작업과 프론트엔드 빌드는 대상이 아니므로 수행하지 않았다.
