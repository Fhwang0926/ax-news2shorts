# Shorts Studio price 모드 제거

## 완료 내용

- `Shorts Studio`에서 `price` 명령과 가격 계산·근거 검증·가격 카드 렌더 경로를 제거했다.
- `shorts-price-producer` 스킬과 기본 프롬프트를 제거했다.
- 플러그인 설명과 루트 README에서 `price` 모드 소개를 제거했다.
- 기존 가격 프로젝트와 과거 완료 문서는 기록 보존을 위해 수정하거나 삭제하지 않았다.

## 검증 결과

- 플러그인 manifest JSON 검사와 Python 구문 검사를 통과했다.
- 제거 작업 시점의 단위 테스트 4건을 통과했다. 당시 지원 중인 대표 fixture의 검토본·최종본·업로드 패키지 생성도 포함한다.
- 소스와 설치본의 `doctor` 지원 모드에서 `price`가 제외된 것을 확인했다.
- 설치본에서 `price` 명령은 `invalid choice` 오류와 종료 코드 2로 실패한다.
- 설치 캐시는 `0.2.0+codex.20260826234307`만 남았고 `shorts-price-producer` 경로는 없다.

프론트엔드 빌드, DB 작업, 외부 API 호출과 YouTube 업로드는 수행하지 않는다.
