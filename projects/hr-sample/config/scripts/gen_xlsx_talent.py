# -*- coding: utf-8 -*-
"""「(주)나린테크 채용이직 분석(2024-2026)」 XLSX 워크북 생성기.

목적
----
`roster.py`가 만드는 개인 단위 로스터에는 분석 가능한 상관 신호가 의도적으로
심어져 있다(등급↔이직, 근속↔이직, 채널↔성과). 이 스크립트는 그 신호를
**워크북 위에서 눈으로 확인할 수 있는 형태**로 집계·시각화한다.

원칙
----
- 모든 수치는 `roster.py` / `data.py`에서 파생된다. 하드코딩된 결론 수치는 없다.
  README 시트의 서술 수치조차 집계 결과를 f-string으로 끼워 넣어 만든다.
- `roster.py`와 `data.py`는 **읽기 전용**이다. import만 하고 수정하지 않는다.
- 스크립트 끝의 검증 블록이 통과하지 못하면 워크북을 저장하지 않는다.

시트 구성
--------
1. 채용퍼널        — 분기별 지원→서류→면접→합격 전환율 (data.FUNNEL)
2. 채널별성과      — 채용 채널이 수습통과·성과등급·잔존으로 이어지는 경로 [핵심]
3. 등급별잔존      — 평가 등급과 자발 이직의 관계                        [핵심]
4. 근속별이직      — 근속 구간과 자발 이직의 관계                        [핵심]
5. 퇴사사유분석    — 실제 term_reason 값 집계
6. 분기별인력이동  — 로스터 실집계 vs data.QUARTERS 교차 검증
7. README          — 시트 설명, 확인 가능한 상관관계, 재현 방법, 고지

실행
----
    cd <이 파일이 있는 디렉터리>
    python gen_xlsx_talent.py
"""

import os
import sys
from collections import Counter, OrderedDict

from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

# roster / data 는 이 스크립트와 같은 디렉터리에 있다 (읽기 전용으로만 사용)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import data as D            # noqa: E402
import roster as R          # noqa: E402


# ══════════════════════════════════════════════════════════════════
# § 출력 경로
# ══════════════════════════════════════════════════════════════════
OUT_DIR = os.path.expanduser("~/Documents/hr-samples")
OUT_NAME = "나린테크 채용이직 분석(2024-2026).xlsx"
OUT_PATH = os.path.join(OUT_DIR, OUT_NAME)

# 근속 기준일 — roster.tenure_years 의 기본 asof 와 동일하게 2026-Q2 기말로 고정
ASOF_LABEL = "2026-06-30"


# ══════════════════════════════════════════════════════════════════
# § 서식 상수 — 워크북 전체가 같은 시각 언어를 쓰도록 한 곳에 모은다
# ══════════════════════════════════════════════════════════════════
FMT_INT = '#,##0'            # 인원·건수
FMT_PCT = '0.0"%"'           # 백분율 — 값은 26.9 처럼 저장하고 서식으로 % 를 붙인다
FMT_SCORE = '0.00'           # 등급점수 (S=4 … D=0)
FMT_YEAR = '0.00'            # 근속 연수 — 1자리로는 그룹 간 차이가 뭉개져 2자리로 둔다

FILL_HEADER = PatternFill("solid", fgColor="1F3864")   # 진남색 헤더
FILL_TITLE = PatternFill("solid", fgColor="D9E2F3")    # 연한 파랑 타이틀
FILL_KEY = PatternFill("solid", fgColor="FFF2CC")      # 핵심 시트 강조(노랑)
FILL_SUB = PatternFill("solid", fgColor="EDEDED")      # 보조 표 헤더(회색)

FONT_HEADER = Font(bold=True, color="FFFFFF", size=10)
FONT_TITLE = Font(bold=True, size=13, color="1F3864")
FONT_NOTE = Font(italic=True, size=9, color="808080")
FONT_TOTAL = Font(bold=True)
FONT_SUBHEAD = Font(bold=True, size=10, color="1F3864")

THIN = Side(style="thin", color="B4C6E7")
MEDIUM = Side(style="medium", color="1F3864")
BORDER_CELL = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
BORDER_TOTAL = Border(left=THIN, right=THIN, top=MEDIUM, bottom=THIN)

CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)
LEFT = Alignment(horizontal="left", vertical="center")


# ══════════════════════════════════════════════════════════════════
# § 공통 유틸
# ══════════════════════════════════════════════════════════════════
def pct(part, whole):
    """백분율. 분모가 0이면 0.0 — 빈 그룹에서 ZeroDivision 으로 죽지 않게."""
    return round(part / whole * 100, 1) if whole else 0.0


def avg(values, nd=2):
    return round(sum(values) / len(values), nd) if values else 0.0


def graded(people):
    """평가 등급을 한 번이라도 받은 사람만.

    `roster._grade_score`는 등급 이력이 없으면 기본 2(=B)를 돌려준다. 첫 평가 전에
    나간 사람까지 평균에 넣으면 존재하지 않는 B 등급이 섞여 신호가 흐려지므로,
    평균 등급점수 계산에서는 등급 보유자만 대상으로 한다.
    """
    return [p for p in people if p["grades"]]


def final_grade(p):
    """최종 등급(가장 최근 평가 차수의 등급). 등급이 없으면 None."""
    if not p["grades"]:
        return None
    return p["grades"][sorted(p["grades"])[-1]]


def avg_score(people):
    """평균 등급점수 — 등급 보유자만 대상으로 `roster._grade_score` 평균.

    등급 보유자가 한 명도 없으면 0.0 대신 None 을 돌려준다. 0.0 은 D등급(=0점)과
    구분되지 않아 '수습 미전환자 전원이 D등급'처럼 읽히기 때문이다. None 은 셀에
    빈 값으로 기록되고, 시트 주석에서 '해당 없음'임을 밝힌다.
    """
    g = graded(people)
    if not g:
        return None
    return avg([R._grade_score(p) for p in g])


def avg_tenure(people):
    return avg([R.tenure_years(p) for p in people], nd=2)


