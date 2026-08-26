# -*- coding: utf-8 -*-
"""정기 리포트 PDF 13종 — 반기 평가 5 · 연간 인사운영 2 · 분기 채용이직 6.
각 리포트는 개요 → 본론(3~6절) → 부서별 세부 → 추이 비교 → 근거 문서로 구성해
실제 인사팀 배포 문서 수준의 분량을 갖춘다."""
import os
from reportlab.platypus import Paragraph, Spacer, PageBreak
import data as D
import pdfkit_ko as K

OUT = os.path.expanduser("~/Documents/hr-samples/")
S = K.styles()
mm = K.MM
P = lambda t, s="body": Paragraph(t, S[s])

def header(flow, title, meta):
    flow.append(P(title, "h1"))
    flow.append(P(meta + "<br/>" + D.FIXTURE_NOTE, "sub"))

def pct(a, b):
    return "%.1f%%" % (a / b * 100) if b else "—"


# ══════════════════════════════════════════════════════════════════
# 반기 인사평가 결과 리포트
# ══════════════════════════════════════════════════════════════════
def half_report(y, h):
    hf = D.half(y, h)
    span = "%d-01-01 ~ %d-06-30" % (y, y) if h == 1 else "%d-07-01 ~ %d-12-31" % (y, y)
    label = "상반기" if h == 1 else "하반기"
    ontime, total_org = D.OKR_ONTIME[(y, h)]
    dept = D.dept_headcount(hf["headcount"])
    f = []
    header(f, "%d년 %s 인사평가 결과 리포트" % (y, label),
           "%s 인사담당 · 대상기간 %s · 배포 2026-08-26" % (D.COMPANY, span))

    f.append(P("1. 개요", "h2"))
    f.append(P("본 리포트는 「인사평가 운영지침」(문서번호 HR-REG-001)에 따라 실시한 %d년 %s "
               "인사평가의 집행 결과를 정리한 것이다. 반기말 재직 인원은 %d명이며, 이 중 "
               "수습기간 중인 %d명은 지침 제10조에 따라 별도 수습평가로 분리해 이 집계에서 "
               "제외했다. 따라서 정규 평가 대상은 %d명이다."
               % (y, label, hf["headcount"], hf["probation"], hf["n"])))
    if (y, h) == (2026, 1):
        f.append(P("이번 차수는 2026-01-15 개정 지침이 적용된 첫 차수로, 보정회의 의무화와 "
                   "이의신청 기한 단축(14일 → 7일), 결과 통보 시 등급 근거 동시 제공이 처음 "
                   "반영됐다. 개정 배경은 인사위원회 회의록 2026-01-08을 참고한다."))
    if (y, h) == (2025, 1):
        f.append(P("이번 차수부터 보정회의를 시범 운영했다. 2025-02-20 결정에 따른 것이며 "
                   "이 시점에는 권고 사항으로, 참석은 본부 재량이었다. 시범 운영 경과는 "
                   "인사위원회 회의록 2025-03-14를 참고한다."))
    f.append(P("평가 대상의 본부별 재직 현황은 다음과 같다.", "body"))
    f.append(K.table([["본부", "재직 인원", "재직 비중"]] +
                     [[d, "%d명" % c, pct(c, hf["headcount"])] for d, c in dept] +
                     [["계", "%d명" % hf["headcount"], "100.0%"]],
                     [50*mm, 30*mm, 30*mm]))

    f.append(P("2. 등급 분포 — 규정치 대비 실제치", "h2"))
    f.append(K.table([["등급", "규정 비율", "인원", "실제 비율", "편차"]] + D.dist_rows(hf),
                     [26*mm, 28*mm, 26*mm, 28*mm, 28*mm]))
    f.append(Spacer(1, 6))
    sr = hf["dist"]["S"] / hf["n"] * 100
    dr = hf["dist"]["D"] / hf["n"] * 100
    f.append(P("S등급 %.1f%%, D등급 %.1f%%로 양 끝 등급이 모두 규정 비율에 미달했다. "
               "평가자가 최상·최하 등급 부여를 회피하는 중앙집중 경향이 이어지고 있다. "
               "이 패턴은 2024년 상반기 차수부터 매 차수 반복돼왔다(§5 참조)."
               % (sr, dr)))

    f.append(P("3. 보정회의 결과", "h2"))
    f.append(K.table([
        ["구분", "건수", "비율"],
        ["등급 상향", "%d건" % hf["up"], pct(hf["up"], hf["n"])],
        ["등급 하향", "%d건" % hf["down"], pct(hf["down"], hf["n"])],
        ["유지", "%d건" % hf["kept"], pct(hf["kept"], hf["n"])],
        ["계", "%d건" % hf["n"], "100.0%"],
    ], [42*mm, 30*mm, 30*mm]))
    f.append(Spacer(1, 6))
    f.append(P("보정으로 등급이 변경된 건은 총 %d건(%s)이다. 하향이 상향보다 많은 구조는 "
               "2024년 첫 차수부터 매 차수 반복되고 있으며, 이번 차수도 예외가 아니었다."
               % (hf["changed"], pct(hf["changed"], hf["n"]))))

    f.append(P("4. OKR 연동 및 처우 반영", "h2"))
    f.append(P("성과평가 70점은 대상기간 개시 시점에 확정된 OKR 달성도로 산정한다. "
               "이번 차수에서 기한 내 OKR을 확정한 조직은 전체 %d개 중 %d개(%s)였다."
               % (total_org, ontime, pct(ontime, total_org))))
    avg_raise = D.weighted_raise(hf)
    avg_bonus = D.weighted_bonus(hf)
    f.append(P("「급여규정」 제8조·제9조에 따라 등급별 인상률·상여 지급률을 적용한 결과, "
               "이번 차수의 평가 대상 가중평균 연봉 인상률은 %.2f%%, 가중평균 상여 지급률은 "
               "기본급 대비 %.1f%%로 추정된다. 개인별 실제 반영은 익월 급여부터 적용된다."
               % (avg_raise, avg_bonus)))

    f.append(P("5. 이의신청 접수", "h2"))
    f.append(K.table([
        ["구분", "건수"],
        ["접수", "%d건" % hf["appeal"]],
        ["인용", "%d건" % hf["upheld"]],
        ["기각", "%d건" % (hf["appeal"] - hf["upheld"])],
    ], [42*mm, 30*mm]))
    f.append(Spacer(1, 6))
    f.append(P("접수 %d건은 평가 대상 %d명 대비 %s 수준이다."
               % (hf["appeal"], hf["n"], pct(hf["appeal"], hf["n"]))))

    f.append(P("6. 차수별 추이", "h2"))
    rows = [["차수", "평가대상", "S", "A", "B", "C", "D", "보정변경", "이의신청"]]
    for row in D.HALVES:
        hh = D.half(row[0], row[1])
        mark = " ◀" if (row[0], row[1]) == (y, h) else ""
        rows.append(["%dH%d%s" % (row[0], row[1], mark), "%d" % hh["n"]] +
                    ["%d" % hh["dist"][g] for g in D.GRADES] +
                    ["%d" % hh["changed"], "%d" % hh["appeal"]])
    f.append(K.table(rows, [20*mm, 20*mm, 12*mm, 12*mm, 12*mm, 12*mm, 12*mm, 20*mm, 20*mm]))

    f.append(Spacer(1, 14))
    f.append(P("근거 문서: 「인사평가 운영지침」(HR-REG-001) 제6조·제9조·제11조·제12조·제10조, "
               "「급여규정」(HR-REG-003) 제8조·제9조", "note"))
    name = "%d %s 인사평가 결과 리포트.pdf" % (y, label)
    return name, K.build(OUT + name, name[:-4], D.COMPANY, f)


