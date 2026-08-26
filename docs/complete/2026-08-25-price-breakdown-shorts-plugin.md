# 생활비 한컷 가격해부 Shorts 플러그인 개발 완료

## 추가 업데이트

- 플러그인만 호출하고 주제·URL·자료가 없으면 추가 질문 없이 최신 후보 최대 3개 조사를 즉시 시작하도록 Skill과 UI 기본 프롬프트를 보강했다.
- 자동화 범위는 후보 조사와 점수 비교까지이며, 프로젝트 생성·캡처·음성·렌더는 Candidate ID 선택 전까지 계속 차단한다.

## PB-02 자장면 프로젝트 진행

- 사용자가 선택한 `PB-02`를 `projects/2026-08-25-pb-02-seoul-jajangmyeon` 프로젝트로 초기화했다.
- 한국소비자원 참가격과 뉴시스 화면에서 2026년 7월 서울 자장면 1인분 평균가 7,654원을 교차 확인했다.
- 서울시 2026년 8월 4주차 시장·마트 평균과 SSG.COM 일반가 화면으로 면 대체치·춘장·돼지고기·감자·식용유 5종을 계산했다.
- 정확 합계는 3,359.18원, 화면 표시값은 `재료값만 약 3,400원`이며, 춘장 배송비 3,000원을 포함했다.
- 전체 레시피가 아닌 핵심 5종, 중식면 대신 국수 대체치, 식용유 5ml 가정임을 `fact-sheet.json`과 결론에 명시했다.
- 독자 제작 hero는 `owned`, 웹 가격 화면 11건은 `review_required`로 기록했다.
- 상태는 `candidate_selected`이며 evidence·script·visual·publish 승인은 모두 `false`로 유지했다. 사람의 웹 인용·개인정보·가격 조건 검토 전에는 다음 단계로 진행하지 않는다.
- 후속 증거 검토에서 뉴시스 캡처에 불필요한 광고·기사 사진이 포함된 점을 확인해 자장면 7,654원 문단만 보이는 `obs-menu-newsis-v2.png`로 교체하고 SHA-256·크롭 범위를 동기화했다.
- 한국소비자원·서울시·SSG 가격 화면의 상품명·용량·일반가·배송비·판매처 표시는 확인했지만, 웹 인용 권리 판단은 사람 승인 대상으로 남겼다.
- 사용자 승인 후 웹 캡처 11건의 인용 범위·개인정보 없음·가격 조건 노출 확인을 기록하고 프로젝트 상태를 `evidence_reviewed`로 전환했다. `script`·`visual`·`publish` 승인은 계속 `false`다.
- 프로젝트 `validate`와 JSON 파싱은 오류·경고 없이 통과했다. 렌더·업로드·프론트엔드 빌드·DB 작업은 수행하지 않았다.

## 요청

- 기술명 `price-breakdown-shorts`, 표시명 `생활비 한컷`의 신규 플러그인을 추가한다.
- 후보를 최대 3개까지 근거와 점수로 비교하되 자동 선택하지 않는다.
- 공개 가격 화면과 Decimal 단가 계산을 바탕으로 38~48초 가격해부 쇼츠를 만든다.
- 원본 채널 자산을 복제하지 않고 노란 고정 헤더, 가격 증거 카드, 연속 Typecast 내레이션, 절약 판단 결론을 사용한다.
- 기존 `news2shorts`, DB, 웹 UI, 실제 업로드, 상품 태그, 제휴 링크는 변경하거나 추가하지 않는다.

## 반영 내용

