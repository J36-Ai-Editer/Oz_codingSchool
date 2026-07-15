# 2일차 Git Branch 전략

## 0. 들어가기 전에

이 문서는 프로젝트를 진행하기 전에 Git과 GitHub를 활용하여 브랜치를 어떻게 관리할지 정리한 학습 자료입니다.  
Git은 단순히 코드를 저장하는 도구가 아니라, 팀원들이 동시에 작업하면서도 안정적으로 개발 흐름을 유지하게 해주는 협업 도구입니다.

브랜치 전략을 정해두면 다음과 같은 장점이 있습니다.

- 여러 사람이 동시에 기능을 개발해도 작업 내용이 섞이지 않습니다.
- 운영 중인 안정적인 코드와 개발 중인 코드를 분리할 수 있습니다.
- Pull Request를 통해 코드 리뷰와 변경 이력을 남길 수 있습니다.
- 배포, 테스트, 긴급 수정 상황을 더 체계적으로 관리할 수 있습니다.

---

## 1. Git Branch 전략이란?

Git Branch 전략은 프로젝트에서 브랜치를 어떤 기준으로 만들고, 어떤 순서로 병합하며, 어떤 브랜치를 배포 기준으로 삼을지 정하는 규칙입니다.

대표적인 전략으로는 다음 두 가지가 많이 사용됩니다.

| 전략 | 특징 | 적합한 상황 |
| --- | --- | --- |
| Git Flow | `main`, `develop`, `feature`, `release`, `hotfix`처럼 역할별 브랜치를 명확히 나눔 | 배포 주기가 정해져 있고 QA 단계가 필요한 프로젝트 |
| GitHub Flow | `main`과 작업 브랜치를 중심으로 PR을 통해 빠르게 병합/배포 | 작고 빠른 변경, 지속적인 배포가 중요한 프로젝트 |

이번 문서에서는 팀 프로젝트에서 안정적인 협업과 배포 연습을 하기 위해 `Git Flow`를 중심으로 정리합니다.

---

## 2. Git Flow 핵심 브랜치

Git Flow는 Vincent Driessen이 제안한 브랜치 전략으로, 개발과 배포 흐름을 브랜치 역할에 따라 나누는 방식입니다.

### 1) main 브랜치

`main` 브랜치는 실제 배포 가능한 안정적인 코드만 존재하는 브랜치입니다.

- 운영 환경에 반영되는 기준 브랜치입니다.
- 직접 커밋하지 않고 PR 또는 merge를 통해서만 변경합니다.
- `main`에 병합된 코드는 언제든 배포 가능한 상태여야 합니다.

### 2) develop 브랜치

`develop` 브랜치는 개발이 완료된 기능들이 모이는 통합 브랜치입니다.

- 기능 개발 브랜치의 기준이 됩니다.
- 여러 `feature` 브랜치가 병합됩니다.
- 배포 전 테스트나 개발 서버 배포 기준으로 사용할 수 있습니다.

### 3) feature 브랜치

`feature` 브랜치는 새로운 기능을 개발하기 위한 브랜치입니다.

- 보통 `develop` 브랜치에서 분기합니다.
- 기능 단위로 브랜치를 생성합니다.
- 작업 완료 후 PR을 생성하여 `develop`으로 병합합니다.

예시:

```bash
feature/login
feature/signup
feature/post-create
feature/#10
```

### 4) release 브랜치

`release` 브랜치는 배포 준비를 위한 브랜치입니다.

- `develop`에서 분기합니다.
- 배포 전 QA, 버그 수정, 문서 정리 등을 진행합니다.
- 테스트가 완료되면 `main`으로 병합하여 배포합니다.
- 배포 후 수정 사항을 `develop`에도 다시 반영해야 합니다.

예시:

```bash
release/v1.0.0
release/2026-07-14
```

### 5) hotfix 브랜치

`hotfix` 브랜치는 운영 중 긴급 수정이 필요할 때 사용하는 브랜치입니다.

- `main`에서 바로 분기합니다.
- 긴급 버그 수정 후 `main`에 병합하여 배포합니다.
- 수정 내용은 반드시 `develop`에도 반영합니다.

예시:

```bash
hotfix/login-error
hotfix/payment-bug
```

---

## 3. Git Flow 전체 흐름

Git Flow의 기본 흐름은 다음과 같습니다.

