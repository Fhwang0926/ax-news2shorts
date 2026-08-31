# 2026-08-29 news2shorts 네팔 EBS 경고 대본 초안 완료

## 작업 범위

- 사용자가 승인한 네팔 대홍수 소스와 선택한 1번 대본 방향 `예언인 줄 알았는데, 다른 재난`만 반영했다.
- EBS가 다룬 임자호수 빙하호 범람과 이번 라수와 빙하·암반 붕괴를 같은 사건으로 오해하지 않도록 비교 반전형 quick-reveal로 구성했다.
- 한국인 9명의 안전과 수색을 첫 훅의 시민 이해관계로 명시했다.
- 전체 대본, 7개 장면 구성, 근거 연결, 검토용 자막 초안까지만 작성했다.
- 이미지, 음성, 썸네일, 영상 렌더링, 업로드 정보는 생성하지 않았다.

## 핵심 편집 판단

- 첫 4초 안에 두 사건의 장소와 원인이 다르다는 사실 제한을 배치했다.
- 이번 홍수의 발생 메커니즘과 기후 요인의 기여도는 분석 중이라는 조건을 유지했다.
- 피해 장면을 자극적으로 소비하지 않고 수색 현황과 고산 재난 감시 공백으로 결론을 회수했다.
- EBS 및 언론사 화면은 공개 접근 가능 여부와 별개로 재사용 권리가 확인되지 않아 이미지 단계에서 사용하지 않도록 기록했다.

## 변경 파일

- `projects/2026-08-29-nepal-ebs-warning-quick-reveal/project.json`: 선택 후크, 시민 이해관계, 진실 가드, 재후킹, 결론과 지역 정보를 기록했다.
- `projects/2026-08-29-nepal-ebs-warning-quick-reveal/sources.json`: 외교부 공식 자료와 국내외 독립 보도·전문가 자료 8건을 기록했다.
- `projects/2026-08-29-nepal-ebs-warning-quick-reveal/fact-sheet.json`: 확인 사실과 잠정 분석 8건을 출처에 연결했다.
- `projects/2026-08-29-nepal-ebs-warning-quick-reveal/script.md`: 선택 후크, 장면별 대본, 전체 내레이션과 검증 메모를 작성했다.
- `projects/2026-08-29-nepal-ebs-warning-quick-reveal/storyboard.json`: 7개 장면의 화면 문구, 내레이션, 근거 주장과 스토리 연결을 기록했다.
- `projects/2026-08-29-nepal-ebs-warning-quick-reveal/captions-draft.srt`: 음성 생성 전 검토용 자막 타이밍 초안을 작성했다.

## 확인 결과

- `project.json`, `sources.json`, `fact-sheet.json`, `storyboard.json`의 JSON 문법을 확인했다.
- news2shorts 초안 검증 결과 오류는 0건이다.
- 남은 경고는 이미지·실제 뉴스 사진·썸네일·업로드 정보가 아직 없다는 다음 단계 항목뿐이다.
- 사용자가 대본 SHA-256 `04e7de85bcdcb768c2a4d99320837a4f1f4dd7d9a6be7b584d329953fcd4c3a9`를 승인했다.
- `image-options.json`에 실제 지원되는 기본 시각 패키지, 재난 과정 설명, EBS 자료 처리 옵션과 제외 사유를 기록했다.
- 사용자가 `A-1-가` 조합을 선택해 권리 대기 실제 대응 사진 2장과 자체 지도·과정도 5장을 준비했다.
- EBS 영상·캡처와 네팔 현장 언론 사진은 사용하지 않았다.
- `assets/review/image-contact-sheet.png`와 `image-review.md`를 만들어 이미지 결과와 권리 상태를 한 번에 검토할 수 있게 했다.
- 이미지 검토 승인 전까지 음성·렌더링을 진행하지 않는다.

## 이미지 구성 v2 전면 수정

- 사용자가 기존 회의 사진과 단순 도식 구성을 거절해 해당 결과를 `revisions/image-v1/`로 보존했다.
- 국제 실제사건 시각 예외를 news2shorts 소스·Skill·템플릿에 추가했다. 한국 시민의 직접 안전 영향, 정확한 현장 국가·로케일, 실제 사건 맥락 검수, 권리 검토 필수를 모두 기록해야 활성화된다.
- 장면 1·2·4·5·6·7을 ABC·Euronews·SBS가 공개한 실제 네팔 홍수·헬기 수색 영상 구간으로 교체했다.
- 장면 3은 CC BY-SA 3.0으로 공개된 실제 임자호수 사진으로 교체했다.
- EBS 영상·캡처는 사용하지 않았고, 방송사 표식과 위치 문구를 제거하지 않았다.
- 새로운 결과는 `assets/review/image-contact-sheet-v2.png`와 `image-review.md`에서 확인한다.

## news2shorts 국제 실제사건 영상 지원

- `plugins/news2shorts/scripts/news2shorts.py`에 한국 시민의 직접 안전·권리 영향이 있는 국제 사건만 허용하는 `international_source_visuals` 검증 경로를 추가했다.
- 새 프로젝트는 `--international-source-country`, `--international-source-locale`, `--international-citizen-stake`를 모두 제공해야 예외를 활성화할 수 있다.
- 국제 실제 사진·영상은 현장 국가·로케일, 실제 사건 맥락 검수, 정확한 장면 근거, 권리 검토 필수를 기록한다. 일반 외국 스톡과 과거 유사 사고 영상은 계속 차단한다.
- `collect-internet-visual`이 한국 대응 자료와 국제 실제사건 자료를 구분해 검증하도록 확장했다.
- Skill의 본문, 권리 정책, 시각 스타일, 출력 계약, 프로젝트 템플릿을 같은 규칙으로 갱신했다.
- 플러그인 버전을 `0.36.5+codex.20260829145552`로 갱신하고 `news2shorts-local`에서 재설치했다.
- 소스와 설치 캐시의 CLI SHA-256은 `0af0cb2e65c5d0825c3cba6aef9df49a2979622e4671d85bcb98b6a093f0d33f`, Skill SHA-256은 `5c2f481e15e3ffd02a80a603d712b10de36d32b35a420a7188374a6440e71d14`로 일치했다.
- Plugin validator, Skill validator, Python 문법, JSON 파싱, CLI 도움말, 프로젝트 초안 검증, `git diff --check`를 확인했다. 단위 테스트와 프론트엔드 빌드는 실행하지 않았다.
