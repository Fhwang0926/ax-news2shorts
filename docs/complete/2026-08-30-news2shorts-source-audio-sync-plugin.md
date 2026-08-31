# news2shorts 원본 영상 음성 동기화 기능 완료

## 원인

- 기존 `continuous-flow` 렌더는 모든 영상 장면의 원음을 버리고 한 개의 연속 Typecast 트랙을 다시 입혔다.
- 원본 대화를 복원하려면 렌더 후 별도 오디오 믹스가 필요했고, 이 경로에서는 영상과 음성 시작점을 프로젝트 밖에서 따로 관리하게 됐다.

## 구현

- `storyboard.json` 장면에 `audio_mode: "source-video"`를 지원한다.
- 원본 음성 장면은 영상과 음성을 동일한 `video_start`와 `duration`으로 자른다.
- `render_text_overlay: false`이면 원본 영상 위에 뉴스 제목·하단 자막을 그리지 않고 작은 출처만 유지한다.
- `external_caption: false`이면 편집 패키지 SRT에서 해당 장면을 제외해 원본 내장 자막과 중복되지 않는다.
- `continuous-flow`에서 원본 음성 장면이 하나라도 있으면 `scene-aligned-hybrid` 경로를 사용한다.
- 원본 음성 장면은 `source-video`, 나머지 설명 장면은 Typecast 또는 기존 장면 음성 계약을 사용한다.
- 기존 원음 없는 continuous-flow와 visual-first 렌더 경로는 변경하지 않았다.

## 변경 파일

- `plugins/news2shorts/scripts/news2shorts.py`
- `plugins/news2shorts/skills/news2shorts/SKILL.md`
- `plugins/news2shorts/skills/news2shorts/references/output-contract.md`
- `plugins/news2shorts/.codex-plugin/plugin.json`

## 실제 프로젝트 검증

- 대상: `projects/2026-08-30-2am-police-door-check`
- 장면 1·3·4·5: `audio_source: source-video`
- 장면 2·6: Typecast `Seohyeon`
- 장면 1 영상·음성 시작점: 각각 `0.000초`
- 첫 사실 제한 장면 시작: `2.500초`
- 결과 영상: 720×1280, H.264/AAC, 29.047초
- 외부 SRT: Typecast 장면과 CTA만 3개 큐
- 0.8초 이상 무음 구간 미검출
- 원본 영상 장면에서 추가 뉴스 자막 미표시 확인
- 0.57초 암부는 원본 현관 화면이며 장면 전환 오류가 아님

## 정적 검증

- Python 문법 검사 통과
- 플러그인 validator 통과
- skill validator 통과
- `git diff --check` 통과
- 프로젝트 validator 오류 0건
- 사용자 지침에 따라 별도 테스트 스위트와 프론트엔드 빌드는 실행하지 않았다.

## 설치

- 마켓플레이스: `news2shorts-local`
- 설치 버전: `0.36.5+codex.20260830021359`
- 소스·설치 캐시의 renderer, SKILL, output-contract SHA-256 일치 확인

## 남은 제한

- 제공 Threads 영상의 재사용 권리와 권리 승인 실사진 요건은 해결되지 않았다.
- 결과물은 `preview.mp4` 로컬 검토본이며 게시용 `short.mp4`가 아니다.
