---
type: run-log
kind: ingest
run_date: "2026-08-26"
author: raine-lemon
summary: "hr-sample 코퍼스 37건 인제스트 — human-resources 토픽 신설, wiki 13편 생성. xlsx·pptx·docx 레인 정식화 동반."
pr:
processed: 37
new_notes: 13
updated_notes: 0
tags: [human-resources, hr-sample, ingest]
sources:
  - "raw/나린테크 인사평가 운영지침(2024 제정).md"
  - "raw/나린테크 인사평가 운영지침(2026 개정).md"
  - "raw/나린테크 취업규칙 발췌(2025 개정).md"
  - "raw/나린테크 급여규정(2026 개정).md"
  - "raw/나린테크 복무규정(2025 개정).md"
  - "raw/2024 상반기 인사평가 결과 리포트.md"
  - "raw/2024 하반기 인사평가 결과 리포트.md"
  - "raw/2025 상반기 인사평가 결과 리포트.md"
  - "raw/2025 하반기 인사평가 결과 리포트.md"
  - "raw/2026 상반기 인사평가 결과 리포트.md"
  - "raw/2024 연간 인사운영 보고서.md"
  - "raw/2025 연간 인사운영 보고서.md"
  - "raw/나린테크 인사마스터 대장(2026H1).md"
  - "raw/나린테크 채용이직 분석(2024-2026).md"
  - "raw/나린테크 급여근태 대장(2026H1).md"
  - "raw/신입 온보딩 교육자료(2026).md"
  - "raw/평가자 교육자료(2026).md"
  - "raw/2026년 급여·상여 정책 설명회.md"
  - "raw/나린테크 인사팀 업무 매뉴얼(SOP).md"
  - "raw/나린테크 표준근로계약서(템플릿).md"
  - "raw/인사위원회 회의록 2026-01-08.md"
  - "raw/인사위원회 회의록 2026-07-30.md"
  - "raw/상대평가의 종말 강제 분포를 걷어낸 3년의 기록.md"
  - "raw/OKR 도입 3년, 무엇이 남았나.md"
  - "raw/온보딩 실패의 비용 - 90일 안에 결정된다.md"
notes:
  - "[[forced-distribution|강제 분포]]"
  - "[[performance-rating-scale|평가 등급 체계]]"
  - "[[calibration-meeting|평가 보정회의]]"
  - "[[rater-error-types|평가자 오류 유형]]"
  - "[[performance-review-cycle|반기 성과평가 사이클]]"
  - "[[evaluation-appeal-process|평가 이의신청]]"
  - "[[evaluation-evidence-record|평가 근거 기록]]"
  - "[[onboarding-30-60-90|30-60-90일 온보딩 플랜]]"
  - "[[probation-evaluation|수습평가]]"
  - "[[recruitment-funnel|채용 퍼널]]"
  - "[[pay-for-performance-linkage|평가 등급과 처우의 연동]]"
  - "[[okr-performance-linkage|OKR과 성과평가 연동]]"
  - "[[voluntary-turnover-rate|자발적 이직률]]"
---

# 2026-08-26 Ingest — hr-sample 코퍼스

## Summary

`projects/hr-sample`가 생성한 가상 기업 인사 코퍼스 37건을 wiki로 컴파일했다.
`human-resources` 토픽을 신설하고 재사용 가능한 인사 개념 13편을 만들었다. 같은 실행에서
`xlsx`·`pptx`·`docx` 세 변환 레인을 정식화해 `docs/raw-layout.md` § 레인 4로 통합 기재했다.

## Details

### 처리 규모

원문 37건은 5개 포맷에서 왔다 — HWPX 규정 5건(H1), PDF 리포트 13건(S2), XLSX 워크북
3건(X1), PPTX 교육자료 3건(P1), DOCX 서식 5건(D1), 그리고 변환 없이 들어온 md 8건
(인사위원회 회의록 4·가상 웹클리핑 3·템플릿 기본 샘플 1). 원본 바이너리는
`raw/<확장자>/`에 보존되고 변환 md만 `Clippings/`를 거쳐 `raw/` 루트로 이동했다.

파일명 정규화는 2건에 적용됐다 — `상대평가의 종말?…`의 `?`(Windows 금지 문자) 제거,
`온보딩 실패의 비용 — 90일…`의 em-dash를 하이픈으로 치환.

### 배치 판정

원문 대부분은 가상 기업 「(주)나린테크」의 실행 컨텍스트지만, 그 안에 담긴 인사 제도
개념은 회사 이름을 지워도 다른 팀이 읽을 수 있다. 그래서 wiki에는 개념 층만 올리고
(강제 분포·보정회의·평가 오류 유형·이직률 지표 등), 코퍼스 자체의 구성·재현 방법은
`projects/hr-sample/README.md`에 남겼다. 회사별 수치는 wiki 본문에 실측 근거로
인용하되 개념 서술이 그 수치에 종속되지 않게 썼다.

