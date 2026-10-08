"""Presentation of saved analyses 32–33. Run with streamlit run app.py."""
from pathlib import Path
import sys

try:
    import streamlit as st
    import plotly.graph_objects as go
except ImportError as exc:
    raise SystemExit("필요 패키지가 없습니다. README.md의 설치 명령을 확인하세요. " + str(exc))

from data_access import METRICS, CLASS_COLUMNS, load_tables, load_boundaries, join_report, display_frame, saved_flag

st.set_page_config(page_title="서울시 전기차 충전 수요–공급 불균형 분석", layout="wide")
ROOT = Path(__file__).resolve().parent.parent
from styles import CSS, CLASS_COLORS, CLASS_LABELS, TIER_COLORS, FONT
from ui_components import (PAGES, DEFAULT_THRESHOLD, page_header, badges, tier_cards,
                           process_flow, compact_table, percentile_chart, stability,
                           message_banner, class_legend, add_priority_labels)
st.markdown(CSS, unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def read_tables():
    return load_tables(ROOT)


@st.cache_data(show_spinner="서울 행정동 경계 불러오는 중…")
def read_boundaries():
    return load_boundaries(ROOT)


try:
    tables = read_tables()
except Exception as exc:
    st.error(f"분석 결과를 읽을 수 없습니다: {exc}")
    st.stop()

primary = display_frame(tables["primary"], tables["candidates"])
coverage = display_frame(tables["coverage"], tables["candidates"])
candidates = display_frame(tables["candidates"], tables["candidates"])
future = tables["watchlist"].loc[tables["watchlist"].watchlist_type.eq("future_pressure_transition_watchlist")].copy()

with st.sidebar:
    st.markdown('<div class="brand">SEOUL · EV</div><div class="brand-sub">Demand–Supply Mismatch</div>', unsafe_allow_html=True)
    page = st.radio("페이지", list(PAGES), label_visibility="collapsed",
                    format_func=lambda x: {"Overview": "01 연구 개요", "Demand–Supply Map": "02 수요–공급 지도", "Priority Areas": "03 우선 검토지역", "EV +10% Scenario": "04 EV +10% 시나리오", "Dong Detail": "05 행정동 상세 조회"}[x])
    st.divider()
    with st.container(border=True):
        threshold = st.radio("저장된 분류 기준", ["p70", "p75", "p80"], index=["p70", "p75", "p80"].index(DEFAULT_THRESHOLD), horizontal=True)
        st.caption("최종 Tier는 기준 선택과 관계없이 유지됩니다.")
    st.caption("주 분석 409개 · 별도 검토 16개 동")
    with st.expander("분석 기준 상세"):
        st.caption("Primary409 · Full26 OOF409\n\nCoverage16 · Core31 OOF425")
        st.caption("저장된 분류·전환 플래그만 선택합니다. Percentile과 최종 Tier는 저장값입니다.")

page_header(page, f"{threshold} 기준으로 확장 검토 유형을 구분한 결과" if page == "Demand–Supply Map" else None)


def get_map_data():
    try:
        geo, path, engine = read_boundaries()
        report = join_report(tables, geo)
        for key, result in report.items():
            if result["missing"]:
                st.warning(f"{key}: 경계 미연결 {result['missing']}")
        return geo, report
    except Exception as exc:
        st.error(f"지도 로딩 실패: {exc}")
        st.info("README.md의 지도 의존성 및 설치 명령을 확인하세요. 다른 페이지의 저장 결과는 볼 수 있습니다.")
        return None, None


def add_polygons(fig, geo, frame, values, name, color=None, line_color="white", line_width=.7, scale=None, context=None):
    if frame.empty:
        return
    hovercols = ["dong_name", "sigungu_name", "candidate_type_p75", "tier_label", *METRICS]
    custom = frame[hovercols].to_numpy().tolist()
    for item, (_, row) in zip(custom, frame.iterrows()):
        item.extend([CLASS_LABELS.get(row.candidate_type_p75, row.candidate_type_p75),
                     CLASS_LABELS.get(row[f"candidate_type_{threshold}"], row[f"candidate_type_{threshold}"])])
    hover = "<b>%{customdata[0]} · %{customdata[1]}</b><br>p75: %{customdata[10]} (%{customdata[2]}) · %{customdata[3]}<br>"
    if threshold != "p75":
        hover += f"선택 {threshold}: %{{customdata[11]}}<br>"
    if context:
        hover += context + "<br>"
    hover += "수요 · 세션 %{customdata[4]:.1f} / T3 %{customdata[5]:.1f}<br>예상 압력 · 세션 %{customdata[6]:.1f} / 시간 %{customdata[7]:.1f}<br>실제 압력 · 세션 %{customdata[8]:.1f} / 시간 %{customdata[9]:.1f}<extra></extra>"
    fig.add_trace(go.Choroplethmap(
        geojson=geo, featureidkey="properties.ADM_CD", locations=frame.dong_code,
        z=values, zmin=0, zmax=100 if scale else 1,
        colorscale=scale or [[0, color], [1, color]], showscale=bool(scale),
        colorbar={"title": "상대위치", "ticksuffix": "", "tickvals": [0, 25, 50, 75, 100], "thickness": 14},
        marker={"line": {"color": line_color, "width": line_width}, "opacity": 1},
        customdata=custom, hovertemplate=hover, name=name, showlegend=not bool(scale)))


def map_figure(geo, frame, metric, scenario=False, height=710, show_coverage=False, priority=False):
    fig = go.Figure()
    features = geo["features"]
    primary_codes, coverage_codes = set(primary.dong_code), set(coverage.dong_code)
    background_status = []
    for feature in features:
        code = feature["properties"]["ADM_CD"]
        if code not in primary_codes | coverage_codes:
            status = "분석 제외/경계 보류"
        elif code in coverage_codes:
            status = "별도 검토 16개 동 · 현재 주 분석 순위와 분리"
        else:
            status = "최종 7개 후보 외" if priority else "미래 전환 보조 후보 외" if scenario else "현재 선택 보기에서 비강조"
        background_status.append(status)
    fig.add_trace(go.Choroplethmap(
        geojson=geo, featureidkey="properties.ADM_CD", locations=[f["properties"]["ADM_CD"] for f in features],
        z=[0] * len(features), colorscale=[[0, "#F7F9FA"], [1, "#F7F9FA"]], showscale=False,
        marker={"line": {"color": "#E2E8F0", "width": .4}},
        text=[f["properties"]["ADM_NM"] for f in features],
        customdata=background_status,
        hovertemplate="%{text}<br>%{customdata}<extra></extra>", showlegend=False))
    if priority:
        # Only the saved seven candidates are colored. No recomputation of Tier.
        for tier in ("Tier 1", "Tier 2", "Tier 3"):
            part = frame.loc[frame.tier_label.eq(tier)]
            add_polygons(fig, geo, part, [0]*len(part), tier, TIER_COLORS[tier],
                         "#1D4ED8" if tier == "Tier 1" else "white", 2 if tier == "Tier 1" else 1,
                         context="최종 확장 우선 검토지역 · 공동 1순위" if tier == "Tier 1" else "최종 확장 우선 검토지역")
        add_priority_labels(fig, geo, frame)
    elif scenario:
        # The current watchlist union is kept separate from the final Tier layer.
        active_codes = set(future.loc[saved_flag(future[f"future_transition_support_{threshold}"]), "dong_code"])
        subset = primary.loc[primary.dong_code.isin(future.dong_code)]
        for active, color, label in [(False, "#FDE7C1", "다른 기준 전환 후보"), (True, "#D97706", f"{threshold} 전환 후보")]:
            selected = subset.loc[subset.dong_code.isin(active_codes).eq(active)]
            add_polygons(fig, geo, selected, [0]*len(selected), label, color, "#B45309", 1.5,
                         context=label + " · 현재 우선후보와 별도인 보조 민감도 결과")
    else:
        if metric in METRICS:
            add_polygons(fig, geo, frame, frame[metric], METRICS[metric], scale=[[0,"#edf4fb"],[.5,"#72add1"],[1,"#124e8a"]])
        else:
            column, palette = (f"candidate_type_{threshold}", CLASS_COLORS) if metric == "class" else ("tier_label", TIER_COLORS)
            for label, color in palette.items():
                part = frame.loc[frame[column].eq(label)]
                meaning = CLASS_LABELS.get(label, label)
                coverage_only = not frame.empty and frame.dong_code.isin(coverage_codes).all()
                add_polygons(fig, geo, part, [0]*len(part), meaning,
                             "rgba(0,0,0,0)" if coverage_only else color,
                             color if coverage_only and label != "OTHER" else "#B45309" if coverage_only else "white",
                             2 if coverage_only else .5, context="별도 검토 16개 동" if coverage_only else None)
        # Coverage is an explicit outline layer, never pooled with Primary values.
        if show_coverage:
            add_polygons(fig, geo, coverage, [0]*len(coverage), "별도 검토 16개 동", "rgba(0,0,0,0)", "#B45309", 2, context="별도 검토 16개 동 · 주 분석과 분리")
    fig.update_layout(height=height, margin={"l":0,"r":0,"t":0,"b":0}, paper_bgcolor="white",
                      map={"style":"white-bg", "center":{"lat":37.555,"lon":126.985}, "zoom":10.25},
                      font={"family":FONT, "color":"#102A43"},
                      showlegend=scenario or priority, legend={"orientation":"h","y":1.01,"x":0,"bgcolor":"rgba(255,255,255,.9)"},
                      hoverlabel={"font":{"family":FONT,"size":13},"bgcolor":"white"},
                      uirevision="priority-map" if priority else "scenario-map" if scenario else "diagnosis-map")
    return fig


if page == "Overview":
    cols = st.columns(5)
    for col, label, value in zip(cols, ["Primary 분석 행정동", "Coverage sensitivity", "p75 A+", "p75 A", "최종 우선 검토지역"],
                                 [len(primary), len(coverage), int(primary.candidate_type_p75.eq("A+").sum()), int(primary.candidate_type_p75.eq("A").sum()), len(candidates)]):
        col.metric(label, value)
    process_flow()
    st.subheader("충전 인프라 확장 우선 검토지역")
    tier_cards(candidates)
    st.caption("개포1동 · 잠실4동은 공동 Tier 1입니다. 최종 Tier는 분류 기준 선택과 관계없이 유지됩니다.")
    left, right = st.columns([1.45, 1])
    with left:
        counts = primary[f"candidate_type_{threshold}"].value_counts().reindex(CLASS_COLORS, fill_value=0)
        fig = go.Figure(go.Bar(x=counts.index, y=counts.values, text=counts.values, textposition="outside", marker_color=list(CLASS_COLORS.values())))
        fig.update_layout(title=f"{threshold} 진단 분류 · 주 분석 행정동", height=270, margin={"l":20,"r":20,"t":50,"b":20}, paper_bgcolor="white", plot_bgcolor="white", yaxis_title="행정동 수", yaxis_range=[0, max(counts)*1.2])
        st.plotly_chart(fig, use_container_width=True)
    with right:
        st.markdown("#### 결과를 읽는 기준")
        st.write("6개 percentile은 각 분석 기준 내 0–100 상대위치입니다.")
        st.write("주 분석과 Coverage 검토는 예측 기반과 기준 모집단이 다릅니다.")
        st.write("EV +10% 보조 관찰지역은 별도 시나리오 페이지에 표시합니다.")

elif page == "Demand–Supply Map":
    scope_col, metric_col, outline_col = st.columns([1, 1.4, 1])
    cohort = scope_col.radio("분석 범위", ["Primary409", "Coverage sensitivity 16"], horizontal=True,
                             format_func=lambda x: "주 분석 409개" if x == "Primary409" else "별도 검토 16개 동")
    labels = {"class":f"{threshold} 진단 분류", "tier":"최종 Tier", **{k:v+" percentile" for k,v in METRICS.items()}}
    metric = metric_col.selectbox("지도 지표", list(labels), index=0, format_func=labels.get)
    show_coverage = outline_col.checkbox("별도 검토 16개 동 보기", value=False)
    selected_frame = primary if cohort == "Primary409" else coverage
    class_counts = selected_frame[f"candidate_type_{threshold}"].value_counts()
    count_aa = int(class_counts.get("A+", 0) + class_counts.get("A", 0))
    for col, label, count in zip(st.columns(5), ["확장 검토 · A+/A", "모델 압력 후보 · B", "운영 hotspot · C", "수요·공급 상대 여유 · D", "기타 · OTHER"],
                                [count_aa, int(class_counts.get("B",0)), int(class_counts.get("C",0)), int(class_counts.get("D",0)), int(class_counts.get("OTHER",0))]):
        col.metric(label, f"{count}개 동")
    scope_label = "주 분석 409개" if cohort == "Primary409" else "별도 검토 16개 동"
    message_banner(f"{scope_label} · {threshold} 기준 확장 검토(A+/A)는 {count_aa}개 동입니다. 다른 동은 모델 압력 후보·운영 hotspot·상대 여유·기타로 구분됩니다.")
    if metric == "class":
        class_legend(show_coverage or cohort != "Primary409")
    elif metric == "tier":
        badges("Tier 1", "Tier 2", "Tier 3")
    if cohort != "Primary409":
        st.caption("별도 검토 16개 동은 경계 중심으로 표시합니다. 별도 모델·425개 기준 percentile이며 주 분석과 통합 순위를 만들지 않습니다.")
        if metric == "tier":
            st.info("Coverage 검토지역은 최종 Tier 대상이 아닙니다.")
    geo, report = get_map_data()
    if geo:
        if metric != "class":
            st.caption(f"지도는 ‘{labels[metric]}’를 표시합니다. 위 카드와 배너는 선택 기준의 진단 분류 요약입니다.")
        st.plotly_chart(map_figure(geo, selected_frame, metric, show_coverage=show_coverage), use_container_width=True, config={"displaylogo":False,"scrollZoom":True})
        with st.expander("지도 연결 및 분석 기준"):
            st.caption(f"경계 조인: Primary {report['primary']['matched']}/409 · Coverage {report['coverage']['matched']}/16 · 서울 {len(geo['features'])}개 경계")
            st.caption("Primary409 · Full26 spatial OOF409 / Coverage16 · Core31 new spatial OOF425")

elif page == "Priority Areas":
    st.markdown('<div class="hero"><h2>최종 확장 우선 검토지역 7개</h2><p>개포1동 · 잠실4동은 공동 1순위입니다. 아래 지도는 저장된 최종 후보 7개만 강조합니다.</p></div>', unsafe_allow_html=True)
    tier_cards(candidates)
    st.caption("개포1동 · 잠실4동 공동 1순위 · 표의 행 배치는 두 지역의 우열을 뜻하지 않습니다.")
    geo, report = get_map_data()
    if geo:
        st.plotly_chart(map_figure(geo, candidates, "tier", priority=True, height=580), use_container_width=True, config={"displaylogo":False})
    st.subheader("최종 7개 후보의 분류와 순위 근거")
    view = candidates[["tier_label", "sigungu_name", "dong_name", "candidate_type_p75", "pareto_front", "mean_rank"]].rename(columns={"tier_label":"Tier", "sigungu_name":"자치구", "dong_name":"행정동", "candidate_type_p75":"p75", "pareto_front":"Pareto", "mean_rank":"Mean rank"})
    compact_table(view, numeric=("Pareto", "Mean rank"), status=("Tier", "p75"), decimals={"Mean rank":2})
    selected = st.selectbox("후보 상세", candidates.dong_code.tolist(), format_func=candidates.set_index("dong_code").area_label.to_dict().get)
    row = candidates.set_index("dong_code").loc[selected]
    left, right = st.columns([.85, 2])
    with left:
        st.subheader(row.dong_name)
        st.caption(row.sigungu_name)
        badges(row.tier_label, row.candidate_type_p75, stability(row))
        st.caption(" · ".join(f"p{p}: {row[f'candidate_type_p{p}']}" for p in (70,75,80)))
        st.caption(f"Pareto {int(row.pareto_front)} · Mean rank {row.mean_rank:.2f}")
        st.caption("Mean rank는 최종 후보 7개 내부 평균순위이며 작을수록 높습니다.")
    with right:
        percentile_chart(row)

elif page == "EV +10% Scenario":
    st.markdown('<div class="hero"><h2>EV +10%는 공간 우선순위를 거의 바꾸지 않았습니다</h2><p>수요·압력 순위 Spearman ≈ 0.9999 · 순위 재편보다 전반적인 수준 상승(level-shift)이 중심입니다.</p><span class="badge" style="background:#DBEAFE;color:#2563EB">Mostly level-shift</span><p>현재 우선후보와는 별도인 보조 민감도 결과 · 지도는 전환 후보 7개만 강조합니다.</p></div>', unsafe_allow_html=True)
    correlation_card, watchlist_card = st.columns(2)
    correlation_card.metric("현재–+10% 순위 상관", "≈ 0.9999")
    watchlist_card.metric("조건부 전환 watchlist", f"{len(future)}개")
    with st.expander("시나리오 해석 근거"):
        st.caption("저장된 30번 분석의 4개 지표 Spearman 범위: 0.999826–0.999907")
    left, right = st.columns([1, 2.2])
    with left:
        st.subheader("Future watchlist · 7개")
        st.caption("조건부 미래 압력 전환 후보")
        watch = future[["sigungu_name", "dong_name"]].copy()
        for p in (70,75,80):
            watch[f"p{p} 전환"] = saved_flag(future[f"future_transition_support_p{p}"]).map({True:"전환",False:"비전환"})
        compact_table(watch.rename(columns={"sigungu_name":"자치구","dong_name":"행정동"}), status=tuple(f"p{p} 전환" for p in (70,75,80)))
        count = int(saved_flag(future[f"future_transition_support_{threshold}"]).sum())
        st.metric(f"{threshold} 저장 전환 플래그", f"{count}개")
        st.caption("7개는 p70/p75/p80 보조 관찰지역의 합집합입니다. 진한 주황은 선택 기준, 옅은 주황은 다른 기준의 관찰지역입니다. 최종 Tier와 별도로 표시합니다.")
    with right:
        geo, report = get_map_data()
        if geo:
            st.plotly_chart(map_figure(geo, primary, "class", scenario=True, height=590), use_container_width=True, config={"displaylogo":False})

    st.markdown('<div class="callout">현재 우선후보와는 별도인 보조 민감도 결과입니다. 미래 최적입지 결과가 아니라 현재 압력 기준 주변 지역을 검토한 결과입니다.</div>', unsafe_allow_html=True)

elif page == "Dong Detail":
    from detail_page import render_detail
    render_detail(ROOT, threshold)
