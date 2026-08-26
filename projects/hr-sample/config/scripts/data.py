# -*- coding: utf-8 -*-
"""(주)나린테크 인사 코퍼스의 단일 진실원.

모든 생성 문서의 수치는 이 파일에서만 나온다. 분기 합 = 연간, 등급 분포 인원 합 =
평가 대상 인원이 되도록 verify()가 강제한다. 가상 데이터이며 실존 기업과 무관하다.
"""

COMPANY = "(주)나린테크"
FIXTURE_NOTE = "※ 본 문서는 지식관리 파이프라인 검증용 가상 샘플이다. 실존 기업·인물과 무관하다."

# ── 분기별 인력 이동 ──────────────────────────────────────────────
# (연, 분기, 기초인원, 채용, 퇴사, 자발퇴사)
QUARTERS = [
    (2024, 1, 165, 12, 7, 5),
    (2024, 2, 170, 10, 8, 7),
    (2024, 3, 172,  9, 6, 5),
    (2024, 4, 175, 11, 6, 4),
    (2025, 1, 180, 13, 9, 8),
    (2025, 2, 184, 12, 7, 6),
    (2025, 3, 189, 10, 8, 7),
    (2025, 4, 191, 14, 7, 5),
    (2026, 1, 198, 12, 7, 5),
    (2026, 2, 203, 16, 7, 6),
]

# ── 반기 평가 차수 ────────────────────────────────────────────────
# 평가 대상(n)은 반기말 재직 인원에서 수습 중 인원(당 분기 입사자)을 뺀 값 —
# 「인사평가 운영지침」 제10조에 따라 수습사원은 정규 평가에서 분리된다.
# dist 합 = n 이 되도록 verify()가 강제한다.
# (연, 반기, {등급: 인원}, 보정상향, 보정하향, 이의신청, 이의인용)
HALVES = [
    (2024, 1, {"S": 15, "A": 34, "B":  84, "C": 24, "D": 5},  8, 10,  3, 1),
    (2024, 2, {"S": 15, "A": 36, "B":  88, "C": 25, "D": 5},  9, 11,  4, 1),
    (2025, 1, {"S": 16, "A": 38, "B":  92, "C": 26, "D": 5},  7, 12,  4, 2),
    (2025, 2, {"S": 16, "A": 40, "B":  96, "C": 27, "D": 5},  9, 13,  6, 2),
    (2026, 1, {"S": 17, "A": 43, "B": 101, "C": 29, "D": 6}, 11, 14, 10, 4),
]

GRADES = ["S", "A", "B", "C", "D"]
QUOTA = {"S": 0.10, "A": 0.20, "B": 0.50, "C": 0.15, "D": 0.05}

# ── OKR 확정률 (반기별) ───────────────────────────────────────────
OKR_ONTIME = {(2024,1): (9,16), (2024,2): (10,16), (2025,1): (11,17),
              (2025,2): (12,18), (2026,1): (14,19)}

# ── 수습 전환 (분기별) ────────────────────────────────────────────
PROBATION = {(2024,1):(12,11),(2024,2):(10,9),(2024,3):(9,8),(2024,4):(11,10),
             (2025,1):(13,11),(2025,2):(12,11),(2025,3):(10,8),(2025,4):(14,13),
             (2026,1):(12,11),(2026,2):(16,15)}

# ── 제도 연혁 ─────────────────────────────────────────────────────
TIMELINE = [
    ("2024-03-01", "「인사평가 운영지침」 제정 — 강제 분포(S10/A20/B50/C15/D5) 도입"),
    ("2024-09-12", "평가자 교육 신설 — 연 1회 2시간"),
    ("2025-02-20", "보정회의 시범 도입 (권고, 의무 아님)"),
    ("2025-07-01", "「취업규칙」 개정 — 수습기간 3개월 명문화"),
    ("2026-01-15", "「인사평가 운영지침」 개정 — 보정회의 의무화, 이의신청 14일→7일"),
]

DEPARTMENTS = ["플랫폼개발본부", "서비스개발본부", "데이터본부", "사업본부", "경영지원본부"]


# ── 파생 계산 ─────────────────────────────────────────────────────
def quarter(y, q):
    for row in QUARTERS:
        if row[0] == y and row[1] == q:
            base, hire, leave, vol = row[2], row[3], row[4], row[5]
            return {"year": y, "q": q, "base": base, "hire": hire, "leave": leave,
                    "voluntary": vol, "end": base + hire - leave}
    raise KeyError((y, q))

def year_quarters(y):
    return [quarter(y, q) for q in (1, 2, 3, 4) if any(r[0] == y and r[1] == q for r in QUARTERS)]

def year_summary(y):
    qs = year_quarters(y)
    avg = sum(q["base"] + q["end"] for q in qs) / (2 * len(qs))
    hire, leave, vol = (sum(q[k] for q in qs) for k in ("hire", "leave", "voluntary"))
    full = len(qs) == 4
    rate = vol / avg * 100 * (1 if full else 4 / len(qs))
    return {"year": y, "quarters": len(qs), "begin": qs[0]["base"], "end": qs[-1]["end"],
            "hire": hire, "leave": leave, "voluntary": vol, "avg_headcount": round(avg, 1),
            "turnover": round(rate, 1), "annualized": not full}

