"""Read-only presentation adapter. No ranking, modelling or classification."""
from pathlib import Path
import json
import pandas as pd

METRICS = {
    "demand_sessions_pct": "예측 충전횟수 수요",
    "demand_t3_pct": "예측 T3 시간 수요",
    "expected_sessions_pressure_pct": "예상 충전횟수 압력",
    "expected_time_pressure_pct": "예상 시간 압력",
    "observed_sessions_pressure_pct": "관측 충전횟수 압력",
    "observed_time_pressure_pct": "관측 시간 압력",
}
CLASS_COLUMNS = [f"candidate_type_p{p}" for p in (70, 75, 80)]
FILES = {
    "primary": "current_priority_409.csv",
    "candidates": "final_primary_candidates.csv",
    "coverage": "coverage16_priority_sensitivity.csv",
    "watchlist": "coverage_and_future_watchlist.csv",
}


def load_tables(root):
    tables = {}
    for key, filename in FILES.items():
        frame = pd.read_csv(Path(root) / "analysis_outputs" / filename,
                            encoding="utf-8-sig", dtype={"dong_code": "string"})
        required = ["dong_code", "sigungu_name", "dong_name", *METRICS, *CLASS_COLUMNS]
        if key == "candidates":
            required += ["final_tier", "evidence_class", "pareto_front", "mean_rank",
                         "final_priority_order", "final_order_tie"]
        if key in ("primary", "coverage"):
            required += ["analysis_scope", "prediction_basis", "percentile_reference_n"]
        if key == "watchlist":
            required += ["watchlist_type", *[f"future_transition_support_p{p}" for p in (70, 75, 80)]]
        missing = set(required) - set(frame.columns)
        if missing:
            raise ValueError(f"{filename}: 필요한 저장 컬럼 없음: {sorted(missing)}")
        if frame.dong_code.duplicated().any():
            raise ValueError(f"{filename}: 중복 행정동 코드")
        for col in METRICS:
            frame[col] = pd.to_numeric(frame[col], errors="raise")
            if not frame[col].between(0, 100).all():
                raise ValueError(f"{filename}: {col}의 0~100 값 또는 결측값 확인 필요")
        for col in CLASS_COLUMNS:
            if not frame[col].isin(["A_PLUS", "A", "B", "C", "D", "OTHER"]).all():
                raise ValueError(f"{filename}: {col}에 미지원 분류")
        tables[key] = frame
    if set(tables["primary"].dong_code) & set(tables["coverage"].dong_code):
        raise ValueError("Primary와 Coverage 코드가 겹칩니다.")
    if not set(tables["candidates"].dong_code) <= set(tables["primary"].dong_code):
        raise ValueError("최종 후보가 Primary409 범위를 벗어납니다.")
    return tables


def load_boundaries(root):
    """Read the lossless Seoul-only EPSG:4326 deployment boundary."""
    path = Path(root) / "reference_data" / "seoul_dong_2025_2Q.geojson"
    with path.open("r", encoding="utf-8") as handle:
        collection = json.load(handle)
    if collection.get("type") != "FeatureCollection":
        raise ValueError("서울 경계 GeoJSON 형식 확인 필요")
    features = collection.get("features", [])
    if len(features) != 426:
        raise ValueError(f"서울 행정동 경계는 426개여야 합니다: {len(features)}개")
    codes = []
    for feature in features:
        props = feature["properties"]
        code = props["ADM_CD"]
        if not isinstance(code, str) or not code.startswith("11") or not props.get("ADM_NM"):
            raise ValueError("서울 경계 코드/행정동명 확인 필요")
        if feature["geometry"]["type"] not in ("Polygon", "MultiPolygon"):
            raise ValueError("서울 경계 geometry 형식 확인 필요")
        codes.append(code)
    if len(codes) != len(set(codes)):
        raise ValueError("서울 경계 코드 중복")
    return collection, str(path), "GeoJSON EPSG:4326"


def join_report(tables, geojson):
    codes = {f["properties"]["ADM_CD"] for f in geojson["features"]}
    return {key: {"matched": int(frame.dong_code.isin(codes).sum()), "total": len(frame),
                  "missing": frame.loc[~frame.dong_code.isin(codes), "dong_code"].tolist()}
            for key, frame in tables.items()}


def display_frame(frame, candidates):
    result = frame.copy()
    tiers = candidates.set_index("dong_code").final_tier
    result["tier_label"] = result.dong_code.map(tiers).map(
        {1: "Tier 1", 2: "Tier 2", 3: "Tier 3"}).fillna("최종 Tier 대상 외")
    result["area_label"] = result.dong_name + " (" + result.sigungu_name + ")"
    for col in CLASS_COLUMNS:
        result[col] = result[col].replace({"A_PLUS": "A+"})
    return result


def saved_flag(series):
    return series.astype(str).str.lower().eq("true")
