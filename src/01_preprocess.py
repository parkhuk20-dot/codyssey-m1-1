"""
전국 시간별 전력수요 원본 CSV(공공데이터포털, 한국전력거래소) 6개를
하나의 시간별 시계열로 병합·정제한다.

원본 구조: 날짜, 1시, 2시, ... 24시  (단위 MWh, 인코딩 EUC-KR/CP949)
시각 규정: 'h시' = 시간대의 끝(hour-ending). 따라서 datetime = 날짜 + h시간.
          예) 1시 -> 그날 01:00, 24시 -> 다음날 00:00
출력: data/processed/demand_hourly.csv, data/processed/demand_daily.csv
"""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed"
OUT.mkdir(parents=True, exist_ok=True)

frames = []
for path in sorted(RAW.glob("demand_*.csv")):
    df = pd.read_csv(path, encoding="cp949")
    df = df.rename(columns={df.columns[0]: "date"})
    df = df[df["date"].notna() & (df["date"].astype(str).str.strip() != "")]
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df[df["date"].notna()]
    frames.append(df)
    print(f"{path.name:24s} rows={len(df):5d}  {df['date'].min().date()} ~ {df['date'].max().date()}")

wide = pd.concat(frames, ignore_index=True)

# ---- wide -> long -------------------------------------------------------
hour_cols = [c for c in wide.columns if str(c).endswith("시")]
long = wide.melt(id_vars="date", value_vars=hour_cols,
                 var_name="hour_label", value_name="demand_mwh")
long["hour"] = long["hour_label"].str.replace("시", "", regex=False).astype(int)
long["demand_mwh"] = pd.to_numeric(long["demand_mwh"], errors="coerce")
long["datetime"] = long["date"] + pd.to_timedelta(long["hour"], unit="h")
long = long[["datetime", "date", "hour", "demand_mwh"]].sort_values("datetime")

# ---- 품질 점검 ----------------------------------------------------------
print("\n[품질 점검]")
print("  전체 관측 수      :", len(long))
dup = long.duplicated(subset="datetime").sum()
print("  중복 시각          :", dup)
long = long.drop_duplicates(subset="datetime", keep="first")

n_missing = long["demand_mwh"].isna().sum()
n_zero = (long["demand_mwh"] == 0).sum()
print("  결측(NaN)          :", n_missing)
print("  0값                :", n_zero)

full_idx = pd.date_range(long["datetime"].min(), long["datetime"].max(), freq="h")
gaps = full_idx.difference(long["datetime"])
print("  시간축 누락 구간   :", len(gaps))
if len(gaps):
    print("   예시:", list(gaps[:5]))

# 이상치 판정: 로버스트 z-score (중앙값·MAD 기준) |z| > 5
med = long["demand_mwh"].median()
mad = (long["demand_mwh"] - med).abs().median()
long["robust_z"] = 0.6745 * (long["demand_mwh"] - med) / mad
n_out = (long["robust_z"].abs() > 5).sum()
print(f"  로버스트 z>5 이상치: {n_out}  (중앙값 {med:,.0f} / MAD {mad:,.0f})")
print(f"  최소 {long['demand_mwh'].min():,.0f} / 최대 {long['demand_mwh'].max():,.0f} MWh")

# ---- 일별 집계 ----------------------------------------------------------
daily = (long.groupby("date")
             .agg(total_mwh=("demand_mwh", "sum"),
                  peak_mwh=("demand_mwh", "max"),
                  min_mwh=("demand_mwh", "min"),
                  mean_mwh=("demand_mwh", "mean"),
                  peak_hour=("demand_mwh", lambda s: s.idxmax()))
             .reset_index())
daily["peak_hour"] = long.loc[daily["peak_hour"], "hour"].values
daily["load_factor"] = daily["mean_mwh"] / daily["peak_mwh"]
daily["dow"] = daily["date"].dt.dayofweek        # 0=월
daily["month"] = daily["date"].dt.month
daily["year"] = daily["date"].dt.year

long.drop(columns="robust_z").to_csv(OUT / "demand_hourly.csv", index=False)
daily.to_csv(OUT / "demand_daily.csv", index=False)
print(f"\n저장 완료: demand_hourly.csv ({len(long)}행), demand_daily.csv ({len(daily)}행)")
