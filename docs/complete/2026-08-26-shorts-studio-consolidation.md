# Shorts Studio 통합과 기존 플러그인 정리 완료

## 작업 범위

- `news2shorts`, `tiktok2shorts`, `healing2shorts`, `whiteboard-shorts`는 수정하지 않았다.
- `story2short`, `romance-drama-shorts`, `price-breakdown-shorts`의 제작 기능을 새 `shorts-studio`로 통합했다.
- `motion2d-studio`, `viral-shorts`는 기능 이전 없이 제거했다.
- 기존 프로젝트·출력·완료 문서와 `animal-viral-shorts`, `s-finder`는 보존했다.

## Shorts Studio

- 하나의 `shorts_studio.py`가 `story`, `romance`, `price` 모드를 제공한다.
- 공통 명령은 `doctor`, `init`, `approve`, `validate`, `render`, `upload-package`다.
- 공통 프로젝트 스키마는 `schema_version: 1`, 모드, 상태, 권리, 승인, 출력 정보를 기록한다.
- 승인 순서는 `assets → content → publish`이며 `unknown`·`review_required`는 검토본까지만 허용한다.
- 최종본은 게시 가능한 프로젝트·자산 권리와 `audio.provider: typecast`가 필요하다. 승인된 로컬 WAV가 없으면 기존 키체인 항목 또는 `TYPECAST_API_KEY`로 연속 음성을 생성한다.
- 검토본은 540×960, 최종본은 720×1280이며 MP4, 썸네일, SRT, 렌더 보고서, 권리 manifest, 편집 패키지와 복사용 YouTube 정보를 만든다.
- 후보 조사, 공개 URL 취득, 기존 프로젝트 가져오기, 립싱크 생성, YouTube OAuth·직접 업로드는 지원하지 않는다.

## 모드별 보존 기능

- `story`: 권리가 확인된 로컬 영상, 실제 행동 근거와 승인된 스토리보드를 캐릭터형 쇼츠로 렌더한다.
- `romance`: 승인된 2인극 대본·장면 자산을 자막과 Typecast 음성으로 렌더하고 합성 표시 승인을 검사한다.
- `price`: 제공된 가격·용량·사용량을 `Decimal`로 계산하고 회원가·쿠폰·첫 구매·적립금을 제외한 가격 카드형 쇼츠를 만든다.

## 검증 결과

- Plugin validator: 통과.
- Skill quick validator 3개: 통과.
- Python 구문, manifest JSON, CLI 도움말과 `doctor --json`: 통과.
- 표준 `unittest` 4개: 통과.
- `story`, `romance`, `price` 임시 fixture의 540×960 검토본과 720×1280·30fps H.264/AAC 최종본 렌더: 통과.
- 최종 fixture의 검은 구간 검사와 0.5초 이상 무음 검사: 통과.
- 가격 단위 환산, 배송비 포함, 쿠폰 거부, 100원 반올림: 통과.
- 권리 미확정·Typecast 미사용 최종 승인, 구형 플러그인 프로젝트 입력: 차단 확인.
- 실제 Typecast API, 외부 조사, YouTube 업로드, 프론트엔드 빌드와 DB 작업은 수행하지 않았다.

## 변경·삭제 파일

- `plugins/shorts-studio`: 통합 플러그인, 세 Skill, 공통 CLI, 테스트와 문서 추가.
- `.agents/plugins/marketplace.json`: 기존 다섯 항목 제거, `shorts-studio` 추가.
- `README.md`: 현재 플러그인 목록과 직접 업로드 미지원 경계 반영.
- `plugins/motion2d-studio`, `plugins/viral-shorts`, `plugins/romance-drama-shorts`, `plugins/price-breakdown-shorts`, `plugins/story2short`: 새 플러그인 검증 후 제거.

과거 프로젝트와 완료 문서는 기록·열람용이며 Shorts Studio에서 가져오거나 실행하지 않는다.
