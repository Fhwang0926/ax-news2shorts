# news2shorts Kangil 메인 보이스 적용 완료

## 요청

- Typecast Kangil 목소리를 news2shorts의 메인으로 사용

## 완료 내용

- 일반 `continuous-flow` 자동 프로젝트의 Typecast 분포를 Kangil 80%, Daeun 20%로 변경했다.
- 같은 프로젝트는 기존처럼 프로젝트 고정 버킷으로 동일한 보이스를 유지한다.
- 민감 뉴스의 Seohyeon, 절차·대처 중심 콘텐츠의 Moonjung, 사용자의 수동 보이스 지정은 그대로 우선한다.
- `visual-first`는 기존처럼 음성 없이 무보컬 BGM을 사용한다.
- 기본 대체 보이스와 `doctor` 기본 보이스 표시도 Kangil Voice ID로 맞췄다.

## 변경 파일

- `plugins/news2shorts/scripts/news2shorts.py`: Kangil 기본 Voice ID와 80:20 자동 선택 분포
- `plugins/news2shorts/README.md`: 사용자 문서의 자동 보이스 정책
- `plugins/news2shorts/skills/news2shorts/SKILL.md`: 제작 지침과 렌더러 설명
- `plugins/news2shorts/tests/test_retention_v16.py`: Kangil 메인 분포 회귀 검사
- `plugins/news2shorts/.codex-plugin/plugin.json`: 설치 캐시 갱신용 버전

## 검증 경계

- 사용자 지침에 따라 테스트와 프론트엔드 빌드는 실행하지 않았다.
- Typecast API 호출이나 음성 렌더도 수행하지 않았다.
