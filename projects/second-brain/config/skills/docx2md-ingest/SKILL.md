---
name: docx2md-ingest
description: >
  워드 문서(.docx)를 vault 잉게스트 가능한 MD로 변환해 Clippings/에 투입한다. 제목
  스타일·표·이미지 사용을 측정해 변환 전략(D1 python-docx 직행 / D2 서식 힌트 기반
  헤딩 추론 / D3 페이지 렌더 → Claude 비전 전사)을 제안하고 사용자 확인 후 실행한다.
  wiki화는 하지 않는다 — 기존 vault-ingest가 이어받는다. 커밋 불가 문서(고객사·개인)는
  vault 밖 변환 모드로 변환만 수행한다. 근거: 2026-08-26 hr-sample 코퍼스 작업
  (§ 근거·주의).
---

# docx2md-ingest (DOCX → Clippings MD)

## 언제 사용하는가

- 사용자가 "이 워드 파일 잉게스트해줘" / "docx를 vault에 넣어줘"라고 요청할 때
- .docx(OOXML) 내용을 wiki 지식으로 만들고 싶을 때

이 스킬은 **변환과 Clippings 투입까지만** 담당한다. 개념 추출·wiki 생성·커밋·PR은
하지 않는다 (기존 vault-ingest / vault-ingest-claude 몫).

**"워드를 PDF로 export해서 pdf2md-ingest를 쓰면 되지 않나"는 열등한 우회다.** docx는
구조 정보를 이미 갖고 있는데 PDF는 그것을 레이아웃으로 굽는다 — 이 스킬의 존재 이유가
그 손실이다:

- **제목 계층**: `Heading 1/2/3` 스타일이 "굵고 큰 글자"로 평탄해진다. `#`/`##`/`###`
  매핑 근거가 사라져 wiki 컴파일 단계에서 절 구조를 복원할 수 없다.
- **표 구조**: 셀 경계가 좌표로만 남아 텍스트 추출이 셀을 잘못 분할·병합한다
  (같은 문서의 hwp 원본 대비 pdf 추출에서 셀 분할 아티팩트가 실제로 관측된 적 있다 —
  `hwp2md-ingest` § 근거·주의).
- **각주·미주**: 페이지 하단 텍스트로 흘러들어가 참조-정의 관계가 끊긴다.
- **추적 변경·주석**: PDF export 시점의 상태만 남고, 원본에 그런 이력이 있었다는
  사실 자체가 소실된다. 이 스킬은 그 사실을 frontmatter `has_revisions`로 보존한다.

`.doc`(구형 바이너리)는 이 스킬의 대상이 아니다 — 워드에서 `.docx`로 다시 저장한 뒤
가져온다. HWP/HWPX는 `hwp2md-ingest`, PDF는 `pdf2md-ingest`.

## 전제 도구 (없으면 안내 후 중단 — 자동 설치 금지)

| 도구 | 확인 | 설치 안내 |
|---|---|---|
| uv (D1·D2 — python-docx 자동 준비) | `command -v uv` | `brew install uv` |
| LibreOffice (D3 렌더 전용) | `command -v soffice` | `brew install --cask libreoffice` |
| poppler (D3 — `pdftoppm`) | `command -v pdftoppm` | `brew install poppler` |

python-docx는 PEP 723 인라인 메타데이터로 uv가 실행 시점에 준비한다 (전역 설치 불필요).
워드·MS Office는 필요 없다. D3을 쓰지 않는 문서라면 uv 하나면 된다.

**스킬 발견용 설치** (머신별 1회): `$VAULT_DIR/.claude/skills/`에 심링크

```bash
mkdir -p "$VAULT_DIR/.claude/skills"
ln -s "$VAULT_DIR/projects/second-brain/config/skills/docx2md-ingest" \
      "$VAULT_DIR/.claude/skills/docx2md-ingest"
```

## 절차

### 0. 게이트 (변환 전 — 하나라도 실패하면 아무것도 쓰지 않고 보고)