```text
main
 ├── hotfix/긴급수정
 │    └── main, develop에 병합
 │
 └── develop
      ├── feature/login
      ├── feature/signup
      └── release/v1.0.0
           └── main, develop에 병합
```

실제 작업 순서는 다음과 같습니다.

1. `develop` 브랜치에서 `feature/기능명` 브랜치를 생성합니다.
2. `feature` 브랜치에서 기능을 개발하고 커밋합니다.
3. 원격 저장소에 `feature` 브랜치를 push합니다.
4. GitHub에서 `feature` → `develop` 방향으로 Pull Request를 생성합니다.
5. 팀원 코드 리뷰 후 PR을 병합합니다.
6. 배포 시점이 되면 `develop`에서 `release` 브랜치를 생성합니다.
7. `release` 브랜치에서 QA와 버그 수정을 진행합니다.
8. 배포 준비가 끝나면 `release`를 `main`에 병합합니다.
9. `release`에서 수정된 내용은 `develop`에도 병합합니다.
10. 운영 중 긴급 오류가 발생하면 `main`에서 `hotfix` 브랜치를 생성하여 수정합니다.

---

## 4. 실전 작업 흐름

### 1) 최신 develop 브랜치 가져오기

작업 브랜치를 만들기 전에는 항상 기준 브랜치를 최신 상태로 맞춥니다.

```bash
git switch develop
git pull origin develop
```

또는 `checkout` 명령어를 사용할 수도 있습니다.

```bash
git checkout develop
git pull origin develop
```

### 2) 기능 브랜치 생성하기

```bash
git switch -c feature/login
```

브랜치명은 팀원들이 봤을 때 어떤 작업인지 바로 알 수 있게 작성합니다.

좋은 예시:

```bash
feature/login
feature/user-profile
feature/post-comment
```

피하는 것이 좋은 예시:

```bash
feature/test
feature/aaa
feature/fix
```

### 3) 기능 개발 후 커밋하기

```bash
git status
git add .
git commit -m "✨ feat: 로그인 기능 추가"
```

커밋 메시지는 변경 내용을 짧고 명확하게 작성합니다.

추천 커밋 타입:

| 타입 | 의미 |
| --- | --- |
| feat | 새로운 기능 추가 |
| fix | 버그 수정 |
| docs | 문서 수정 |
| style | 코드 포맷팅, 세미콜론 등 기능 변화 없는 수정 |
| refactor | 기능 변화 없는 코드 개선 |
| test | 테스트 코드 추가/수정 |
| chore | 설정, 빌드, 패키지 등 기타 작업 |
| hotfix | 운영 긴급 수정 |

이슈 번호를 함께 남기면 추후 작업 추적이 쉬워집니다.

```bash
git commit -m "[#10] ✨ feat: 로그인 API 연동"
```

단, 커밋 메시지를 편집할 때 `#10 feat: ...`처럼 맨 앞에 `#`을 쓰면 Git 편집기에서 주석으로 처리될 수 있으므로 `[#10]` 형태를 추천합니다.

### 4) 작업 브랜치 최신화하기

내가 작업하는 동안 다른 팀원의 코드가 `develop`에 병합되었을 수 있습니다. PR을 올리기 전에는 내 브랜치를 최신 `develop` 기준으로 맞춥니다.

```bash
git switch feature/login
git pull --rebase origin develop
```

`rebase`를 사용하면 `develop`의 최신 커밋 위에 내 작업 커밋을 다시 올리는 형태가 됩니다. 그래서 커밋 흐름을 비교적 깔끔하게 유지할 수 있습니다.

최신화 후 로그를 확인합니다.

```bash
git log --oneline --graph
```

### 5) 원격 저장소에 push하기

```bash
git push origin feature/login
```

이미 원격에 push한 브랜치를 rebase한 경우에는 커밋 해시가 바뀌기 때문에 일반 push가 거절될 수 있습니다. 이때는 안전하게 아래 명령어를 사용합니다.

```bash
git push --force-with-lease origin feature/login
```

`--force-with-lease`는 무조건 덮어쓰는 `-f`보다 안전합니다. 원격 브랜치에 내가 모르는 다른 변경사항이 있으면 push를 막아주기 때문입니다.

---

## 5. Pull Request 전략

GitHub 협업에서는 직접 브랜치를 병합하기보다 Pull Request를 통해 리뷰 과정을 거치는 것이 좋습니다.

### 1) PR 생성 기준

기능 개발이 완료되면 다음 방향으로 PR을 생성합니다.

