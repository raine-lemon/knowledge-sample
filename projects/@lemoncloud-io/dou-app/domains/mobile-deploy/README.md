---
type: domain
canonical: repo
source_path: "apps/mobile/docs/deploy.md"
source_branch: "develop"
source_commit: "e2529a7c0"
last_synced: 2026-09-14
---

# mobile-deploy

iOS/Android × dev/prod 4개 스토어 앱을 로컬 맥에서 명령 한 번으로 업로드하는 fastlane 파이프라인. 정본은 repo 문서이고, 이 노트는 정본 관계와 운영 게이트만 담는다.

## Snapshot

- 원문 스냅샷: `raw/dou-app-deploy-e2529a7c0.md` (capture header 외 본문 무수정)
- 정본: `lemoncloud-io/dou-app@e2529a7c0` — `apps/mobile/docs/deploy.md`, `origin/develop` 도달 확인
- drift는 이 사본을 고쳐서가 아니라 재승격으로 해소한다 (`canonical: repo`)

## 운영 게이트

- **업로드까지만 자동이다.** 심사 제출·출시 버튼은 사람이 누른다 — 파이프라인이 스토어에 올려놓는 지점에서 멈춘다.
- **빌드번호는 되돌릴 수 없다.** 스토어가 같은 `versionCode`/`CFBundleVersion` 재업로드를 거부하므로, 성공한 업로드를 다시 올리려면 `yarn mobile:version build`가 선행돼야 한다. 업로드 실패 후 단순 재시도와 구분된다.
- **버전 진실원은 Android `build.gradle`이다.** `version-mobile.js`가 iOS와 어긋나면 "out of sync"로 중단한다 — 한쪽 플랫폼만 수동 수정한 흔적이다.
- **dev/prod Play 계정이 다르다.** Android dev/prod는 서로 다른 Google Cloud 계정이라 서비스 계정 JSON이 2개 필요하다 (`PLAY_JSON_KEY_PATH`, `PLAY_JSON_KEY_PATH_DEV`).

## 자격증명 경계

배포 자격증명(App Store Connect `.p8`, Play 서비스 계정 JSON 2개, fastlane `.env`, Android keystore)은 repo의 `apps/mobile/fastlane/`에 두고 **전부 gitignore된다**. vault는 이 파일들을 사본으로도 보관하지 않는다 — 이 레인이 담는 것은 배치 규칙까지다 (`VAULT_RULES.md` § Core Rules).

2026-09-14 승격 시 이 4개 파일이 Google Drive 공유본으로 vault 인제스트 대상에 섞여 들어왔고, 자격증명이라 전량 제외했다. 배포 자격증명은 Drive 경유로 돌리지 않는 편이 안전하다.