def count_type(people, ttype):
    return sum(1 for p in people if p["term_type"] == ttype)


def top_dept(people):
    """그룹 내 최다 본부 — '본부명(건수)' 문자열."""
    if not people:
        return "-"
    dept, n = Counter(p["dept"] for p in people).most_common(1)[0]
    return "%s(%d)" % (dept, n)


# ══════════════════════════════════════════════════════════════════
# § 시트 뼈대 헬퍼 — 타이틀/주석/헤더/데이터/합계 를 일관되게 찍는다
# ══════════════════════════════════════════════════════════════════
def sheet_head(ws, title, note, headers, key=False, header_row=3):
    """1행 타이틀, 2행 주석, `header_row`행 헤더를 찍고 헤더 행 번호를 돌려준다."""
    ncol = len(headers)
    last_letter = get_column_letter(ncol)

    ws.cell(row=1, column=1, value=title).font = FONT_TITLE
    for c in range(1, ncol + 1):
        ws.cell(row=1, column=c).fill = FILL_KEY if key else FILL_TITLE
    ws.merge_cells("A1:%s1" % last_letter)
    ws.cell(row=1, column=1).alignment = LEFT

    ws.cell(row=2, column=1, value=note).font = FONT_NOTE
    ws.merge_cells("A2:%s2" % last_letter)
    ws.cell(row=2, column=1).alignment = LEFT

    for c, h in enumerate(headers, start=1):
        cell = ws.cell(row=header_row, column=c, value=h)
        cell.font = FONT_HEADER
        cell.fill = FILL_HEADER
        cell.alignment = CENTER
        cell.border = BORDER_CELL
    ws.row_dimensions[header_row].height = 30
    return header_row


def write_rows(ws, start_row, rows, formats, total_row=False):
    """데이터 행 기록. `formats`는 열 인덱스(0-base) → 숫자서식 매핑."""
    r = start_row
    for row in rows:
        for c, v in enumerate(row, start=1):
            cell = ws.cell(row=r, column=c, value=v)
            cell.border = BORDER_CELL
            if c - 1 in formats:
                cell.number_format = formats[c - 1]
            cell.alignment = LEFT if c == 1 else CENTER
        r += 1
    if total_row:
        for c in range(1, len(rows[-1]) + 1):
            cell = ws.cell(row=r - 1, column=c)
            cell.font = FONT_TOTAL
            cell.border = BORDER_TOTAL
    return r


def finish(ws, header_row, last_row, widths, autofilter=True):
    """열 너비·틀고정·자동필터 마무리."""
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = ws.cell(row=header_row + 1, column=2)
    if autofilter:
        ws.auto_filter.ref = "A%d:%s%d" % (header_row, get_column_letter(len(widths)), last_row)


def add_bar(ws, anchor, title, y_title, cat_ref, data_refs, fmt=FMT_PCT, height=8, width=16):
    """막대 차트 삽입.

    cat_ref  : (min_col, min_row, max_row) — 카테고리(축 라벨) 범위
    data_refs: [(col, header_row, max_row), ...] — 계열 범위 (헤더 포함)
    """
    ch = BarChart()
    ch.type = "col"
    ch.style = 10
    ch.title = title
    ch.y_axis.title = y_title
    ch.y_axis.numFmt = fmt
    ch.height = height
    ch.width = width
    ch.gapWidth = 60

    cats = Reference(ws, min_col=cat_ref[0], min_row=cat_ref[1], max_row=cat_ref[2])
    for col, hr, mr in data_refs:
        ch.add_data(Reference(ws, min_col=col, min_row=hr, max_row=mr), titles_from_data=True)
    ch.set_categories(cats)
    ws.add_chart(ch, anchor)
    return ch


# ══════════════════════════════════════════════════════════════════
# § 집계 — 시트별 행 데이터를 순수 함수로 만들어 검증 블록에서 재사용한다
# ══════════════════════════════════════════════════════════════════
FUNNEL_KEYS = [(2025, 1), (2025, 2), (2025, 3), (2025, 4), (2026, 1), (2026, 2)]


def agg_funnel():
    """시트1 — 분기별 채용 퍼널 (data.FUNNEL)."""
    rows = []
    tot = [0, 0, 0, 0]
    for (y, q) in FUNNEL_KEYS:
        appl, doc, itv, fin = D.FUNNEL[(y, q)]
        rows.append(["%d-Q%d" % (y, q), appl, doc, pct(doc, appl), itv,
                     pct(itv, doc), fin, pct(fin, itv), pct(fin, appl)])
        tot = [tot[0] + appl, tot[1] + doc, tot[2] + itv, tot[3] + fin]
    a, b, c, f = tot
    rows.append(["합계", a, b, pct(b, a), c, pct(c, b), f, pct(f, c), pct(f, a)])
    return rows


def agg_channel(people):
    """시트2 — 채용 채널별 성과·잔존. 신입(seeded=False)만 대상."""
    newbies = [p for p in people if not p["seeded"]]
    rows = []
    for ch, _, _, _ in R.CHANNELS:
        grp = [p for p in newbies if p["channel"] == ch]
        passed = sum(1 for p in grp if p["probation_passed"])
        g = graded(grp)
        sa = sum(1 for p in g if final_grade(p) in ("S", "A"))
        vol = count_type(grp, "자발")
        rows.append([ch, len(grp), passed, pct(passed, len(grp)), avg_score(grp),
                     pct(sa, len(g)), vol, pct(vol, len(grp)), avg_tenure(grp)])
    # 합계 행 — 비율은 행 합이 아니라 전체 모집단에서 다시 계산한다
    passed = sum(1 for p in newbies if p["probation_passed"])
    g = graded(newbies)
    sa = sum(1 for p in g if final_grade(p) in ("S", "A"))
    vol = count_type(newbies, "자발")
    rows.append(["합계", len(newbies), passed, pct(passed, len(newbies)),
                 avg_score(newbies), pct(sa, len(g)), vol,
                 pct(vol, len(newbies)), avg_tenure(newbies)])
    return rows, newbies


