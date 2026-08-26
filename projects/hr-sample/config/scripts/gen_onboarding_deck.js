// 신입 온보딩 오리엔테이션 덱 생성기 (12슬라이드, 16:9).
// 출력: projects/hr-sample/outputs/2026-onboarding-orientation.pptx
// 사용:  npm install pptxgenjs && node gen_onboarding_deck.js <out.pptx>
// 근거 자료: raw/신입 온보딩 교육자료(2026).md, raw/나린테크 인사팀 업무 매뉴얼(SOP).md,
//           wiki/onboarding-30-60-90.md, wiki/probation-evaluation.md, 2025 연간·분기 리포트.
// 이 코퍼스의 다른 생성기(gen_*.py)와 달리 Node + pptxgenjs를 쓴다.
// 슬라이드 11의 막대그래프는 네이티브 차트가 Keynote에서 렌더되지 않아 도형으로 그린다.
const pptxgen = require("pptxgenjs");
const p = new pptxgen();
p.layout = "LAYOUT_WIDE"; // 13.33 x 7.5
p.author = "나린테크 인사담당";
p.title = "신입 온보딩 오리엔테이션 (2026)";

const F = "Apple SD Gothic Neo";
const DARK = "0B2E36", TEAL = "028090", SEA = "00A896", MINT = "02C39A";
const TXT = "22323A", MUTED = "6B7A80", TINT = "EAF4F5", WHITE = "FFFFFF";
const M = 0.6;

function title(s, t, sub) {
  s.addText(t, { x: M, y: 0.42, w: 12.1, h: 0.62, fontFace: F, fontSize: 34, bold: true, color: TXT, isTextBox: true, margin: 0 });
  if (sub) s.addText(sub, { x: M, y: 1.06, w: 12.1, h: 0.34, fontFace: F, fontSize: 13, color: MUTED, isTextBox: true, margin: 0 });
}
function numCircle(s, x, y, n, d, fill) {
  s.addShape(p.ShapeType.ellipse, { x, y, w: d, h: d, fill: { color: fill || TEAL } });
  s.addText(n, { x, y, w: d, h: d, fontFace: F, fontSize: d > 0.6 ? 20 : 14, bold: true, color: WHITE, align: "center", valign: "middle", isTextBox: true, margin: 0 });
}
function card(s, x, y, w, h, fill) {
  s.addShape(p.ShapeType.roundRect, { x, y, w, h, rectRadius: 0.08, fill: { color: fill || TINT }, line: { color: fill || TINT, width: 0 } });
}

/* ---------- 1. Title ---------- */
let s = p.addSlide();
s.background = { color: DARK };
s.addText("신입 온보딩 오리엔테이션", { x: M, y: 2.1, w: 8.4, h: 0.9, fontFace: F, fontSize: 42, bold: true, color: WHITE, isTextBox: true, margin: 0 });
s.addText("입사 후 3개월, 독립까지의 설계도", { x: M, y: 3.05, w: 8.4, h: 0.45, fontFace: F, fontSize: 19, color: MINT, isTextBox: true, margin: 0 });
s.addText("(주)나린테크 인사담당  ·  2026-08-26 세션용  ·  2026년 1월판 교육자료 기준", { x: M, y: 3.72, w: 8.4, h: 0.35, fontFace: F, fontSize: 13, color: "9BB0B5", isTextBox: true, margin: 0 });
s.addText("근거 문서 — 인사평가 운영지침(HR-REG-001) · 취업규칙(HR-REG-002) · 급여규정(HR-REG-003) · 복무규정(HR-REG-004) · 인사팀 SOP(HR-SOP-001)",
  { x: M, y: 6.5, w: 12.1, h: 0.5, fontFace: F, fontSize: 10, color: "7A9198", isTextBox: true, margin: 0 });