### 레인 정식화 (동반 작업)

인제스트 전, 계약 없이 임시 코드(`P1`/`D1` + `note:` 키)로 변환해 오던 pptx·docx와
신규 xlsx를 정식 스킬로 승격했다. `xlsx2md-ingest`(X1/X2/X3), `pptx2md-ingest`(P1/P2/P3),
`docx2md-ingest`(D1/D2/D3) 세 스킬과 각 변환 스크립트를 만들고, `docs/raw-layout.md`에
5개 포맷을 묶은 § 레인 4를 신설했다. `pdf`·`hwp`도 그동안 각 스킬 §3에만 정의돼 있었고
이 문서에 레인으로 기재되지 않았던 것을 함께 정리했다.

`projects/hr-sample/config/scripts/convert.py`는 자체 변환 구현을 버리고 각 스킬의 공식
스크립트를 호출하도록 재작성했다 — 코퍼스가 문서화된 경로로 생산되게 하기 위해서다.

### 검증

- wiki 위키링크 85개 전부 해소, 끊긴 링크 0
- wiki `sources` provenance 참조 85개 전부 실제 `raw/` 파일로 해석
- 코퍼스 교차 검증 65건 통과 (`projects/hr-sample/config/scripts/verify_corpus.py`)
- `vault_verify.py` 공유 불변식 통과 (memory 크기·마커·raw append-only)

## Dropped / Issues

### 처리 중 발견해 수정한 결함 3건

1. **xlsx 백분율 100배 오류** — `x1-convert.py`가 Excel의 `0.0%`(진짜 백분율, ×100)와
   `0.0"%"`(리터럴 % 문자)를 구분하지 않아 저장값 95가 `9500.0%`로 변환됐다. 따옴표 밖
   `%`만 백분율로 판정하도록 고치고 xlsx 3건을 재변환했다. 위키 작성 서브에이전트 둘이
   독립적으로 잡아낸 결함이다.
2. **회의록 조문 번호 불일치** — 2026-01-08 회의록이 보정회의를 "신설 제7조", 이의신청을
   "제8조"로 적었으나 시행 지침의 실제 조문은 제11조·제12조다. 지침을 15개조에서
   18개조로 확장하면서 회의록을 갱신하지 않은 탓이다.
3. **append-only 위반 (자체 유발 후 원복)** — 2024년 반기 리포트의 시대착오(보정회의
   시범 도입 2025-02-20보다 앞선 차수에 "보정회의 결과" 절이 존재)를 고치려고 PDF를
   재생성했는데, 해당 PDF는 직전 커밋(`1ce26a0`)에 이미 들어가 있어 `raw/` append-only를
   위반했다. `vault_verify.py`가 이를 defect 2건으로 잡아냈고 원본을 복원했다.
   `docs/raw-layout.md` § Append-only에 따라 커밋된 `raw/` 파일 수정은 사용자 승인
   사항이므로 임의로 진행하지 않았다.

### 남은 코퍼스 모순 1건 (미수정)

2024년 상·하반기 리포트가 보정회의 결과를 보고하지만, 보정회의 시범 도입은 2025-02-20,
의무화는 2026-01-15이다. 생성기(`gen_pdf.py`)에는 시기별 서술 분기를 이미 넣어 뒀으나
적용하려면 커밋된 `raw/pdf/` 2건을 교체해야 하고 이는 승인 사항이다. 승인 시 선택지는
둘이다 — (a) append-only 예외 절차로 원본 교체 + provenance 일괄 갱신, (b) 갱신판을
새 파일로 추가(예: `…-v2.pdf`). `wiki/calibration-meeting.md`가 이 모순을
`needs-update`로 이미 표기하고 있다.

### 남은 needs-update

13편 전부 본문에 `needs-update` 표기를 포함한다. 공통 사유는 세 갈래다.

- **상관과 인과의 구분** — 등급·근속·채용채널과 이직률의 상관은 데이터에 있으나 인과를
  주장할 근거가 없다. 외부 채용시장 요인도 분리하지 못했다.
- **표본 한계** — 채널당 9~40명, D등급 13명 등 하위 그룹 표본이 작아 비율의 신뢰구간이
  넓다.
- **미검증 해석** — 이의신청 증가를 "근거 제공 시작의 효과"로 본 인사담당 해석 등,
  당사자 진술이며 독립 검증이 없다.

### 스킬 쪽 남은 과제

세 신규 스킬의 전략 라우팅 임계값(X2 1000행, P2 슬라이드당 50자, D2 유사제목 판정)은
전부 초기 추정치이며 실측 벤치마크가 없다. X3·P2·P3·D2·D3 경로는 아직 실문서로 실행된
적이 없다. 각 SKILL.md § 근거·주의에 그대로 명시했다.

`raw/screenshots/`의 `.ocr.md` 필드 구성도 `telegram-screenshot-digest.md` 스킬 본문이
이 vault에 없어 다른 레인 패턴에서 유추한 상태로 남아 있다.