def half(y, h):
    """반기 평가 차수. n(평가 대상)은 재직 인원에서 파생된다."""
    for row in HALVES:
        if row[0] == y and row[1] == h:
            _, _, dist, up, down, appeal, upheld = row
            endq = quarter(y, 2 if h == 1 else 4)
            probation = endq["hire"]              # 당 분기 입사자 = 수습 중
            n = endq["end"] - probation
            return {"year": y, "half": h, "n": n, "dist": dist, "up": up, "down": down,
                    "appeal": appeal, "upheld": upheld, "headcount": endq["end"],
                    "probation": probation, "changed": up + down,
                    "kept": n - up - down}
    raise KeyError((y, h))


def dist_rows(hf):
    """등급별 [등급, 규정비율, 인원, 실제비율, 편차] 행."""
    out = []
    for g in GRADES:
        cnt = hf["dist"][g]
        act = cnt / hf["n"] * 100
        quota = QUOTA[g] * 100
        out.append([g, "%.0f%%" % quota, "%d명" % cnt, "%.1f%%" % act,
                    "%+.1f%%p" % (act - quota)])
    return out


def verify():
    """문서 생성 전 자기 검증. 하나라도 깨지면 생성 중단."""
    errs = []
    # 분기 연쇄: 이전 분기 기말 = 다음 분기 기초
    for i in range(1, len(QUARTERS)):
        prev, cur = quarter(*QUARTERS[i-1][:2]), quarter(*QUARTERS[i][:2])
        if prev["end"] != cur["base"]:
            errs.append("분기 연쇄 불일치 %s → %s: %d != %d" %
                        (QUARTERS[i-1][:2], QUARTERS[i][:2], prev["end"], cur["base"]))
    # 자발퇴사 <= 전체퇴사
    for r in QUARTERS:
        if r[5] > r[4]:
            errs.append("자발퇴사 > 전체퇴사 %s" % (r[:2],))
    # 등급 인원 합 = 평가 대상
    for row in HALVES:
        hf = half(row[0], row[1])
        tot = sum(hf["dist"].values())
        if tot != hf["n"]:
            errs.append("등급 합 != 평가대상 %d-%d: %d != %d (재직 %d - 수습 %d)"
                        % (row[0], row[1], tot, hf["n"], hf["headcount"], hf["probation"]))
        if hf["up"] + hf["down"] > hf["n"]:
            errs.append("보정 건수 > 대상 인원 %d-%d" % (row[0], row[1]))
        if hf["upheld"] > hf["appeal"]:
            errs.append("인용 > 접수 %d-%d" % (row[0], row[1]))
    # 수습 전환자 <= 채용
    for (y, q), (intake, passed) in PROBATION.items():
        if passed > intake:
            errs.append("수습 전환 > 입사 %d-Q%d" % (y, q))
        if intake != quarter(y, q)["hire"]:
            errs.append("수습 입사 != 분기 채용 %d-Q%d: %d != %d"
                        % (y, q, intake, quarter(y, q)["hire"]))
    return errs


if __name__ == "__main__":
    e = verify()
    if e:
        print("검증 실패:"); [print(" -", x) for x in e]; raise SystemExit(1)
    print("데이터 모델 검증 통과\n")
    print("%-6s %6s %6s %6s %6s %8s" % ("기간", "기초", "채용", "퇴사", "기말", "자발퇴사"))
    for r in QUARTERS:
        q = quarter(r[0], r[1])
        print("%d-Q%d %6d %6d %6d %6d %8d" % (q["year"], q["q"], q["base"], q["hire"],
                                              q["leave"], q["end"], q["voluntary"]))
    print()
    for y in (2024, 2025, 2026):
        s = year_summary(y)
        print("%d년: 기초 %d → 기말 %d | 채용 %d 퇴사 %d | 이직률 %.1f%%%s"
              % (y, s["begin"], s["end"], s["hire"], s["leave"], s["turnover"],
                 " (연환산)" if s["annualized"] else ""))
    print()
    print("%-9s %6s %6s %6s  %s" % ("평가차수", "재직", "수습", "대상", "등급분포"))
    for row in HALVES:
        hf = half(row[0], row[1])
        d = " ".join("%s%d" % (g, hf["dist"][g]) for g in GRADES)
        print("%d-H%d   %6d %6d %6d  %s" % (row[0], row[1], hf["headcount"],
                                            hf["probation"], hf["n"], d))


# ══════════════════════════════════════════════════════════════════
# § 확장 — 부서별 분포·급여·연차 (2026-08-26 추가)
# ══════════════════════════════════════════════════════════════════

DEPT_SHARE = [
    ("플랫폼개발본부", 0.28),
    ("서비스개발본부", 0.24),
    ("데이터본부",     0.14),
    ("사업본부",       0.20),
    ("경영지원본부",   0.14),
]

