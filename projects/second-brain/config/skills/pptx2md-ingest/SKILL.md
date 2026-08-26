---
name: pptx2md-ingest
description: >
  PPTX(파워포인트)를 vault 잉게스트 가능한 MD로 변환해 Clippings/에 투입한다. 슬라이드
  구조(슬라이드 수·슬라이드당 텍스트량·도형 구성·발표자 노트)를 측정해 변환 전략
  (P1 python-pptx 직행 / P2 슬라이드 렌더 → Claude 비전 전사 / P3 혼합)을 제안하고
  사용자 확인 후 실행한다. 슬라이드 경계·발표자 노트·표를 보존한다. wiki화는 하지
  않는다 — 기존 vault-ingest가 이어받는다. 커밋 불가 문서(고객사·개인)는 vault 밖
  변환 모드로 변환만 수행한다. 근거: 2026-08-26 hr-sample 코퍼스 변환 (§ 근거·주의).
---

# pptx2md-ingest (PPTX → Clippings MD)

## 언제 사용하는가

- 사용자가 "이 ppt 잉게스트해줘" / "발표자료를 vault에 넣어줘"라고 요청할 때
- .pptx(OOXML 프레젠테이션) 내용을 wiki 지식으로 만들고 싶을 때

이 스킬은 **변환과 Clippings 투입까지만** 담당한다. 개념 추출·wiki 생성·커밋·PR은
하지 않는다 (기존 vault-ingest / vault-ingest-claude 몫).

**PDF로 export해서 `pdf2md-ingest`로 우회하지 않는다.** 그 경로는 원리적으로 열등하다:

- **슬라이드 경계가 깨진다** — 빌드(애니메이션 단계)가 있으면 한 슬라이드가 여러 페이지로
  찢어지고, 핸드아웃 레이아웃으로 내보내면 여러 슬라이드가 한 페이지에 묶인다. 어느 쪽이든
  `<!-- slide N -->` 번호가 원본 슬라이드 번호와 어긋난다.
- **발표자 노트가 사라진다** — 기본 export에 노트는 포함되지 않는다. 노트 포함 레이아웃으로
  내보내면 이번엔 본문 레이아웃이 또 달라진다. 노트는 슬라이드 본문보다 서술이 풍부한 경우가
  많아 잉게스트 가치가 큰 층이다.
- **도형·SmartArt 텍스트가 뭉개진다** — export 시점에 렌더된 그림이 되거나, 텍스트로 남더라도
  텍스트 추출 계열은 좌표 순서로 읽어 도형의 논리적 순서(제목 → 불릿 → 캡션)를 잃는다.
  불릿 level(1단/2단)도 들여쓰기 정보와 함께 사라진다.

.pptx는 OOXML이라 슬라이드·제목 자리표시자·불릿 level·표 셀·발표자 노트를 **원본 구조 그대로**
읽을 수 있다. "ppt를 pdf로 출력해서" 우회할 필요가 없다는 것이 이 스킬의 존재 이유다.

## 전제 도구 (없으면 안내 후 중단 — 자동 설치 금지)

| 도구 | 확인 | 설치 안내 |
|---|---|---|
| uv (P1 — python-pptx 자동 준비) | `command -v uv` | `brew install uv` |
| LibreOffice `soffice` (P2·P3 슬라이드 렌더) | `command -v soffice` | `brew install --cask libreoffice` |
| poppler `pdftoppm` (P2·P3 렌더 2단계) | `command -v pdftoppm` | `brew install poppler` |

P1만 쓸 거면 uv 하나로 충분하다 — PowerPoint·Keynote는 필요 없다. LibreOffice·poppler는
비전 전사(P2·P3)로 갈 때만 확인한다.

**스킬 발견용 설치** (머신별 1회): `$VAULT_DIR/.claude/skills/`에 심링크

```bash
mkdir -p "$VAULT_DIR/.claude/skills"
ln -s "$VAULT_DIR/projects/second-brain/config/skills/pptx2md-ingest" \
      "$VAULT_DIR/.claude/skills/pptx2md-ingest"
```

## 절차

### 0. 게이트 (변환 전 — 하나라도 실패하면 아무것도 쓰지 않고 보고)

1. **커밋 가능성**: 사용자에게 확인 — "이 발표자료는 팀 공유 vault에 커밋 가능한 문서인가?"
   고객사·개인 문서면 정식 잉게스트(§3 산출·마무리)는 중단한다. 변환 자체가 필요한
   경우에는 § vault 밖 변환 모드를 제안하고, 사용자가 그 모드를 명시적으로 선택한
   경우에만 진행한다. (사내 교육자료는 슬라이드 본문보다 **발표자 노트**에 개인·인사
   맥락이 남아 있는 경우가 있으니, 노트가 있으면 그 사실을 함께 알린다.)