def agg_grade_experienced(people):
    """시트3 주표 — 등급 '경험자' 기준.

    한 사람이 여러 반기에 걸쳐 서로 다른 등급을 받으면 여러 행에 중복 계상된다
    (연인원). 그래서 이 표에는 합계 행을 두지 않고, 중복 없는 확인은 아래
    `agg_grade_final()`(최종등급 기준, 1인 1행)이 맡는다. 두 기준 모두 README에
    명시한다.
    """
    rows = []
    for g in D.GRADES:
        grp = [p for p in people if g in p["grades"].values()]
        stay = sum(1 for p in grp if p["term_date"] is None)
        vol = count_type(grp, "자발")
        invol = count_type(grp, "비자발")
        rows.append([g, len(grp), stay, vol, invol, pct(vol, len(grp)), avg_tenure(grp)])
    return rows


def agg_grade_final(people):
    """시트3 보조표 — 최종등급 기준. 1인 1행이므로 합계가 전체 인원과 정확히 일치."""
    rows = []
    for g in D.GRADES + [None]:
        grp = [p for p in people if final_grade(p) == g]
        stay = sum(1 for p in grp if p["term_date"] is None)
        vol = count_type(grp, "자발")
        invol = count_type(grp, "비자발")
        label = g if g else "미평가(첫 평가 전 퇴사)"
        rows.append([label, len(grp), stay, vol, invol, pct(vol, len(grp)), avg_tenure(grp)])
    stay = sum(1 for p in people if p["term_date"] is None)
    rows.append(["합계", len(people), stay, count_type(people, "자발"),
                 count_type(people, "비자발"),
                 pct(count_type(people, "자발"), len(people)), avg_tenure(people)])
    return rows


TENURE_BUCKETS = OrderedDict([
    ("1년 미만", (0.0, 1.0)),
    ("1~2.5년", (1.0, 2.5)),
    ("2.5~5년", (2.5, 5.0)),
    ("5~10년", (5.0, 10.0)),
    ("10년 이상", (10.0, 999.0)),
])


def agg_tenure(people):
    """시트4 — 근속 구간별 이직. 근속은 퇴사자는 퇴사일, 재직자는 기준일까지."""
    rows = []
    for label, (lo, hi) in TENURE_BUCKETS.items():
        grp = [p for p in people if lo <= R.tenure_years(p) < hi]
        vol = count_type(grp, "자발")
        invol = count_type(grp, "비자발")
        rows.append([label, len(grp), vol, pct(vol, len(grp)), invol, avg_score(grp)])
    vol = count_type(people, "자발")
    rows.append(["합계", len(people), vol, pct(vol, len(people)),
                 count_type(people, "비자발"), avg_score(people)])
    return rows


def agg_reasons(people):
    """시트5 — 실제 term_reason 값 집계 (자발·비자발 모두)."""
    leavers = [p for p in people if p["term_reason"]]
    total = len(leavers)
    # 자발 사유를 먼저, 그 안에서는 건수 내림차순으로 정렬해 읽기 쉽게
    reasons = sorted(set(p["term_reason"] for p in leavers),
                     key=lambda r: (0 if any(p["term_type"] == "자발" for p in leavers
                                             if p["term_reason"] == r) else 1,
                                    -sum(1 for p in leavers if p["term_reason"] == r)))
    rows = []
    for rsn in reasons:
        grp = [p for p in leavers if p["term_reason"] == rsn]
        rows.append([rsn, len(grp), pct(len(grp), total), avg_tenure(grp),
                     avg_score(grp), top_dept(grp)])
    rows.append(["합계", total, 100.0, avg_tenure(leavers), avg_score(leavers),
                 top_dept(leavers)])
    return rows, leavers


def agg_quarters(people):
    """시트6 — 로스터에서 실집계한 분기별 인력 이동.

    기초 인원은 두 가지 방식으로 구한다.
      (a) 연쇄식: 직전 분기 기말 + 채용 - 퇴사
      (b) 날짜식: 분기 시작일 이전 입사 & 분기 시작일 이후 퇴사(또는 재직)
    둘과 data.QUARTERS 가 모두 일치해야 한다 (검증 블록에서 확인).
    """
    rows = []
    base = sum(1 for p in people if p["seeded"])     # 기초 인원 = 2024-Q1 이전 입사자
    for (y, q, d_base, d_hire, d_leave, d_vol) in D.QUARTERS:
        hire = sum(1 for p in people if p["hire_quarter"] == (y, q))
        term = [p for p in people if p["term_quarter"] == (y, q)]
        vol = sum(1 for p in term if p["term_type"] == "자발")
        invol = sum(1 for p in term if p["term_type"] == "비자발")
        end = base + hire - len(term)
        avg_hc = (base + end) / 2.0
        rows.append(["%d-Q%d" % (y, q), base, hire, len(term), vol, invol, end,
                     end - base, pct(vol, avg_hc)])
        base = end
    # 합계 — 기초는 첫 분기, 기말은 마지막 분기 값을 그대로 쓴다
    first_base = sum(1 for p in people if p["seeded"])
    t_hire = sum(r[2] for r in rows)
    t_term = sum(r[3] for r in rows)
    t_vol = sum(r[4] for r in rows)
    t_invol = sum(r[5] for r in rows)
    last_end = rows[-1][6]
    avg_hc = sum((r[1] + r[6]) / 2.0 for r in rows) / len(rows)
    rows.append(["합계(10개 분기)", first_base, t_hire, t_term, t_vol, t_invol,
                 last_end, last_end - first_base, pct(t_vol, avg_hc)])
    return rows


def base_by_date(people, y, q):
    """분기 시작일 기준 재직 인원 — 연쇄식 기초 인원의 독립 교차 검증용."""
    qs = R._quarter_start(y, q)
    return sum(1 for p in people
               if p["hire_date"] < qs and (p["term_date"] is None or p["term_date"] >= qs))


