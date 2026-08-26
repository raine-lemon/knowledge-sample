# pdf2md-ingest 스킬 설계 문서
<!-- origin: lemoncloud-io/knowledge@01f358b:projects/second-brain/config/skills/pdf2md-ingest/design.md -->

- 작성: 2026-08-07
- 상태: 설계 확정 (사용자 승인 완료)
- 근거: `projects/pdf2md-bench/outputs/verdict-report.md` §5.2(밀도 라우팅 인사이트), §7(S6 추가 평가), §7.4(라우팅 권고)

## 1. 목적

PDF 문서를 vault 잉게스트 가능한 MD로 변환해 `Clippings/`에 투입하는 Claude Code 스킬.
pdf2md-bench의 판정 결과(전략별 강점 상이)를 라우팅 규칙으로 코드화한다.
wiki화는 이 스킬의 범위 밖 — 기존 vault-ingest 파이프라인이 이어받는다.

## 2. 확정된 결정사항

| 축 | 결정 | 근거 |
|---|---|---|
| 실행 주체 | 랩탑 클코 직접 (사용자 요청 시) | S6 런타임이 랩탑에 구축됨. Hermes 랩퍼는 YAGNI — 필요 시 후속 |
| 라우팅 | 밀도 측정 후 제안·사용자 확인 | S4 비용 발생 — 자동 선택보다 제안이 안전 |
| 출력 | 변환 MD → `Clippings/`, 원본 → `raw/pdf/` | 기존 잉게스트와 관심사 분리, provenance 보존 |
| 전략 라인업 | S2 / S6 / S4 (S5 하이브리드 비채택) | S5는 벤치 탈락 — 텍스트 뼈대 손상 상속 (§5.3) |

## 3. 파일 배치

```
projects/second-brain/config/skills/pdf2md-ingest/
├── SKILL.md              # 절차 본문 (클코가 읽고 실행) — 소스오브트루스
├── design.md             # 본 문서
└── scripts/
    ├── measure-density.sh   # pdftotext 페이지별 공백 제거 문자수 → 밀도 프로파일
    ├── s2-convert.py        # pymupdf4llm 랩퍼 (몇 줄)
    └── s6-ocr.mjs           # pdftoppm 150dpi → ppu-paddle-ocr → 페이지 마커 MD
```

- 클코 자동 발견용 설치(머신별 1회): `$VAULT_DIR/.claude/skills/pdf2md-ingest` →
  위 디렉토리로 **심링크** (`.claude/`는 git 미추적). 설치 명령은 SKILL.md 셋업 절에 기록.
- S6 런타임 의존성(node_modules ~303MB)은 vault 밖 `~/.cache/ppu-paddle-ocr-runtime/`에
  1회 `npm install` (`ppu-paddle-ocr@6.x` + `onnxruntime-node`). 스크립트가 `NODE_PATH`로 참조.
  vault에는 스크립트만 커밋한다.
- 전제 도구: `pdftoppm`·`pdftotext`(poppler), Python 3 + `pymupdf4llm`, Node 18+.
  셋업 절에 존재 확인 명령과 설치 안내 포함. 자동 설치는 하지 않는다.

## 4. 실행 흐름

### 4.1 공통 게이트 (변환 전)

1. **커밋 가능성 게이트**: "이 PDF는 팀 공유 vault에 커밋 가능한 문서인가?"를 사용자에게
   확인. 고객사·개인 문서면 **중단**하고 vault 밖 경로만 안내 (pdf2md-bench 데이터 취급
   규칙 상속 — 실데이터 vault 커밋 금지).
2. `VAULT_DIR` resolve (vault 규칙 순서: 명시값 > vault 구조 확인된 CWD > 사용자에게 질문.
   `~/knowledge` 조용한 fallback 금지).
3. `raw/pdf/<원본파일명>.pdf` 동명 파일 존재 시 중단·보고 (append-only 계약).

### 4.2 밀도 측정 → 전략 제안

- `measure-density.sh <pdf>`: 페이지별 텍스트 레이어 문자수(공백 제거) 출력.
- 분류: **페이지당 300자 미만 = 이미지 지배 페이지** (벤치 실측: 이미지 지배 99~287자,
  혼합 536자+).