2. **VAULT_DIR resolve**: 사용자 명시값 > vault 구조(`VAULT_RULES.md`, `wiki/`, `raw/`,
   `Clippings/`, `templates/`)가 확인된 현재 루트 > 그 외에는 사용자에게 질문.
   `~/knowledge` 조용한 fallback 금지. 절대경로로 resolve.
3. **중복**: `raw/pptx/<원본파일명>.pptx`가 이미 있으면 중단·보고 (raw/는 append-only —
   `docs/raw-layout.md` § Append-only).

### 1. 구조 측정 → 전략 제안

P1 추출은 저비용·무해(읽기 전용)이므로 먼저 통계만 뽑아 전략을 판정한다:

```bash
SKILL_DIR="$VAULT_DIR/projects/second-brain/config/skills/pptx2md-ingest"
uv run "$SKILL_DIR/scripts/p1-convert.py" <file.pptx> --stats
```

JSON 키: `slides`(슬라이드 수) · `notes`(발표자 노트가 있는 슬라이드 수) ·
`images`(전사 불가 이미지·차트 도형 수) · `tables` · `charts` ·
`chars`(공백 제외 총 문자수) · `chars_per_slide` · `sparse_slides`(공백 제외 50자 미만
슬라이드 수) · `sparse_slide_numbers`(그 슬라이드 번호 — P3 대상 목록).

| 프로파일 | 제안 | 근거 |
|---|---|---|
| `sparse_slides` = 0 (전 슬라이드 50자 이상) | **P1 채택** — 산출 그대로 사용 | 텍스트 프레임 위주. 제목·불릿 level·표·노트가 구조 그대로 나온다 (2026-08-26 hr-sample 3종 실측: 113~160자/슬라이드) |
| `chars_per_slide` < 50 (사실상 전 슬라이드 희소) | **P2 제안** — 이미지·다이어그램 위주. 비용 고지 후 사용자 확인 | 텍스트 추출 계열 원리적 불가 |
| `sparse_slides` ≥ 1 이지만 `chars_per_slide` ≥ 50 | **P3 제안** — P1 산출 + `sparse_slide_numbers` 슬라이드만 비전 전사로 보완 | 표지·간지·도해 몇 장만 희소한 경우가 흔하다. 전면 P2는 과비용 |
| `images` ≥ 1 인데 텍스트는 충분 | P1 채택하되 `[IMAGE: ...]` 마커 위치를 함께 보고 | 이미지 **내용**은 P1이 못 읽는다. 그림 속 정보가 핵심이면 해당 슬라이드만 P3 병행 |
| 파일 열기 실패·`slides` = 0 | 중단 — 손상·암호화·`.ppt` 여부 확인 안내 | § 에러 처리 |

측정 결과(슬라이드 수·슬라이드당 문자수·노트/표/이미지 수)와 제안·예상 비용을 사용자에게
보여주고 **확인받은 뒤** 변환한다. 노트가 있으면(`notes` ≥ 1) 노트도 함께 보존된다는 점을
명시한다 — 게이트 1의 판단이 바뀔 수 있다.

### 2. 변환 (산출은 스크래치 디렉토리에 — 완성 전 vault에 쓰지 않는다)

- **P1**: `uv run "$SKILL_DIR/scripts/p1-convert.py" <file.pptx> > <scratch>/converted.md`
  (PEP 723 메타데이터로 uv가 python-pptx를 자동 준비. stdout으로 MD를 낸다.)

  스크립트가 지키는 산출 규칙 — P2·P3의 손 전사도 **같은 규칙을 따른다**:

  - 슬라이드마다 `<!-- slide N -->` 마커 (N은 원본 슬라이드 번호, 1부터 연속)
  - 제목 도형(title 자리표시자, 없으면 첫 텍스트 도형의 첫 줄)은 `## `. 제목 도형의
    나머지 줄은 부제로 `_기울임_`
  - 불릿 계층은 `-` / `  -` — 단락 level과 불릿 글리프(`•`=1단, `–`=2단) 중 깊은 쪽을 쓴다
  - **발표자 노트는 `> 발표자 노트:` 인용 블록**으로 슬라이드 블록 끝에 붙인다
  - 표 도형은 md 표 (첫 행을 헤더로, 셀 안 `|`는 이스케이프, 줄바꿈은 `<br>`)
  - 그룹 도형은 재귀 순회하고, SmartArt는 `mc:AlternateContent` 폴백 드로잉에서 텍스트를
    수집한다 (중복 제거). 도형이 갈려 끊긴 인접 불릿 묶음은 하나로 합친다
  - 전사 불가한 그림·차트는 `[IMAGE: 도형이름]` / `[CHART: 도형이름]` 마커로 남긴다
  - 첫 줄은 1번 슬라이드 첫 텍스트 줄에서 뽑은 원제목 H1 (§3에서 다시 붙이지 말 것)