1. **커밋 가능성**: 사용자에게 확인 — "이 워드 문서는 팀 공유 vault에 커밋 가능한가?"
   고객사·개인 문서면 정식 잉게스트(§3 산출·마무리)는 중단한다. 변환 자체가 필요한
   경우에는 § vault 밖 변환 모드를 제안하고, 사용자가 그 모드를 명시적으로 선택한
   경우에만 진행한다.
   **워드 문서에 특유한 위험**: 추적된 변경이력(track changes)과 주석(comments)에는
   미공개 내부 논의 — 반려 사유, 협상 여지, 특정 인물 평가, 삭제하기로 한 조항 —
   가 그대로 남아 있는 경우가 흔하다. 화면에 "최종본"으로 보여도 파일 안에는 남는다.
   §1 측정이 `has_revisions: true`를 보고하면, 그 사실과 함께 **삽입·삭제·주석의 실제
   내용을 사용자에게 보여주고** 커밋 가능성을 다시 확인한다. 이 재확인 없이는 §3으로
   가지 않는다.
2. **VAULT_DIR resolve**: 사용자 명시값 > vault 구조(`VAULT_RULES.md`, `wiki/`, `raw/`,
   `Clippings/`, `templates/`)가 확인된 현재 루트 > 그 외에는 사용자에게 질문.
   `~/knowledge` 조용한 fallback 금지. 절대경로로 resolve.
3. **중복**: `raw/docx/<원본파일명>.docx`가 이미 있으면 중단·보고 (raw/는 append-only —
   `docs/raw-layout.md` § Append-only). 파일명은 `docs/raw-layout.md` § 파일명 정규화를
   적용한 이름으로 판정·보존한다.

### 1. 구조 측정 → 전략 제안

측정은 읽기 전용·무해하므로 먼저 실행해 그 통계로 전략을 판정한다:

```bash
SKILL_DIR="$VAULT_DIR/projects/second-brain/config/skills/docx2md-ingest"
uv run "$SKILL_DIR/scripts/d1-convert.py" <file.docx> --stats
```

JSON으로 문단 수(`paragraphs`)·표 수(`tables`)·이미지 수(`images`)·본문 문자수(`chars`)·
제목 스타일 사용 여부(`has_heading_styles`, `heading_styles`)·서식만으로 만든 유사 제목
수(`pseudo_headings`)·각주/미주 수·추적 변경·주석(`revisions`, `has_revisions`)이 나온다.

전략 코드:

- **D1 — 스타일이 정돈된 문서.** `Heading 1~3` 스타일을 실제로 쓰는 문서. python-docx로
  직행해 제목 계층을 md 헤딩으로 그대로 매핑한다. 손실이 가장 적고 무료·초 단위.
- **D2 — 스타일 없이 굵기·크기로만 제목을 표현한 문서.** 헤딩을 서식 힌트(bold 전용
  런, 큰 글자 크기)로 **추론**한다. 추론이므로 결과를 사용자에게 보여주고 확인받는다.
- **D3 — 이미지·도형 위주로 텍스트 추출이 빈약한 문서.** 페이지를 렌더해 Claude가
  비전으로 전사한다. 비용이 드므로 시작 전 고지·확인 필수.

라우팅 판정표:

| 프로파일 | 판정 | 근거 |
|---|---|---|
| `has_heading_styles` = true 그리고 `chars` ≥ 300 | **D1 채택** — 산출 그대로 사용 | 제목 계층이 문서에 명시돼 있어 추론 불필요 (2026-08-26 hr-sample 5종 실측) |
| `has_heading_styles` = false, `pseudo_headings` ≥ 1, `chars` ≥ 300 | **D2 제안** — 추론 헤딩 목록을 보여주고 확인 | 서식이 유일한 제목 신호. 오탐(강조용 굵은 글씨)이 섞일 수 있어 사람 확인이 게이트 |
| `has_heading_styles` = false, `pseudo_headings` = 0, `chars` ≥ 300 | **D1 채택** — 평문 문서로 처리 | 헤딩이 없는 게 정상인 문서(계약서 본문·서신). 없는 계층을 만들어내지 않는다 |
| `chars` < 300 그리고 `images` ≥ 1 | **D3 제안** (D1 산출은 폐기) | 텍스트 추출 계열 원리적 불가. 비용 고지 후 사용자 확인 |
| `chars` < 300, `images` = 0 | 희소 텍스트 문서 가능성 — D1 산출을 보여주고 사용자 판단 | 짧은 서식·공문이 정상일 수 있음 |
| `has_revisions` = true | 전략과 별개로 **§0 게이트 1 재확인** 후 진행 | 미공개 내부 논의 유입 위험 |

