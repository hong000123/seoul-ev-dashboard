"""Read-only integration validation, without Streamlit/Plotly dependencies."""
import ast
import hashlib
import json
from pathlib import Path
import sys
sys.stdout.reconfigure(encoding="utf-8")

from data_access import FILES, METRICS, load_tables, load_boundaries, join_report, display_frame, saved_flag

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent
source_files = [root / "analysis_outputs" / name for name in FILES.values()]
source_files += [root / "reference_data" / "seoul_dong_2025_2Q.geojson"]
source_files += [root / "analysis_outputs" / "dong_predictor_master.csv", root / "analysis_outputs" / "dong_current_demand_supply.csv"]
def hashes():
    return {str(p): hashlib.file_digest(p.open("rb"), "sha256").hexdigest() for p in source_files}
before = hashes()
for path in Path(__file__).parent.glob("*.py"):
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
tables = load_tables(root)
geo, path, engine = load_boundaries(root)
report = join_report(tables, geo)
assert {k:len(v) for k,v in tables.items()} == {"primary":409,"coverage":16,"candidates":7,"watchlist":23}
assert all(v["matched"] == v["total"] for v in report.values())
assert len(geo["features"]) == 426
assert tables["primary"].percentile_reference_n.eq(409).all()
assert tables["coverage"].percentile_reference_n.eq(425).all()
assert tables["primary"].analysis_scope.eq("Primary409").all()
assert tables["coverage"].analysis_scope.eq("Coverage16").all()
assert tables["primary"].candidate_type_p75.value_counts()["A_PLUS"] == 3
assert tables["primary"].candidate_type_p75.value_counts()["A"] == 4
candidates = tables["candidates"]
expected = {1:{"개포1동","잠실4동"},2:{"신사동","고덕1동"},3:{"압구정동","도봉1동","화곡1동"}}
for tier,names in expected.items():
    assert set(candidates.loc[candidates.final_tier.eq(tier),"dong_name"]) == names
assert candidates.loc[candidates.dong_name.eq("신사동"),"sigungu_name"].eq("강남구").all()
assert candidates.loc[candidates.final_tier.eq(1),"final_order_tie"].all()
assert candidates.loc[candidates.final_tier.eq(1),"final_priority_order"].eq(1).all()
display = display_frame(tables["primary"], candidates)
assert display[list(METRICS)].equals(tables["primary"][list(METRICS)])
assert display.tier_label.eq("Tier 1").sum() == 2
future = tables["watchlist"].loc[tables["watchlist"].watchlist_type.eq("future_pressure_transition_watchlist")]
assert set(future.dong_name) == {"이태원2동","보광동","성수2가1동","자양2동","장안1동","방배4동","마천2동"}
assert not set(future.dong_code) & set(candidates.dong_code)
assert [int(saved_flag(future[f"future_transition_support_p{p}"]).sum()) for p in (70,75,80)] == [3,3,1]
def check_coords(coords):
    if isinstance(coords[0], (int,float)):
        assert 126 < coords[0] < 128 and 37 < coords[1] < 38, coords
    else:
        for part in coords:
            check_coords(part)
for feature in geo["features"]:
    assert feature["geometry"]["type"] in ("Polygon","MultiPolygon")
    check_coords(feature["geometry"]["coordinates"])
try:
    from shapely.geometry import shape
    assert all(shape(f["geometry"]).is_valid for f in geo["features"])
    geometry_status = "426 valid polygons"
except ImportError:
    geometry_status = "coordinate and geometry type validation only"
assert before == hashes(), "Source files changed"
print(json.dumps({"status":"PASS","engine":engine,"boundary_count":len(geo["features"]),"joins":report,
                  "geometry":geometry_status,"source_hashes_unchanged":True,
                  "ui_runtime":"Run validate_ui.py for server-free Streamlit route checks"}, ensure_ascii=False, indent=2))