# ══════════════════════════════════════════════════════════════════
# § 시트 생성
# ══════════════════════════════════════════════════════════════════
def sheet_funnel(wb):
    ws = wb.create_sheet("채용퍼널")
    headers = ["분기", "지원자", "서류통과", "서류통과율(%)", "면접진행",
               "면접전환율(%)", "최종합격", "합격전환율(%)", "전체전환율(%)"]
    hr = sheet_head(
        ws, "분기별 채용 퍼널 (2025-Q1 ~ 2026-Q2)",
        "출처: data.FUNNEL. 각 전환율은 직전 단계 대비이며, 전체전환율만 지원자 대비다. "
        "최종합격 인원은 data.QUARTERS 의 분기 채용 인원과 동일하다.",
        headers)
    rows = agg_funnel()
    fmts = {1: FMT_INT, 2: FMT_INT, 3: FMT_PCT, 4: FMT_INT, 5: FMT_PCT,
            6: FMT_INT, 7: FMT_PCT, 8: FMT_PCT}
    last = write_rows(ws, hr + 1, rows, fmts, total_row=True) - 1
    finish(ws, hr, last, [16, 11, 11, 14, 11, 14, 11, 14, 14])
    return ws, len(rows)


def sheet_channel(wb, people):
    ws = wb.create_sheet("채널별성과")
    headers = ["채용채널", "채용인원", "수습통과", "수습통과율(%)", "평균등급점수",
               "S+A 비율(%)", "자발퇴사", "자발이직률(%)", "평균근속(년)"]
    hr = sheet_head(
        ws, "[핵심] 채용 채널별 입사 후 성과·잔존",
        "대상: 2024-Q1 이후 입사한 신입만 (기초 인원은 채널 정보가 없다). "
        "평균등급점수는 등급 보유자의 최종등급 점수 평균(S=4·A=3·B=2·C=1·D=0), "
        "S+A 비율은 등급 보유자 중 최종등급이 S 또는 A 인 비율. 근속 기준일 %s. "
        "신입은 관측 창이 최대 2.5년이라 평균근속의 절대값은 짧다 — 채널 간 비교로만 읽는다."
        % ASOF_LABEL,
        headers, key=True)
    rows, newbies = agg_channel(people)
    fmts = {1: FMT_INT, 2: FMT_INT, 3: FMT_PCT, 4: FMT_SCORE, 5: FMT_PCT,
            6: FMT_INT, 7: FMT_PCT, 8: FMT_YEAR}
    last = write_rows(ws, hr + 1, rows, fmts, total_row=True) - 1
    finish(ws, hr, last, [16, 11, 11, 14, 14, 13, 11, 14, 13])

    data_last = last - 1          # 합계 행 제외
    add_bar(ws, "K3", "채널별 평균 등급점수 (S=4 … D=0)", "평균등급점수",
            (1, hr + 1, data_last), [(5, hr, data_last)], fmt=FMT_SCORE)
    add_bar(ws, "K20", "채널별 수습통과율 · 자발이직률", "비율(%)",
            (1, hr + 1, data_last), [(4, hr, data_last), (8, hr, data_last)])
    return ws, len(rows), newbies


def sheet_grade(wb, people):
    ws = wb.create_sheet("등급별잔존")
    headers = ["최종등급", "인원", "재직", "자발퇴사", "비자발퇴사",
               "자발이직률(%)", "평균근속(년)"]
    hr = sheet_head(
        ws, "[핵심] 평가 등급별 잔존·이직",
        "주표는 '등급 경험자' 기준 — 해당 등급을 한 번이라도 받은 사람을 센다. "
        "한 사람이 반기마다 다른 등급을 받을 수 있어 연인원이며 합계는 중복 계상되므로 "
        "합계 행을 두지 않는다. 중복 없는 집계는 아래 보조표(최종등급 기준)를 본다.",
        headers, key=True)
    rows = agg_grade_experienced(people)
    fmts = {1: FMT_INT, 2: FMT_INT, 3: FMT_INT, 4: FMT_INT, 5: FMT_PCT, 6: FMT_YEAR}
    last = write_rows(ws, hr + 1, rows, fmts, total_row=False) - 1
    finish(ws, hr, last, [22, 11, 11, 12, 13, 15, 13])

    add_bar(ws, "I3", "등급별 자발 이직률 — S에서 D로 갈수록 상승", "자발이직률(%)",
            (1, hr + 1, last), [(6, hr, last)])

    # ── 보조표: 최종등급 기준 (1인 1행, 중복 없음) ──
    sub = last + 3
    ws.cell(row=sub, column=1,
            value="※ 보조표 — 최종등급 기준 (1인 1행, 중복 없음). 합계가 전체 인원과 일치한다.")
    ws.cell(row=sub, column=1).font = FONT_SUBHEAD
    subhr = sub + 1
    for c, h in enumerate(headers, start=1):
        cell = ws.cell(row=subhr, column=c, value=h)
        cell.font = Font(bold=True, size=10, color="1F3864")
        cell.fill = FILL_SUB
        cell.alignment = CENTER
        cell.border = BORDER_CELL
    sub_rows = agg_grade_final(people)
    sub_last = write_rows(ws, subhr + 1, sub_rows, fmts, total_row=True) - 1
    return ws, len(rows), len(sub_rows), sub_rows


def sheet_tenure(wb, people):
    ws = wb.create_sheet("근속별이직")
    headers = ["근속구간", "인원", "자발퇴사", "자발이직률(%)", "비자발퇴사", "평균등급점수"]
    hr = sheet_head(
        ws, "[핵심] 근속 구간별 이직",
        "근속은 퇴사자는 입사일→퇴사일, 재직자는 입사일→%s. "
        "평균등급점수는 등급 보유자의 최종등급 점수 평균(S=4 … D=0)." % ASOF_LABEL,
        headers, key=True)
    rows = agg_tenure(people)
    fmts = {1: FMT_INT, 2: FMT_INT, 3: FMT_PCT, 4: FMT_INT, 5: FMT_SCORE}
    last = write_rows(ws, hr + 1, rows, fmts, total_row=True) - 1
    finish(ws, hr, last, [16, 11, 12, 15, 13, 14])

    data_last = last - 1
    add_bar(ws, "H3", "근속 구간별 자발 이직률 — 1~2.5년 구간이 피크", "자발이직률(%)",
            (1, hr + 1, data_last), [(4, hr, data_last)])
    return ws, len(rows)


