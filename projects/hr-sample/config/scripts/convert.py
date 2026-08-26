# -*- coding: utf-8 -*-
"""원문(PDF/HWPX/XLSX/PPTX/DOCX) → raw/ 보존 + Clippings/ MD 투입.

각 포맷의 본문 변환은 **해당 스킬의 공식 스크립트를 호출**한다 — hr-sample이 별도
구현을 갖고 있으면 스킬과 갈라지므로, 문서화된 경로를 그대로 쓴다.
frontmatter·raw 보존은 각 스킬 §3(산출·마무리) 규정을 따른다.

  PDF  — pdf2md-ingest §3   (source_pdf·sha256·converted_by·converted_at·pages)
  HWPX — hwp2md-ingest §3   (source_hwp·…·tables·images)
  XLSX — xlsx2md-ingest §3  (source_xlsx·…·sheets·rows·truncated)
  PPTX — pptx2md-ingest §3  (source_pptx·…·slides·notes·images)
  DOCX — docx2md-ingest §3  (source_docx·…·paragraphs·tables·has_revisions)
"""
import os, sys, json, hashlib, shutil, pathlib, subprocess

VAULT  = pathlib.Path(os.path.expanduser("~/knowledge-sample"))
SRC    = pathlib.Path(os.path.expanduser("~/Documents/hr-samples"))
SKILLS = VAULT / "projects/second-brain/config/skills"
PYBIN  = sys.executable
TODAY  = "2026-08-26"

def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()

def preserve(src, lane):
    dst_dir = VAULT / "raw" / lane
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst = dst_dir / src.name
    shutil.copy2(src, dst)
    return dst, "raw/%s/%s" % (lane, src.name)

def emit(name, text):
    out = VAULT / "Clippings" / name
    out.write_text(text, encoding="utf-8")
    return out.stat().st_size