측정 결과(문단·표·이미지·문자수·제목 스타일·추적 변경)와 제안·예상 비용을 사용자에게
보여주고 **확인받은 뒤** 변환한다. `chars`가 충분해도 `images` ≥ 1이고 이미지 속
텍스트·도표가 핵심이면 D3 병행을 제안한다 (D1은 이미지 **내용**을 읽지 못하고
`[IMAGE]` 마커만 남긴다).

`chars` 300 기준은 `pdf2md-ingest`의 페이지당 300자(image-dominant) 기준을 문서 단위로
차용한 초기 추정치다 — 실사용 축적 후 조정 대상 (needs-update).

### 2. 변환 (산출은 스크래치 디렉토리에 — 완성 전 vault에 쓰지 않는다)

- **D1**: `uv run "$SKILL_DIR/scripts/d1-convert.py" <file.docx> > <scratch>/converted.md`
- **D2**: 같은 스크립트로 1차 산출을 만든 뒤, `pseudo_headings`로 잡힌 문단 목록을
  사용자에게 제시해 어느 것이 실제 제목이고 몇 단계인지 확정하고, 확정된 것만 `#`/`##`/
  `###`로 승격한다. 확정 전에 임의로 승격하지 않는다 — 추론 결과를 사람이 승인하는 것이
  D2의 정의다.
- **D3** (클코 자신이 수행): 렌더 후 비전 전사.

  ```bash
  soffice --headless --convert-to pdf --outdir <scratch> <file.docx>
  pdftoppm -png -r 150 <scratch>/<name>.pdf <scratch>/pages/p
  ```

  이후 규칙은 `pdf2md-ingest` S4와 동일: 보이는 것만 충실히 전사(추측·보완·요약 금지),
  표는 MD 표로 재구성, 다이어그램은 내부 라벨을 모두 옮기고 관계를 텍스트로 서술,
  페이지마다 `<!-- page N -->` 마커, 시작 전 예상 비용(약 0.045 USD/페이지) 고지.

**변환 규칙 (D1·D2 공통) — 스크립트가 지키는 계약이자, 손으로 고칠 때의 기준:**

- **문서 순서 보존 (필수).** `doc.element.body`를 **XML 자식 순서대로** 순회해
  `w:p`(문단)와 `w:tbl`(표)을 제자리에 섞는다. `doc.paragraphs`와 `doc.tables`는 각각
  **별도의 평면 리스트**라 서로의 위치 정보를 갖고 있지 않다 — 둘을 순서대로 이어붙이면
  **표가 전부 문서 맨 끝으로 몰린다.** 2026-08-26에 실제로 이렇게 만들어 표 2개가 본문과
  분리됐고, `body.iterchildren()` 순회로 바꿔 고쳤다. 스크립트를 수정하든 새로 짜든
  이 순회 방식을 바꾸지 말 것. 회귀 확인은 §4.
- **제목**: `Heading 1~3` → `#`/`##`/`###` (4단계 이상은 `####`…, `Title` → `#`).
  본문 첫 줄이 원제목 H1이 되도록 한다 (§3).
- **목록**: `List Bullet` → `-`, `List Number` → `1.`. `List Paragraph`는 번호 서식
  판별에 numbering 파트 조회가 필요해 불릿으로 통일한다 — 원문이 번호 목록이면
  §4에서 육안 확인 후 손으로 고친다. 들여쓰기는 스타일 접미 숫자와 `w:ilvl` 중 큰 값.
  연속 목록 항목 사이에는 빈 줄을 넣지 않는다.
- **표**: md 표로 재구성. 셀 안 줄바꿈은 `<br>`, 셀 안 `|`는 이스케이프. **표 블록의 행
  사이에 빈 줄을 넣지 않는다** — 빈 줄이 끼면 md 표로 렌더되지 않는다. 가로 병합 셀은
  python-docx가 같은 셀을 반복해 돌려주므로 값이 중복 표시된다 (원문 손실 없음, 육안 확인).
- **각주·미주**: 본문에는 `[^fnN]`/`[^enN]` 참조를 남기고, 정의는 본문 끝에
  `[^fnN]: <내용>`으로 모은다. `footnotes.xml`/`endnotes.xml`의 separator 항목은 제외.
