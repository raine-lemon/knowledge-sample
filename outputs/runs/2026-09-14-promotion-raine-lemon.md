---
type: run-log
kind: promotion
run_date: "2026-09-14"
author: raine-lemon
summary: "Drive 사본 5건 중 4건은 자격증명이라 제외. 남은 1건은 clipping이 아닌 repo 문서로 판정, dou-app deploy 정본을 승격했다. 레인 단독, wiki 0건."
pr:
processed: 1
new_notes: 0
updated_notes: 0
tags: [promotion, dou-app, mobile-deploy]
sources:
  - "raw/dou-app-deploy-e2529a7c0.md"
notes: []
---

# 2026-09-14 승격 — dou-app 모바일 배포 파이프라인

## Summary

사용자가 `~/Downloads/drive-download-20260825T015602Z-1-001`를 인제스트 대상으로 제시했다. 5개 파일 중 4개가 실운영 자격증명이라 전량 제외했고, 남은 문서 1건은 clipping이 아니라 repo 문서로 판정되어 `vault-ingest`가 아닌 `vault-promote` 레인으로 처리했다. 산출은 raw 스냅샷 1건 + repo 등록 1건 + 도메인 레인 1건이고 wiki 신규 노트는 0건이다.

## Details

**대상 판정.** 제시된 폴더의 구성은 `.env`, `AuthKey_9LRM8VHB8D.p8`, `play-service-account-dev.json`, `play-service-account-prod.json`, `자동배포.md`였다. 앞의 4개는 App Store Connect / Play Console 배포 자격증명이다. 이 vault는 git 추적되는 공용 팀 볼트이고 ingest 산출물은 PR로 올라가므로 커밋 시 4개 스토어 앱의 서명·배포 권한이 그대로 노출된다 (`VAULT_RULES.md` § Core Rules). 인제스트하지 않았고, 사본도 남기지 않았다.

확인 결과 이 4개는 이미 `lemoncloud-io/dou-app`의 `apps/mobile/fastlane/`에 배치되어 있고 gitignore도 걸려 있다 (`.gitignore` `*.p8`, `apps/mobile/fastlane/*.json`, `.env` 3개 규칙). Drive 사본은 중복이었다.

**레인 판정.** `자동배포.md`는 `apps/mobile/docs/deploy.md`와 내용이 동일한 prettier 적용 전 판이었다. 표·리스트 정렬 공백만 다르고 문장은 일치한다. 따라서 `docs/raw-layout.md` 레인 2(repo-doc 스냅샷)이며 `Clippings/` 경유 웹 클리핑 레인이 아니다. 스냅샷은 Drive의 낡은 사본이 아니라 repo 정본(`e2529a7c0`, `origin/develop` 도달 확인)을 떴다.

**배치 판정 — 레인 단독, wiki 0건.** `vault-promote` § 절차 4의 기본값을 적용했다. 문서 내용은 배포 대상 4개 앱의 식별자·채널, fastlane 자격증명 배치, `yarn mobile:*` 명령 계보, repo 파일별 역할표로 전부 dou-app 실행 컨텍스트다. "repo 이름을 지워도 다른 팀이 읽을 수 있는 개념"에 가장 가까운 후보는 스토어의 빌드번호 단조 증가 제약이었으나, 단독 wiki 노트로 뽑으면 이 vault의 기존 topic 두 개(knowledge-management, human-resources) 어디에도 걸리지 않는 고아 문서가 된다. § 절차 4의 "애매하면 레인 하나로 둔다"에 따라 레인으로 접었고, 해당 게이트는 레인 README `## 운영 게이트`에 서술로 남겼다.

**repo 등록.** `lemoncloud-io/dou-app`이 추적 계층에 없어 `projects/@lemoncloud-io/dou-app/README.md`를 함께 생성했다 (`vault-promote` § 절차 1). 기본 브랜치가 `master`가 아니라 `develop`이라 frontmatter `branch`에 고정했다. org 인덱스와 메인 인덱스 org 행(1 repos → 2 repos)을 같은 커밋에서 갱신했다.

**검증.** 스냅샷 capture header 7키 충족, 본문은 정본과 diff 0 (`git show e2529a7c0:apps/mobile/docs/deploy.md` 대조). wiki 노트 0건이라 `wiki/INDEX.md`·`wiki/topics/` 갱신 대상 없음. 기존 raw/·archive/ 수정·rename·삭제 없음.

## Dropped / Issues

- **탈락 4건 (자격증명)**: `.env`, `AuthKey_9LRM8VHB8D.p8`, `play-service-account-dev.json`, `play-service-account-prod.json`. 사유는 위 Details 참조. repo에 이미 배치·gitignore되어 있으므로 vault 조치는 없고, Drive 사본과 `~/Downloads` 잔여본 정리는 사용자 몫으로 남겼다.
- **needs-update 없음.** 정본 commit이 `origin/develop`에 도달해 있어 미머지 캐비앳이 필요 없다.
- **후속**: `projects/@lemoncloud-io/dou-app/README.md`의 `goal`·`next_action`은 등록 시 초안이다. 최종값은 사용자가 정한다 (`docs/github-linked-projects.md` § Write Boundaries).