```text
base: develop
compare: feature/login
```

즉, `feature/login` 브랜치의 변경 내용을 `develop` 브랜치에 반영해 달라고 요청하는 것입니다.

### 2) PR에 포함하면 좋은 내용

PR 본문에는 다음 내용을 포함하는 것이 좋습니다.

- 어떤 기능을 구현했는지
- 주요 변경 파일 또는 변경 내용
- 테스트한 내용
- 스크린샷이 필요한 경우 화면 캡처
- 관련 이슈 번호

예시:

```md
## ✅ PR 요약
- 로그인 API 연동 기능을 추가했습니다.

## 📄 상세 내용
- 로그인 폼 입력값 검증 추가
- 로그인 성공 시 토큰 저장
- 로그인 실패 시 에러 메시지 출력

## 🧪 테스트
- [x] 올바른 계정으로 로그인 성공 확인
- [x] 잘못된 비밀번호 입력 시 에러 메시지 확인

## 🔗 관련 이슈
- close #10
```

### 3) 코드 리뷰

리뷰어는 변경된 코드가 다음 기준을 만족하는지 확인합니다.

- 요구사항을 제대로 구현했는가?
- 불필요하게 복잡한 코드는 없는가?
- 버그 가능성이 있는 부분은 없는가?
- 네이밍과 폴더 구조가 일관적인가?
- 테스트 또는 직접 확인이 충분히 되었는가?

리뷰 결과는 보통 다음 세 가지로 나뉩니다.

| 리뷰 상태 | 의미 |
| --- | --- |
| Approve | 병합해도 좋음 |
| Comment | 단순 의견 또는 질문 |
| Request changes | 수정이 필요함 |

리뷰 피드백을 반영했다면 추가 커밋 후 다시 push하면 PR이 자동으로 업데이트됩니다.

---

## 6. Merge 전략

GitHub PR을 병합할 때는 보통 세 가지 방식이 있습니다.

| 방식 | 특징 |
| --- | --- |
| Create a merge commit | merge commit이 남아 브랜치 병합 기록이 보존됨 |
| Squash and merge | 여러 커밋을 하나로 합쳐 병합함 |
| Rebase and merge | 커밋을 재배치하여 직선형 히스토리로 병합함 |

팀 프로젝트에서는 하나의 방식을 정해서 일관되게 사용하는 것이 중요합니다.

초기 학습 프로젝트에서는 다음 기준을 추천합니다.

- 커밋 단위가 지저분하고 작은 수정 커밋이 많다면 `Squash and merge`
- 기능별 커밋 히스토리를 살리고 싶다면 `Rebase and merge`
- 병합 흐름 자체를 기록으로 남기고 싶다면 `Create a merge commit`

중요한 것은 “어떤 전략이 절대적으로 좋다”가 아니라, 팀에서 정한 규칙을 모두가 지키는 것입니다.

---

## 7. GitHub Flow와 비교하기

GitHub Flow는 Git Flow보다 단순한 브랜치 전략입니다.

기본 흐름은 다음과 같습니다.

```text
main → feature 브랜치 생성 → 작업 → PR → 리뷰 → main 병합 → 배포
```

GitHub Flow의 특징:

- `main` 브랜치가 항상 배포 가능한 상태입니다.
- 별도의 `develop`, `release` 브랜치를 두지 않는 경우가 많습니다.
- 작은 단위의 작업을 빠르게 PR로 올리고 병합합니다.
- 지속적 배포(CI/CD)와 잘 어울립니다.

Git Flow와 비교하면 다음과 같습니다.

| 구분 | Git Flow | GitHub Flow |
| --- | --- | --- |
| 브랜치 구조 | 복잡하지만 역할이 명확함 | 단순함 |
| 배포 방식 | 정해진 배포 주기에 적합 | 수시 배포에 적합 |
| QA 단계 | `develop`, `release`에서 단계적으로 가능 | PR, 테스트 자동화 중심 |
| 학습 난이도 | 비교적 높음 | 비교적 낮음 |
| 추천 상황 | 팀 프로젝트, 배포 연습, QA 단계 필요 | 작은 서비스, 빠른 배포, 개인/소규모 프로젝트 |

따라서 이번 프로젝트처럼 협업 과정과 배포 흐름을 학습하는 상황에서는 Git Flow를 적용하고, 이후 프로젝트 규모가 작거나 빠른 배포가 중요해지면 GitHub Flow도 고려할 수 있습니다.