- 로컬 마켓플레이스에 `price-breakdown-shorts`를 등록하고 독립 플러그인·Skill·CLI를 추가했다.
- 후보 계약은 1~3개, 사용자 선택 필수, BEST 자동 선택 금지, 100점 고정 배점, 공식 메뉴 또는 메뉴 화면 두 개, 재료 판매처 두 곳 이상을 검사한다.
- g·kg·ml·L·개 단위를 기준 단위로 변환하고 `Decimal`로 일반가와 피할 수 없는 배송비를 계산한다. 회원가·첫 구매·쿠폰·적립금은 계산에서 사용하지 않는다.
- 구성품별 정확 식·금액·정규화 단가와 전체 정확 합계를 보존하고, 화면에는 가장 가까운 100원으로 반올림한 `재료값만 약 N원`을 사용한다.
- 기본 10개 장면과 41.6초 타임라인을 만들고, 2초 훅 뒤에 독자 영수증 로고·노란 헤더·주제 제목을 고정한다.
- 웹 가격 장면에는 판매처·캡처 시각·가격 조건·출처 정보를 유지하고, 개인정보나 조건을 숨기는 크롭을 차단한다.
- 검토본은 540×960, 최종본은 720×1280·30fps·H.264/AAC로 렌더한다. 검토본만 `--no-tts`를 허용하며 최종본은 Typecast 연속 음성이 없으면 중단한다.
- `candidate_selected → evidence_reviewed → script_reviewed → draft_rendered → publish_ready → rendered` 상태 순서와 evidence·script·visual·publish 승인을 강제한다.
- 웹 캡처는 기본 `review_required`이며 인용 범위·개인정보·가격 조건 검토 또는 장면의 중립 데이터 카드 교체 전에는 게시 준비를 차단한다.
- `review.mp4` 또는 `short.mp4`, `thumbnail.jpg`, `captions.srt`, 장면 PNG·클립·연속 음성·타임라인·참조 MP4 편집 패키지, 출처 포함 업로드 문구를 생성한다.
- 업로드 패키지에는 빈 제휴 링크·상품 태그와 `upload_performed=false`를 명시하며 실제 업로드를 수행하지 않는다.

## 변경 파일

- `plugins/price-breakdown-shorts/.codex-plugin/plugin.json`: 플러그인 매니페스트, 표시명, 설명과 설치 버전.
- `plugins/price-breakdown-shorts/skills/price-breakdown-shorts/`: 후보 조사·선택·승인·권리·제작 흐름을 안내하는 Skill과 계약 문서.
- `plugins/price-breakdown-shorts/scripts/price_breakdown_shorts.py`: 계산, 검증, 승인, Typecast, FFmpeg 렌더, 편집·업로드 패키지 CLI.
- `plugins/price-breakdown-shorts/tests/fixture_factory.py`: 실제 상품이나 판매처가 아닌 합성 가격 화면 fixture.
- `plugins/price-breakdown-shorts/tests/test_price_breakdown_shorts.py`: 계산·차단 규칙·상태·렌더·미디어 품질 전 과정 테스트.
- `plugins/price-breakdown-shorts/assets/brand.json`: 독자 브랜드 색상과 영수증 선형 로고 규칙.
- `plugins/price-breakdown-shorts/README.md`: 명령과 기능·비기능 경계.
- `.agents/plugins/marketplace.json`: `news2shorts-local` 마켓플레이스 항목.

## 검증 결과

- Python 문법 검사와 CLI 도움말·`doctor --json`: 통과.
- 표준 `unittest`: 4개 테스트 통과.
- 단위 환산, 배송비 포함, 쿠폰 제외, 100원 반올림, 정확 합계·가격 비율: 통과.
- 후보 3개 제한, 선택 누락, 권리 누락, 72시간 경고, 게시 준비 24시간 차단: 통과.
- 합성 fixture 전체 흐름: 540×960 검토본과 720×1280·30fps H.264/AAC 최종본 렌더 통과.
- 대표 프레임 노란 고정 헤더, `blackdetect`, 유음 합성 fixture의 `silencedetect`, FFprobe 속성 검사: 통과.
- 원본과 설치 캐시의 전체 파일 비교: 차이 없음.
- 핵심 CLI SHA-256: `e63834053bfecfc960742a053d9eb9b52f9b2c7f7a8a278bedb63f60913e99ad`로 일치.
- Skill SHA-256: `c951aab19a2e01947e7dc696d3a236d3b2c7cd66a7d7d92842fcd5240aca12ba`로 일치.
- 원본·설치 캐시 Plugin validator와 Skill validator: 통과.
- 설치 상태: `price-breakdown-shorts@news2shorts-local` `0.1.0+codex.20260825133258`, enabled.

## 외부 확인 경계

- 실제 가격 후보 조사와 실제 판매 페이지 캡처는 플러그인 실행 시 공개 화면에서 수행한다. 이번 테스트는 합성 fixture만 사용했다.
- 현재 Codex 환경에서 Typecast 키가 확인되지 않아 실제 Typecast 요청은 수행하지 않았다. 최종 렌더 경로는 테스트용 연속 유음 WAV로 검증했으며 제품 코드의 로컬 TTS 자동 대체는 허용하지 않는다.
- 공정 이용과 웹 캡처 게시 가능 여부는 사안별 사람 검토가 필요하며 출처 표시만으로 권리가 확보되지는 않는다.
- 실제 업로드·상품 링크·제휴·상품 태그, 프론트엔드 빌드, DB 작업은 수행하지 않았다.
