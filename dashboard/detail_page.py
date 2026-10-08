"""Page 05 only. Existing page renderers and analysis results are untouched."""
import pandas as pd
import streamlit as st
from ui_components import badges, percentile_chart, stability, compact_table, selection_reason
from detail_data import (load_detail_tables, get_detail, FEATURES, NETWORK, number,
                         flag, period, has_value, raw_view)


@st.cache_data(show_spinner=False)
def cached_detail(root):
    return load_detail_tables(root)


def show_metric(container, label, row, column, decimals=0, unit="", caption=None):
    container.metric(label, number(row.get(column), decimals, unit))
    if caption:
        container.caption(caption)


def render_detail(root, threshold):
    try:
        tables = cached_detail(root)
    except Exception as exc:
        st.error(f"행정동 상세자료를 읽을 수 없습니다: {exc}")
        return
    master = tables["master"]
    gu_list = sorted(master.sigungu_name.unique())
    gu_col, dong_col = st.columns(2)
    gu = gu_col.selectbox("자치구", gu_list, index=gu_list.index("강남구") if "강남구" in gu_list else 0, key="detail_gu")
    local = master.loc[master.sigungu_name.eq(gu)].sort_values("dong_name")
    codes = local.index.tolist()
    code = dong_col.selectbox("행정동", codes, index=codes.index("11230680") if "11230680" in codes else 0,
                              format_func=lambda c: local.loc[c, "dong_name"], key=f"detail_dong_{gu}")
    rows = get_detail(tables, code)
    m, model, candidate = rows["master"], rows["model"], rows.get("candidates", {})
    supply = rows.get("supply", m)
    is_coverage = "coverage" in rows
    scope = "Coverage" if is_coverage else "Primary"
    st.title(f"{gu} · {m['dong_name']}")
    tier = f"Tier {int(float(candidate['final_tier']))}" if candidate else "최종 Tier 대상 외"
    cls = lambda p: model.get(f"candidate_type_{p}", "—").replace("A_PLUS", "A+")
    watch = rows.get("watchlist", {})
    future_member = watch.get("watchlist_type") == "future_pressure_transition_watchlist"
    flags = watch if future_member else model
    transition = flags.get("future_transition_support_p75")
    transition_label = "p75 미래 전환: " + ("해당" if str(transition).lower() == "true" else "비해당" if str(transition).lower() == "false" else "데이터 없음")
    badges("Coverage · 별도 검토" if is_coverage else scope, tier, f"p75 {cls('p75')}", transition_label)
    if is_coverage:
        st.caption("Coverage 검토지역은 별도 모델·425개 기준 percentile입니다. 주 분석과 절대예측값을 직접 비교하지 않습니다.")

    selection_reason(model, candidate, is_coverage)
    st.subheader("수요 배경 · 지역의 특성")
    labels = ["EV 등록대수", "생활인구", "직장인구", "집객시설", "View-T 교통량"]
    for col, (field, (_, unit)), label in zip(st.columns(5), FEATURES.items(), labels):
        show_metric(col, label, m, field, 1 if field == "living_pop_mean" else 0, unit)
    st.caption("View-T 교통량은 추정 링크교통량의 행정동 거리가중평균입니다.")

    st.subheader("현재 충전 인프라와 실제 이용")
    fields = [(supply, "active_port_count", "Active ports", 0), (supply, "station_count", "Station count", 0),
              (model, "sessions_per_day", "sessions/day", 2), (model, "t3_hours_per_day", "T3 hours/day", 2),
              (model, "sessions_per_port_day", "sessions/port/day", 2)]
    cols = st.columns(6)
    for col, (source, field, label, digits) in zip(cols, fields):
        show_metric(col, label, source, field, digits)
    utilization = model.get("port_time_utilization")
    cols[5].metric("Port-time utilization", number(float(utilization) * 100, 1, "%") if has_value(utilization) else "—")

    st.subheader("수요·예상 압력·실제 압력 비교")
    percentile_chart(model, model.get("percentile_reference_n", "—"))

    st.subheader("기준을 바꿔도 진단이 유지되나요?")
    for col, pctl in zip(st.columns(3), ("p70", "p75", "p80")):
        with col:
            st.caption(pctl)
            badges(cls(pctl))
    badges(tier, stability(model))
    if candidate:
        st.caption(f"Pareto {number(candidate.get('pareto_front'))} · Mean rank {number(candidate.get('mean_rank'), 2)} · 최종 후보 7개 내부 순위")
    st.caption(f"조건부 미래 압력 전환 후보: {'해당' if future_member else '해당 없음'} · 선택 {threshold} 전환: {flag(flags.get(f'future_transition_support_{threshold}'))}")

    st.subheader("근거 자료 더 보기")
    with st.expander("기본·수요 특성 더 보기 · 집객시설 / View-T / 분석 가능 여부"):
        left, right = st.columns(2)
        for col, field in zip([left, right], ["poi_total", "viewt_traffic_adt_2024"]):
            label, unit = FEATURES[field]
            show_metric(col, label, m, field, unit=unit, caption=period(m, field))
        st.caption("View-T는 추정 링크교통량의 행정동 거리가중평균이며 행정동 전체 통행량 합계가 아닙니다.")
        st.write(f"핵심 X 결측 변수: {m.get('core_x_missing_variables') or '없음'}")
        st.caption(f"경계 기준: {m.get('boundary_base_date', '자료 없음')} · master 기준: {m.get('master_as_of_date', '자료 없음')} · 모든 425개 행정동을 유지하며 결측을 보간하지 않습니다.")
    with st.expander("도로망 특성 · AIw1kA / AIA / ACw1kC / ACC"):
        for col, (field, label) in zip(st.columns(4), NETWORK.items()):
            show_metric(col, label, m, field, 3, caption=period(m, field))
        st.caption("실제 교통량이 아닌 도로망 구조지표입니다. 저장된 길이가중평균을 표시합니다.")
        st.caption(f"도로망 coverage 상태: {m.get('network_coverage_status', '자료 없음')}")
    with st.expander("충전 공급 · 충전소 / 급속·완속 구성"):
        for col, field, label in zip(st.columns(5), ["active_port_count","station_count","fast_port_count","slow_port_count","unknown_type_port_count"], ["Active ports","Station count","급속 포트","완속 포트","유형 미상 포트"]):
            show_metric(col, label, supply, field)
        st.caption(f"공급 집계 기준: {supply.get('analysis_as_of_date', '자료 없음')} · 급속 비중은 저장 컬럼이 없어 표시하지 않습니다.")
    with st.expander("실제 관측 충전행태 · 수요 / 공급압력 / 보조 추정치"):
        for col, field, label, digits in zip(st.columns(4), ["sessions_per_day","t3_hours_per_day","sessions_per_port_day","port_time_utilization"], ["Sessions/day","T3 hours/day","Sessions/port/day","Port-time utilization"], [2,2,2,3]):
            # T3 hours/day is read from analysis 32, never derived from total minutes.
            show_metric(col, label, model, field, digits)
        st.caption(period(m, "sessions_per_port_day"))
        st.caption("Sessions/day와 T3 hours/day는 관측 충전수요입니다. 포트당 세션과 utilization은 공급압력 지표이며 utilization은 저장된 0–1 비율입니다.")
        if "estimated_kwh_per_port_day" in supply:
            st.write(f"보조 추정치 · estimated kWh/port/day: **{number(supply.get('estimated_kwh_per_port_day'), 2)}**")
            st.caption(f"{period(m, 'estimated_kwh_per_port_day')} · 모델 {supply.get('kwh_model', '자료 없음')} · 실측 전력량이 아닙니다. 동시점 검증 가능: {flag(supply.get('kwh_contemporaneous_validation_available'))}")
    with st.expander("모델 원값 · 저장된 예측수요 / 예상압력"):
        st.caption(f"{model.get('prediction_basis', '자료 없음')} · {scope}")
        if is_coverage:
            st.warning("별도 Core 모델의 원값입니다. Primary409와 절대예측값 직접 비교 금지.")
        fields = {"predicted_sessions_per_day":"예측 sessions/day", "predicted_t3_hours_per_day":"예측 T3 hours/day", "expected_sessions_pressure":"예상 sessions/port/day", "expected_time_pressure":"예상 time pressure"}
        compact_table(pd.DataFrame([{"저장 지표":label,"값":model.get(key)} for key,label in fields.items()]), numeric=("값",), decimals={"값":2})
    with st.expander("전체 데이터 보기"):
        st.caption("선택 행정동의 파일별 원본 컬럼과 저장 문자열입니다. 빈 문자열은 원본 결측이며 동일 컬럼도 출처별로 보존합니다.")
        raw = raw_view(rows)
        raw["원값"] = raw["원값"].map(lambda v: v if has_value(v) else "—")
        st.dataframe(raw, hide_index=True, use_container_width=True, height=440)
