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
import sys
import os
import plotly.graph_objects as go
import plotly.express as px

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

# ========== Page Config (무조건 첫 번째!) ==========
st.set_page_config(page_title="🔬 Research Lab", page_icon="🔬", layout="wide")

# ========== CSS 로드 ==========
def load_css():
    css_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "style.css")
    if os.path.exists(css_path):
        with open(css_path, 'r', encoding='utf-8') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

load_css()

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
            filename = uploaded_file.name.lower()
            
            if filename.endswith('.npy'):
                elevation = load_dem_npy(uploaded_file.read())
            elif filename.endswith('.asc'):
                content = uploaded_file.read().decode('utf-8')
                elevation, metadata = load_dem_asc(content)
                cell_size = metadata.get('cellsize', cell_size)
            else:  # CSV
                content = uploaded_file.read().decode('utf-8')
                elevation = load_dem_csv(content)
            
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

# 탭 구성
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🗺️ 3D 뷰", "📊 프로파일", "📈 Hypsometric", "⛰️ 경사 분석", "💾 내보내기"
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
    st.plotly_chart(fig, use_container_width=True)
    
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
    st.plotly_chart(fig_profile, use_container_width=True)
    
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
        st.plotly_chart(fig_slope, use_container_width=True)
    
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
        st.plotly_chart(fig_loc, use_container_width=True)

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
    st.plotly_chart(fig_hypso, use_container_width=True)
    
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
    st.plotly_chart(fig_slope_map, use_container_width=True)
    
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
    st.plotly_chart(fig_hist, use_container_width=True)
    
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
        st.plotly_chart(fig_curv, use_container_width=True)
        
        st.markdown("**해석:** 양수(빨강) = 볼록, 음수(파랑) = 오목")

# ==========================================
# Tab 5: 데이터 내보내기
# ==========================================
with tab5:
    st.subheader("💾 데이터 내보내기")
    
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
            label="📄 CSV 다운로드",
            data=csv_bytes,
            file_name="elevation.csv",
            mime="text/csv"
        )
    
    with col2:
        npy_bytes = export_to_bytes_npy(elevation)
        st.download_button(
            label="🔢 NumPy 다운로드",
            data=npy_bytes,
            file_name="elevation.npy",
            mime="application/octet-stream"
        )
    
    with col3:
        # ASC 포맷
        from io import StringIO
        asc_buffer = StringIO()
        h, w = elevation.shape
        asc_buffer.write(f"ncols {w}\n")
        asc_buffer.write(f"nrows {h}\n")
        asc_buffer.write(f"xllcorner 0\n")
        asc_buffer.write(f"yllcorner 0\n")
        asc_buffer.write(f"cellsize {cell_size}\n")
        asc_buffer.write(f"nodata_value -9999\n")
        for row in elevation:
            asc_buffer.write(' '.join(f'{x:.4f}' for x in row) + '\n')
        
        st.download_button(
            label="🗺️ ASC 다운로드",
            data=asc_buffer.getvalue(),
            file_name="elevation.asc",
            mime="text/plain"
        )
    
    st.markdown("---")
    
    # 파라미터 JSON
    st.subheader("📋 파라미터 기록 (재현성)")
    
    import json
    from datetime import datetime
    
    export_params = {
        **params,
        'statistics': get_dem_statistics(elevation),
        'hypsometric_integral': calculate_hypsometric_curve(elevation).hypsometric_integral,
        'relief_ratio': calculate_relief_ratio(elevation),
        'exported_at': datetime.now().isoformat(),
        'geo_lab_version': '1.0.0'
    }
    
    params_json = json.dumps(export_params, indent=2, ensure_ascii=False)
    st.code(params_json, language='json')
    
    st.download_button(
        label="📋 파라미터 JSON 다운로드",
        data=params_json,
        file_name="parameters.json",
        mime="application/json"
    )
    
    st.success("""
    **💡 재현성 팁:**
    이 JSON 파일을 논문 Supplementary Material에 포함하면,
    다른 연구자가 동일한 결과를 재현할 수 있습니다.
    """)
