# 총량이 아니라 피크가 문제다 — 전국 전력수요 13년 시계열 분석

한국전력거래소의 시간별 전국 전력수요 **113,952개 관측(2013~2025, 4,748일)** 과
기상청 서울 관측소 일자료를 결합해, 전력 수요의 총량·계절·시각 구조가 13년 동안
어떻게 바뀌었는지 분석했다.

**→ [분석 리포트 전문 (REPORT.md)](REPORT.md)**
**→ [인터랙티브 대시보드 (GitHub Pages, 로그인 불필요)](https://parkhuk20-dot.github.io/codyssey-m1-1/dashboard.html)**
**→ [인터랙티브 대시보드 (Claude Artifact)](https://claude.ai/code/artifact/0df2fa95-d2fd-44ae-b31b-f06aba2ae0a8)**

## 핵심 결과 세 줄

1. 2013→2025년 총수요는 +10.8% 늘었지만 최대수요는 +25.4% 늘었다. 연간 부하율은 76.1% → 67.2%로 떨어졌다.
2. 2016년을 기점으로 연중 최대 부하가 겨울에서 여름으로 넘어갔다. 2024년 격차는 7.9GW다.
3. 여름철 피크 시각이 15시(2013)에서 19시(2025)로 4시간 밀렸다. 저녁−낮 격차는 13년 연속 한 방향으로 커졌다.

## 폴더 구조

```
M1-1/
├── REPORT.md                     분석 리포트 (본 과제의 주 결과물)
├── QUESTIONS.md                  분석 질문 4개의 정의와 선정 이유
├── dashboard.html                인터랙티브 대시보드 (단독 실행 가능)
├── dashboard_data.json           대시보드용 압축 데이터
├── data/
│   ├── DATA_SOURCE.md            출처·수집방법·라이선스·결측 처리 규정
│   ├── raw/                      원본 CSV (전력수요 6 + 기상 1)
│   └── processed/                정제 결과 3종
├── images/                       시각화 9종 + 대시보드 캡처 2종
├── src/
│   ├── viz_style.py              공통 차트 스타일·팔레트
│   ├── 01_preprocess.py          전력수요 병합·정제
│   ├── 02_merge_weather.py       기상 결합
│   ├── 03_visualize.py           시각화 01~07
│   ├── 04_decompose_forecast.py  MSTL 분해 + 베이스라인 예측 (08~09)
│   ├── 05_dashboard_data.py      대시보드 데이터 생성
│   ├── 99_verify.py              리포트 수치·이미지 링크 검증
│   └── collect_asos.js           기상 API 수집 스크립트
├── requirements.txt
├── .env.example                  API 키 형식 (실제 키는 .env, gitignore 대상)
└── .gitignore
```

## 실행 방법

```bash
pip install -r requirements.txt

python src/01_preprocess.py          # 원본 6개 → demand_hourly / demand_daily
python src/02_merge_weather.py       # 기상 결합 → daily_merged
python src/03_visualize.py           # images/01~07
python src/04_decompose_forecast.py  # images/08~09
python src/05_dashboard_data.py      # dashboard_data.json
python src/99_verify.py              # 리포트 수치 재계산 검증 (불일치 시 exit 1)
```

앞 단계의 출력을 뒤 단계가 입력으로 쓰므로 순서대로 실행해야 한다.

대시보드는 `dashboard.html`을 브라우저로 열면 바로 동작한다. 데이터가 파일 안에
들어 있어 서버가 필요 없다.

### 한글 폰트

차트 한글 렌더링에 `Noto Sans CJK` 계열 폰트가 필요하다. 다른 환경에서는
`src/viz_style.py`의 `font.family`를 시스템 한글 폰트(`AppleGothic`,
`Malgun Gothic`, `NanumGothic` 등)로 바꾼다.

### 기상 데이터를 새로 수집하려면

[공공데이터포털 ASOS 일자료 서비스](https://www.data.go.kr/data/15059093/openapi.do)에서
활용신청(자동승인) 후 인증키를 발급받아 `.env`에 넣는다.

```
KMA_API_KEY=발급받은_Decoding_키
```

승인 직후에는 키가 API 서버에 전파되기까지 1시간가량 걸린다. 그 사이 호출하면
`SERVICE_KEY_IS_NOT_REGISTERED_ERROR`가 발생하는데, 신청 실패가 아니라 대기 상태다.

## 실행 환경

Python 3.10.12 / pandas 2.3.3 / numpy / matplotlib 3.10.9 / statsmodels 0.15.0

## 데이터 출처 및 라이선스

| 데이터 | 제공기관 | 라이선스 |
|---|---|---|
| [시간별 전국 전력수요량](https://www.data.go.kr/data/15065266/fileData.do) | 한국전력거래소 | 이용허락범위 제한 없음 |
| [지상(종관, ASOS) 일자료](https://www.data.go.kr/data/15059093/openapi.do) | 기상청 | 이용허락범위 제한 없음 |

두 데이터 모두 공공데이터포털 제공분이며 무료다. 수집 방법과 전처리 규정은
[`data/DATA_SOURCE.md`](data/DATA_SOURCE.md)에 정리했다.

## AI 사용 투명성

본 분석은 Claude를 활용해 수행했다. 사용한 작업, 사용 이유, 검증 방법은
[REPORT.md 8장](REPORT.md#8-ai-사용-로그)에 기록했다.
