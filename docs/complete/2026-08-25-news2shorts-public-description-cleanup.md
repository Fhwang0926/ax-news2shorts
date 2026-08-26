# news2shorts 공개 설명 제작 문구 제거

## 완료 일자

- 2026-08-25

## 반영 범위

- YouTube 공개 설명에서 사진 제공처·라이선스·자료사진 여부와 Typecast·TTS·합성음성 같은 제작 내부 문구를 금지했다.
- 이전 프로젝트의 `publish.json`에 해당 문구가 남아 있어도 `upload-package` 출력에서는 문장 단위로 자동 제외한다.
- version 4 검증에서는 저장된 공개 설명에 해당 문구가 있으면 검토본은 경고, 최종본은 오류로 처리한다.
- 이미지 권리와 TTS 정보는 삭제하지 않고 `rights-manifest.json`, `render-report.json`, `contains_synthetic_media`, `altered_content`에 유지한다.
- 직전 서울 월세 프로젝트의 공개 설명에서도 해당 문구를 제거했다.
- 플러그인 버전을 `0.36.2+codex.20260825220500`으로 갱신했다.

## 변경 파일

- `plugins/news2shorts/scripts/news2shorts.py`: 공개 설명 제작 문구 탐지·검증·출력 필터.
- `plugins/news2shorts/skills/news2shorts/SKILL.md`: 공개 설명과 내부 권리·합성 기록의 경계.
- `plugins/news2shorts/skills/news2shorts/references/upload-package.md`: 업로드 설명 금지 문구와 출력 규칙.
- `plugins/news2shorts/skills/news2shorts/references/output-contract.md`: `publish.json` 공개 설명 계약.
- `plugins/news2shorts/README.md`: 사용자용 공개 설명 동작.
- `plugins/news2shorts/.codex-plugin/plugin.json`: 플러그인 버전.
- `projects/2026-08-25-seoul-rent-300/publish.json`: 기존 공개 설명 정리.

## 검증 결과

- Python AST와 플러그인·프로젝트 JSON 파싱을 통과했다.
- Skill Creator 빠른 구조 검사를 통과했다.
- 사실 문장과 제작 내부 문구가 섞인 합성 입력에서 사실과 태그만 남고 Pexels·자료사진·Typecast 문장이 제거되는 것을 확인했다.
- 서울 월세 프로젝트 검증은 오류 0건으로 통과했고 업로드 설명은 357자에서 288자로 정리됐다.
- 설치본 `upload-package` 출력에 사진 제공처·라이선스·자료사진·Typecast·합성음성 문구가 없는 것을 확인했다.
- `news2shorts@news2shorts-local` `0.36.2+codex.20260825220500` installed·enabled 상태를 확인했다.
- 작업본과 설치 캐시의 스크립트·Skill SHA-256이 각각 일치했다.

## 수행하지 않은 작업

- 영상 재렌더와 YouTube 업로드는 수행하지 않는다.
- 프론트엔드 빌드와 DB 작업은 수행하지 않는다.
