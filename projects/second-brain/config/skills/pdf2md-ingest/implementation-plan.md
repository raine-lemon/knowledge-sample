# pdf2md-ingest 스킬 구현 플랜
<!-- origin: lemoncloud-io/knowledge@01f358b:projects/second-brain/config/skills/pdf2md-ingest/implementation-plan.md -->

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** PDF를 밀도 라우팅(S2/S6/S4)으로 MD 변환해 `Clippings/`에 투입하는 클코 스킬 완성 (설계: 같은 디렉토리 `design.md`).

**Architecture:** 스크립트 3개(밀도 측정 sh / S2 py / S6 mjs) + SKILL.md 절차 문서. S6 런타임 의존성은 vault 밖 `~/.cache/ppu-paddle-ocr-runtime/`, 실행 시 스크립트를 런타임 디렉토리로 복사해 bare import가 그 node_modules를 보게 한다. E2E는 임시 샌드박스 vault에서 합성 PDF로 검증.

**Tech Stack:** bash + poppler(pdftotext/pdftoppm/pdfinfo), Python 3 + pymupdf4llm, Node 18+ + ppu-paddle-ocr@6.x + onnxruntime-node.

## Global Constraints

- 스킬 런타임은 자동 설치 금지 — 도구 부재 시 셋업 명령 안내 후 중단 (design §6).
- fail-closed: 부분 산출물을 `Clippings/`·`raw/`에 남기지 않는다 (design §6).
- 고객사 벤치 PDF(`~/Downloads/베스핀글로벌_청리움_STEP1_구축방향_2026.06.23.pdf`)는 **로컬 검증에만** 사용, 산출물·내용을 절대 커밋하지 않는다.
- 이미지 지배 페이지 기준: 공백 제거 문자수 **300자 미만** (design §4.2).
- S6 기본 모델 `v5-korean-mobile`, 옵션 `v6-tiny` (design §4.3).
- Clippings frontmatter 필수 키 5종: `source_pdf`, `source_sha256`, `converted_by`, `converted_at`, `pages` (design §4.4).
- SKILL.md 본문은 한국어 산문, 헤딩·코드·고유명사는 영어 유지 (vault Language Convention).
- 커밋은 이 브랜치(`feat/pdf2md-ingest-skill`)에 태스크당 1회.

---

### Task 1: measure-density.sh — 페이지별 텍스트 밀도 측정

**Files:**
- Create: `projects/second-brain/config/skills/pdf2md-ingest/scripts/measure-density.sh`

**Interfaces:**
- Produces: `measure-density.sh <pdf>` → stdout에 `pages: N`, 페이지별 `p<i>: <chars>[ image-dominant]`, 마지막 줄 `image-dominant: <low>/<N>`. exit 0 정상 / 비0 실패. SKILL.md(Task 4)가 이 출력 형식을 그대로 인용한다.

- [ ] **Step 1: 스크립트 작성**

```bash
#!/usr/bin/env bash
# 페이지별 텍스트 레이어 밀도(공백 제거 문자수) 측정 — pdf2md-ingest 라우팅 입력
# usage: measure-density.sh <pdf>
# 기준: 300자 미만 = image-dominant (pdf2md-bench §5.2 실측 기반)
set -euo pipefail

PDF="${1:?usage: measure-density.sh <pdf>}"
[ -f "$PDF" ] || { echo "not found: $PDF" >&2; exit 1; }

PAGES=$(pdfinfo "$PDF" | awk '/^Pages:/{print $2}')
[ -n "$PAGES" ] || { echo "pdfinfo failed" >&2; exit 1; }

echo "pages: $PAGES"
LOW=0
for p in $(seq 1 "$PAGES"); do
  N=$(pdftotext -f "$p" -l "$p" "$PDF" - 2>/dev/null | tr -d '[:space:]' | wc -c | tr -d ' ')
  FLAG=""
  if [ "$N" -lt 300 ]; then FLAG=" image-dominant"; LOW=$((LOW+1)); fi
  echo "p$p: $N$FLAG"
done
echo "image-dominant: $LOW/$PAGES"
```

`chmod +x` 필수.

- [ ] **Step 2: 벤치 PDF로 검증 실행**

