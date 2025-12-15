"""
🧪 Geo-Lab Script: 사용자 코드로 지형 생성
Python 코드로 직접 지형을 생성하고 조작합니다.
"""
import streamlit as st
import numpy as np
import sys
import os

# 상위 디렉토리 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.grid import WorldGrid
from engine.script_engine import ScriptExecutor
from app.components.renderer import render_terrain_plotly
from app.components.animation_renderer import create_animated_terrain_figure
from engine.ideal_landforms import IDEAL_LANDFORM_GENERATORS

st.set_page_config(page_title="🧪 Lab Script", page_icon="🧪", layout="wide")

st.header("🧪 Geo-Lab Script")
st.markdown("_Python 코드로 직접 지형을 생성하고 조작합니다._")

# 사이드바 설정
st.sidebar.subheader("⚙️ 그리드 설정")
grid_size = st.sidebar.slider("그리드 크기", 50, 200, 100)

# 탭 구성
tab1, tab2, tab3 = st.tabs(["📝 코드 편집", "📚 예제 코드", "📖 도움말"])

with tab1:
    st.subheader("📝 코드 편집기")
    
    # 기본 코드 템플릿
    default_code = '''# Geo-Lab Script 예제
# 사용 가능한 변수: elevation, bedrock, sediment, water_depth, np, math

# 1. 기본 지형 생성 (평탄한 평원)
h, w = elevation.shape
elevation[:, :] = 10.0

# 2. 중앙에 원뿔형 산 추가
center_y, center_x = h // 2, w // 2
for y in range(h):
    for x in range(w):
        dist = np.sqrt((y - center_y)**2 + (x - center_x)**2)
        if dist < 30:
            peak_height = 50.0 * (1 - dist / 30)
            elevation[y, x] += peak_height

# 3. 하천 추가 (왼쪽에서 오른쪽으로)
for x in range(w):
    river_y = int(center_y + 10 * np.sin(x * 0.1))
    for dy in range(-2, 3):
        if 0 <= river_y + dy < h:
            elevation[river_y + dy, x] -= 5.0
            water_depth[river_y + dy, x] = 3.0

print("지형 생성 완료!")
'''
    
    # 세션 상태에 코드 저장
    if 'user_script' not in st.session_state:
        st.session_state['user_script'] = default_code
    
    # 코드 편집기
    user_code = st.text_area(
        "Python 코드",
        value=st.session_state.get('user_script', default_code),
        height=400,
        key="code_editor"
    )
    st.session_state['user_script'] = user_code
    
    col1, col2 = st.columns(2)
    
    with col1:
        run_button = st.button("▶️ 실행", type="primary", use_container_width=True)
    with col2:
        reset_button = st.button("🔄 초기화", use_container_width=True)
    
    if reset_button:
        st.session_state['user_script'] = default_code
        st.rerun()
    
    if run_button:
        with st.spinner("코드 실행 중..."):
            try:
                # 그리드 생성
                grid = WorldGrid(grid_size, grid_size)
                executor = ScriptExecutor(grid)
                
                # 스크립트 실행
                success, message = executor.execute(user_code)
                
                if success:
                    st.success(f"✅ {message}")
                    
                    # 결과 시각화
                    st.subheader("📊 결과")
                    
                    # 2D / 3D 선택
                    view_mode = st.radio("뷰 모드", ["3D", "2D"], horizontal=True)
                    
                    if view_mode == "3D":
                        fig = render_terrain_plotly(
                            grid.elevation,
                            "스크립트 결과",
                            add_water=True,
                            water_depth_grid=grid.water_depth,
                            water_level=-999,
                            force_camera=False
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        import matplotlib.pyplot as plt
                        fig, ax = plt.subplots(figsize=(10, 8))
                        im = ax.imshow(grid.elevation, cmap='terrain', origin='lower')
                        plt.colorbar(im, ax=ax, label='Elevation (m)')
                        ax.set_title("2D 고도 맵")
                        st.pyplot(fig)
                    
                    # 통계
                    st.markdown("**📈 통계:**")
                    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
                    col_s1.metric("최저 고도", f"{grid.elevation.min():.1f}m")
                    col_s2.metric("최고 고도", f"{grid.elevation.max():.1f}m")
                    col_s3.metric("평균 고도", f"{grid.elevation.mean():.1f}m")
                    col_s4.metric("수역 비율", f"{(grid.water_depth > 0).sum() / grid.water_depth.size * 100:.1f}%")
                    
                else:
                    st.error(f"❌ {message}")
                    
            except Exception as e:
                st.error(f"❌ 오류: {str(e)}")

with tab2:
    st.subheader("📚 검증된 지형 불러오기")
    st.markdown("_이미 구현된 지형을 불러와서 변형하거나 학습할 수 있습니다._")
    
    # 카테고리별 지형 목록
    landform_categories = {
        "🌊 하천 지형": ["v_valley", "meander", "free_meander", "alluvial_fan", "incised_meander", "delta", "waterfall"],
        "🔺 삼각주": ["bird_foot_delta", "arcuate_delta", "cuspate_delta"],
        "❄️ 빙하 지형": ["u_valley", "cirque", "horn", "arete", "fjord", "drumlin"],
        "🌋 화산 지형": ["shield_volcano", "stratovolcano", "caldera", "cinder_cone"],
        "🦇 카르스트": ["karst_doline", "uvala", "tower_karst"],
        "🏜️ 건조 지형": ["barchan_dune", "mesa", "pedestal_rock", "wadi", "playa"],
        "🏖️ 해안 지형": ["coastal_cliff", "spit", "lagoon", "tombolo"]
    }
    
    selected_cat = st.selectbox("카테고리 선택", list(landform_categories.keys()))
    available_landforms = [lf for lf in landform_categories[selected_cat] if lf in IDEAL_LANDFORM_GENERATORS]
    
    if available_landforms:
        selected_landform = st.selectbox("지형 선택", available_landforms)
        
        col1, col2 = st.columns(2)
        
        with col1:
            load_size = st.slider("그리드 크기", 50, 150, 100, key="load_size")
        with col2:
            load_stage = st.slider("형성 단계", 0.0, 1.0, 1.0, 0.1, key="load_stage")
        
        if st.button("🔄 지형 불러오기", type="primary", use_container_width=True):
            try:
                # 지형 생성 함수 호출
                landform_func = IDEAL_LANDFORM_GENERATORS[selected_landform]
                
                # stage 파라미터 지원 여부 확인
                import inspect
                sig = inspect.signature(landform_func)
                params = list(sig.parameters.keys())
                
                if 'stage' in params:
                    result = landform_func(load_size, load_stage)
                else:
                    result = landform_func(load_size)
                
                # 결과 처리 (tuple인 경우 elevation만 추출)
                if isinstance(result, tuple):
                    elevation = result[0]
                else:
                    elevation = result
                
                st.success(f"✅ {selected_landform} 지형 불러오기 완료!")
                
                # 3D 시각화
                fig = render_terrain_plotly(
                    elevation,
                    f"{selected_landform} (Stage {int(load_stage*100)}%)",
                    add_water=True,
                    water_level=-999,
                    force_camera=False
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # 통계
                col_s1, col_s2, col_s3 = st.columns(3)
                col_s1.metric("최저 고도", f"{elevation.min():.1f}m")
                col_s2.metric("최고 고도", f"{elevation.max():.1f}m")
                col_s3.metric("평균 고도", f"{elevation.mean():.1f}m")
                
                # 코드 확인
                with st.expander("💻 이 지형의 코드 보기"):
                    st.markdown(f"""
```python
from engine.ideal_landforms import IDEAL_LANDFORM_GENERATORS

# 지형 생성
landform_func = IDEAL_LANDFORM_GENERATORS['{selected_landform}']
elevation = landform_func(grid_size={load_size}, stage={load_stage})

# 결과: {elevation.shape} 크기의 고도 배열
# 최저: {elevation.min():.1f}m, 최고: {elevation.max():.1f}m
```

**함수 소스 위치:** `engine/ideal_landforms.py` → `create_{selected_landform}()`
                    """)
                    
            except Exception as e:
                st.error(f"❌ 오류: {str(e)}")
    else:
        st.warning("이 카테고리에 사용 가능한 지형이 없습니다.")
    
    st.markdown("---")
    st.markdown("""
    ### 💡 팁: 직접 코드 짜는 법
    
    **기본 패턴:**
    ```python
    h, w = elevation.shape
    center_y, center_x = h // 2, w // 2
    
    for y in range(h):
        for x in range(w):
            dist = np.sqrt((y - center_y)**2 + (x - center_x)**2)
            # 거리 기반 높이 계산
            elevation[y, x] = 높이공식(dist)
    ```
    
    **핵심 원칙:**
    1. `elevation[:, :]`로 전체 초기화
    2. for 루프로 각 셀 순회
    3. 거리 기반 높이 공식 적용
    4. `water_depth`로 물 표시
    """)

with tab3:
    st.subheader("📖 도움말")
    
    st.markdown("""
    ### 사용 가능한 변수
    
    | 변수 | 타입 | 설명 |
    |------|------|------|
    | `elevation` | np.ndarray | 고도 배열 (수정 가능) |
    | `bedrock` | np.ndarray | 기반암 배열 |
    | `sediment` | np.ndarray | 퇴적물 배열 |
    | `water_depth` | np.ndarray | 수심 배열 |
    | `np` | module | NumPy 모듈 |
    | `math` | module | math 모듈 |
    
    ### 기본 패턴
    
    ```python
    # 그리드 크기 가져오기
    h, w = elevation.shape
    
    # 전체 고도 설정
    elevation[:, :] = 10.0
    
    # 특정 영역 수정
    elevation[10:20, 30:40] = 50.0
    
    # 거리 기반 지형
    for y in range(h):
        for x in range(w):
            dist = np.sqrt((y - center_y)**2 + (x - center_x)**2)
            elevation[y, x] = some_function(dist)
    ```
    
    ### 주의사항
    
    - `import` 문은 사용할 수 없습니다 (보안)
    - `open()`, `exec()`, `eval()` 사용 불가
    - 무한 루프 주의 (브라우저가 멈출 수 있음)
    """)