---

## 8. Conflict 해결 방법

Conflict는 서로 다른 브랜치에서 같은 파일의 같은 부분을 수정했을 때 발생합니다.

예를 들어 `develop` 브랜치와 내 `feature/login` 브랜치에서 같은 줄을 다르게 수정했다면 Git은 어떤 코드를 선택해야 할지 판단할 수 없습니다.

충돌이 발생하면 파일 안에 다음과 같은 표시가 생깁니다.

```txt
<<<<<<< HEAD
console.log("develop 브랜치의 코드");
=======
console.log("feature 브랜치의 코드");
>>>>>>> feature/login
```

해결 순서는 다음과 같습니다.

1. 충돌이 발생한 파일을 엽니다.
2. `<<<<<<<`, `=======`, `>>>>>>>` 표시를 확인합니다.
3. 어떤 코드를 남길지 결정합니다.
4. 충돌 표시를 모두 삭제하고 최종 코드만 남깁니다.
5. 수정한 파일을 staging합니다.

```bash
git add 충돌_파일명
```

rebase 중이었다면 다음 명령어로 이어서 진행합니다.

```bash
git rebase --continue
```

충돌 해결이 어렵거나 방향이 애매하면 혼자 판단하지 말고 해당 코드를 작성한 팀원과 소통하는 것이 가장 좋습니다.

만약 rebase를 취소하고 이전 상태로 돌아가고 싶다면 다음 명령어를 사용할 수 있습니다.

```bash
git rebase --abort
```

---

## 9. 팀 프로젝트 브랜치 규칙 예시

이번 프로젝트에서는 다음 규칙을 사용할 수 있습니다.

### 브랜치명

```text
main
develop
feature/기능명
release/버전명
hotfix/수정내용
```

예시:

```bash
feature/login
feature/post-list
feature/comment-create
release/v1.0.0
hotfix/login-token-error
```

### 작업 시작 전

```bash
git switch develop
git pull origin develop
git switch -c feature/기능명
```

### 작업 중

```bash
git status
git add .
git commit -m "✨ feat: 기능 설명"
```

### PR 생성 전

```bash
git pull --rebase origin develop
git push origin feature/기능명
```

### PR 병합 후

- GitHub에서 원격 feature 브랜치를 삭제합니다.
- 로컬에서도 사용이 끝난 브랜치를 삭제합니다.

```bash
git switch develop
git pull origin develop
git branch -d feature/기능명
```

---

## 10. 주의사항

- `main` 브랜치에는 직접 push하지 않습니다.
- 공용 브랜치인 `main`, `develop`, `release`에서는 force push를 하지 않습니다.
- 작업 브랜치는 기능 단위로 작게 만듭니다.
- PR은 너무 커지기 전에 올리는 것이 좋습니다.
- 브랜치 최신화는 자주 할수록 충돌 가능성이 줄어듭니다.
- 충돌이 발생하면 관련 팀원과 먼저 소통합니다.
- 병합이 끝난 feature 브랜치는 삭제하여 브랜치 목록을 정리합니다.
- 배포 후에는 `main`의 변경사항이 `develop`에도 반영되었는지 확인합니다.

---

## 11. 정리

Git Branch 전략은 팀 프로젝트의 교통 규칙과 같습니다.  
규칙이 없으면 각자 원하는 방향으로 움직이다가 충돌이 자주 발생하지만, 브랜치 역할과 병합 흐름을 정해두면 협업이 훨씬 안정적이 됩니다.

이번 프로젝트에서는 다음 흐름을 기억하면 됩니다.

```text
develop에서 feature 생성
→ 기능 개발
→ PR 생성
→ 코드 리뷰
→ develop 병합
→ release에서 배포 준비
→ main 배포
→ 필요 시 hotfix 처리
```

처음에는 브랜치가 많아 복잡해 보일 수 있지만, 실제로는 “안정적인 코드와 작업 중인 코드를 분리한다”는 하나의 원칙에서 출발합니다.  
브랜치 전략을 잘 지키면 코드뿐만 아니라 팀의 협업 방식도 함께 정리됩니다.

---

## 참고 자료

- [주니어 개발자의 현업에서 배운 Git Flow](https://velog.io/@myoungji-kim/git-flow)
- [사례로 이해하는 GitHub Flow](https://www.heropy.dev/p/6hdJi6)
- 첨부 학습 자료: Git Flow, PR, Review, Conflict 해결 가이드
