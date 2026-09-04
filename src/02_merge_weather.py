"""
기상청 ASOS 서울(108) 일자료를 전력수요 일별 집계와 결합한다.

수집: 공공데이터포털 기상청_지상(종관,ASOS) 일자료 조회서비스 OpenAPI
      (브라우저에서 연도별 호출 -> CSV 저장, src/collect_asos.js 참고)
결측 처리 규정:
  - sumRn(일강수량) 공란은 '강수 없음'을 뜻하므로 0.0으로 채운다. (결측 아님)
  - 그 외 기상요소의 공란은 관측 결측으로 보고 NaN 유지 후 개수를 기록한다.
출력: data/processed/daily_merged.csv
"""
from pathlib import Path
import pandas as pd, numpy as np

ROOT = Path(__file__).resolve().parents[1]
w = pd.read_csv(ROOT/"data/raw/asos_seoul_2013_2025.csv")
w = w.rename(columns={"tm":"date","avgTa":"temp_avg","minTa":"temp_min","maxTa":"temp_max",
                      "sumRn":"rain_mm","avgRhm":"humid","avgWs":"wind","sumGsr":"solar_mj",
                      "sumSsHr":"sunshine_hr"})
w["date"] = pd.to_datetime(w["date"])
num = ["temp_avg","temp_min","temp_max","rain_mm","humid","wind","solar_mj","sunshine_hr"]
for c in num:
    w[c] = pd.to_numeric(w[c], errors="coerce")

print("[기상 결측 현황] (전체 %d일)" % len(w))
for c in num:
    print(f"  {c:12s} 결측 {w[c].isna().sum():4d}")
w["rain_mm"] = w["rain_mm"].fillna(0.0)   # 공란 = 강수 없음
print("  -> rain_mm 공란은 '강수 없음'으로 보아 0.0으로 대체")

d = pd.read_csv(ROOT/"data/processed/demand_daily.csv", parse_dates=["date"])
m = d.merge(w, on="date", how="inner", validate="one_to_one")
print(f"\n결합 결과: {len(m)}행  ({m['date'].min().date()} ~ {m['date'].max().date()})")
print(f"  전력수요 {len(d)}행 / 기상 {len(w)}행 -> 결합 {len(m)}행 (누락 {len(d)-len(m)}일)")

# 냉방도일 / 난방도일 (기준 18도)
m["CDD"] = (m["temp_avg"] - 18).clip(lower=0)
m["HDD"] = (18 - m["temp_avg"]).clip(lower=0)
m.to_csv(ROOT/"data/processed/daily_merged.csv", index=False)
print("저장: data/processed/daily_merged.csv")

print("\n[기온-수요 관계 확인]")
for lo, hi, lab in [(-99,0,"영하"),(0,10,"0~10도"),(10,18,"10~18도"),(18,24,"18~24도"),
                    (24,28,"24~28도"),(28,99,"28도 이상")]:
    s = m[(m["temp_avg"]>=lo)&(m["temp_avg"]<hi)]
    if len(s): print(f"  {lab:10s} n={len(s):5d}  일총수요 {s['total_mwh'].mean()/1000:7,.0f} GWh  일최대 {s['peak_mwh'].mean()/1000:6.1f} GW")
print(f"\n  상관계수 전체        : {m['temp_avg'].corr(m['total_mwh']):+.3f}")
print(f"  상관계수 여름(6~8월) : {m[m.month.isin([6,7,8])]['temp_avg'].corr(m[m.month.isin([6,7,8])]['total_mwh']):+.3f}")
print(f"  상관계수 겨울(12,1,2): {m[m.month.isin([12,1,2])]['temp_avg'].corr(m[m.month.isin([12,1,2])]['total_mwh']):+.3f}")
print(f"  CDD와 여름수요       : {m[m.month.isin([6,7,8])]['CDD'].corr(m[m.month.isin([6,7,8])]['total_mwh']):+.3f}")
print(f"  HDD와 겨울수요       : {m[m.month.isin([12,1,2])]['HDD'].corr(m[m.month.isin([12,1,2])]['total_mwh']):+.3f}")
