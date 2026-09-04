"""보너스 A — 시계열 분해(MSTL)와 베이스라인 예측."""
import sys; sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from pathlib import Path
import pandas as pd, numpy as np
import matplotlib.pyplot as plt
from statsmodels.tsa.seasonal import MSTL
from viz_style import *

ROOT = Path(__file__).resolve().parents[1]; IMG = ROOT/"images"
d = pd.read_csv(ROOT/"data/processed/daily_merged.csv", parse_dates=["date"]).sort_values("date")
s = pd.Series(d["total_mwh"].values/1000, index=pd.DatetimeIndex(d["date"]), name="GWh")
s.index.freq = "D"

# ── 분해: 주간(7일)과 연간(365일) 계절성을 동시에 분리 ────────────────────
print("MSTL 분해 중 (periods=7, 365)...")
res = MSTL(s, periods=(7, 365)).fit()
trend, w7, y365, resid = res.trend, res.seasonal["seasonal_7"], res.seasonal["seasonal_365"], res.resid

var = {"추세":trend.var(), "연간 계절성":y365.var(), "주간 계절성":w7.var(), "잔차":resid.var()}
tot = sum(var.values())
print("\n[성분별 분산 기여도]")
for k,v in var.items(): print(f"  {k:10s} {v/tot*100:5.1f}%")
print(f"\n  추세 2013년 초 {trend.iloc[:30].mean():,.0f} GWh -> 2025년 말 {trend.iloc[-30:].mean():,.0f} GWh")
print(f"  연간 계절성 진폭 {y365.max()-y365.min():,.0f} GWh (최대 {y365.idxmax().strftime('%m-%d')}, 최소 {y365.idxmin().strftime('%m-%d')})")
print(f"  주간 계절성 진폭 {w7.max()-w7.min():,.0f} GWh")
print(f"  잔차 표준편차 {resid.std():,.0f} GWh, 최대 이상 {resid.abs().max():,.0f} GWh ({resid.abs().idxmax().date()})")

fig, axes = plt.subplots(5,1, figsize=(10,10.5), sharex=True)
for ax, (ser, lab) in zip(axes, [(s,"원계열"),(trend,"추세"),(y365,"연간 계절성"),
                                 (w7,"주간 계절성"),(resid,"잔차")]):
    ax.plot(ser.index, ser.values, color=S1_BLUE, linewidth=0.7)
    ax.set_ylabel(lab, color=INK_2, fontsize=10)
    frame(ax)
axes[4].axhline(0, color=AXIS, linewidth=0.8)
titles(axes[0], "13년치 수요를 추세·연간·주간·잔차로 분해했다",
       "MSTL 분해 · 일 총수요(GWh) · periods = 7일, 365일")
save(fig, IMG/"08_stl_decomposition.png")

# ── 예측: 마지막 28일 홀드아웃, 베이스라인 3종 ────────────────────────────
H = 28
train, test = d.iloc[:-H].copy(), d.iloc[-H:].copy()
act = test["total_mwh"].values/1000

# (1) 계절 나이브: 364일 전(=52주 전) 같은 요일
sn = d.set_index("date")["total_mwh"]/1000
p1 = np.array([sn.get(t - pd.Timedelta(days=364), np.nan) for t in test["date"]])
# (2) 계절 나이브 + 추세 보정 (최근 28일 평균 / 1년 전 28일 평균)
r = (train["total_mwh"].iloc[-28:].mean() / train["total_mwh"].iloc[-392:-364].mean())
p2 = p1 * r
# (3) 기온 회귀: 냉방도일·난방도일 + 요일 (최근 3년 학습)
tr3 = train[train["date"] >= train["date"].max() - pd.Timedelta(days=1095)]
X = np.column_stack([np.ones(len(tr3)), tr3["CDD"], tr3["HDD"],
                     pd.get_dummies(tr3["dow"], drop_first=True).astype(float).values])
beta, *_ = np.linalg.lstsq(X, tr3["total_mwh"].values/1000, rcond=None)
Xt = np.column_stack([np.ones(len(test)), test["CDD"], test["HDD"],
                      pd.get_dummies(test["dow"], drop_first=True)
                        .reindex(columns=range(1,7), fill_value=0).astype(float).values])
p3 = Xt @ beta

def mape(p): 
    m = ~np.isnan(p); return np.mean(np.abs(act[m]-p[m])/act[m])*100
print(f"\n[홀드아웃 {H}일 예측 정확도 — {test['date'].min().date()} ~ {test['date'].max().date()}]")
names = ["① 계절 나이브(364일 전)", "② 계절 나이브 + 추세보정", "③ 기온회귀(CDD·HDD+요일)"]
for n,p in zip(names,[p1,p2,p3]): print(f"  {n:26s} MAPE {mape(p):5.2f}%")

fig, ax = plt.subplots(figsize=(9.6,5.2))
hist = d.iloc[-(H+42):]
ax.plot(hist["date"], hist["total_mwh"]/1000, color=MUTED, linewidth=1.6, label="실제")
ax.plot(test["date"], p1, color=S2_ORANGE, linewidth=2, label=f"① 계절 나이브 ({mape(p1):.1f}%)")
ax.plot(test["date"], p3, color=S1_BLUE, linewidth=2, label=f"③ 기온회귀 ({mape(p3):.1f}%)")
ax.axvline(test["date"].iloc[0], color=AXIS, linewidth=0.8)
ax.text(test["date"].iloc[0], ax.get_ylim()[1], " 예측 구간", color=INK_2, fontsize=9.5, va="top")
ax.set_ylabel("일 총수요 (GWh)")
frame(ax); titles(ax, f"기온을 넣으면 오차가 {mape(p1):.1f}%에서 {mape(p3):.1f}%로 줄어든다",
                 f"마지막 {H}일 홀드아웃 예측 · 정확도보다 '무엇을 가정했는가'가 핵심")
ax.legend(labelcolor=INK_2, loc="lower left")
save(fig, IMG/"09_forecast_baseline.png")
