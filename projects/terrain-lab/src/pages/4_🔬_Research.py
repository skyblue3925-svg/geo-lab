"""
🔬 Research Lab: 연구용 지형 분석 도구

대학 연구자를 위한 고급 분석 기능:
- DEM 업로드 (드론 측량 데이터)
- 종/횡단면 프로파일
- Hypsometric Curve
- 사면 경사 분석
- 데이터 내보내기
"""
import streamlit as st
import numpy as np
import json
import sys
import os
from app.utils.plotly_compat import go, px, plotly_error_message

if go is None or px is None:
    st.error(plotly_error_message())
    st.stop()

# 상위 디렉토리 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.analysis import (
    extract_profile, extract_cross_section, extract_longitudinal,
    calculate_hypsometric_curve, calculate_slope_distribution,
    calculate_relief_ratio, calculate_curvature, compare_elevations
)
from engine.dem_io import (
    load_dem_csv, load_dem_npy, load_dem_asc,
    export_to_bytes_csv, export_to_bytes_npy,
    get_dem_statistics
)
from engine.ideal_landforms import IDEAL_LANDFORM_GENERATORS
from app.components.renderer import render_terrain_plotly
from app.services.dem_research import (
    DEM_LAYER_LABELS,
    analyze_dem_surface,
    dem_research_cards,
    normalize_dem_layer,
    process_hints_from_dem,
)
from app.utils.mode_helpers import build_export_provenance, build_provenance_panel, get_research_context
from app.utils.research_compare import (
    align_reference_dem,
    build_research_comparison_summary,
    build_research_comparison_report,
    compute_profile_error_stats,
    export_comparison_report_json_bytes,
    export_comparison_report_markdown_bytes,
    export_profile_comparison_csv_bytes,
)

# ========== Page Config (무조건 첫 번째!) ==========
st.set_page_config(page_title="🔬 Research Lab", page_icon="🔬", layout="wide")

# ========== CSS 로드 ==========
def load_css():
    css_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "style.css")
    if os.path.exists(css_path):
        with open(css_path, 'r', encoding='utf-8') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

load_css()


def load_uploaded_dem_file(uploaded_file):
    filename = uploaded_file.name.lower()
    metadata = {}

    if filename.endswith('.npy'):
        elevation = load_dem_npy(uploaded_file.read())
    elif filename.endswith('.asc'):
        content = uploaded_file.read().decode('utf-8')
        elevation, metadata = load_dem_asc(content)
    else:
        content = uploaded_file.read().decode('utf-8')
        elevation = load_dem_csv(content)

    return elevation, metadata


# ========== 헤더 ==========
st.markdown("""
<div style='margin-bottom: 1.5rem;'>
    <h1 style='font-size: 2.2rem; font-weight: 700; margin-bottom: 0.25rem;'>🔬 Research Lab</h1>
    <p style='color: #86868b; font-size: 1rem;'>대학 연구자를 위한 고급 지형 분석 도구</p>
</div>
""", unsafe_allow_html=True)

# 세션 상태 초기화
if 'research_elevation' not in st.session_state:
    st.session_state['research_elevation'] = None
if 'research_params' not in st.session_state:
    st.session_state['research_params'] = {}

# ==========================================
# 사이드바: 데이터 소스 선택
# ==========================================
st.sidebar.subheader("📁 데이터 소스")

data_source = st.sidebar.radio(
    "데이터 선택",
    ["🧪 시뮬레이션 생성", "📤 DEM 업로드"],
    key="data_source"
)

elevation = None
params = {}

if data_source == "🧪 시뮬레이션 생성":
    st.sidebar.markdown("---")
    
    # 지형 선택
    landform_options = list(IDEAL_LANDFORM_GENERATORS.keys())
    selected_landform = st.sidebar.selectbox("지형 선택", landform_options)
    
    grid_size = st.sidebar.slider("그리드 크기", 50, 200, 100, key="sim_grid")
    stage = st.sidebar.slider("형성 단계", 0.0, 1.0, 1.0, 0.05, key="sim_stage")
    cell_size = st.sidebar.number_input("셀 크기 (m)", 1.0, 100.0, 10.0, key="cell_size")
    
    if st.sidebar.button("🔄 지형 생성", type="primary"):
        try:
            landform_func = IDEAL_LANDFORM_GENERATORS[selected_landform]
            import inspect
            sig = inspect.signature(landform_func)
            params = list(sig.parameters.keys())
            
            if 'stage' in params:
                result = landform_func(grid_size, stage)
            else:
                result = landform_func(grid_size)
            
            if isinstance(result, tuple):
                elevation = result[0]
            else:
                elevation = result
            
            st.session_state['research_elevation'] = elevation
            st.session_state['research_params'] = {
                'landform': selected_landform,
                'grid_size': grid_size,
                'stage': stage,
                'cell_size': cell_size,
                'source': 'simulation'
            }
            st.sidebar.success(f"✅ {selected_landform} 생성 완료!")
        except Exception as e:
            st.sidebar.error(f"오류: {e}")

