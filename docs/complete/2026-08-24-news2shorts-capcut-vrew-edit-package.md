# news2shorts CapCut/Vrew 편집 호환 패키지

## 완료 일자

- 2026-08-24

## 요청

- `news2shorts` 영상 결과를 CapCut과 Vrew 등 외부 편집 프로그램에서 장면·음성·자막 단위로 다시 편집할 수 있게 한다.
- 외부 편집 호환 기능을 특정 영상이 아닌 플러그인의 공통 렌더 결과에 적용한다.

## 반영 내용

- 모든 미리보기·최종 렌더가 `edit-package/<출력명>/`을 함께 생성한다.
- 플러그인 완성본 `reference.mp4`와 뉴스 고정 텍스트를 제거한 `editable.mp4`를 분리했다.
- 인트로 전환 오프셋과 실제 렌더 장면 길이를 반영한 UTF-8 `captions.srt`를 생성한다.
- 장면별 720x1280 MP4, 48kHz PCM WAV, 투명 PNG 오버레이를 보존한다.
- `timeline.csv`에 인트로 중첩 구간, 장면 시작·종료 시각, 대사·화면 문구, 파일 경로를 기록한다.
- `edit-manifest.json`과 `metadata/`에 스토리보드·출처·권리 기록을 보존한다.
- CapCut Desktop/Web과 Vrew용 한국어 가져오기 안내를 `사용방법.txt`로 제공한다.
- 외부 편집 결과가 `storyboard.json`으로 자동 역수입되지 않는 단방향 경계를 명시했다.
- 렌더 보고서 version 3에 편집 패키지 경로·호환 대상·장면 수와 검증 결과를 기록한다.

## 변경 파일

- `plugins/news2shorts/scripts/news2shorts.py`
  - 깨끗한 장면 렌더, 장면별 음성 정규화, SRT·CSV·manifest 작성, 패키지 검사 추가.
- `plugins/news2shorts/skills/news2shorts/SKILL.md`
  - 영상 범위와 최종 전달물에 CapCut/Vrew 편집 패키지 포함.
- `plugins/news2shorts/skills/news2shorts/references/output-contract.md`
  - 편집 패키지 디렉터리와 파일 계약, 단방향 호환 경계 추가.
- `plugins/news2shorts/README.md`, `README.md`
  - 외부 편집 가져오기 방식과 결과 파일 설명 추가.
- `plugins/news2shorts/.codex-plugin/plugin.json`
  - 기존 시민 관점 훅·질문형 썸네일 설명을 보존하고 편집 호환 기능을 추가한 버전으로 갱신.

## 검증 결과

- 기존 뉴스 프로젝트의 임시 복사본에서 `--draft --no-tts --overwrite` 실제 렌더 성공.
- `reference.mp4`와 텍스트가 제거된 `editable.mp4`를 각각 프레임으로 확인.
- 7개 뉴스 장면의 MP4·WAV·PNG, CTA MP4·WAV, SRT, CSV, manifest 생성 확인.
- SRT 첫 자막이 3.15초 인트로와 0.25초 전환을 반영해 2.90초에 시작하는 것을 확인.
- 생성 패키지를 포함한 프로젝트 검증 통과.
- Typecast API 호출, 외부 편집 프로그램 UI 가져오기, YouTube 업로드, DB 작업은 수행하지 않았다.