s.addShape(p.ShapeType.ellipse, { x: 9.6, y: 1.85, w: 3.0, h: 3.0, fill: { color: TEAL } });
s.addText([{ text: "90", options: { fontSize: 62, bold: true, color: WHITE, breakLine: true } },
           { text: "일 안에 결정된다", options: { fontSize: 14, color: "CDEDEF" } }],
  { x: 9.6, y: 2.35, w: 3.0, h: 2.0, fontFace: F, align: "center", isTextBox: true, margin: 0 });
s.addNotes("가상 샘플 코퍼스 기반 자료. 세션 시작 시 목적(3개월 내 독립)과 근거 문서 체계를 먼저 공유한다.");

/* ---------- 2. Why ---------- */
s = p.addSlide();
title(s, "왜 첫 90일을 설계하는가", "조기 퇴사 의사는 입사 초기에 형성되고, 실제 퇴사는 몇 달 뒤에 일어난다");
const why = [
  ["명시적 목표", "30·60·90일 단위 달성 기준이 문서로 있어야 한다. \"적응하세요\"는 목표가 아니다."],
  ["평가자가 아닌 멘토", "멘토가 평가 권한을 함께 가지면 입사자는 모르는 것을 묻지 않는다."],
  ["첫 완결 경험", "60일 안에 작은 과제라도 처음부터 끝까지 혼자 끝내본 경험이 필요하다."],
  ["예측 가능한 수습평가", "기준을 모른 채 평가받는 경험은 조직 신뢰를 크게 훼손한다."],
];
why.forEach(([h, d], i) => {
  const y = 1.62 + i * 1.32;
  numCircle(s, M, y, String(i + 1), 0.62, i % 2 ? SEA : TEAL);
  s.addText(h, { x: 1.4, y: y - 0.02, w: 6.9, h: 0.34, fontFace: F, fontSize: 17, bold: true, color: TXT, isTextBox: true, margin: 0 });
  s.addText(d, { x: 1.4, y: y + 0.33, w: 6.9, h: 0.6, fontFace: F, fontSize: 12.5, color: MUTED, isTextBox: true, margin: 0 });
});
card(s, 8.9, 1.62, 3.8, 4.6, TINT);
s.addText([{ text: "89.9%", options: { fontSize: 52, bold: true, color: TEAL, breakLine: true } },
           { text: "누적 수습 통과율", options: { fontSize: 15, bold: true, color: TXT, breakLine: true } },
           { text: "2024-Q1 이후 입사 신입 119명 중 107명 정규 전환", options: { fontSize: 12, color: MUTED, breakLine: true } }],
  { x: 9.2, y: 1.95, w: 3.3, h: 2.1, fontFace: F, valign: "top", isTextBox: true, margin: 0 });
s.addText([{ text: "13.9%", options: { fontSize: 30, bold: true, color: "B85042", breakLine: true } },
           { text: "전체 퇴사 72건 중 \"수습 미전환\" 10건, 평균근속 0.32년", options: { fontSize: 12, color: MUTED } }],
  { x: 9.2, y: 4.15, w: 3.3, h: 1.6, fontFace: F, valign: "top", isTextBox: true, margin: 0 });
s.addText("온보딩에 쓰는 시간은 비용이 아니라, 이미 지출한 채용 비용을 지키는 일이다.",
  { x: M, y: 6.85, w: 12.1, h: 0.35, fontFace: F, fontSize: 12, italic: true, color: TEAL, isTextBox: true, margin: 0 });

/* ---------- 3. Agenda ---------- */
s = p.addSlide();
title(s, "오늘 세션 흐름", "약 60분 — 제도 안내 후 30-60-90일 목표 초안 작성으로 마무리합니다");
const ag = [["온보딩의 목표", "3개월 안에 독립"], ["입사 첫 주", "D+1 ~ D+5 체크리스트"], ["30-60-90일 플랜", "이해 · 기여 · 독립"],
             ["멘토 제도", "역할과 평가 분리"], ["수습평가", "판단 기준과 연장 조항"], ["처우 · 첫 평가", "급여·복리후생·반기 사이클"]];
