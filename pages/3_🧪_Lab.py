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
from engine.simple_lem import SimpleLEM, create_demo_simulation

# 확장 모듈 import
try:
    from engine.lem.climate import ClimateSystem
    from engine.lem.human import HumanActivity
    from engine.lem.visualization import LEMVisualizer
    LEM_EXTENSIONS = True
except ImportError:
    LEM_EXTENSIONS = False

# ========== Page Config (무조건 첫 번째!) ==========
st.set_page_config(page_title="🧪 Lab Script", page_icon="🧪", layout="wide")

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
    <h1 style='font-size: 2.2rem; font-weight: 700; margin-bottom: 0.25rem;'>🧪 Geo-Lab Script</h1>
    <p style='color: #86868b; font-size: 1rem;'>Python 코드로 직접 지형을 생성하고 조작합니다.</p>
</div>
""", unsafe_allow_html=True)

# 사이드바 설정
st.sidebar.subheader("⚙️ 그리드 설정")
grid_size = st.sidebar.slider("그리드 크기", 50, 200, 100)

# 탭 구성 (지형 시뮬레이션으로 통합)
tab1, tab2, tab3, tab4 = st.tabs([
    "📝 코드 편집", "📚 예제 코드", "🌍 지형 시뮬레이션", "📖 도움말"
])


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

# ========== 지형 시뮬레이션 탭 ==========
with tab3:
    st.subheader("🌍 지형 발달 시뮬레이터")
    st.markdown("_침식 · 풍화 · 단층 · 화산 · 빙하 · 해안 · 기후 · 인간활동 통합 모델_")
    
    # 설명
    with st.expander("📚 물리 법칙 설명", expanded=False):
        st.markdown("""
        ### Stream Power Law (하천 침식)
        ```
        E = K × A^m × S^n
        ```
        - **E**: 침식률 (m/year)
        - **K**: 침식계수 - 암석 저항성의 역수
        - **A**: 상류 유역면적 (m²)
        - **S**: 경사 (m/m)
        - **m** ≈ 0.5, **n** ≈ 1.0

        ### Hillslope Diffusion (사면 확산)
        ```
        ∂z/∂t = D × ∇²z
        ```
        - 시간이 지나면서 사면이 완만해지는 과정
        - **D**: 확산계수 (m²/year)
        """)
    
    col_params, col_results = st.columns([1, 2])
    
    with col_params:
        st.markdown("### 🎯 시나리오 선택")
        
        # 시나리오 프리셋 (Gallery 지형 포함)
        scenario = st.selectbox(
            "시뮬레이션 시나리오",
            [
                "--- 🏔️ 산지/침식 ---",
                "🏔️ 산지 형성 (융기+침식)",
                "🗻 V자곡 (하천침식)",
                "❄️ U자곡 (빙하침식)",
                "⛰️ 단층 산지",
                "--- 🌊 하천/퇴적 ---",
                "🔄 곡류 하천 (사행)",
                "🏖️ 삼각주 (Delta)",
                "📐 선상지 (Alluvial Fan)",
                "--- 🏜️ 건조/바람 ---",
                "🏜️ 사막 지형 (바람침식)",
                "🌙 바르한 사구",
                "--- 🌊 해안 ---",
                "🌊 해안 절벽 (해식애)",
                "🏖️ 해안단구",
                "--- 🌋 화산/특수 ---",
                "🌋 화산 지형 (성층화산)",
                "🕳️ 카르스트 (돌리네)",
                "🧊 권곡/빙하호",
                "--- ⚙️ 사용자 ---",
                "⚙️ 자유 설정"
            ],
            key="lem_scenario"
        )
        
        # 시나리오별 프리셋 정의
        SCENARIO_PRESETS = {
            "🏔️ 산지 형성 (융기+침식)": {
                "initial_topo": "돔형 산지",
                "enable_weathering": True, "enable_sediment": True,
                "enable_lateral": False, "enable_glacial": False,
                "enable_marine": False, "enable_landslides": True,
                "enable_faulting": False, "enable_karst": False,
                "enable_aeolian": False, "enable_volcanic": False,
                "enable_groundwater": False, "enable_freeze_thaw": False,
                "enable_bioerosion": True, "enable_lake": False,
                "enable_glacial_deposit": False
            },
            "🗻 V자곡 (하천침식)": {
                "initial_topo": "V자곡",
                "enable_weathering": True, "enable_sediment": True,
                "enable_lateral": True, "enable_glacial": False,
                "enable_marine": False, "enable_landslides": True,
                "enable_faulting": False, "enable_karst": False,
                "enable_aeolian": False, "enable_volcanic": False,
                "enable_groundwater": False, "enable_freeze_thaw": False,
                "enable_bioerosion": True, "enable_lake": False,
                "enable_glacial_deposit": False
            },
            "❄️ U자곡 (빙하침식)": {
                "initial_topo": "U자곡",
                "enable_weathering": True, "enable_sediment": True,
                "enable_lateral": False, "enable_glacial": True,
                "enable_marine": False, "enable_landslides": False,
                "enable_faulting": False, "enable_karst": False,
                "enable_aeolian": False, "enable_volcanic": False,
                "enable_groundwater": False, "enable_freeze_thaw": True,
                "enable_bioerosion": False, "enable_lake": True,
                "enable_glacial_deposit": True
            },
            "⛰️ 단층 산지": {
                "initial_topo": "경사면",
                "enable_weathering": True, "enable_sediment": True,
                "enable_lateral": False, "enable_glacial": False,
                "enable_marine": False, "enable_landslides": True,
                "enable_faulting": True, "enable_karst": False,
                "enable_aeolian": False, "enable_volcanic": False,
                "enable_groundwater": False, "enable_freeze_thaw": False,
                "enable_bioerosion": True, "enable_lake": False,
                "enable_glacial_deposit": False
            },
            "🔄 곡류 하천 (사행)": {
                "initial_topo": "곡류",
                "enable_weathering": True, "enable_sediment": True,
                "enable_lateral": True, "enable_glacial": False,
                "enable_marine": False, "enable_landslides": False,
                "enable_faulting": False, "enable_karst": False,
                "enable_aeolian": False, "enable_volcanic": False,
                "enable_groundwater": False, "enable_freeze_thaw": False,
                "enable_bioerosion": True, "enable_lake": True,
                "enable_glacial_deposit": False
            },
            "🏖️ 삼각주 (Delta)": {
                "initial_topo": "삼각주",
                "enable_weathering": False, "enable_sediment": True,
                "enable_lateral": True, "enable_glacial": False,
                "enable_marine": True, "enable_landslides": False,
                "enable_faulting": False, "enable_karst": False,
                "enable_aeolian": False, "enable_volcanic": False,
                "enable_groundwater": False, "enable_freeze_thaw": False,
                "enable_bioerosion": True, "enable_lake": False,
                "enable_glacial_deposit": False
            },
            "📐 선상지 (Alluvial Fan)": {
                "initial_topo": "선상지",
                "enable_weathering": True, "enable_sediment": True,
                "enable_lateral": True, "enable_glacial": False,
                "enable_marine": False, "enable_landslides": True,
                "enable_faulting": False, "enable_karst": False,
                "enable_aeolian": False, "enable_volcanic": False,
                "enable_groundwater": False, "enable_freeze_thaw": False,
                "enable_bioerosion": False, "enable_lake": False,
                "enable_glacial_deposit": False
            },
            "🏜️ 사막 지형 (바람침식)": {
                "initial_topo": "경사면",
                "enable_weathering": True, "enable_sediment": False,
                "enable_lateral": False, "enable_glacial": False,
                "enable_marine": False, "enable_landslides": False,
                "enable_faulting": False, "enable_karst": False,
                "enable_aeolian": True, "enable_volcanic": False,
                "enable_groundwater": False, "enable_freeze_thaw": False,
                "enable_bioerosion": False, "enable_lake": False,
                "enable_glacial_deposit": False
            },
            "🌙 바르한 사구": {
                "initial_topo": "바르한",
                "enable_weathering": False, "enable_sediment": False,
                "enable_lateral": False, "enable_glacial": False,
                "enable_marine": False, "enable_landslides": False,
                "enable_faulting": False, "enable_karst": False,
                "enable_aeolian": True, "enable_volcanic": False,
                "enable_groundwater": False, "enable_freeze_thaw": False,
                "enable_bioerosion": False, "enable_lake": False,
                "enable_glacial_deposit": False
            },
            "🌊 해안 절벽 (해식애)": {
                "initial_topo": "해안절벽",
                "enable_weathering": True, "enable_sediment": True,
                "enable_lateral": False, "enable_glacial": False,
                "enable_marine": True, "enable_landslides": True,
                "enable_faulting": False, "enable_karst": False,
                "enable_aeolian": False, "enable_volcanic": False,
                "enable_groundwater": False, "enable_freeze_thaw": False,
                "enable_bioerosion": True, "enable_lake": False,
                "enable_glacial_deposit": False
            },
            "🏖️ 해안단구": {
                "initial_topo": "경사면",
                "enable_weathering": True, "enable_sediment": True,
                "enable_lateral": False, "enable_glacial": False,
                "enable_marine": True, "enable_landslides": False,
                "enable_faulting": True, "enable_karst": False,
                "enable_aeolian": False, "enable_volcanic": False,
                "enable_groundwater": False, "enable_freeze_thaw": False,
                "enable_bioerosion": True, "enable_lake": False,
                "enable_glacial_deposit": False
            },
            "🌋 화산 지형 (성층화산)": {
                "initial_topo": "경사면",
                "enable_weathering": True, "enable_sediment": True,
                "enable_lateral": True, "enable_glacial": False,
                "enable_marine": False, "enable_landslides": True,
                "enable_faulting": False, "enable_karst": False,
                "enable_aeolian": False, "enable_volcanic": True,
                "enable_groundwater": False, "enable_freeze_thaw": False,
                "enable_bioerosion": True, "enable_lake": True,
                "enable_glacial_deposit": False
            },
            "🕳️ 카르스트 (돌리네)": {
                "initial_topo": "경사면",
                "enable_weathering": True, "enable_sediment": False,
                "enable_lateral": False, "enable_glacial": False,
                "enable_marine": False, "enable_landslides": False,
                "enable_faulting": False, "enable_karst": True,
                "enable_aeolian": False, "enable_volcanic": False,
                "enable_groundwater": True, "enable_freeze_thaw": False,
                "enable_bioerosion": True, "enable_lake": True,
                "enable_glacial_deposit": False
            },
            "🧊 권곡/빙하호": {
                "initial_topo": "돔형 산지",
                "enable_weathering": True, "enable_sediment": True,
                "enable_lateral": False, "enable_glacial": True,
                "enable_marine": False, "enable_landslides": True,
                "enable_faulting": False, "enable_karst": False,
                "enable_aeolian": False, "enable_volcanic": False,
                "enable_groundwater": False, "enable_freeze_thaw": True,
                "enable_bioerosion": False, "enable_lake": True,
                "enable_glacial_deposit": True
            }
        }
        
        # 모드 선택
        advanced_mode = st.checkbox("⚙️ 고급 모드", value=False, help="모든 파라미터 직접 설정")
        
        st.markdown("---")
        
        # 시나리오 프리셋 적용 (자유 설정 아닌 경우)
        if scenario != "⚙️ 자유 설정" and scenario in SCENARIO_PRESETS:
            preset = SCENARIO_PRESETS[scenario]
            # 프리셋에서 값 가져오기
            initial_topo_name = preset["initial_topo"]
            
            # 확장된 초기 지형 매핑
            TOPO_MAPPING = {
                "돔형 산지": "🏔️ 돔형 산지",
                "경사면": "📐 경사면",
                "V자곡": "🗻 V자곡",
                "U자곡": "❄️ U자곡",
                "곡류": "🔄 곡류",
                "삼각주": "🏖️ 삼각주",
                "선상지": "📐 선상지",
                "바르한": "🌙 바르한",
                "해안절벽": "🌊 해안절벽"
            }
            initial_topo = TOPO_MAPPING.get(initial_topo_name, "🏔️ 돔형 산지")
            
            # 프리셋 플래그
            enable_weathering = preset["enable_weathering"]
            enable_sediment = preset["enable_sediment"]
            enable_lateral = preset["enable_lateral"]
            enable_glacial = preset["enable_glacial"]
            enable_marine = preset["enable_marine"]
            enable_landslides = preset["enable_landslides"]
            enable_faulting = preset["enable_faulting"]
            enable_karst = preset["enable_karst"]
            enable_aeolian = preset["enable_aeolian"]
            enable_volcanic = preset["enable_volcanic"]
            enable_groundwater = preset["enable_groundwater"]
            enable_freeze_thaw = preset["enable_freeze_thaw"]
            enable_bioerosion = preset["enable_bioerosion"]
            enable_lake = preset["enable_lake"]
            enable_glacial_deposit = preset["enable_glacial_deposit"]
            
            st.info(f"📍 **{scenario}** 시나리오 적용됨")
        else:
            # 자유 설정: 초기 지형 선택
            initial_topo = st.selectbox(
                "초기 지형",
                ["🏔️ 돔형 산지", "📐 경사면", "🗻 V자곡"],
                key="lem_initial_free"
            )
        
        # 핵심 파라미터 (기본 모드에서도 표시)
        st.markdown("**📊 핵심 파라미터**")
        
        K = st.slider(
            "침식계수 (K)",
            min_value=0.00001,
            max_value=0.001,
            value=0.0001,
            step=0.00001,
            format="%.5f",
            help="높을수록 침식이 빠름"
        )
        
        D = st.slider(
            "확산계수 (D)",
            min_value=0.001,
            max_value=0.1,
            value=0.01,
            step=0.001,
            format="%.3f",
            help="높을수록 사면 평탄화가 빠름"
        )
        
        U = st.slider(
            "융기율 (U)",
            min_value=0.0,
            max_value=0.001,
            value=0.0003,
            step=0.0001,
            format="%.4f",
            help="지각 융기 속도 (m/year)"
        )
        
        # 고급 모드: 상세 파라미터 표시 (expander 안에)
        if advanced_mode or scenario == "⚙️ 자유 설정":
            with st.expander("🔧 상세 프로세스 설정", expanded=False):
                st.markdown("**🪨 풍화 설정**")
                
                enable_weathering = st.checkbox("풍화 활성화", value=True, help="기반암 → 토양 변환 과정", key="adv_weathering")
                
                W0 = st.slider(
                    "최대 풍화율 (W0)",
                    min_value=0.0001,
                    max_value=0.01,
                    value=0.001,
                    step=0.0001,
                    format="%.4f",
                    help="토양이 없을 때 기반암 풍화 속도 (m/year)",
                    key="adv_w0"
                )
                
                st.markdown("**🏔️ 퇴적물 운반**")
                
                enable_sediment = st.checkbox("퇴적물 운반 활성화", value=True, help="침식 물질의 하류 이동 및 퇴적", key="adv_sediment")
                
                Vs = st.slider(
                    "퇴적 속도 (Vs)",
                    min_value=0.1,
                    max_value=5.0,
                    value=1.0,
                    step=0.1,
                    format="%.1f",
                    help="높을수록 퇴적물이 빨리 쌓임",
                    key="adv_vs"
                )
                
                st.markdown("**🌊 측방 침식 (곡류)**")
                
                enable_lateral = st.checkbox("측방 침식 활성화", value=False, help="하천이 옆으로 침식 → 골짜기 확장", key="adv_lateral")
                
                Kl = st.slider(
                    "측방 침식계수 (Kl)",
                    min_value=0.000001,
                    max_value=0.0001,
                    value=0.00001,
                    step=0.000001,
                    format="%.6f",
                    help="높을수록 하천이 옆으로 빠르게 침식",
                    disabled=not enable_lateral,
                    key="adv_kl"
                )
                
                st.markdown("**❄️ 빙하 / 🌊 해안 / ⛰️ 기타**")
                
                col_adv1, col_adv2 = st.columns(2)
                with col_adv1:
                    enable_glacial = st.checkbox("빙하 침식", value=False, key="adv_glacial")
                    enable_marine = st.checkbox("해안 침식", value=False, key="adv_marine")
                    enable_landslides = st.checkbox("산사태", value=False, key="adv_landslide")
                    enable_faulting = st.checkbox("단층 운동", value=False, key="adv_fault")
                    enable_karst = st.checkbox("카르스트", value=False, key="adv_karst")
                with col_adv2:
                    enable_aeolian = st.checkbox("바람 침식", value=False, key="adv_aeolian")
                    enable_volcanic = st.checkbox("화산 활동", value=False, key="adv_volcanic")
                    enable_groundwater = st.checkbox("지하수", value=False, key="adv_ground")
                    enable_freeze_thaw = st.checkbox("동결파쇄", value=False, key="adv_freeze")
                    enable_bioerosion = st.checkbox("식생 보호", value=False, key="adv_bio")
                
                col_adv3, col_adv4 = st.columns(2)
                with col_adv3:
                    enable_lake = st.checkbox("호수 형성", value=False, key="adv_lake")
                with col_adv4:
                    enable_glacial_deposit = st.checkbox("빙하 퇴적", value=False, key="adv_glac_dep")
                
                # 세부 값들 (기본값)
                Kg, glacier_ela = 0.0001, 200.0
                Km, sea_level = 0.001, 0.0
                critical_slope = 0.6
                fault_rate, fault_position = 0.001, 0.5
                Kk = 0.0001
                Ka, wind_direction = 0.0001, 0.0
                volcanic_rate, volcanic_position = 0.01, (0.5, 0.5)
                water_table, spring_rate = 50.0, 0.001
                Kf, freeze_elevation = 0.0005, 300.0
                vegetation_factor = 0.5
                lake_threshold = 0.001
                moraine_rate = 0.3
        else:
            # 고급 모드 아닐 때: 기본값 사용
            enable_weathering = True
            enable_sediment = True
            enable_lateral = False
            enable_glacial = False
            enable_marine = False
            enable_landslides = False
            enable_faulting = False
            enable_karst = False
            enable_aeolian = False
            enable_volcanic = False
            enable_groundwater = False
            enable_freeze_thaw = False
            enable_bioerosion = False
            enable_lake = False
            enable_glacial_deposit = False
            
            # 기본값
            W0, Vs, Kl = 0.001, 1.0, 0.00001
            Kg, glacier_ela = 0.0001, 200.0
            Km, sea_level = 0.001, 0.0
            critical_slope = 0.6
            fault_rate, fault_position = 0.001, 0.5
            Kk = 0.0001
            Ka, wind_direction = 0.0001, 0.0
            volcanic_rate, volcanic_position = 0.01, (0.5, 0.5)
            water_table, spring_rate = 50.0, 0.001
            Kf, freeze_elevation = 0.0005, 300.0
            vegetation_factor = 0.5
            lake_threshold = 0.001
            moraine_rate = 0.3
        
        # ========== 🔬 고급 Landlab 물리 모델 ==========
        st.markdown("---")
        st.markdown("### 🔬 고급 물리 모델")
        st.caption("Landlab 기반 추가 물리 과정")
        
        # 확산 모델 선택
        diffusion_model = st.selectbox(
            "확산 모델",
            ["Linear (기본)", "Nonlinear (급경사)", "Depth-Dependent (토양)", "Taylor Nonlinear"],
            index=0,
            help="사면 확산 모델 선택"
        )
        
        if diffusion_model == "Nonlinear (급경사)":
            Sc_critical = st.slider("임계 경사 (Sc)", 0.5, 2.0, 1.0, 0.1, help="이 경사에서 확산 무한대")
        else:
            Sc_critical = 1.0
        
        # 유역 계산 선택
        flow_model = st.selectbox(
            "유역 계산 방식",
            ["D8 (기본)", "MFD (다중유향)"],
            index=0,
            help="유역면적 계산 알고리즘"
        )
        
        # 퇴적물 모델
        enable_exner = st.checkbox("Exner 방정식", value=False, help="하상 변동 정밀 계산")
        
        # 사면 안정성
        enable_slope_stability = st.checkbox("사면 안정성 분석", value=False, help="무한사면 안전율 계산")
        if enable_slope_stability:
            col_ss1, col_ss2 = st.columns(2)
            with col_ss1:
                cohesion = st.number_input("점착력 (Pa)", value=5000.0, step=1000.0)
            with col_ss2:
                friction_angle = st.number_input("내부마찰각 (°)", value=30.0, step=5.0)
        else:
            cohesion, friction_angle = 5000.0, 30.0
        
        # 해안 모델
        enable_coastal = st.checkbox("해안 지형 모델", value=False, help="파랑침식/연안류")
        if enable_coastal:
            wave_height = st.slider("파고 (m)", 0.5, 5.0, 2.0)
        else:
            wave_height = 2.0
        
        # 등압 조절
        enable_isostasy = st.checkbox("Flexural Isostasy", value=False, help="하중에 의한 지각 변형")
        
        # 기본값 설정 (expander 스코프 문제 해결)
        rain_type = "normal"
        rain_intensity = 1.0
        climate_scenario = "없음"
        enable_dam = False
        dam_position, dam_height = 50, 30
        enable_deforestation = False
        deforest_intensity = 0.0
        
        # ========== 🌧️ 기후 시나리오 ==========
        with st.expander("🌧️ 기후 시나리오 (강우, 기후변화)", expanded=False):
            st.caption("강우 패턴 및 기후 변화")
            
            # 강우 이벤트
            rain_event = st.selectbox(
                "강우 이벤트",
                ["normal (기본)", "storm (폭풍)", "drought (가뭄)", "monsoon (몬순)"],
                index=0,
                help="강우 패턴이 침식에 영향"
            )
            rain_type = rain_event.split(" ")[0]
            
            rain_intensity = st.slider("강우 강도", 0.5, 3.0, 1.0, 0.1, help="1.0=기본, >1.5=폭우")
            
            # 기후 변화 시나리오
            climate_scenario = st.selectbox(
                "기후 변화 시나리오",
                ["없음", "RCP 2.6 (저감)", "RCP 4.5 (중간)", "RCP 8.5 (고배출)", "빙하기"],
                index=0,
                help="장기 기후 변화 시나리오"
            )
        
        # ========== 🏗️ 인간 활동 ==========
        with st.expander("🏗️ 인간 활동 (댐, 벌채)", expanded=False):
            st.caption("댐 건설 및 삼림 벌채")
            
            # 댐 건설
            enable_dam = st.checkbox("댐 건설", value=False, help="하천에 댐 구조물 추가")
            if enable_dam:
                col_dam1, col_dam2 = st.columns(2)
                with col_dam1:
                    dam_position = st.slider("댐 위치 (%)", 20, 80, 50, help="하류에서 상류 방향")
                with col_dam2:
                    dam_height = st.slider("댐 높이 (m)", 10, 100, 30)
            else:
                dam_position, dam_height = 50, 30
            
            # 삼림 벌채
            enable_deforestation = st.checkbox("삼림 벌채", value=False, help="식생 감소 → 침식 증가")
            if enable_deforestation:
                deforest_intensity = st.slider("벌채 강도", 0.1, 1.0, 0.5, help="1.0=완전 벌채")
            else:
                deforest_intensity = 0.0
        
        st.markdown("---")
        
        # 시간 설정
        total_time = st.slider(
            "시뮬레이션 시간 (년)",
            min_value=10000,
            max_value=500000,
            value=50000,
            step=10000,
            format="%d"
        )
        
        lem_grid_size = st.slider(
            "해상도",
            min_value=50,
            max_value=150,
            value=80,
            step=10,
            key="lem_grid"
        )
        
        run_lem = st.button("▶️ 시뮬레이션 실행", type="primary", use_container_width=True)
    
    with col_results:
        # 시뮬레이션 실행
        if run_lem:
            with st.spinner("🌊 침식 시뮬레이션 실행 중..."):
                try:
                    # LEM 객체 생성 (풍화 + 퇴적물 파라미터 포함)
                    lem = SimpleLEM(
                        grid_size=lem_grid_size,
                        K=K, D=D, U=U,
                        W0=W0, enable_weathering=enable_weathering,
                        Vs=Vs, enable_sediment_transport=enable_sediment,
                        Kl=Kl, enable_lateral_erosion=enable_lateral,
                        # 고급 기능
                        Kg=Kg, glacier_ela=glacier_ela, enable_glacial=enable_glacial,
                        Km=Km, sea_level=sea_level, enable_marine=enable_marine,
                        critical_slope=critical_slope, enable_landslides=enable_landslides,
                        fault_rate=fault_rate, fault_position=fault_position, enable_faulting=enable_faulting,
                        Kk=Kk, enable_karst=enable_karst,
                        # 추가 기능
                        Ka=Ka, wind_direction=wind_direction, enable_aeolian=enable_aeolian,
                        volcanic_rate=volcanic_rate, volcanic_position=volcanic_position, enable_volcanic=enable_volcanic,
                        water_table=water_table, spring_rate=spring_rate, enable_groundwater=enable_groundwater,
                        Kf=Kf, freeze_elevation=freeze_elevation, enable_freeze_thaw=enable_freeze_thaw,
                        vegetation_factor=vegetation_factor, enable_bioerosion=enable_bioerosion,
                        lake_threshold=lake_threshold, enable_lake=enable_lake,
                        moraine_rate=moraine_rate, enable_glacial_deposit=enable_glacial_deposit
                    )
                    
                    # 초기 지형 생성 (확장)
                    from engine.ideal_landforms import (
                        create_u_valley, create_v_valley, create_meander,
                        create_delta, create_alluvial_fan, create_barchan_dune,
                        create_coastal_cliff
                    )
                    
                    if initial_topo == "🏔️ 돔형 산지":
                        lem.create_initial_mountain(peak_height=300.0, noise_amp=5.0)
                    elif initial_topo == "📐 경사면":
                        lem.create_inclined_surface(slope=0.02, noise_amp=3.0)
                    elif initial_topo == "🗻 V자곡":
                        initial_elev = create_v_valley(lem_grid_size)
                        lem.set_initial_topography(initial_elev)
                    elif initial_topo == "❄️ U자곡":
                        initial_elev = create_u_valley(lem_grid_size)
                        lem.set_initial_topography(initial_elev)
                    elif initial_topo == "🔄 곡류":
                        initial_elev = create_meander(lem_grid_size)
                        lem.set_initial_topography(initial_elev)
                    elif initial_topo == "🏖️ 삼각주":
                        initial_elev = create_delta(lem_grid_size)
                        lem.set_initial_topography(initial_elev)
                    elif initial_topo == "📐 선상지":
                        initial_elev = create_alluvial_fan(lem_grid_size)
                        lem.set_initial_topography(initial_elev)
                    elif initial_topo == "🌙 바르한":
                        initial_elev = create_barchan_dune(lem_grid_size)
                        lem.set_initial_topography(initial_elev)
                    elif initial_topo == "🌊 해안절벽":
                        initial_elev = create_coastal_cliff(lem_grid_size)
                        lem.set_initial_topography(initial_elev)
                    else:
                        # 기본값
                        lem.create_initial_mountain(peak_height=300.0, noise_amp=5.0)
                    
                    # 초기 상태 저장
                    initial_elevation = lem.elevation.copy()
                    
                    # 시뮬레이션 실행
                    history, times = lem.run(
                        total_time=total_time,
                        dt=100.0,
                        save_interval=max(1, int(total_time / 100 / 20)),
                        verbose=False
                    )
                    
                    # ========== 🔬 고급 물리 모델 적용 ==========
                    final_elevation = history[-1].copy()
                    advanced_results = {}
                    
                    # 1. 고급 확산 모델 적용
                    if diffusion_model != "Linear (기본)":
                        from engine.lem.advanced_physics import DiffusionModels
                        diff = DiffusionModels(lem_grid_size)
                        
                        if diffusion_model == "Nonlinear (급경사)":
                            dz = diff.nonlinear(final_elevation, D=D, Sc=Sc_critical, dt=100.0)
                        elif diffusion_model == "Depth-Dependent (토양)":
                            dz = diff.depth_dependent(final_elevation, lem.soil_depth, D0=D, dt=100.0)
                        else:  # Taylor
                            dz = diff.taylor_nonlinear(final_elevation, D=D, Sc=Sc_critical, dt=100.0)
                        
                        final_elevation += dz
                        advanced_results['diffusion'] = diffusion_model
                    
                    # 2. MFD 유역면적 재계산
                    if flow_model == "MFD (다중유향)":
                        from engine.lem.advanced_physics import FlowRouting
                        flow = FlowRouting(lem_grid_size)
                        drainage_mfd = flow.accumulate_mfd(final_elevation)
                        st.session_state['lem_drainage_mfd'] = drainage_mfd
                        advanced_results['flow'] = 'MFD'
                    
                    # 3. Exner 방정식 (하상변동)
                    if enable_exner:
                        from engine.lem.advanced_physics import SedimentModels
                        sed = SedimentModels(lem_grid_size)
                        exner_result = sed.exner(final_elevation, lem.sediment_flux, dt=100.0)
                        final_elevation += exner_result.bed_change
                        st.session_state['lem_exner'] = exner_result
                        advanced_results['exner'] = True
                    
                    # 4. 사면 안정성 분석
                    if enable_slope_stability:
                        from engine.lem.advanced_physics import SlopeStability
                        stability = SlopeStability(lem_grid_size)
                        slope = lem.calculate_slope()
                        stability_result = stability.infinite_slope(
                            slope, lem.soil_depth, 
                            cohesion=cohesion, friction_angle=friction_angle
                        )
                        st.session_state['lem_stability'] = stability_result
                        advanced_results['stability'] = True
                    
                    # 5. 해안 지형 모델
                    if enable_coastal:
                        from engine.lem.advanced_physics import CoastalModels
                        coastal = CoastalModels(lem_grid_size)
                        wave_erosion = coastal.wave_ravinement(
                            final_elevation, sea_level=sea_level, 
                            wave_height=wave_height, dt=100.0
                        )
                        final_elevation -= wave_erosion
                        st.session_state['lem_wave_erosion'] = wave_erosion
                        advanced_results['coastal'] = True
                    
                    # 6. Flexural Isostasy
                    if enable_isostasy:
                        from engine.lem.advanced_physics import Isostasy
                        iso = Isostasy(lem_grid_size)
                        load = (initial_elevation - final_elevation) * 2700  # 침식량 × 밀도
                        deflection = iso.flexural(load)
                        final_elevation += deflection
                        st.session_state['lem_isostasy'] = deflection
                        advanced_results['isostasy'] = True
                    
                    # ========== 🌧️ 기후 시나리오 적용 ==========
                    # 강우 이벤트 효과 (침식률 조정)
                    if rain_type != "normal":
                        from engine.lem.climate import ClimateSystem
                        climate = ClimateSystem(lem_grid_size)
                        rainfall = climate.rainfall_event(rain_type, intensity=rain_intensity)
                        
                        # 강우에 따른 추가 침식
                        erosion_factor = rainfall * 0.001 * rain_intensity
                        final_elevation -= erosion_factor
                        advanced_results['rain'] = rain_type
                    
                    # 기후 변화 시나리오
                    if climate_scenario != "없음":
                        scenario_map = {
                            "RCP 2.6 (저감)": "rcp26",
                            "RCP 4.5 (중간)": "rcp45",
                            "RCP 8.5 (고배출)": "rcp85",
                            "빙하기": "ice_age"
                        }
                        from engine.lem.climate import ClimateSystem
                        climate = ClimateSystem(lem_grid_size)
                        clim_result = climate.climate_change(scenario_map.get(climate_scenario, "rcp45"), total_time)
                        
                        # 해수면 변화 적용
                        new_sea_level = clim_result['sea_level']
                        final_elevation = np.where(final_elevation < new_sea_level, new_sea_level, final_elevation)
                        advanced_results['climate'] = climate_scenario
                    
                    # ========== 🏗️ 인간 활동 적용 ==========
                    # 댐 건설
                    if enable_dam:
                        from engine.lem.human import HumanActivity
                        human = HumanActivity(lem_grid_size)
                        dam_row = int(lem_grid_size * dam_position / 100)
                        dam_col = lem_grid_size // 2
                        dam = human.build_dam((dam_row, dam_col), height=dam_height)
                        
                        # 댐 지형 적용
                        for dy in range(-2, 3):
                            for dx in range(-5, 6):
                                r, c = dam_row + dy, dam_col + dx
                                if 0 <= r < lem_grid_size and 0 <= c < lem_grid_size:
                                    final_elevation[r, c] += dam_height * 0.5
                        advanced_results['dam'] = dam_height
                    
                    # 삼림 벌채 (침식 증가)
                    if enable_deforestation and deforest_intensity > 0:
                        # 벌채 지역 침식 증가
                        erosion_boost = deforest_intensity * 0.005
                        final_elevation -= erosion_boost
                        advanced_results['deforest'] = deforest_intensity
                    
                    # 최종 결과 업데이트
                    history[-1] = final_elevation
                    st.session_state['lem_advanced'] = advanced_results
                    
                    # 결과를 session_state에 저장
                    st.session_state['lem_history'] = history
                    st.session_state['lem_times'] = times
                    st.session_state['lem_initial'] = initial_elevation
                    st.session_state['lem_erosion_map'] = lem.get_erosion_map()
                    st.session_state['lem_drainage_map'] = lem.get_drainage_map()
                    st.session_state['lem_soil_map'] = lem.get_soil_depth_map()
                    st.session_state['lem_weathering_map'] = lem.get_weathering_map()
                    st.session_state['lem_total_time'] = total_time
                    st.session_state['lem_weathering_enabled'] = enable_weathering
                    
                    # 적용된 고급 모델 표시
                    if advanced_results:
                        applied = ", ".join(advanced_results.keys())
                        st.success(f"✅ 시뮬레이션 완료! ({len(history)}개 프레임) | 🔬 고급: {applied}")
                    else:
                        st.success(f"✅ 시뮬레이션 완료! ({len(history)}개 프레임)")
                    
                except Exception as e:
                    st.error(f"❌ 오류: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())
        
        # 저장된 결과가 있으면 표시
        if 'lem_history' in st.session_state:
            history = st.session_state['lem_history']
            times = st.session_state['lem_times']
            initial_elevation = st.session_state['lem_initial']
            erosion_map = st.session_state['lem_erosion_map']
            drainage_map = st.session_state['lem_drainage_map']
            soil_map = st.session_state.get('lem_soil_map', None)
            weathering_map = st.session_state.get('lem_weathering_map', None)
            saved_total_time = st.session_state['lem_total_time']
            weathering_enabled = st.session_state.get('lem_weathering_enabled', False)
            
            # 결과 표시 (풍화 활성화 시 토양두께 탭 추가)
            if weathering_enabled and soil_map is not None:
                result_tabs = st.tabs(["🗺️ 최종 지형", "📊 비교", "🎬 애니메이션", "📈 침식률", "🪨 토양두께"])
            else:
                result_tabs = st.tabs(["🗺️ 최종 지형", "📊 비교", "🎬 애니메이션", "📈 침식률"])
            
            with result_tabs[0]:
                # 최종 지형 3D (하천 네트워크 포함)
                fig_final = render_terrain_plotly(
                    history[-1],
                    f"최종 지형 ({saved_total_time:,}년 후)",
                    add_water=True,
                    water_level=0,
                    force_camera=False,
                    drainage_area=drainage_map,
                    river_threshold_percentile=95  # 상위 5% 배수면적 = 하천
                )
                st.plotly_chart(fig_final, use_container_width=True)
                st.caption("🌊 파란 점 = 하천 네트워크 (배수면적 상위 5%)")
            
            with result_tabs[1]:
                # 초기 vs 최종 비교
                import matplotlib.pyplot as plt
                
                fig_compare, axes = plt.subplots(1, 2, figsize=(14, 5))
                
                im1 = axes[0].imshow(initial_elevation, cmap='terrain', origin='lower')
                axes[0].set_title("초기 지형")
                plt.colorbar(im1, ax=axes[0], label='고도 (m)')
                
                im2 = axes[1].imshow(history[-1], cmap='terrain', origin='lower')
                axes[1].set_title(f"최종 지형 ({saved_total_time:,}년 후)")
                plt.colorbar(im2, ax=axes[1], label='고도 (m)')
                
                plt.tight_layout()
                st.pyplot(fig_compare)
                plt.close(fig_compare)
                
                # 변화량
                col_m1, col_m2, col_m3 = st.columns(3)
                elev_change = history[-1] - initial_elevation
                col_m1.metric("최대 침식", f"{-elev_change.min():.1f}m")
                col_m2.metric("최대 융기/퇴적", f"{elev_change.max():.1f}m")
                col_m3.metric("평균 고도 변화", f"{elev_change.mean():.1f}m")
            
            with result_tabs[2]:
                # 시간별 애니메이션
                st.markdown("### 🎬 지형 진화 애니메이션")
                
                col_ctrl1, col_ctrl2, col_ctrl3 = st.columns([1, 1, 1])
                
                with col_ctrl1:
                    auto_play = st.checkbox("▶️ 자동 재생", value=False, key="lem_autoplay")
                with col_ctrl2:
                    play_speed = st.slider("재생 속도", 0.1, 2.0, 0.5, key="lem_speed")
                with col_ctrl3:
                    gen_gif = st.button("📥 GIF 생성", key="lem_gif_btn")
                
                # 프레임 슬라이더
                frame_idx = st.slider(
                    "시간 프레임",
                    0, len(history)-1, 
                    st.session_state.get('lem_current_frame', len(history)-1),
                    key="lem_frame_slider"
                )
                
                # 현재 프레임 저장
                st.session_state['lem_current_frame'] = frame_idx
                
                current_time = times[frame_idx]
                
                # 프로그레스 바
                progress = (frame_idx + 1) / len(history)
                st.progress(progress, text=f"⏱️ {current_time:,.0f}년 / {saved_total_time:,.0f}년")
                
                # 3D 지형 표시 (하천 네트워크 포함)
                fig_anim = render_terrain_plotly(
                    history[frame_idx],
                    f"지형 진화 ({current_time:,.0f}년)",
                    add_water=True,
                    water_level=0,
                    force_camera=False,
                    drainage_area=drainage_map,
                    river_threshold_percentile=95
                )
                st.plotly_chart(fig_anim, use_container_width=True, key=f"anim_chart_{frame_idx}")
                
                # 자동 재생 (Streamlit 제한으로 rerun 사용)
                if auto_play and frame_idx < len(history) - 1:
                    import time
                    time.sleep(play_speed)
                    st.session_state['lem_current_frame'] = frame_idx + 1
                    st.rerun()
                elif auto_play and frame_idx >= len(history) - 1:
                    st.session_state['lem_current_frame'] = 0  # 처음으로 돌아가기
                    st.rerun()
                
                # GIF 생성
                if gen_gif:
                    with st.spinner("🎥 GIF 생성 중..."):
                        try:
                            import matplotlib.pyplot as plt
                            from matplotlib import animation
                            import io
                            
                            fig, ax = plt.subplots(figsize=(8, 6))
                            
                            def update(frame):
                                ax.clear()
                                ax.imshow(history[frame], cmap='terrain', origin='lower')
                                ax.set_title(f"{times[frame]:,.0f}년")
                                ax.axis('off')
                            
                            anim = animation.FuncAnimation(fig, update, frames=len(history), interval=200)
                            
                            # GIF 저장
                            gif_path = "lem_animation.gif"
                            anim.save(gif_path, writer='pillow', fps=5)
                            plt.close(fig)
                            
                            with open(gif_path, 'rb') as f:
                                st.download_button(
                                    "📥 GIF 다운로드",
                                    data=f.read(),
                                    file_name="landform_evolution.gif",
                                    mime="image/gif"
                                )
                            st.success("✅ GIF 생성 완료!")
                        except Exception as e:
                            st.error(f"GIF 생성 실패: {e}")
            
            with result_tabs[3]:
                # 침식률 맵
                import matplotlib.pyplot as plt
                
                fig_maps, axes = plt.subplots(1, 2, figsize=(14, 5))
                
                im1 = axes[0].imshow(erosion_map, cmap='Reds', origin='lower')
                axes[0].set_title("침식률 (m/year)")
                plt.colorbar(im1, ax=axes[0])
                
                im2 = axes[1].imshow(drainage_map, cmap='Blues', origin='lower')
                axes[1].set_title("유역면적 (log10)")
                plt.colorbar(im2, ax=axes[1])
                
                plt.tight_layout()
                st.pyplot(fig_maps)
                plt.close(fig_maps)
                
                st.markdown("""
                **해석:**
                - **침식률**: 빨간색이 진할수록 침식이 빠른 곳 (하천)
                - **유역면적**: 파란색이 진할수록 상류 집수 면적이 넓은 곳
                """)
            
            # 토양두께 탭 (풍화 활성화 시에만)
            if weathering_enabled and soil_map is not None:
                with result_tabs[4]:
                    st.markdown("### 🪨 토양 두께 및 풍화율")
                    
                    import matplotlib.pyplot as plt
                    
                    fig_soil, axes = plt.subplots(1, 2, figsize=(14, 5))
                    
                    im1 = axes[0].imshow(soil_map, cmap='YlOrBr', origin='lower')
                    axes[0].set_title(f"토양 두께 (평균: {soil_map.mean():.3f}m)")
                    plt.colorbar(im1, ax=axes[0], label='두께 (m)')
                    
                    im2 = axes[1].imshow(weathering_map, cmap='Greens', origin='lower')
                    axes[1].set_title("풍화율 (m/year)")
                    plt.colorbar(im2, ax=axes[1])
                    
                    plt.tight_layout()
                    st.pyplot(fig_soil)
                    plt.close(fig_soil)
                    
                    col1, col2, col3 = st.columns(3)
                    col1.metric("평균 토양 두께", f"{soil_map.mean():.3f}m")
                    col2.metric("최대 토양 두께", f"{soil_map.max():.3f}m")
                    col3.metric("평균 풍화율", f"{weathering_map.mean():.6f} m/yr")
                    
                    st.markdown("""
                    **해석:**
                    - **토양 두께**: 갈색이 진할수록 토양층(레골리스)이 두꺼운 곳
                    - **풍화율**: 녹색이 진할수록 기반암 → 토양 변환이 빠른 곳
                    - 토양이 두꺼워지면 풍화율이 감소 (지수적 감소)
                    """)
        
        else:
            # 결과 없을 때 안내 표시
            st.info("👈 왼쪽에서 파라미터를 설정하고 **시뮬레이션 실행** 버튼을 누르세요.")
            
            # 예시 이미지/설명
            st.markdown("""
            ### 🔬 이 시뮬레이션으로 할 수 있는 것
            
            1. **침식계수(K) 변화**: 암석 종류에 따른 침식 속도 차이 관찰
            2. **확산계수(D) 변화**: 사면 각도 변화 관찰
            3. **융기율(U) 변화**: 융기와 침식의 균형 → 평형 지형
            4. **시간 증가**: 지형이 어떻게 진화하는지 관찰
            
            ### 💡 추천 실험
            
            | 실험 | K | D | U | 예상 결과 |
            |------|---|---|---|----------|
            | 빠른 침식 | 0.0005 | 0.01 | 0.0003 | 깊은 계곡 형성 |
            | 느린 침식 | 0.00005 | 0.05 | 0.0003 | 완만한 사면 |
            | 융기 우세 | 0.0001 | 0.01 | 0.001 | 산지 높아짐 |
            | 균형 상태 | 0.0001 | 0.01 | 0.0001 | 평형 지형 |
            """)


with tab4:
    st.subheader("📖 도움말")
    
    st.markdown("""
    ### 🌍 지형 시뮬레이션 기능
    
    | 카테고리 | 기능 |
    |----------|------|
    | **침식** | Stream Power, 측방침식, 빙하침식, 해안침식 |
    | **퇴적** | 퇴적물 운반, Exner, 소류사/부유사 |
    | **풍화** | 지수풍화, 동결파쇄, 토양 생성 |
    | **대지형** | 단층, 화산, 등압조절(Isostasy) |
    | **수문** | D8/MFD 유역, Priority Flood, 호수 |
    | **사면** | 확산(4종), 산사태, 사면안정성 |
    | **기후** | 강우이벤트, 기후변화, 해수면 |
    | **인간** | 댐, 삼림벌채 |
    | **해안** | 파랑, 연안류, 해식애 |
    
    ### 사용 가능한 변수 (코드 편집)
    
    | 변수 | 타입 | 설명 |
    |------|------|------|
    | `elevation` | np.ndarray | 고도 배열 (수정 가능) |
    | `bedrock` | np.ndarray | 기반암 배열 |
    | `sediment` | np.ndarray | 퇴적물 배열 |
    | `water_depth` | np.ndarray | 수심 배열 |
    | `np` | module | NumPy 모듈 |
    | `math` | module | math 모듈 |
    
    ### 주의사항
    
    - `import` 문은 사용할 수 없습니다 (보안)
    - `open()`, `exec()`, `eval()` 사용 불가
    - 무한 루프 주의 (브라우저가 멈출 수 있음)
    """)