def sheet_reasons(wb, people):
    ws = wb.create_sheet("퇴사사유분석")
    headers = ["퇴사사유", "건수", "비중(%)", "평균근속(년)", "평균등급점수", "주요본부"]
    hr = sheet_head(
        ws, "퇴사 사유별 분석 (자발·비자발 전체)",
        "roster.py 가 실제로 부여한 term_reason 값을 그대로 집계했다. "
        "자발 사유를 먼저 배치하고 그 안에서 건수 내림차순으로 정렬했다. "
        "주요본부는 해당 사유의 최다 본부와 그 건수. "
        "평균등급점수가 빈 칸이면 그 사유의 퇴사자가 전원 첫 평가 전에 나가 등급 이력이 "
        "없다는 뜻이다 (0점=D등급과 구분하기 위해 비워 둔다).",
        headers)
    rows, leavers = agg_reasons(people)
    fmts = {1: FMT_INT, 2: FMT_PCT, 3: FMT_YEAR, 4: FMT_SCORE}
    last = write_rows(ws, hr + 1, rows, fmts, total_row=True) - 1
    finish(ws, hr, last, [22, 10, 12, 14, 14, 20])
    return ws, len(rows), leavers


def sheet_movement(wb, people):
    ws = wb.create_sheet("분기별인력이동")
    headers = ["분기", "기초", "채용", "퇴사", "자발", "비자발", "기말", "순증",
               "분기이직률(%)"]
    hr = sheet_head(
        ws, "분기별 인력 이동 (2024-Q1 ~ 2026-Q2)",
        "모든 값은 개인 로스터에서 직접 집계했으며, data.QUARTERS 와 전부 일치함을 "
        "생성 시 검증했다. 분기이직률 = 자발퇴사 ÷ 평균인원((기초+기말)/2) × 100 "
        "— data.year_summary() 의 이직률 정의와 같다(연환산 아님).",
        headers)
    rows = agg_quarters(people)
    fmts = {1: FMT_INT, 2: FMT_INT, 3: FMT_INT, 4: FMT_INT, 5: FMT_INT,
            6: FMT_INT, 7: FMT_INT, 8: FMT_PCT}
    last = write_rows(ws, hr + 1, rows, fmts, total_row=True) - 1
    finish(ws, hr, last, [18, 10, 10, 10, 10, 10, 10, 10, 15])
    return ws, len(rows)


