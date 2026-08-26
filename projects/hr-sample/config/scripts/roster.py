# -*- coding: utf-8 -*-
"""개인 단위 로스터 — XLSX 데이터셋의 기반.

data.py의 집계 수치(분기별 채용·퇴사, 반기별 등급 분포, 부서 배분)를 **정확히**
재현하는 개인 레코드를 결정론적으로 생성한다. 같은 seed면 항상 같은 결과다.

분석 가능한 상관 신호를 의도적으로 심어 뒀다 (§ 심어둔 신호). 목업이지만
"D등급자의 이직률이 실제로 더 높은가?" 같은 질문에 데이터가 답할 수 있어야
질의 실증에 쓸 수 있기 때문이다.
"""
import random
from datetime import date, timedelta
import data as D

SEED = 20260826

# ── 채용 채널 ─────────────────────────────────────────────────────
# (채널명, 배분 가중치, 수습통과 보정, 성과 보정) — 보정값이 § 심어둔 신호의 근원
CHANNELS = [
    ("직원추천",     0.28,  +0.12,  +1.05),
    ("채용공고",     0.34,   0.00,   0.00),
    ("헤드헌팅",     0.16,  +0.06,  +0.65),
    ("커리어페어",   0.12,  -0.08,  -0.95),
    ("인턴전환",     0.10,  +0.10,  +0.45),
]

# 부서별 평가 성향 — 중앙집중 경향의 강도가 부서마다 다르다
DEPT_BIAS = {
    "플랫폼개발본부":  0.45,
    "서비스개발본부":  0.00,
    "데이터본부":      0.60,
    "사업본부":       -0.40,
    "경영지원본부":   -0.20,
}

LEVEL_BY_TENURE = [(0, 2, "L1"), (2, 5, "L2"), (5, 9, "L3"), (9, 14, "L4"), (14, 99, "L5")]

TERM_REASONS_VOL = ["이직(타사)", "개인사유", "창업/이직준비"]
TERM_REASON_PROBATION_VOL = "수습 중 자진 퇴사"
TERM_REASONS_INVOL = ["수습 미전환", "계약 종료", "성과 미달"]

GRADE_SCORE = {"S": 4, "A": 3, "B": 2, "C": 1, "D": 0}


def _quarter_end(y, q):
    return {1: date(y, 3, 31), 2: date(y, 6, 30), 3: date(y, 9, 30), 4: date(y, 12, 31)}[q]

def _quarter_start(y, q):
    return {1: date(y, 1, 1), 2: date(y, 4, 1), 3: date(y, 7, 1), 4: date(y, 10, 1)}[q]

def _level_for(tenure_years):
    for lo, hi, code in LEVEL_BY_TENURE:
        if lo <= tenure_years < hi:
            return code
    return "L5"

def _pick_dept(rng, people_so_far):
    """목표 비율 대비 부족한 부서를 우선 배정한다.

    순수 확률 배분은 목표에서 크게 벗어나 끝에서 대규모 리밸런싱을 부르고, 그 이동이
    부서별 평가 성향 신호를 희석한다. 채용 시점에 부족분을 메우면 이동이 거의 없어진다.
    """
    alive = [p for p in people_so_far if p["term_date"] is None]
    n = len(alive) + 1
    have = {}
    for p in alive:
        have[p["dept"]] = have.get(p["dept"], 0) + 1
    weights = []
    for d, share in D.DEPT_SHARE:
        target = share * n
        gap = target - have.get(d, 0)
        weights.append(max(0.02, gap))
    return rng.choices([d for d, _ in D.DEPT_SHARE], weights=weights)[0]


def _pick_weighted(rng, items):
    total = sum(w for _, w, *_ in items)
    r = rng.random() * total
    acc = 0.0
    for it in items:
        acc += it[1]
        if r <= acc:
            return it
    return items[-1]