else:  # DEM 업로드
    st.sidebar.markdown("---")
    st.sidebar.markdown("""
    **지원 포맷:**
    - CSV (쉼표 구분)
    - NumPy (.npy)
    - ESRI ASCII Grid (.asc)
    """)
    
    uploaded_file = st.sidebar.file_uploader(
        "DEM 파일 업로드",
        type=['csv', 'npy', 'asc', 'txt'],
        key="dem_upload"
    )
    
    cell_size = st.sidebar.number_input("셀 크기 (m)", 1.0, 100.0, 10.0, key="upload_cell_size")

    if uploaded_file is not None:
        try:
            elevation, metadata = load_uploaded_dem_file(uploaded_file)
            cell_size = metadata.get('cellsize', cell_size)

            st.session_state['research_elevation'] = elevation
            st.session_state['research_params'] = {
                'filename': uploaded_file.name,
                'shape': elevation.shape,
                'cell_size': cell_size,
                'source': 'upload'
            }
            st.sidebar.success(f"✅ DEM 로드 완료! ({elevation.shape})")
        except Exception as e:
            st.sidebar.error(f"파일 로드 오류: {e}")

# 현재 로드된 데이터 사용
if st.session_state['research_elevation'] is not None:
    elevation = st.session_state['research_elevation']
    params = st.session_state['research_params']
    cell_size = params.get('cell_size', 10.0)

# ==========================================
# 메인 콘텐츠
# ==========================================
if elevation is None:
    st.info("👈 왼쪽 사이드바에서 데이터를 생성하거나 업로드하세요.")
    st.stop()

if params.get("source") == "case_mode":
    case_title = params.get("case_title", "케이스 모드")
    case_id = params.get("case_id", "")
    anchor = params.get("anchor", "")
    baseline_label = params.get("baseline_label", "")
    intervention_label = params.get("intervention_label", "")
    st.info(
        "케이스 모드 데이터셋이 로드되었습니다.\n\n"
        f"사례: {case_title} ({case_id})\n\n"
        f"실제 앵커: {anchor}\n\n"
        f"A/B 프레이밍: A={baseline_label} | B={intervention_label}"
    )

# 탭 구성
research_context = get_research_context(params)
st.markdown(
    build_provenance_panel(
        research_context["title"],
        research_context["summary"],
        research_context["badges"],
        research_context["notes"],
    ),
    unsafe_allow_html=True,
)

comparison_summary = st.session_state.get('research_comparison_summary')
comparison_profile_csv = st.session_state.get('research_comparison_profile_csv')
comparison_report = st.session_state.get('research_comparison_report')

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "3D View",
    "Profile",
    "Hypsometric",
    "Slope",
    "DEM Compare",
    "Lab DEM 진단",
    "Export",
])

# ==========================================
# Tab 1: 3D 뷰
# ==========================================
with tab1:
    st.subheader("🗺️ 3D 지형 뷰")
    
    # 기본 통계
    stats = get_dem_statistics(elevation)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("최저 고도", f"{stats['min']:.1f}m")
    col2.metric("최고 고도", f"{stats['max']:.1f}m")
    col3.metric("기복량", f"{stats['range']:.1f}m")
    col4.metric("평균 고도", f"{stats['mean']:.1f}m")
    
    # 3D 렌더링
    fig = render_terrain_plotly(
        elevation,
        params.get('landform', 'DEM'),
        add_water=True,
        water_level=-999,
        force_camera=False
    )
    st.plotly_chart(fig, width="stretch")
    
    # Relief Ratio
    rr = calculate_relief_ratio(elevation)
    st.markdown(f"**기복비 (Relief Ratio):** {rr:.4f}")

