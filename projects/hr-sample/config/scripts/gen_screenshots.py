# -*- coding: utf-8 -*-
"""screenshots/YYYY-MM-DD/ 레인 샘플 2건 — Slack 대화 목업, HR 시스템 대시보드 목업.
raw-layout.md § 3 계약: <slug>-<short-hash>.<ext> + 짝 .ocr.md, append-only.
telegram-screenshot-digest.md 스킬 본문이 이 vault에 없어 .ocr.md의 세부 필드는
다른 레인(H1/S2/P1/D1)의 frontmatter 패턴에서 유추했다 — README에 명시.
"""
import os, hashlib
from PIL import Image, ImageDraw, ImageFont
import data as D

OUT_DIR = os.path.expanduser("~/knowledge-sample/raw/screenshots/2026-08-26")
os.makedirs(OUT_DIR, exist_ok=True)

FONT_DIR = "/System/Library/Fonts/Supplemental/"
def font(size, bold=False):
    path = FONT_DIR + ("AppleGothic.ttf")
    return ImageFont.truetype(path, size)

def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""): h.update(b)
    return h.hexdigest()[:7]


# ══════════════════════════════════════════════════════════════════
# 1. Slack 스타일 대화 목업 — #people-ops 채널
# ══════════════════════════════════════════════════════════════════
def slack_mockup():
    W, H = 1000, 760
    BG = (255, 255, 255)
    SIDEBAR_BG = (74, 21, 75)
    HEADER_BG = (255, 255, 255)
    TEXT = (29, 28, 29)
    SUB = (97, 96, 98)
    LINK = (18, 100, 163)

    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    # 사이드바
    d.rectangle([0, 0, 220, H], fill=SIDEBAR_BG)
    d.text((20, 20), "나린테크", font=font(18, True), fill=(255,255,255))
    d.text((20, 55), "# people-ops", font=font(14, True), fill=(255,255,255))
    for i, ch in enumerate(["# general", "# people-ops", "# 플랫폼개발본부", "# 랜덤"]):
        y = 90 + i*30
        w = (255,255,255) if ch == "# people-ops" else (200, 180, 200)
        if ch == "# people-ops":
            d.rectangle([10, y-4, 210, y+22], fill=(60, 15, 61))
        d.text((22, y), ch, font=font(13), fill=w)

    # 헤더
    d.rectangle([220, 0, W, 56], fill=HEADER_BG)
    d.line([220, 56, W, 56], fill=(221,221,221), width=1)
    d.text((240, 16), "# people-ops", font=font(17, True), fill=TEXT)

    # 메시지 목업
    msgs = [
        ("김하나", "10:14 AM", "인사담당",
         "2026년 상반기 평가 결과 통보 나갔습니다. 이번부터 등급 근거도 같이 보내드렸어요 —\n"
         "「인사평가 운영지침」 제12조 개정 반영입니다."),
        ("박서준", "10:17 AM", "플랫폼개발본부",
         "확인했습니다. 근데 저희 팀 D등급 대상자가 없어서 분포 규정(5%)에서 좀 벗어났는데,\n"
         "이거 문제 없나요?"),
        ("김하나", "10:19 AM", "인사담당",
         "지침 제6조 제3항에 따라 10명 미만 조직은 상위 조직 합산으로 처리됩니다.\n"
         "플랫폼개발본부는 59명이라 합산 대상은 아니에요 — 보정회의에서 논의된 사항입니다."),
        ("박서준", "10:20 AM", "플랫폼개발본부", "아 넵 감사합니다!"),
        ("이수민", "10:32 AM", "인사담당",
         "이의신청 접수는 오늘 자정까지입니다 (통보일+7일, 지침 제12조 제2항).\n"
         "질문 있으신 분들은 이 채널에 남겨주세요."),
    ]
    y = 80
    for name, time, dept, text in msgs:
        d.ellipse([240, y, 276, y+36], fill=(120+hash(name)%100, 90, 140))
        initials = name[0]
        d.text((251, y+7), initials, font=font(16, True), fill=(255,255,255))
        d.text((290, y), name, font=font(14, True), fill=TEXT)
        nw = d.textlength(name, font=font(14, True))
        d.text((290+nw+8, y+2), time, font=font(11), fill=SUB)
        d.text((290, y+20), text, font=font(13), fill=TEXT)
        lines = text.count("\n") + 1
        y += 40 + lines*20

    p = OUT_DIR + "/people-ops-calibration-question-%s.png"
    tmp = p % "tmp"
    img.save(tmp)
    h = sha(tmp)
    final = p % h
    os.rename(tmp, final)
    return final, h, msgs

def slack_ocr(msgs, image_path, h):
    lines = ["#people-ops", ""]
    for name, time, dept, text in msgs:
        lines.append("%s (%s) [%s]" % (name, dept, time))
        lines.append(text.replace("\n", " "))
        lines.append("")
    body = "\n".join(lines)
    rel = "raw/screenshots/2026-08-26/" + os.path.basename(image_path)
    md = ("---\n"
          'source_image: "%s"\n'
          'source_sha256_prefix: "%s"\n'
          "captured: \"2026-08-26\"\n"
          'ocr_engine: "mock-vision-transcribe (hr-sample 픽스처용, 실제 OCR 엔진 미사용)\"\n'
          'note: "telegram-screenshot-digest 스킬 본문이 이 vault에 없어 필드는 다른 레인 패턴에서 유추. Slack 채널 #people-ops 대화 스크린샷의 텍스트 전사."\n'
          "---\n\n# 스크린샷 OCR 전사 — #people-ops 대화\n\n%s" % (rel, h, body))
    with open(image_path.replace(".png", ".ocr.md"), "w", encoding="utf-8") as f:
        f.write(md)
    return len(md)