def dept_headcount(total):
    """최대잔여법(largest remainder)으로 정수 배분 — 합이 total과 정확히 일치."""
    raw = [(name, total * share) for name, share in DEPT_SHARE]
    floors = [(name, int(v), v - int(v)) for name, v in raw]
    remainder = total - sum(f for _, f, _ in floors)
    floors.sort(key=lambda x: -x[2])
    out = {name: f for name, f, _ in floors}
    for i in range(remainder):
        name = floors[i % len(floors)][0]
        out[name] += 1
    return [(name, out[name]) for name, _ in DEPT_SHARE]


def dept_hires(y, q):
    """분기 채용 인원의 본부별 배분 — quarter_report와 동일 로직(최대잔여법 아님, 균등+나머지)."""
    d = quarter(y, q)
    base = d["hire"] // len(DEPARTMENTS)
    rem = d["hire"] - base * len(DEPARTMENTS)
    return [(dept, base + (1 if i < rem else 0)) for i, dept in enumerate(DEPARTMENTS)]


# ── 직급 체계 및 급여 밴드 (연봉, 만원 단위) ─────────────────────
GRADE_LEVELS = [
    # (직급코드, 직급명, 하한, 상한, 표준연봉)
    ("L1", "사원",   3400, 4200, 3800),
    ("L2", "선임",   4200, 5400, 4800),
    ("L3", "책임",   5400, 7000, 6200),
    ("L4", "수석",   7000, 9500, 8200),
    ("L5", "본부장", 9500, 13000, 11000),
]

# 평가 등급별 급여 인상률·상여 배율 (제도 설계상의 연동표)
GRADE_TO_RAISE = {"S": 8.0, "A": 5.0, "B": 3.0, "C": 1.0, "D": 0.0}   # 연봉 인상률(%)
GRADE_TO_BONUS = {"S": 200, "A": 150, "B": 100, "C": 50,  "D": 0}     # 기본급 대비 상여(%)

# ── 연차휴가 (근속연수별 가산, 근로기준법 기준 정책화) ───────────
LEAVE_BY_TENURE = [
    (0, 1, 11),    # 근속 1년 미만: 월 1일 (최대 11일)
    (1, 3, 15),
    (3, 5, 16),
    (5, 7, 17),
    (7, 9, 18),
    (9, 11, 19),
    (11, 99, 20),  # 상한 20일 (2년마다 1일 가산, 상한 25일까지 조항에서 별도 서술)
]

def annual_leave_days(years):
    for lo, hi, days in LEAVE_BY_TENURE:
        if lo <= years < hi:
            return days
    return 25

# ── 채용 퍼널 (분기별) ────────────────────────────────────────────
# (연, 분기, 지원자, 서류통과, 면접진행, 최종합격) — 최종합격 == hire
FUNNEL = {
    (2025,1): (312, 84, 41, 13), (2025,2): (298, 79, 38, 12),
    (2025,3): (256, 68, 33, 10), (2025,4): (341, 91, 44, 14),
    (2026,1): (289, 77, 37, 12), (2026,2): (378, 102, 49, 16),
}

def verify_ext():
    errs = []
    for name, share in DEPT_SHARE:
        pass
    if abs(sum(s for _, s in DEPT_SHARE) - 1.0) > 1e-9:
        errs.append("DEPT_SHARE 합 != 1.0")
    for (y, q), (a, b, c, hire) in FUNNEL.items():
        if hire != quarter(y, q)["hire"]:
            errs.append("퍼널 최종합격 != 분기 채용 %d-Q%d: %d != %d" % (y, q, hire, quarter(y,q)["hire"]))
        if not (a >= b >= c >= hire):
            errs.append("퍼널 단계 역전 %d-Q%d" % (y, q))
    for y, q in [(r[0], r[1]) for r in QUARTERS]:
        total = sum(c for _, c in dept_headcount(quarter(y,q)["end"]))
        if total != quarter(y, q)["end"]:
            errs.append("부서 배분 합 불일치 %d-Q%d: %d != %d" % (y, q, total, quarter(y,q)["end"]))
    return errs

# ── 자발적 퇴사 사유 배분 (최대잔여법) ────────────────────────────
ATTRITION_REASON_SHARE = [("이직(타사)", 0.50), ("개인사유", 0.30), ("창업/이직준비", 0.20)]

def attrition_reasons(voluntary):
    raw = [(name, voluntary * s) for name, s in ATTRITION_REASON_SHARE]
    floors = [(name, int(v), v - int(v)) for name, v in raw]
    remainder = voluntary - sum(f for _, f, _ in floors)
    floors.sort(key=lambda x: -x[2])
    out = {name: f for name, f, _ in floors}
    for i in range(remainder):
        out[floors[i % len(floors)][0]] += 1
    return [(name, out[name]) for name, _ in ATTRITION_REASON_SHARE]

def weighted_raise(hf):
    return sum(hf["dist"][g] * GRADE_TO_RAISE[g] for g in GRADES) / hf["n"]

def weighted_bonus(hf):
    return sum(hf["dist"][g] * GRADE_TO_BONUS[g] for g in GRADES) / hf["n"]