- **P2** (클코 자신이 수행): 슬라이드를 이미지로 렌더한 뒤 순서대로 Read로 정독하며 전사한다.

  ```bash
  soffice --headless --convert-to pdf --outdir <scratch> <file.pptx>
  pdftoppm -png -r 150 <scratch>/<원본파일명>.pdf <scratch>/slides/s
  ```

  전사 규칙은 pdf2md-ingest S4와 동일하다:

  - 보이는 것만 충실히 전사 — 추측·보완·요약 금지 (환각 방지)
  - 표는 MD 표로 재구성
  - 다이어그램·그림은 내부 라벨을 모두 옮기고, 화살표·흐름 등 관계를 텍스트로 서술
  - 슬라이드마다 `<!-- slide N -->` 마커
  - 시작 전 예상 비용(약 0.045 USD/슬라이드)을 사용자에게 고지

  렌더 이미지에는 **발표자 노트가 나오지 않는다.** `notes` ≥ 1이면 P1을 함께 돌려
  노트 인용 블록만 해당 슬라이드에 병합한다. 폰트 치환으로 원본과 서체가 달라 보일 수
  있으나 전사 대상은 텍스트이므로 허용한다 — 글자가 깨져(두부·물음표) 읽히지 않으면
  중단·보고한다.

- **P3** (혼합): P1 산출을 뼈대로 두고, `sparse_slide_numbers`의 슬라이드만 P2 방식으로
  렌더·전사해 해당 `<!-- slide N -->` 블록의 내용을 교체한다. 비용은 대상 슬라이드 수
  × 약 0.045 USD로 고지한다. 병합 후 마커 번호가 1..N 연속인지 반드시 재확인한다(§4).

### 3. 산출·마무리

1. 원본 보존: `cp <file.pptx> "$VAULT_DIR/raw/pptx/<원본파일명>.pptx"` (디렉토리 없으면
   생성). 원본 파일명에 크로스 플랫폼 금지 문자나 smart punctuation이 있으면
   `docs/raw-layout.md` § 파일명 정규화를 적용하고, provenance는 정규화된 이름으로 적는다.
2. frontmatter를 붙여 `Clippings/<원본파일명 확장자만 .md>`로 이동:

   ```yaml
   ---
   source_pptx: "raw/pptx/<원본파일명>.pptx"
   source_sha256: "<shasum -a 256 결과>"
   converted_by: P1|P2|P3
   converted_at: "YYYY-MM-DD"
   slides: N
   notes: N          # 발표자 노트가 있는 슬라이드 수
   images: N         # 텍스트로 옮기지 못한 이미지 도형 수
   ---
   ```

   `slides`·`notes`·`images`는 §1의 `--stats` 값을 그대로 쓴다. P2·P3로 이미지 내용을
   전사했다면 그만큼 `images`를 줄인다(전사된 도형은 더 이상 "옮기지 못한" 것이 아니다).
   본문 첫 줄은 원제목 H1 (`# <문서 제목>`) — P1 산출에는 이미 들어 있다.
3. 완료 보고: 전략·슬라이드 수·노트/표/이미지 수·MD 크기·경로 + "잉게스트는
   vault-ingest(-claude)로 별도 실행" 안내.

### 4. 검증 (완료 선언 전)

- `grep -c '<!-- slide '` 결과 = frontmatter `slides` = `--stats`의 `slides`
- 마커 번호가 1..N **연속**인지 (P3 병합에서 중복·누락이 생기기 쉽다)
- frontmatter 필수 키 7종 존재 (`source_pptx`·`source_sha256`·`converted_by`·
  `converted_at`·`slides`·`notes`·`images`)
- MD 0바이트면 실패 처리. `chars_per_slide` < 50인데 P1 산출을 채택했다면 경고 + 사용자
  확인 (표지·목차만 있는 짧은 덱이 정상일 수 있다 — 확인 없이 완료 선언 금지)
- `notes` ≥ 1이면 `> 발표자 노트:` 블록 수 = `notes`
- 모든 산출 경로가 `$VAULT_DIR` 아래인지 (vault 밖 변환 모드에서는 반대 — 아래 § 참고)