ag.forEach(([h, d], i) => {
  const x = M + (i % 3) * 4.12, y = 1.7 + Math.floor(i / 3) * 2.6;
  card(s, x, y, 3.85, 2.35, i % 2 ? WHITE : TINT);
  if (i % 2) s.addShape(p.ShapeType.roundRect, { x, y, w: 3.85, h: 2.35, rectRadius: 0.08, fill: { color: WHITE }, line: { color: "D6E5E7", width: 1 } });
  numCircle(s, x + 0.32, y + 0.32, String(i + 1), 0.5, i % 2 ? SEA : TEAL);
  s.addText(h, { x: x + 0.32, y: y + 1.15, w: 3.2, h: 0.34, fontFace: F, fontSize: 16, bold: true, color: TXT, valign: "top", isTextBox: true, margin: 0 });
  s.addText(d, { x: x + 0.32, y: y + 1.58, w: 3.2, h: 0.4, fontFace: F, fontSize: 12, color: MUTED, valign: "top", isTextBox: true, margin: 0 });
});

/* ---------- 4. Goal ---------- */
s = p.addSlide();
s.background = { color: DARK };
s.addText("온보딩의 목표", { x: M, y: 0.7, w: 12.1, h: 0.6, fontFace: F, fontSize: 34, bold: true, color: WHITE, isTextBox: true, margin: 0 });
s.addText("입사 후 3개월 안에 독립적으로 업무를 수행할 수 있는 상태에 도달한다.\n회사의 일하는 방식과 평가·보상 기준을 정확히 이해한다.",
  { x: M, y: 1.5, w: 8.0, h: 1.0, fontFace: F, fontSize: 17, color: "CDEDEF", lineSpacing: 26, isTextBox: true, margin: 0 });
const goals = [["3개월", "수습기간", "입사일로부터 · 취업규칙 제12조\n2025-07-01 개정으로 6개월 → 3개월"],
                ["D-14", "수습평가 실시", "수습기간 종료 2주 전 · 지침 제10조"],
                ["첫 주", "목표 확정", "멘토와 30-60-90일 목표를 함께 작성\n이후 변경은 멘토 합의 사항"]];
goals.forEach(([n, h, d], i) => {
  const x = M + i * 4.12;
  s.addShape(p.ShapeType.roundRect, { x, y: 3.0, w: 3.85, h: 2.9, rectRadius: 0.08, fill: { color: "12414B" }, line: { color: "12414B", width: 0 } });
  s.addText(n, { x: x + 0.35, y: 3.3, w: 3.15, h: 0.8, fontFace: F, fontSize: 40, bold: true, color: MINT, isTextBox: true, margin: 0 });
  s.addText(h, { x: x + 0.35, y: 4.15, w: 3.15, h: 0.35, fontFace: F, fontSize: 16, bold: true, color: WHITE, isTextBox: true, margin: 0 });
  s.addText(d, { x: x + 0.35, y: 4.6, w: 3.15, h: 1.1, fontFace: F, fontSize: 11.5, color: "9BB0B5", valign: "top", isTextBox: true, margin: 0 });
});
s.addText("수습은 신분이나 처우를 낮추는 기간이 아니라 판단 기간이다.",
  { x: M, y: 6.4, w: 12.1, h: 0.35, fontFace: F, fontSize: 13, italic: true, color: MINT, isTextBox: true, margin: 0 });

/* ---------- 5. First week ---------- */
s = p.addSlide();
title(s, "입사 첫 주 체크리스트", "D+1 ~ D+5 — 인사팀 SOP는 입사 D-3에 장비·계정 신청과 멘토 배정 요청을 끝낸다");
const wk = [["D+1", "계정·장비 세팅\n사내 시스템 접근 권한 신청"], ["D+1", "멘토 배정 확인\n첫 1:1 일정 예약"],
            ["D+2~3", "팀 온보딩 문서 리뷰\n제품·고객·용어 정리"], ["D+3", "30-60-90일 목표 초안\n멘토와 함께 작성"],
            ["D+5", "인사담당 오리엔테이션\n급여·복리후생·근태 안내"]];