Run:
```bash
projects/second-brain/config/skills/pdf2md-ingest/scripts/measure-density.sh "$HOME/Downloads/베스핀글로벌_청리움_STEP1_구축방향_2026.06.23.pdf"
```

Expected (벤치 §5.2 실측과 대조):
- `pages: 29`
- `p12`~`p15`, `p24` 줄에 `image-dominant` 플래그 (각각 300자 미만)
- `p19`(≈575자), `p20`(≈536자)은 플래그 없음
- 마지막 줄 `image-dominant: <n>/29`에서 n ≥ 5

- [ ] **Step 3: 인자 없는 호출·없는 파일 호출이 비0 exit인지 확인**

Run: `scripts/measure-density.sh; echo "exit=$?"` → usage 메시지 + `exit=1` (set -u로 ${1:?} 실패)
Run: `scripts/measure-density.sh /tmp/nope.pdf; echo "exit=$?"` → `not found` + `exit=1`

- [ ] **Step 4: Commit**

```bash
git add projects/second-brain/config/skills/pdf2md-ingest/scripts/measure-density.sh
git commit -m "feat: pdf2md-ingest 밀도 측정 스크립트 (300자 기준 image-dominant 분류)"
```

---

### Task 2: s2-convert.py — pymupdf4llm 랩퍼

**Files:**
- Create: `projects/second-brain/config/skills/pdf2md-ingest/scripts/s2-convert.py`

**Interfaces:**
- Consumes: 없음 (독립)
- Produces: `python3 s2-convert.py <pdf> <out.md>` → out.md 생성, stdout `wrote <chars> chars -> <out.md>`. 실패 시 비0 exit.

- [ ] **Step 1: 개발 의존성 확인 (없으면 설치)**

Run: `python3 -c "import pymupdf4llm; print(pymupdf4llm.__name__)" 2>&1`
없으면: `pip3 install --user pymupdf4llm` 후 재확인. (개발 환경 준비 — 스킬 런타임의 자동 설치 금지 원칙과 별개.)

- [ ] **Step 2: 스크립트 작성**

```python
#!/usr/bin/env python3
"""S2: pymupdf4llm PDF -> MD 변환 랩퍼 (pdf2md-ingest).

usage: s2-convert.py <pdf> <out.md>
"""
import sys


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit("usage: s2-convert.py <pdf> <out.md>")
    try:
        import pymupdf4llm
    except ImportError:
        sys.exit("pymupdf4llm not installed — run: pip3 install --user pymupdf4llm")
    md = pymupdf4llm.to_markdown(sys.argv[1])
    if not md.strip():
        sys.exit("empty conversion result")
    with open(sys.argv[2], "w", encoding="utf-8") as f:
        f.write(md)
    print(f"wrote {len(md)} chars -> {sys.argv[2]}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: 벤치 PDF로 검증 실행**

Run:
```bash
python3 projects/second-brain/config/skills/pdf2md-ingest/scripts/s2-convert.py \
  "$HOME/Downloads/베스핀글로벌_청리움_STEP1_구축방향_2026.06.23.pdf" /tmp/s2-check.md
