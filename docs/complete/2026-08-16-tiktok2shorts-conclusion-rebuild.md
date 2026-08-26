# 2026-08-16 tiktok2shorts 길이·최종 결론 리빌드 완료

## 요청 반영

- 기존 17.321초, 4장면 결과를 25.521초, 7장면으로 다시 구성했다.
- 시작에는 완성된 계란국을 보여 주고, 말린 버섯·무·참기름·달걀물 순서를 거쳐 마지막 4.5초에 완성 그릇을 다시 보여 준다.
- 마지막 화면 문구는 `계란국 한 그릇이 완성됐다`와 `다진 파와 계란 가닥으로 마무리`이며, 원본의 다진 파가 올려진 완성 그릇 장면을 사용한다.

## 플러그인 개선

- 최종 렌더 검증에서 마지막 스토리보드 장면이 반드시 `role: "conclusion"`이어야 한다.
- 결론 장면도 실제 원본 또는 출처가 기록된 시각 자산과 `source_evidence`를 갖춰야 하며, 추상적인 엔드카드만으로는 최종 렌더할 수 없다.
- `delivery-note.md`와 `render-report.json`에 최종 결론 및 장면 역할이 기록된다.
- 새 프로젝트의 기본 해설 계획도 마지막 비트를 `conclusion`으로 생성한다.

## 결과물

- 최종 MP4: `outputs/tiktok2shorts/2026-08-16/egg-drop-soup/outputs/short.mp4`
- 전달 문서: `outputs/tiktok2shorts/2026-08-16/egg-drop-soup/delivery-note.md`
- 렌더 보고서: `outputs/tiktok2shorts/2026-08-16/egg-drop-soup/render-report.json`
- 원본 링크: `https://www.tiktok.com/@jujumaoo/video/7662349457840688405`
- 25.521초, 720x1280, H.264/AAC, 7개 장면 모두 `source_video`다. 원본 구간 합계는 18초 제한 안이다.

## 검증 경계

- Python 구문 검사, `validate --final`, 실제 `render --overwrite`, 변경 공백 검사를 통과했다.
- 최종 MP4에서 말린 버섯, 참기름, 완성 계란국 결론 장면을 추출해 화면 문구와 원본 영문 표기를 대조했다.
- 외부 업로드, 게시 권한, 수익화 판단, 라이선스의 법적 유효성은 검증하지 않았다. 원본 권리 상태는 `unknown`이고 결과물은 로컬 전용이다.

## 변경 파일

- `plugins/tiktok2shorts/scripts/tiktok2shorts.py`: 결론 장면 검증, 전달 문서 결론 표시, 렌더 보고서 장면 역할 기록.
- `plugins/tiktok2shorts/.codex-plugin/plugin.json`: 0.1.4 버전과 결론 보장 설명 반영.
- `plugins/tiktok2shorts/README.md`, `skills/tiktok2shorts/SKILL.md`, `skills/tiktok2shorts/references/output-contract.md`: 실제 결론 장면 계약 문서화.
- `outputs/tiktok2shorts/2026-08-16/egg-drop-soup/{script,storyboard,commentary-plan,viral-analysis}.json`: 25.5초 7장면 시나리오와 결론 장면 반영.