def sheet_readme(wb, ctx):
    """README — 시트 설명 + 확인 가능한 상관관계(실측치) + 재현 방법 + 고지."""
    ws = wb.create_sheet("README")
    ws.column_dimensions["A"].width = 22
    ws.column_dimensions["B"].width = 108

    r = [1]

    def title(text):
        ws.cell(row=r[0], column=1, value=text).font = FONT_TITLE
        ws.cell(row=r[0], column=1).fill = FILL_TITLE
        ws.cell(row=r[0], column=2).fill = FILL_TITLE
        r[0] += 2

    def head(text):
        ws.cell(row=r[0], column=1, value=text).font = FONT_SUBHEAD
        ws.cell(row=r[0], column=1).fill = FILL_KEY
        ws.cell(row=r[0], column=2).fill = FILL_KEY
        r[0] += 1

    def line(a, b=""):
        ws.cell(row=r[0], column=1, value=a).font = Font(bold=bool(a), size=10)
        ws.cell(row=r[0], column=1).alignment = Alignment(vertical="top")
        c = ws.cell(row=r[0], column=2, value=b)
        c.alignment = Alignment(vertical="top", wrap_text=True)
        r[0] += 1

    def blank():
        r[0] += 1

    title("(주)나린테크 채용이직 분석 (2024-2026) — README")
    line("생성일", "2026-08-26 기준 스냅샷 / 근속 기준일 %s" % ASOF_LABEL)
    line("모집단", "전체 %d명 (기초 인원 %d명 + 2024-Q1 이후 신입 %d명), "
                   "기말 재직 %d명, 퇴사 %d명"
         % (ctx["n_all"], ctx["n_seeded"], ctx["n_new"], ctx["n_active"], ctx["n_left"]))
    blank()

    head("■ 시트 구성")
    line("채용퍼널", "2025-Q1~2026-Q2 6개 분기의 지원→서류→면접→최종합격 전환율. "
                    "출처는 data.FUNNEL 이고 최종합격 인원은 분기 채용 인원과 같다.")
    line("채널별성과", "[핵심] 채용 채널 5종별 수습통과율·평균등급점수·S+A 비율·"
                      "자발이직률·평균근속. 신입 %d명만 대상." % ctx["n_new"])
    line("등급별잔존", "[핵심] 평가 등급과 이직의 관계. 주표는 등급 경험자 기준(연인원), "
                      "보조표는 최종등급 기준(1인 1행).")
    line("근속별이직", "[핵심] 근속 5개 구간별 자발/비자발 이직과 평균 등급점수.")
    line("퇴사사유분석", "roster.py 가 부여한 실제 term_reason %d종의 건수·비중·"
                        "평균근속·평균등급점수·주요본부." % ctx["n_reasons"])
    line("분기별인력이동", "10개 분기의 기초/채용/퇴사/자발/비자발/기말/순증/분기이직률. "
                          "로스터 실집계이며 data.QUARTERS 와 전량 대조 검증했다.")
    blank()

    head("■ 이 데이터셋에서 확인 가능한 상관관계")
    line("① 등급 ↔ 이직", ctx["corr_grade"])
    line("", ctx["corr_grade_detail"])
    line("② 근속 ↔ 이직", ctx["corr_tenure"])
    line("", ctx["corr_tenure_detail"])
    line("③ 채널 ↔ 성과", ctx["corr_channel"])
    line("", ctx["corr_channel_detail"])
    blank()

    head("■ 집계 기준 (해석 시 주의)")
    line("등급 경험자 기준",
         "등급별잔존 주표는 '해당 등급을 한 번이라도 받은 사람'을 센다. 한 사람이 반기마다 "
         "다른 등급을 받으면 여러 행에 중복 계상되므로 인원 합(%d명)이 전체 인원(%d명)보다 "
         "크다. 이는 의도된 연인원 집계이며, 그래서 주표에는 합계 행을 두지 않았다."
         % (ctx["grade_exp_sum"], ctx["n_all"]))
    line("최종등급 기준",
         "같은 시트의 보조표는 가장 최근 평가 차수의 등급으로 1인 1행만 센다. 첫 평가 전에 "
         "퇴사해 등급이 없는 %d명은 '미평가' 행으로 분리했고, 합계 %d명은 전체 인원과 "
         "정확히 일치한다." % (ctx["n_ungraded"], ctx["n_all"]))
    line("평균등급점수",
         "roster._grade_score(S=4·A=3·B=2·C=1·D=0)를 최종등급에 적용한 값의 평균. "
         "이 함수는 등급 이력이 없으면 기본 2(=B)를 돌려주므로, 존재하지 않는 B가 섞이지 "
         "않도록 등급 보유자만 평균 대상으로 삼았다.")
    line("근속(년)",
         "퇴사자는 입사일→퇴사일, 재직자는 입사일→%s. roster.tenure_years() 와 동일."
         % ASOF_LABEL)
    line("분기이직률",
         "자발퇴사 ÷ 평균인원((기초+기말)/2) × 100. data.year_summary() 의 이직률 정의와 "
         "같으며 연환산하지 않은 분기 실측치다.")
    blank()

    head("■ 데이터 출처와 재현 방법")
    line("단일 진실원", "data.py — 분기별 인력 이동(QUARTERS), 반기 등급 분포(HALVES), "
                       "수습 전환(PROBATION), 채용 퍼널(FUNNEL), 부서 배분(DEPT_SHARE).")
    line("개인 로스터", "roster.py — data.py 의 집계 수치를 정확히 재현하는 개인 레코드를 "
                       "결정론적으로 생성한다. seed = %d (roster.SEED). 같은 seed면 "
                       "언제 실행해도 같은 로스터가 나온다." % R.SEED)
    line("생성 스크립트", "projects/hr-sample/config/scripts/gen_xlsx_talent.py")
    line("재현 절차", "1) 위 scripts 디렉터리로 이동  "
                     "2) openpyxl 이 설치된 파이썬으로 `python gen_xlsx_talent.py` 실행  "
                     "3) ~/Documents/hr-samples/ 아래에 같은 파일이 다시 만들어진다. "
                     "스크립트 내장 검증(분기 집계 대조·인원 합계·신호 단조성)이 하나라도 "
                     "실패하면 파일을 저장하지 않는다.")
    line("검증 결과", ctx["verify_summary"])
    blank()

    head("■ 고지")
    line("가상 목업 데이터",
         "%s 본 워크북의 회사명·조직·인원·평가 등급·퇴사 사유는 지식관리 파이프라인 검증을 "
         "위해 생성한 가상 목업 데이터이며, 실존하는 기업·단체·인물과 아무런 관련이 없다. "
         "실제 인사 의사결정의 근거로 사용해서는 안 된다." % D.FIXTURE_NOTE)

    ws.freeze_panes = "A2"
    return ws, r[0] - 1