def build(seed=SEED):
    rng = random.Random(seed)
    people = []
    next_id = 1

    def new_person(hire_dt, hire_q, seeded=False):
        nonlocal next_id
        ch = _pick_weighted(rng, CHANNELS)
        dept = _pick_dept(rng, people)
        p = {
            "emp_id": "N%04d" % next_id,
            "dept": dept,
            "hire_date": hire_dt,
            "hire_quarter": hire_q,
            "channel": ch[0],
            "_probation_boost": ch[2],
            # 잠재 성과 특성 — 사람마다 고정. 채널·부서 보정이 여기 들어간다.
            "_talent": rng.gauss(0, 1) + ch[3] + DEPT_BIAS[dept],
            "probation_passed": None,
            "term_date": None,
            "term_quarter": None,
            "term_type": None,
            "term_reason": None,
            "grades": {},
            "seeded": seeded,
        }
        next_id += 1
        people.append(p)
        return p

    # ── 기초 인원 165명: 2024-Q1 이전 입사자 (근속 분포를 만들어 준다) ──
    base_n = D.QUARTERS[0][2]
    for _ in range(base_n):
        # 근속 0.5~12년 — 오래된 사람일수록 적게
        yrs = min(12.0, abs(rng.gauss(0, 3.4)) + 0.5)
        hd = date(2024, 1, 1) - timedelta(days=int(yrs * 365.25))
        p = new_person(hd, None, seeded=True)
        p["probation_passed"] = True

    active = list(people)
    pending_fail = []   # 수습 미전환 확정자 — 수습 3개월이므로 다음 분기에 퇴사 처리

    # ── 분기별 시뮬레이션 ────────────────────────────────────────
    for (y, q, base, hire, leave, vol) in D.QUARTERS:
        assert len(active) == base, "기초 인원 불일치 %d-Q%d: %d != %d" % (y, q, len(active), base)

        # 1) 채용
        qs, qe = _quarter_start(y, q), _quarter_end(y, q)
        intake, passed = D.PROBATION[(y, q)]
        assert intake == hire
        newbies = []
        for _ in range(hire):
            offset = rng.randint(0, (qe - qs).days)
            p = new_person(qs + timedelta(days=offset), (y, q))
            newbies.append(p)

        # 2) 수습 판정 — 채널 보정이 통과율에 반영되도록 가중 샘플
        fail_n = intake - passed
        if fail_n > 0:
            w = [max(0.05, 1.0 - nb["_probation_boost"] - nb["_talent"] * 0.25) for nb in newbies]
            failed = _weighted_sample(rng, newbies, w, fail_n)
        else:
            failed = []
        for nb in newbies:
            nb["probation_passed"] = nb not in failed

        active += newbies

        # 3) 퇴사 — 등급·근속이 확률에 실제로 영향을 준다
        #    평가보다 먼저 처리한다: 평가 대상은 "반기말 재직" 기준이고(data.py),
        #    이직 결정은 직전 차수 등급을 보고 내리므로 순서가 현실과도 맞는다.
        #    수습 미전환자는 「취업규칙」 제12조의 수습 3개월을 반영해 **다음 분기**에
        #    나간다 — 같은 분기에 내보내면 반기말 재직 대비 평가대상 수가 어긋난다.
        forced = list(pending_fail)
        pending_fail = [nb for nb in newbies if nb["probation_passed"] is False]
        remaining = leave - len(forced)
        assert remaining >= 0, "%d-Q%d 퇴사 %d < 수습미전환 %d" % (y, q, leave, len(forced))

        fset = set(id(p) for p in forced)
        pset = set(id(p) for p in pending_fail)
        candidates = [p for p in active
                      if id(p) not in fset and id(p) not in pset
                      and p["hire_quarter"] != (y, q)]
        w = [_attrition_weight(p, y, q) for p in candidates]
        leavers = _weighted_sample(rng, candidates, w, remaining)

        # 자발/비자발 배분.
        # 수습 미전환 확정자라도 통보 전에 본인이 먼저 나가는 경우가 있어(자발),
        # 비자발 정원을 넘는 인원은 자발로 분류한다 — 그렇지 않으면 비자발 정원이
        # 수습 실패자 수보다 적은 분기(2025-Q2 등)에서 배분이 불가능해진다.
        invol_cap = leave - vol
        forced_invol_n = min(len(forced), invol_cap)
        forced_invol = set(id(x) for x in forced[:forced_invol_n])

        rest_invol_n = invol_cap - forced_invol_n
        lw = [(4 - _grade_score(x)) + 0.5 for x in leavers]   # 성과 낮을수록 비자발↑
        rest_invol = _weighted_sample(rng, leavers, lw, rest_invol_n)
        rest_invol_ids = set(id(x) for x in rest_invol)

        for x in forced:
            if id(x) in forced_invol:
                _terminate(rng, x, y, q, qe, "비자발", "수습 미전환")
            else:
                _terminate(rng, x, y, q, qe, "자발", "수습 중 자진 퇴사")
        for x in leavers:
            if id(x) in rest_invol_ids:
                _terminate(rng, x, y, q, qe, "비자발",
                           rng.choice(TERM_REASONS_INVOL[1:]))
            else:
                _terminate(rng, x, y, q, qe, "자발",
                           rng.choices(TERM_REASONS_VOL, weights=[0.50, 0.30, 0.20])[0])

        gone = fset | set(id(x) for x in leavers)
        active = [p for p in active if id(p) not in gone]

        assert len(active) == base + hire - leave, \
            "%d-Q%d 기말 불일치: %d != %d" % (y, q, len(active), base + hire - leave)

        # 4) 반기말이면 평가 — 기말 재직자 중 당 분기 입사자(수습 중)는 제외
        if q in (2, 4):
            h = 1 if q == 2 else 2
            hf = D.half(y, h)
            eligible = [p for p in active if p["hire_quarter"] != (y, q)]
            assert len(eligible) == hf["n"], \
                "평가대상 불일치 %d-H%d: %d != %d" % (y, h, len(eligible), hf["n"])
            _assign_grades(rng, eligible, hf, (y, h))

    moved = rebalance_departments(rng, active)
    for p in people:
        p.setdefault("dept_changed", False)
        p.setdefault("prev_dept", None)
    return people, active


