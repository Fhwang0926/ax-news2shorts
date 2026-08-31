# News2Shorts v16 유지율·Visual-first 업그레이드 완료

## 완료 내용

- 신규 프로젝트 계약을 version 16으로 올렸다.
- 신규 기본 길이를 continuous-flow 20초로 줄이고 12~35초를 실제 CLI에서 허용했다.
- `--delivery-mode visual-first`를 추가했다.
  - 8~14초
  - 4~6개 콘텐츠 장면
  - 내레이션 없음
  - 첫 3초 화면 상태 3개 또는 실제 영상
  - renderer-generated 무보컬 `news-pulse` BGM
- v16은 전체화면 인트로 대신 첫 프레임 좌상단 64px 뉴스한면 로고를 사용한다.
- v15 이하 프로젝트는 저장된 3.15초 인트로를 그대로 렌더한다.
- `shorts_profile.first_answer_scene_id`와 `truth_guard_scene_id`를 추가했다.
  - continuous-flow 첫 답변 8초 이내
  - visual-first 첫 답변 1.5초 이내
  - 의미를 바꾸는 조건 4초 이내
- render-report version 4에 `audio_bed`, 실제 `retention_timing`, 브랜드 모드를 기록한다.
- v16 CTA 기본값을 2초로 줄이고 visual-first CTA는 무음으로 유지한다.
- CapCut/Vrew 편집 패키지에 corner-logo 자산과 background-music.wav를 포함한다.

## 비교 검토본

- 원본 보존: `projects/2026-08-27-interest-rate-again`
- 신규 검토본: `projects/2026-08-27-interest-rate-again-visual-v2`
- 결과: `preview.mp4`, 13.521초, 720x1280, 30fps, H.264/AAC
- 첫 본문: 0.000초
- 첫 답변: 0.000초
- 계산 조건: 0.000초
- CTA: 2.000초
- 첫 3초 화면 상태: 3개
- 오디오: 무보컬 news-pulse, 평균 -26.7dB, 최대 -20.9dB
- 한국은행·서울 주거 실사 4장과 보유 증거 그래픽 2장을 독립 복사하고 권리·한국 배경 기록을 새 프로젝트에 남겼다.

## 변경 파일

- `plugins/news2shorts/scripts/news2shorts.py`
- `plugins/news2shorts/skills/news2shorts/SKILL.md`
- `plugins/news2shorts/skills/news2shorts/templates/project.template.json`
- `plugins/news2shorts/skills/news2shorts/references/shorts-playbook.md`
- `plugins/news2shorts/skills/news2shorts/references/visual-style.md`
- `plugins/news2shorts/skills/news2shorts/references/reference-formats.md`
- `plugins/news2shorts/skills/news2shorts/references/output-contract.md`
- `plugins/news2shorts/skills/news2shorts/agents/openai.yaml`
- `plugins/news2shorts/README.md`
- `plugins/news2shorts/.codex-plugin/plugin.json`
- `plugins/news2shorts/tests/test_retention_v16.py`
- `projects/2026-08-27-interest-rate-again-visual-v2/*`

## 검증 결과

- 설치 버전: `news2shorts@news2shorts-local` `0.36.5+codex.20260829044342`
- source/cache manifest·script·SKILL·template·output-contract SHA-256 일치
- Python unittest 5개 통과
- Python 구문 검사 통과
- project template·plugin manifest JSON 검사 통과
- source·installed plugin `doctor --json` 통과
- 기존 version 14 금리 프로젝트 검증 오류·경고 0건
- visual-first v2 draft 검증 오류·경고 0건
- visual-first v2 final 검증은 승인 3개 미완료만 차단
- preview.mp4·editable.mp4 전체 디코딩 통과
- corner-logo v16 0초 lead-in과 legacy-full v15 2.9초 lead-in 분기 확인
- 0/1.2/2.2/4/7/12.7초 연락시트 육안 확인
- DB 작업과 프론트엔드 빌드 없음
- Codex PATH alias 생성 경고는 남았지만 플러그인 설치·활성화와 설치본 validator는 통과

## 미검증·게시 경계

- 실제 YouTube 업로드와 Shorts 성과 개선은 검증하지 않았다.
- Typecast가 포함된 v16 continuous-flow 실렌더는 키체인 접근 제한 때문에 수행하지 않았다.
- v2는 `editorial_reviewed`, `rights_reviewed`, `synthetic_disclosure_reviewed`가 false인 로컬 검토본이다.
- 최종 `short.mp4`, 업로드, 예약, 게시, 댓글 등록은 수행하지 않았다.
