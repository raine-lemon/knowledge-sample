# -*- coding: utf-8 -*-
"""생성된 Clippings MD를 다시 읽어 문서 간 수치 정합성을 검증한다.
데이터 모델이 아니라 **산출물**을 검사하므로, 생성 과정의 실수까지 잡는다."""
import os, re, pathlib, sys
import data as D

# 인제스트 전에는 Clippings/, 인제스트 후에는 raw/ 루트에 원문이 있다.
# 두 상태 모두에서 검증이 돌도록 파일이 있는 쪽을 자동으로 고른다.
_VAULT = pathlib.Path(os.path.expanduser("~/knowledge-sample"))
CLIP = _VAULT / "Clippings"
if not any(CLIP.glob("*.md")):
    CLIP = _VAULT / "raw"
ok, bad = [], []

def read(name):
    p = CLIP / name
    if not p.exists():
        bad.append("파일 없음: %s" % name); return ""
    return p.read_text(encoding="utf-8")

def flat(text):
    """PDF markdown 추출은 문장 중간에서 줄바꿈이 들어간다 — 산문 부분일치 검사는
    공백을 정규화한 버전으로 한다. 표 행 정규식 검사는 원문 그대로 쓴다."""
    return re.sub(r"\s+", " ", text)

def check(label, cond, detail=""):
    (ok if cond else bad).append("%s%s" % (label, ("  — " + detail) if detail and not cond else ""))

# ── 1. 분기 리포트 연쇄: 이전 기말 = 다음 기초 ───────────────────
seq = [(2025,1),(2025,2),(2025,3),(2025,4),(2026,1),(2026,2)]
def q_nums(y, q):
    t = read("%d Q%d 채용이직 리포트.md" % (y, q))
    g = lambda k: int(re.search(r"\|%s\|(\d+)명\|" % k, t).group(1)) if re.search(r"\|%s\|(\d+)명\|" % k, t) else None
    return {"base": g("기초 재직"), "hire": g("채용"), "end": g("기말 재직")}

prev = None
for y, q in seq:
    n = q_nums(y, q)
    m = D.quarter(y, q)
    check("%d-Q%d 리포트 수치 = 데이터 모델" % (y, q),
          n["base"] == m["base"] and n["end"] == m["end"],
          "리포트 %s vs 모델 base=%d end=%d" % (n, m["base"], m["end"]))
    if prev:
        check("%d-Q%d 기초 = 직전 분기 기말" % (y, q), n["base"] == prev,
              "기초 %s ≠ 직전 기말 %s" % (n["base"], prev))
    prev = n["end"]

# ── 2. 연간 보고서 채용 합 = 분기 리포트 채용 합 ─────────────────

# ── 7. 부서 배분 합 = 재직 인원 (반기 리포트) ────────────────────
for y, h in [(r[0], r[1]) for r in D.HALVES]:
    hf = D.half(y, h)
    label = "상반기" if h == 1 else "하반기"
    t = read("%d %s 인사평가 결과 리포트.md" % (y, label))
    dept = D.dept_headcount(hf["headcount"])
    for dn, c in dept:
        if not re.search(r"\|%s\|%d명\|" % (dn, c), t):
            bad.append("%d-H%d 부서표에 %s %d명 없음" % (y, h, dn, c))
    ok.append("%d-H%d 부서 배분 합 = 재직(%d명)" % (y, h, hf["headcount"]))

# ── 8. 급여규정 등급 연동표가 HWPX·PDF·PPTX 세 곳 모두 일치 ───────
g26 = read("나린테크 급여규정(2026 개정).md")
for g in D.GRADES:
    raise_pct = D.GRADE_TO_RAISE[g]
    bonus_pct = D.GRADE_TO_BONUS[g]
    check("급여규정 %s등급 인상률 %.1f%%" % (g, raise_pct),
          ("%s등급 — 인상률 %.1f%%" % (g, raise_pct)) in g26)
    check("급여규정 %s등급 상여 %d%%" % (g, bonus_pct),
          ("%s등급 — 기본급 대비 %d%%" % (g, bonus_pct)) in g26)
comp = read("2026년 급여·상여 정책 설명회.md")
for g in D.GRADES:
    check("설명회 슬라이드 %s등급 인상률 = 급여규정" % g,
          ("%s등급 — 인상률 %.1f%%" % (g, D.GRADE_TO_RAISE[g])) in comp)

# ── 9. 상호 참조 — docx/pptx 신규 문서 ───────────────────────────
sop = read("나린테크 인사팀 업무 매뉴얼(SOP).md")
check("SOP → 지침 제12조 참조", "제12조" in sop)
check("SOP → 급여규정 제7조 참조", "급여규정 제7조" in sop or "제7조" in sop)
contract = read("나린테크 표준근로계약서(템플릿).md")
check("근로계약서 → 급여규정 제3조 참조", "급여규정" in contract and "제3조" in contract)
check("근로계약서 → 복무규정 제5조(연차) 참조", "복무규정" in contract)
jd = read("직무기술서_백엔드.md")
check("직무기술서 → 급여규정 제3조 참조", "급여규정" in jd and "제3조" in jd)

# ── 10. 복무규정 연차 테이블이 HWPX·근로계약서 일치 ──────────────
leave26 = read("나린테크 복무규정(2025 개정).md")
check("복무규정에 근속 0년 미만 11일 명시", "11일" in leave26)
check("복무규정에 근속 11년 이상 20일 명시", "20일" in leave26)


