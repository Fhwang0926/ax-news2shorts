# news2shorts 공통 인트로·본편 전환 적용 완료

## 요청

- 사용자가 만든 한국 지도 블러 배경 캐릭터 영상을 모든 `news2shorts` 결과물 앞에 고정한다.
- 인트로에서 뉴스 본편으로 넘어갈 때 화면 전환 효과를 적용한다.
- 뉴스 쇼츠 본편과 기존 구독·좋아요 테일은 인트로 뒤에 유지한다.

## 반영 내용

- 플러그인 내부에 3.15초 720x1280 H.264/AAC 공통 인트로 자산과 메타데이터를 포함했다.
- 새 프로젝트를 version 7로 올리고 `brand_intro.enabled=true`, `asset=oldman-korea-map`, `transition=fadeblack`, `transition_duration=0.25`를 기본값으로 추가했다.
- 기존 프로젝트에 설정이 없어도 현재 렌더러로 다시 렌더하면 같은 인트로를 자동으로 붙인다.
- 인트로 원본 오디오와 첫 뉴스 오디오를 0.25초 동안 교차시키고, 영상도 같은 구간에만 `fadeblack`을 적용한다.
- 뉴스 장면 사이는 기존 하드 컷을 유지하고, 최종 순서를 `공통 인트로 → 뉴스 본편 → 결론 → CTA 테일`로 고정했다.
- `doctor`, 프로젝트 검사, 최종 렌더 검사, `render-report.json`에 공통 인트로 자산·영상/음성·전환 상태를 추가했다.
- 플러그인 버전을 `0.26.0+codex.20260824000201`로 갱신하고 Codex 캐시에 재설치했다.

## 변경 파일

- `plugins/news2shorts/assets/brand-intro-oldman-korea-map.mp4`: 공통 인트로 영상 자산.
- `plugins/news2shorts/assets/brand-intro-oldman-korea-map.json`: 원본 유형, 편집 내역, 해시, 반복 사용 범위와 권리 책임 기록.
- `plugins/news2shorts/scripts/news2shorts.py`: 인트로 설정·진단·검증·영상/오디오 전환·렌더 보고서 구현.
- `plugins/news2shorts/skills/news2shorts/templates/project.template.json`: version 7과 기본 `brand_intro` 계약.
- `plugins/news2shorts/skills/news2shorts/SKILL.md`: 모든 렌더의 인트로·본편·CTA 순서와 전환 규칙.
- `plugins/news2shorts/skills/news2shorts/references/output-contract.md`: project/render-report version 7 계약.
- `plugins/news2shorts/README.md`, `README.md`: 사용자 동작과 렌더 순서 설명.
- `plugins/news2shorts/.codex-plugin/plugin.json`: 0.26.0 버전 및 기능 설명.

## 검증

- Python AST 및 JSON 파싱 통과.
- Skill Creator `quick_validate.py` 원본·설치 캐시 모두 통과.
- `doctor --json` 원본·설치 캐시 모두 `ok: true`; 공통 인트로 720x1280, 영상·음성 스트림 확인.
- 기존 version 4 프로젝트 복사본을 원본 렌더러와 설치 캐시 렌더러에서 각각 `--draft --no-tts`로 실제 렌더 성공.
- 설치 캐시 결과: 28.23초, 720x1280, 30fps, H.264/AAC, 인트로 및 CTA 활성화.
- 0.40초·2.75초에서 인트로, 2.98초에서 전환 중 암전, 3.18초 이후 첫 뉴스 화면을 프레임으로 확인했다.
- 인트로·뉴스 경계 오디오 구간에 오디오 신호가 존재함을 확인했다.
- 원본과 설치 캐시의 렌더러·Skill·인트로 자산 SHA-256 일치 확인.
- `git diff --check` 통과. 프론트엔드 빌드는 대상이 아니므로 실행하지 않았다.

## 권리 경계

공통 인트로는 사용자가 제공한 원본을 사용자의 반복 적용 요청에 따라 플러그인 자산으로 포함했다. 이 기록은 제3자 저작권 또는 상업적 게시 권리를 새로 부여하지 않으며, 실제 공개·수익화 권리 확인은 사용자 책임으로 남긴다.
