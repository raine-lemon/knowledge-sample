# areas/

PARA의 A — 상시 책임영역. 종료일이 없는 지속 활동을 담는다.

| 하위 | 역할 |
|---|---|
| `daily/` | 일일 노트 `YYYY-MM-DD.md`. 템플릿: `templates/daily-note.md` |
| `weekly/` | 주간 보고서 `YYYY-MM-DD.md`(보고일) + 같은 이름 `.html` 뷰. 템플릿: `templates/weekly-report.{md,html}` |
| `ideas/` | 아이디어 노트 `<slug>.md`. 템플릿: `templates/idea.md`. status로 성장 추적 |

- daily 노트는 하루 1개. Hermes `vault-daily-brief`가 생성, `vault-daily-close`가 마감.
- weekly 보고서는 주 1개. `vault-weekly-report` 스킬이 git 전수 통계로 집계해 생성.
- 아이디어가 `ready`가 되면 프로젝트로 승격하거나 wiki 개념으로 전환한다.
