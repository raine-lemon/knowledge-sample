---
name: private-note
description: >
  사용자의 개인 업무/연구 노트를 `private/YYYY-MM-DD.md`에 열거나 새로 만든다.
  이 폴더는 git에 커밋되지 않는 로컬 전용 스크래치 공간이다. 사용자가 "오늘
  private 노트 시작해줘", "개인 노트 열어줘", "private에 기록해줘"처럼 개인
  전용 기록을 요청할 때 사용한다. (팀에 공유되는 `areas/daily/` 노트와는
  별개이며, 그 스킬과 혼동하지 않는다.)
origin: lemoncloud-io/knowledge@01f358b:projects/second-brain/config/skills/private-note.md
---

# Private Note (개인 전용, git 비추적)

`private/`는 이 vault 안에서 유일하게 git 추적 대상이 아닌 개인 작업 공간이다.
팀과 공유되는 `areas/daily/`와 달리, 형식에 얽매이지 않는 자유 기록용이며
저장 즉시 팀 vault에는 절대 노출되지 않는다.

## 언제 사용하는가

- 사용자가 "오늘 private 노트 시작해줘", "개인 노트 열어줘"처럼 개인 전용
  기록을 요청할 때
- 실험적 시도, 진행 중인 생각, 아직 공유하기 이른 관찰을 적어둘 때
- `areas/daily/` 공용 데일리 노트와는 별개로 개인 메모가 필요할 때

## 전제 조건

- vault root는 `CLAUDE.md` § Vault Root 규칙을 따라 확인한다.
- `.gitignore`에 `private/` 항목이 있어야 한다. 없으면 먼저 추가하고 사용자에게
  알린다 (이 항목이 없으면 이 스킬로 만든 파일이 실수로 커밋될 수 있다).

## 절차

1. 현재 날짜를 `date +%F`로 얻는다 (추측하지 않는다).
2. `private/` 디렉터리가 없으면 생성한다 (`mkdir -p private`).
3. 대상 파일은 `private/YYYY-MM-DD.md` (오늘 날짜 기준).
4. 파일이 이미 있으면 그대로 이어서 사용한다 (덮어쓰지 않는다).
5. 파일이 없으면 `templates/private-note.md`를 읽어 `{{date}}` 자리를
   오늘 날짜로 채워 새로 만든다.
6. 사용자가 특정 기록 내용을 함께 전달했으면 `## Notes` 아래에 이어 적는다.
7. 파일 경로를 사용자에게 알려준다.

## 금지 사항

- `private/` 아래 파일을 `git add`, `git commit`, `git push` 하지 않는다.
- `private/` 안의 내용을 `wiki/`, `outputs/`, `areas/daily/` 등 팀 공유 경로로
  옮기거나 인용하지 않는다 — 승격이 필요하면 사용자에게 명시적으로 확인한다.
- `.gitignore`의 `private/` 항목을 제거하거나 예외(`!private/...`)를 추가하지
  않는다.

## 트리거 예시

- "오늘 private 노트 시작해줘."
- "개인 노트 열어줘."
- "private에 오늘 작업 기록해줘: <내용>"
