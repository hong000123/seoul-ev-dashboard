"""Shared presentation theme; no external assets or fonts."""
CLASS_COLORS = {"A+": "#B91C1C", "A": "#F59E0B", "B": "#EAB308", "C": "#0D9488", "D": "#A8C7C6", "OTHER": "#F1F4F6"}
CLASS_LABELS = {"A+":"강한 확장 검토", "A":"확장 검토", "B":"모델 압력 후보", "C":"운영 hotspot", "D":"수요·공급 상대 여유", "OTHER":"기타(이번 분류상 특이점 없음)"}
TIER_COLORS = {"Tier 1": "#2563EB", "Tier 2": "#60A5FA", "Tier 3": "#A5C8EB", "최종 Tier 대상 외": "#E2E8F0"}
FONT = 'Pretendard, "Noto Sans KR", "Malgun Gothic", Arial, sans-serif'
CSS = """
<style>
.stApp {background:#F8FAFC;color:#102A43;}
html, body, .stApp, .stApp input, .stApp button, .stApp select, .stApp textarea {
 font-family:Pretendard,"Noto Sans KR","Malgun Gothic",Arial,sans-serif;}
[data-testid="stHeader"] {background:transparent;height:2.5rem;}
[data-testid="stToolbar"], [data-testid="stAppDeployButton"], #MainMenu, footer {display:none!important;}
.block-container {padding:2.4rem 2.6rem 2rem;max-width:1850px;}
h1 {font-size:34px!important;font-weight:750!important;color:#102A43;letter-spacing:-.04em;}
h2 {font-size:24px!important;font-weight:700!important;color:#102A43;}
h3 {font-size:22px!important;color:#102A43;}
[data-testid="stCaptionContainer"] {color:#64748B;font-size:13px;}
[data-testid="stSidebar"] {background:#fff;border-right:1px solid #E2E8F0;}
.brand {font-size:23px;font-weight:800;letter-spacing:.08em;margin-bottom:4px;}
.brand-sub {font-size:13px;color:#64748B;margin-bottom:28px;}
[data-testid="stSidebar"] [role="radiogroup"] {gap:6px;}
[data-testid="stSidebar"] [role="radiogroup"] label {padding:10px 12px;border-radius:8px;border-left:3px solid transparent;}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {background:#EFF6FF;border-left-color:#2563EB;color:#2563EB;}
[data-testid="stSidebar"] [role="radiogroup"][aria-orientation="horizontal"] label {padding:6px 9px;}
[data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"] {border-radius:14px;}
[data-testid="stMetric"], .panel, .tiercard {background:white;border:1px solid #E2E8F0;border-radius:16px;box-shadow:0 2px 8px rgba(16,42,67,.025);padding:20px;}
[data-testid="stMetric"] {min-height:122px;}
[data-testid="stMetricLabel"] {color:#64748B;font-size:13px;}
[data-testid="stMetricValue"] {font-size:32px;font-weight:700;color:#102A43;}
.page-header {border-bottom:1px solid #E2E8F0;padding-bottom:20px;margin-bottom:24px;}
.page-header h1 {margin:0;padding:0;line-height:1.3;}
.subtitle {color:#64748B;font-size:16px;margin:10px 0 0;}
.tiercard {min-height:155px;border-top:4px solid #A5C8EB;}.tiercard.tier1 {background:#EFF6FF;border-color:#BFDBFE;border-top-color:#2563EB;}
.tiercard.tier2 {border-top-color:#60A5FA;}.tiercard small {display:block;color:#64748B;margin-top:10px;font-size:13px;}
.tiercard p {font-size:20px;margin:16px 0 0;line-height:1.5;}
.badge {display:inline-block;border-radius:99px;padding:4px 10px;font-size:12px;font-weight:600;margin:0 6px 6px 0;white-space:nowrap;}
.flow {display:flex;align-items:center;gap:12px;margin:24px 0;}
.flow-step {flex:1;background:#fff;border:1px solid #E2E8F0;border-radius:12px;padding:18px 12px;text-align:center;font-size:14px;}
.flow-step small {display:block;color:#2563EB;font-size:12px;margin-bottom:8px;}.flow-arrow {color:#94A3B8;}
.hero {background:#EFF6FF;border:1px solid #BFDBFE;border-radius:16px;padding:24px;margin-bottom:24px;}
.hero h2 {font-size:30px!important;margin:0 0 12px;}.hero p {color:#64748B;font-size:16px;}
.callout {background:#F1F5F9;color:#64748B;border-radius:12px;padding:16px 20px;font-size:14px;margin:16px 0;}
.legend {display:flex;flex-wrap:wrap;gap:8px 18px;font-size:13px;margin:0 0 16px;}.legend i {display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:6px;}
.legend small {color:#64748B;font-size:11px;}.legend .outline-dot {background:transparent!important;border:2px solid #B45309;}
.message-banner {background:#EFF6FF;border-left:4px solid #2563EB;border-radius:12px;padding:16px 20px;margin:16px 0;color:#102A43;font-size:16px;line-height:1.65;}
.reason-card {background:#FFF;border:1px solid #E2E8F0;border-left:4px solid #2563EB;border-radius:16px;padding:20px;margin:12px 0 24px;}
.reason-card p {margin:8px 0 0;line-height:1.7;font-size:15px;color:#475569;}
.badge.active {background:#FFF1D6;color:#92400E;}.badge.inactive {background:#F1F5F9;color:#64748B;}
.group-key {color:#64748B;font-size:13px;margin-bottom:4px;}
.research-table {border-collapse:collapse;width:100%;font-size:14px;margin:8px 0 20px;}
.research-table th {background:#F1F5F9;color:#64748B;font-size:13px;font-weight:600;}
.research-table td,.research-table th {padding:10px 14px;text-align:left;border-bottom:1px solid #F1F5F9;}
.research-table tbody tr:nth-child(even) {background:#FAFCFE;}.research-table .numeric {text-align:right;font-variant-numeric:tabular-nums;}
@media(max-width:900px) {.block-container {padding:2rem 1rem;}.flow {flex-wrap:wrap;}.flow-step {min-width:130px;}h1 {font-size:30px!important;}}
</style>
"""
