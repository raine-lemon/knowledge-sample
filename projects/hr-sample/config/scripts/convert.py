# -*- coding: utf-8 -*-
"""원문(PDF/HWPX/PPTX) → raw/ 보존 + Clippings/ MD 투입.

frontmatter는 각 스킬이 규정한 필수 키를 그대로 따른다:
  PDF  — pdf2md-ingest §3 (source_pdf·source_sha256·converted_by·converted_at·pages)
  HWPX — hwp2md-ingest §3 (source_hwp·source_sha256·converted_by·converted_at·tables·images)
  PPTX — 대응 스킬 없음. 위 패턴에서 유추한 임시 형식 (note 키로 명시).
  DOCX — 대응 스킬 없음. PPTX와 동일하게 임시 형식 (note 키로 명시).
"""
import os, sys, hashlib, shutil, pathlib

VAULT = pathlib.Path(os.path.expanduser("~/personal-knowledge"))
SRC   = pathlib.Path(os.path.expanduser("~/Documents/hr-samples"))
TODAY = "2026-08-26"

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


def conv_hwpx(src):
    from hwp_hwpx_parser import extract_hwpx
    dst, rel = preserve(src, "hwp")
    text, _ = extract_hwpx(str(dst))
    lines = [l.rstrip() for l in text.splitlines()]
    title, body = lines[0], "\n\n".join(l for l in lines[1:] if l.strip())
    md = ("---\n"
          'source_hwp: "%s"\n'
          'source_sha256: "%s"\n'
          "converted_by: H1\n"
          'converted_at: "%s"\n'
          "tables: 0\n"
          "images: %d\n"
          "---\n\n# %s\n\n%s\n" % (rel, sha(dst), TODAY, text.count("[IMAGE]"), title, body))
    return emit(src.stem + ".md", md), len(text)


def conv_pdf(src):
    import pymupdf4llm, fitz
    dst, rel = preserve(src, "pdf")
    pages = fitz.open(str(dst)).page_count
    body = pymupdf4llm.to_markdown(str(dst), show_progress=False).strip()
    bl = body.splitlines()
    if bl and bl[0].startswith("#"):
        title, body = bl[0].lstrip("# ").strip(), "\n".join(bl[1:]).lstrip("\n")
    else:
        title = src.stem
    md = ("---\n"
          'source_pdf: "%s"\n'
          'source_sha256: "%s"\n'
          "converted_by: S2\n"
          'converted_at: "%s"\n'
          "pages: %d\n"
          "---\n\n# %s\n\n%s\n" % (rel, sha(dst), TODAY, pages, title, body))
    tables = len([l for l in body.splitlines() if l.strip().startswith("|")])
    return emit(src.stem + ".md", md), tables


def conv_pptx(src):
    from pptx import Presentation
    dst, rel = preserve(src, "pptx")
    prs = Presentation(str(dst))
    slides = list(prs.slides)
    parts, title = [], src.stem
    for i, s in enumerate(slides, 1):
        blocks = [sh.text_frame.text.strip() for sh in s.shapes
                  if sh.has_text_frame and sh.text_frame.text.strip()]
        parts.append("<!-- slide %d -->" % i)
        if i == 1:
            head = blocks[0].splitlines() if blocks else [src.stem]
            title = head[0].strip()
            parts += [x.strip() for x in head[1:] if x.strip()]
            continue
        for j, b in enumerate(blocks):
            bl = b.splitlines()
            if j == 0:
                parts.append("## " + bl[0].strip())
                parts += ["_%s_" % x.strip() for x in bl[1:] if x.strip()]
            else:
                for line in bl:
                    line = line.strip()
                    if not line: continue
                    parts.append("- " + line[2:] if line.startswith("• ")
                                 else "  - " + line[2:] if line.startswith("– ") else line)
    md = ("---\n"
          'source_pptx: "%s"\n'
          'source_sha256: "%s"\n'
          "converted_by: P1\n"
          'converted_at: "%s"\n'
          "slides: %d\n"
          'note: "pptx 레인은 스킬·raw 계약에 아직 없음 — 계약 확정 전 임시 변환"\n'
          "---\n\n# %s\n\n%s\n" % (rel, sha(dst), TODAY, len(slides), title,
                                   "\n\n".join(parts)))
    return emit(src.stem + ".md", md), len(slides)


def conv_docx(src):
    from docx import Document
    from docx.table import Table
    from docx.text.paragraph import Paragraph
    from docx.oxml.ns import qn
    dst, rel = preserve(src, "docx")
    doc = Document(str(dst))
    parts, title = [], src.stem
    first_heading_seen = False
    n_tables = 0

    def para_line(el):
        text = el.text.strip()
        if not text:
            return None
        style = (el.style.name or "").lower()
        if style.startswith("heading 1") or style.startswith("title"):
            return ("h1", text)
        if style.startswith("heading 2"):
            return "## " + text
        if style.startswith("list bullet") or style.startswith("list paragraph"):
            return "- " + text
        return text

    def table_lines(tbl):
        rows = [[c.text.strip() for c in row.cells] for row in tbl.rows]
        if not rows:
            return []
        out = ["", "| " + " | ".join(rows[0]) + " |",
               "|" + "|".join(["---"] * len(rows[0])) + "|"]
        for r in rows[1:]:
            out.append("| " + " | ".join(r) + " |")
        return out

    # 본문 순서(document order)대로 문단·표를 번갈아 처리한다 —
    # doc.paragraphs·doc.tables는 각각 별도 평면 리스트라 순서 정보가 없다.
    body = doc.element.body
    for child in body.iterchildren():
        if child.tag == qn("w:p"):
            line = para_line(Paragraph(child, doc))
            if line is None:
                continue
            if isinstance(line, tuple):
                if not first_heading_seen:
                    title = line[1]; first_heading_seen = True
                else:
                    parts.append("# " + line[1])
            else:
                parts.append(line)
        elif child.tag == qn("w:tbl"):
            n_tables += 1
            parts += table_lines(Table(child, doc))

    md = ("---\n"
          'source_docx: "%s"\n'
          'source_sha256: "%s"\n'
          "converted_by: D1\n"
          'converted_at: "%s"\n'
          "paragraphs: %d\n"
          "tables: %d\n"
          'note: "docx 레인은 스킬·raw 계약에 아직 없음 — 계약 확정 전 임시 변환"\n'
          "---\n\n# %s\n\n%s\n" % (rel, sha(dst), TODAY, len(doc.paragraphs),
                                       n_tables, title, "\n\n".join(parts)))
    return emit(src.stem + ".md", md), n_tables


if __name__ == "__main__":
    handlers = {".hwpx": ("H1", conv_hwpx, "문자"), ".pdf": ("S2", conv_pdf, "표행"),
                ".pptx": ("P1", conv_pptx, "슬라이드"), ".docx": ("D1", conv_docx, "표")}
    files = sorted(SRC.iterdir())
    n = 0
    for f in files:
        h = handlers.get(f.suffix.lower())
        if not h: continue
        strat, fn, unit = h
        size, metric = fn(f)
        n += 1
        print("  %s  %6d B  %-46s %4d %s" % (strat, size, f.stem[:46], metric, unit))
    print("변환 %d종 → Clippings/ (원본은 raw/ 보존)" % n)