# ══════════════════════════════════════════════════════════════════
# 연간 인사운영 보고서
# ══════════════════════════════════════════════════════════════════
def annual_report(y):
    s = D.year_summary(y)
    qs = D.year_quarters(y)
    dept = D.dept_headcount(s["end"])
    f = []
    header(f, "%d년 연간 인사운영 보고서" % y,
           "%s 인사담당 · 대상기간 %d-01-01 ~ %d-12-31 · 배포 2026-08-26" % (D.COMPANY, y, y))

    f.append(P("1. 인력 현황 요약", "h2"))
    f.append(P("%d년 기초 인원은 %d명, 기말 인원은 %d명으로 순증 %d명이다. "
               "연간 채용 %d명, 퇴사 %d명이며 이 중 자발적 퇴사는 %d명이다."
               % (y, s["begin"], s["end"], s["end"] - s["begin"],
                  s["hire"], s["leave"], s["voluntary"])))
    f.append(P("기말 기준 본부별 재직 인원은 다음과 같다.", "body"))
    f.append(K.table([["본부", "재직 인원", "재직 비중"]] +
                     [[d, "%d명" % c, pct(c, s["end"])] for d, c in dept] +
                     [["계", "%d명" % s["end"], "100.0%"]],
                     [50*mm, 30*mm, 30*mm]))

    f.append(P("2. 분기별 인력 이동", "h2"))
    rows = [["분기", "기초", "채용", "퇴사", "기말", "자발퇴사"]]
    for q in qs:
        rows.append(["Q%d" % q["q"], "%d명" % q["base"], "%d명" % q["hire"],
                     "%d명" % q["leave"], "%d명" % q["end"], "%d명" % q["voluntary"]])
    rows.append(["계", "—", "%d명" % s["hire"], "%d명" % s["leave"], "—", "%d명" % s["voluntary"]])
    f.append(K.table(rows, [22*mm, 24*mm, 24*mm, 24*mm, 24*mm, 26*mm]))

    f.append(P("3. 이직률 및 퇴사 사유", "h2"))
    f.append(P("연평균 재직 인원 %.1f명 기준 자발적 이직률은 %.1f%%다. "
               "산식은 자발적 퇴사자 수를 연평균 재직 인원으로 나눈 값이다."
               % (s["avg_headcount"], s["turnover"])))
    prev = D.year_summary(y - 1) if y - 1 in (2024, 2025) else None
    if prev:
        diff = s["turnover"] - prev["turnover"]
        f.append(P("전년(%d년 %.1f%%) 대비 %+.1f%%p 변동했다."
                   % (prev["year"], prev["turnover"], diff)))
    reasons = D.attrition_reasons(s["voluntary"])
    f.append(K.table([["사유", "인원", "비중"]] +
                     [[r, "%d명" % c, pct(c, s["voluntary"])] for r, c in reasons],
                     [50*mm, 30*mm, 30*mm]))

    f.append(P("4. 수습 전환", "h2"))
    rows = [["분기", "입사", "정규 전환", "전환율"]]
    ti = tp = 0
    for q in qs:
        intake, passed = D.PROBATION[(y, q["q"])]
        ti += intake; tp += passed
        rows.append(["Q%d" % q["q"], "%d명" % intake, "%d명" % passed, pct(passed, intake)])
    rows.append(["계", "%d명" % ti, "%d명" % tp, pct(tp, ti)])
    f.append(K.table(rows, [24*mm, 28*mm, 30*mm, 28*mm]))
    f.append(Spacer(1, 6))
    f.append(P("전환 기준은 「인사평가 운영지침」 제10조(2024년은 제13조)의 30-60-90일 목표 "
               "달성 여부이며, 「취업규칙」 제13조에 따라 기준 미달 시 1회 1개월 연장이 "
               "가능하다.", "body"))

    f.append(P("5. 평가 차수 요약", "h2"))
    rows = [["차수", "평가 대상", "S", "A", "B", "C", "D", "이의신청"]]
    for h in (1, 2):
        hf = D.half(y, h)
        rows.append(["%dH%d" % (y, h), "%d명" % hf["n"]] +
                    ["%d" % hf["dist"][g] for g in D.GRADES] + ["%d건" % hf["appeal"]])
    f.append(K.table(rows, [22*mm, 24*mm, 14*mm, 14*mm, 14*mm, 14*mm, 14*mm, 22*mm]))

    f.append(P("6. 채용 퍼널 연간 집계", "h2"))
    fs = [D.FUNNEL[(y, q)] for q in (1, 2, 3, 4) if (y, q) in D.FUNNEL]
    if fs:
        tot = [sum(x) for x in zip(*fs)]
        f.append(K.table([["단계", "인원", "직전 단계 대비 통과율"]] + [
            ["지원", "%d명" % tot[0], "—"],
            ["서류통과", "%d명" % tot[1], pct(tot[1], tot[0])],
            ["면접진행", "%d명" % tot[2], pct(tot[2], tot[1])],
            ["최종합격", "%d명" % tot[3], pct(tot[3], tot[2])],
        ], [40*mm, 30*mm, 50*mm]))
    else:
        f.append(P("해당 연도 채용 퍼널 데이터는 분기 리포트 체계 도입(2025년) 이전으로 집계되지 않았다.", "body"))

    f.append(P("7. 제도 변경 이력", "h2"))
    ev = [(d, t) for d, t in D.TIMELINE if d.startswith(str(y))]
    if ev:
        f.append(K.table([["일자", "내용"]] + [[d, t] for d, t in ev], [28*mm, 118*mm]))
    else:
        f.append(P("해당 연도에 제도 변경 사항 없음."))

    f.append(Spacer(1, 14))
    f.append(P("근거 문서: 분기 채용·이직 리포트, 반기 인사평가 결과 리포트, 「급여규정」(HR-REG-003)", "note"))
    name = "%d 연간 인사운영 보고서.pdf" % y
    return name, K.build(OUT + name, name[:-4], D.COMPANY, f)