wk.forEach(([d, t], i) => {
  const x = M + i * 2.47;
  card(s, x, 1.85, 2.27, 2.55, TINT);
  s.addShape(p.ShapeType.roundRect, { x: x + 0.28, y: 2.15, w: 0.95, h: 0.42, rectRadius: 0.06, fill: { color: i < 2 ? TEAL : SEA } });
  s.addText(d, { x: x + 0.28, y: 2.15, w: 0.95, h: 0.42, fontFace: F, fontSize: 13, bold: true, color: WHITE, align: "center", valign: "middle", isTextBox: true, margin: 0 });
  s.addText(t, { x: x + 0.28, y: 2.72, w: 1.92, h: 1.9, fontFace: F, fontSize: 12.5, color: TXT, lineSpacing: 19, valign: "top", isTextBox: true, margin: 0 });
});
card(s, M, 5.3, 12.13, 1.35, WHITE);
s.addShape(p.ShapeType.roundRect, { x: M, y: 5.3, w: 12.13, h: 1.35, rectRadius: 0.08, fill: { color: WHITE }, line: { color: "D6E5E7", width: 1 } });
s.addText([{ text: "근태·재택근무 기준", options: { bold: true, color: TXT } },
           { text: "은 「복무규정」(HR-REG-004) 제2장을 참조합니다. 오리엔테이션에서 급여·복리후생·근태를 함께 안내하고, 인사담당은 30일·60일 시점에 목표 진행 상황을 체크인합니다.", options: { color: MUTED } }],
  { x: 1.6, y: 5.1, w: 10.6, h: 0.85, fontFace: F, fontSize: 13, valign: "middle", isTextBox: true, margin: 0 });
numCircle(s, 0.85, 5.27, "!", 0.5, TEAL);

/* ---------- 6. 30-60-90 ---------- */
s = p.addSlide();
title(s, "30-60-90일 플랜", "목표는 입사 첫 주에 확정하고, 이후 변경은 멘토 합의 사항");
const plan = [["30", "이해", TEAL, ["팀의 제품·고객·용어 파악", "개발환경 세팅 완료", "멘토와 주 2회 30분 정기 면담"]],
              ["60", "기여", SEA, ["작은 단위 과제를 처음부터 끝까지 단독 완료 (최소 2건)", "코드리뷰에 리뷰어로 참여 시작"]],
              ["90", "독립", MINT, ["팀 스프린트에 정규 인원으로 편성", "수습평가 대상 목표의 달성 여부를 멘토와 함께 점검"]]];
plan.forEach(([n, h, c, items], i) => {
  const x = M + i * 4.12;
  card(s, x, 1.75, 3.85, 3.45, TINT);
  numCircle(s, x + 0.35, 2.05, n, 0.85, c);
  s.addText(h, { x: x + 1.35, y: 2.2, w: 2.2, h: 0.5, fontFace: F, fontSize: 22, bold: true, color: TXT, valign: "middle", isTextBox: true, margin: 0 });
  s.addText(items.map((t, k) => ({ text: t, options: { bullet: true, breakLine: k < items.length - 1 } })),
    { x: x + 0.4, y: 3.05, w: 3.15, h: 2.7, fontFace: F, fontSize: 13, color: TXT, lineSpacing: 20, paraSpaceAfter: 8, valign: "top", isTextBox: true, margin: 0 });
});
s.addText("이 목표가 그대로 수습평가의 판단 기준이 됩니다 — 교육 커리큘럼이 아니라 첫 주에 양쪽이 합의하는 평가 계약에 가깝습니다.",
  { x: M, y: 5.45, w: 12.1, h: 0.4, fontFace: F, fontSize: 13, italic: true, color: TEAL, isTextBox: true, margin: 0 });