def _grade_score(p):
    if not p["grades"]:
        return 2
    last = sorted(p["grades"])[-1]
    return GRADE_SCORE[p["grades"][last]]


def _attrition_weight(p, y, q):
    """이직 확률 가중치 — 낮은 등급·근속 1~2년차에서 높다 (§ 심어둔 신호)."""
    w = 1.0
    s = _grade_score(p)
    w *= {0: 3.4, 1: 2.2, 2: 1.0, 3: 0.55, 4: 0.40}[s]      # 등급 → 이직
    tenure = (_quarter_end(y, q) - p["hire_date"]).days / 365.25
    if tenure < 1:     w *= 1.15
    elif tenure < 2.5: w *= 1.85                             # 근속 1~2년차 피크
    elif tenure < 5:   w *= 0.85
    else:              w *= 0.55
    return max(0.02, w)


def _assign_grades(rng, eligible, hf, key):
    """등급 분포를 **정확히** 맞추되, 잠재 성과 순위대로 배정해 지속성을 만든다."""
    scored = []
    for p in eligible:
        prev = _grade_score(p) if p["grades"] else 2
        noise = rng.gauss(0, 0.62)
        scored.append((p["_talent"] + (prev - 2) * 0.42 + noise, p))
    scored.sort(key=lambda t: -t[0])
    i = 0
    for g in D.GRADES:
        for _ in range(hf["dist"][g]):
            scored[i][1]["grades"][key] = g
            i += 1
    assert i == len(eligible)


def _weighted_sample(rng, items, weights, k):
    """가중 비복원 추출 — 정확히 k개."""
    if k <= 0:
        return []
    pool = list(zip(items, weights))
    out = []
    for _ in range(min(k, len(pool))):
        total = sum(w for _, w in pool)
        r = rng.random() * total
        acc = 0.0
        for idx, (it, w) in enumerate(pool):
            acc += w
            if r <= acc:
                out.append(it)
                pool.pop(idx)
                break
        else:
            out.append(pool.pop()[0])
    return out


def _terminate(rng, p, y, q, qe, ttype, reason):
    qs = _quarter_start(y, q)
    p["term_date"] = qs + timedelta(days=rng.randint(0, (qe - qs).days))
    p["term_quarter"] = (y, q)
    p["term_type"] = ttype
    p["term_reason"] = reason


def rebalance_departments(rng, active):
    """재직자 부서를 목표 배분(D.dept_headcount)에 맞춘다.

    부서는 확률로 생성되므로 목표와 어긋난다. 초과 부서 → 부족 부서로 이동시키되,
    이동자에게 `dept_changed`/`prev_dept`를 남긴다 — 「인사평가 운영지침」 제14조
    (조직 개편 시 평가)가 실제로 다루는 상황이고, 분석 축이 하나 늘어난다.
    등급은 이미 배정된 뒤이므로 부서별 평가 성향 신호는 이동분(전체의 6% 내외)만
    희석된다.
    """
    want = dict(D.dept_headcount(len(active)))
    by_dept = {}
    for p in active:
        by_dept.setdefault(p["dept"], []).append(p)

    surplus, deficit = [], []
    for d, _ in D.DEPT_SHARE:
        have = len(by_dept.get(d, []))
        diff = have - want[d]
        if diff > 0:
            surplus.append((d, diff))
        elif diff < 0:
            deficit.append((d, -diff))

    moved = 0
    for d, need in deficit:
        while need > 0:
            for i, (sd, cnt) in enumerate(surplus):
                if cnt <= 0:
                    continue
                pool = by_dept[sd]
                # 근속이 짧은 쪽을 먼저 이동 — 조직 개편의 통상 패턴
                pool.sort(key=lambda x: x["hire_date"], reverse=True)
                person = pool.pop(0)
                person["prev_dept"] = person["dept"]
                person["dept"] = d
                person["dept_changed"] = True
                by_dept.setdefault(d, []).append(person)
                surplus[i] = (sd, cnt - 1)
                need -= 1
                moved += 1
                break
            else:
                break
    for p in active:
        p.setdefault("dept_changed", False)
        p.setdefault("prev_dept", None)
    return moved


# ── 파생 필드 ─────────────────────────────────────────────────────
def tenure_years(p, asof=date(2026, 6, 30)):
    end = p["term_date"] or asof
    return round((end - p["hire_date"]).days / 365.25, 1)

