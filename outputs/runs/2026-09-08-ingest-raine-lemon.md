---
type: run-log
kind: ingest
run_date: "2026-09-08"
author: raine-lemon
summary: "PARA 웹 클리핑 1건 인제스트 — knowledge-management 토픽의 첫 아티클 2편 생성, 갱신 0편."
pr: 3
processed: 1
new_notes: 2
updated_notes: 0
tags: [knowledge-management, ingest]
sources:
  - "raw/PARA 체계적인 노트 정리법 PARA 하는 법, 개념, 장점, 옵시디언.md"
notes:
  - "[[para-method|PARA]]"
  - "[[purpose-based-organization|목적 기준 분류]]"
---

# 2026-09-08 Ingest — PARA 클리핑

## Summary

골든래빗 아티클 「[PARA] 체계적인 노트 정리법」 웹 클리핑 1건을 처리했다. 지금까지 비어 있던
`knowledge-management` 토픽에 첫 아티클 2편을 만들었다 — 프레임워크 노트
[[para-method|PARA]]와 그 아래 깔린 분류 원리를 떼어낸 개념 노트
[[purpose-based-organization|목적 기준 분류]]. 기존 wiki 노트 갱신은 없었다.

## Details

### 중복 게이트

클리핑의 `source:`는 `https://goldenrabbit.co.kr/articles/fp493i1ooGVoo0pkMHXc`다. `raw/`
frontmatter 전수 검사에서 goldenrabbit.co.kr 도메인은 0건이었고, 기존 raw source URL 4건
(hr-insight 2, people-ops-weekly 1, reddit 1)과도 겹치지 않는다. 신규 클리핑으로 처리했고
`-1` suffix 보존 경로는 타지 않았다.

### 파일명 정규화

원본 파일명은 이미 Web Clipper 단계에서 대괄호와 `|`가 제거된 상태로 들어왔다. 다만 `|`가
있던 자리에 연속 공백 2칸이 남아 `docs/raw-layout.md` § 파일명 정규화 3-1(연속 공백 접기)이
적용된 유일한 항목이다. smart punctuation·금지 문자·emoji는 파일명에 없었고, NFC였으며
83바이트로 120바이트 한도 안이다.

- `Clippings/PARA 체계적인 노트 정리법 PARA  하는 법, 개념, 장점, 옵시디언.md` (84 B)
- → `raw/PARA 체계적인 노트 정리법 PARA 하는 법, 개념, 장점, 옵시디언.md` (83 B)

원제목의 대괄호와 `|`는 frontmatter `title:`에 그대로 남아 있으므로 손실은 없다.

### 노트 설계 판정

원문은 한 프레임워크(PARA)를 설명하지만 그 안에 성격이 다른 두 층이 있다. 하나는 네 폴더의
정의·운영 절차라는 **구현**이고, 다른 하나는 "주제가 아니라 목적으로 나눈다"는 **원리**다.
원리 층은 PARA 없이도 성립하고 이 vault의 디렉터리 계약을 설명하는 데도 쓰이므로 별도 개념
노트로 분리했다. 프레임워크 노트는 `templates/wiki-framework.md`(Summary/Principles/
Workflow/When To Use/Related Concepts), 개념 노트는 `templates/wiki-concept.md`(Summary/
Details/Connections/Open Questions) 구조를 그대로 따랐다.

두 노트 모두 `VAULT_RULES.md` § Directory Contract와의 대응을 Connections/Related Concepts에
적었다. 이 vault의 `projects/`·`areas/`·`archive/`가 PARA와 이름·역할이 겹치되 Resource 층만
`wiki/`(정제 개념)와 `raw/`(원문 보존)로 갈라져 있다는 관찰이며, 클리핑 원문이 아니라 vault
자체 문서에 근거한 서술이다.

`status`는 둘 다 `draft`로 두었다. 분량은 stub 기준(350단어)을 넘지만 단일 출처에 기반하고
교차 검증이 없어 `complete`로 올리지 않았다.

### 검증

- `Clippings/` 비었음
- 두 노트의 `sources`는 `"raw/<정규화된 이름>.md"` 문자열이며 실제 파일로 해석됨
- 위키링크 4개(`[[para-method]]` ×2, `[[purpose-based-organization]]` ×2) 전부 해소
- alias는 `[[note-slug|Alias]]` 형식, 파이프 이스케이프 없음
- `docs/vault-ingest-log.md` 미수정 (2026-08-14 동결)

## Dropped / Issues

### 노트로 만들지 않은 것

- **세컨드 브레인 / Tiago Forte** — 원문에서 출처로만 언급되고 개념 서술이 없다. 근거 없이
  일반 지식으로 채우면 vault 규칙 위반이므로 stub도 만들지 않았다. 관련 클리핑이 더 들어오면
  그때 생성한다.
- **WIP 제한** — 프로젝트 폴더의 효용을 설명하는 한 문장으로만 등장한다. [[para-method]] 본문
  When To Use 절에 인라인으로 남겼다.

### 남은 needs-update 3건 (모두 [[para-method]]·[[purpose-based-organization]] 본문 표기)

원문이 골든래빗 출판사 아티클(《세컨드 브레인은 옵시디언》 발췌)이고 서술 전체가 저자
개인의 운영 경험에 근거한다는 점에서 파생된다.

1. **효과 실측 없음** — "가장 효율적이라고 알려진", 정리 시간·재발견 성공률 개선 등은 측정치가
   아니라 평판·경험 서술이다. 주제 분류와의 비교 실험 근거가 없다.
2. **이동 시점 주장** — "루틴을 세우면 오히려 지속하기 어렵다"는 저자 판단이며 비교 근거가 없다.
3. **시점 종속 서술** — "Tiago Forte는 PARA를 Evernote에서 쓴다"는 2024-06-10 기준이다. 현재도
   그런지 확인되지 않았다.

### 그 외

- `wiki/TOPIC_MAP.md`는 변경하지 않았다. `knowledge-management`는 이미 root topic으로 등재돼
  있고 이번 실행에서 신규 토픽이 생기지 않았다. 토픽 페이지의 아티클 목록은
  `wiki/topics/knowledge-management.md`가 갖는다.
- 실행 시작 시점에 이번 ingest와 무관한 미커밋 파일 `areas/daily/2026-08-26.md`(untracked)가
  있었다. 스테이징하지 않아 이 PR에는 포함되지 않는다.