wc -c /tmp/s2-check.md
```

Expected: `wrote ...` 출력, 파일 크기 18KB~26KB (벤치 S2.md 22.0KB와 동급). 확인 후 `rm /tmp/s2-check.md` (고객사 데이터 잔존 방지).

- [ ] **Step 4: 인자 오류가 비0 exit인지 확인**

Run: `python3 scripts/s2-convert.py; echo "exit=$?"` → usage + `exit=1`

- [ ] **Step 5: Commit**

```bash
git add projects/second-brain/config/skills/pdf2md-ingest/scripts/s2-convert.py
git commit -m "feat: pdf2md-ingest S2 변환 스크립트 (pymupdf4llm 랩퍼)"
```

---

### Task 3: S6 런타임 셋업 + s6-ocr.mjs

**Files:**
- Create: `projects/second-brain/config/skills/pdf2md-ingest/scripts/s6-ocr.mjs`
- Create (vault 밖, 커밋 아님): `~/.cache/ppu-paddle-ocr-runtime/package.json` + node_modules

**Interfaces:**
- Consumes: 없음 (독립)
- Produces: 실행 규약 — 스크립트를 런타임 디렉토리로 복사 후 실행 (bare import 해석 때문):
  `cp scripts/s6-ocr.mjs ~/.cache/ppu-paddle-ocr-runtime/ && node ~/.cache/ppu-paddle-ocr-runtime/s6-ocr.mjs <pdf> <out.md> [--model v6-tiny]`
  → out.md에 `<!-- page N -->` 마커 페이지별 텍스트. stderr에 진행 로그. SKILL.md(Task 4)가 이 규약을 그대로 인용한다.

- [ ] **Step 1: 런타임 디렉토리 구축 (1회 셋업 — SKILL.md 셋업 절과 동일 명령)**

```bash
mkdir -p ~/.cache/ppu-paddle-ocr-runtime && cd ~/.cache/ppu-paddle-ocr-runtime
npm init -y >/dev/null
npm install ppu-paddle-ocr onnxruntime-node
```

Run: `node -e "import('ppu-paddle-ocr').then(m=>console.log(typeof m.PaddleOcrService))" --input-type=module` (cwd=런타임 디렉토리) → `function`
주의: 이 방식은 cwd 기준이 아니라 스크립트 파일 위치 기준으로 해석되므로, 위 확인은 런타임 디렉토리 안에서 실행해야 한다.

- [ ] **Step 2: 스크립트 작성**

```javascript
// S6: PDF -> pdftoppm 150dpi -> ppu-paddle-ocr -> 페이지 마커 MD (pdf2md-ingest)
//
// bare import가 런타임 node_modules를 보도록, 반드시 런타임 디렉토리로 복사 후 실행:
//   RUNTIME=~/.cache/ppu-paddle-ocr-runtime
//   cp scripts/s6-ocr.mjs "$RUNTIME/" && node "$RUNTIME/s6-ocr.mjs" <pdf> <out.md> [--model v6-tiny]
//
// 기본 모델 v5-korean-mobile (v6 tiny/small은 한글을 한자로 오인식 — wiki/pp-ocrv6.md 실측)
import { mkdtemp, readdir, readFile, writeFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { execFileSync } from "node:child_process";
import { PaddleOcrService, V5_KOREAN_MOBILE_MODEL, V6_TINY_MODEL } from "ppu-paddle-ocr";

const args = process.argv.slice(2);
let model = V5_KOREAN_MOBILE_MODEL;
const mi = args.indexOf("--model");
if (mi !== -1) {
  const name = args[mi + 1];
  if (name === "v6-tiny") model = V6_TINY_MODEL;
  else if (name !== "v5-korean-mobile") {
    console.error(`unknown model: ${name} (v5-korean-mobile | v6-tiny)`);
    process.exit(2);
  }
  args.splice(mi, 2);
}
const [pdf, out] = args;
if (!pdf || !out) {
  console.error("usage: node s6-ocr.mjs <pdf> <out.md> [--model v6-tiny]");
  process.exit(2);
}

const pagesDir = await mkdtemp(join(tmpdir(), "s6-pages-"));
try {
  execFileSync("pdftoppm", ["-png", "-r", "150", pdf, join(pagesDir, "p")]);
  const files = (await readdir(pagesDir)).filter((f) => f.endsWith(".png")).sort();
  if (files.length === 0) throw new Error("pdftoppm produced no pages");

  const service = new PaddleOcrService({ model });
  await service.initialize();
  const t0 = performance.now();
  const parts = [];
  for (const [i, f] of files.entries()) {
    const buf = await readFile(join(pagesDir, f));
    // v6.3.0 Node API는 문자열 경로 미지원 — ArrayBuffer로 전달 (wiki/pp-ocrv6.md 실측)
    const ab = buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength);
    const result = await service.recognize(ab);
    parts.push(`<!-- page ${i + 1} -->\n\n${result.text.trim()}\n`);
    console.error(`page ${i + 1}/${files.length} (${result.text.length} chars)`);
  }
  await writeFile(out, parts.join("\n"));
  console.error(`--- ${files.length} pages, ${((performance.now() - t0) / 1000).toFixed(1)}s -> ${out}`);
  await service.destroy();
} finally {
  await rm(pagesDir, { recursive: true, force: true });
}
```

- [ ] **Step 3: 벤치 PDF로 검증 실행**

```bash
RUNTIME=~/.cache/ppu-paddle-ocr-runtime
cp projects/second-brain/config/skills/pdf2md-ingest/scripts/s6-ocr.mjs "$RUNTIME/"
node "$RUNTIME/s6-ocr.mjs" "$HOME/Downloads/베스핀글로벌_청리움_STEP1_구축방향_2026.06.23.pdf" /tmp/s6-check.md
grep -c '<!-- page' /tmp/s6-check.md && wc -c /tmp/s6-check.md
```

Expected: 마커 29개, 크기 20KB~26KB (벤치 S6.md 23.2KB와 동급), 총 소요 60초 미만. 확인 후 `rm /tmp/s6-check.md`.

- [ ] **Step 4: 인자 오류·잘못된 모델명이 exit 2인지 확인**

Run: `node "$RUNTIME/s6-ocr.mjs"; echo "exit=$?"` → usage + `exit=2`
Run: `node "$RUNTIME/s6-ocr.mjs" a.pdf b.md --model nope; echo "exit=$?"` → unknown model + `exit=2`

- [ ] **Step 5: Commit**

```bash
git add projects/second-brain/config/skills/pdf2md-ingest/scripts/s6-ocr.mjs
git commit -m "feat: pdf2md-ingest S6 변환 스크립트 (ppu-paddle-ocr v5-korean-mobile)"
```

---

### Task 4: SKILL.md — 절차 본문

**Files:**
- Create: `projects/second-brain/config/skills/pdf2md-ingest/SKILL.md`

**Interfaces:**
- Consumes: Task 1~3의 스크립트 규약 (출력 형식·실행 규약을 본문에 그대로 인용)
- Produces: 클코가 읽고 실행하는 절차 문서. 아래 전문을 그대로 사용.

- [ ] **Step 1: SKILL.md 작성 (아래 전문)**

````markdown
---
name: pdf2md-ingest
description: >
  PDF를 vault 잉게스트 가능한 MD로 변환해 Clippings/에 투입한다. 페이지별 텍스트
  밀도를 측정해 변환 전략(S2 pymupdf4llm / S6 로컬 OCR / S4 Claude 비전 전사)을
  제안하고 사용자 확인 후 실행한다. wiki화는 하지 않는다 — 기존 vault-ingest가
  이어받는다. 근거: projects/pdf2md-bench/outputs/verdict-report.md
---

# pdf2md-ingest (PDF → Clippings MD)

## 언제 사용하는가

- 사용자가 "이 PDF 잉게스트해줘" / "PDF를 vault에 넣어줘"라고 요청할 때
- PDF 내용을 wiki 지식으로 만들고 싶은데 원본이 md가 아닐 때

이 스킬은 **변환과 Clippings 투입까지만** 담당한다. 개념 추출·wiki 생성·커밋·PR은
하지 않는다 (기존 vault-ingest / vault-ingest-claude 몫).

## 전제 도구 (없으면 안내 후 중단 — 자동 설치 금지)

| 도구 | 확인 | 설치 안내 |
|---|---|---|
| poppler (`pdfinfo`·`pdftotext`·`pdftoppm`) | `command -v pdftoppm` | `brew install poppler` |
| Python 3 + pymupdf4llm (S2) | `python3 -c "import pymupdf4llm"` | `pip3 install --user pymupdf4llm` |
| Node 18+ (S6) | `node --version` | nvm 등으로 설치 |
| S6 런타임 (1회) | `ls ~/.cache/ppu-paddle-ocr-runtime/node_modules/ppu-paddle-ocr` | 아래 셋업 절 |

**S6 런타임 1회 셋업** (~330MB, vault 밖):

```bash
mkdir -p ~/.cache/ppu-paddle-ocr-runtime && cd ~/.cache/ppu-paddle-ocr-runtime
npm init -y && npm install ppu-paddle-ocr onnxruntime-node
```

**스킬 발견용 설치** (머신별 1회): `$VAULT_DIR/.claude/skills/`에 심링크

```bash
mkdir -p "$VAULT_DIR/.claude/skills"
ln -s "$VAULT_DIR/projects/second-brain/config/skills/pdf2md-ingest" \
      "$VAULT_DIR/.claude/skills/pdf2md-ingest"
