# news2shorts 중간 CTA와 마지막 CTA 동시 유지 개선 완료

## 요청

- 마지막 사용자 지정 CTA를 추가하더라도 중간 구독 CTA가 임의로 없어지지 않도록 플러그인 개선
- 변경 내용을 현재 저장소에 커밋하고 원격 브랜치에 푸시

## 반영 내용

- `cta_tail.keep_after_mid_cta` 설정을 추가했다.
- 중간 CTA가 렌더된 상태에서 이 값이 `true`이면 기존 0.8초 브랜드 마감으로 강제 교체하지 않고 사용자 지정 마지막 CTA를 유지한다.
- 중간 CTA와 마지막 CTA를 함께 요청했을 때 `mid_cta.mode`를 `disabled`로 바꾸지 않도록 Skill 규칙을 추가했다.
- 렌더 보고서에 `explicit-final-cta-after-mid-v1` 선택 전략을 기록한다.
- 최종 검증기는 중간 CTA 뒤 사용자 지정 CTA를 허용하되, 설정이 없으면 기존 브랜드 마감 계약을 그대로 검사한다.
- 새 프로젝트 템플릿은 `keep_after_mid_cta: false`로 시작해 기존 기본 동작과 호환된다.
- 현재 기본소득당 프로젝트는 `mid_cta.mode: enabled`와 `cta_tail.keep_after_mid_cta: true`를 사용해 중간 구독 CTA와 마지막 좋아요 CTA를 모두 유지하도록 변경했다.

## 변경 파일

- `plugins/news2shorts/scripts/news2shorts.py`
- `plugins/news2shorts/skills/news2shorts/templates/project.template.json`
- `plugins/news2shorts/skills/news2shorts/SKILL.md`
- `plugins/news2shorts/skills/news2shorts/references/output-contract.md`
- `plugins/news2shorts/README.md`
- `plugins/news2shorts/tests/test_retention_v16.py`
- `plugins/news2shorts/.codex-plugin/plugin.json`
- `projects/2026-09-02-basic-income-party-11b-subsidy/project.json`
- `projects/2026-09-02-basic-income-party-11b-subsidy/script.md`
- `docs/complete/2026-09-02-news2shorts-preserve-mid-and-final-cta.md`

## 확인

- Python 구문 검사
- Skill validator
- Plugin validator
- CLI 도움말
- 현재 프로젝트 무음 시각 검토 렌더
- 렌더 보고서에서 중간 CTA와 마지막 CTA 동시 존재 확인
- 작업본과 설치 캐시 비교
- 변경 파일 공백 검사

## 수행하지 않은 작업

- 사용자 지침에 따라 자동화 테스트와 프론트엔드 빌드는 실행하지 않았다.
- 기사 이미지 권리가 미확정이므로 게시용 최종 렌더는 생성하지 않았다.
- DB 작업과 YouTube 업로드·예약·게시·댓글 등록은 수행하지 않았다.