/* ---------- 7. Mentor ---------- */
s = p.addSlide();
title(s, "멘토 제도", "「취업규칙」 제14조 — 멘토는 같은 팀의 선임 1명으로 지정한다");
s.addText("멘토의 역할", { x: M, y: 1.8, w: 6.6, h: 0.35, fontFace: F, fontSize: 20, bold: true, color: TXT, isTextBox: true, margin: 0 });
s.addText([
  { text: "30-60-90일 목표 수립 지원", options: { bullet: true, breakLine: true } },
  { text: "주간 면담 — 30일 구간은 주 2회 30분", options: { bullet: true, breakLine: true } },
  { text: "막힌 지점 해소", options: { bullet: true, breakLine: true } },
  { text: "팀 내 관계 형성 지원 — 첫 2주간 회의 동석", options: { bullet: true, breakLine: true } },
  { text: "온보딩 완료 후 회고를 인사담당에 제출", options: { bullet: true } },
], { x: M, y: 2.3, w: 6.5, h: 3.2, fontFace: F, fontSize: 14.5, color: TXT, lineSpacing: 22, paraSpaceAfter: 10, valign: "top", isTextBox: true, margin: 0 });
s.addShape(p.ShapeType.roundRect, { x: 7.5, y: 1.75, w: 5.23, h: 4.4, rectRadius: 0.08, fill: { color: DARK }, line: { color: DARK, width: 0 } });
s.addText("멘토는 평가자가 될 수 없다", { x: 7.9, y: 2.1, w: 4.4, h: 0.8, fontFace: F, fontSize: 24, bold: true, color: MINT, isTextBox: true, margin: 0 });
s.addText([
  { text: "1차 평가자는 직속 상급자입니다.", options: { breakLine: true, color: WHITE } },
  { text: "멘토 의견은 수습평가의 참고자료로만 사용됩니다.", options: { breakLine: true, color: WHITE } },
  { text: "", options: { breakLine: true } },
  { text: "멘토가 평가 권한을 함께 가지면 신규 입사자는 모르는 것을 묻지 않습니다. 질문이 곧 약점의 노출이 되기 때문입니다.", options: { color: "9BB0B5" } },
], { x: 7.9, y: 2.95, w: 4.4, h: 2.9, fontFace: F, fontSize: 13.5, lineSpacing: 22, valign: "top", isTextBox: true, margin: 0 });

/* ---------- 8. Probation ---------- */
s = p.addSlide();
title(s, "수습평가 기준", "수습평가는 상대평가가 아니다 — 30-60-90일 목표의 달성 여부만 본다");
const cmp = [["정규 인사평가", "A7BEAE", ["등급 분포 준수 — S 10% / A 20% / B 50% / C 15% / D 5%", "조직 내 상대 위치를 가리는 절차", "성과 70점(OKR) + 역량 30점"]],
             ["수습평가", TEAL, ["등급 분포를 적용하지 않는다 — 지침 제10조 제2항", "목표 달성 여부만 보는 절대 판단 — 제10조 제3항", "결과는 정규 전환 여부 판단의 근거"]]];
cmp.forEach(([h, c, items], i) => {
  const x = M + i * 6.27;
  card(s, x, 1.75, 5.86, 3.3, i ? TINT : "F4F6F4");
  s.addText(h, { x: x + 0.4, y: 2.0, w: 5.0, h: 0.42, fontFace: F, fontSize: 20, bold: true, color: i ? TEAL : "5C6B60", isTextBox: true, margin: 0 });
  s.addText(items.map((t, k) => ({ text: t, options: { bullet: true, breakLine: k < items.length - 1 } })),
    { x: x + 0.4, y: 2.55, w: 5.1, h: 2.3, fontFace: F, fontSize: 13.5, color: TXT, lineSpacing: 21, paraSpaceAfter: 9, valign: "top", isTextBox: true, margin: 0 });
});
s.addShape(p.ShapeType.roundRect, { x: M, y: 5.35, w: 12.13, h: 1.35, rectRadius: 0.08, fill: { color: DARK }, line: { color: DARK, width: 0 } });
s.addText([{ text: "기준 미달 시 ", options: { color: WHITE } },
           { text: "1회에 한해 1개월 연장", options: { color: MINT, bold: true } },
           { text: "할 수 있습니다 (취업규칙 제13조 제3항). 연장 후에도 미달이면 정규 전환을 하지 않을 수 있고, 이때 사유를 서면으로 통지합니다 (제4항).", options: { color: WHITE } }],
  { x: 1.6, y: 5.6, w: 10.55, h: 0.85, fontFace: F, fontSize: 13.5, valign: "middle", isTextBox: true, margin: 0 });