# ══════════════════════════════════════════════════════════════════
# 2. HR 시스템 대시보드 목업 — 등급 분포 차트
# ══════════════════════════════════════════════════════════════════
def dashboard_mockup():
    hf = D.half(2026, 1)
    W, H = 1000, 700
    BG = (247, 248, 250)
    CARD = (255, 255, 255)
    NAVY = (30, 41, 59)
    ACCENT = (37, 99, 235)
    TEXT = (30, 41, 59)
    SUB = (100, 116, 139)

    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    # 상단 바
    d.rectangle([0, 0, W, 56], fill=NAVY)
    d.text((24, 16), "나린테크 HR 시스템 — 평가 관리", font=font(17, True), fill=(255,255,255))
    d.text((W-180, 18), "인사담당 로그인", font=font(12), fill=(200,210,230))

    # 카드 영역
    d.rectangle([24, 80, W-24, H-24], fill=CARD, outline=(226,232,240), width=1)
    d.text((48, 104), "2026년 상반기 등급 분포", font=font(20, True), fill=TEXT)
    d.text((48, 134), "평가 대상 %d명 (재직 %d명 - 수습 %d명) · 지침 제6조 규정 대비" %
           (hf["n"], hf["headcount"], hf["probation"]), font=font(13), fill=SUB)

    colors = {"S": (37,99,235), "A": (59,130,246), "B": (147,197,253),
              "C": (253,186,116), "D": (248,113,113)}
    chart_x, chart_y, chart_w, chart_h = 80, 200, 780, 320
    max_pct = 55
    bw = chart_w // 5
    for i, g in enumerate(D.GRADES):
        cnt = hf["dist"][g]
        pct = cnt / hf["n"] * 100
        quota = D.QUOTA[g] * 100
        bh = int(chart_h * pct / max_pct)
        qh = int(chart_h * quota / max_pct)
        x0 = chart_x + i*bw + 30
        x1 = x0 + 90
        y1 = chart_y + chart_h
        y0 = y1 - bh
        d.rectangle([x0, y0, x1, y1], fill=colors[g])
        # 규정선
        qy = y1 - qh
        d.line([x0-8, qy, x1+8, qy], fill=(15,23,42), width=2)
        d.text((x0+20, y1+10), g, font=font(18, True), fill=TEXT)
        d.text((x0, y0-44), "%d명" % cnt, font=font(14, True), fill=TEXT)
        d.text((x0, y0-24), "%.1f%%" % pct, font=font(12), fill=SUB)
    d.text((chart_x, chart_y-30), "실선 = 규정 비율선  |  막대 = 실제 인원 비율", font=font(11), fill=SUB)

    y = chart_y + chart_h + 70
    d.text((48, y), "보정회의: 상향 %d건 · 하향 %d건  |  이의신청: 접수 %d건 · 인용 %d건" %
           (hf["up"], hf["down"], hf["appeal"], hf["upheld"]), font=font(13), fill=TEXT)

    p = OUT_DIR + "/eval-system-grade-distribution-2026h1-%s.png"
    tmp = p % "tmp"
    img.save(tmp)
    h = sha(tmp)
    final = p % h
    os.rename(tmp, final)
    return final, h, hf

def dashboard_ocr(hf, image_path, h):
    rows = "\n".join("%s: %d명 (%.1f%%, 규정 %.0f%%)" % (g, hf["dist"][g], hf["dist"][g]/hf["n"]*100, D.QUOTA[g]*100)
                     for g in D.GRADES)
    body = ("나린테크 HR 시스템 — 평가 관리\n"
            "2026년 상반기 등급 분포\n"
            "평가 대상 %d명 (재직 %d명 - 수습 %d명) - 지침 제6조 규정 대비\n\n"
            "%s\n\n"
            "보정회의: 상향 %d건 - 하향 %d건\n"
            "이의신청: 접수 %d건 - 인용 %d건\n"
            % (hf["n"], hf["headcount"], hf["probation"], rows, hf["up"], hf["down"],
               hf["appeal"], hf["upheld"]))
    rel = "raw/screenshots/2026-08-26/" + os.path.basename(image_path)
    md = ("---\n"
          'source_image: "%s"\n'
          'source_sha256_prefix: "%s"\n'
          "captured: \"2026-08-26\"\n"
          'ocr_engine: "mock-vision-transcribe (hr-sample 픽스처용, 실제 OCR 엔진 미사용)"\n'
          'note: "telegram-screenshot-digest 스킬 본문이 이 vault에 없어 필드는 다른 레인 패턴에서 유추. 사내 평가 관리 시스템 대시보드 스크린샷의 텍스트 전사."\n'
          "---\n\n# 스크린샷 OCR 전사 — 평가 관리 대시보드\n\n%s" % (rel, h, body))
    with open(image_path.replace(".png", ".ocr.md"), "w", encoding="utf-8") as f:
        f.write(md)
    return len(md)


if __name__ == "__main__":
    p1, h1, msgs = slack_mockup()
    sz1 = slack_ocr(msgs, p1, h1)
    print("  %s  (%d bytes PNG)" % (os.path.basename(p1), os.path.getsize(p1)))
    print("  %s  (%d bytes OCR)" % (os.path.basename(p1).replace(".png",".ocr.md"), sz1))

    p2, h2, hf = dashboard_mockup()
    sz2 = dashboard_ocr(hf, p2, h2)
    print("  %s  (%d bytes PNG)" % (os.path.basename(p2), os.path.getsize(p2)))
    print("  %s  (%d bytes OCR)" % (os.path.basename(p2).replace(".png",".ocr.md"), sz2))
    print("screenshots 레인 2쌍 생성 완료")
