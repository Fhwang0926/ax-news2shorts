# news2shorts 지역·인물·책임 템플릿과 제주 영상 재생성 완료

## 요청

- 제주도처럼 기사에서 확인되는 실제 지역명을 화면과 내레이션에 사용한다.
- 실제 인물 사진을 우선 검토하고, 사용 시 권리와 사건 당사자 여부를 분명히 한다.
- 거짓 보고·자료 삭제처럼 확인된 분노·책임 포인트를 시민 피해와 강하게 연결한다.
- 개선 사항을 한 영상 전용이 아닌 새 프로젝트 공통 템플릿으로 반영하고 기존 제주 영상을 재생성한다.

## 플러그인 반영

- 새 프로젝트 버전을 10으로 올리고 `editorial_grounding` 계약을 추가했다.
- `locations`는 검증된 실제 이름과 첫 맥락 장면을 기록하고, 해당 장면의 화면 또는 내레이션에 이름이 실제로 등장하는지 검사한다.
- `people`는 중앙 실명 인물의 역할, 첫 주요 장면, 사진 사용·사생활 제외·권리 장애 상태를 기록한다.
- 실명 인물의 사용 자산은 `person_names`와 육안 식별 검수를 요구하고 생성형 인물 대체를 차단한다.
- 피해자·사인 사진은 공개 여부만으로 재사용하지 않고, 권리 근거와 공익상 필요가 없으면 `privacy_excluded`로 남긴다.
- 다른 실제 사람의 자료사진은 `사건 당사자 아님`을 표시하도록 문서화했다.
- `accountability`는 확인된 행위·누락, 시민 피해·신뢰 훼손, 근거 주장, 임팩트 장면을 연결한다. 근거가 없으면 `not_applicable`을 사용한다.
- 기존 version 9 이하 프로젝트는 새 계약을 강제하지 않아 호환성을 유지한다.
- 플러그인 버전을 `0.30.0+codex.20260824102104`로 올리고 로컬 마켓플레이스에 재설치했다.

## 제주 영상 재생성

- 첫 훅을 `제주도 경찰이 실종 두 건을 허위 종결했다면, 믿을 수 있습니까?`로 바꿨다.
- `안전 확인 없는 무사 거짓 보고 → 사건 종결 → 자료 삭제와 추가 종결 → 가족 재신고 뒤 사망 발견` 순서로 책임과 피해를 연결했다.
- 홍석기 국가수사본부장과 제주경찰청을 실제 이름으로 언급했다.
- CC BY-SA 4.0의 실제 한국 경찰관 자료사진을 사용하고 첫 화면에 `사건 당사자 아님`을 크게 표시했다.
- 홍석기 본부장 사진은 통신사 저작권 때문에 제외했고, 장미란 씨 사진은 가족 제공·실종 목적과 사생활 문제로 제외했다.
- 결론 카드를 `사과보다 검증 / 관리자 승인 · 기록 추적 / 개인 일탈?`로 강화했다.
- Typecast 자동 보이스 `Seohyeon`으로 720×1280 H.264/AAC 검토 영상 `preview-v2.mp4`를 만들었다.
- 총 길이는 35.718초이며 별도 썸네일과 CapCut/Vrew 호환 편집 패키지를 다시 만들었다.

## 변경 파일

- `plugins/news2shorts/.codex-plugin/plugin.json`: 0.30.0 버전과 기능 설명.
- `plugins/news2shorts/scripts/news2shorts.py`: version 10 지역·인물·책임 검증과 실명 인물 자산 연결 검사.
- `plugins/news2shorts/skills/news2shorts/SKILL.md`: 제작 단계의 지역명, 실제 인물, 책임 연결 규칙.
- `plugins/news2shorts/skills/news2shorts/references/shorts-playbook.md`: 구체성·책임 게이트와 장면 전개 기준.
- `plugins/news2shorts/skills/news2shorts/references/rights-policy.md`: 실명 인물·피해자·맥락 자료사진 권리 정책.
- `plugins/news2shorts/skills/news2shorts/references/output-contract.md`: `editorial_grounding` 데이터 계약.
- `plugins/news2shorts/skills/news2shorts/templates/project.template.json`: 새 version 10 기본 필드.
- `plugins/news2shorts/skills/news2shorts/agents/openai.yaml`: 기본 제작 프롬프트.
- `plugins/news2shorts/README.md`: 사용자용 기능 설명.
- `projects/2026-08-24-jeju-police-false-closures-followup/project.json`: 제주도·인물·책임 검토 기록.
- `projects/2026-08-24-jeju-police-false-closures-followup/script.md`: 지역명과 강한 책임 연결 대본.
- `projects/2026-08-24-jeju-police-false-closures-followup/storyboard.json`: 실제 경찰관 자료사진과 강화된 6장면 팩트스택.
- `projects/2026-08-24-jeju-police-false-closures-followup/rights-manifest.json`: 사진 라이선스, 인물 제외 근거, 사건 당사자 아님 기록.
- `projects/2026-08-24-jeju-police-false-closures-followup/publish.json`: 제주도와 책임 연결이 포함된 업로드 설명·고정 댓글.
- `projects/2026-08-24-jeju-police-false-closures-followup/preview-v2.mp4`: 재생성 검토 영상.
- `projects/2026-08-24-jeju-police-false-closures-followup/thumbnail.jpg`: 실제 경찰관·제주경찰청·경찰차 합성 썸네일.
- `projects/2026-08-24-jeju-police-false-closures-followup/edit-package/preview-v2/`: 외부 편집 호환 패키지.

## 검증

- Python 구문, JSON 파싱, Skill 빠른 검증, 도움말 실행과 `git diff --check`를 통과했다.
- 설치 캐시와 소스의 스크립트, SKILL, 프로젝트 템플릿 SHA-256이 일치한다.
- 설치된 플러그인 목록에서 `news2shorts 0.30.0+codex.20260824102104` 활성화를 확인했다.
- Typecast 키체인 연결과 `Seohyeon` 음성 사용을 확인했다.
- 재생성 영상은 720×1280, H.264/AAC, 35.718초다.
- 첫 인물 장면, 전체 접촉 시트, 결론 카드와 썸네일을 육안 확인했다.
- 홍석기 본부장 실사진 권리 장애와 모든 근거 장면이 정지 이미지라는 권고는 투명하게 유지했다.

## 남은 단계

- 실종·사망 관련 민감 뉴스이므로 결과는 검토용 `preview-v2.mp4`다.
- 사용자가 표현과 권리 기록을 승인한 뒤에만 최종 `short.mp4`를 만든다.