def run(script, *args, want_stderr=False):
    r = subprocess.run([PYBIN, str(script)] + [str(a) for a in args],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("%s 실패: %s" % (script.name, r.stderr.strip()[:300]))
    return (r.stdout, r.stderr) if want_stderr else r.stdout

def split_title(body, fallback):
    """스크립트 출력 첫 H1을 제목으로 승격 (중복 방지)."""
    lines = body.strip().splitlines()
    if lines and lines[0].startswith("# "):
        return lines[0][2:].strip(), "\n".join(lines[1:]).lstrip("\n")
    return fallback, body.strip()

def fm(pairs, title, body):
    head = "\n".join('%s: %s' % (k, v) for k, v in pairs)
    return "---\n%s\n---\n\n# %s\n\n%s\n" % (head, title, body)


# ── HWPX (hwp2md-ingest H1) ──────────────────────────────────────
def conv_hwpx(src):
    from hwp_hwpx_parser import extract_hwpx
    dst, rel = preserve(src, "hwp")
    text, _ = extract_hwpx(str(dst))
    lines = [l.rstrip() for l in text.splitlines()]
    title = lines[0]
    body = "\n\n".join(l for l in lines[1:] if l.strip())
    md = fm([('source_hwp', '"%s"' % rel), ('source_sha256', '"%s"' % sha(dst)),
             ('converted_by', 'H1'), ('converted_at', '"%s"' % TODAY),
             ('tables', 0), ('images', text.count("[IMAGE]"))], title, body)
    return emit(src.stem + ".md", md), len(text)


# ── PDF (pdf2md-ingest S2) ───────────────────────────────────────
def conv_pdf(src):
    import pymupdf4llm, fitz
    dst, rel = preserve(src, "pdf")
    pages = fitz.open(str(dst)).page_count
    title, body = split_title(pymupdf4llm.to_markdown(str(dst), show_progress=False),
                              src.stem)
    md = fm([('source_pdf', '"%s"' % rel), ('source_sha256', '"%s"' % sha(dst)),
             ('converted_by', 'S2'), ('converted_at', '"%s"' % TODAY),
             ('pages', pages)], title, body)
    tables = len([l for l in body.splitlines() if l.strip().startswith("|")])
    return emit(src.stem + ".md", md), tables


# ── XLSX (xlsx2md-ingest X1/X2) ──────────────────────────────────
def conv_xlsx(src):
    script = SKILLS / "xlsx2md-ingest/scripts/x1-convert.py"
    dst, rel = preserve(src, "xlsx")
    # 이 스크립트는 --stats 플래그 대신 stderr 마지막 줄에 `stats k=v ...` 를 낸다.
    def measure(*extra):
        body, err = run(script, dst, *extra, want_stderr=True)
        line = [l for l in err.strip().splitlines() if l.startswith("stats ")][-1]
        st = {}
        for tok in line[len("stats "):].split():
            k, _, v = tok.partition("=")
            st[k] = v
        return body, st

    # SKILL §1 라우팅은 **시트별** 판정이다(stderr의 rows는 전 시트 합계이므로
    # 그 값과 1000을 비교하면 안 된다). --max-rows를 항상 넘겨 스크립트가 시트마다
    # 1000행 경계를 적용하게 하고, 실제로 자른 시트가 있으면 truncated=true가 온다.
    body, stats = measure("--max-rows", "1000")
    truncated = stats.get("truncated") == "true"
    title, body = split_title(body, src.stem)
    md = fm([('source_xlsx', '"%s"' % rel), ('source_sha256', '"%s"' % sha(dst)),
             ('converted_by', 'X2' if truncated else 'X1'),
             ('converted_at', '"%s"' % TODAY),
             ('sheets', int(stats.get("sheets", 0))),
             ('rows', int(stats.get("rows", 0))),
             ('truncated', 'true' if truncated else 'false')], title, body)
    return emit(src.stem + ".md", md), int(stats.get("sheets", 0))


# ── PPTX (pptx2md-ingest P1) ─────────────────────────────────────
def conv_pptx(src):
    script = SKILLS / "pptx2md-ingest/scripts/p1-convert.py"
    dst, rel = preserve(src, "pptx")
    stats = json.loads(run(script, dst, "--stats"))
    title, body = split_title(run(script, dst), src.stem)
    md = fm([('source_pptx', '"%s"' % rel), ('source_sha256', '"%s"' % sha(dst)),
             ('converted_by', 'P1'), ('converted_at', '"%s"' % TODAY),
             ('slides', stats["slides"]), ('notes', stats["notes"]),
             ('images', stats["images"])], title, body)
    return emit(src.stem + ".md", md), stats["slides"]


# ── DOCX (docx2md-ingest D1) ─────────────────────────────────────
def conv_docx(src):
    script = SKILLS / "docx2md-ingest/scripts/d1-convert.py"
    dst, rel = preserve(src, "docx")
    stats = json.loads(run(script, dst, "--stats"))
    title, body = split_title(run(script, dst), src.stem)
    md = fm([('source_docx', '"%s"' % rel), ('source_sha256', '"%s"' % sha(dst)),
             ('converted_by', 'D1'), ('converted_at', '"%s"' % TODAY),
             ('paragraphs', stats["paragraphs"]), ('tables', stats["tables"]),
             ('has_revisions', 'true' if stats["has_revisions"] else 'false')],
            title, body)
    return emit(src.stem + ".md", md), stats["tables"]


HANDLERS = {
    ".hwpx": ("H1", conv_hwpx, "문자"),
    ".pdf":  ("S2", conv_pdf,  "표행"),
    ".xlsx": ("X1", conv_xlsx, "시트"),
    ".pptx": ("P1", conv_pptx, "슬라이드"),
    ".docx": ("D1", conv_docx, "표"),
}

if __name__ == "__main__":
    n = 0
    for f in sorted(SRC.iterdir()):
        h = HANDLERS.get(f.suffix.lower())
        if not h:
            continue
        strat, fn, unit = h
        size, metric = fn(f)
        n += 1
        print("  %s  %6d B  %-44s %4d %s" % (strat, size, f.stem[:44], metric, unit))
    print("변환 %d종 → Clippings/ (원본은 raw/<확장자>/ 보존)" % n)
