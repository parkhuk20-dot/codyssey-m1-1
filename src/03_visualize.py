"""리포트용 시각화 생성. images/ 에 PNG 저장."""
import sys; sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from pathlib import Path
import pandas as pd, numpy as np
import matplotlib.pyplot as plt
from viz_style import *

ROOT = Path(__file__).resolve().parents[1]
IMG = ROOT/"images"; IMG.mkdir(exist_ok=True)
d = pd.read_csv(ROOT/"data/processed/daily_merged.csv", parse_dates=["date"])
h = pd.read_csv(ROOT/"data/processed/demand_hourly.csv", parse_dates=["datetime","date"])
h["year"]=h["date"].dt.year; h["month"]=h["date"].dt.month

# 01. Q1 총수요 vs 최대수요 지수
y = d.groupby("year").agg(total=("total_mwh","sum"), peak=("peak_mwh","max"))
idx_t = y["total"]/y["total"].iloc[0]*100
idx_p = y["peak"]/y["peak"].iloc[0]*100
fig, ax = plt.subplots(figsize=(9,5))
ax.plot(idx_t.index, idx_t, color=S1_BLUE, linewidth=2, marker="o", markersize=4.5,
        markeredgecolor=SURFACE, markeredgewidth=2, label="총수요")
ax.plot(idx_p.index, idx_p, color=S2_ORANGE, linewidth=2, marker="o", markersize=4.5,
        markeredgecolor=SURFACE, markeredgewidth=2, label="최대수요")
ax.axhline(100, color=AXIS, linewidth=0.8)
ax.annotate(f"최대수요 {idx_p.iloc[-1]:.0f}", (2025, idx_p.iloc[-1]), xytext=(6,2),
            textcoords="offset points", color=S2_ORANGE, fontsize=10.5, fontweight="600")
ax.annotate(f"총수요 {idx_t.iloc[-1]:.0f}", (2025, idx_t.iloc[-1]), xytext=(6,-4),
            textcoords="offset points", color=S1_BLUE, fontsize=10.5, fontweight="600")
ax.set_xlim(2012.6, 2026.9); ax.set_xticks(range(2013,2026,2)); ax.set_ylabel("2013 = 100")
frame(ax); titles(ax, "총수요는 11% 늘었고, 최대수요는 25% 늘었다",
                  "전국 전력수요 지수 · 2013년을 100으로 환산 · 출처 한국전력거래소")
ax.legend(loc="upper left", labelcolor=INK_2)
save(fig, IMG/"01_index_total_vs_peak.png")

# 02. Q1 연간 부하율
hrs = pd.Series({v: (366 if v%4==0 else 365)*24 for v in y.index})
lf = y["total"]/hrs/y["peak"]*100
fig, ax = plt.subplots(figsize=(9,4.6))
ax.plot(lf.index, lf, color=S1_BLUE, linewidth=2, marker="o", markersize=4.5,
        markeredgecolor=SURFACE, markeredgewidth=2)
ax.annotate(f"{lf.iloc[0]:.1f}%", (2013, lf.iloc[0]), xytext=(4,7), textcoords="offset points",
            color=INK, fontsize=11, fontweight="600")
ax.annotate(f"{lf.iloc[-1]:.1f}%", (2025, lf.iloc[-1]), xytext=(4,-2), textcoords="offset points",
            color=INK, fontsize=11, fontweight="600")
ax.set_xlim(2012.6, 2026.2); ax.set_xticks(range(2013,2026,2)); ax.set_ylabel("연간 부하율 (%)")
frame(ax); titles(ax, "설비를 얼마나 알차게 쓰는지는 12년째 나빠지고 있다",
                  "연간 부하율 = 연평균 수요 ÷ 연최대 수요 · 높을수록 설비 활용도가 높다")
save(fig, IMG/"02_load_factor.png")

