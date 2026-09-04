"""대시보드용 압축 데이터 생성 (dashboard_data.json)."""
from pathlib import Path
import pandas as pd, numpy as np, json

ROOT = Path(__file__).resolve().parents[1]
d = pd.read_csv(ROOT/"data/processed/daily_merged.csv", parse_dates=["date"]).sort_values("date")
h = pd.read_csv(ROOT/"data/processed/demand_hourly.csv", parse_dates=["datetime","date"])
h["year"]=h["date"].dt.year; h["month"]=h["date"].dt.month

out = {
  "start": d["date"].min().strftime("%Y-%m-%d"),
  "n": len(d),
  # 일별: 총수요(GWh 정수), 최대수요(MW 정수), 평균기온(0.1도 정수)
  "total": [int(round(v/1000)) for v in d["total_mwh"]],
  "peak":  [int(round(v)) for v in d["peak_mwh"]],
  "temp":  [int(round(v*10)) for v in d["temp_avg"]],
  "dow":   [int(v) for v in d["dow"]],
  # 연도x월x시간 평균 (GW 소수1자리) — 시간대 프로파일용
  "profile": {},
}
pv = h.groupby(["year","month","hour"])["demand_mwh"].mean()/1000
for (yr,mo,hr), v in pv.items():
    out["profile"].setdefault(str(yr), {}).setdefault(str(mo), {})[str(hr)] = round(float(v),2)

p = ROOT/"dashboard_data.json"
p.write_text(json.dumps(out, separators=(",",":")))
print(f"저장: {p.name}  {p.stat().st_size/1024:.0f} KB  ({out['n']}일)")