## vault 밖 변환 모드 (커밋 불가 문서용)

게이트 1(커밋 가능성) 실패 — 고객사·개인 문서 — 인데 변환 산출물 자체는 필요한 경우의
공식 경로. 게이트가 이 모드를 **제안**할 수는 있지만, 진입은 사용자의 명시적 선택으로만
한다 (기본값 아님). 규칙은 `pdf2md-ingest` § vault 밖 변환 모드와 동일하다:

- §0 게이트 3(중복 검사) 생략, §1·§2 동일 수행, §3은 **전부 생략** — vault 아래에
  아무것도 쓰지 않는다. §4 검증은 산출 경로가 `$VAULT_DIR` **밖**인지로 뒤집힌다.
- 산출 MD는 파생 작업의 입력으로만 쓰고, 파생 결과물이 vault로 들어갈 때는 커밋 전에
  개인정보(연락처·이메일·사업자번호·상세 주소) 미유입을 diff 기준으로 검증한다.
  발표자 노트가 특히 위험 층이다 — 노트 블록은 별도로 훑는다.
- 완료 보고에 모드 명칭("vault 밖 변환")과 산출 경로를 명시한다.

## 에러 처리 (fail-closed)

- 도구 부재 → 위 설치 안내 후 중단. 자동 설치 금지.
- **`.ppt`(97-2003 바이너리)** → python-pptx는 읽지 못한다. `soffice --convert-to pptx`로
  선변환이 필요하다는 사실과 명령을 안내하고 **중단**한다. 자동 변환하지 않는다 —
  raw/에 원본(.ppt)을 보존할지 변환본(.pptx)을 보존할지는 사용자 결정 사항이다.
- 암호화·손상 파일로 열기 실패 → 원인을 그대로 보고하고 중단 (P2도 soffice 렌더가
  같은 이유로 실패한다).
- P1이 열리긴 하는데 `chars` = 0 → 스크립트가 실패 종료한다. P2를 제안하되 비용 고지 후
  사용자 확인.
- 변환 실패 → 스크래치만 정리하고 `Clippings/`·`raw/`는 건드리지 않는다.
- 게이트 실패 → 아무것도 쓰지 않고 사유 보고.

## 근거·주의 (요약)

- **신설 경위**: 2026-08-26 hr-sample 코퍼스 작업 중 신설. 그 이전에는 `converted_by: P1`
  임시 코드로 계약 없이 변환해 왔고(해당 산출물의 frontmatter `note` 키 참조), 이 스킬이
  그 상태를 정식화한다. 임시 산출물에 있던 `note: "pptx 레인은 스킬·raw 계약에 아직 없음"`
  키는 이 스킬 확정 이후 신규 변환에는 붙이지 않는다 (기존 파일은 소급 수정하지 않는다).
- **P1 실측 범위**: 2026-08-26 hr-sample 3종(9·10·10 슬라이드, 전부 텍스트박스) 변환 —
  마커 수 = 슬라이드 수, 113~160자/슬라이드, 제목·2단 불릿 계층 보존 확인. 발표자 노트·표·
  그룹 도형·SmartArt 폴백·그림 마커 경로는 같은 날 **합성 픽스처(5슬라이드)**로만 확인했다.
  실문서 검증은 아직 없다.
- **P2·P3는 미실측**: `soffice → pdftoppm` 렌더 경로와 비전 전사 병합은 아직 실행 검증하지
  않았다. 첫 사용 시 렌더 산출 페이지 수 = 슬라이드 수인지부터 확인하고, 결과를 이 절에
  기록한다 (needs-update).
- **임계값은 추정치**: 슬라이드당 50자 기준은 실측 벤치마크가 아니라 pdf2md-ingest의
  페이지당 300자(image-dominant) 기준을 슬라이드 정보 밀도에 맞춰 낮춘 초기 추정치다.
  라우팅 표 전체가 같은 성격 — 실사용 축적 후 조정 대상.
- **이미지 내용은 P1이 못 읽는다** (`[IMAGE: ...]`는 도형 이름만 남긴다). 차트도 마찬가지로
  계열 데이터가 아니라 `[CHART: ...]` 마커만 남는다.
- 관련: PDF는 `pdf2md-ingest`, 한글 문서는 `hwp2md-ingest`. 다른 포맷도 같은 형태의
  스킬로 정식화하는 중이니 `config/skills/` 목록을 먼저 확인한다 — 스킬이 없는 포맷은
  `projects/hr-sample/config/scripts/convert.py`가 임시 코드로 변환하고 있을 수 있다.
