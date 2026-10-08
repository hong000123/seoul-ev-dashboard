"""Server-free route/interaction checks against the real saved data."""
import ast
import hashlib
import json
from pathlib import Path
import sys
sys.stdout.reconfigure(encoding="utf-8")

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
local_dependencies = HERE / "_ui_dependencies"
if local_dependencies.is_dir():
    sys.path.append(str(local_dependencies))
from streamlit.testing.v1 import AppTest
from data_access import load_tables, display_frame, CLASS_COLUMNS, METRICS
from detail_data import load_detail_tables, number
from ui_components import PAGES

root = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE.parent
source = (HERE / "app.py").read_text(encoding="utf-8")
source = source.replace('ROOT = Path(__file__).resolve().parent.parent', f'ROOT = Path({str(root)!r})')
for name in ("app.py", "detail_page.py", "detail_data.py", "data_access.py", "styles.py", "ui_components.py", "validate_ui.py"):
    ast.parse((HERE / name).read_text(encoding="utf-8"), filename=name)
tables = load_tables(root)
original = {key: frame.copy(deep=True) for key, frame in tables.items()}
checks = []

def healthy(app):
    assert not app.exception, [e.value for e in app.exception]
    assert not app.error, [e.value for e in app.error]

def chart(app, index=0):
    return json.loads(app.get("plotly_chart")[index].proto.spec)

def colored_codes(spec):
    return {code for trace in spec["data"][1:] for code in trace.get("locations", [])}

app = AppTest.from_string(source, default_timeout=40).run()
healthy(app)
assert app.sidebar.radio[1].value == "p75"
assert [m.value for m in app.metric] == ["409", "16", "3", "4", "7"]
for page in PAGES:
    app.sidebar.radio[0].set_value(page).run()
    healthy(app)
    checks.append(page)
    if page == "Demand–Supply Map":
        assert app.selectbox[0].value == "class"
        assert app.checkbox[0].value is False
        assert [m.value for m in app.metric] == ["7개 동", "7개 동", "31개 동", "70개 동", "294개 동"]
        assert not any(t.get("name") == "별도 검토 16개 동" for t in chart(app)["data"])
        assert colored_codes(chart(app)) == set(tables["primary"].dong_code)
        assert "분석 제외/경계 보류" in chart(app)["data"][0]["customdata"]
        assert all(len(t["customdata"][0]) == 12 for t in chart(app)["data"][1:])
        app.checkbox[0].check().run()
        healthy(app)
        outline = next(t for t in chart(app)["data"] if t.get("name") == "별도 검토 16개 동")
        assert len(outline["locations"]) == 16
        assert outline["colorscale"][0][1] == "rgba(0,0,0,0)"
        app.radio[0].set_value("Coverage sensitivity 16").run()
        healthy(app)
        for metric in ("tier", "demand_sessions_pct", "observed_time_pressure_pct"):
            app.selectbox[0].set_value(metric).run()
            healthy(app)
    if page == "Priority Areas":
        spec = chart(app)
        assert colored_codes(spec) == set(tables["candidates"].dong_code)
        assert {t["name"]:len(t["locations"]) for t in spec["data"][1:] if t["type"] == "choroplethmap"} == {"Tier 1":2,"Tier 2":2,"Tier 3":3}
        assert {name for t in spec["data"] if t["type"] == "scattermap" for name in t["text"]} == {"개포1동","잠실4동","신사동","고덕1동","압구정동","도봉1동","화곡1동"}
        for code in tables["candidates"].dong_code:
            app.selectbox[0].set_value(code).run()
            healthy(app)
            assert chart(app, 1)["layout"]["xaxis"]["range"] == [0, 100]
    if page == "EV +10% Scenario":
        future_codes = set(tables["watchlist"].loc[tables["watchlist"].watchlist_type.eq("future_pressure_transition_watchlist"), "dong_code"])
        assert colored_codes(chart(app)) == future_codes
        assert sum(len(t["locations"]) for t in chart(app)["data"][1:] if t["name"] == "p75 전환 후보") == 3
        assert any('badge active' in m.value and '비전환' in m.value for m in app.markdown)
    if page == "Dong Detail":
        detail = load_detail_tables(root)
        for code in ["11230680", tables["coverage"].dong_code.iloc[0], tables["watchlist"].loc[tables["watchlist"].watchlist_type.eq("future_pressure_transition_watchlist"), "dong_code"].iloc[0]]:
            gu = detail["master"].loc[code, "sigungu_name"]
            app.selectbox[0].set_value(gu).run()
            app.selectbox[1].set_value(code).run()
            healthy(app)
            assert chart(app)["layout"]["xaxis"]["range"] == [0, 100]
            assert any("왜 선정 / 비선정되었나요?" in m.value for m in app.markdown)
            assert any("p75 미래 전환:" in m.value for m in app.markdown)
for threshold in ("p70", "p75", "p80"):
    app.sidebar.radio[1].set_value(threshold).run()
    for page in ("Demand–Supply Map", "Priority Areas", "EV +10% Scenario"):
        app.sidebar.radio[0].set_value(page).run()
        healthy(app)
        if page == "Priority Areas":
            assert colored_codes(chart(app)) == set(tables["candidates"].dong_code)
        elif page == "EV +10% Scenario":
            assert colored_codes(chart(app)) == future_codes
for key, frame in tables.items():
    assert frame.equals(original[key]), f"In-memory source mutated: {key}"
assert number(None) == "—" and number(float("nan")) == "—"
baseline_path = HERE / "ui_data_hashes_before.json"
if baseline_path.exists():
    baseline = json.loads(baseline_path.read_text(encoding="utf-8-sig"))
    for entry in baseline:
        with Path(entry["Path"]).open("rb") as handle:
            assert hashlib.file_digest(handle, "sha256").hexdigest().upper() == entry["Hash"], entry["Path"]
result = {"status":"PASS", "syntax":"PASS", "routes":checks, "default_threshold":"p75", "coverage_default":False, "source_hashes_unchanged":baseline_path.exists(), "interactions":"7 candidates, Primary/Coverage/future detail, map metrics, all thresholds", "server_started":False}
(HERE / "ui_validation_result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(result, ensure_ascii=False, indent=2))
