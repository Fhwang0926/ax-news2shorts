# news2shorts 이미지 안전 맞춤·인기 보이스 자동 선택·CTA 음성 반영

## 완료 일자

- 2026-08-20

## 반영 범위

- 새 정지 이미지는 `image_fit: "auto"`를 기본으로 사용한다.
  - 원본 전체를 증거 안전 영역에 축소 배치한다.
  - 남는 세로 화면은 같은 이미지의 어두운 블러 배경으로 채운다.
  - 문서·차트·단체 사진은 `contain`, 의도적으로 검수한 전체 화면 크롭만 `cover`를 사용할 수 있다.
- Typecast는 공개되지 않은 수치형 사용량 1위를 임의로 만들지 않는다.
  - Typecast 공식 인기 캐릭터 Top 5인 다은·서현·필재·문정·강일을 후보군으로 사용한다.
  - 민감성, 안내 비중, 포맷, 목표 길이에 따라 콘텐츠에 맞는 후보를 자동 선택한다.
  - 선택 전략, 인기 후보 근거, 공식 출처, 보이스와 이유를 진단·프로젝트·렌더 보고서에 기록한다.
- 결론 뒤 공통 CTA는 같은 선택 음성으로 `구독과 좋아요 누르면, 빠른 소식 전해드릴게요.`를 읽는다.
  - 기본 CTA 화면은 `빠른 소식 계속 / 구독 · 좋아요`다.
  - 실제 음성 길이에 0.25초 여유를 더해 최대 6초 안에서 테일 길이를 자동 조정한다.
  - `--no-tts`를 명시한 검토 렌더만 기존 자체 큐를 사용한다.

## 변경 파일

- `plugins/news2shorts/scripts/news2shorts.py`
  - `auto`, `contain`, `cover` 이미지 맞춤 렌더와 검증을 추가했다.
  - 공식 인기 후보군 기반 Typecast 선택 전략과 근거 기록을 추가했다.
  - 장면과 같은 보이스·Smart Emotion 문맥을 사용하는 CTA 음성 합성과 실제 길이 조정을 추가했다.
- `plugins/news2shorts/skills/news2shorts/templates/project.template.json`
  - 4초 CTA 기본값, 빠른 소식 문구, CTA 내레이션과 음성 활성화를 추가했다.
- `plugins/news2shorts/skills/news2shorts/templates/storyboard.template.json`
  - 정지 이미지 기본값 `image_fit: "auto"`를 추가했다.
- `plugins/news2shorts/skills/news2shorts/SKILL.md`
  - 이미지 원본 보존, 공개 근거가 있는 인기 후보 자동 선택, CTA 음성 제작 규칙을 반영했다.
- `plugins/news2shorts/skills/news2shorts/references/output-contract.md`
  - 새 이미지 맞춤·보이스 선택·CTA 렌더 보고서 계약을 문서화했다.
- `plugins/news2shorts/skills/news2shorts/references/visual-style.md`
  - 증거 안전 영역 이미지 배치와 CTA 음성 시각 규칙을 추가했다.
- `plugins/news2shorts/README.md`, `README.md`
  - 사용자 기능과 렌더 동작을 새 기본값에 맞췄다.
- `plugins/news2shorts/.codex-plugin/plugin.json`
  - 플러그인 버전을 `0.20.0+codex.20260820`으로 올렸다.

## 검증 결과

- Python 도움말 실행과 JSON 템플릿 파싱 성공
- Skill 구조 검사 성공
- 자동 보이스 분기 확인
  - 30초 일반 쇼츠: Daeun
  - 45초 팩트 뉴스: Seohyeon
  - 45초 스토리: Piljae
  - 민감 뉴스: Seohyeon
- 1280x853 가로 사진을 렌더해 원본 전체가 안전 영역에 남고 블러 배경이 채워지는 것을 직접 확인
- CTA 검토 렌더가 720x1280 H.264/AAC, 4초, 화면 글자 비잘림 상태임을 직접 확인
- macOS 키체인의 Typecast 설정 상태 확인
- 실제 Typecast CTA 합성 성공
  - 보이스: Daeun
  - 합성 음성: 3.857초
  - 자동 조정 CTA: 4.107초
- 기존 version 4 프로젝트 복사본 전체 렌더 성공
  - 720x1280 H.264/AAC
  - 6개 장면 모두 `image_fit: "auto"` 보고서 기록
- `git diff --check` 성공
- 로컬 플러그인 `news2shorts@news2shorts-local` 0.20.0 설치·활성화 확인
- 설치 캐시의 렌더러와 Skill SHA-256이 소스와 일치함을 확인

## 수행하지 않은 작업

- 새 뉴스 영상 제작과 YouTube 업로드는 수행하지 않았다.
- DB 작업과 프론트엔드 빌드는 대상이 아니므로 수행하지 않았다.

## 근거

- Typecast 공식 인기 캐릭터 Top 5 소개: `https://typecast.ai/kr/learn/typecast-new-editor-characters/`
