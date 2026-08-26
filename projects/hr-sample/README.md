---
type: project
status: active
goal: "인사 도메인 목업 코퍼스를 생성·유지해 vault 인제스트와 질의 기능을 실증한다."
due:
milestones:
  - name: "단일 데이터 모델 기반 3년치 코퍼스 생성 (33종, 4개 포맷)"
    due: 2026-08-26
    done: true
  - name: "문서 간 수치 정합성 자동 검증 (65 assertion)"
    due: 2026-08-26
    done: true
  - name: "raw-layout 공식 레인(repo-doc 스냅샷·screenshots) 채우기"
    due: 2026-08-26
    done: true
  - name: "pptx·docx 레인 계약 확정"
    due:
    done: false
  - name: "첫 인제스트 실행 — wiki 컴파일 결과 검증"
    due:
    done: false
next_action: "pptx·docx 레인 계약(정식화 또는 제외) 확정, 이어서 첫 인제스트 실행"
---

# hr-sample

## Status

Active. 코퍼스 생성은 완료됐고 레인 계약 확정과 인제스트 실증이 남았다.

## Purpose

vault의 인제스트 파이프라인과 질의 기능을 **실제 업무 문서에 가까운 규모와 밀도**로
검증하기 위한 목업 코퍼스. 가상 기업 「(주)나린테크」의 2024~2026년 인사 문서 33종,
4개 파일 포맷(HWPX·PDF·PPTX·DOCX)으로 구성된다.

목업이지만 아무 숫자나 넣지 않는다. 모든 수치는 `config/scripts/data.py` 하나에서
나오고, 분기 합이 연간과 맞고 등급 인원 합이 재직 인원에서 수습을 뺀 값과 맞으며,
부서별 배분·급여 연동표·연차 정책까지 문서 전체에서 일관된다. 생성된 산출물을
다시 읽어 65개 assertion으로 교차 검증했고 전부 통과했다.

## Current Context

### 코퍼스 구성 (33종)

| 유형 | 문서 | 건수 | 원본 포맷 | 레인 |
| --- | --- | --- | --- | --- |
| 규정 | 인사평가 운영지침 2024 제정(15개조)·2026 개정(18개조), 취업규칙(5장 22개조), 급여규정, 복무규정 | 5 | HWPX | H1 |
| 반기 리포트 | 인사평가 결과 리포트 2024H1 ~ 2026H1 (부서별 표·급여 연동 포함) | 5 | PDF | S2 |
| 연간 보고서 | 연간 인사운영 보고서 2024, 2025 (퇴사 사유·채용 퍼널 포함) | 2 | PDF | S2 |
| 분기 리포트 | 채용·이직 리포트 2025Q1 ~ 2026Q2 (채용 퍼널·퇴사 사유 포함) | 6 | PDF | S2 |
| 교육자료 | 신입 온보딩, 평가자 교육, 급여·상여 정책 설명회 | 3 | PPTX | P1 (계약 미정) |
| 서식·문서 | 표준근로계약서, 직무기술서 3직무(백엔드·인사담당·PM), 업무 매뉴얼(SOP) | 5 | DOCX | D1 (계약 미정) |
| 회의록 | 인사위원회 2025-03 / 2025-09 / 2026-01 / 2026-07 | 4 | MD | 변환 없음 |
| 웹 클리핑 | 강제분포, OKR, 온보딩 (가상 매체) | 3 | MD | 변환 없음 |

원본은 `raw/pdf/`·`raw/hwp/`·`raw/pptx/`·`raw/docx/`(1.2MB)에, 변환 MD는
`Clippings/`(180KB, 34건 — 템플릿 기본 샘플 1건 포함)에 있다.

### 공식 raw-layout 레인 (docs/raw-layout.md 계약)

pptx·docx가 계약에 없는 임시 레인인 것과 달리, 아래 둘은 `docs/raw-layout.md`가
**직접 규정한** 레인이다. 서브에이전트 3개를 병렬로 띄워 repo-doc 스냅샷을,
screenshots는 직접 생성해 채웠다.

| 레인 | 문서 | 건수 | 근거 |
| --- | --- | --- | --- |
| repo-doc 스냅샷 (§2) | 등급분포 검증기·OKR 확정 알리미·평가 근거기록 검색기 설계 3종 | 3 | `vault-promote.md` 패턴, capture header 완전 준수 |
| screenshots/YYYY-MM-DD/ (§3) | Slack #people-ops 대화, HR 시스템 등급분포 대시보드 | 2쌍(png+ocr.md) | `raw-layout.md` §3 |

**repo-doc 스냅샷**은 가상 내부 repo `narintech/hr-tools`(등록된 GitHub-linked
프로젝트 아님 — capture header `note`에 명시)에서 사내 인사 도구 3종의 설계 문서를
승격한 형태다. 「인사평가 운영지침」 조문(제5조·제6조·제10~13조·제15조)과
`data.py`의 실측 수치(등급 분포, OKR 확정률 5개 차수 추이)를 정확히 인용한다.
Clippings/를 거치지 않고 `raw/` 루트에 직접 들어간다 — 계약상 승격 워크플로는
클리핑 인제스트와 별도 레인이기 때문이다.

