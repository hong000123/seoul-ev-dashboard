"""Read-only, source-preserving lookup for the master 425 administrative dongs."""
from pathlib import Path
import pandas as pd

DETAIL_FILES = {
    "master": "dong_predictor_master.csv",
    "primary": "current_priority_409.csv",
    "supply": "dong_current_demand_supply.csv",
    "candidates": "final_primary_candidates.csv",
    "coverage": "coverage16_priority_sensitivity.csv",
    "watchlist": "coverage_and_future_watchlist.csv",
}
FEATURES = {
    "ev_registrations": ("EV 등록대수", "대"),
    "living_pop_mean": ("생활인구 mean", "명"),
    "work_pop": ("직장인구", "명"),
    "poi_total": ("집객시설 수", "개"),
    "viewt_traffic_adt_2024": ("View-T 평일 연평균 추정교통량", "대/일"),
}
NETWORK = {f"{name}_length_weighted_mean": name for name in ("AIw1kA", "AIA", "ACw1kC", "ACC")}
PERIOD_LABELS = {
    "2026Q2 label; underlying reference date unconfirmed": "2026Q2 제공분기 · 실제 기준시점 미확정(지연자료)",
    "2026Q2 label; annual refresh": "2026Q2 제공분기 · 연 1회 갱신",
    "2024 weekday annual average": "2024년 평일 연평균 · 링크교통량 거리가중평균",
    "2023 road network": "2023년 도로망 · 길이가중평균",
    "P7: 2026-09-22~26 and 2026-10-03~04": "P7 · 2026-09-22~26 및 2026-10-03~04 (7일)",
}


def load_detail_tables(root):
    tables = {}
    for name, filename in DETAIL_FILES.items():
        path = Path(root) / "analysis_outputs" / filename
        if name == "supply" and not path.exists():
            continue
        # Preserve source text (codes, flags, precision, empty cells) for the raw view.
        frame = pd.read_csv(path, encoding="utf-8-sig", dtype=str, keep_default_na=False)
        required = {"dong_code", "sigungu_name", "dong_name"}
        if not required <= set(frame.columns):
            raise ValueError(f"{filename}: 필수 식별 컬럼 없음")
        if frame.dong_code.eq("").any() or frame.dong_code.duplicated().any():
            raise ValueError(f"{filename}: 빈 코드 또는 중복 코드")
        tables[name] = frame.set_index("dong_code", drop=False)
    codes = set(tables["master"].index)
    primary, coverage = set(tables["primary"].index), set(tables["coverage"].index)
    if primary & coverage or primary | coverage != codes:
        raise ValueError("Master와 Primary/Coverage 코드 범위 불일치")
    for key, frame in tables.items():
        shared = frame.index.intersection(tables["master"].index)
        for col in ("sigungu_name", "dong_name"):
            if not frame.loc[shared, col].equals(tables["master"].loc[shared, col]):
                raise ValueError(f"{DETAIL_FILES[key]}: 코드에 연결된 {col} 불일치")
    return tables


def get_detail(tables, code):
    if code not in tables["master"].index:
        raise KeyError("Master425에 없는 행정동")
    rows = {key: frame.loc[code].to_dict() for key, frame in tables.items() if code in frame.index}
    rows["model"] = rows.get("primary", rows.get("coverage", {}))
    return rows


def has_value(value):
    return value is not None and str(value).strip().lower() not in ("", "nan", "na", "none", "<na>")


def number(value, decimals=0, unit=""):
    if not has_value(value):
        return "—"
    try:
        return f"{float(value):,.{decimals}f}" + (f" {unit}" if unit else "")
    except (TypeError, ValueError):
        return str(value)


def flag(value):
    if not has_value(value):
        return "—"
    return {"true": "해당", "false": "해당 없음"}.get(str(value).lower(), str(value))


def period(master, column):
    value = master.get(column + "__source_period", "")
    return PERIOD_LABELS.get(value, value) if has_value(value) else "기준기간 자료 없음"


def raw_view(rows):
    values = []
    for source, row in rows.items():
        if source == "model":
            continue
        values.extend({"파일 / 원본 컬럼": f"{DETAIL_FILES[source]} / {key}", "원값": str(value)}
                      for key, value in row.items())
    return pd.DataFrame(values)
