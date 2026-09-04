"""REPORT.md의 이미지 링크와 핵심 수치를 원본에서 재계산해 검증한다."""
from pathlib import Path
import re, sys
import pandas as pd, numpy as np

ROOT = Path(__file__).resolve().parents[1]
rep = (ROOT/"REPORT.md").read_text()
fails = []

# 1) 이미지 링크 검증
links = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", rep)
print(f"[이미지 링크 {len(links)}개]")
for L in links:
    ok = (ROOT/L).exists()
    print(f"  {'OK ' if ok else 'X  '} {L}")
    if not ok: fails.append(f"이미지 없음: {L}")
imgs = sorted(p.name for p in (ROOT/"images").glob("*.png"))
unused = [i for i in imgs if not any(i in L for L in links)]
if unused: print(f"  (리포트에 안 쓰인 이미지: {unused})")

# 2) 원본 CSV -> 전처리 결과 샘플링 대조
raw = pd.read_csv(ROOT/"data/raw/demand_2025.csv", encoding="cp949")
h = pd.read_csv(ROOT/"data/processed/demand_hourly.csv", parse_dates=["datetime","date"])
print("\n[샘플링 대조: 원본 vs 전처리]")
checks = [("2025-01-01",1),("2025-01-04",1),("2025-06-15",14),("2025-12-31",24)]
for ds, hh in checks:
    o = float(raw.loc[raw.iloc[:,0]==ds, f"{hh}시"].iloc[0])
    p = float(h.loc[(h["date"]==ds)&(h["hour"]==hh), "demand_mwh"].iloc[0])
    ok = abs(o-p) < 1e-6
    print(f"  {'OK ' if ok else 'X  '} {ds} {hh}시  원본 {o:,.0f} / 전처리 {p:,.0f}")
    if not ok: fails.append(f"값 불일치 {ds} {hh}시")

# 3) 리포트 핵심 수치 재계산
d = pd.read_csv(ROOT/"data/processed/daily_merged.csv", parse_dates=["date"])
y = d.groupby("year").agg(total=("total_mwh","sum"), peak=("peak_mwh","max"), mean_h=("mean_mwh","mean"))
claims = []
claims.append(("총수요 지수 2025 = 110.8", round(y["total"].iloc[-1]/y["total"].iloc[0]*100,1), 110.8))
claims.append(("최대수요 지수 2025 = 125.4", round(y["peak"].iloc[-1]/y["peak"].iloc[0]*100,1), 125.4))
hrs = pd.Series({v:(366 if v%4==0 else 365)*24 for v in y.index})
lf = y["total"]/hrs/y["peak"]*100
claims.append(("연간 부하율 2013 = 76.1%", round(lf.iloc[0],1), 76.1))
claims.append(("연간 부하율 2025 = 67.2%", round(lf.iloc[-1],1), 67.2))
claims.append(("2024 최대수요 = 97.1GW", round(y.loc[2024,"peak"]/1000,1), 97.1))
mm = d.groupby(["year","month"])["peak_mwh"].max().unstack()
claims.append(("2024 여름-겨울 격차 = 7.9GW",
               round((mm.loc[2024,[6,7,8]].max()-mm.loc[2024,[12,1,2]].max())/1000,1), 7.9))
claims.append(("2016 여름피크 = 85.2GW", round(mm.loc[2016,[6,7,8]].max()/1000,1), 85.2))
claims.append(("2016 겨울피크 = 83.0GW", round(mm.loc[2016,[12,1,2]].max()/1000,1), 83.0))
claims.append(("전체 상관 = -0.191", round(d["temp_avg"].corr(d["total_mwh"]),3), -0.191))
sm_ = d[d.month.isin([6,7,8])]; wi = d[d.month.isin([12,1,2])]
claims.append(("여름 상관 = +0.546", round(sm_["temp_avg"].corr(sm_["total_mwh"]),3), 0.546))
claims.append(("겨울 상관 = -0.358", round(wi["temp_avg"].corr(wi["total_mwh"]),3), -0.358))
b = d.groupby(pd.cut(d.temp_avg,[-99,0,10,18,24,28,99], right=False), observed=True)["total_mwh"].mean()/1000
claims.append(("28도 이상 일총수요 = 1691 GWh", round(b.iloc[-1]), 1691))
claims.append(("영하 일총수요 = 1649 GWh", round(b.iloc[0]), 1649))
claims.append(("10~18도 일총수요 = 1387 GWh", round(b.iloc[2]), 1387))
claims.append(("역대 최대 = 97115 MWh", int(h["demand_mwh"].max()), 97115))
claims.append(("관측 수 = 113952", len(h), 113952))
claims.append(("일수 = 4748", len(d), 4748))

print("\n[리포트 수치 재계산]")
for label, got, want in claims:
    ok = (abs(got-want) < 0.051) if isinstance(want,float) else (got==want)
    print(f"  {'OK ' if ok else 'X  '} {label:32s} 재계산 {got}")
    if not ok: fails.append(f"{label} -> 재계산 {got}")

print("\n" + ("검증 통과 — 불일치 0건" if not fails else f"불일치 {len(fails)}건:\n  " + "\n  ".join(fails)))
sys.exit(1 if fails else 0)
