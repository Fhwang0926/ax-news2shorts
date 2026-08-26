# News2Shorts 상황 일치 이미지와 비판형 막타 개선

## 요청 반영

- 장면의 주제만 비슷한 아이콘을 고르지 않고 `주체 + 행동 + 보이는 결과`가 실제 대사와 맞는 이미지를 고르도록 제작 규칙을 강화했다.
- 사과 장면은 서비스 아이콘 묶음 대신 익명 식당 직원이 소비자에게 허리 숙여 사과하는 편집 이미지로 교체했다.
- 결말 카드에서 `환불 완료 여부 미확인`을 제거하고, 확인된 업체 조치를 먼저 제시한 뒤 `사진 오류, 소비자 부담?`으로 끝내도록 변경했다.
- 중요한 불확실성은 사실표와 `truth_guard`에 보존하되, 비핵심 미확인 상태를 결말 문구로 소비하지 않도록 검증 규칙을 추가했다.

## 플러그인 변경

- `plugins/news2shorts/skills/news2shorts/SKILL.md`: 핵심 장면별 의미 브리프와 비판형 payoff 규칙 추가.
- `plugins/news2shorts/skills/news2shorts/references/visual-style.md`: 장면의 동사에 맞는 이미지 우선순위 추가.
- `plugins/news2shorts/skills/news2shorts/references/shorts-playbook.md`: 사과·환불·점검 등 행동별 직접 시각화와 미확인 막타 금지 규칙 추가.
- `plugins/news2shorts/scripts/news2shorts.py`: 일반적인 `미확인`, `확인 중`, `아직 없음`, `지켜봐야` payoff punch를 검증에서 차단하고 예시 문구를 시민 부담형으로 교체.
- `plugins/news2shorts/.codex-plugin/plugin.json`: 버전을 `0.36.1+codex.20260825220000`으로 갱신.

## 재생성 프로젝트

- 프로젝트: `projects/2026-08-25-pyeongtaek-tonkatsu-menu-gap/`
- 새 사과 이미지: `assets/generated/apology-bow-editorial.png`
- 새 비판 결말 이미지: `assets/generated/five-vs-two-consumer-question.png`
- 수정 영상: `preview.mp4`
- 수정 결말: `업체도 관리 소홀 인정 → 수정·점검·환불·사과 약속 → 사진 오류, 소비자 부담?`
- 수정 음성 막타: `환불과 사과도 약속했습니다. 사진 오류, 소비자 몫일까요?`

## 검증 결과

- Skill Creator 빠른 검증 통과.
- Python 문법과 JSON 파싱 통과.
- 소스와 설치 캐시의 스크립트·Skill SHA-256 일치.
- `news2shorts@news2shorts-local` `0.36.1+codex.20260825220000` installed·enabled 확인.
- 설치본 doctor 통과: 720x1280 브랜드 인트로, FFmpeg, FFprobe, Pillow, 로컬 TTS 확인.
- Typecast Piljae로 720x1280 H.264/AAC 31.728초 검토 영상을 재생성.
- 추출 프레임에서 사과 행동, 5조각 대 2조각, 결말 문구의 잘림과 겹침이 없는 것을 확인.
- 초안 검증 통과, `git diff --check` 통과.

## 남은 제한

- 6개 장면 중 생성 이미지가 4개라 플러그인 권장 비율 40%를 넘는다.
- 사건과 직접 일치하면서 재사용 권리가 확인된 실제 뉴스 사진이 없어 공개용 최종 권리 검증은 통과하지 않는다.
- scene-03 자체 제작 그래픽과 scene-04 일반 자료사진도 사건 직접 사진으로 승인하지 않았다.
- 따라서 공개용 `short.mp4`와 YouTube 업로드는 만들지 않았고, 승인 전 `preview.mp4`만 갱신했다.
- 프론트엔드 빌드와 DB 작업은 수행하지 않았다.