```

## 절차

### 0. 게이트 (변환 전 — 하나라도 실패하면 아무것도 쓰지 않고 보고)

1. **커밋 가능성**: 사용자에게 확인 — "이 PDF는 팀 공유 vault에 커밋 가능한 문서인가?"
   고객사·개인 문서면 중단하고 vault 밖 경로(예: `~/work/`)만 안내한다.
2. **VAULT_DIR resolve**: 사용자 명시값 > vault 구조(`VAULT_RULES.md`, `wiki/`, `raw/`,
   `Clippings/`, `templates/`)가 확인된 현재 루트 > 그 외에는 사용자에게 질문.
   `~/knowledge` 조용한 fallback 금지. 절대경로로 resolve.
3. **중복**: `raw/pdf/<원본파일명>.pdf`가 이미 있으면 중단·보고 (raw/는 append-only).

### 1. 밀도 측정 → 전략 제안

```bash
SKILL_DIR="$VAULT_DIR/projects/second-brain/config/skills/pdf2md-ingest"
"$SKILL_DIR/scripts/measure-density.sh" <pdf>
```

출력의 `image-dominant: <n>/<pages>`로 제안을 정한다:

| 밀도 프로파일 | 제안 | 근거 (pdf2md-bench 실측) |
|---|---|---|
| image-dominant 0페이지 | **S2** | 텍스트 문서 T1·T2 만점, 무료·초 단위 |
| image-dominant ≥1페이지 | **S6 기본**, S4 옵션 병기 | 둘 다 QA 15/15. S6=$0·초 단위 / S4=구조·서술 우위, ~$0.045/p·수 분 |
| 전 페이지 텍스트 0자 (스캔) | **S6 기본**, S4 옵션 | 텍스트 추출 계열 원리적 불가 |

측정 결과(총 페이지·image-dominant 수)와 제안·예상 비용을 사용자에게 보여주고
**확인받은 뒤** 변환한다. S5(하이브리드)는 제안하지 않는다 — 텍스트 뼈대의 구조
손상을 상속하는 맹점 (verdict-report §5.3).

### 2. 변환 (산출은 스크래치 디렉토리에 — 완성 전 vault에 쓰지 않는다)

- **S2**: `python3 "$SKILL_DIR/scripts/s2-convert.py" <pdf> <scratch>/converted.md`
- **S6**: 스크립트를 런타임으로 복사 후 실행 (bare import 해석 때문에 필수):

  ```bash
  RUNTIME=~/.cache/ppu-paddle-ocr-runtime
  cp "$SKILL_DIR/scripts/s6-ocr.mjs" "$RUNTIME/"
  node "$RUNTIME/s6-ocr.mjs" <pdf> <scratch>/converted.md          # 한글 문서 (기본)
  node "$RUNTIME/s6-ocr.mjs" <pdf> <scratch>/converted.md --model v6-tiny  # 영문 전용
  ```

- **S4** (클코 자신이 수행): `pdftoppm -png -r 150 <pdf> <scratch>/pages/p`로 렌더 후
  페이지 이미지를 순서대로 Read로 정독하며 전사한다. 규칙:
  - 보이는 것만 충실히 전사 — 추측·보완·요약 금지 (환각 방지)
  - 표는 MD 표로 재구성
  - 다이어그램·그림은 내부 라벨을 모두 옮기고, 화살표·흐름 등 관계를 텍스트로 서술
  - 페이지마다 `<!-- page N -->` 마커
  - 시작 전 예상 비용(~$0.045/페이지)을 사용자에게 고지

### 3. 산출·마무리

1. 원본 보존: `cp <pdf> "$VAULT_DIR/raw/pdf/<원본파일명>.pdf"` (디렉토리 없으면 생성)
2. frontmatter를 붙여 `Clippings/<원본파일명 확장자만 .md>.md`로 이동:

   ```yaml
   ---
   source_pdf: "raw/pdf/<원본파일명>.pdf"
   source_sha256: "<shasum -a 256 결과>"
   converted_by: S2|S4|S6
   converted_at: "YYYY-MM-DD"
   pages: N
   ---
   ```

   본문 첫 줄은 원제목 H1 (`# <문서 제목>`).
