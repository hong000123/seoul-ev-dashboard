# 서울시 EV 충전 수요–공급 분석 · 경량 배포본

이 폴더만 GitHub/Streamlit Cloud 배포에 사용합니다. 원본 프로젝트와 독립적으로 실행하며 모델 학습·분류·Tier·percentile을 재계산하지 않습니다.

## 실행
~~~powershell
Set-Location 'C:\EV_Dashboard_Deploy'
python -m pip install -r requirements.txt
python -m streamlit run dashboard\app.py --server.port 8502 --theme.base=light
~~~
이미 실행 중인 localhost:8502 서버가 있으면 별도로 중복 실행하지 않습니다.

GitHub에는 이 폴더를 저장소 루트로 올립니다. Streamlit 앱 진입 파일은 dashboard/app.py, 의존성 파일은 루트 requirements.txt입니다. 배경지도는 Plotly white-bg이므로 지도 API 키를 사용하지 않습니다.

## 필수 입력
- reference_data/seoul_dong_2025_2Q.geojson: 서울 행정동 426개, EPSG:4326, ADM_CD·ADM_NM·geometry.
- analysis_outputs/current_priority_409.csv
- analysis_outputs/coverage16_priority_sensitivity.csv
- analysis_outputs/final_primary_candidates.csv
- analysis_outputs/coverage_and_future_watchlist.csv
- analysis_outputs/dong_predictor_master.csv
- analysis_outputs/dong_current_demand_supply.csv

서울 GeoJSON은 전국 SGIS 2025년 2분기 경계(EPSG:5179)에서 기존 앱이 선택하던 ADM_CD가 11로 시작하는 동일한 426개를 좌표 변환한 결과입니다. 단순화·좌표 반올림·경계 수정은 하지 않았습니다. 행정동명 원본 필드는 ADM_NM이며 dong_code ↔ ADM_CD 조인은 유지합니다. 전국 SGIS 폴더는 검증 통과 후 이 배포본에서만 제거합니다.

## 페이지 및 보존 기준
연구 개요 / 수요–공급 지도 / 우선 검토지역 / EV +10% 시나리오 / 행정동 상세 조회의 5개 페이지를 유지합니다. 기본 p75, Primary409·Coverage16 구분, 최종 7개 후보와 Tier, 시나리오 전환값, 색상·UI는 기존 그대로입니다.

## 검증
~~~powershell
python -B dashboard\validate_dashboard.py
python -B dashboard\validate_ui.py
~~~
첫 명령은 구문·GeoJSON·분류·Tier·조인·입력 해시를 확인합니다. 두 번째는 서버를 띄우지 않는 Streamlit AppTest입니다. GeoJSON 로딩에는 GeoPandas/PyShp/PyProj가 필요 없습니다. 선택적 Shapely 설치 시 폴리곤 유효성 검사도 수행합니다.

캐시·로컬 검증 결과·환경 파일·secrets.toml은 Git에 포함하지 않습니다. 비밀정보는 공개 저장소에 올리지 않습니다.