- **이미지·도형**: `[IMAGE]` 마커만 남는다 (내용은 못 읽는다 — 필요하면 D3).
- **추적 변경**: **최종본(모든 변경을 수락한 상태)을 기준**으로 읽는다. 삽입분(`w:ins`
  하위 `w:t`)은 포함되고 삭제분은 `w:delText` 태그라 자연히 빠진다. 다만 원본에 그런
  이력이 있었다는 사실은 반드시 frontmatter `has_revisions: true`로 남긴다 (§3).
  주석(comments) 본문은 산출 MD에 넣지 않는다 — §0 게이트 1에서 사람이 확인할 대상이지,
  vault에 커밋할 대상이 아니다.

### 3. 산출·마무리

1. 원본 보존: `cp <file.docx> "$VAULT_DIR/raw/docx/<원본파일명>.docx"` (디렉토리 없으면
   생성). 파일명은 `docs/raw-layout.md` § 파일명 정규화 적용.
2. frontmatter를 붙여 `Clippings/<원본파일명 확장자만 .md>`로 이동:

   ```yaml
   ---
   source_docx: "raw/docx/<원본파일명>.docx"
   source_sha256: "<shasum -a 256 결과>"
   converted_by: D1|D2|D3
   converted_at: "YYYY-MM-DD"
   paragraphs: N
   tables: N
   has_revisions: true|false   # 추적 변경·주석이 원본에 있었는지
   ---
   ```

   본문 첫 줄은 원제목 H1 (`# <문서 제목>`).
3. 완료 보고: 전략·문단/표 수·추적 변경 유무·MD 크기·경로 + "잉게스트는
   vault-ingest(-claude)로 별도 실행" 안내.

### 4. 검증 (완료 선언 전)

- frontmatter 필수 키 7종 존재 (`source_docx`·`source_sha256`·`converted_by`·
  `converted_at`·`paragraphs`·`tables`·`has_revisions`)
- **표 수 일치**: 산출 MD의 md 표 블록 수 = `--stats`의 `tables`
- **표가 문서 끝에 몰려 있지 않은지 육안 확인** (§2 문서 순서 함정의 회귀 테스트).
  각 표가 원문에서 그 표를 소개하는 제목·문장 **바로 아래**에 있는지 최소 1개는 원본과
  대조한다. 표들이 마지막 절 뒤에 연달아 붙어 있으면 순회 방식이 잘못된 것이다 —
  산출을 폐기하고 §2를 다시 한다.
- 표 블록 내부에 빈 줄이 없는지 (있으면 md 표로 렌더되지 않는다)
- MD 0바이트면 실패 처리. `chars` < 300인데 D1 산출을 채택했다면 사용자 확인을 거쳤는지
  재확인. `[IMAGE]` 마커가 있으면 그 사실을 보고에 포함
- `has_revisions: true`인데 §0 게이트 1 재확인을 거치지 않았다면 커밋 대상에서 제외
- D3 산출은 `<!-- page N -->` 마커 수 = 렌더된 페이지 수
- 모든 산출 경로가 `$VAULT_DIR` 아래인지 (vault 밖 변환 모드에서는 반대 — 아래 § 참고)

## vault 밖 변환 모드 (커밋 불가 문서용)

게이트 1(커밋 가능성) 실패 — 고객사·개인 문서, 또는 추적 변경·주석에 미공개 내부 논의가
남아 있는 문서 — 인데 변환 산출물 자체는 필요한 경우의 공식 경로. 게이트가 이 모드를
**제안**할 수는 있지만, 진입은 사용자의 명시적 선택으로만 한다 (기본값 아님). 규칙은
`pdf2md-ingest` § vault 밖 변환 모드와 동일하다:

- §0 게이트 3(중복 검사) 생략, §1·§2 동일 수행, §3은 **전부 생략** — vault 아래에
  아무것도 쓰지 않는다. §4 검증은 산출 경로가 `$VAULT_DIR` **밖**인지로 뒤집힌다.
- 산출 MD는 세션 스크래치 디렉토리 또는 사용자가 지정한 vault 밖 경로에만 둔다.
  frontmatter 부착은 선택이며, 붙이더라도 vault 밖 산출물에만 붙인다.