3. 완료 보고: 전략·페이지 수·MD 크기·경로 + "잉게스트는 vault-ingest(-claude)로
   별도 실행" 안내.

### 4. 검증 (완료 선언 전)

- `<!-- page N -->` 마커 수 = 페이지 수 (S6/S4)
- MD 0바이트면 실패 처리. 페이지당 평균 100자 미만이면 경고 + 사용자 확인
  (희소 텍스트 문서일 수 있음)
- frontmatter 필수 키 5종 존재 (`source_pdf`·`source_sha256`·`converted_by`·`converted_at`·`pages`)
- 모든 산출 경로가 `$VAULT_DIR` 아래인지

## 에러 처리 (fail-closed)

- 도구·런타임 부재 → 위 셋업 명령 안내 후 중단. 자동 설치 금지.
- 변환 실패 → 스크래치만 정리하고 `Clippings/`·`raw/`는 건드리지 않는다.
- 게이트 실패 → 아무것도 쓰지 않고 사유 보고.

## 근거·주의 (요약)

- 전략별 강점: `projects/pdf2md-bench/outputs/verdict-report.md` (S6 §7, 라우팅 §7.4)
- ppu-paddle-ocr 실측 주의점: `wiki/pp-ocrv6.md` § Setup Notes (한글=v5-korean-mobile,
  ArrayBuffer 입력, 모델 캐시 `~/.cache/ppu-paddle-ocr`)
