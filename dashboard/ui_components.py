"""Reusable, read-only presentation helpers."""
from html import escape
import streamlit as st
import plotly.graph_objects as go
from data_access import METRICS
from detail_data import has_value, number
from styles import CLASS_COLORS, CLASS_LABELS, TIER_COLORS, FONT

PAGES = {"Overview": ("서울시 전기차 충전 수요–공급 불균형 분석", "행정동 단위 관측 충전수요 예측과 충전 인프라 확장 우선지역 분석"),
         "Demand–Supply Map": ("서울 행정동 수요–공급 진단 지도", "p75 기준으로 확장 검토 유형을 구분한 결과"),
         "Priority Areas": ("충전 인프라 확장 우선 검토지역", "최종 7개 후보만 강조해 확장 검토의 공간 우선순위를 보여줍니다"),
         "EV +10% Scenario": ("EV +10% 시나리오", "전기차 증가에 따른 공간 우선순위와 조건부 미래 압력 전환 후보"),
         "Dong Detail": ("행정동 상세 조회", "지역 특성, 충전 인프라와 모델 기반 진단을 함께 확인합니다")}
DEFAULT_THRESHOLD = "p75"

def page_header(page, subtitle=None):
    title, default_subtitle = PAGES[page]
    subtitle = subtitle or default_subtitle
    st.markdown(f'<div class="page-header"><h1>{escape(title)}</h1><p class="subtitle">{escape(subtitle)}</p></div>', unsafe_allow_html=True)

def badge(value):
    label = str(value).replace("A_PLUS", "A+") if has_value(value) else "—"
    color = CLASS_COLORS.get(label, TIER_COLORS.get(label, "#64748B"))
    if label == "OTHER":
        color = "#64748B"
    if label.startswith("p75 "):
        color = CLASS_COLORS.get(label.removeprefix("p75 "), "#64748B")
        if label == "p75 OTHER":
            color = "#64748B"
    if label in ("전환", "비전환"):
        return f'<span class="badge {"active" if label == "전환" else "inactive"}">{label}</span>'
    return f'<span class="badge" style="color:{color};background:{color}18">{escape(label)}</span>'

def badges(*values):
    st.markdown("".join(badge(v) for v in values), unsafe_allow_html=True)

def tier_cards(candidates):
    for col, tier in zip(st.columns(3), (1, 2, 3)):
        group = candidates.loc[candidates.final_tier.eq(tier)]
        names = " · ".join(group.dong_name)
        note = "공동 1순위 · 두 지역의 우열 없음" if tier == 1 else "저장된 최종 우선순위"
        col.markdown(f'<div class="tiercard tier{tier}">{badge(f"Tier {tier}")}<p>{escape(names)}</p><small>{note}</small></div>', unsafe_allow_html=True)

def message_banner(message):
    st.markdown(f'<div class="message-banner">{escape(message)}</div>', unsafe_allow_html=True)

def class_legend(include_coverage=False):
    items = ''.join(f'<span><i style="background:{color}"></i>{escape(CLASS_LABELS[code])} <small>({code})</small></span>' for code,color in CLASS_COLORS.items())
    if include_coverage:
        items += '<span><i class="outline-dot"></i>별도 검토 16개 동 <small>(Coverage)</small></span>'
    st.markdown(f'<div class="legend">{items}</div>', unsafe_allow_html=True)

def selection_reason(model, candidate, is_coverage):
    """Explain saved membership only; do not infer or recompute selection."""
    cls = str(model.get("candidate_type_p75", "—")).replace("A_PLUS", "A+")
    meaning = CLASS_LABELS.get(cls, "진단 데이터 없음")
    if is_coverage:
        text = f"이 동은 별도 검토 16개 동(Coverage)에 속하며 p75 진단은 ‘{meaning}’입니다. 별도 모델의 민감도 검토 대상으로, 현재 주 분석의 최종 7개 후보 순위에는 포함되지 않습니다."
    elif candidate:
        tier = int(float(candidate['final_tier']))
        text = f"p75에서 ‘{meaning}’로 분류되어 현재 확장 검토 후보 7개에 포함되었습니다. 저장된 안정성·Pareto·순위통합 결과의 최종 분류는 Tier {tier}이며, "
        text += "개포1동·잠실4동이 공동 1순위입니다." if tier == 1 else "세부 근거는 아래 기준별 분류와 6개 percentile에서 확인할 수 있습니다."
    else:
        text = f"p75 진단은 ‘{meaning}’입니다. 현재 최종 7개는 주 분석의 p75 A+/A 후보로 구성되며, 이 동은 저장된 최종 후보 목록에 포함되지 않았습니다."
    st.markdown(f'<div class="reason-card"><b>왜 선정 / 비선정되었나요?</b><p>{escape(text)}</p></div>', unsafe_allow_html=True)

def process_flow():
    steps = ["지역특성", "관측 충전수요 예측", "현재 공급 대비 압력", "실제 이용압력 교차확인", "확장 우선지역"]
    st.markdown('<div class="flow">' + '<span class="flow-arrow">→</span>'.join(f'<div class="flow-step"><small>0{i}</small>{s}</div>' for i, s in enumerate(steps, 1)) + '</div>', unsafe_allow_html=True)