- 제안 규칙:

| 밀도 프로파일 | 제안 | 근거 (벤치 실측) |
|---|---|---|
| 이미지 지배 페이지 없음 | S2 | 텍스트 문서 T1·T2 만점, 무료·초 단위 |
| 이미지 지배 페이지 존재 | **S6 기본**, S4 옵션 병기 | 둘 다 15/15. S6=$0·초 단위 / S4=구조·서술 우위, ~$0.045/p·수 분 |
| 텍스트 레이어 전무 (스캔) | S6 기본, S4 옵션 | 텍스트 추출 계열 원리적 불가 |

- 측정 결과(총 페이지, 이미지 지배 페이지 수·비율)와 제안 전략·예상 비용을 제시하고
  **사용자 확인 후** 변환 실행.

### 4.3 변환 실행

- **S2**: `s2-convert.py <pdf> <out.md>` — pymupdf4llm `to_markdown()`.
- **S6**: `s6-ocr.mjs <pdf> <out.md>` — 스크립트가 임시 디렉토리에 pdftoppm 150dpi 렌더 → PaddleOCR
  `v5-korean-mobile`(기본, 한글 문서) 페이지별 인식 → `<!-- page N -->` 마커로 조립.
  영문 전용 문서는 `--model v6-tiny` 옵션. 실측 기준 29p ≈ 23초, LLM 비용 $0.
  주의사항 코드화: Node API는 ArrayBuffer 입력(문자열 경로 버그), 모델 캐시
  `~/.cache/ppu-paddle-ocr`.
- **S4**: 스크립트 없음 — 클코가 pdftoppm 렌더 후 페이지 이미지를 Read로 정독하며 전사.
  SKILL.md에 전사 규칙 내장 (벤치 C2 요지): 보이는 것만 충실 전사(환각 금지), 표는 MD 표로,
  다이어그램은 라벨 + 관계(화살표·흐름) 서술, 페이지 마커 유지.

### 4.4 산출·마무리

- 원본 PDF → `raw/pdf/<원본파일명>.pdf` 복사.
- 변환 MD → `Clippings/<원본파일명>.md` (확장자만 교체 — raw/ 클리핑 파일명 관례와 동일하게
  원제목 유지). frontmatter:

```yaml
---
source_pdf: "raw/pdf/<원본파일명>.pdf"
source_sha256: "<원본 해시>"
converted_by: S2|S4|S6
converted_at: "YYYY-MM-DD"
pages: N
---
```

- 본문 첫 줄은 원제목 H1.
- 완료 보고: "Clippings 투입 완료 — 잉게스트는 vault-ingest(-claude)로 별도 실행".
  이 스킬은 wiki화·커밋·PR을 하지 않는다.

## 5. 검증 (완료 선언 전)

- 페이지 수 = `<!-- page N -->` 마커 수 일치 (S6/S4)
- MD 크기 sanity: 0바이트는 실패 처리. 페이지당 평균 100자 미만이면 (희소 텍스트 문서일 수
  있으므로) 실패가 아니라 경고 + 사용자 확인
- frontmatter 필수 키 5종 존재
- 모든 산출 경로가 `$VAULT_DIR` 아래인지

## 6. 에러 처리 (fail-closed)

- 도구 부재 → 셋업 명령 안내 후 중단. 자동 설치 금지.
- S6 런타임 미구축 → 1회 셋업 절차 안내 후 중단.
- 변환 실패 → 부분 산출물을 `Clippings/`·`raw/`에 남기지 않는다 (스크래치에서 완성 후 이동).
- 게이트 실패(커밋 불가 문서, 동명 raw 파일) → 아무것도 쓰지 않고 보고.

## 7. 범위 밖 (후속 후보)

- Hermes 랩퍼 진입점 (원격/자동화) — 필요 시 vault-ingest-claude 패턴으로 추가
- 하이브리드 재설계 ("이미지 대조 검증 후 교체" — 벤치 §5.3 교훈) — 별도 실험
- 다른 문서 유형(스캔·양식) 벤치 확장
