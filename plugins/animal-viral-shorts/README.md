# Animal Viral Shorts

TikTok과 YouTube Shorts에서 공개 지표와 실제 동물 행동이 확인된 원본을 최대 3개 비교하거나, 사용자가 제공한 URL·로컬 영상을 등록합니다. 소스와 스토리를 각각 한 번씩 사용자가 선택한 뒤 기승전결, 관찰 대상·행동 대비 카드, 장면별 비보컬 음악·효과음, 필요한 한국어 원문 번역이 있는 59.5초 이하 720x1280 로컬 MP4를 만듭니다.

## 핵심 원칙

- 공개 후보는 100만 조회와 플랫폼별 보조 도달·참여 조건을 모두 확인합니다.
- 후보마다 실제 영상의 처음부터 결말까지, 눈길을 붙드는 장면, 활용 방향과 현실적인 한계를 함께 설명합니다.
- 후보가 3개보다 적어도 기준을 낮추거나 숫자를 채우지 않습니다.
- 후보 1개와 스토리 1개를 사용자가 직접 선택하기 전에는 다음 단계로 진행하지 않습니다.
- 화면에서 확인한 행동과 타임코드가 없는 자막·결말·감정 단정은 거부합니다.
- 새 스토리는 기·승·전·결과 서로 다른 재미 장치를 갖춰야 하며, 근거 점수와 재미 점수를 별도로 통과해야 합니다.
- 유형별 길이는 가이드일 뿐이며 CTA를 포함한 최종본은 59.5초 이하에서 실제 변화 밀도에 맞춰 정합니다.
- 검토용 영상의 재미와 음악 적합성을 사용자가 모두 승인하기 전에는 최종본을 만들지 않습니다.
- 권리 불명 소스는 로컬 검토용으로만 유지하고 게시 가능으로 표시하지 않습니다.
- 원 제작자 워터마크, 동물 얼굴, 사람 얼굴을 자막 블러로 가리지 않습니다.
- 영어 원본 자막은 사람이 검토한 표시 구간에만 불투명 `원문 번역` 또는 자연스러운 `원문 의역` 카드로 덮고, 번역·의역을 관찰 근거로 사용하지 않습니다.
- 검토 상태는 프로젝트 보고서에 기록하며 영상 화면에는 별도의 로컬 초안 배지를 넣지 않습니다.
- 공개 YouTube 설명에는 제작자 핸들을 기본으로 반복하지 않으며, 출처·권리 정보는 프로젝트 파일과 영상 내 출처 표시에 보존합니다.
- 반전·행동 전환에는 원본음을 해치지 않는 짧은 비보컬 효과음만 선택적으로 넣습니다.
- 결말 뒤에는 1.8초 무음 `구독 · 좋아요` CTA 샷을 정확히 한 번 붙입니다.
- TTS, 내레이션, 보컬 음악, 실제 업로드, DB, 웹 UI, 별도 서버는 포함하지 않습니다.

## 명령 흐름

환경 확인:

    python3 scripts/animal_viral_shorts.py doctor --json

Skill이 조사한 후보를 검증:

    python3 scripts/animal_viral_shorts.py score-candidates \
      --input ./candidates.input.json \
      --output ./ranked-candidates.json \
      --top-k 3

사용자가 고른 후보로 프로젝트 생성:

    python3 scripts/animal_viral_shorts.py init \
      --project-dir outputs/animal-viral-shorts/YYYY-MM-DD/project \
      --candidates ./ranked-candidates.json \
      --candidate-id candidate-id \
      --visual-preset observation-contrast-v1

직접 제공한 URL 또는 로컬 파일도 사용할 수 있습니다.

    python3 scripts/animal_viral_shorts.py init \
      --project-dir outputs/animal-viral-shorts/YYYY-MM-DD/project \
      --source-url "https://www.youtube.com/shorts/VIDEO_ID" \
      --creator "creator" \
      --rights-status unknown

    python3 scripts/animal_viral_shorts.py init \
      --project-dir outputs/animal-viral-shorts/YYYY-MM-DD/project \
      --source-file ./authorized-source.mp4 \
      --creator "creator" \
      --rights-status permission_confirmed

이후 흐름:

    python3 scripts/animal_viral_shorts.py acquire --project-dir <project>
    python3 scripts/animal_viral_shorts.py preview --project-dir <project>
    python3 scripts/animal_viral_shorts.py observe --project-dir <project> --input ./reviewed-observations.json
    python3 scripts/animal_viral_shorts.py stories --project-dir <project> --input ./story-options.input.json

