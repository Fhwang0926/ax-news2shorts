# 2026-08-19 Animal Viral Shorts MVP 작업 완료

## 작업 범위

- 독립 설치 가능한 animal-viral-shorts 플러그인과 Skill을 추가했다.
- TikTok과 YouTube Shorts 후보를 동일 스키마로 검증하고, 절대 조회수·플랫폼별 보조 지표·편집 적합성·중복·권리 상태를 기준으로 최대 3개만 비교하도록 구현했다.
- 사용자가 직접 제공한 TikTok URL, YouTube Shorts URL, 로컬 MP4·MOV 계열 파일로 프로젝트를 시작할 수 있도록 구현했다.
- 후보 선택 전 획득을 금지하고, 선택한 정식 URL만 yt-dlp로 획득하며 실패 시 source_pending으로 중단하도록 구현했다.
- 대표 프레임과 콘택트시트를 만든 뒤에만 관찰 행동, 타임코드, 감정 근거 수준, 민감 소재, 자막 블러와 워터마크·얼굴 보호 영역을 등록하도록 구현했다.
- 실제 관찰 ID에 연결된 3~6개 비트와 결말을 가진 서로 다른 스토리 3안만 통과시키고, 사용자 선택 전 compose와 render를 차단하도록 구현했다.
- comic-reversal, skill-challenge, relationship-before-after, emotional-assist, pure-behavior-loop의 길이와 고정 점수 계약을 추가했다.
- 선택 스토리를 대본, 스토리보드, 음악 계획, 편집 계획으로 조합하도록 구현했다.
- 720x1280, 30fps, H.264/AAC animal-viral-card-v1 템플릿과 세로 크롭·가로 블러 배경·상단 2줄 헤드라인·하단 장면 자막·출처 표기를 구현했다.
- 원본음을 유지하고 렌더러 생성 비보컬 BGM 또는 출처·라이선스·SHA-256이 기록된 로컬 비보컬 음원을 혼합하도록 구현했다.
- 마지막 실제 원본 프레임 0.5~1초 유지, 비검정 종료 프레임, 해상도·코덱·오디오·fps·길이 검증을 추가했다.
- 권리 불명 원본의 개별 8초·총 18초 제한, 사실상 전체 재업로드 방지, not_permitted 차단, TTS·내레이션·보컬·게시 기능 부재를 최종 게이트에 포함했다.

## 신규 파일

- plugins/animal-viral-shorts/.codex-plugin/plugin.json
- plugins/animal-viral-shorts/README.md
- plugins/animal-viral-shorts/scripts/animal_viral_shorts.py
- plugins/animal-viral-shorts/skills/animal-viral-shorts/SKILL.md
- plugins/animal-viral-shorts/skills/animal-viral-shorts/agents/openai.yaml
- plugins/animal-viral-shorts/skills/animal-viral-shorts/references/candidate-schema.md
- plugins/animal-viral-shorts/skills/animal-viral-shorts/references/output-contract.md
- plugins/animal-viral-shorts/skills/animal-viral-shorts/references/rights-policy.md
- plugins/animal-viral-shorts/skills/animal-viral-shorts/references/story-schema.md
- plugins/animal-viral-shorts/skills/animal-viral-shorts/references/visual-template.md
- plugins/animal-viral-shorts/skills/animal-viral-shorts/references/workflow.md
- plugins/animal-viral-shorts/templates/animal-viral-card-v1.json
- plugins/animal-viral-shorts/templates/candidates.input.json
- plugins/animal-viral-shorts/templates/music-profiles.json
- plugins/animal-viral-shorts/templates/reviewed-observations.input.json
- plugins/animal-viral-shorts/templates/story-options.input.json

## 기존 파일의 최소 변경

- README.md: 플러그인 목록에 animal-viral-shorts 한 줄을 추가했다.
- .agents/plugins/marketplace.json: 기존 순서를 유지하고 신규 플러그인 entry를 마지막에 추가했다.

기존 news2shorts, tiktok2shorts, story2short, whiteboard-shorts, motion2d-studio, viral-shorts 구현은 수정하지 않았다. 작업 시작 전에 존재하던 다른 변경·미추적 파일도 제거하거나 재작성하지 않았다.

## 수행한 정적 확인

- 모든 신규 JSON 파일과 marketplace JSON이 파싱됐다.
- Plugin validator가 통과했다.
- Skill quick validator가 통과했다.
- 최상위 CLI와 doctor, score-candidates, init, acquire, preview, observe, stories, select-story, compose, edit-plan, validate, render의 도움말이 모두 로드됐다.
- doctor --json에서 Python 3.14.5, FFmpeg, FFprobe, Pillow 12.3.0, yt-dlp Python 모듈, Apple SD Gothic Neo 한국어 글꼴을 확인했다.
- doctor 결과 ready_for_preview_and_render가 true였다.
- 이미 등록된 news2shorts-local 마켓플레이스에서 animal-viral-shorts 0.1.0+codex.20260819를 설치했고 installed, enabled 상태를 확인했다.
- 설치 캐시의 CLI SHA-256이 저장소 원본과 일치했으며 설치본 Plugin validator와 Skill validator도 통과했다.
- git diff --check가 통과했다.

## 실행하지 않은 검증

- AGENTS.md 지침에 따라 자동 테스트와 프론트엔드 빌드는 실행하지 않았다.
- 외부 TikTok·YouTube 후보 검색이나 영상 다운로드를 실행하지 않았다.
- 권리 정리된 실제 fixture를 사용한 init부터 최종 MP4까지의 전체 렌더는 실행하지 않았다.
- 최종 MP4의 실제 음량, 자막 가독성, 크롭, 블러, 마지막 프레임을 시각·청각 검수하지 않았다.
- 게시 권리, 공정 이용, 사실성, 동물 복지, 수익화, 플랫폼 승인, 조회수 성과를 검증하지 않았다.
- DB 작업과 외부 업로드는 수행하지 않았다.

## 남은 외부 확인

- 실제 제작 전 현재 공개 지표와 정식 원본 URL을 다시 확인해야 한다.
- 사용자가 선택한 영상의 권리 상태와 필요한 출처 표기를 별도로 검토해야 한다.
- 실제 렌더 검증이 필요하면 권리 정리된 짧은 로컬 영상을 제공한 뒤 전체 흐름 실행을 별도로 요청해야 한다.
