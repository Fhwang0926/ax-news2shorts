# news2shorts 실제 사진·결론·출처 표시 개선 완료

## 반영 내용

- 새 영상은 권리, 비합성 여부, 기사 연관성을 확인한 실제 뉴스 사진을 최소 1장 사용하도록 했다.
- 실제 사진이 없으면 생성 이미지로 조용히 대체하지 않고 최종 렌더에서 명확한 오류를 표시하도록 했다.
- 생성 이미지는 왜곡, 중복 물체, 깨진 형태·글자, 의도하지 않은 로고와 잘못된 크롭을 육안으로 확인한 `visual_quality_reviewed` 기록이 있어야 새 프로젝트의 최종 검증을 통과하도록 했다.
- 생성 이미지 안에는 글자·숫자·로고를 넣지 않고 렌더러의 자막을 사용하도록 제작 규칙을 보강했다.
- 마지막 `payoff` 장면에 굵은 노란색 `결론` 배지를 자동 표시하고 최소 3.5초 유지하도록 했다.
- 모든 장면 하단에 작은 `뉴스 출처: <매체명>`을 표시하고 `sources.json`의 ID와 연결하도록 했다.
- 자산 소유·사용 권리 표시는 기존 `credit`, 보도 근거는 새 `source_label`로 분리했다.
- 기존 프로젝트는 새 필수 옵션이 없으면 이전과 같은 검증 규칙을 적용해 다시 렌더할 수 있도록 호환성을 유지했다.

## 변경 파일

- `plugins/news2shorts/scripts/news2shorts.py`: 실제 사진, 생성 이미지 육안 검수, 장면별 뉴스 출처, 결론 노출 검증과 렌더링 추가
- `plugins/news2shorts/skills/news2shorts/SKILL.md`: 실제 뉴스 사진 필수 수집과 생성 이미지 품질 검수 작업 흐름 추가
- `plugins/news2shorts/skills/news2shorts/references/rights-policy.md`: 실제 사진 인정 조건과 생성 이미지 품질 승인 항목 추가
- `plugins/news2shorts/skills/news2shorts/references/output-contract.md`: 새 프로젝트·스토리보드·권리 매니페스트 필드 정의 추가
- `plugins/news2shorts/skills/news2shorts/references/visual-style.md`: 결론 배지와 작은 뉴스 출처 표시 규칙 추가
- `plugins/news2shorts/skills/news2shorts/templates/project.template.json`: 새 검증·표시 옵션 기본 활성화
- `plugins/news2shorts/skills/news2shorts/templates/storyboard.template.json`: `source_label`, `source_ids` 기본 필드 추가
- `plugins/news2shorts/README.md`: 새 제작·검증 규칙과 제한사항 반영
- `plugins/news2shorts/.codex-plugin/plugin.json`: 버전 `0.7.0+codex.20260817` 및 기능 설명 갱신

## 확인 결과

- Python 구문 검사 통과
- 원본 및 설치 캐시 Skill 검사 통과
- 새 프로젝트 초기화 시 실제 사진, 생성 이미지 품질, 결론 배지, 뉴스 출처 옵션이 자동 활성화됨을 확인
- 새 최종 검증에서 실제 사진 누락, 생성 이미지 육안 검수 누락, 장면별 출처 누락을 각각 오류로 차단함을 확인
- 기존 `2026-08-16-aircon-45c-factcheck` 프로젝트는 최종 검증 오류 0건으로 호환됨을 확인
- 음성 없이 임시 720x1280 MP4를 렌더하고 마지막 프레임에서 `결론` 배지, 자막, 자산 크레딧, 작은 뉴스 출처가 겹치거나 잘리지 않음을 육안 확인
- 설치 캐시와 원본 렌더러의 SHA-256이 일치함을 확인
- 재설치 버전: `news2shorts@news2shorts-local` `0.7.0+codex.20260817`

## 범위

- 기존 쇼츠 프로젝트와 최종 영상은 수정하거나 다시 제작하지 않았다.
- 기사 사진은 공개돼 있다는 이유만으로 가져오지 않으며, 사용 권리를 확인할 수 없으면 최종 제작을 중단한다.
- 외부 업로드, 게시, 데이터베이스 작업, 프론트엔드 빌드는 수행하지 않았다.
