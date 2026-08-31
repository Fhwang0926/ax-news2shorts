# News2Shorts 뉴스 이미지 우선 무음 검토본 재렌더

## 완료 내용

- 길막 주차 프로젝트의 핵심 장면 3개를 일반 스톡 대신 실제 뉴스 기사 이미지로 교체했다.
- SBS 상가 주차장 출입구 차단 사건, 뉴스제주 공영주차장 출입구 차단 사건, 머니투데이 아파트 출구 차단 사건 이미지를 사용했다.
- 세 이미지의 원문 URL, 게시사, 최종 다운로드 URL, SHA-256, 검색어와 장면 연관성을 `rights-manifest.json`에 기록했다.
- 번호판은 원본에서 가림 처리된 상태를 확인했고 사용자명·댓글·아바타·개인 주소·불필요한 인물은 포함하지 않았다.
- 세 이미지는 사용 권리 검토 전이므로 `unreviewed`, `review_required`, `approved: false`, `local_review_only: true`로 유지했다.
- 화면에는 매체명만 표시하고 `게시 전 권리 확인 필요` 같은 검토 문구는 제거했다. 권리 대기 상태는 JSON 메타데이터에만 유지했다.
- `--no-tts`로 Typecast 호출 없이 검토 영상을 다시 만들었다. 뉴스 본문은 무음이며 공통 인트로의 원본 오디오와 CTA의 낮은 자체 큐만 유지된다.
- 무음 continuous-flow가 내레이션 글자 수로 장면 길이를 재분배하던 문제를 수정해 스토리보드 요청 길이를 그대로 사용하도록 개선했다.

## 변경 파일

- `plugins/news2shorts/scripts/news2shorts.py`
- `plugins/news2shorts/skills/news2shorts/SKILL.md`
- `plugins/news2shorts/skills/news2shorts/references/output-contract.md`
- `plugins/news2shorts/README.md`
- `plugins/news2shorts/.codex-plugin/plugin.json`
- `projects/2026-08-28-parking-blocking-fine/project.json`
- `projects/2026-08-28-parking-blocking-fine/storyboard.json`
- `projects/2026-08-28-parking-blocking-fine/rights-manifest.json`
- 뉴스 이미지 3개와 프로젝트 렌더·썸네일·편집 패키지 결과물

## 설치 상태

- marketplace: `news2shorts-local`
- installed plugin: `news2shorts@news2shorts-local`
- version: `0.36.5+codex.20260828100230`

## 검증 결과

- Skill quick validation: 통과
- Plugin validation: 통과
- Python syntax validation: 통과
- 프로젝트 draft validation: 오류 0
- 예상된 권리 검토 경고 3개만 유지
- 실제 검토 영상: 31.067초, 720x1280, 30fps, H.264/AAC
- `continuous_flow.timing_strategy`: `storyboard-requested`
- hook 장면: 요청·렌더 2.1초
- payoff 장면: 요청·렌더 4.0초
- `preview.mp4` 및 `editable.mp4` 전체 디코딩 확인
- 본문 TTS 요청 0회
- 본문 무음 구간 확인
- DB 작업 없음
- 프론트엔드 빌드 없음
- YouTube 업로드·게시 없음

## 결과물

- `projects/2026-08-28-parking-blocking-fine/preview.mp4`
- `projects/2026-08-28-parking-blocking-fine/thumbnail.jpg`
- `projects/2026-08-28-parking-blocking-fine/render-report.json`
- `projects/2026-08-28-parking-blocking-fine/edit-package/preview/editable.mp4`
- `projects/2026-08-28-parking-blocking-fine/edit-package/preview/captions.srt`
- `projects/2026-08-28-parking-blocking-fine/edit-package/preview/timeline.csv`

## 남은 승인 경계

- 결과는 `rendered_draft` 상태다.
- 뉴스 이미지 3개는 사용자가 게시 전에 권리 확인 또는 교체해야 한다.
- `editorial_reviewed`, `rights_reviewed`, `synthetic_disclosure_reviewed`는 `false`로 유지한다.
- 최종 `short.mp4` 생성과 업로드는 수행하지 않았다.