# ══════════════════════════════════════════════════════════════════
# § 검증 — 실패하면 예외를 던져 저장 자체를 막는다
# ══════════════════════════════════════════════════════════════════
def run_verification(people, active, ch_rows, newbies, grade_rows, grade_final_rows,
                     tenure_rows, qrows, reason_rows, leavers):
    out = []      # 화면 출력 줄
    errs = []     # 치명적 불일치

    def ok(cond, msg):
        out.append("  [%s] %s" % ("OK " if cond else "FAIL", msg))
        if not cond:
            errs.append(msg)

    out.append("── 1. roster.py 자체 검증 ──")
    r_errs, got, want = R.verify(people, active)
    ok(not r_errs, "roster.verify() 통과 (%s)" % ("이상 없음" if not r_errs else r_errs[:3]))
    d_errs = D.verify() + D.verify_ext()
    ok(not d_errs, "data.verify()/verify_ext() 통과")

    out.append("── 2. 시트6 분기 집계 vs data.QUARTERS 전량 대조 ──")
    mism = []
    for i, (y, q, d_base, d_hire, d_leave, d_vol) in enumerate(D.QUARTERS):
        row = qrows[i]
        d_invol = d_leave - d_vol
        d_end = d_base + d_hire - d_leave
        checks = [("기초", row[1], d_base), ("채용", row[2], d_hire),
                  ("퇴사", row[3], d_leave), ("자발", row[4], d_vol),
                  ("비자발", row[5], d_invol), ("기말", row[6], d_end),
                  ("기초(날짜식)", base_by_date(people, y, q), d_base)]
        for name, a, b in checks:
            if a != b:
                mism.append("%d-Q%d %s %s != %s" % (y, q, name, a, b))
    ok(not mism, "10개 분기 × 7개 항목(기초·채용·퇴사·자발·비자발·기말·기초날짜식) "
                 "= 70개 대조 전부 일치" if not mism else "불일치 %s" % mism[:5])
    ok(qrows[-1][6] == len(active),
       "최종 기말 %d명 == 재직자 수 %d명" % (qrows[-1][6], len(active)))
    ok(qrows[-1][2] == len(newbies),
       "분기 채용 합계 %d명 == 신입 총원 %d명" % (qrows[-1][2], len(newbies)))

    out.append("── 3. 시트2 채널 집계 ──")
    ch_sum = sum(r[1] for r in ch_rows[:-1])
    ok(ch_sum == len(newbies) == ch_rows[-1][1],
       "채널별 채용인원 합 %d == 합계 행 %d == 신입 총원 %d"
       % (ch_sum, ch_rows[-1][1], len(newbies)))
    ok(len(ch_rows) - 1 == len(R.CHANNELS),
       "채널 행 %d개 == roster.CHANNELS %d개" % (len(ch_rows) - 1, len(R.CHANNELS)))
    ok(all(p["channel"] for p in newbies), "신입 전원이 채널 정보를 보유")
    ok(sum(r[6] for r in ch_rows[:-1]) == ch_rows[-1][6],
       "채널별 자발퇴사 합 %d == 합계 행 %d" % (sum(r[6] for r in ch_rows[:-1]),
                                              ch_rows[-1][6]))

    out.append("── 4. 시트3 인원 합계 (중복 계상 여부) ──")
    exp_sum = sum(r[1] for r in grade_rows)
    out.append("  [INFO] 등급 경험자 기준 합 %d명 (전체 %d명 대비 +%d명 중복 — 연인원, "
               "README 명시)" % (exp_sum, len(people), exp_sum - len(people)))
    fin_sum = sum(r[1] for r in grade_final_rows[:-1])
    ok(fin_sum == len(people) == grade_final_rows[-1][1],
       "최종등급 기준 보조표 합 %d == 전체 인원 %d (중복 없음)" % (fin_sum, len(people)))
    ok(sum(r[2] for r in grade_final_rows[:-1]) == len(active),
       "보조표 재직 합 %d == 재직자 %d" % (sum(r[2] for r in grade_final_rows[:-1]),
                                          len(active)))

    out.append("── 5. 시트4 근속 구간 ──")
    t_sum = sum(r[1] for r in tenure_rows[:-1])
    ok(t_sum == len(people) == tenure_rows[-1][1],
       "근속 구간 인원 합 %d == 전체 인원 %d (구간 누락·중복 없음)" % (t_sum, len(people)))
    peak = max(tenure_rows[:-1], key=lambda r: r[3])
    ok(peak[0] == "1~2.5년",
       "자발이직률 피크 구간 = %s (%.1f%%) — 기대값 1~2.5년" % (peak[0], peak[3]))

    out.append("── 6. 시트5 퇴사 사유 ──")
    rs = sum(r[1] for r in reason_rows[:-1])
    ok(rs == len(leavers) == len(people) - len(active),
       "사유별 건수 합 %d == 퇴사자 %d" % (rs, len(people) - len(active)))

    out.append("── 7. 심어둔 신호 검출 (등급 → 자발 이직률 단조 증가) ──")
    rates = {r[0]: r[5] for r in grade_rows}
    seq = " < ".join("%s %.1f%%" % (g, rates[g]) for g in ["S", "A", "B", "C"])
    ok(rates["S"] < rates["A"] < rates["B"] < rates["C"],
       "S < A < B < C 단조 증가 확인: %s" % seq)
    out.append("       (참고) D등급 %.1f%% — D는 표본 %d명으로 작아 단조성 판정에서 제외"
               % (rates["D"], next(r[1] for r in grade_rows if r[0] == "D")))
    # 중복 없는 최종등급 기준에서도 같은 방향이 나와야 신호가 집계 방식의 산물이 아니다
    frates = {r[0]: r[5] for r in grade_final_rows[:-1]}
    fseq = " < ".join("%s %.1f%%" % (g_, frates[g_]) for g_ in ["S", "A", "B", "C"])
    ok(frates["S"] < frates["A"] < frates["B"] < frates["C"],
       "최종등급 기준(중복 없음)에서도 S < A < B < C 재현: %s" % fseq)

    out.append("── 8. 신호 검출 (채널 → 성과) ──")
    by_ch = {r[0]: r for r in ch_rows[:-1]}
    ok(by_ch["직원추천"][4] > by_ch["커리어페어"][4],
       "직원추천 평균등급점수 %.2f > 커리어페어 %.2f"
       % (by_ch["직원추천"][4], by_ch["커리어페어"][4]))

    return out, errs