- 산출 MD는 파생 작업의 입력으로만 쓰고, 파생 결과물이 vault로 들어갈 때는 커밋 전에
  개인정보(연락처·이메일·주민번호·계좌·상세 주소) 미유입을 diff 기준으로 검증한다
  (`VAULT_RULES.md` § Core Rules의 개인 데이터 금지 조항). 인사·계약 문서는 이 위험이
  기본값이라고 보고 다룬다.
- 완료 보고에 모드 명칭("vault 밖 변환")과 산출 경로를 명시해, 정식 잉게스트로
  오인되지 않게 한다.

## 에러 처리 (fail-closed)

- 도구 부재 → 위 설치 안내 후 중단. 자동 설치 금지.
- `.doc`·암호화 문서 → 중단하고 사유 보고 (`.doc`는 `.docx` 재저장, 암호는 해제 후 재시도).
  python-docx는 둘 다 열지 못한다.
- D1 실패(파싱 불가·깨진 파일) → D3을 제안하되, 원인(비표준 포맷·손상)을 함께 보고.
- 변환 결과가 비었으면(`empty conversion result`) 성공으로 처리하지 않는다 — D3 검토.
- 변환 실패 → 스크래치만 정리하고 `Clippings/`·`raw/`는 건드리지 않는다.
- 게이트 실패 → 아무것도 쓰지 않고 사유 보고.

## 근거·주의 (요약)

- **신설 경위 (정직하게)**: 2026-08-26 hr-sample 코퍼스 작업 중 신설했다. 그 이전에는
  `projects/hr-sample/config/scripts/convert.py`가 `converted_by: D1`이라는 임시 코드와
  `note: "docx 레인은 스킬·raw 계약에 아직 없음 — 계약 확정 전 임시 변환"`을 달고 계약
  없이 변환해 왔다. 이 스킬이 그 임시 상태를 정식화한 것이다. 기존 산출물의 `note:` 키는
  이 스킬의 필수 키 7종에 포함되지 않는다 (신규 변환부터 적용 — 기존 파일 소급 수정은
  하지 않는다).
- **전략 라우팅 임계값은 실측 벤치마크가 아니라 초기 추정치다.** `chars` 300,
  `pseudo_headings` ≥ 1, 유사 제목 판정의 80자·14pt 기준 모두 `pdf2md-ingest`/
  `hwp2md-ingest`에서 차용하거나 추정한 값이다. D2·D3은 아직 실문서로 돌려본 적이 없다.
  코퍼스가 쌓이면 재보정한다 (needs-update).
- **문단·표 순서 함정은 실측이다.** 2026-08-26 첫 구현이 `doc.paragraphs`와 `doc.tables`를
  이어붙이는 방식이어서 표가 전부 문서 맨 끝으로 몰렸다. `doc.element.body.iterchildren()`
  순회로 수정했고, 수정본은 hr-sample 5종에서 표가 제자리에 오는 것을 확인했다
  (예: "1. 반기 평가 운영 타임라인" 제목 바로 아래에 해당 표).
- **D1 스크립트 실측 범위 (2026-08-26)**: hr-sample .docx 5종 — 제목 스타일 매핑,
  `List Bullet` 목록, md 표 2종, 문서 순서 보존 확인. 합성 문서로 `w:ins`/`w:del`
  최종본 처리(삽입 포함·삭제 제외)와 `has_revisions` 감지, 셀 안 `|` 이스케이프,
  유사 제목 탐지 1건 확인.
- **미검증 영역**: 각주·미주 수집(`footnotes.xml`/`endnotes.xml`)은 구현했으나 샘플
  문서가 없어 실문서로 검증하지 못했다 — 각주가 있는 문서를 처음 다룰 때 §4에서 참조와
  정의가 짝을 이루는지 반드시 육안 확인한다. 텍스트 상자·도형 안의 텍스트는 XML 순회가
  `[IMAGE]` 마커와 본문 텍스트를 함께 잡아 중복처럼 보일 수 있다 — 이 역시 미검증.
- 관련 계약: `docs/raw-layout.md` (§ Append-only, § 파일명 정규화),
  `pdf2md-ingest` (S4 비전 전사 규칙·vault 밖 변환 모드 정본),
  `hwp2md-ingest` (전략 코드 체계·`[IMAGE]` 마커 관행).
