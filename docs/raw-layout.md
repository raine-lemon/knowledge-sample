# raw/ 보존소 계약
<!-- origin: lemoncloud-io/knowledge@01f358b:docs/raw-layout.md -->

`raw/`의 상세 계약. `VAULT_RULES.md` § Directory Contract의 한 줄("Processed source
originals. Append-only")을 이 문서가 구체화한다. 배경과 실측 근거:
`outputs/2026-08-14-raw-folder-organization.md`.

## 레인

raw/는 유입 경로가 다른 4개 레인을 담는다.

### 1. 웹 클리핑 (루트 `*.md`)

- 유입: Obsidian Web Clipper → `Clippings/` → ingest가 이동
  (`projects/second-brain/config/skills/vault-ingest-claude.md`).
- frontmatter: clipper 표준 7키 — `title`, `source`(URL), `author`, `created`,
  `published`, `description`, `tags`.
- 파일명: 이동 시점에 정규화한다 — § 파일명 정규화.

### 2. repo-doc 스냅샷 (루트 `<project>-<doc-slug>-<short-commit>.md`)

- 유입: 팀/개인 repo 문서의 특정 commit 시점 원문 캡처. 주 생산자는 승격 워크플로 —
  `projects/second-brain/config/skills/vault-promote.md` (2026-08-14 명문화).
- 정본이 repo 문서가 아니라 개인 KB 증류 노트면 `source:`에
  `"개인 KB 증류 노트 <slug> (근거: <org/repo>@<commit>)"`으로 적는다
  (레인 README의 `canonical: kb-distilled`와 짝).
- 예외는 하나 — 원문 자체를 복제할 수 없을 때(코드·개인 데이터·라이선스)만 스냅샷 없이 개념을
  올린다. 비공개 저장소는 사유가 아니다(사본이지 링크가 아니다). 조건·검증 대체는
  `vault-promote.md` § 원문 복제 불가 델타.
- capture header 의무 (2026-08-14부터, 기존 파일 소급 없음):

  ```yaml
  ---
  title: "<사람이 읽는 제목>"
  source: "<org/repo> — <repo 내 경로>"
  commit: "<short-hash>"
  branch: "<branch>"
  captured: YYYY-MM-DD
  author: <캡처한 사람>
  note: "<캡처 맥락. 본문 무수정 명시>"
  ---
  ```

- capture header는 캡처 **시점에** 붙이는 메타데이터이고, 본문은 원문 그대로 둔다.
  이미 raw/에 들어간 파일에 header를 소급 추가하는 것은 append-only 위반이다 —
  메타데이터 보충은 색인(`docs/raw-index.md`)이 맡는다.

### 3. `screenshots/YYYY-MM-DD/`

- 계약 소유:
  `projects/auto-digest-screenshot-via-telegram/config/skills/telegram-screenshot-digest.md`.
- `<slug>-<short-hash>.<ext>` + 짝 `.ocr.md`, append-only.

### 4. 변환 원본 (`<확장자>/` 하위 디렉터리)

바이너리 문서를 MD로 변환할 때 **원본 파일 자체**를 보존하는 레인. 변환 산출 MD는
`Clippings/`로 들어가 1번 레인(웹 클리핑)과 같은 경로로 처리되고, 이 레인에는
원본만 남는다. 변환은 손실이 있으므로(표 구조·서식·이미지) 원본이 최종 근거다.

| 하위 디렉터리 | 확장자 | 담당 스킬 | 전략 코드 |
| --- | --- | --- | --- |
| `pdf/` | `.pdf` | `pdf2md-ingest` | S2 / S4 / S6 |
| `hwp/` | `.hwp` `.hwpx` | `hwp2md-ingest` | H1 / H3 |
| `xlsx/` | `.xlsx` `.xlsm` | `xlsx2md-ingest` | X1 / X2 / X3 |
| `pptx/` | `.pptx` | `pptx2md-ingest` | P1 / P2 / P3 |
| `docx/` | `.docx` | `docx2md-ingest` | D1 / D2 / D3 |

- 파일명: **원본 파일명 그대로** 유지한다. 변환 MD가 `Clippings/`를 거쳐 1번 레인으로
  이동할 때 § 파일명 정규화가 적용되지만, 이 레인의 원본은 provenance 문자열
  (`source_pdf:` 등)이 정확히 가리켜야 하므로 정규화하지 않는다.
- 중복 게이트: 같은 경로에 파일이 이미 있으면 변환을 중단하고 보고한다(append-only).
- 변환 MD의 frontmatter는 각 스킬 § 3이 규정한 필수 키를 갖는다. 공통 4키는
  `source_<ext>`(이 레인의 상대경로), `source_sha256`, `converted_by`(전략 코드),
  `converted_at`. 나머지는 포맷별로 다르다(pdf `pages`, xlsx `sheets`·`rows`·
  `truncated`, pptx `slides`·`notes`·`images`, docx `paragraphs`·`tables`·
  `has_revisions`, hwp `tables`·`images`).
- 이력: `pdf/`·`hwp/`는 2026-08 각 스킬 § 3에만 정의돼 있었고 이 문서에 레인으로
  기재되지 않았다. 2026-08-26 `xlsx`·`pptx`·`docx` 3종을 추가하면서 5개를 하나의
  레인으로 통합 기재했다. 기존 파일의 배치·명명은 바뀌지 않는다.

## Append-only의 정의

- **내용 수정 금지, rename 금지, 삭제 금지.** 셋 다 append-only 위반이다.
- provenance(`"raw/<file>.md"` 문자열)가 정확한 경로 매칭에 의존하므로, rename은 조용한
  링크 부패를 만든다 (이력상 실제 발생: 2026-07-20 rename 1건, 2026-07-03 삭제 1건 —
  계약 확립 전).
- rename이 불가피하면(예: 개인정보가 노출된 파일명, 크로스 플랫폼 비호환 파일명):
  **사용자 승인** 후, 참조하는 모든 provenance 문자열을 같은 커밋에서 일괄 수정하고,
  사유를 run-log 노트로 남긴다
  (`outputs/runs/`, `kind: maintenance` — `templates/run-log.md`).
- 적용 이력: 2026-08-19 `?` 포함 파일명 2건 rename (Windows 클론/체크아웃 장애 실측,
  사용자 요청) — `outputs/runs/2026-08-19-maintenance-steve-lemon.md`.

## 파일명 정규화 (Clippings → raw 이동 시점)

원제목은 frontmatter `title:`에 남으므로 파일명은 안정성을 우선한다. 이동 시점에
파일명만 바꾼다(내용 무수정):

1. smart punctuation을 ASCII로 치환: `’‘` → `'`, `“”` → `'`, `—`·`–` → `-`, `…` → `...`
   (곧은 큰따옴표 `"`는 Windows 금지 문자라 치환 결과로 만들지 않는다 — 2026-08-19 수정)
2. **크로스 플랫폼 금지 문자 제거** (2026-08-19 추가, Windows 장애 실측 후):
   `< > : " / \ | ? *` 와 제어문자(U+0000–U+001F)를 제거한다. Windows 예약어
   (`CON`, `PRN`, `AUX`, `NUL`, `COM1`–`COM9`, `LPT1`–`LPT9`)와 확장자 앞 이름이
   **대소문자 무시**로 일치하면 `-note`를 붙인다.
3. emoji 제거
3-1. 치환·제거(1–3)를 모두 마친 뒤 연속 공백을 하나로 접고, 끝의 `.`·공백을
   제거한다 (2·3단계 어느 쪽이 만든 공백이든 여기서 정리된다 — 2026-08-19 실증에서
   적용 시점 모호로 명확화)
4. `.md` 포함 120바이트 초과 시 단어 경계에서 절단
5. 동명 충돌 시 `-1`, `-2` suffix (기존 규칙, `vault-ingest.md`)
6. 한글 파일명은 NFC로 저장 (현재 전 파일 NFC — 유지)

provenance는 정규화된 이름으로 기록한다. 기존 파일은 소급 rename하지 않는다
(§ Append-only).

## ingest 게이트

`vault-ingest-claude`/`vault-ingest`가 클리핑 처리 시 적용한다.

- **URL 중복 게이트**: 신규 클리핑의 `source:` URL이 기존 raw frontmatter에 이미 있으면
  새 wiki 노트를 만들지 않고 기존 노트를 갱신한다. 원문은 그래도 `-1` suffix로 raw/에
  보존한다 (재클리핑도 이력이다).
- **파일명 정규화 게이트**: § 파일명 정규화를 적용한 이름으로 이동한다.

## 색인

`docs/raw-index.md`가 raw 루트 파일별 유입일·source·파생 노트 역링크를 담는다.

- 재생성: vault 루트에서
  `python3 projects/second-brain/config/scripts/generate_raw_index.py`
- `vault-lint` 패스가 재생성한다. **수동 편집 금지.**
- 색인이 raw/ 밖에 있는 이유: raw/ 안의 index는 매 ingest마다 편집이 필요해
  append-only와 충돌한다.
- 오펀(참조 0건)·source URL 중복이 발견되면 색인 상단에 표시된다 — lint 리포트로
  올린다.

## 하지 않기로 한 것 (2026-08-14 결정)

- **기존 파일 소급 rename/슬러그화** — 참조 무결 상태에서 실익이 링크 부패 위험보다
  작다.
- **서브폴더 재구조화**(`raw/YYYY-MM/` 등) — flat 구조가 아직 감당된다. **루트 200건
  도달 시** 신규분부터 재검토한다 (파일 수는 색인 상단에 표시).