numCircle(s, 0.85, 5.77, "+", 0.5, SEA);

/* ---------- 9. Pay & benefits ---------- */
s = p.addSlide();
title(s, "수습기간 중 급여·복리후생", "「취업규칙」·「급여규정」·「복무규정」 발췌");
const pay = [["임금 100%", "수습기간 중 임금은 정규 임금의 100%\n취업규칙 제12조 제3항", TEAL, true],
             ["상여금 미지급", "상여금은 수습기간 중 지급하지 않는다\n급여규정 제9조 제4항", "B85042", false],
             ["연차 매월 1일", "입사 첫 달부터 매월 1일씩 발생 (최대 11일)\n복무규정 제5조", SEA, true],
             ["재택근무 불가", "수습기간 중에는 신청할 수 없다\n복무규정 제3조 제3항", "B85042", false]];
pay.forEach(([h, d, c, ok], i) => {
  const x = M + (i % 2) * 6.27, y = 1.8 + Math.floor(i / 2) * 2.35;
  card(s, x, y, 5.86, 2.05, TINT);
  numCircle(s, x + 0.38, y + 0.35, ok ? "O" : "X", 0.55, c);
  s.addText(h, { x: x + 1.15, y: y + 0.38, w: 4.4, h: 0.4, fontFace: F, fontSize: 18, bold: true, color: TXT, isTextBox: true, margin: 0 });
  s.addText(d, { x: x + 1.15, y: y + 0.92, w: 4.5, h: 0.9, fontFace: F, fontSize: 12.5, color: MUTED, lineSpacing: 18, valign: "top", isTextBox: true, margin: 0 });
});
s.addText("수습기간은 근속연수에 산입됩니다 (취업규칙 제12조 제2항).",
  { x: M, y: 6.6, w: 12.1, h: 0.35, fontFace: F, fontSize: 13, italic: true, color: TEAL, isTextBox: true, margin: 0 });

/* ---------- 10. First regular cycle ---------- */
s = p.addSlide();
title(s, "첫 정규 평가 사이클", "정규 전환 후 첫 평가는 다음 반기 차수부터 적용됩니다 — 상반기 1~6월 / 하반기 7~12월");
const flow = [["OKR 확정", "대상기간 개시일"], ["자기평가", "종료 +1주"], ["1차 평가", "종료 +3주"], ["2차 평가", "종료 +4주"],
              ["보정회의", "2차 마감 +1주"], ["결과 통보", "보정 종료 +3일"], ["이의신청", "통보 +7일"], ["급여 반영", "확정 익월"]];