# 03. Q2 여름-겨울 피크 격차 (발산형)
mm = d.groupby(["year","month"])["peak_mwh"].max().unstack()
gap = (mm[[6,7,8]].max(axis=1) - mm[[12,1,2]].max(axis=1))/1000
fig, ax = plt.subplots(figsize=(9,5))
cols = [DIV_WARM if v>0 else DIV_COOL for v in gap]
ax.bar(gap.index, gap.values, color=cols, width=0.68, zorder=3)
ax.axhline(0, color=AXIS, linewidth=1.0, zorder=4)
ax.set_ylabel("여름 피크 − 겨울 피크 (GW)"); ax.set_xlim(2012.4, 2025.6); ax.set_xticks(range(2013,2026,2))
ax.text(2013.0,  6.9, "여름이 더 높음", color=DIV_WARM, fontsize=10.5, fontweight="600")
ax.text(2019.4, -4.2, "겨울이 더 높음", color=DIV_COOL, fontsize=10.5, fontweight="600")
ax.annotate("2016년 첫 역전", (2016, gap[2016]), xytext=(-16,28), textcoords="offset points",
            color=INK_2, fontsize=9.5,
            arrowprops=dict(arrowstyle="-", color=AXIS, linewidth=0.8))
frame(ax); titles(ax, "2016년, 여름이 처음으로 겨울을 넘어섰다",
                  "연도별 계절 최대수요 격차 · 양수면 그해 최대 부하는 여름에 발생")
save(fig, IMG/"03_summer_vs_winter_gap.png")

# 04. Q3 여름 시간대별 프로파일의 연도별 이동 (순서형 램프)
s = h[h["month"].isin([6,7,8])]
prof = s.pivot_table(index="hour", columns="year", values="demand_mwh", aggfunc="mean")/1000
yrs = sorted(prof.columns)
fig, ax = plt.subplots(figsize=(9.4,5.4))
for i, yr in enumerate(yrs):
    c = ORD_CMAP(i/(len(yrs)-1))
    ax.plot(prof.index, prof[yr], color=c, linewidth=2 if yr in (2013,2025) else 1.4, zorder=3)
for yr, dy in ((2013,-15),(2025,10)):
    pk = prof[yr].idxmax()
    ax.plot([pk],[prof[yr].max()], "o", markersize=7.5,
            color=ORD_CMAP(0.0 if yr==2013 else 1.0),
            markeredgecolor=SURFACE, markeredgewidth=2, zorder=5)
    ax.annotate(f"{yr}년 피크 {pk}시", (pk, prof[yr].max()), xytext=(9,dy),
                textcoords="offset points", color=INK, fontsize=10.5, fontweight="600")
sm = plt.cm.ScalarMappable(cmap=ORD_CMAP, norm=plt.Normalize(2013,2025))
cb = fig.colorbar(sm, ax=ax, pad=0.02, fraction=0.035)
cb.outline.set_visible(False); cb.set_ticks([2013,2017,2021,2025])
cb.ax.tick_params(color=MUTED, labelcolor=INK_2, size=0)
ax.set_xticks(range(2,25,2)); ax.set_xlabel("시각 (시)"); ax.set_ylabel("평균 수요 (GW)")
frame(ax); titles(ax, "여름 피크 시각이 12년 동안 15시에서 19시로 밀렸다",
                  "6~8월 시간대별 평균 전력수요 · 색이 진할수록 최근 연도")
save(fig, IMG/"04_summer_hourly_profile.png")

# 05. Q3 저녁-낮 격차 추이
noon = prof.loc[12:14].mean(); eve = prof.loc[18:20].mean(); dif = eve-noon
fig, ax = plt.subplots(figsize=(9,4.6))
ax.bar(dif.index, dif.values, color=[DIV_WARM if v>0 else DIV_COOL for v in dif],
       width=0.68, zorder=3)
ax.axhline(0, color=AXIS, linewidth=1.0, zorder=4)
ax.annotate(f"{dif.iloc[-1]:+.1f} GW", (2025, dif.iloc[-1]), xytext=(-16,7),
            textcoords="offset points", color=INK, fontsize=11, fontweight="600")