def level_of(p, asof=date(2026, 6, 30)):
    return _level_for(tenure_years(p, asof))

def salary(p, asof=date(2026, 6, 30)):
    """직급 표준연봉에서 시작해 누적 평가 등급 인상률을 반영 (만원)."""
    lvl = level_of(p, asof)
    lo, hi, std = next((l, h, s) for c, n, l, h, s in D.GRADE_LEVELS if c == lvl)
    amt = float(std)
    for key in sorted(p["grades"]):
        amt *= (1 + D.GRADE_TO_RAISE[p["grades"][key]] / 100.0 * 0.5)
    return int(min(hi, max(lo, round(amt))))

def leave_entitled(p, asof=date(2026, 6, 30)):
    return D.annual_leave_days(int(tenure_years(p, asof)))


def verify(people, active):
    errs = []
    # 부서 배분
    want = dict(D.dept_headcount(D.quarter(2026, 2)["end"]))
    got = {}
    for p in active:
        got[p["dept"]] = got.get(p["dept"], 0) + 1
    # 부서는 확률 배분이라 정확히 일치하지 않는다 — 리밸런싱은 build 밖에서
    # 각 반기 등급 분포
    for row in D.HALVES:
        key = (row[0], row[1])
        hf = D.half(*key)
        cnt = {}
        for p in people:
            g = p["grades"].get(key)
            if g:
                cnt[g] = cnt.get(g, 0) + 1
        for g in D.GRADES:
            if cnt.get(g, 0) != hf["dist"][g]:
                errs.append("%s %s등급 %d != %d" % (key, g, cnt.get(g, 0), hf["dist"][g]))
    # 퇴사 집계
    for (y, q, base, hire, leave, vol) in D.QUARTERS:
        t = [p for p in people if p["term_quarter"] == (y, q)]
        v = [p for p in t if p["term_type"] == "자발"]
        if len(t) != leave:
            errs.append("%d-Q%d 퇴사 %d != %d" % (y, q, len(t), leave))
        if len(v) != vol:
            errs.append("%d-Q%d 자발퇴사 %d != %d" % (y, q, len(v), vol))
    if len(active) != D.quarter(2026, 2)["end"]:
        errs.append("기말 재직 %d != %d" % (len(active), D.quarter(2026, 2)["end"]))
    return errs, got, want


if __name__ == "__main__":
    people, active = build()
    errs, got, want = verify(people, active)
    print("로스터 생성: 전체 %d명 / 재직 %d명 / 퇴사 %d명"
          % (len(people), len(active), len(people) - len(active)))
    print("집계 검증:", "통과" if not errs else errs[:6])
    print()
    print("부서 배분 (리밸런싱 후):")
    for d, _ in D.DEPT_SHARE:
        print("  %-14s %3d  목표 %3d  %s"
              % (d, got.get(d, 0), want[d], "OK" if got.get(d,0)==want[d] else "MISMATCH"))
    print("  조직 이동 이력 보유:", sum(1 for p in active if p.get("dept_changed")), "명")

    print()
    print("── 심어둔 신호가 실제로 검출되는가 ──")
    # 1) 마지막 등급 → 자발 이직률
    print("  [등급 → 자발 이직률]")
    for g in D.GRADES:
        had = [p for p in people if g in p["grades"].values()]
        left = [p for p in had if p["term_type"] == "자발"]
        if had:
            print("    %s등급 경험자 %3d명 중 자발 퇴사 %2d명 (%.1f%%)"
                  % (g, len(had), len(left), len(left)/len(had)*100))
    # 2) 채용 채널 → 수습 통과율
    print("  [채용 채널 → 수습 통과율]")
    for ch, _, _, _ in CHANNELS:
        cand = [p for p in people if p["channel"] == ch and p["probation_passed"] is not None
                and not p["seeded"]]
        ok_ = [p for p in cand if p["probation_passed"]]
        if cand:
            print("    %-10s %3d명 중 %3d명 통과 (%.1f%%)"
                  % (ch, len(cand), len(ok_), len(ok_)/len(cand)*100))
    # 3) 근속 구간 → 자발 이직률
    print("  [근속 구간 → 자발 이직률]")
    import collections
    buckets = collections.OrderedDict([("1년 미만",(0,1)),("1~2.5년",(1,2.5)),
                                        ("2.5~5년",(2.5,5)),("5년 이상",(5,99))])
    for label,(lo,hi) in buckets.items():
        grp = [p for p in people if lo <= tenure_years(p) < hi]
        left = [p for p in grp if p["term_type"] == "자발"]
        if grp:
            print("    %-10s %3d명 중 자발 퇴사 %2d명 (%.1f%%)"
                  % (label, len(grp), len(left), len(left)/len(grp)*100))
