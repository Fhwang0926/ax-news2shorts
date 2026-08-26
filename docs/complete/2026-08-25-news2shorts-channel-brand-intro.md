# news2shorts 뉴스한면 채널 인트로 적용 완료

## 요청

- 사용자가 제공한 실제 뉴스한면 채널 로고를 공통 인트로에 사용한다.
- 인트로 문구를 `세상의 이슈를 모아 / 우리 삶의 문제를 짚습니다`로 고정한다.
- 확인한 샘플을 `news2shorts` 플러그인의 새 기본 인트로로 반영하고 재설치한다.

## 반영 내용

- 실제 채널 로고를 포함한 3.15초 720x1280 H.264/AAC 인트로를 플러그인 자산으로 추가했다.
- 새 기본 자산 ID를 `news-hanmyeon-channel`로 변경했다.
- 새 프로젝트 템플릿과 런타임 기본값은 뉴스한면 인트로를 사용한다.
- 기존 프로젝트가 저장한 `oldman-korea-map` 자산 ID는 레거시 호환용으로 유지했다.
- 검증, 렌더 보고서, 편집 패키지는 프로젝트에 설정된 기본 또는 레거시 자산을 일관되게 사용한다.
- 플러그인 버전을 `0.36.0+codex.20260825210241`로 올리고 로컬 Codex 캐시에 재설치했다.

## 변경 파일

- `plugins/news2shorts/assets/brand-intro-news-hanmyeon.mp4`: 실제 채널 로고와 고정 문구를 포함한 기본 인트로.
- `plugins/news2shorts/assets/news-hanmyeon-channel-logo.png`: 사용자가 제공한 채널 로고 원본 사본.
- `plugins/news2shorts/assets/brand-intro-news-hanmyeon.json`: 자산 해시, 구성, 사용 범위와 권리 경계.
- `plugins/news2shorts/scripts/news2shorts.py`: 새 기본 자산, 레거시 자산 매핑, 검증·렌더·편집 패키지 처리.
- `plugins/news2shorts/skills/news2shorts/templates/project.template.json`: 새 기본 자산 ID.
- `plugins/news2shorts/skills/news2shorts/references/output-contract.md`: 기본 및 레거시 인트로 계약.
- `plugins/news2shorts/skills/news2shorts/SKILL.md`: 뉴스한면 로고·문구와 렌더 순서.
- `plugins/news2shorts/README.md`, `README.md`: 사용자 동작 설명.
- `plugins/news2shorts/.codex-plugin/plugin.json`: 버전과 기능 설명.

## 검증

- Python 구문 검사, Plugin·자산·템플릿 JSON 파싱, Skill Creator `quick_validate.py`, `git diff --check` 통과.
- 원본과 설치 캐시의 `doctor --json`이 모두 `ok: true`이며 기본 자산 `news-hanmyeon-channel`의 720x1280 영상과 오디오 스트림을 확인했다.
- 원본 렌더러에서 새 기본 자산과 레거시 `oldman-korea-map` 자산을 각각 본문 테스트 클립에 합성했다. 두 결과 모두 0.25초 `fadeblack`과 4.422초 총 길이를 기록했다.
- 새 기본 합성본에서 실제 채널 로고와 두 줄 문구, 전환 중 암전, 전환 후 본문 프레임을 직접 확인했다.
- 설치 캐시 렌더러로도 새 기본 인트로 합성을 실행했다. 결과는 720x1280, 30fps, H.264/AAC, 4.422초이며 전체 디코딩을 통과했다.
- 원본과 설치 캐시의 렌더러, Skill, 인트로 MP4, 채널 로고 PNG SHA-256이 각각 일치한다.
- 프론트엔드 변경이 아니므로 프론트 빌드는 실행하지 않았다.

## 권리 경계

채널 로고는 사용자가 제공했고 반복 적용을 요청했다. 이 기록은 제3자 권리를 새로 부여하지 않으며 실제 공개·수익화 권리 확인은 사용자 책임으로 남긴다.