ax.set_ylabel("저녁(18~20시) − 낮(12~14시), GW"); ax.set_xlim(2012.4, 2025.6); ax.set_xticks(range(2013,2026,2))
frame(ax); titles(ax, "여름 저녁이 낮보다 더 부담스러워진 것은 2018년부터다",
                  "6~8월 평균 수요의 저녁·낮 격차 · 13년 내리 한 방향으로 커졌다")
save(fig, IMG/"05_evening_minus_noon.png")

# 06. Q4 기온-수요 산점 (3계열)
d["grp"] = np.where(d.month.isin([6,7,8]),"여름",
            np.where(d.month.isin([12,1,2]),"겨울","봄·가을"))
fig, ax = plt.subplots(figsize=(9,5.4))
for g,c in (("봄·가을",S3_AQUA),("겨울",S1_BLUE),("여름",S2_ORANGE)):
    sub = d[d.grp==g]
    ax.scatter(sub.temp_avg, sub.total_mwh/1000, s=7, color=c, alpha=.45,
               linewidths=0, label=g, zorder=3)
b = d.groupby(pd.cut(d.temp_avg, np.arange(-15,36,2.5)), observed=True)["total_mwh"].mean()/1000
ctr = [iv.mid for iv in b.index]
ax.plot(ctr, b.values, color=INK, linewidth=2, zorder=5)
lo = b.idxmin()
ax.annotate(f"수요 최저 {lo.left:.0f}~{lo.right:.0f}℃", (lo.mid, b.min()),
            xytext=(-96,-96), textcoords="offset points", color=INK,
            fontsize=10.5, fontweight="600",
            bbox=dict(boxstyle="round,pad=0.35", facecolor=SURFACE, edgecolor="none"),
            arrowprops=dict(arrowstyle="-", color=INK_2, linewidth=1.0,
                            shrinkA=2, shrinkB=4))
ax.set_xlabel("서울 일평균기온 (℃)"); ax.set_ylabel("전국 일 총수요 (GWh)")
frame(ax); titles(ax, "기온과 수요는 직선이 아니라 U자로 만난다",
                  "일별 4,748개 관측 · 검은 선은 2.5℃ 구간 평균 · 기상청 서울(108) 기준")
from matplotlib.lines import Line2D
handles = [Line2D([],[], marker="o", linestyle="none", markersize=7, color=c, label=g)
           for g,c in (("봄·가을",S3_AQUA),("겨울",S1_BLUE),("여름",S2_ORANGE))]
ax.legend(handles=handles, loc="upper center", ncol=3, labelcolor=INK_2,
          handletextpad=.4, columnspacing=1.8)
save(fig, IMG/"06_temp_vs_demand.png")

# 07. 월x시간 히트맵 (순차형)
pv = h.pivot_table(index="hour", columns="month", values="demand_mwh", aggfunc="mean")/1000
fig, ax = plt.subplots(figsize=(8.6,5.6))
im = ax.imshow(pv.values, aspect="auto", cmap=SEQ_CMAP, origin="lower",
               extent=[0.5,12.5,0.5,24.5])
cb = fig.colorbar(im, ax=ax, pad=0.03, fraction=0.045)
cb.outline.set_visible(False); cb.ax.tick_params(color=MUTED, labelcolor=INK_2, size=0)
cb.ax.set_title("GW", color=INK_2, fontsize=9.5, pad=8)
ax.set_xticks(range(1,13)); ax.set_yticks(range(2,25,2))
ax.set_xlabel("월"); ax.set_ylabel("시각 (시)")
for sp in ("top","right","left","bottom"): ax.spines[sp].set_visible(False)
titles(ax, "여름 오후와 겨울 오전, 두 개의 봉우리",
       "월×시간대 평균 전력수요 · 2013~2025년 전체 평균")
save(fig, IMG/"07_hour_month_heatmap.png")

print("\n완료")
