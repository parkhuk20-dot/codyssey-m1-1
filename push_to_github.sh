#!/usr/bin/env bash
# M1-1 과제를 GitHub에 올린다.
# 실행: 터미널에서  cd ~/Desktop/codyssey/M1-1 && bash push_to_github.sh
set -euo pipefail

OWNER="parkhuk20-dot"
REPO="codyssey-m1-1"
VIS="public"

cd "$(dirname "$0")"
echo "==> 작업 폴더: $(pwd)"

# 0) 이전에 만들다 만 .git 정리 (샌드박스 제약으로 잠금 파일이 남아 있음)
if [ -d .git ] && ! git rev-parse HEAD >/dev/null 2>&1; then
  echo "==> 미완성 .git 정리"
  rm -rf .git
fi

# 1) 저장소 초기화
if [ ! -d .git ]; then
  git init -q -b main
  echo "==> git init 완료 (main)"
fi

# 2) 스테이징
git add -A

# 3) 안전장치 — 인증키가 들어간 .env가 절대 올라가지 않게 확인
if git ls-files --cached | grep -qE '(^|/)\.env$'; then
  echo "!! 중단: .env가 스테이징되었습니다. .gitignore를 확인하세요." >&2
  exit 1
fi
echo "==> .env 미포함 확인 · 파일 $(git ls-files | wc -l | tr -d ' ')개"

# 4) 커밋
if git rev-parse HEAD >/dev/null 2>&1; then
  git commit -q -m "분석 결과물 업데이트" || echo "==> 변경 없음, 커밋 생략"
else
  git commit -q -F - <<'MSG'
전력수요 13년 시계열 분석 — 리포트·시각화·대시보드

한국전력거래소 시간별 전국 전력수요(2013~2025, 113,952관측)와
기상청 서울 ASOS 일자료를 결합해 분석했다.

- REPORT.md: 분석 질문 4개, 시각화 11종, 인사이트 4개, 결론·한계, AI 사용 로그
- src/: 전처리·결합·시각화·MSTL 분해·베이스라인 예측·검증 스크립트
- dashboard.html: 기간·집계단위·지표·계절 필터가 있는 단독 실행 대시보드
- data/DATA_SOURCE.md: 출처·수집방법·라이선스·결측 처리 규정

핵심 결과
- 총수요 +10.8% 대비 최대수요 +25.4%, 연간 부하율 76.1% -> 67.2%
- 2016년 여름 피크가 겨울을 첫 추월, 2024년 격차 7.9GW
- 여름 피크 시각 15시(2013) -> 19시(2025)

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01BSCWwYU4eQ6AHLLsaEjRT5
MSG
  echo "==> 커밋 완료"
fi

# 5) 원격 저장소 생성 및 push
if git remote get-url origin >/dev/null 2>&1; then
  echo "==> origin 이미 설정됨: $(git remote get-url origin)"
  git push -u origin main
elif command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
  echo "==> gh CLI로 저장소 생성 후 push"
  gh repo create "$OWNER/$REPO" --"$VIS" --source=. --remote=origin --push
else
  cat <<EOS

────────────────────────────────────────────────────────
커밋까지 끝났습니다. 원격 저장소만 만들면 됩니다.

방법 A — gh CLI 설치가 되어 있다면:
    brew install gh && gh auth login
    그 다음 이 스크립트를 다시 실행하세요.

방법 B — 웹에서 직접 만들기:
    1) https://github.com/new 접속
    2) Repository name 에  $REPO  입력
    3) $VIS 선택, README/gitignore/license 는 모두 체크 해제
    4) Create repository 클릭
    5) 아래 두 줄을 터미널에 붙여넣기

    git remote add origin https://github.com/$OWNER/$REPO.git
    git push -u origin main

    (사용자명은 $OWNER, 비밀번호 자리에는 GitHub Personal Access Token
     을 넣어야 합니다. 토큰은 Settings > Developer settings >
     Personal access tokens 에서 발급합니다.)
────────────────────────────────────────────────────────
EOS
  exit 0
fi

echo ""
echo "완료 → https://github.com/$OWNER/$REPO"