# ══════════════════════════════════════════════════════════════════
# 분기 채용·이직 리포트
# ══════════════════════════════════════════════════════════════════
def quarter_report(y, q):
    d = D.quarter(y, q)
    intake, passed = D.PROBATION[(y, q)]
    dept_h = D.dept_hires(y, q)
    reasons = D.attrition_reasons(d["voluntary"])
    f = []
    header(f, "%d년 %d분기 채용·이직 리포트" % (y, q),
           "%s 인사담당 · 대상기간 %d년 %d분기 · 배포 2026-08-26" % (D.COMPANY, y, q))

    f.append(P("1. 인력 이동", "h2"))
    f.append(K.table([
        ["구분", "인원"],
        ["기초 재직", "%d명" % d["base"]],
        ["채용", "%d명" % d["hire"]],
        ["퇴사", "%d명" % d["leave"]],
        ["— 자발적 퇴사", "%d명" % d["voluntary"]],
        ["— 비자발적 퇴사", "%d명" % (d["leave"] - d["voluntary"])],
        ["기말 재직", "%d명" % d["end"]],
    ], [50*mm, 30*mm]))
    f.append(Spacer(1, 6))
    f.append(P("분기 순증은 %+d명이다. 자발적 퇴사가 전체 퇴사의 %s를 차지한다."
               % (d["end"] - d["base"], pct(d["voluntary"], d["leave"]))))

    f.append(P("2. 채용 퍼널", "h2"))
    if (y, q) in D.FUNNEL:
        ap, doc, itv, hire = D.FUNNEL[(y, q)]
        f.append(K.table([
            ["단계", "인원", "직전 단계 대비 통과율"],
            ["지원", "%d명" % ap, "—"],
            ["서류통과", "%d명" % doc, pct(doc, ap)],
            ["면접진행", "%d명" % itv, pct(itv, doc)],
            ["최종합격", "%d명" % hire, pct(hire, itv)],
        ], [40*mm, 30*mm, 50*mm]))
        f.append(Spacer(1, 6))
        f.append(P("지원자 %d명 중 최종합격은 %d명으로 전체 전환율은 %s다."
                   % (ap, hire, pct(hire, ap))))
    else:
        f.append(P("해당 분기는 퍼널 집계 체계 도입 이전이다.", "body"))

    f.append(P("3. 본부별 채용 배분", "h2"))
    rows = [["본부", "채용"]] + [[dn, "%d명" % c] for dn, c in dept_h]
    rows.append(["계", "%d명" % d["hire"]])
    f.append(K.table(rows, [56*mm, 26*mm]))

    f.append(P("4. 자발적 퇴사 사유", "h2"))
    if d["voluntary"] > 0:
        f.append(K.table([["사유", "인원", "비중"]] +
                         [[r, "%d명" % c, pct(c, d["voluntary"])] for r, c in reasons],
                         [50*mm, 30*mm, 30*mm]))
    else:
        f.append(P("해당 분기 자발적 퇴사 없음.", "body"))

    f.append(P("5. 수습 전환", "h2"))
    f.append(P("당 분기 입사자 %d명 중 %d명이 수습을 통과해 정규 전환됐다(전환율 %s). "
               "수습평가는 30-60-90일 목표 달성 여부로 판단하며 등급 분포를 적용하지 않는다."
               % (intake, passed, pct(passed, intake))))
    if passed < intake:
        f.append(P("미전환 %d명의 사유는 수습평가 기준 미달이며, 「취업규칙」 제13조 제3항에 "
                   "따른 1개월 연장을 거친 뒤에도 기준에 미달한 경우다. 개별 면담 기록을 보존한다."
                   % (intake - passed)))

    f.append(Spacer(1, 14))
    f.append(P("근거 문서: 「취업규칙」(HR-REG-002) 제3장(채용·수습), 「인사평가 운영지침」(HR-REG-001) 제10조", "note"))
    name = "%d Q%d 채용이직 리포트.pdf" % (y, q)
    return name, K.build(OUT + name, name[:-4], D.COMPANY, f)


if __name__ == "__main__":
    errs = D.verify() + D.verify_ext()
    if errs:
        print("데이터 검증 실패:", errs); raise SystemExit(1)
    os.makedirs(OUT, exist_ok=True)
    made = []
    for yy, hh in [(r[0], r[1]) for r in D.HALVES]:
        made.append(half_report(yy, hh))
    for yy in (2024, 2025):
        made.append(annual_report(yy))
    for yy, qq in [(2025,1),(2025,2),(2025,3),(2025,4),(2026,1),(2026,2)]:
        made.append(quarter_report(yy, qq))
    for n, sz in made:
        print("  %7d B  %s" % (sz, n))
    print("PDF %d종 생성" % len(made))
