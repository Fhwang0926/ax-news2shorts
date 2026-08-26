# Issue2Shorts 제거 완료

## 완료 내용

- `issue2shorts@news2shorts-local` 설치를 해제했다.
- 플러그인 소스, 마켓플레이스 등록, 루트 README 안내를 제거했다.
- 전용 후보 프로젝트와 산출물, 법사위 호칭 쇼츠 결과물을 제거했다.
- 기존 플러그인 초안 및 제작 완료 문서를 제거했다.

## 제거 대상

- `plugins/issue2shorts/`
- `projects/issue2shorts/`
- `outputs/issue2shorts/`
- `outputs/2026-08-22/법사위-씨-호칭-논쟁/`
- `docs/complete/2026-08-21-issue2shorts-plugin-draft.md`
- `docs/complete/2026-08-22-issue2shorts-assembly-honorific-video.md`
- `.agents/plugins/marketplace.json`의 플러그인 등록
- `README.md`의 플러그인 안내

## 확인 결과

- 마켓플레이스 JSON 파싱 성공
- 설치 캐시 제거 확인
- 작업 완료 기록을 제외한 전용 경로와 문자열 참조 없음
- 프론트엔드 빌드는 대상이 아니므로 수행하지 않음
