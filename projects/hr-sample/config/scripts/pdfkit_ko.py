# -*- coding: utf-8 -*-
"""한국어 PDF 생성 공용 스타일. 표는 격자선을 넣어 pymupdf4llm이 표로 검출하게 한다."""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

FONT_PATH = "/System/Library/Fonts/Supplemental/AppleGothic.ttf"
F = "AppleGothic"
_registered = False

def _reg():
    global _registered
    if not _registered:
        pdfmetrics.registerFont(TTFont(F, FONT_PATH))
        _registered = True

def styles():
    _reg()
    return {
        "h1":   ParagraphStyle("h1", fontName=F, fontSize=17, leading=23, spaceAfter=4),
        "sub":  ParagraphStyle("sub", fontName=F, fontSize=9.5, leading=14,
                               textColor=colors.HexColor("#666666"), spaceAfter=14),
        "h2":   ParagraphStyle("h2", fontName=F, fontSize=12.5, leading=18,
                               spaceBefore=14, spaceAfter=6),
        "body": ParagraphStyle("body", fontName=F, fontSize=10, leading=16.5, spaceAfter=6),
        "note": ParagraphStyle("note", fontName=F, fontSize=8.5, leading=13,
                               textColor=colors.HexColor("#888888")),
    }

def table(data, widths):
    """격자선 있는 표 — 표 검출이 걸리도록 GRID를 준다."""
    _reg()
    t = Table(data, colWidths=widths, hAlign="LEFT", repeatRows=1)
    t.setStyle(TableStyle([
        ("FONTNAME", (0,0), (-1,-1), F),
        ("FONTSIZE", (0,0), (-1,-1), 8.5),
        ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#999999")),
        ("BOX", (0,0), (-1,-1), 0.9, colors.HexColor("#555555")),
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#EDEDED")),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("ALIGN", (1,1), (-1,-1), "CENTER"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ]))
    return t

def build(path, title, author, flow):
    _reg()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    doc = SimpleDocTemplate(path, pagesize=A4,
        leftMargin=22*mm, rightMargin=22*mm, topMargin=20*mm, bottomMargin=18*mm,
        title=title, author=author)
    doc.build(flow)
    return os.path.getsize(path)

MM = mm