````

- [ ] **Step 2: 정합 검증**

Run: `grep -c "300자\|image-dominant" projects/second-brain/config/skills/pdf2md-ingest/SKILL.md` → 기준치 언급 존재.
design.md §4와 SKILL.md 절차를 나란히 읽고 어긋난 항목 0건 확인 (라우팅 표·frontmatter 키·에러 규칙).

- [ ] **Step 3: Commit**

```bash
git add projects/second-brain/config/skills/pdf2md-ingest/SKILL.md
git commit -m "feat: pdf2md-ingest SKILL.md — 게이트·밀도 라우팅·변환·검증 절차"
```

---

### Task 5: 심링크 설치 + 샌드박스 E2E

**Files:**
- Create (git 미추적): `$VAULT_DIR/.claude/skills/pdf2md-ingest` 심링크
- 샌드박스: `/tmp/pdf2md-e2e/` (임시 vault + 합성 PDF — 종료 시 삭제)

**Interfaces:**
- Consumes: Task 1~4 전부 (스킬 절차 전체를 실제로 밟는다)

- [ ] **Step 1: 심링크 설치 (실제 vault 루트 = 이 worktree)**

```bash
V=$(git rev-parse --show-toplevel)   # 이 worktree(=vault 루트)의 절대경로
mkdir -p "$V/.claude/skills"
ln -sfn "$V/projects/second-brain/config/skills/pdf2md-ingest" "$V/.claude/skills/pdf2md-ingest"
ls -l "$V/.claude/skills/"
```

Expected: 심링크 존재, `git status`에 나타나지 않음 (`.claude/` 미추적 확인 — 나타나면 gitignore 추가 검토를 보고).

- [ ] **Step 2: 샌드박스 vault + 합성 PDF 준비**

```bash
SB=/tmp/pdf2md-e2e
mkdir -p "$SB"/{wiki,raw,Clippings,templates,outputs}
touch "$SB/VAULT_RULES.md"
printf '합성 테스트 문서\n\n첫 페이지 본문입니다. 예약 시스템의 개요를 설명한다. %s\n\n%s\n' \
  "$(python3 -c "print('가나다라마바사 텍스트 밀도 확보용 문장. '*30)")" \
  "$(python3 -c "print('두 번째 문단. '*40)")" > "$SB/doc.txt"
cupsfilter "$SB/doc.txt" > "$SB/synthetic-test.pdf" 2>/dev/null
pdfinfo "$SB/synthetic-test.pdf" | grep Pages
```

Expected: 1페이지 이상의 유효 PDF. (cupsfilter 실패 시 대안: `textutil -convert html` 후 브라우저 인쇄 대신 — `python3 -c "import pymupdf; d=pymupdf.open(); p=d.new_page(); p.insert_text((72,72), open('$SB/doc.txt').read()); d.save('$SB/synthetic-test.pdf')"` — pymupdf는 Task 2에서 설치됨.)