# ==========================================
# Tab 2: 프로파일 분석
# ==========================================
with tab2:
    st.subheader("📊 종/횡단면 프로파일")
    
    h, w = elevation.shape
    
    profile_type = st.radio("프로파일 유형", ["횡단면 (E-W)", "종단면 (N-S)", "사용자 정의"], horizontal=True)
    
    if profile_type == "횡단면 (E-W)":
        row = st.slider("행 위치 (N-S)", 0, h-1, h//2, key="cross_row")
        profile = extract_cross_section(elevation, row, cell_size)
        title = f"횡단면 (Row {row})"
        
    elif profile_type == "종단면 (N-S)":
        col = st.slider("열 위치 (E-W)", 0, w-1, w//2, key="long_col")
        profile = extract_longitudinal(elevation, col, cell_size)
        title = f"종단면 (Col {col})"
        
    else:  # 사용자 정의
        st.markdown("시작점과 끝점을 지정하세요:")
        col1, col2 = st.columns(2)
        with col1:
            start_row = st.number_input("시작 Row", 0, h-1, 0)
            start_col = st.number_input("시작 Col", 0, w-1, 0)
        with col2:
            end_row = st.number_input("끝 Row", 0, h-1, h-1)
            end_col = st.number_input("끝 Col", 0, w-1, w-1)
        
        profile = extract_profile(
            elevation, (start_row, start_col), (end_row, end_col),
            num_samples=100, cell_size=cell_size
        )
        title = f"프로파일 ({start_row},{start_col}) → ({end_row},{end_col})"
    
    # 프로파일 그래프
    fig_profile = go.Figure()
    
    fig_profile.add_trace(go.Scatter(
        x=profile.distance,
        y=profile.elevation,
        mode='lines',
        name='고도',
        line=dict(color='brown', width=2)
    ))
    
    fig_profile.update_layout(
        title=title,
        xaxis_title="거리 (m)",
        yaxis_title="고도 (m)",
        height=400,
        template='plotly_dark'
    )
    st.plotly_chart(fig_profile, width="stretch")
    
    # 경사도 그래프
    with st.expander("📐 경사도 프로파일"):
        fig_slope = go.Figure()
        fig_slope.add_trace(go.Scatter(
            x=profile.distance,
            y=profile.slope,
            mode='lines',
            name='경사도',
            line=dict(color='orange', width=2)
        ))
        fig_slope.update_layout(
            title="경사도 변화",
            xaxis_title="거리 (m)",
            yaxis_title="경사도 (°)",
            height=300,
            template='plotly_dark'
        )
        st.plotly_chart(fig_slope, width="stretch")
    
    # 프로파일 위치 표시 (2D)
    with st.expander("🗺️ 프로파일 위치"):
        fig_loc = go.Figure()
        fig_loc.add_trace(go.Heatmap(z=elevation, colorscale='Viridis'))
        
        # 프로파일 라인
        points = profile.points
        fig_loc.add_trace(go.Scatter(
            x=[p[1] for p in points],
            y=[p[0] for p in points],
            mode='lines',
            line=dict(color='red', width=3),
            name='프로파일'
        ))
        
        fig_loc.update_layout(
            title="프로파일 위치",
            height=400,
            template='plotly_dark',
            yaxis=dict(scaleanchor="x", scaleratio=1)
        )
        st.plotly_chart(fig_loc, width="stretch")

# ==========================================
# Tab 3: Hypsometric Curve
# ==========================================
with tab3:
    st.subheader("📈 Hypsometric Curve (고도-면적 곡선)")
    
    st.markdown("""
    **해석:**
    - **HI > 0.6**: 유년기 (Young) - 침식 초기, 융기 우세
    - **0.35 < HI < 0.6**: 장년기 (Mature) - 평형 상태
    - **HI < 0.35**: 노년기 (Old) - 침식 후기, 준평원화
    """)
    
    hypso = calculate_hypsometric_curve(elevation)
    
    # 결과 표시
    col1, col2 = st.columns(2)
    col1.metric("Hypsometric Integral (HI)", f"{hypso.hypsometric_integral:.3f}")
    col2.metric("침식 단계", hypso.stage)
    
    # Hypsometric Curve 그래프
    fig_hypso = go.Figure()
    
    fig_hypso.add_trace(go.Scatter(
        x=hypso.relative_area,
        y=hypso.relative_elevation,
        mode='lines',
        name='Hypsometric Curve',
        line=dict(color='blue', width=3),
        fill='tozeroy',
        fillcolor='rgba(0, 100, 255, 0.3)'
    ))
    
    # 대각선 (이론적 평형)
    fig_hypso.add_trace(go.Scatter(
        x=[0, 1],
        y=[1, 0],
        mode='lines',
        name='평형선',
        line=dict(color='gray', dash='dash')
    ))
    
    fig_hypso.update_layout(
        title=f"Hypsometric Curve (HI = {hypso.hypsometric_integral:.3f})",
        xaxis_title="상대 면적 (a/A)",
        yaxis_title="상대 고도 (h/H)",
        height=500,
        template='plotly_dark',
        xaxis=dict(range=[0, 1]),
        yaxis=dict(range=[0, 1])
    )
    st.plotly_chart(fig_hypso, width="stretch")
    
    # 해석
    st.info(f"""
    **분석 결과:**
    - Hypsometric Integral = {hypso.hypsometric_integral:.3f}
    - 침식 단계: {hypso.stage}
    - {"지형이 아직 많이 침식되지 않았습니다." if hypso.hypsometric_integral > 0.5 else "지형이 상당히 침식되었습니다."}
    """)

# ==========================================
# Tab 4: 경사 분석
# ==========================================
with tab4:
    st.subheader("⛰️ 사면 경사 분석")
    
    slope_result = calculate_slope_distribution(elevation, cell_size)
    slope_stats = slope_result['statistics']
    
    # 통계
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("평균 경사", f"{slope_stats['mean']:.1f}°")
    col2.metric("최대 경사", f"{slope_stats['max']:.1f}°")
    col3.metric("표준편차", f"{slope_stats['std']:.1f}°")
    col4.metric("중앙값", f"{slope_stats['median']:.1f}°")
    
    # 경사도 맵
    fig_slope_map = go.Figure()
    fig_slope_map.add_trace(go.Heatmap(
        z=slope_result['slope_grid'],
        colorscale='YlOrRd',
        colorbar=dict(title='경사도 (°)')
    ))
    fig_slope_map.update_layout(
        title="경사도 분포",
        height=400,
        template='plotly_dark',
        yaxis=dict(scaleanchor="x", scaleratio=1)
    )
    st.plotly_chart(fig_slope_map, width="stretch")
    
    # 히스토그램
    hist = slope_result['histogram']
    fig_hist = go.Figure()
    fig_hist.add_trace(go.Bar(
        x=hist['bin_centers'],
        y=hist['counts'],
        marker_color='orange'
    ))
    fig_hist.update_layout(
        title="경사도 히스토그램",
        xaxis_title="경사도 (°)",
        yaxis_title="셀 수",
        height=350,
        template='plotly_dark'
    )
    st.plotly_chart(fig_hist, width="stretch")
    
    # 곡률 분석
    with st.expander("🔄 곡률 (Curvature) 분석"):
        curvature = calculate_curvature(elevation, cell_size)
        
        curv_type = st.selectbox("곡률 유형", ["Profile (경사방향)", "Plan (등고선방향)", "Total"])
        curv_map = curvature[curv_type.split()[0].lower()]
        
        fig_curv = go.Figure()
        fig_curv.add_trace(go.Heatmap(
            z=curv_map,
            colorscale='RdBu',
            zmid=0,
            colorbar=dict(title='곡률')
        ))
        fig_curv.update_layout(
            title=f"{curv_type} Curvature",
            height=400,
            template='plotly_dark',
            yaxis=dict(scaleanchor="x", scaleratio=1)
        )
        st.plotly_chart(fig_curv, width="stretch")
        
        st.markdown("**해석:** 양수(빨강) = 볼록, 음수(파랑) = 오목")

# ==========================================
# Tab 5: 데이터 내보내기
# ==========================================
# ==========================================
# Tab 5: DEM Comparison
# ==========================================
with tab5:
    st.subheader("DEM 비교 / 검증")
    st.caption("현재 DEM과 기준 DEM을 나란히 비교해 오차, 단면 오차, HI 차이를 함께 확인합니다.")

    control_col1, control_col2 = st.columns(2)
    with control_col1:
        compare_cross_row = st.slider(
            "횡단면 비교 행",
            0,
            elevation.shape[0] - 1,
            elevation.shape[0] // 2,
            key='research_compare_row',
        )
    with control_col2:
        compare_long_col = st.slider(
            "종단면 비교 열",
            0,
            elevation.shape[1] - 1,
            elevation.shape[1] // 2,
            key='research_compare_col',
        )

    compare_upload = st.file_uploader(
        "비교할 기준 DEM 업로드",
        type=['csv', 'npy', 'asc', 'txt'],
        key='research_compare_upload',
    )

    if compare_upload is not None:
        try:
            reference_elevation_raw, reference_meta = load_uploaded_dem_file(compare_upload)
            reference_cell_size = reference_meta.get('cellsize', cell_size)
            reference_elevation = align_reference_dem(elevation, reference_elevation_raw)

            if elevation.shape != reference_elevation_raw.shape:
                st.warning("현재 DEM과 기준 DEM의 격자 크기가 달라 shape 기준 bilinear 보간 후 비교합니다. extent/CRS 정합은 자동 처리하지 않습니다.")
            if abs(reference_cell_size - cell_size) > 1e-9:
                st.info(f"기준 DEM 셀 크기: {reference_cell_size:g}m | 현재 DEM 셀 크기: {cell_size:g}m | 셀 크기 차이는 해석 시 함께 고려하세요.")

            comparison = compare_elevations(
                elevation,
                reference_elevation,
                label1='Current DEM',
                label2=compare_upload.name,
            )
            stats_cmp = comparison['statistics']

            current_hypso = calculate_hypsometric_curve(elevation)
            reference_hypso = calculate_hypsometric_curve(reference_elevation)

            cross_current = extract_cross_section(elevation, compare_cross_row, cell_size)
            cross_reference = extract_cross_section(reference_elevation, compare_cross_row, cell_size)
            long_current = extract_longitudinal(elevation, compare_long_col, cell_size)
            long_reference = extract_longitudinal(reference_elevation, compare_long_col, cell_size)
            cross_stats = compute_profile_error_stats(cross_current, cross_reference)
            long_stats = compute_profile_error_stats(long_current, long_reference)
            cross_error = cross_stats['error']
            long_error = long_stats['error']
            cross_rmse = cross_stats['rmse']
            long_rmse = long_stats['rmse']
            cross_mae = cross_stats['mae']
            long_mae = long_stats['mae']
            cross_peak_error = cross_stats['peak_abs_error']
            long_peak_error = long_stats['peak_abs_error']

            comparison_summary = build_research_comparison_summary(
                reference_name=compare_upload.name,
                reference_shape=reference_elevation_raw.shape,
                reference_cell_size=reference_cell_size,
                stats_cmp=stats_cmp,
                current_hypso=current_hypso,
                reference_hypso=reference_hypso,
                cross_stats=cross_stats,
                long_stats=long_stats,
                compare_cross_row=compare_cross_row,
                compare_long_col=compare_long_col,
            )
            comparison_report = build_research_comparison_report(
                summary=comparison_summary,
                stats_cmp=stats_cmp,
                current_hypso=current_hypso,
                reference_hypso=reference_hypso,
                cross_stats=cross_stats,
                long_stats=long_stats,
                current_shape=elevation.shape,
                current_cell_size=cell_size,
                reference_shape=reference_elevation_raw.shape,
                reference_cell_size=reference_cell_size,
            )
            hi_diff = comparison_summary['hi_diff']
            hi_message = comparison_summary['hi_message']
            comparison_profile_csv = export_profile_comparison_csv_bytes(
                cross_current=cross_current,
                cross_reference=cross_reference,
                cross_error=cross_error,
                long_current=long_current,
                long_reference=long_reference,
                long_error=long_error,
            )
            st.session_state['research_comparison_summary'] = comparison_summary
            st.session_state['research_comparison_profile_csv'] = comparison_profile_csv
            st.session_state['research_comparison_report'] = comparison_report

            st.caption(f"비교 단면: 횡단면 row {compare_cross_row}, 종단면 col {compare_long_col}")
            st.caption("비교 결과는 동일 좌표계 정합이 끝난 정밀 매칭이 아니라, 현재는 shape 기준 내부 보간 비교입니다.")
            cmp_col1, cmp_col2, cmp_col3, cmp_col4 = st.columns(4)
            cmp_col1.metric('RMSE', f"{stats_cmp['rmse']:.3f}")
            cmp_col2.metric('MAE', f"{stats_cmp['mae']:.3f}")
            cmp_col3.metric('상관계수', f"{stats_cmp['correlation']:.3f}")
            cmp_col4.metric('평균 차이', f"{stats_cmp['mean_diff']:+.3f}")

            cmp_col5, cmp_col6, cmp_col7, cmp_col8 = st.columns(4)
            cmp_col5.metric('정규화 RMSE', f"{stats_cmp['normalized_rmse']:.3f}")
            cmp_col6.metric('유효 비교율', f"{stats_cmp['valid_ratio']*100:.1f}%")
            cmp_col7.metric('현재 기복량', f"{stats_cmp['current_range']:.3f} m")
            cmp_col8.metric('기준 기복량', f"{stats_cmp['reference_range']:.3f} m")

            st.markdown("#### 단면 해석")
            profile_summary_col1, profile_summary_col2 = st.columns(2)
            with profile_summary_col1:
                st.metric('횡단면 RMSE', f"{cross_rmse:.3f}")
                st.metric('횡단면 MAE', f"{cross_mae:.3f}")
                st.metric('횡단면 최대 절대 오차', f"{cross_peak_error:.3f} m")
            with profile_summary_col2:
                st.metric('종단면 RMSE', f"{long_rmse:.3f}")
                st.metric('종단면 MAE', f"{long_mae:.3f}")
                st.metric('종단면 최대 절대 오차', f"{long_peak_error:.3f} m")

            if stats_cmp['normalized_rmse'] < 0.05 and stats_cmp['correlation'] >= 0.9:
                st.success("전반적 형상은 매우 유사합니다. 차이 맵과 단면 오차에서 국지적 변화를 확인하세요.")
            elif stats_cmp['normalized_rmse'] < 0.15:
                st.info("전체 구조는 비슷하지만, 단면 오차와 HI 차이에서 확인해야 할 구간이 있습니다.")
            else:
                st.warning("구조 차이가 뚜렷합니다. 차이 맵과 비교 단면을 우선 검토하세요.")

            st.markdown("#### \ube60\ub978 \ud574\uc11d \uc694\uc57d")
            for brief_line in comparison_summary.get('brief', []):
                st.markdown(f"- {brief_line}")

            fig_diff = go.Figure()
            fig_diff.add_trace(go.Heatmap(
                z=comparison['difference_grid'],
                colorscale='RdBu',
                zmid=0,
                colorbar=dict(title='고도 차이')
            ))
            fig_diff.update_layout(
                title=f"차이 맵: 현재 DEM - {compare_upload.name}",
                height=420,
                template='plotly_dark',
                yaxis=dict(scaleanchor='x', scaleratio=1),
            )
            st.plotly_chart(fig_diff, width="stretch")

            fig_error_hist = go.Figure()
            fig_error_hist.add_trace(go.Histogram(
                x=comparison['difference_grid'].ravel(),
                nbinsx=40,
                marker_color='#0f766e',
                opacity=0.85,
            ))
            fig_error_hist.update_layout(
                title='고도 차이 분포',
                xaxis_title='고도 차이',
                yaxis_title='셀 수',
                height=320,
                template='plotly_dark',
            )
            st.plotly_chart(fig_error_hist, width="stretch")

            profile_col1, profile_col2 = st.columns(2)
            with profile_col1:
                fig_cross = go.Figure()
                fig_cross.add_trace(go.Scatter(
                    x=cross_current.distance,
                    y=cross_current.elevation,
                    mode='lines',
                    name='현재 DEM',
                    line=dict(color='#2563eb', width=3),
                ))
                fig_cross.add_trace(go.Scatter(
                    x=cross_reference.distance,
                    y=cross_reference.elevation,
                    mode='lines',
                    name='기준 DEM',
                    line=dict(color='#f97316', width=3, dash='dash'),
                ))
                fig_cross.update_layout(
                    title='횡단면 비교',
                    xaxis_title='거리 (m)',
                    yaxis_title='고도 (m)',
                    height=340,
                    template='plotly_dark',
                )
                st.plotly_chart(fig_cross, width="stretch")
                st.caption(f"횡단면 최대 절대 오차: {cross_peak_error:.3f} m")

            with profile_col2:
                fig_long = go.Figure()
                fig_long.add_trace(go.Scatter(
                    x=long_current.distance,
                    y=long_current.elevation,
                    mode='lines',
                    name='현재 DEM',
                    line=dict(color='#059669', width=3),
                ))
                fig_long.add_trace(go.Scatter(
                    x=long_reference.distance,
                    y=long_reference.elevation,
                    mode='lines',
                    name='기준 DEM',
                    line=dict(color='#e11d48', width=3, dash='dash'),
                ))
                fig_long.update_layout(
                    title='종단면 비교',
                    xaxis_title='거리 (m)',
                    yaxis_title='고도 (m)',
                    height=340,
                    template='plotly_dark',
                )
                st.plotly_chart(fig_long, width="stretch")
                st.caption(f"종단면 최대 절대 오차: {long_peak_error:.3f} m")

            error_col1, error_col2 = st.columns(2)
            with error_col1:
                fig_cross_error = go.Figure()
                fig_cross_error.add_trace(go.Scatter(
                    x=[float(cross_current.distance[0]), float(cross_current.distance[-1])],
                    y=[0.0, 0.0],
                    mode='lines',
                    name='기준선',
                    line=dict(color='#94a3b8', width=1.5, dash='dash'),
                ))
                fig_cross_error.add_trace(go.Scatter(
                    x=cross_current.distance,
                    y=cross_error,
                    mode='lines',
                    name='오차 (현재-기준)',
                    line=dict(color='#f59e0b', width=3),
                    fill='tozeroy',
                    fillcolor='rgba(245, 158, 11, 0.22)',
                ))
                fig_cross_error.update_layout(
                    title='횡단면 오차 프로파일',
                    xaxis_title='거리 (m)',
                    yaxis_title='고도 차이 (m)',
                    height=320,
                    template='plotly_dark',
                )
                st.plotly_chart(fig_cross_error, width="stretch")

            with error_col2:
                fig_long_error = go.Figure()
                fig_long_error.add_trace(go.Scatter(
                    x=[float(long_current.distance[0]), float(long_current.distance[-1])],
                    y=[0.0, 0.0],
                    mode='lines',
                    name='기준선',
                    line=dict(color='#94a3b8', width=1.5, dash='dash'),
                ))
                fig_long_error.add_trace(go.Scatter(
                    x=long_current.distance,
                    y=long_error,
                    mode='lines',
                    name='오차 (현재-기준)',
                    line=dict(color='#22c55e', width=3),
                    fill='tozeroy',
                    fillcolor='rgba(34, 197, 94, 0.20)',
                ))
                fig_long_error.update_layout(
                    title='종단면 오차 프로파일',
                    xaxis_title='거리 (m)',
                    yaxis_title='고도 차이 (m)',
                    height=320,
                    template='plotly_dark',
                )
                st.plotly_chart(fig_long_error, width="stretch")

            fig_hypso_compare = go.Figure()
            fig_hypso_compare.add_trace(go.Scatter(
                x=current_hypso.relative_area,
                y=current_hypso.relative_elevation,
                mode='lines',
                name=f"현재 DEM (HI={current_hypso.hypsometric_integral:.3f})",
                line=dict(color='#2563eb', width=3),
            ))
            fig_hypso_compare.add_trace(go.Scatter(
                x=reference_hypso.relative_area,
                y=reference_hypso.relative_elevation,
                mode='lines',
                name=f"기준 DEM (HI={reference_hypso.hypsometric_integral:.3f})",
                line=dict(color='#f97316', width=3, dash='dash'),
            ))
            fig_hypso_compare.update_layout(
                title='Hypsometric Curve 비교',
                xaxis_title='상대 면적 (a/A)',
                yaxis_title='상대 고도 (h/H)',
                height=360,
                template='plotly_dark',
                xaxis=dict(range=[0, 1]),
                yaxis=dict(range=[0, 1]),
            )
            st.plotly_chart(fig_hypso_compare, width="stretch")
            st.info(f"HI 해석: {hi_message}")
        except Exception as e:
            st.error(f"DEM 비교 실패: {e}")
    elif comparison_summary:
        st.info(f"마지막 비교 기준: {comparison_summary['reference_name']}")
    else:
        st.info("기준 DEM을 업로드하면 RMSE, MAE, 단면 오차, HI 차이와 차이 맵을 바로 확인할 수 있습니다.")

with tab6:
    st.subheader("Lab 물리모델 입력 진단")
    st.caption("현재 DEM을 Lab의 초기 지형으로 넘기기 전에 경사, 곡률, 배수 집중을 빠르게 확인합니다.")

    dem_analysis = analyze_dem_surface(elevation)
    card_cols = st.columns(4)
    for card_col, (label, value, help_text) in zip(card_cols, dem_research_cards(dem_analysis), strict=False):
        card_col.metric(label, value, help=help_text)

    layer_key = st.selectbox(
        "진단 레이어",
        list(DEM_LAYER_LABELS.keys()),
        format_func=lambda key: DEM_LAYER_LABELS[key],
        key="research_lab_dem_layer",
    )
    layer = normalize_dem_layer(dem_analysis, layer_key)

    fig_lab_dem = go.Figure()
    fig_lab_dem.add_trace(
        go.Heatmap(
            z=layer,
            colorscale="Viridis",
            colorbar={"title": DEM_LAYER_LABELS[layer_key]},
            zmin=0,
            zmax=1,
        )
    )
    fig_lab_dem.update_layout(
        title=f"{DEM_LAYER_LABELS[layer_key]} 정규화 지도",
        height=440,
        template="plotly_dark",
        xaxis_title="X grid",
        yaxis_title="Y grid",
        yaxis_autorange="reversed",
    )
    st.plotly_chart(fig_lab_dem, width="stretch")

    st.markdown("#### 형성과정 후보 해석")
    for hint in process_hints_from_dem(dem_analysis):
        st.write(f"- {hint}")
    st.info("다음 단계에서는 이 진단값을 Lab 엔진의 초기 표면, 물 공급, 침식 강도, 퇴적 조건 추정값으로 연결합니다.")

with tab7:
    st.subheader("\ub370\uc774\ud130 \ub0b4\ubcf4\ub0b4\uae30")

    st.markdown("""
    **포맷 설명:**
    - **CSV**: Excel, QGIS, R, MATLAB 등에서 사용
    - **NumPy (.npy)**: Python 분석용, 빠른 저장/로드
    - **ASC**: ESRI ArcGIS 호환 포맷
    """)

    col1, col2, col3 = st.columns(3)

    with col1:
        csv_bytes = export_to_bytes_csv(elevation)
        st.download_button(
            label="CSV \ub2e4\uc6b4\ub85c\ub4dc",
            data=csv_bytes,
            file_name="elevation.csv",
            mime="text/csv"
        )

    with col2:
        npy_bytes = export_to_bytes_npy(elevation)
        st.download_button(
            label="NumPy \ub2e4\uc6b4\ub85c\ub4dc",
            data=npy_bytes,
            file_name="elevation.npy",
            mime="application/octet-stream"
        )

    with col3:
        from io import StringIO

        asc_buffer = StringIO()
        h, w = elevation.shape
        asc_buffer.write(f"ncols {w}\n")
        asc_buffer.write(f"nrows {h}\n")
        asc_buffer.write("xllcorner 0\n")
        asc_buffer.write("yllcorner 0\n")
        asc_buffer.write(f"cellsize {cell_size}\n")
        asc_buffer.write("nodata_value -9999\n")
        for row in elevation:
            asc_buffer.write(' '.join(f'{x:.4f}' for x in row) + '\n')

        st.download_button(
            label="ASC \ub2e4\uc6b4\ub85c\ub4dc",
            data=asc_buffer.getvalue(),
            file_name="elevation.asc",
            mime="text/plain"
        )

    st.markdown("---")

    from datetime import datetime

    if comparison_summary:
        st.subheader("\ube44\uad50 \uacb0\uacfc \ub0b4\ubcf4\ub0b4\uae30")
        export_col1, export_col2 = st.columns(2)

        with export_col1:
            comparison_json = export_comparison_report_json_bytes(
                comparison_report or {
                    "summary": comparison_summary,
                    "metrics": {},
                    "interpretation": comparison_summary.get("brief", []),
                    "sections": {},
                    "hypsometric": {
                        "current": comparison_summary.get("hi_current", 0.0),
                        "reference": comparison_summary.get("hi_reference", 0.0),
                        "difference": comparison_summary.get("hi_diff", 0.0),
                        "message": comparison_summary.get("hi_message", ""),
                    },
                    "context": {},
                }
            )
            st.download_button(
                label="\ube44\uad50 \ub9ac\ud3ec\ud2b8 JSON \ub2e4\uc6b4\ub85c\ub4dc",
                data=comparison_json,
                file_name="comparison_report.json",
                mime="application/json"
            )

        with export_col2:
            comparison_markdown = export_comparison_report_markdown_bytes(
                comparison_report or {
                    "summary": comparison_summary,
                    "metrics": {},
                    "interpretation": comparison_summary.get("brief", []),
                    "sections": {},
                    "hypsometric": {
                        "current": comparison_summary.get("hi_current", 0.0),
                        "reference": comparison_summary.get("hi_reference", 0.0),
                        "difference": comparison_summary.get("hi_diff", 0.0),
                        "message": comparison_summary.get("hi_message", ""),
                    },
                    "context": {},
                }
            )
            st.download_button(
                label="\ube44\uad50 \ub9ac\ud3ec\ud2b8 MD \ub2e4\uc6b4\ub85c\ub4dc",
                data=comparison_markdown,
                file_name="comparison_report.md",
                mime="text/markdown"
            )

        if comparison_profile_csv:
            st.download_button(
                label="\ub2e8\uba74 \ube44\uad50 CSV \ub2e4\uc6b4\ub85c\ub4dc",
                data=comparison_profile_csv,
                file_name="comparison_profiles.csv",
                mime="text/csv"
            )

        if comparison_report:
            st.caption("리포트 JSON/MD에는 개요, 해석 요약, 단면 지표, HI 차이, 비교 문맥이 함께 들어갑니다.")
        elif comparison_profile_csv:
            st.caption("단면 CSV에는 횡단면과 종단면의 거리별 오차가 들어갑니다.")
        st.markdown("---")

    st.subheader("\ud30c\ub77c\ubbf8\ud130 \uae30\ub85d (\uc7ac\ud604\uc131)")

    export_params = {
        **params,
        'statistics': get_dem_statistics(elevation),
        'hypsometric_integral': calculate_hypsometric_curve(elevation).hypsometric_integral,
        'relief_ratio': calculate_relief_ratio(elevation),
        'provenance': build_export_provenance(research_context),
        'comparison_summary': comparison_summary,
        'exported_at': datetime.now().isoformat(),
        'geo_lab_version': '1.1.0'
    }

    params_json = json.dumps(export_params, indent=2, ensure_ascii=False)
    st.code(params_json, language='json')

    st.download_button(
        label="\ud30c\ub77c\ubbf8\ud130 JSON \ub2e4\uc6b4\ub85c\ub4dc",
        data=params_json,
        file_name="parameters.json",
        mime="application/json"
    )

    st.success("""
    **U0001f4a1 재현성 팁:**
    이 JSON 파일을 논문 Supplementary Material에 포함하면,
    다른 연구자가 동일한 결과를 재현할 수 있습니다.
    """)