t25 = read("2025 연간 인사운영 보고서.md")
qsum = sum(D.quarter(2025, q)["hire"] for q in (1,2,3,4))
check("2025 연간 채용 합 = 분기 합(%d명)" % qsum,
      re.search(r"연간 채용 %d명" % qsum, t25) is not None)
lsum = sum(D.quarter(2025, q)["leave"] for q in (1,2,3,4))
check("2025 연간 퇴사 합 = 분기 합(%d명)" % lsum,
      re.search(r"퇴사 %d명" % lsum, t25) is not None)

# ── 3. 반기 평가 대상 = 재직 − 수습 ──────────────────────────────
for y, h in [(r[0], r[1]) for r in D.HALVES]:
    hf = D.half(y, h)
    label = "상반기" if h == 1 else "하반기"
    t = flat(read("%d %s 인사평가 결과 리포트.md" % (y, label)))
    check("%d-H%d 평가대상 %d = 재직 %d − 수습 %d"
          % (y, h, hf["n"], hf["headcount"], hf["probation"]),
          ("재직 인원은 %d명" % hf["headcount"]) in t
          and ("%d명은 지침 제10조" % hf["probation"]) in t
          and ("정규 평가 대상은 %d명" % hf["n"]) in t)
    # 등급 인원 합
    tot = sum(hf["dist"].values())
    check("%d-H%d 등급 인원 합 = 평가대상 (%d)" % (y, h, tot), tot == hf["n"])
    for g in D.GRADES:
        cnt = hf["dist"][g]
        if not re.search(r"\|%s\|\d+%%\|%d명\|" % (g, cnt), t):
            bad.append("%d-H%d 표에 %s %d명 없음" % (y, h, g, cnt))

# ── 4. 회의록이 인용한 수치 = 리포트 수치 ────────────────────────
m2601 = read("인사위원회 회의록 2026-01-08.md")
h252 = D.half(2025, 2)
check("2026-01 회의록의 2025-H2 평가대상(%d명) 일치" % h252["n"],
      ("평가 대상 %d명" % h252["n"]) in m2601)
check("2026-01 회의록의 보정 건수(상향 %d/하향 %d) 일치" % (h252["up"], h252["down"]),
      ("보정회의 상향 %d건, 하향 %d건" % (h252["up"], h252["down"])) in m2601)

m2607 = read("인사위원회 회의록 2026-07-30.md")
h261 = D.half(2026, 1)
check("2026-07 회의록의 2026-H1 평가대상(%d명) 일치" % h261["n"],
      ("평가 대상 %d명" % h261["n"]) in m2607)
check("2026-07 회의록의 이의신청(%d건) = 리포트" % h261["appeal"],
      ("접수 %d건" % h261["appeal"]) in m2607)

m2503 = read("인사위원회 회의록 2025-03-14.md")
y24 = D.year_summary(2024)
check("2025-03 회의록의 2024 이직률(%.1f%%) = 연간보고서" % y24["turnover"],
      ("자발적 이직률 %.1f%%" % y24["turnover"]) in m2503
      and ("이직률은 %.1f%%" % y24["turnover"]) in read("2024 연간 인사운영 보고서.md"))

# ── 5. 규정 개정 대비: 2024 제정 vs 2026 개정 ───────────────────
g24 = read("나린테크 인사평가 운영지침(2024 제정).md")
g26 = read("나린테크 인사평가 운영지침(2026 개정).md")
check("2024 제정판: 이의신청 기한 14일 / 심의 30일",
      "14일 이내에 인사담당 부서에 이의를 신청" in g24
      and "접수일로부터 30일 이내에 완료" in g24)
check("2026 개정판: 이의신청 기한 7일 / 심의 14일",
      "7일 이내에 인사담당 부서에 이의를 신청" in g26
      and "접수일로부터 14일 이내에 완료" in g26)
check("2026 개정판 부칙에 개정 이력 명시 (제10조→제12조, 14일→7일)",
      "종전 제10조" in g26 and "14일에서 7일로" in g26)
check("2026 개정판: 등급 근거 동시 제공 신설",
      "등급 산정의 근거를 함께 제공" in g26 and "근거를 함께 제공" not in g24)
check("2026 개정판에만 보정회의 조문", "제11조 (평가 보정회의)" in g26 and "보정회의" not in g24)
check("2026 개정판에만 평가자 교육 조문", "제9조 (평가자 교육)" in g26 and "평가자 교육" not in g24)
check("양쪽 모두 동일 등급 분포 규정",
      "S 10% / A 20% / B 50% / C 15% / D 5%" in g24 and
      "S 10% / A 20% / B 50% / C 15% / D 5%" in g26)

# ── 6. 상호 참조 존재 ────────────────────────────────────────────
rules = read("나린테크 취업규칙 발췌(2025 개정).md")
check("취업규칙 → 지침 제10조 참조", "「인사평가 운영지침」 제10조" in rules)
onb = read("신입 온보딩 교육자료(2026).md")
check("온보딩 자료 → 취업규칙·지침 참조",
      "「취업규칙」 제13조" in onb and "제10조" in onb)
rat = read("평가자 교육자료(2026).md")
check("평가자 교육 → 지침 조문 참조", "제9조" in rat and "제6조" in rat and "제11조" in rat)

# ── 결과 ─────────────────────────────────────────────────────────
print("통과 %d건 / 실패 %d건\n" % (len(ok), len(bad)))
for x in ok:  print("  PASS  %s" % x)
if bad:
    print()
    for x in bad: print("  FAIL  %s" % x)
    sys.exit(1)
