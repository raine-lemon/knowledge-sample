# Vault Ingest Log

`wiki/VAULT_MEMORY.md`에서 분리한 vault 실행 이력 원장이다. **세션 시작 시 로드하지 않는다.**
"2026-07-17에 무엇을 처리했는지" 같은 질문이 생겼을 때만 읽는다.

- Append-only. 기존 항목을 편집하거나 삭제하지 않는다.
- ingest 1회 = bullet 1개. 상시 로드되지 않으므로 서술 길이 제한은 없다.
- `wiki/VAULT_MEMORY.md`에는 최신 1건의 요약 한 줄만 남긴다(교체, append 아님).
  예산 규칙은 `VAULT_RULES.md` § Core Rules 참조.
- 각 실행의 전체 변경 내역은 git 이력과 해당 PR 본문에도 남아 있다. 이 파일은 네트워크 없이
  grep할 수 있는 로컬 색인 역할을 한다.

## Ingest Runs

<!-- ingest 1회 = bullet 1개. 새 항목은 이 섹션 끝에 append한다. -->

