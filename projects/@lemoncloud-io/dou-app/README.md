---
type: project
repo: "lemoncloud-io/dou-app"
scope: team
branch: "develop"
status: active
goal: "React Native 하이브리드 모바일 앱을 포함한 DoU Nx 모노레포의 구조·배포 파이프라인을 vault 추적 계층에 연결한다."
due:
milestones: []
next_action: "goal·next_action 최종값을 사용자 승인 후 확정한다 (등록 시 초안)."
last_synced: 2026-09-14
---

# dou-app

## Status

Active. `lemoncloud-io` org의 Nx 모노레포로 web·mobile·admin 4개 앱과 15개 공유 라이브러리를 담는다. 이 노트는 2026-09-14 배포 문서 승격을 계기로 repo를 추적 계층에 등록한 것이다. 기본 브랜치가 `master`가 아니라 `develop`이라 frontmatter `branch`에 고정했다.

## Purpose

모바일 배포 파이프라인처럼 여러 사람이 같은 절차를 반복 실행하는 repo 문서를, 정본이 움직여도 팀이 시점 고정본으로 읽을 수 있게 vault에 붙잡아 둔다.

## Related Wiki

없음. 2026-09-14 승격의 배치 판정은 레인 단독이었다 — 근거는 `outputs/runs/2026-09-14-promotion-raine-lemon.md`.

## Sync Notes

- 2026-09-14: `vault-promote` 실행 중 미등록 repo임이 확인되어 등록. 로컬 클론은 `$GITHUB_DIR/lemoncloud-io/dou-app`. 추적 브랜치 `develop`.
- `goal`·`next_action`은 등록 시 초안이다. 최종값은 사용자가 정한다 (`docs/github-linked-projects.md` § Write Boundaries).
