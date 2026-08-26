# news2shorts 정치인 실사진 우선·생성 장면 감축 반영

## 완료 일자

- 2026-08-22

## 플러그인 변경

- 대본·헤드라인·자막에서 실명 정치인과 공직자를 먼저 추출하도록 제작 규칙을 추가했다.
- 핵심 정치인은 첫 주요 언급에 재사용 권리가 확인된 실사진을 우선 배치한다.
- 실명 정치인의 AI 얼굴은 생성하지 않는다.
- 사진의 자산별 권리가 불명확하거나 워터마크가 있으면 `no_usable_asset`으로 기록하고, 공식 문서·도표·지도·영상·설명 그래픽 순으로 대체한다.
- 새 프로젝트의 생성 장면 기본 상한을 40%로 설정했다. 상한을 넘으면 검증기가 실사진·공식 자료·영상·도표 재탐색을 요청한다.
- 생성 스틸이 3장면 이상 연속되지 않도록 제작 가이드와 검증 기준을 강화했다.

## 현재 영상 개선

- 대상: `outputs/2026-08-22/법사위-씨-호칭-논쟁`
- 기존 생성 장면 6/9(66.7%)를 3/9(33.3%)로 줄였다.
- 2번 장면을 김민석 실사진(CC BY 3.0)으로 교체했다.
- 4·6번 장면을 김태규 실사진 2장(공공누리 1유형)으로 교체했다.
- 박균택 사진은 자산별 재사용 조건이 불명확하거나 워터마크·후원 문구가 포함된 후보만 확인돼 제외하고, 얼굴 생성 대신 기존 설명 그래픽을 유지했다.
- 정치인 사진 3장의 출처·라이선스·해시·관련성 검수를 `rights-manifest.json`에 기록했다.
- 새 실사진이 반영된 썸네일과 최종 MP4를 다시 생성했다.

## 변경 파일

- `plugins/news2shorts/skills/news2shorts/SKILL.md`: 실명 정치인 사진 우선, AI 얼굴 금지, 40% 생성 상한 절차를 추가했다.
- `plugins/news2shorts/skills/news2shorts/references/rights-policy.md`: 정치인·공직자 사진의 권리 확인과 대체 규칙을 추가했다.
- `plugins/news2shorts/skills/news2shorts/references/shorts-playbook.md`: 생성 자산 연속 및 비율 기준을 강화했다.
- `plugins/news2shorts/skills/news2shorts/references/visual-style.md`: 실명 공인의 실사진 배치 규칙을 추가했다.
- `plugins/news2shorts/skills/news2shorts/templates/project.template.json`: `named_politician_photo_priority` 및 `max_generated_scene_ratio` 기본값을 추가했다.
- `plugins/news2shorts/scripts/news2shorts.py`: 설정값 범위와 생성 장면 비율·연속 검사를 추가했다.
- `plugins/news2shorts/.codex-plugin/plugin.json`: 기능 설명과 설치 캐시 버전을 갱신했다.
- `outputs/2026-08-22/법사위-씨-호칭-논쟁/project.json`: 실사진 우선·40% 기준을 반영했다.
- `outputs/2026-08-22/법사위-씨-호칭-논쟁/storyboard.json`: 3개 설명 그래픽을 정치인 실사진으로 교체했다.
- `outputs/2026-08-22/법사위-씨-호칭-논쟁/rights-manifest.json`: 사진 출처·권리·검수 기록을 추가했다.
- `outputs/2026-08-22/법사위-씨-호칭-논쟁/publish.json`: 실사진과 일부 설명 그림 사용 공지를 갱신했다.

## 검증 결과

- Skill 구조 검사 통과
- 플러그인 구조 검사 통과
- Python AST, JSON 구문, `git diff --check` 통과
- 최종 프로젝트 검증 오류 0건
- 최종 영상 720x1280, H.264/AAC, 41.13초, Typecast `Seohyeon`
- 화면의 실사진 3개 장면과 실사진이 포함된 합성 썸네일 육안 확인
- 화면에 초안·검토·합성 배지를 표시하지 않음
- 남은 경고 1건: 결론 장면 5.5초가 일반 장면 4초 권장치를 넘지만, 결론 장면 권장 범위 3.5~6초 안에 있음
- `news2shorts@news2shorts-local` `0.22.0+codex.20260822075501` 설치·활성화 확인
- 소스와 설치 캐시의 Skill·렌더러 SHA-256 일치 확인

## 수행하지 않은 작업

- YouTube 업로드·게시는 수행하지 않았다.
- DB 작업과 프론트엔드 빌드는 대상이 아니므로 수행하지 않았다.