# ══════════════════════════════════════════════════════════════════
# § main
# ══════════════════════════════════════════════════════════════════
def main():
    people, active = R.build()
    newbies_all = [p for p in people if not p["seeded"]]

    wb = Workbook()
    wb.remove(wb.active)

    ws1, n1 = sheet_funnel(wb)
    ws2, n2, newbies = sheet_channel(wb, people)
    ws3, n3, n3b, grade_final_rows = sheet_grade(wb, people)
    ws4, n4 = sheet_tenure(wb, people)
    ws5, n5, leavers = sheet_reasons(wb, people)
    ws6, n6 = sheet_movement(wb, people)

    # 검증에 쓸 행 데이터를 다시 집계 (시트에 쓴 것과 같은 순수 함수)
    ch_rows, _ = agg_channel(people)
    grade_rows = agg_grade_experienced(people)
    tenure_rows = agg_tenure(people)
    qrows = agg_quarters(people)
    reason_rows, _ = agg_reasons(people)

    lines, errs = run_verification(people, active, ch_rows, newbies, grade_rows,
                                   grade_final_rows, tenure_rows, qrows,
                                   reason_rows, leavers)

    print("=" * 74)
    print(" 검증 결과")
    print("=" * 74)
    for ln in lines:
        print(ln)
    print()

    if errs:
        print("검증 실패 — 워크북을 저장하지 않는다:")
        for e in errs:
            print("  -", e)
        raise SystemExit(1)

    # ── README 서술용 실측치 ────────────────────────────────────
    g = {r[0]: r for r in grade_rows}                    # 등급 경험자 기준
    gf = {r[0]: r for r in grade_final_rows[:-1]}         # 최종등급 기준(보조표)
    ch = {r[0]: r for r in ch_rows[:-1]}
    tb = {r[0]: r for r in tenure_rows[:-1]}
    best_ch = max(ch.values(), key=lambda r: r[4] or 0)
    worst_ch = min(ch.values(), key=lambda r: r[4] if r[4] is not None else 99)
    peak_t = max(tb.values(), key=lambda r: r[3])

    ctx = {
        "n_all": len(people),
        "n_active": len(active),
        "n_left": len(people) - len(active),
        "n_seeded": sum(1 for p in people if p["seeded"]),
        "n_new": len(newbies_all),
        "n_reasons": len(reason_rows) - 1,
        "n_ungraded": sum(1 for p in people if not p["grades"]),
        "grade_exp_sum": sum(r[1] for r in grade_rows),
        "corr_grade":
            "평가 등급이 낮을수록 자발 이직률이 계단식으로 올라간다 — "
            "S %.1f%% → A %.1f%% → B %.1f%% → C %.1f%% → D %.1f%% "
            "(S 대비 C는 약 %.1f배)."
            % (g["S"][5], g["A"][5], g["B"][5], g["C"][5], g["D"][5],
               g["C"][5] / g["S"][5] if g["S"][5] else 0),
        "corr_grade_detail":
            "등급 경험자 기준 모집단은 S %d명·A %d명·B %d명·C %d명·D %d명. "
            "중복 없는 최종등급 기준(같은 시트 보조표)에서도 S %.1f%% → A %.1f%% → "
            "B %.1f%% → C %.1f%% → D %.1f%% 로 같은 방향이 재현된다. "
            "『등급별잔존』 시트의 막대 차트에서 바로 보인다. "
            "다만 평균근속은 등급과 단조 관계가 아니다 — 등급 보유자는 최소 한 번의 "
            "반기 평가를 넘긴 생존자라 S %.2f년·D %.2f년으로 오히려 저평가군이 길다."
            % (g["S"][1], g["A"][1], g["B"][1], g["C"][1], g["D"][1],
               gf["S"][5], gf["A"][5], gf["B"][5], gf["C"][5], gf["D"][5],
               g["S"][6], g["D"][6]),
        "corr_tenure":
            "자발 이직은 근속 %s 구간에서 %.1f%%로 정점을 찍는다 — 그 앞 구간(%s %.1f%%)"
            "보다도, 뒤 구간(%s %.1f%%)보다도 높고, %s 구간에서는 %.1f%%까지 내려간다."
            % (peak_t[0], peak_t[3], tenure_rows[0][0], tenure_rows[0][3],
               tenure_rows[2][0], tenure_rows[2][3],
               tenure_rows[3][0], tenure_rows[3][3]),
        "corr_tenure_detail":
            "구간별 자발이직률: " + " / ".join(
                "%s %.1f%%(%d명 중 %d명)" % (r[0], r[3], r[1], r[2])
                for r in tenure_rows[:-1])
            + ". 입사 1년 미만보다 1~2.5년차가 더 위험한 구간이라는 뜻이다. "
              "마지막 %s 구간은 %d명뿐이라 비율의 신뢰도가 낮다."
              % (tenure_rows[4][0], tenure_rows[4][1]),
        "corr_channel":
            "채용 채널에 따라 입사 후 성과가 갈린다 — %s 출신의 평균 등급점수가 %.2f로 "
            "가장 높고 %s 출신이 %.2f로 가장 낮다(차이 %.2f점)."
            % (best_ch[0], best_ch[4], worst_ch[0], worst_ch[4],
               best_ch[4] - worst_ch[4]),
        "corr_channel_detail":
            "채널별 (평균등급점수 / S+A 비율 / 수습통과율 / 자발이직률): " + " / ".join(
                "%s %.2f·%.1f%%·%.1f%%·%.1f%%" % (r[0], r[4] or 0, r[5], r[3], r[7])
                for r in ch_rows[:-1])
            + ". 신입 %d명 기준." % len(newbies_all),
        "verify_summary":
            "분기 집계 대조 %d건(10개 분기 × 7개 항목) 전량 일치, 채널 채용인원 합 = "
            "신입 총원 %d명, 최종등급 보조표 합 = 전체 %d명(중복 없음), "
            "근속 구간 합 = 전체 %d명, 등급별 자발이직률 S<A<B<C 단조 증가 확인."
            % (len(D.QUARTERS) * 7, len(newbies_all), len(people), len(people)),
    }

    ws7, n7 = sheet_readme(wb, ctx)

    # README 를 맨 앞으로 옮겨 파일을 열면 설명부터 보이게 한다
    wb.move_sheet("README", offset=-6)
    wb.active = 0

    os.makedirs(OUT_DIR, exist_ok=True)
    wb.save(OUT_PATH)

    size = os.path.getsize(OUT_PATH)
    print("=" * 74)
    print(" 저장 완료")
    print("=" * 74)
    print("  경로 : %s" % OUT_PATH)
    print("  크기 : %s bytes (%.1f KB)" % ("{:,}".format(size), size / 1024.0))
    print()
    print("  시트별 데이터 행 수 (헤더·합계 제외한 표 행 수는 괄호 안):")
    print("    README          %2d줄" % n7)
    print("    채용퍼널        %2d행 (분기 %d + 합계 1)" % (n1, n1 - 1))
    print("    채널별성과      %2d행 (채널 %d + 합계 1)" % (n2, n2 - 1))
    print("    등급별잔존      %2d행 (주표: 등급 %d) + 보조표 %d행" % (n3, n3, n3b))
    print("    근속별이직      %2d행 (구간 %d + 합계 1)" % (n4, n4 - 1))
    print("    퇴사사유분석    %2d행 (사유 %d + 합계 1)" % (n5, n5 - 1))
    print("    분기별인력이동  %2d행 (분기 %d + 합계 1)" % (n6, n6 - 1))
    print()
    print("  관측된 상관관계")
    print("    ① 등급 ↔ 이직 : %s" % ctx["corr_grade"])
    print("    ② 근속 ↔ 이직 : %s" % ctx["corr_tenure"])
    print("    ③ 채널 ↔ 성과 : %s" % ctx["corr_channel"])


if __name__ == "__main__":
    main()