flow.forEach(([h, d], i) => {
  const x = M + (i % 4) * 3.09, y = 1.85 + Math.floor(i / 4) * 1.75;
  card(s, x, y, 2.85, 1.4, i < 4 ? TINT : WHITE);
  if (i >= 4) s.addShape(p.ShapeType.roundRect, { x, y, w: 2.85, h: 1.4, rectRadius: 0.08, fill: { color: WHITE }, line: { color: "D6E5E7", width: 1 } });
  s.addText(String(i + 1), { x: x + 0.25, y: y + 0.15, w: 0.6, h: 0.3, fontFace: F, fontSize: 12, bold: true, color: i < 4 ? TEAL : SEA, isTextBox: true, margin: 0 });
  s.addText(h, { x: x + 0.25, y: y + 0.5, w: 2.4, h: 0.33, fontFace: F, fontSize: 15.5, bold: true, color: TXT, isTextBox: true, margin: 0 });
  s.addText(d, { x: x + 0.25, y: y + 0.88, w: 2.4, h: 0.32, fontFace: F, fontSize: 11.5, color: MUTED, isTextBox: true, margin: 0 });
});
s.addShape(p.ShapeType.roundRect, { x: M, y: 5.45, w: 12.13, h: 1.3, rectRadius: 0.08, fill: { color: DARK }, line: { color: DARK, width: 0 } });
s.addText([{ text: "성과평가 70점(OKR 달성도) + 역량평가 30점", options: { color: MINT, bold: true } },
           { text: "  ·  OKR은 대상기간 개시 시점에 확정 — 개시 후 수정은 예외 처리  ·  평가 등급은 연봉 인상률·상여 지급률에 연동 (급여규정 제8조·제9조)", options: { color: WHITE } }],
  { x: 0.95, y: 5.6, w: 11.4, h: 1.0, fontFace: F, fontSize: 13, valign: "middle", isTextBox: true, margin: 0 });

/* ---------- 11. Conversion rate ---------- */
s = p.addSlide();
title(s, "실측 — 정규 전환율", "수습평가는 형식이 아니라 실제로 결과가 갈리는 절차입니다");
const bars = [["2025 Q1", 84.6, TEAL], ["2025 Q2", 91.7, SEA], ["2025 Q3", 80.0, TEAL], ["2025 Q4", 92.9, SEA], ["2026 Q2", 93.8, MINT]];
const BASE = 5.55, TOP = 2.25, LO = 60, HI = 100, PH = BASE - TOP;
[70, 80, 90, 100].forEach(v => {
  const y = BASE - (v - LO) / (HI - LO) * PH;
  s.addShape(p.ShapeType.line, { x: 1.15, y, w: 7.3, h: 0, line: { color: "E4EDEE", width: 1 } });
  s.addText(String(v) + "%", { x: 0.6, y: y - 0.12, w: 0.52, h: 0.24, fontFace: F, fontSize: 9.5, color: MUTED, align: "right", valign: "middle", isTextBox: true, margin: 0 });
});
s.addText("분기별 수습 통과율", { x: 1.15, y: 1.72, w: 4.0, h: 0.3, fontFace: F, fontSize: 13, bold: true, color: TXT, valign: "top", isTextBox: true, margin: 0 });
bars.forEach(([lab, v, c], i) => {
  const bw = 0.98, x = 1.35 + i * 1.45, h = (v - LO) / (HI - LO) * PH;
  s.addShape(p.ShapeType.roundRect, { x, y: BASE - h, w: bw, h, rectRadius: 0.03, fill: { color: c }, line: { color: c, width: 0 } });
  s.addText(v.toFixed(1) + "%", { x: x - 0.16, y: BASE - h - 0.34, w: bw + 0.32, h: 0.3, fontFace: F, fontSize: 12, bold: true, color: TXT, align: "center", valign: "middle", isTextBox: true, margin: 0 });
  s.addText(lab, { x: x - 0.16, y: BASE + 0.08, w: bw + 0.32, h: 0.28, fontFace: F, fontSize: 11.5, color: MUTED, align: "center", valign: "middle", isTextBox: true, margin: 0 });
});
s.addShape(p.ShapeType.line, { x: 1.15, y: BASE, w: 7.3, h: 0, line: { color: "C9D9DB", width: 1 } });
card(s, 8.85, 1.7, 3.88, 4.3, TINT);
s.addText([{ text: "87.8%", options: { fontSize: 40, bold: true, color: TEAL, breakLine: true } },
           { text: "2025년 연간 — 입사 49명 중 43명 전환", options: { fontSize: 12.5, color: MUTED, breakLine: true } },
           { text: "", options: { fontSize: 10, breakLine: true } },
           { text: "읽을 때 주의", options: { fontSize: 14, bold: true, color: TXT, breakLine: true } },
           { text: "분기 모수가 10~16명이라 분기 전환율의 등락(80.0%~93.8%)을 제도 효과로 읽기는 어렵습니다. 1~2명 차이가 10%p 이상을 움직입니다.", options: { fontSize: 12, color: MUTED } }],
  { x: 9.2, y: 2.0, w: 3.3, h: 3.7, fontFace: F, valign: "top", isTextBox: true, margin: 0 });