def compact_table(frame, numeric=(), status=(), decimals=None):
    decimals = decimals or {}
    header = "".join(f'<th class="{"numeric" if c in numeric else ""}">{escape(str(c))}</th>' for c in frame.columns)
    rows = []
    for _, row in frame.iterrows():
        cells = []
        for col, value in row.items():
            if not has_value(value):
                content = "—"
            elif col in status:
                content = badge(value)
            else:
                content = escape(number(value, decimals.get(col, 0)) if col in numeric else str(value))
            cells.append(f'<td class="{"numeric" if col in numeric else ""}">{content}</td>')
        rows.append("<tr>" + "".join(cells) + "</tr>")
    st.markdown(f'<table class="research-table"><thead><tr>{header}</tr></thead><tbody>{"".join(rows)}</tbody></table>', unsafe_allow_html=True)

def percentile_chart(row, reference=409):
    groups = ["수요"] * 2 + ["예상 공급압력"] * 2 + ["실제 이용압력"] * 2
    labels = ["예측 세션수요", "예측 T3수요", "예상 세션압력", "예상 시간압력", "관측 세션압력", "관측 시간압력"]
    colors = ["#2563EB"] * 2 + ["#0D9488"] * 2 + ["#F59E0B"] * 2
    values = [float(row[k]) if has_value(row.get(k)) else None for k in METRICS]
    fig = go.Figure(go.Bar(x=values, y=list(range(6)), orientation="h", marker_color=colors,
        text=[f"{v:.1f}" if v is not None else "데이터 없음" for v in values], textposition="outside", cliponaxis=False,
        customdata=list(zip(groups, labels)), hovertemplate="%{customdata[0]} · %{customdata[1]}: %{x:.1f}<extra></extra>"))
    fig.update_layout(height=340, margin={"l":5,"r":48,"t":10,"b":40}, font={"family":FONT,"color":"#102A43"},
        xaxis={"range":[0,100],"dtick":25,"title":f"분석 기준 {reference}개 내 상대위치 (percentile)","gridcolor":"#E2E8F0","fixedrange":True},
        yaxis={"autorange":"reversed","tickvals":list(range(6)),"ticktext":labels}, paper_bgcolor="white", plot_bgcolor="white",
        shapes=[{"type":"line","xref":"paper","x0":0,"x1":1,"y0":y,"y1":y,"line":{"color":"#E2E8F0","width":1}} for y in (1.5,3.5)])
    st.markdown('<div class="group-key">수요 <span style="color:#2563EB">●</span>　 예상 공급압력 <span style="color:#0D9488">●</span>　 실제 이용압력 <span style="color:#F59E0B">●</span></div>', unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True, config={"displaylogo":False})
    means = [(g, sum(v for v in values[i:i+2] if v is not None) / len([v for v in values[i:i+2] if v is not None])) for g, i in zip(groups[::2], (0,2,4)) if any(v is not None for v in values[i:i+2])]
    if means:
        strongest = max(means, key=lambda x:x[1])
        st.caption(f"저장된 percentile에서 {strongest[0]}의 평균 상대위치가 {strongest[1]:.1f}로 세 그룹 중 가장 높습니다.")

def stability(row):
    classes = [str(row.get(f"candidate_type_p{p}", "—")).replace("A_PLUS", "A+") for p in (70,75,80)]
    return f"{sum(c == classes[1] for c in classes)}/3 동일 분류"


def label_point(geometry):
    """Interior point for display only, using an even-odd polygon scanline.

    Select the largest polygon, avoid vertex heights, then take the midpoint
    of the widest interior interval. Holes are included in the intersections.
    No geometry or analysis data is written or changed.
    """
    polygons = [geometry["coordinates"]] if geometry["type"] == "Polygon" else geometry["coordinates"]
    def area(ring):
        return abs(sum(a[0]*b[1] - b[0]*a[1] for a,b in zip(ring, ring[1:])))
    rings = max(polygons, key=lambda polygon: area(polygon[0]))
    levels = sorted({point[1] for ring in rings for point in ring})
    middle = (levels[0] + levels[-1]) / 2
    scans = sorted(((a+b)/2 for a,b in zip(levels,levels[1:])), key=lambda y: abs(y-middle))
    for lat in scans:
        crossings = sorted(a[0] + (lat-a[1])*(b[0]-a[0])/(b[1]-a[1])
                           for ring in rings for a,b in zip(ring,ring[1:])
                           if (a[1] > lat) != (b[1] > lat))
        intervals = list(zip(crossings[::2], crossings[1::2]))
        if intervals:
            left, right = max(intervals, key=lambda pair: pair[1]-pair[0])
            if right > left:
                return (left+right)/2, lat
    raise ValueError("후보 지도 라벨의 내부점을 찾을 수 없습니다.")


def add_priority_labels(fig, geo, frame):
    """Text-only layer; polygon colors and saved Tier remain untouched."""
    features = {feature["properties"]["ADM_CD"]:feature for feature in geo["features"]}
    positions = {"개포1동":"bottom right", "잠실4동":"top right", "신사동":"bottom left",
                 "고덕1동":"top right", "압구정동":"top left", "도봉1동":"top center", "화곡1동":"bottom left"}
    for tier in ("Tier 1", "Tier 2", "Tier 3"):
        group = frame.loc[frame.tier_label.eq(tier)]
        points = [label_point(features[code]["geometry"]) for code in group.dong_code]
        if not points:
            continue
        # Scattermap accepts one textposition per trace, so each name has its
        # own small text trace and independent anchor without moving polygons.
        for name, point in zip(group.dong_name, points):
            fig.add_trace(go.Scattermap(lon=[point[0]], lat=[point[1]],
                mode="text", text=[name], textposition=positions.get(name,"top center"),
                textfont={"family":FONT,"size":15 if tier == "Tier 1" else 13,"weight":700 if tier == "Tier 1" else 500,"color":"#102A43"},
                name=f"{tier} · {name}", showlegend=False, hoverinfo="skip"))