여기서 스토리 3안을 사용자에게 보여 주고 멈춥니다. 사용자가 고른 뒤:

    python3 scripts/animal_viral_shorts.py select-story --project-dir <project> --story-id story-02
    python3 scripts/animal_viral_shorts.py compose --project-dir <project>
    python3 scripts/animal_viral_shorts.py edit-plan --project-dir <project>
    python3 scripts/animal_viral_shorts.py validate --project-dir <project> --final
    python3 scripts/animal_viral_shorts.py render --project-dir <project> --draft

검토용 `outputs/preview.mp4`를 확인한 뒤 재미와 음악이 모두 자연스러우면 승인합니다.

    python3 scripts/animal_viral_shorts.py approve-draft \
      --project-dir <project> \
      --story-fit pass \
      --music-fit pass \
      --note "기승전결과 결말 음악 확인"

승인 후 최종본을 만듭니다.

    python3 scripts/animal_viral_shorts.py render --project-dir <project>
    python3 scripts/animal_viral_shorts.py upload-package --project-dir <project>

결과물은 프로젝트의 outputs/preview.mp4, draft-render-report.json, outputs/short.mp4, draft-review.json, render-report.json, delivery-note.md, edit-plan.md, youtube-upload.json, youtube-upload.md입니다. 업로드 정보에는 제목·설명·태그·썸네일·고정 댓글·설정이 포함되며, 시청자층·합성 콘텐츠·유료 프로모션·연령 제한·미확정 권리는 검토 대상으로 남습니다.

스토리 또는 음악이 어울리지 않으면 `approve-draft`에 `revise`를 기록하고 자막·음악 계획을 수정한 뒤 검토용 렌더를 다시 만듭니다.

## 렌더 템플릿

`animal-viral-card-v1`은 720x1280, 30fps, H.264/AAC 고정 골격입니다. 신규 프로젝트의 기본 화면 프리셋은 `observation-contrast-v1`입니다. 상단 고정 2줄 헤드라인, 중앙 실제 원본 영상, 하단의 짧은 관찰 대상 라벨과 실제 행동 메시지를 사용합니다. 일반 장면은 3초, 마지막 결말 장면은 프레임 고정을 포함해 4초 이내로 제한해 관찰→대비→결말 리듬을 유지합니다.

`subject_label`은 `앞쪽 병아리`처럼 검토된 관찰 대상과 연결되는 2~12자 명사구만 허용합니다. 대사, 감탄문, 추정 감정·의도는 라벨로 사용할 수 없습니다. 기는 질문, 승은 노란 누적 카드, 전은 붉은 대비, 결은 검정 카드로 강조하되 기승전결 라벨 자체는 화면에 표시하지 않습니다. 기존 프로젝트에 화면 프리셋 필드가 없으면 원래 `animal-viral-card-v1` 화면으로 렌더링됩니다.

프리셋은 참조 영상의 정보 위계와 빠른 관찰 대비 문법만 일반화합니다. 타 채널의 로고·폰트·문구·음악·장면 순서·원본 영상은 복제하지 않습니다. `--visual-preset animal-viral-card-v1`을 지정하면 신규 프로젝트에서도 기존 화면을 선택할 수 있습니다.

기본 생성 음악은 장면마다 같은 곡을 바꾸는 방식이 아니라 같은 조성과 BPM을 유지한 채 에너지와 악기 층을 조절합니다. 기는 낮게 시작하고, 승에서 리듬을 쌓고, 전에서 짧게 비우고, 결에서 임팩트 또는 해소를 줍니다. 원본 소리가 중요한 장면에서는 BGM을 더 낮추며, 효과음은 `question_pop`, `soft_whoosh`, 낮고 긴 감쇠의 `bass_drum`을 검토된 타이밍에만 생성합니다.

가로 원본은 동일 프레임의 블러 배경 위에 전체 화면을 보존하고, 세로 원본은 검토한 초점 좌표에 맞춰 크롭합니다. 마지막 장면은 검토된 실제 원본 프레임을 0.5~1초 유지합니다.

## 검증 경계

로컬 MP4가 기술 검증을 통과해도 저작권, 게시 허가, 공정 이용, 수익화, 사실성, 동물 복지 전문 판단 또는 바이럴 성과가 확인된 것은 아닙니다. 외부 게시 전에는 별도의 권리·사실·플랫폼 검토가 필요합니다.