s.addText("출처: 2025 연간 인사운영 보고서 · 2025 Q1~Q4 / 2026 Q2 채용·이직 리포트 (가상 샘플)",
  { x: M, y: 6.5, w: 12.1, h: 0.35, fontFace: F, fontSize: 10, color: MUTED, isTextBox: true, margin: 0 });

/* ---------- 12. Contacts ---------- */
s = p.addSlide();
s.background = { color: DARK };
s.addText("문의 · 근거 문서", { x: M, y: 0.75, w: 12.1, h: 0.65, fontFace: F, fontSize: 34, bold: true, color: WHITE, isTextBox: true, margin: 0 });
const ct = [["온보딩 과정 전반", "인사담당 · 내부 채널 #people-ops"], ["30-60-90일 목표 조정", "소속 팀 멘토"], ["평가·급여 제도 문의", "인사담당"]];
ct.forEach(([h, d], i) => {
  const x = M + i * 4.12;
  s.addShape(p.ShapeType.roundRect, { x, y: 1.75, w: 3.85, h: 1.6, rectRadius: 0.08, fill: { color: "12414B" }, line: { color: "12414B", width: 0 } });
  s.addText(h, { x: x + 0.35, y: 2.0, w: 3.2, h: 0.35, fontFace: F, fontSize: 15, bold: true, color: MINT, isTextBox: true, margin: 0 });
  s.addText(d, { x: x + 0.35, y: 2.5, w: 3.2, h: 0.7, fontFace: F, fontSize: 12.5, color: WHITE, valign: "top", isTextBox: true, margin: 0 });
});
s.addText("근거 문서 체계", { x: M, y: 3.75, w: 12.1, h: 0.4, fontFace: F, fontSize: 20, bold: true, color: WHITE, isTextBox: true, margin: 0 });
s.addTable([
  [{ text: "문서번호", options: { bold: true, color: WHITE } }, { text: "문서명", options: { bold: true, color: WHITE } }, { text: "다루는 내용", options: { bold: true, color: WHITE } }],
  ["HR-REG-001", "인사평가 운영지침", "평가 절차·등급·보정회의·이의신청"],
  ["HR-REG-002", "취업규칙 (발췌)", "근로시간·채용/수습·복무·휴가"],
  ["HR-REG-003", "급여규정", "직급·인상률·상여·성과급"],
  ["HR-REG-004", "복무규정", "근태·연차·경조사·병가"],
  ["HR-SOP-001", "인사팀 업무 매뉴얼", "온보딩·채용·오프보딩 실행 절차"],
], {
  x: M, y: 4.3, w: 12.13, colW: [1.9, 3.4, 6.83], border: { type: "solid", color: "1D4E58", pt: 1 },
  fontFace: F, fontSize: 12, color: "CDEDEF", fill: { color: "0F3841" }, rowH: 0.34, valign: "middle", margin: 0.08,
});
s.addText("※ 본 자료는 지식관리 파이프라인 검증용 가상 샘플입니다. 실존 기업·인물과 무관합니다.",
  { x: M, y: 6.9, w: 12.1, h: 0.3, fontFace: F, fontSize: 10, color: "7A9198", isTextBox: true, margin: 0 });

p.writeFile({ fileName: process.argv[2] }).then(f => console.log("wrote " + f));