이 과정에서 서브에이전트 하나가 실제로 유용한 검증을 했다: 프롬프트에 내가
"2026H1 리포트 §2에 '3개 조직 D=0' 문구가 있다"고 잘못 지시했는데, 에이전트가
원문에 없다는 걸 확인하고 지어내지 않은 채 가상 시나리오로 명확히 분리 표기했다
(전사 집계 수치는 실제 리포트와 정확히 일치시킴).

**screenshots**는 `telegram-screenshot-digest.md` 스킬 본문이 이 vault에 없어
`.ocr.md`의 필드 구성을 다른 레인(H1/S2/P1/D1)의 frontmatter 패턴에서 유추했다
— `source_image`·`source_sha256_prefix`·`captured`·`ocr_engine`·`note`. 실제
스킬 계약과 다를 수 있다.

### 데이터 모델 — 무엇이 서로 맞물리는가

`data.py`가 정의하는 축:

- **분기별 인력 이동** (2024Q1~2026Q2, 10개 분기) — 기초·채용·퇴사·자발퇴사가 사슬로 연결
- **반기 평가 차수** (5개 차수) — 평가 대상 = 반기말 재직 − 수습 중 인원, 등급 인원 합과 일치
- **부서별 배분** (5개 본부, 최대잔여법으로 정수 배분) — 부서 합이 항상 전체와 일치
- **급여 연동표** — 등급별 인상률(S 8.0%~D 0.0%)·상여 지급률(S 200%~D 0%), 직급 5단계(L1~L5) 연봉 밴드
- **연차 정책** — 근속연수별 부여일수 (근로기준법 기반)
- **채용 퍼널** (2025Q1~2026Q2) — 지원→서류통과→면접→최종합격, 최종합격은 분기 채용 인원과 일치
- **퇴사 사유 배분** — 자발적 퇴사를 이직/개인사유/창업 3종으로 최대잔여법 배분
- **제도 연혁** — 규정 제·개정 5건의 일자·내용

### 서사 축 — 질의가 걸리는 지점

강제 분포(S10/A20/B50/C15/D5)를 2024년 도입한 뒤 5개 차수 연속 S·D 등급이 규정 비율에
미달했고, 그 대응으로 2025년 보정회의 시범 운영 → 2026년 지침 개정(보정회의 의무화,
이의신청 14일→7일, 등급 근거 동시 제공)으로 이어진다. 강제 분포 존치 여부는 아직
미결이며 2026-10 인사위원회 안건으로 남아 있다.

이 축 덕분에 다음 유형의 질의가 성립한다.

- 시계열 — "2024년과 2026년 이직률 차이는?"
- 제도 대비 — "지침 2024 제정판과 2026 개정판의 조문상 차이는?" (15개조 vs 18개조, 조번호 이동까지 부칙에 명시)
- 처우 연동 — "S등급을 받으면 연봉이 얼마나 오르나?" (급여규정 ↔ 반기 리포트 ↔ 설명회 PPTX 세 곳이 같은 표)
- 인과 추적 — "보정회의를 의무화한 근거가 뭐였나?" (회의록 3건에 걸쳐 이어짐)
- 교차 확인 — "회의록이 인용한 수치가 리포트와 맞나?"
- 부서 단위 — "플랫폼개발본부 재직 인원 추이는?"
- 긴장 관계 — 사내 규정(강제분포 유지) vs 웹 클리핑(폐지 사례)
- 채용 실무 — "백엔드 개발자 직무기술서에 명시된 연봉 범위는?" (직무기술서 ↔ 급여규정)

### 미결 사항

- **pptx·docx 레인이 계약에 없다.** `pdf2md-ingest`·`hwp2md-ingest`는 있으나 슬라이드·
  워드문서용 스킬이 없어 `raw/pptx/`·`raw/docx/`와 `source_pptx`/`source_docx`·
  `converted_by: P1`/`D1`을 기존 두 스킬 패턴에서 유추했다. 변환 MD의 frontmatter
  `note` 키에 이 사실을 남겼다. 정식화하려면 `docs/raw-layout.md`에 레인을 추가하고
  스킬을 만들어야 하고, 그럴 생각이 없으면 커밋 전에 `raw/pptx/`·`raw/docx/`와
  해당 MD 8건을 제거해야 한다.
- **screenshots `.ocr.md` 필드가 추정치다.** 실제 `telegram-screenshot-digest.md`
  스킬 본문을 확보하면 `raw/screenshots/2026-08-26/*.ocr.md` 2건의 frontmatter를
  정본 계약에 맞춰 재작성해야 할 수 있다.