- [ ] **Step 3: 스킬 절차를 샌드박스에서 수동 실행 (S2 경로)**

SKILL.md 절차 0~4를 `VAULT_DIR=$SB`로 그대로 밟는다:
- 게이트: 합성 문서 = 커밋 가능(테스트), raw/pdf 중복 없음 → 통과
- 밀도 측정 → Expected: image-dominant 0 → S2 제안
- S2 변환 → 스크래치에 converted.md
- 산출: `$SB/raw/pdf/synthetic-test.pdf` + `$SB/Clippings/synthetic-test.md` (frontmatter 5키)

- [ ] **Step 4: E2E 검증 명령**

```bash
ls "$SB/raw/pdf/" "$SB/Clippings/"
head -8 "$SB/Clippings/synthetic-test.md"   # frontmatter 5키 육안 확인
python3 - <<'EOF'
import re
t = open("/tmp/pdf2md-e2e/Clippings/synthetic-test.md").read()
fm = t.split("---")[1]
missing = [k for k in ("source_pdf","source_sha256","converted_by","converted_at","pages") if k+":" not in fm]
assert not missing, f"missing keys: {missing}"
print("frontmatter OK")
EOF
```

Expected: 두 산출물 존재, `frontmatter OK`.

- [ ] **Step 5: 샌드박스 정리 + (커밋 대상 변경 없음 확인)**

```bash
rm -rf /tmp/pdf2md-e2e
git status --short   # 스킬 파일 외 신규 변경 없어야 함
```

E2E는 커밋할 파일을 만들지 않는다 — 이 태스크는 커밋 없음.

---

### Task 6: 프로젝트 문서 갱신 + PR

**Files:**
- Modify: `projects/second-brain/README.md` (Log에 한 줄)
- Modify: `projects/pdf2md-bench/README.md` (frontmatter `next_action` 갱신 — 스킬 제작 완료 반영)

**Interfaces:**
- Consumes: Task 1~5 완료 상태

- [ ] **Step 1: second-brain README Log에 추가**

Log 섹션(없으면 만들지 말고 기존 서술 관례를 따름)에:
`- 2026-08-07: pdf2md-ingest 클코 스킬 추가 — PDF를 밀도 라우팅(S2/S6/S4)으로 변환해 Clippings/ 투입. 근거: pdf2md-bench 판정. config/skills/pdf2md-ingest/`

- [ ] **Step 2: pdf2md-bench README next_action 갱신**

`next_action: "완료 — pdf2md-ingest 스킬 제작됨 (projects/second-brain/config/skills/pdf2md-ingest/). 남은 후속: 하이브리드 재설계 실험(§5.3)은 필요 시"`

- [ ] **Step 3: Commit + PR**

```bash
git add projects/second-brain/README.md projects/pdf2md-bench/README.md
git commit -m "docs: pdf2md-ingest 스킬 등록 반영 (second-brain·pdf2md-bench README)"
git push -u origin feat/pdf2md-ingest-skill
gh pr create --base master --title "feat: pdf2md-ingest 클코 스킬 — 밀도 라우팅 PDF→Clippings 변환" \
  --body "<설계·플랜·E2E 요약, 머지는 사용자 액션>"
```

Expected: PR URL 출력. 머지는 사용자 판단.

---

## Self-Review 결과 (작성 후 점검)

- 스펙 커버리지: design §3(파일 배치)=Task 1~4, §4.1 게이트·§4.2 라우팅·§4.3 변환·§4.4 산출=Task 4(SKILL.md)+Task 5(E2E), §5 검증=Task 4 §4+Task 5 Step 4, §6 에러=Task 1/2/3 오류 exit 검증+SKILL.md 에러 절, 심링크 설치=Task 5 Step 1. 갭 없음.
- 플레이스홀더: 코드 블록 전부 실행 가능한 전문 수록. PR body만 요약 지시(작성 시점 내용 의존).
- 타입/규약 일관성: `measure-density.sh` 출력 형식·`s6-ocr.mjs` 복사-실행 규약·frontmatter 5키가 Task 간 동일 표기임을 확인.
