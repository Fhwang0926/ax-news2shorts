# Animal Viral Shorts 베이스 드럼 효과음 추가

## 완료 일자

- 2026-08-25

## 반영 범위

- 사용자의 `뿌우웅` 요청을 지속 베이스나 음성 샘플이 아닌 낮고 긴 감쇠의 베이스 드럼으로 명확히 구분했다.
- 렌더러 생성 무보컬 효과음에 `bass_drum` 유형을 추가했다.
- 약 0.9초 동안 저역 피치가 내려가며 감쇠하는 결정적 PCM 파형으로 구현했다.
- 검토된 묵직한 등장, 대결 전환, 결말에만 배치하도록 스킬과 스토리 계약을 제한했다.
- 플러그인 버전을 `0.4.4+codex.20260825`로 갱신했다.

## 변경 파일

- `plugins/animal-viral-shorts/scripts/animal_viral_shorts.py`: `bass_drum` 검증과 합성 파형 추가.
- `plugins/animal-viral-shorts/skills/animal-viral-shorts/SKILL.md`: 베이스 드럼 사용 조건과 무보컬 경계 추가.
- `plugins/animal-viral-shorts/skills/animal-viral-shorts/references/story-schema.md`: 스토리 효과음 유형과 사용 조건 갱신.
- `plugins/animal-viral-shorts/skills/animal-viral-shorts/references/output-contract.md`: 최종 검증의 지원 효과음 목록 갱신.
- `plugins/animal-viral-shorts/README.md`: 생성 효과음 설명 갱신.
- `plugins/animal-viral-shorts/.codex-plugin/plugin.json`: 버전과 기능 설명 갱신.
- `projects/2026-08-25-brodie-arena-big-boss-v1/creative-brief.json`: 사용자의 베이스 드럼 연출 확정.

## 제한

- 사람 목소리로 `뿌우`를 말한 샘플은 생성하거나 사용하지 않는다.
- 원본 권리 상태는 `unknown`이므로 로컬 검토 범위를 넘는 공개·상업 사용에는 별도 허가가 필요하다.
- 후속 작업에서 공식 URL 원본과 프레임을 검토해 세 스토리 모두 우승 표시 장면에 베이스 드럼 한 번을 배치했다.
- 스토리 자동 선택과 전체 영상 렌더는 아직 수행하지 않는다.

## 검증

- 소스와 설치 캐시의 스킬 구조 검사를 통과했다.
- `animal-viral-shorts@news2shorts-local` `0.4.4+codex.20260825` 설치·활성화를 확인했다.
- 설치본 `doctor --json`에서 메타데이터·프리뷰·렌더 준비 상태를 확인했다.
- 소스와 설치 캐시의 핵심 스크립트·스킬 SHA-256이 각각 일치했다.
- `bass_drum` 한 번을 넣은 3초, 48kHz, 2채널 PCM 검토 샘플을 생성했다.
- 검토 샘플은 0.5초에 시작해 약 1.30초에 감쇠했으며 피크는 -10.15dB로 클리핑이 없었다.
- 프론트엔드 빌드, DB 작업, 로그인·쿠키·캡차·DRM 우회, 제3자 다운로드 사이트, 전체 영상 렌더, 외부 게시·업로드는 수행하지 않았다.