- **repo-doc 스냅샷의 `narintech/hr-tools`는 등록된 프로젝트가 아니다.**
  `projects/@narintech/hr-tools/`로 실제 등록하려면 `github-project-link` 스킬
  절차를 별도로 밟아야 한다 (지금은 순수 콘텐츠 픽스처 목적으로만 존재).

## Related Wiki

- [[wiki/INDEX|Wiki Index]]

## Log

- 2026-08-26: 코퍼스 25종 1차 생성 (HWPX 3·PDF 13·PPTX 2·MD 7). 검증 38건 통과.
- 2026-08-26: 대폭 확장 — HWPX 3→5(급여규정·복무규정 신설, 기존 3종 조문 대폭 증보:
  15~18개조), PDF 13종에 부서별 표·급여 연동·채용 퍼널·퇴사 사유 추가, PPTX 2→3
  (급여·상여 정책 설명회 신설), DOCX 신규 5종(근로계약서·직무기술서 3·SOP 매뉴얼) —
  vault에 없던 4번째 원본 포맷. `data.py`에 부서 배분(최대잔여법)·급여 밴드·연차
  정책·채용 퍼널·퇴사사유 배분 추가. 검증 65건 전부 통과. `convert.py`에 docx 핸들러
  (`converted_by: D1`) 추가 — pptx와 동일하게 계약 미확정 임시 레인.
- 2026-08-26: `docs/raw-layout.md`가 공식 규정한 나머지 2개 레인(repo-doc 스냅샷·
  screenshots)을 채웠다. repo-doc 스냅샷 3종은 서브에이전트 병렬 실행으로 생산
  (가상 내부 repo `narintech/hr-tools`, capture header 완전 준수). screenshots는
  Pillow로 Slack 대화·HR 대시보드 목업 2쌍(png+ocr.md) 직접 생성. 저장소를
  `personal-knowledge` → `knowledge-sample`로 개명(GitHub rename + 로컬 디렉터리 +
  `team-settings.yaml` 좌표 갱신).
- 2026-08-26: 코퍼스를 처음 소비하는 산출물 — 2025 연간 인사운영 보고서 분석판(`outputs/`,
  md 진실원 + html 뷰, 차트 10종). 1차 리포트 17건을 재집계하면서 원문 간 불일치 3건을 찾았다:
  퇴사 사유의 분기 합 ≠ 연간 집계(각 1명), 회의록 2025-09-05의 취업규칙 조번호 off-by-one,
  2025 리포트가 인용한 급여규정 조번호가 2026 개정판 기준. 첫 건은 `data.py` 배분 지점 결정 필요.

## Outputs

| 산출물 | 내용 |
| --- | --- |
| `outputs/2025-annual-hr-report.md` | 2025년(작년) 연간 인사운영 보고서 분석판 — 진실원. 1차 리포트 17건 재집계, 원문 간 불일치 3건 기록 |
| `outputs/2025-annual-hr-report.html` | 같은 보고서의 시각화 뷰 (SVG 차트 10종·표 10종, light/dark). `.md`에서 재생성하는 뷰이며 진실원이 아니다 |
| `outputs/2026-onboarding-orientation.pptx` | 신입 온보딩 오리엔테이션 덱 12슬라이드. 교육자료(2026)·SOP·wiki 두 문서(30-60-90, 수습평가)·전환율 실측을 세션 진행용으로 재구성 |

생성 스크립트는 `config/scripts/`에 있다. 전체 재생성:

```bash
cd projects/hr-sample/config/scripts
python3 data.py          # 데이터 모델 자기 검증
python3 gen_hwpx.py      # 규정 5종
python3 gen_pdf.py       # 리포트 13종
python3 gen_pptx.py      # 교육자료 3종
python3 gen_docx.py      # 서식·문서 5종
python3 gen_md.py        # 회의록·클리핑 7종 → Clippings/ 직행
python3 convert.py       # 원문 26종 → raw/ 보존 + Clippings/ 투입
python3 verify_corpus.py # 산출물 교차 검증 (65 assertion)
```

온보딩 덱만 재생성 (Node + pptxgenjs, 다른 생성기와 다른 툴체인):

```bash
cd projects/hr-sample/config/scripts
npm install pptxgenjs
node gen_onboarding_deck.js ../../outputs/2026-onboarding-orientation.pptx
```

`gen_pdf.py`·`gen_pptx.py`·`gen_docx.py`·`convert.py`는 `reportlab`, `python-pptx`,
`python-docx`, `pymupdf4llm`, `hwp-hwpx-parser`를 필요로 한다. PDF 한글은 macOS
시스템 폰트 `AppleGothic.ttf`를 임베드한다 — reportlab 기본 한국어 CID 폰트는
가운뎃점(`·`) 글리프가 없어 텍스트 레이어에서 문자가 누락된다(실측 확인). PDF 표는
격자선(GRID)을 넣어야 `pymupdf4llm`이 표로 검출한다 — 격자선 없이 가로선만 넣으면
공백 구분 텍스트로 떨어져 md 표가 만들어지지 않는다(실측 확인).
