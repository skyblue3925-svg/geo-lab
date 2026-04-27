"""
Geo-Lab AI v4.0: 다중 이론 모델 + 사실적 렌더링
각 지형에 대해 여러 이론을 선택하고 비교할 수 있음
"""
import streamlit as st
from app.services.streamlit_compat import image_stretch
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm, colors
from matplotlib.colors import LightSource
import matplotlib.patches as mpatches
import sys
import os
import time
from PIL import Image

# 엔진 임포트
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from engine.pyvista_render import (
        PYVISTA_AVAILABLE, render_v_valley_pyvista, 
        render_delta_pyvista, render_meander_pyvista
    )
    import pyvista as pv
    from stpyvista import stpyvista
    STPYVISTA_AVAILABLE = True
except ImportError:
    PYVISTA_AVAILABLE = False
    STPYVISTA_AVAILABLE = False

# Plotly (인터랙티브 3D)
from app.utils.plotly_compat import go, plotly_error_message
if go is None:
    st.error(plotly_error_message())
    st.stop()

# 통합 물리 엔진 임포트 (Phase 5)
from engine.grid import WorldGrid
from engine.fluids import HydroKernel
from engine.erosion_process import ErosionProcess
from engine.script_engine import ScriptExecutor
from engine.system import EarthSystem
from engine.ideal_landforms import IDEAL_LANDFORM_GENERATORS, ANIMATED_LANDFORM_GENERATORS, create_delta, create_alluvial_fan, create_meander, create_u_valley, create_v_valley, create_barchan_dune, create_coastal_cliff

# 페이지 설정
st.set_page_config(
    page_title="🌊 Geo-Lab AI v4",
    page_icon="🌊",
    layout="wide"
)

# CSS
st.markdown("""
<style>
    .main-header { font-size: 2rem; font-weight: bold; color: #1565C0; }
    .theory-card { 
        background: linear-gradient(135deg, #E3F2FD, #BBDEFB); 
        padding: 1rem; border-radius: 10px; margin: 0.5rem 0;
        border-left: 4px solid #1565C0;
    }
    .formula { 
        font-family: 'Courier New', monospace; 
        background: #263238; color: #80CBC4;
        padding: 0.3rem 0.6rem; border-radius: 4px;
        display: inline-block;
    }
    .theory-title { font-weight: bold; color: #1565C0; font-size: 1.1rem; }
</style>
""", unsafe_allow_html=True)


# ============ 이론 정의 ============

V_VALLEY_THEORIES = {
    "Stream Power Law": {
        "formula": "E = K × A^m × S^n",
        "description": "유량(A)과 경사(S)의 거듭제곱 관계로 침식률 계산. 가장 널리 사용되는 모델.",
        "params": ["K (침식계수)", "m (면적지수, 0.3-0.6)", "n (경사지수, 1.0-2.0)"],
        "key": "stream_power"
    },
    "Shear Stress Model": {
        "formula": "E = K × (τ - τc)^a",
        "description": "하천 바닥의 전단응력(τ)이 임계값(τc)을 초과할 때 침식 발생.",
        "params": ["K (침식계수)", "τc (임계 전단응력)", "a (지수)"],
        "key": "shear_stress"
    },
    "Detachment-Limited": {
        "formula": "E = K × A^m × S^n × (1 - Qs/Qc)",
        "description": "퇴적물 공급량(Qs)이 운반능력(Qc)보다 작을 때만 침식. 암석 분리 속도 제한.",
        "params": ["K (분리계수)", "Qc (운반능력)"],
        "key": "detachment"
    }
}

MEANDER_THEORIES = {
    "Helical Flow (Rozovskii)": {
        "formula": "V_r = (V²/gR) × h",
        "description": "곡류에서 원심력에 의해 나선형 2차류 발생. 바깥쪽 표면류, 안쪽 바닥류.",
        "params": ["V (유속)", "R (곡률반경)", "h (수심)"],
        "key": "helical"
    },
    "Ikeda-Parker-Sawai Model": {
        "formula": "∂η/∂t = E₀ × U × (H/H₀)^α × χ",
        "description": "하안 침식률이 유속(U), 수심(H), 곡률(χ)의 함수. 곡류 진화의 표준 모델.",
        "params": ["E₀ (침식계수)", "H₀ (기준수심)", "α (지수)"],
        "key": "ikeda_parker"
    },
    "Seminara Bar Model": {
        "formula": "λ = β × W × Fr^γ",
        "description": "포인트바 형성과 채널 이동의 결합 모델. 바의 파장(λ)이 채널폭(W)과 Froude수(Fr)에 비례.",
        "params": ["β (비례상수)", "γ (지수)", "Fr (Froude수)"],
        "key": "seminara"
    }
}

DELTA_THEORIES = {
    "Galloway Classification": {
        "formula": "Δ = f(River, Wave, Tidal)",
        "description": "하천·파랑·조류 3가지 에너지 균형으로 삼각주 형태 결정. 가장 널리 사용.",
        "params": ["하천 에너지", "파랑 에너지", "조류 에너지"],
        "key": "galloway"
    },
    "Orton-Reading Model": {
        "formula": "Δ = f(Grain, Wave, Tidal)",
        "description": "퇴적물 입자 크기와 해양 에너지를 고려. 세립질/조립질 삼각주 구분.",
        "params": ["입자크기", "파랑 에너지", "조류 에너지"],
        "key": "orton"
    },
    "Bhattacharya Model": {
        "formula": "Δ = f(Qsed, Hs, Tr)",
        "description": "퇴적물 공급량(Qsed), 유의파고(Hs), 조차(Tr)의 정량적 모델.",
        "params": ["Qsed (퇴적물량)", "Hs (파고)", "Tr (조차)"],
        "key": "bhattacharya"
    }
}

# ===== 해안 지형 이론 =====
COASTAL_THEORIES = {
    "Wave Erosion (Sunamura)": {
        "formula": "E = K × H^a × T^b",
        "description": "파고(H)와 주기(T)에 따른 해식애 침식률. 해식애 후퇴의 기본 모델.",
        "params": ["H (파고)", "T (파 주기)", "K (암석 저항계수)"],
        "key": "wave_erosion"
    },
    "Cliff Retreat Model": {
        "formula": "R = E₀ × (H/Hc)^n",
        "description": "임계파고(Hc) 초과 시 해식애 후퇴. 노치 형성과 붕괴 사이클.",
        "params": ["E₀ (기준 후퇴율)", "Hc (임계파고)", "n (지수)"],
        "key": "cliff_retreat"
    },
    "CERC Transport": {
        "formula": "Q = K × H²{b} × sin(2θ)",
        "description": "연안류에 의한 모래 이동. 사빈, 사취, 사주 형성의 기본 모델.",
        "params": ["H_b (쇄파 파고)", "θ (파향각)", "K (수송계수)"],
        "key": "cerc"
    },
    "Spit & Lagoon": {
        "formula": "Qs = H^2.5 * sin(2α)",
        "description": "연안류에 의해 모래가 곶 끝에서 뻗어나가 사취와 석호 형성.",
        "params": ["연안류 강도", "모래 공급", "파향"],
        "key": "spit"
    },
    "Tombolo": {
        "formula": "Kd = H_diff / H_inc",
        "description": "섬 후면의 파랑 회절로 인한 모래 퇴적. 육계도 형성.",
        "params": ["섬 거리", "파랑 에너지", "섬 크기"],
        "key": "tombolo"
    },
    "Tidal Flat": {
        "formula": "D = C * ws * (1 - τ/τd)",
        "description": "조수 간만의 차로 형성되는 광활한 갯벌.",
        "params": ["조차(Tidal Range)", "퇴적물 농도"],
        "key": "tidal_flat"
    }
}

# ===== 카르스트 지형 이론 =====
KARST_THEORIES = {
    "Chemical Weathering": {
        "formula": "CaCO₃ + H₂O + CO₂ → Ca(HCO₃)₂",
        "description": "탄산칼슘의 화학적 용식. CO₂ 농도와 수온에 따라 용식률 변화.",
        "params": ["CO₂ 농도", "수온", "강수량"],
        "key": "chemical"
    },
    "Doline Evolution": {
        "formula": "V = V₀ × exp(kt)",
        "description": "돌리네의 지수적 성장. 시간에 따라 우발라, 폴리에로 발전.",
        "params": ["초기 크기", "성장률", "병합 확률"],
        "key": "doline"
    },
    "Cave Development": {
        "formula": "D = f(Q, S, t)",
        "description": "지하수 유량(Q)과 경사(S)에 따른 동굴 발달. 종유석/석순 형성.",
        "params": ["지하수 유량", "경사", "석회암 두께"],
        "key": "cave"
    }
}

# ===== 화산 지형 이론 =====
VOLCANIC_THEORIES = {
    "Effusive (Shield)": {
        "formula": "H/R = f(η)",
        "description": "저점성 현무암질 용암. 순상화산(방패 모양) 형성. 하와이, 제주도.",
        "params": ["용암 점성", "분출률", "경사각"],
        "key": "shield"
    },
    "Explosive (Strato)": {
        "formula": "VEI = log₁₀(V)",
        "description": "고점성 안산암/유문암. 성층화산(원추형) 형성. 후지산, 백두산.",
        "params": ["폭발지수(VEI)", "화산재량", "용암/화쇄류 비율"],
        "key": "strato"
    },
    "Caldera Formation": {
        "formula": "D = f(Vmagma)",
        "description": "마그마 방 비움 후 함몰. 칼데라 호수 형성. 백두산 천지.",
        "params": ["마그마 방 크기", "함몰 깊이"],
        "key": "caldera"
    }
}

# ===== 빙하 지형 이론 =====
GLACIAL_THEORIES = {
    "Glacial Erosion": {
        "formula": "E = K × U × H",
        "description": "빙하 이동속도(U)와 두께(H)에 따른 침식. V자곡→U자곡 변형.",
        "params": ["빙하 속도", "빙하 두께", "암석 경도"],
        "key": "erosion"
    },
    "Fjord Development": {
        "formula": "D = E × t + SLR",
        "description": "빙하 침식 후 해수면 상승으로 피오르 형성. 노르웨이 해안.",
        "params": ["침식 깊이", "해수면 상승"],
        "key": "fjord"
    },
    "Moraine Deposition": {
        "formula": "V = f(Qsed, Tmelting)",
        "description": "빙퇴석 퇴적. 분급 불량 퇴적물. 드럼린, 에스커 형성.",
        "params": ["퇴적물량", "융빙 속도"],
        "key": "moraine"
    }
}

# ===== 건조 지형 이론 =====
ARID_THEORIES = {
    "Barchan Dune": {
        "formula": "H = 0.1 × L",
        "description": "초승달 모양 사구. 바람 방향으로 뿔이 향함. 단일 바람 방향.",
        "params": ["풍속", "모래 공급량", "바람 방향"],
        "key": "barchan"
    },
    "Mesa-Butte Evolution": {
        "formula": "R = K × S × t",
        "description": "고원(메사) → 탁상지(뷰트) → 첨탑(스파이어) 침식 단계.",
        "params": ["후퇴율", "경도 차이"],
        "key": "mesa"
    },
    "Pediment Formation": {
        "formula": "S = f(P, R)",
        "description": "산지 기슭의 완만한 암반 평탄면. 페디먼트 + 바하다.",
        "params": ["강수량", "암석 저항"],
        "key": "pediment"
    }
}

# ===== 평야 지형 이론 =====
PLAIN_THEORIES = {
    "Floodplain Development": {
        "formula": "A = f(Q, S, t)",
        "description": "범람원 발달. 자연제방 + 배후습지 형성. 토지 이용 분화.",
        "params": ["유량", "경사", "퇴적물량"],
        "key": "floodplain"
    },
    "Levee-Backswamp": {
        "formula": "H_levee > H_backswamp",
        "description": "자연제방(조립질) vs 배후습지(세립질) 분급. 논/밭 이용.",
        "params": ["퇴적물 분급", "범람 빈도"],
        "key": "levee"
    },
    "Alluvial Plain": {
        "formula": "D = Qsed × t / A",
        "description": "충적평야 형성. 선상지 → 범람원 → 삼각주 연속체.",
        "params": ["퇴적물량", "유역면적"],
        "key": "alluvial"
    }
}


# ============ 시뮬레이션 함수들 ============

@st.cache_data(ttl=3600)
def simulate_v_valley(theory: str, time_years: int, params: dict, grid_size: int = 80):
    """V자곡 시뮬레이션 (Hybrid Approach) - 교과서적인 V자 단면 강제"""
    
    # [Hybrid Approach]
    # 물리 엔진의 불확실성을 제거하고, 완벽한 V자를 보여주기 위해 형태를 강제함.
    
    cell_size = 1000.0 / grid_size
    grid = WorldGrid(width=grid_size, height=grid_size, cell_size=cell_size)
    rows, cols = grid_size, grid_size
    center = cols // 2
    
    # 1. Base Logic: Time-dependent Incision
    # 시간이 지날수록 깊어지고, V자가 선명해짐.
    # U-Valley is U-shaped, V-Valley is V-shaped.
    
    max_depth_possible = 150.0
    # [Fix] Remove offset and scale faster for visualization
    # 50,000 years to reach 50% depth, sat at 200k
    current_depth = max_depth_possible * (1.0 - np.exp(-time_years / 50000.0))
    
    # Rock Hardness affects width/steepness
    rock_h = params.get('rock_hardness', 0.5)
    # Hard rock -> Steep slope (Narrow V)
    # Soft rock -> Gentle slope (Wide V)
    
    valley_width_factor = 0.5 + (1.0 - rock_h) * 1.5 # 0.5(Hard) ~ 2.0(Soft)
    
    # 2. Build Terrain
    for r in range(rows):
        # Longitudinal Profile (Downstream slope)
        base_elev = 250.0 - (r / rows) * 60.0 # 250 -> 190
        grid.bedrock[r, :] = base_elev
        
    grid.update_elevation()
    
    # 3. Carve V-Shape (Analytical)
    x_coords = np.linspace(-500, 500, cols)
    
    for c in range(cols):
        dist_x = abs(c - center) # Distance from river center
        dist_meters = dist_x * cell_size
        
        # --- 탭 구성 ---
    tabs = st.tabs(["🏔️ 지형 시뮬레이션", "📜 스크립트 랩", "🌍 Project Genesis (Unified Engine)"])
    
    # [Tab 1] 기존 시뮬레이터 (Legacy & Refactored)
    with tabs[0]:
        st.title("🏔️ 지형 형성 시뮬레이터 (Geo-Landform Simulator)")
        # ... (Existing content remains here) ...
        # Need to indent existing content or just use 'with tabs[0]:' logic
        # For this tool, I will just INSERT the new tab code at the END of the file or appropriate place.
        # But wait, existing code structure is 'with st.sidebar... if mode == ...'
        # The structure is messy.
        # I should insert the NEW tab logic where tabs are defined.
        
        # Let's verify where tabs are defined.
        # Line 206: tabs = st.tabs(["시뮬레이션", "갤러리", "설정"]) -> Wait, viewed file didn't show this.
        # Let's inspect main.py structure again quickly before editing.
        pass

    # [New Tab Logic Placeholder - Will replace in next step after verifying structure]function: Depth decreases linearly with distance
        # z = z_base - max_depth * (1 - dist / width)
        
        width_m = 400.0 * valley_width_factor
        
        if dist_meters < width_m:
            # Linear V-shape
            incision_ratio = (1.0 - dist_meters / width_m)
            # Make it slightly concave (power 1.2) for realism? Or strict V (power 1)?
            # Textbook is strict V
            incision = current_depth * incision_ratio 
            
            grid.bedrock[:, c] -= incision
            
    # 4. Add Physics Noise (Textures)
    # 하천 바닥에 약간의 불규칙성
    noise = np.random.rand(rows, cols) * 5.0
    grid.bedrock += noise
    
    # Wiggle the river center slightly? (Sinusuosity)
    # V-valleys are usually straight-ish, but let's keep it simple.
    
    grid.update_elevation()
    
    # Calculate stats
    depth = current_depth
    x = np.linspace(0, 1000, cols)
    
    # [Fix] Water Depth
    water_depth = np.zeros_like(grid.elevation)
    # V-valley bottom
    river_w = 8
    water_depth[:, center-river_w:center+river_w+1] = 2.0
    
    return {'elevation': grid.elevation, 'depth': depth, 'x': x, 'water_depth': water_depth}


@st.cache_data(ttl=3600)
def simulate_meander(theory: str, time_years: int, params: dict, grid_size: int = 100):
    """
    자유 곡류 시뮬레이션 (Process-Based)
    - Kinoshita Curve로 경로 생성 -> 3D 지형에 조각(Carving) & 퇴적(Deposition)
    """
    cell_size = 1000.0 / grid_size
    grid = WorldGrid(width=grid_size, height=grid_size, cell_size=cell_size)
    
    # 1. 초기 평야 (Floodplain)
    # 완만한 경사 (서 -> 동 흐름 가정 혹은 남북?)
    # 기존 코드: x축 방향으로 흐름
    rows, cols = grid_size, grid_size
    
    # 기본 고도: 50m
    grid.bedrock[:] = 50.0
    # Add slight slope W->E
    X, Y = np.meshgrid(np.linspace(0, 1000, cols), np.linspace(0, 1000, rows))
    grid.bedrock -= (X / 1000.0) * 5.0 # 5m drop over 1km
    
    # 2. Kinoshita Curve Path Generation (Legacy Logic preserved for path)
    n_points = 1000
    s_vals = np.linspace(0, 20, n_points)
    
    cycle_period = 100000
    cycle_progress = (time_years % cycle_period) / cycle_period
    # Amp grows then cutoff
    max_theta = 2.2
    theta_0 = 0.5 + cycle_progress * (max_theta - 0.5)
    
    flattening = params.get('flattening', 0.2)
    k_wavenumber = 1.0
    
    # Current Path
    theta = theta_0 * np.sin(k_wavenumber * s_vals) + (theta_0 * flattening) * np.sin(3 * k_wavenumber * s_vals)
    dx = np.cos(theta)
    dy = np.sin(theta)
    x_path = np.cumsum(dx)
    y_path = np.cumsum(dy)
    
    # Rotate to flow Left->Right (W->E)
    angle = np.arctan2(y_path[-1] - y_path[0], x_path[-1] - x_path[0])
    target_angle = 0 # X-axis
    rot_angle = target_angle - angle
    
    rot_mat = np.array([[np.cos(rot_angle), -np.sin(rot_angle)],[np.sin(rot_angle), np.cos(rot_angle)]])
    coords = np.vstack([x_path, y_path])
    rotated = rot_mat @ coords
    px = rotated[0, :]
    py = rotated[1, :]
    
    # Normalize to fit Grid (0-1000 with margins)
    margin = 100
    p_width = px.max() - px.min()
    if p_width > 0:
        scale = (1000 - 2*margin) / p_width
        px = (px - px.min()) * scale + margin
        py = py * scale
        py = py - py.mean() + 500 # Center Y
    
    # 3. Process-Based Terrain Modification
    # A. Carve Channel (Subtractive)
    # B. Deposit Point Bar (Additive - Inside Bend)
    # C. Natural Levee (Additive - Banks)
    
    channel_width = 30.0 # m
    channel_depth = 5.0 # m
    levee_height = 1.0 # m
    levee_width = 20.0 # m
    
    # Interpolate path for grid
    # Map grid x,y to distance from channel
    
    # Create distance field simplistic: for each grid point, find dist to curve? Too slow (100x100 * 1000).
    # Faster: Draw curve onto grid mask.
    
    grid.sediment[:] = 5.0 # Soil layer
    
    # Iterate path points and carve
    # Use finer resolution for drawing
    for i in range(n_points):
        cx, cy = px[i], py[i]
        
        # Grid indices
        c_idx = int(cx / cell_size)
        r_idx = int(cy / cell_size)
        
        # Carve circle
        radius_cells = int(channel_width / cell_size / 2) + 1
        
        # Curvature for Point Bar
        # Calculate local curvature
        # kappa = d(theta)/ds approx
        if 0 < i < n_points-1:
            dx_local = px[i+1] - px[i-1]
            dy_local = py[i+1] - py[i-1]
            # Vector along river: (dx, dy)
            # Normal vector (Inside/Outside): (-dy, dx)
            
            # Simple approach: Check neighbors
            for dr in range(-radius_cells*3, radius_cells*3 + 1):
                for dc in range(-radius_cells*3, radius_cells*3 + 1):
                    rr, cc = r_idx + dr, c_idx + dc
                    if 0 <= rr < rows and 0 <= cc < cols:
                        # Physical coord
                        gy = rr * cell_size
                        gx = cc * cell_size
                        dist = np.sqrt((gx - cx)**2 + (gy - cy)**2)
                        
                        if dist < channel_width / 2:
                            # Channel Bed
                            grid.sediment[rr, cc] = 0 # Erode all sediment
                            grid.bedrock[rr, cc] = min(grid.bedrock[rr, cc], 50.0 - (gx/1000.0)*5.0 - channel_depth)
                        
                        elif dist < channel_width / 2 + levee_width:
                            # Levee (Both sides initially)
                            grid.sediment[rr, cc] += levee_height * np.exp(-(dist - channel_width/2)/10.0)
                            
            # Point Bar Deposition: Inner Bend
            # If turning LEFT, Inner is LEFT.
            # Local curvature check required.
            # Or just use pre-calc theta?
            pass

    # [Fix] To make it smooth, use diffusion
    erosion = ErosionProcess(grid)
    erosion.hillslope_diffusion(dt=1.0)
    
    # [Fix] Water Depth
    # Fill channel using HydroKernel (Physics Flow)
    grid.update_elevation()
    
    # Add flow source at start of path
    # Find start point (min X)
    start_idx = np.argmin(px)
    sx, sy = px[start_idx], py[start_idx]
    sr, sc = int(sy/cell_size), int(sx/cell_size)
    
    precip = np.zeros((rows, cols))
    if 0 <= sr < rows and 0 <= sc < cols:
        precip[sr-2:sr+3, sc-2:sc+3] = 20.0 # Source
    
    # Also some rain mapping to channel?
    # Route flow
    hydro = HydroKernel(grid)
    discharge = hydro.route_flow_d8(precipitation=precip)
    
    # Map to depth
    water_depth = np.log1p(discharge) * 0.5
    water_depth[water_depth < 0.1] = 0

    # Calculate sinuosity for UI
    path_len = np.sum(np.sqrt(np.diff(px)**2 + np.diff(py)**2))
    straight = np.sqrt((px[-1]-px[0])**2 + (py[-1]-py[0])**2) + 0.01
    sinuosity = path_len / straight
    
    return {
        'elevation': grid.elevation, 
        'water_depth': water_depth,
        'sinuosity': sinuosity,
        'oxbow_lakes': [] # TODO: Implement Oxbow in grid
    }


@st.cache_data(ttl=3600)
def simulate_delta(theory: str, time_years: int, params: dict, grid_size: int = 100):
    """
    삼각주 시뮬레이션 (Process-Based)
    - 하천이 바다로 유입 -> 유속 감소 -> 퇴적 -> 해안선 전진(Progradation) -> 유로 변경(Avulsion)
    """
    cell_size = 1000.0 / grid_size
    grid = WorldGrid(width=grid_size, height=grid_size, cell_size=cell_size, sea_level=0.0)
    
    rows, cols = grid_size, grid_size
    
    # 1. 초기 지형
    # Land (Top) -> Sea (Bottom)
    # 완만한 경사
    center = cols // 2
    
    # Bedrock Slope
    # Row 0: +20m -> Row 100: -20m
    Y, X = np.meshgrid(np.linspace(0, 1000, cols), np.linspace(0, 1000, rows))
    grid.bedrock = 20.0 - (Y / 1000.0) * 40.0
    
    # Pre-carve a slight valley upstream to guide initial flow
    for r in range(rows // 3):
        for c in range(cols):
            dist = abs(c - center)
            if dist < 10:
                grid.bedrock[r, c] -= 2.0 * (1.0 - dist/10.0)
                
    grid.update_elevation()
    
    # 2. 물리 엔진
    hydro = HydroKernel(grid)
    erosion = ErosionProcess(grid, K=0.02, m=1.0, n=1.0)
    
    # 파라미터
    river_flux = params.get('river', 0.5) * 200.0 # Sediment input
    wave_energy = params.get('wave', 0.5)
    
    # Delta Type Logic (Process-based modulation)
    # Wave energy high -> Diffusion high -> Arcuate / Smooth Coast
    # Wave energy low -> Diffusion low -> Bird's Foot
    diffusion_rate = 0.01 + wave_energy * 0.1
    
    steps = max(50, min(time_years // 100, 300))
    dt = 1.0
    
    # 3. 시뮬레이션 루프
    for i in range(steps):
        # 강수 (상류 유입)
        precip = np.zeros((rows, cols))
        precip[0:2, center-2:center+3] = 20.0
        
        # Flow
        discharge = hydro.route_flow_d8(precipitation=precip)
        
        # Sediment Inflow at top
        grid.sediment[0:2, center-2:center+3] += river_flux * 0.1 * dt
        
        # Transport & Deposit
        erosion.simulate_transport(discharge, dt=dt)
        
        # Wave Action (Diffusion)
        # 해안선 근처에서 확산이 일어남
        # Hillslope diffusion approximates wave smoothing
        erosion.hillslope_diffusion(dt=dt * diffusion_rate * 100.0)
        
        grid.update_elevation()
        
    # 4. 결과 정리
    # Water Depth Calculation
    # Sea Depth (flat) vs River Depth (flow)
    
    # Recalculate final flow
    precip_final = np.zeros((rows, cols))
    precip_final[0:2, center-2:center+3] = 10.0
    discharge_final = hydro.route_flow_d8(precipitation=precip_final)
    
    # 1. Sea Water
    water_depth = np.zeros_like(grid.elevation)
    sea_mask = grid.elevation < 0
    water_depth[sea_mask] = -grid.elevation[sea_mask]
    
    # 2. River Water
    river_depth = np.log1p(discharge_final) * 0.5
    land_mask = grid.elevation >= 0
    
    # Combine (On land, show river. At sea, show sea depth)
    water_depth[land_mask] = river_depth[land_mask]
    
    # Calculate Metrics
    # Area: Sediment accumulated above sea level (approx)
    # Exclude initial land (bedrock > 0)
    delta_mask = (grid.elevation > 0) & (grid.bedrock < 0)
    area = np.sum(delta_mask) * (cell_size**2) / 1e6
    
    # Determine Type for UI display
    if wave_energy > 0.6:
        delta_type = "원호상 (Arcuate)"
    elif river_flux > 300 and wave_energy < 0.3:
         delta_type = "조족상 (Bird's Foot)"
    else:
         delta_type = "혼합형 (Mixed)"
    
    return {'elevation': grid.elevation, 'water_depth': water_depth, 'area': area, 'delta_type': delta_type}


@st.cache_data(ttl=3600)
def simulate_coastal(theory: str, time_years: int, params: dict, grid_size: int = 100):
    """해안 지형 시뮬레이션 (물리 엔진 적용)"""
    
    # 1. 그리드 초기화 (Headland & Bay)
    cell_size = 1000.0 / grid_size
    grid = WorldGrid(width=grid_size, height=grid_size, cell_size=cell_size)
    rows, cols = grid_size, grid_size
    
    # 기본: 깊은 바다 -> 얕은 바다 -> 육지 (Y축 방향)
    for r in range(rows):
        # Y=0(Deep Ocean) -> Y=100(Land)
        base_elev = (r / rows) * 60.0 - 20.0 # -20m ~ +40m
        grid.bedrock[r, :] = base_elev
        
    # 곶 (Headland) 돌출
    # 중앙 부분은 해안선이 바다(Y=low) 쪽으로 튀어나옴
    center = cols // 2
    headland_width = cols // 3
    for c in range(cols):
        dist = abs(c - center)
        if dist < headland_width:
            # 돌출부 추가 높이
            protrusion = (1.0 - dist/headland_width) * 40.0
            # 바다 쪽으로 연장
            grid.bedrock[:, c] += protrusion * 0.5 # 전체적으로 높임
            
            # 앞부분을 더 바다로
            for r in range(rows):
                if r < rows // 2: # 바다 쪽 절반
                     grid.bedrock[r, c] += protrusion * (1.0 - r/(rows//2))

    # 랜덤 노이즈
    np.random.seed(42)
    grid.bedrock += np.random.rand(rows, cols) * 2.0
    grid.update_elevation()
    
    # 2. 엔진
    erosion = ErosionProcess(grid, K=0.01)
    
    steps = 100
    wave_height = params.get('wave_height', 2.0)
    rock_resistance = params.get('rock_resistance', 0.5)
    
    # 파랑 에너지 계수 (암석 저항 반대)
    erodibility = (1.0 - rock_resistance) * 0.2
    
    result_type = "해식애 & 파식대"
    
    for i in range(steps):
        # [Hybrid Approach]
        # 교과서적인 해식애(Sea Cliff)와 파식대(Wave-cut Platform) 강제
        
        # 1. Retreat Cliff
        # Amount of retreat proportional to step
        retreat_dist = min(30, i * 0.5)
        
        # Current Cliff Position (roughly)
        # Original Headland was centered at Y=50 (approx)
        # We push Y back based on X (Headland shape)
        
        # Platform mask (Area eroded)
        # Headland (center cols) retreats faster? No, wave focuses on headland.
        
        # Define Cliff Line
        for c in range(cols):
             dist = abs(c - center)
             if dist < headland_width:
                 # Original protrusion extent
                 orig_y = 50 + (1.0 - dist/headland_width) * 40.0
                 
                 # Current cliff y (Retreating)
                 # fast retreat at tip
                 retreat_local = retreat_dist * (1.0 + (1.0 - dist/headland_width))
                 current_y = orig_y - retreat_local
                 current_y = max(current_y, 20.0) # Limit
                 
                 # Apply Profile
                 # Platform (Low, flat) below current_y
                 # Cliff (Steep) at current_y
                 
                 # Platform level: -10 ~ 0 approx
                 # Carve everything sea-side of current_y down to platform level
                 
                 for r in range(rows):
                     if r < current_y:
                         # Platform
                         target_h = -5.0 + (r/100.0)*2.0 
                         if grid.bedrock[r, c] > target_h:
                             grid.bedrock[r, c] = target_h
                     else:
                         # Cliff face or Land
                         # Keep heavy
                         pass
                         
        # 2. Physics detail (Stacks/Arches?)
        # Leave some random columns (Stacks) on the platform
        if i == steps - 1:
            # Random Stacks
            stack_prob = 0.02
            noise = np.random.rand(rows, cols)
            platform_mask = (grid.bedrock < 0) & (grid.bedrock > -10)
            grid.bedrock[platform_mask & (noise < stack_prob)] += 30.0 # Stacks
            
    result_type = "해식애 & 파식대 & 시스택"
        

        
    return {
        'elevation': grid.elevation,
        'type': result_type,
        'cliff_retreat': 0, 'platform_width': 0, 'notch_depth': 0
    }



@st.cache_data(ttl=3600)
def simulate_coastal_deposition(theory: str, time_years: int, params: dict, grid_size: int = 100):
    """해안 퇴적 지형 시뮬레이션 - 사취, 육계도, 갯벌"""
    x = np.linspace(0, 1000, grid_size)
    y = np.linspace(0, 1000, grid_size)
    X, Y = np.meshgrid(x, y)
    elevation = np.zeros((grid_size, grid_size))
    
    dt = 100
    steps = max(1, time_years // dt)
    
    # 공통: 해수면 0m 기준
    
    if theory == "spit":
        # 사취 & 석호: 꺾인 해안선에서 모래가 연장됨
        # 초기 지형: 왼쪽은 육지, 오른쪽은 만(Bay)
        # 만의 입구: X=300 지점
        coast_y = 200
        
        # 육지 기본
        land_mask = (X < 300) & (Y > coast_y) # 왼쪽 해안
        elevation[land_mask] = 10
        
        # 만의 안쪽 (오른쪽 깊숙한 곳)
        bay_coast_y = 600
        bay_mask = (X >= 300) & (Y > bay_coast_y)
        elevation[bay_mask] = 10
        
        # 바다 (점진적 깊어짐)
        sea_mask = elevation == 0
        elevation[sea_mask] = -10 - (Y[sea_mask]/1000)*10
        
        # 사취 성장 (왼쪽 곶에서 오른쪽으로)
        growth_rate = params.get('drift_strength', 0.5) * 5
        spit_len = min(600, steps * growth_rate)
        
        # 사취 형성 (X: 300 -> 300+len)
        spit_width = 30 + params.get('sand_supply', 0.5) * 20
        
        spit_mask = (X >= 300) & (X < 300 + spit_len) & (Y > coast_y - spit_width/2) & (Y < coast_y + spit_width/2)
        
        # 끝부분은 뭉툭하게/휘어지게 (Hook)
        if spit_len > 100:
            hook_x = 300 + spit_len
            hook_mask = (X > hook_x - 50) & (X < hook_x) & (Y > coast_y) & (Y < coast_y + 100)
            # 파향에 따라 휘어짐
            if params.get('wave_angle', 45) > 30:
                 elevation[hook_mask & (elevation < 0)] = 2
        
        elevation[spit_mask] = 3 # 해수면 위로 드러남
        
        # 석호 형성 여부 (사취가 만을 막았는지)
        lagoon_closed = spit_len > 600
        
        result_type = "사취 (Spit)"
        if lagoon_closed: result_type += " & 석호 (Lagoon)"
        
    elif theory == "tombolo":
        # 육계도: 육지 + 섬 + 사주
        coast_y = 200
        
        # 육지
        elevation[Y < coast_y] = 10
        elevation[Y >= coast_y] = -15 # 바다
        
        # 섬 (중앙에 위치)
        island_dist = 300 + params.get('island_dist', 0.5) * 300 # 300~600m
        island_y = coast_y + island_dist
        island_r = 80 + params.get('island_size', 0.5) * 50
        
        dist_from_island = np.sqrt((X-500)**2 + (Y-island_y)**2)
        island_mask = dist_from_island < island_r
        elevation[island_mask] = 30 * np.exp(-dist_from_island[island_mask]**2 / (island_r/2)**2)
        
        # 육계사주 (Tombolo) 성장
        # 파랑이 섬 뒤쪽으로 회절되어 퇴적
        # 육지(200)와 섬(island_y) 사이 이어짐
        
        connect_factor = min(1.0, steps * params.get('wave_energy', 0.5) * 0.05)
        
        # 모래톱 (X=500 중심)
        bar_width = 40 + connect_factor * 100
        bar_mask = (X > 500 - bar_width/2) & (X < 500 + bar_width/2) & (Y >= coast_y) & (Y <= island_y)
        
        # 모래톱 높이: 서서히 올라옴
        target_height = 2 # 해수면보다 약간 높음
        current_bar_h = -5 + connect_factor * 7
        
        elevation[bar_mask] = np.maximum(elevation[bar_mask], current_bar_h)
        
        result_type = "육계도 (Tombolo)" if current_bar_h > 0 else "육계사주 형성 중"
        
    elif theory == "tidal_flat":
        # 갯벌: 완만한 경사 + 조수 골 (Tidal Creek)
        # 매우 완만한 경사
        slope = 0.005
        elevation = 5 - Y * slope # Y=0: 5m -> Y=1000: 0m ...
        
        # 조차 (Tidal Range)
        tidal_range = params.get('tidal_range', 3.0) # 0.5 ~ 6m
        high_tide = tidal_range / 2
        low_tide = -tidal_range / 2
        
        # 갯벌 영역: High Tide와 Low Tide 사이
        flat_mask = (elevation < high_tide) & (elevation > low_tide)
        
        # 갯벌 골 (Meandering Creeks)
        # 프랙탈 수로
        n_creeks = 3
        for i in range(n_creeks):
            cx = 200 + i * 300
            cy = np.linspace(200, 1000, 200)
            
            # 수로 굴곡
            cx_curve = cx + 50 * np.sin(cy * 0.02) + np.random.normal(0, 5, 200)
            
            for j, y_pos in enumerate(cy):
                iy = int(y_pos * grid_size / 1000)
                ix = int(cx_curve[j] * grid_size / 1000)
                if 0 <= iy < grid_size and 0 <= ix < grid_size:
                    # 수로 깊이
                    depth = 2 + (y_pos/1000) * 3 # 바다 쪽으로 갈수록 깊어짐
                    elevation[iy, max(0,ix-3):min(grid_size,ix+4)] -= depth
        
        result_type = "갯벌 (Tidal Flat)"
        
    else:
        result_type = "해안 지형"
        
    return {
        'elevation': elevation,
        'type': result_type,
        'cliff_retreat': 0, 'platform_width': 0, 'notch_depth': 0
    }


@st.cache_data(ttl=3600)
def simulate_alluvial_fan(time_years: int, params: dict, grid_size: int = 100):
    """
    선상지 시뮬레이션 (Project Genesis Unified Engine)
    - 통합 엔진(EarthSystem)을 사용하여 자연스러운 선상지 형성 과정 재현
    - 상류 산지 -> 급경사 변환부(Apex) -> 평지 확산
    """
    cell_size = 1000.0 / grid_size
    grid = WorldGrid(width=grid_size, height=grid_size, cell_size=cell_size)
    
    rows, cols = grid_size, grid_size
    center = cols // 2
    apex_row = int(rows * 0.2)
    
    # 1. 초기 지형 설정 (Scenario Setup)
    # A. Mountain Zone (Steep)
    for r in range(apex_row):
        # 100m -> 50m drop
        grid.bedrock[r, :] = 100.0 - (r / apex_row) * 50.0 
        
    # B. Plain Zone (Flat)
    # 50m -> 40m (Very gentle slope)
    for r in range(apex_row, rows):
        grid.bedrock[r, :] = 50.0 - ((r - apex_row) / (rows - apex_row)) * 10.0
        
    # C. Canyon Carving (Channel in Mountain)
    for r in range(apex_row + 5): # Extend slightly beyond apex
        for c in range(cols):
            dist = abs(c - center)
            width = 3 + (r / apex_row) * 5
            if dist < width:
                # V-shape cut
                depth = 10.0 * (1.0 - dist/width)
                grid.bedrock[r, c] -= depth

    # Add random noise
    np.random.seed(42)
    grid.bedrock += np.random.rand(rows, cols) * 1.0
    grid.update_elevation()
    
    # 2. 통합 엔진 초기화 (Unified Engine)
    engine = EarthSystem(grid)
    
    # 3. 시뮬레이션 설정 (Config)
    # K값을 낮춰서 운반 능력(Capacity)을 줄임 -> 평지에서 퇴적 유도
    engine.erosion.K = 0.005 
    
    steps = max(50, min(time_years // 100, 200))
    sediment_supply = params.get('sediment', 0.5) * 1000.0 # 퇴적물 공급량 대폭 증가
    
    # Settings for the Engine
    settings = {
        'precipitation': 0.0,
        'rain_source': (0, center, 5, 50.0), # 강수량 증가
        'sediment_source': (apex_row, center, 2, sediment_supply), 
        'diffusion_rate': 0.1 # 확산 활성화 (부채꼴 형성 도움)
    }
    
    # 4. 엔진 구동 (The Loop)
    for i in range(steps):
        engine.step(dt=1.0, settings=settings)
        
    # 5. 결과 반환
    engine.get_state() # Update grid state one last time
    
    # Calculate metrics
    fan_mask = grid.sediment > 1.0
    area = np.sum(fan_mask) * (cell_size**2) / 1e6
    radius = np.sqrt(area * 1e6 / np.pi) * 2 if area > 0 else 0
    
    # Debug Info
    sed_max = grid.sediment.max()
    
    return {
        'elevation': grid.elevation,
        'water_depth': grid.water_depth,
        'sediment': grid.sediment, # Explicit return for visualization
        'area': area,
        'radius': radius,
        'debug_sed_max': sed_max,
        'debug_steps': steps
    }


@st.cache_data(ttl=3600)
def simulate_river_terrace(time_years: int, params: dict, grid_size: int = 100):
    """하안단구 시뮬레이션 (물리 엔진 적용)"""
    # 1. 그리드 초기화 (V자곡 유사)
    cell_size = 1000.0 / grid_size
    grid = WorldGrid(width=grid_size, height=grid_size, cell_size=cell_size)
    
    rows, cols = grid_size, grid_size
    center = cols // 2
    
    # 초기: 넓은 범람원이 있는 U자곡 형태
    for r in range(rows):
        grid.bedrock[r, :] = 150.0 - (r/rows)*20.0 # 완만한 하류 경사
    
    for c in range(cols):
        dist = abs(c - center)
        # 넓은 하곡 (200m)
        if dist < 100:
            grid.bedrock[:, c] -= 20.0
        else:
            # 양쪽 언덕
            grid.bedrock[:, c] += (dist - 100) * 0.2
            
    grid.update_elevation()
    
    hydro = HydroKernel(grid)
    erosion = ErosionProcess(grid, K=0.001)
    
    uplift_rate = params.get('uplift', 0.5) * 0.1 # 융기 속도
    n_terraces = int(params.get('n_terraces', 3))
    
    # 사이클 계산
    # 평형 상태(범람원 형성) -> 융기(하각) -> 평형(새 범람원)
    total_cycles = n_terraces
    current_time = 0
    terrace_heights = []
    
    # [Optimization] Performance Cap
    # Avoid excessive loops if time_years is large
    raw_duration = max(20, time_years // total_cycles)
    max_duration_per_cycle = 50 # Fixed physics steps per cycle
    
    # Scale physics parameters to match time scaling
    time_scale = raw_duration / max_duration_per_cycle
    dt = 1.0 * time_scale # Increase time step
    
    # [Hybrid Approach]
    # 교과서적인 하안단구(Stairs) 형태 강제 + 애니메이션 지원
    
    # 1. Base U-Valley (Already initialized)
    
    # 2. Determine Progress based on Time
    # Assume 1 Terrace takes 20,000 years to form fully (Uplift + Incision)
    years_per_cycle = 20000 
    
    # Calculate how many cycles are completed at current time
    cycle_progress_float = time_years / years_per_cycle
    
    completed_cycles = int(cycle_progress_float)
    current_fraction = cycle_progress_float - completed_cycles
    
    # Cap at n_terraces
    if completed_cycles > n_terraces:
        completed_cycles = n_terraces
        current_fraction = 0.0
        
    if completed_cycles == n_terraces:
        current_fraction = 0.0 # Fully done
        
    level_step = 20.0 
    
    # 3. Simulate Logic
    # Run fully completed cycles first
    for cycle in range(completed_cycles):
        if cycle >= n_terraces: break
        
        # A. Uplift (Full)
        grid.bedrock += 10.0 * uplift_rate
        
        # B. Incision (Full)
        current_width = 100 - cycle * 20
        for c in range(cols):
            dist = abs(c - center)
            if dist < current_width:
                 grid.bedrock[:, c] -= 15.0
                 
        # Record height
        mid_elev = grid.bedrock[rows//2, center]
        terrace_heights.append(mid_elev)
        
    # Run current partial cycle (Animation effect)
    if completed_cycles < n_terraces:
        cycle = completed_cycles
        
        # A. Partial Uplift
        # Uplift happens gradually or triggered?
        # Let's say Uplift scales with fraction
        grid.bedrock += 10.0 * uplift_rate * current_fraction
        
        # B. Partial Incision (Depth or Width?)
        # Incision depth scales with fraction
        current_width = 100 - cycle * 20
        incision_depth = 15.0 * current_fraction
        
        for c in range(cols):
            dist = abs(c - center)
            if dist < current_width:
                 grid.bedrock[:, c] -= incision_depth

    # C. Smoothing (Physics Texture)
    erosion.hillslope_diffusion(dt=5.0)
    
    # [Fix] Water Depth
    water_depth = np.zeros_like(grid.elevation)
    center_c = cols // 2
    # Determine current river width at bottom
    # Just use a visual width
    river_w = 10
    water_depth[:, center_c-river_w:center_c+river_w] = 5.0
    
    return {'elevation': grid.elevation, 'n_terraces': n_terraces, 'heights': terrace_heights, 'water_depth': water_depth}


@st.cache_data(ttl=3600)
def simulate_stream_piracy(time_years: int, params: dict, grid_size: int = 100):
    """하천쟁탈 시뮬레이션 - 교과서적 이상적 모습"""
    
    x = np.linspace(0, 1000, grid_size)
    y = np.linspace(0, 1000, grid_size)
    X, Y = np.meshgrid(x, y)
    
    # 기본 지형: 경사면 (상류가 높음)
    elevation = 150 - Y * 0.1
    
    # 분수령 (두 하천 사이의 능선)
    ridge_x = 500
    ridge = 20 * np.exp(-((X - ridge_x)**2) / (80**2))
    elevation += ridge
    
    # 하천 계곡 형성
    # 피탈하천 (좌측, 약한 침식력) - Y방향으로 흐름
    river1_x = 300
    river1_valley = 30 * np.exp(-((X - river1_x)**2) / (40**2))
    elevation -= river1_valley
    
    # 쟁탈하천 (우측, 강한 침식력) - 더 깊은 계곡
    river2_x = 700
    erosion_diff = params.get('erosion_diff', 0.7)
    river2_depth = 50 * erosion_diff
    river2_valley = river2_depth * np.exp(-((X - river2_x)**2) / (50**2))
    elevation -= river2_valley
    
    dt = 100
    steps = max(1, time_years // dt)
    
    captured = False
    capture_time = 0
    elbow_point = None
    
    # 두부침식 진행 (Process Visualization)
    headcut_progress = min(steps * erosion_diff * 3, 200)  # 최대 200m 진행
    
    # 쟁탈 전이라도 침식곡이 분수령 쪽으로 파고드는 과정 시각화
    # 쟁탈하천(river2)에서 분수령(ridge) 쪽으로 침식 진행
    # River2 X=700 -> Ridge X=500. Headcut moves Left.
    current_head_x = river2_x - headcut_progress # 700 - progress
    
    # 침식 채널 생성 (Progressive Channel)
    # 700에서 current_head_x까지 파냄
    if headcut_progress > 0:
        # Y 위치는 400 (elbow_point 예정지)
        erosion_y = 400
        # X range: current_head_x ~ 700
        
        # Grid iterate or vector ops? Vector ops easier.
        # Create a channel mask
        channel_len = headcut_progress
        # Gaussian profile along Y, Linear along X?
        
        # X: current_head_x to 700
        # We carve a path
        eroding_mask_x = (X > current_head_x) & (X < 700)
        eroding_mask_y = np.abs(Y - erosion_y) < 30
        
        # Depth tapers at the head
        dist_from_start = (700 - X)
        depth_profile = river2_depth * 0.8 # Base depth
        
        # Apply erosion
        mask = eroding_mask_x & eroding_mask_y
        elevation[mask] -= depth_profile * np.exp(-(Y[mask]-erosion_y)**2 / 20**2)
    
    if headcut_progress > 150:  # 분수령을 넘어 쟁탈 발생 (150m is dist to ridge zone)
        captured = True
        capture_time = int(150 / (erosion_diff * 3) * dt)
        elbow_point = (ridge_x - 50, 400)  # 굴곡점 위치
        
        # 쟁탈 후 지형 변화 (완전 연결)
        # 1. 쟁탈하천이 분수령을 파고 피탈하천 상류와 연결
        # Already partially done by progressive erosion, but let's connect fully
        capture_zone_x = np.linspace(river1_x, current_head_x, 50) # Connect remaining gap
        capture_zone_y = 400
        for cx in capture_zone_x:
            mask = ((X - cx)**2 + (Y - capture_zone_y)**2) < 30**2
            elevation[mask] -= river2_depth * 0.8
        
        # 2. 피탈하천 상류 → 쟁탈하천으로 유입 (직각 굴곡)
        for j in range(grid_size):
            if Y[j, 0] < capture_zone_y:  # 상류 부분
                # 피탈하천 상류는 그대로
                pass
            else:  # 하류 부분 - 유량 감소로 얕아짐
                mask = np.abs(X[j, :] - river1_x) < 40
                elevation[j, mask] += 15  # 풍갭 형성 (건천화)
        
        # 3. 풍갭 표시 (마른 계곡)
        wind_gap_y = capture_zone_y + 50
        wind_gap_mask = (np.abs(X - river1_x) < 30) & (np.abs(Y - wind_gap_y) < 50)
        elevation[wind_gap_mask] = elevation[wind_gap_mask].mean()  # 평탄화
    
    # [Fix] Water Depth Calculation for Visualization
    water_depth = np.zeros_like(elevation)
    
    # 1. River 2 (Capturing Stream) - Always flowing
    # Valley mask
    # X > 550, Y > 0. Roughly.
    # Actually use analytic distance check
    dist_r2 = np.abs(X - river2_x)
    # Head ward erosion channel
    head_mask = (X > current_head_x) & (X < 700) & (np.abs(Y - 400) < 20)
    
    r2_mask = (dist_r2 < 40) | head_mask
    water_depth[r2_mask] = 3.0 # Deep water
    
    # 2. River 1 (Victim Stream)
    if not captured:
        # Full flow
        dist_r1 = np.abs(X - river1_x)
        r1_mask = dist_r1 < 30
        water_depth[r1_mask] = 3.0
    else:
        # Captured!
        capture_y = 400
        # Upstream (Y < capture_y) -> Flows to River 2
        # Connect to R2
        dist_r1_upper = np.abs(X - river1_x)
        r1_upper_mask = (dist_r1_upper < 30) & (Y < capture_y)
        water_depth[r1_upper_mask] = 3.0
        
        # Connection channel
        conn_mask = (X > river1_x) & (X < current_head_x) & (np.abs(Y - capture_y) < 20)
        water_depth[conn_mask] = 3.0
        
        # Downstream (Y > capture_y) -> Dry (Wind Gap)
        # Maybe small misfit stream?
        dist_r1_lower = np.abs(X - river1_x)
        r1_lower_mask = (dist_r1_lower < 20) & (Y > capture_y + 50) # Skip wind gap
        water_depth[r1_lower_mask] = 0.5 # Misfit stream (shallow)
    
    
    return {
        'elevation': elevation, 
        'captured': captured, 
        'capture_time': capture_time if captured else None,
        'elbow_point': elbow_point,
        'water_depth': water_depth
    }


@st.cache_data(ttl=3600)
def simulate_entrenched_meander(time_years: int, params: dict, grid_size: int = 100):
    """
    감입 곡류 시뮬레이션 (Process-Based)
    - Kinoshita Curve로 곡류 형성 -> 지반 융기 -> 하방 침식(Incision)
    """
    cell_size = 1000.0 / grid_size
    grid = WorldGrid(width=grid_size, height=grid_size, cell_size=cell_size)
    rows, cols = grid_size, grid_size
    
    # 1. 초기 지형 및 경로 생성 (Kinoshita Curve - simulate_meander와 동일 로직)
    # 융기 전의 평탄한 범람원
    grid.bedrock[:] = 50.0 
    
    # Kinoshita Path Generation
    n_points = 1000
    s = np.linspace(0, 20, n_points)
    
    # 성숙한 곡류 (High amplitude)
    theta_0 = 1.8 
    flattening = 0.2
    
    theta = theta_0 * np.sin(s) + (theta_0 * flattening) * np.sin(3 * s)
    dx = np.cos(theta)
    dy = np.sin(theta)
    x = np.cumsum(dx)
    y = np.cumsum(dy)
    
    # Rotate & Scale
    angle = np.arctan2(y[-1] - y[0], x[-1] - x[0])
    rot_mat = np.array([[np.cos(-angle), -np.sin(-angle)],[np.sin(-angle), np.cos(-angle)]])
    coords = np.vstack([x, y])
    rotated = rot_mat @ coords
    px = rotated[0, :]
    py = rotated[1, :]
    
    # Normalize
    margin = 100
    p_width = px.max() - px.min()
    if p_width > 0:
        scale = (1000 - 2*margin) / p_width
        px = (px - px.min()) * scale + margin
        py = py * scale
        py = py - py.mean() + 500
        
    # Slope terrain along X (since we rotated current to X-axis in Kinoshita logic above)
    # Check px direction. px increases index 0->end.
    # So Flow is West -> East (Left -> Right).
    # Add Slope W->E
    Y, X = np.meshgrid(np.linspace(0, 1000, rows), np.linspace(0, 1000, cols))
    grid.bedrock[:] = 50.0  - (X / 1000.0) * 10.0 # 10m drop
    
    # 2. 하천 경로 마스크 생성
    river_mask = np.zeros((rows, cols), dtype=bool)
    channel_width = 30.0 # m
    
    # Draw channel
    # Pre-calculate cells in channel to speed up loop
    for k in range(n_points):
        cx, cy = px[k], py[k]
        c_idx = int(cx / cell_size)
        r_idx = int(cy / cell_size)
        
        radius_cells = int(channel_width / cell_size / 2) + 1
        for dr in range(-radius_cells, radius_cells + 1):
            for dc in range(-radius_cells, radius_cells + 1):
                rr, cc = r_idx + dr, c_idx + dc
                if 0 <= rr < rows and 0 <= cc < cols:
                     dist = np.sqrt((rr*cell_size - cy)**2 + (cc*cell_size - cx)**2)
                     if dist < channel_width/2:
                         river_mask[rr, cc] = True
                         
    # 3. 융기 및 침식 시뮬레이션
    uplift_rate = params.get('uplift', 0.5) * 0.01 # m/year -> scale down for sim step
    incision_power = 1.2 # 침식력이 융기보다 강해야 파임
    
    steps = max(50, min(time_years // 100, 300))
    dt = 10.0
    
    incision_type = params.get('incision_type', 'U') # U (Ingrown) or V (Entrenched)

    for i in range(steps):
        # Uplift entire terrain
        grid.bedrock += uplift_rate * dt
        # Maintain slope? Uplift is uniform. Slope is preserved.
        
        # Channel Incision (Erosion)
        current_incision = uplift_rate * dt * incision_power
        
        # Apply incision to channel
        grid.bedrock[river_mask] -= current_incision
        
        # Slope Evolution (Diffusion)
        diff_k = 0.01 if incision_type == 'V' else 0.05
        grid.update_elevation()
        erosion = ErosionProcess(grid) 
        erosion.hillslope_diffusion(dt=dt * diff_k)
        
    # 4. 결과 정리
    grid.update_elevation()
    
    # Calculate depth
    max_elev = grid.elevation.max()
    min_elev = grid.elevation[river_mask].mean()
    depth = max_elev - min_elev
    
    type_name = "착근 곡류 (Ingrown)" if incision_type == 'U' else "감입 곡류 (Entrenched)"
    
    # [Fix] Water Depth using HydroKernel
    # Add source at left
    precip = np.zeros((rows, cols))
    # Find start
    start_idx = np.argmin(px)
    sx, sy = px[start_idx], py[start_idx]
    sr, sc = int(sy/cell_size), int(sx/cell_size)
    if 0 <= sr < rows and 0 <= sc < cols:
         precip[sr-2:sr+3, sc-2:sc+3] = 50.0
         
    hydro = HydroKernel(grid)
    discharge = hydro.route_flow_d8(precipitation=precip)
    water_depth = np.log1p(discharge) * 0.5
    water_depth[water_depth < 0.1] = 0
    
    return {'elevation': grid.elevation, 'depth': depth, 'type': type_name, 'water_depth': water_depth}


@st.cache_data(ttl=3600)
def simulate_waterfall(time_years: int, params: dict, grid_size: int = 100):
    """
    폭포 시뮬레이션 (Process-Based)
    - 두부 침식(Headward Erosion) 원리 구현
    - 급경사(폭포) -> 강한 전단력 -> 침식 -> 상류로 후퇴
    """
    cell_size = 1000.0 / grid_size
    grid = WorldGrid(width=grid_size, height=grid_size, cell_size=cell_size)
    rows, cols = grid_size, grid_size
    
    # 1. 초기 지형: 단단한 기반암 절벽
    center = cols // 2
    
    # 상류 (100m) -> 하류 (0m)
    # 절벽 위치: 중앙
    cliff_pos = 500
    
    Y, X = np.meshgrid(np.linspace(0, 1000, rows), np.linspace(0, 1000, cols))
    
    grid.bedrock[:] = 100.0
    grid.bedrock[Y >= cliff_pos] = 20.0 # Downstream base level
    
    # Slope face
    slope_mask = (Y >= cliff_pos-20) & (Y < cliff_pos+20)
    # Linear ramp for stability initially
    grid.bedrock[slope_mask] = 100.0 - (Y[slope_mask] - (cliff_pos-20))/40.0 * 80.0
    
    # Pre-carve channel to guide water
    grid.bedrock[:, center-5:center+5] -= 2.0
    
    grid.update_elevation()
    
    # 2. 물리 팩터
    hydro = HydroKernel(grid)
    erosion = ErosionProcess(grid, K=0.1) # K very high for noticeable retreat
    
    retreat_k = params.get('retreat_rate', 0.5) * 5.0 # retreat multiplier
    
    steps = max(50, min(time_years // 100, 300))
    dt = 1.0
    
    # Track position
    initial_knickpoint = cliff_pos
    current_knickpoint = cliff_pos
    
    for i in range(steps):
        # Flow
        precip = np.zeros((rows, cols))
        precip[0:5, center-5:center+5] = 20.0 # Upstream flow source
        
        discharge = hydro.route_flow_d8(precipitation=precip)
        
        # Erosion (Stream Power)
        # E = K * A^m * S^n
        # Waterfall face has huge S -> Huge E
        
        # To simulate retreat, we need significant erosion at the knickpoint
        # We modify K locally based on params
        # Or just let standard Stream Power do it?
        # Standard SP might smooth the slope rather than maintain a cliff.
        # "Parallel Retreat" requires a cap rock mechanism (hard layer over soft layer).
        
        # Let's simulate Cap Rock simple logic:
        # Erosion only effective if slope > critical
        
        # Calculate Slope (Magnitude)
        grad_y, grad_x = np.gradient(grid.elevation)
        slope = np.sqrt(grad_y**2 + grad_x**2)
        
        # Enhanced erosion at steep slopes (Face)
        cliff_mask = slope > 0.1
        
        # Apply extra erosion to cliff face to simulate undercutting/retreat
        # Erosion proportional to water flux * slope
        # K_eff = K * retreat_k
        
        eroded_depth = discharge * slope * retreat_k * dt * 0.05
        
        grid.bedrock[cliff_mask] -= eroded_depth[cliff_mask]
        
        # Flattening prevention (maintain cliff)
        # If lower part erodes, upper part becomes unstable -> discrete collapse
        # Simple simulation: Smoothing? No, simplified retreat
        
        # Just pure erosion usually rounds it.
        # Let's rely on the high K on the face.
        
        grid.update_elevation()
        erosion.hillslope_diffusion(dt=dt*0.1) # Minimal diffusion to keep sharpness
        
    # 3. 결과 분석
    # 침식이 가장 많이 일어난 지점 찾기 (Steepest slope upstream)
    grad_y, grad_x = np.gradient(grid.elevation)
    slope = np.sqrt(grad_y**2 + grad_x**2)
    # Find max slope index along river profile
    profile_slope = slope[:, center]
    # Find the peak slope closest to upstream
    peaks = np.where(profile_slope > 0.05)[0]
    if len(peaks) > 0:
        current_knickpoint = peaks.min() * cell_size
    else:
        current_knickpoint = 1000 # Eroded away?
        
    retreat_amount = current_knickpoint - initial_knickpoint # Should be negative (moves up = smaller Y)
    # But wait, Y increases downstream? 
    # Y=0 (Upstream), Y=1000 (Downstream).
    # Cliff at 500. Upstream is 0-500.
    # Retreat means moving towards 0.
    # So current should be < 500.
    
    total_retreat = abs(500 - current_knickpoint)
    
    # [Fix] Water Depth
    precip = np.zeros((rows, cols))
    precip[0:5, center-5:center+5] = 10.0
    discharge = hydro.route_flow_d8(precipitation=precip)
    water_depth = np.log1p(discharge) * 0.5
    
    # Plunge pool depth?
    # Add fake pool depth if slope is high
    water_depth[slope > 0.1] += 2.0
    
    return {'elevation': grid.elevation, 'retreat': total_retreat, 'water_depth': water_depth}

@st.cache_data(ttl=3600)
def simulate_braided_stream(time_years: int, params: dict, grid_size: int = 100):
    """망상 하천 시뮬레이션 (물리 엔진 적용)"""
    # 1. 그리드 초기화
    # 넓고 평탄한 하곡
    cell_size = 1000.0 / grid_size
    grid = WorldGrid(width=grid_size, height=grid_size, cell_size=cell_size)
    
    rows, cols = grid_size, grid_size
    
    # 기본 경사 (북 -> 남)
    for r in range(rows):
        grid.bedrock[r, :] = 100.0 - (r / rows) * 10.0 # 100m -> 90m (완경사)
        
    # 하곡 (Valley) 형성 - 양쪽이 높음
    center = cols // 2
    for c in range(cols):
        dist = abs(c - center)
        # 800m 폭의 넓은 계곡
        if dist > 20: 
            grid.bedrock[:, c] += (dist - 20) * 0.5 
            
    # 랜덤 노이즈 (유로 형성을 위한 불규칙성)
    np.random.seed(42)
    grid.bedrock += np.random.rand(rows, cols) * 1.5
    grid.update_elevation()
    
    # 2. 엔진
    hydro = HydroKernel(grid)
    erosion = ErosionProcess(grid, K=0.05, m=1.0, n=1.0) # K Increased
    
    # 파라미터
    n_channels = int(params.get('n_channels', 5)) # 입력 유량의 분산 정도?
    sediment_load = params.get('sediment', 0.5) * 200.0 # 퇴적물 공급량
    
    dt = 1.0
    steps = 100
    
    for i in range(steps):
        # 변동하는 유량 (Braiding 유발)
        # 시간/공간적으로 변하는 강수
        precip = np.random.rand(rows, cols) * 0.1 + 0.01 # Noise Increased
        
        discharge = hydro.route_flow_d8(precipitation=precip)
        
        # 상류 유입 (퇴적물 과부하)
        # 상류 중앙부에 물과 퇴적물 쏟아부음
        inflow_width = max(3, n_channels * 2)
        grid.sediment[0:2, center-inflow_width:center+inflow_width] += sediment_load * dt * 0.1
        discharge[0:2, center-inflow_width:center+inflow_width] += 100.0 # 강한 유량
        
        # 침식 및 퇴적
        erosion.simulate_transport(discharge, dt=dt)
        
        # 측방 침식 효과 (Banks collapse) - 단순 확산으로 근사
        # 망상하천은 하안이 불안정함
        erosion.hillslope_diffusion(dt=dt * 0.1) # Diffusion Decreased (Sharper)
        
    # [Fix] Water Depth
    # Use flow accumulation to show braided channels
    precip = np.ones((rows, cols)) * 0.01
    inflow_width = max(3, n_channels * 2)
    precip[0:2, center-inflow_width:center+inflow_width] += 50.0 # Source
    
    discharge = hydro.route_flow_d8(precipitation=precip)
    water_depth = np.log1p(discharge) * 0.3
    water_depth[water_depth < 0.2] = 0 # Filter shallow flow
        
    return {'elevation': grid.elevation, 'type': "망상 하천 (Braided)", 'water_depth': water_depth}

@st.cache_data(ttl=3600)
def simulate_levee(time_years: int, params: dict, grid_size: int = 100):
    """
    자연제방 및 배후습지 시뮬레이션 (Process-Based)
    - 홍수 범람 시 수로 주변에 유속 감소 -> 퇴적 (자연제방)
    - 수로에서 멀어질수록 미립질 퇴적 -> 배후습지
    """
    cell_size = 1000.0 / grid_size
    grid = WorldGrid(width=grid_size, height=grid_size, cell_size=cell_size)
    rows, cols = grid_size, grid_size
    
    # 1. 초기 지형: 평탄한 범람원 + 중앙 수로
    grid.bedrock[:] = 50.0
    center_c = cols // 2
    
    # Simple straight channel
    channel_width_cells = 3
    for c in range(center_c - channel_width_cells, center_c + channel_width_cells + 1):
        grid.bedrock[:, c] -= 5.0 # Channel depth
        
    grid.update_elevation()
    
    # 2. 물리 프로세스
    hydro = HydroKernel(grid)
    erosion = ErosionProcess(grid)
    
    flood_freq = params.get('flood_freq', 0.5)
    flood_magnitude = 10.0 + flood_freq * 20.0 # Flood height
    
    steps = max(50, min(time_years // 100, 300))
    dt = 1.0
    
    # Sediment concentration in flood water
    sediment_load = 0.5 
    
    # 3. 홍수 시뮬레이션 루프
    # 매 스텝마다 홍수가 나는 것은 아니지만, 시뮬레이션 상으로는 퇴적 누적을 계산
    # Simplified Model:
    # Water Level rises -> Spreads sediment from channel -> Deposits close to bank
    
    # Using 'diffusion' logic for suspended sediment
    # Channel has high concentration (C=1). Floodplain has C=0 initially.
    # Diffusion spreads C outwards.
    # Deposition rate proportional to C.
    
    # Or simplified physics:
    # 1. Raise water level globally (Flood)
    # 2. Add sediment source at channel
    # 3. Diffuse sediment
    # 4. Deposit
    
    sediment_map = np.zeros((rows, cols)) # Instantaneous sediment in water
    
    for i in range(steps):
        # Flood Event
        # Source at channel
        sediment_map[:, center_c-channel_width_cells:center_c+channel_width_cells+1] = sediment_load
        
        # Diffusion of sediment (Turbulent mixing)
        # Using a gaussian or neighbor averaging loop is slow in Python.
        # Use erosion.hillslope_diffusion trick on the sediment_map? No, that's for elevation.
        # Simple Numpy diffusion:
        
        # Lateral diffusion
        for _ in range(5): # Diffusion steps per flood
            sediment_map[:, 1:-1] = 0.25 * (sediment_map[:, :-2] + 2*sediment_map[:, 1:-1] + sediment_map[:, 2:])
            
        # Deposition
        # Deposit fraction of suspended sediment to ground
        deposit_rate = 0.1 * dt
        deposition = sediment_map * deposit_rate
        
        # Don't deposit inside channel (kept clear by flow)
        # Or deposit less? Natural levees form at bank, not bed.
        # Bed is scoured.
        
        # Mask channel
        channel_mask = (grid.bedrock[:, center_c] < 46.0) # Check depth
        # Better: use index
        channel_indices = slice(center_c-channel_width_cells, center_c+channel_width_cells+1)
        deposition[:, channel_indices] = 0
        
        grid.sediment += deposition
        
    # [Fix] Backswamp Water
    # Low lying areas far from river might retain water if we simulated rain
    # But here we just simulating formation.
    
    # Raise channel bed slightly? No.
    
    grid.update_elevation()
    
    # Calculate Levee Height
    levee_height = grid.sediment.max()
    
    # [Fix] Water Depth
    water_depth = np.zeros_like(grid.elevation)
    water_depth[:, center_c-channel_width_cells:center_c+channel_width_cells+1] = 4.0 # Bankfull
    
    # Backswamp water
    # Areas where sediment is low (far away) -> Water table is close
    # Visualize swamp
    max_sed = grid.sediment.max()
    swamp_mask = (grid.sediment < max_sed * 0.2) & (np.abs(np.arange(cols) - center_c) > 20)
    water_depth[swamp_mask] = 0.5 # Shallow water
    
    return {'elevation': grid.elevation, 'levee_height': levee_height, 'water_depth': water_depth}


@st.cache_data(ttl=3600)
def simulate_karst(theory: str, time_years: int, params: dict, grid_size: int = 100):
    """카르스트 지형 시뮬레이션 (물리 엔진 적용 - 화학적 용식)"""
    # 1. 그리드 초기화 (석회암 대지)
    cell_size = 1000.0 / grid_size
    grid = WorldGrid(width=grid_size, height=grid_size, cell_size=cell_size)
    rows, cols = grid_size, grid_size
    
    # 평탄한 고원 (100m)
    grid.bedrock[:] = 100.0
    # 약간의 불규칙성 (용식 시작점)
    np.random.seed(42)
    grid.bedrock += np.random.rand(rows, cols) * 2.0
    grid.update_elevation()
    
    # 2. 엔진
    hydro = HydroKernel(grid)
    erosion = ErosionProcess(grid) # 물리적 침식은 미미함
    
    co2 = params.get('co2', 0.5) # 용식 효율
    rainfall = params.get('rainfall', 0.5) # 강수량
    
    # 화학적 용식 계수
    dissolution_rate = 0.05 * co2
    
    dt = 1.0
    steps = 100
    
    # 돌리네 초기 씨앗 (Weak spots)
    n_seeds = 5 + int(co2 * 5)
    seeds = [(np.random.randint(10, rows-10), np.random.randint(10, cols-10)) for _ in range(n_seeds)]
    
    for cx, cy in seeds:
        # 초기 함몰
        grid.bedrock[cx, cy] -= 5.0
        
    grid.update_elevation()
    
    for i in range(steps):
        # [Hybrid Approach]
        # 교과서적인 돌리네(Doline) 형태 강제 (Round Depression)
        
        # 1. Physics (Dissolution) - keep it mostly for creating the *seeds*
        # But force the shape to be round
        
        # Aggressive deepening at seeds
        for cx, cy in seeds:
             Y, X = np.ogrid[:grid_size, :grid_size]
             dist = np.sqrt((X - cx)**2 + (Y - cy)**2)
             
             # Bowl shape
             # depth increases with time
             current_depth = (i / steps) * 30.0 * co2
             radius = 5.0 + (i/steps)*5.0
             
             mask = dist < radius
             depression = current_depth * (1.0 - (dist[mask]/radius)**2)
             
             # Apply max depth (don't double dip if overlapping)
             # We want to subtract.
             # grid.bedrock[mask] = min(grid.bedrock[mask], 100.0 - depression) 
             # Simpler: subtract increment
             
        # Re-implement: Just carve analytical bowls at the END?
        # No, iterative is better for animation.
        pass
        
    # Finalize Shape (Force Round Bowls)
    # [Fix] Scale evolution by time
    evolution = min(1.0, time_years / 50000.0)
    
    for cx, cy in seeds:
         Y, X = np.ogrid[:grid_size, :grid_size]
         dist = np.sqrt((X - cx)**2 + (Y - cy)**2)
         
         # Grow radius and depth
         radius = 3.0 + 7.0 * evolution # 3m -> 10m
         mask = dist < radius
         
         # Ideal Bowl
         depth = 20.0 * co2 * evolution
         profile = 100.0 - depth * (1.0 - (dist/radius)**2)
         grid.bedrock = np.where(mask, np.minimum(grid.bedrock, profile), grid.bedrock)
         
    # U-Valley or Karst Valley?
    # Just Dolines for now.
                
    max_depth = 100.0 - grid.bedrock.min()
    return {'elevation': grid.bedrock, 'depth': max_depth, 'n_dolines': n_seeds}

@st.cache_data(ttl=3600)
def simulate_tower_karst(time_years: int, params: dict, grid_size: int = 100):
    """탑 카르스트 시뮬레이션 - 차별 용식"""
    x = np.linspace(0, 1000, grid_size)
    y = np.linspace(0, 1000, grid_size)
    X, Y = np.meshgrid(x, y)
    
    # [Hybrid Approach]
    # 교과서적인 탑 카르스트 (Steep Towers) 강제
    
    cell_size = 1000.0 / grid_size
    grid = WorldGrid(width=grid_size, height=grid_size, cell_size=cell_size)
    
    # 1. Base Plain
    grid.bedrock[:] = 20.0
    
    # 2. Towers (Random distribution but sharp)
    np.random.seed(99)
    n_towers = 15
    centers = [(np.random.randint(10, 90), np.random.randint(10, 90)) for _ in range(n_towers)]
    
    Y, X = np.ogrid[:grid_size, :grid_size]
    
    towers_elev = np.zeros_like(grid.bedrock)
    
    for cx, cy in centers:
         dist = np.sqrt((X - cx)**2 + (Y - cy)**2)
         # Tower Shape: Steep sides, rounded top (Sugarloaf)
         radius = 8.0
         # [Fix] Towers become more prominent (or surrounding erodes) over time
         # Assume surrounding erodes, making towers relatively higher?
         # Or assume towers grow? Simulation subtracts from 20m plane?
         # Ah, sim adds `towers_elev` to `grid.bedrock`.
         # Let's scale height.
         evolution = min(1.0, time_years / 100000.0)
         
         target_height = 50.0 + np.random.rand() * 50.0
         height = target_height * evolution
         
         # Profile: 
         # if dist < radius: h * exp(...)
         # make it steeper than gaussian
         shape = height * (1.0 / (1.0 + np.exp((dist - radius)*1.0)))
         towers_elev = np.maximum(towers_elev, shape)
         
    grid.bedrock += towers_elev
    
    return {'elevation': grid.bedrock, 'type': "탑 카르스트 (Tower)"}


@st.cache_data(ttl=3600)
def simulate_cave(time_years: int, params: dict, grid_size: int = 100):
    """석회 동굴 시뮬레이션 - 석순/종유석 성장 (바닥면 기준)"""
    x = np.linspace(0, 100, grid_size)
    y = np.linspace(0, 100, grid_size)
    X, Y = np.meshgrid(x, y)
    
    elevation = np.zeros((grid_size, grid_size))
    
    # 동굴 바닥 (평탄)
    
    # 석순 (Stalagmites) 성장
    # 랜덤 위치에 씨앗
    np.random.seed(42)
    n_stalagmites = 10
    centers = [(np.random.randint(20, 80), np.random.randint(20, 80)) for _ in range(n_stalagmites)]
    
    growth_rate = params.get('rate', 0.5)
    
    steps = max(1, time_years // 100)
    total_growth = steps * growth_rate * 0.05
    
    for cx, cy in centers:
        # 가우시안 형상
        dist = np.sqrt((X - cx)**2 + (Y - cy)**2)
        
        # 성장: 높이와 너비가 같이 커짐
        h = total_growth * (0.8 + np.random.rand()*0.4)
        w = h * 0.3 # 뾰족하게
        
        shape = h * np.exp(-(dist**2)/(w**2 + 1))
        elevation = np.maximum(elevation, shape)
        
    return {'elevation': elevation, 'type': "석회동굴 (Cave)"}


@st.cache_data(ttl=3600)
def simulate_volcanic(theory: str, time_years: int, params: dict, grid_size: int = 100):
    """화산 지형 시뮬레이션 (물리 엔진 적용 - 용암 유동)"""
    # 1. 그리드 초기화
    cell_size = 1000.0 / grid_size
    grid = WorldGrid(width=grid_size, height=grid_size, cell_size=cell_size)
    rows, cols = grid_size, grid_size
    center = cols // 2
    
    # 기반 지형 (평지)
    grid.bedrock[:] = 50.0
    
    # 2. 엔진 (용암 흐름 -> HydroKernel 응용)
    hydro = HydroKernel(grid)
    # 용암은 물보다 점성이 매우 높음 -> 확산이 잘 안되고 쌓임
    # 여기서는 'Sediment'를 용암으로 간주하여 쌓이게 함
    
    eruption_rate = params.get('eruption_rate', 0.5)
    lava_viscosity = 0.5 # 점성
    
    # [Hybrid Approach]
    # 교과서적인 화산(Cone/Shield) 형태 강제
    
    # 1. Ideal Volcano Shape
    # Cone (Strato) or Dome (Shield)
    
    Y, X = np.ogrid[:grid_size, :grid_size]
    # Center
    cx, cy = grid_size//2, grid_size//2
    dist = np.sqrt((X - cx)**2 + (Y - cy)**2)
    
    volcano_h = 0.0
    
    if theory == "shield":
         # Shield: Wide, gentle slope (Gaussian)
         volcano_h = 100.0 * np.exp(-(dist**2)/(40**2))
    elif theory == "strato":
         # Strato: Steep, concave (Exponential)
         volcano_h = 150.0 * np.exp(-dist/15.0)
    elif theory == "caldera":
         # Caldera: Strato then cut top
         base_h = 150.0 * np.exp(-dist/15.0)
         # Cut top (Crater)
         crater_mask = dist < 20
         base_h[crater_mask] = 80.0 # Floor
         # Rim
         rim_mask = (dist >= 20) & (dist < 25)
         # Smooth transition is tricky, just hard cut for "Textbook" look
         volcano_h = base_h
    
    # Apply to Sediment (Lava)
    # [Fix] Scale height by time
    growth = min(1.0, time_years / 50000.0)
    grid.sediment += volcano_h * growth
    
    # 2. Add Flow Textures (Physics)
    hydro = HydroKernel(grid)
    steps = 50
    for i in range(steps):
         # Add slight roughness/flow lines
         erosion = ErosionProcess(grid)
         erosion.hillslope_diffusion(dt=1.0)
             
    # 최종 지형 = 기반암 + 용암
    grid.update_elevation()
    
    volcano_type = theory.capitalize()
    height = grid.elevation.max() - 50.0
    
    return {'elevation': grid.elevation, 'height': height, 'type': volcano_type}

@st.cache_data(ttl=3600)
def simulate_lava_plateau(time_years: int, params: dict, grid_size: int = 100):
    """용암 대지 시뮬레이션 - 열하 분출"""
    x = np.linspace(-500, 500, grid_size)
    y = np.linspace(-500, 500, grid_size)
    X, Y = np.meshgrid(x, y)
    
    # 기존 지형 (울퉁불퉁한 산지)
    elevation = 50 * np.sin(X/100) * np.cos(Y/100) + 20 * np.random.rand(grid_size, grid_size)
    
    # 열하 분출 (Fissure Eruption)
    # 중앙을 가로지르는 틈
    fissure_width = 10
    fissure_mask = np.abs(X) < fissure_width
    
    eruption_rate = params.get('eruption_rate', 0.5)
    steps = max(1, time_years // 100)
    
    # 용암류 채우기 (Flood Fill logic simplified)
    # 낮은 곳부터 채워져서 평탄해짐
    
    total_volume = steps * eruption_rate * 1000
    current_level = elevation.min()
    
    # 간단한 수위 상승 모델 (평탄화)
    # 용암은 유동성이 커서 수평을 유지하려 함
    # [Fix] Scale level by time
    growth = min(1.0, time_years / 50000.0)
    target_level = current_level + (total_volume / (grid_size**2) * 2) * growth # 대략적 높이 증가
    
    # 기존 지형보다 낮은 곳은 용암으로 채움 (평탄면 형성)
    # But only up to target_level
    lava_cover = np.maximum(elevation, target_level)
    # Actually, we should fill ONLY if elevation < target_level
    # And preserve mountains above target_level
    # logic: new_h = max(old_h, target_level) is correct for filling valleys
    
    # 가장자리는 약간 흐름 (경사)
    dist_from_center = np.abs(X)
    lava_cover = np.where(dist_from_center < 400, lava_cover, np.minimum(lava_cover, elevation + (lava_cover-elevation)*np.exp(-(dist_from_center-400)/50)))

    return {'elevation': lava_cover, 'type': "용암 대지 (Lava Plateau)"}

@st.cache_data(ttl=3600)
def simulate_columnar_jointing(time_years: int, params: dict, grid_size: int = 100):
    """주상절리 시뮬레이션 - 육각 기둥 패턴"""
    x = np.linspace(-20, 20, grid_size)
    y = np.linspace(-20, 20, grid_size)
    X, Y = np.meshgrid(x, y)
    
    # 기본 용암 대지 (평탄)
    elevation = np.ones((grid_size, grid_size)) * 100
    
    # 육각형 패턴 생성 (간단한 수학적 근사)
    # Cosine 간섭으로 벌집 모양 유사 패턴 생성
    scale = 2.0
    hex_pattern = np.cos(X*scale) + np.cos((X/2 + Y*np.sqrt(3)/2)*scale) + np.cos((X/2 - Y*np.sqrt(3)/2)*scale)
    
    # 기둥의 높이 차이 (풍화)
    erosion_rate = params.get('erosion_rate', 0.5)
    steps = max(1, time_years // 100)
    
    # [Fix] Scale weathering by time
    weathering = (steps * erosion_rate * 0.05) * (time_years / 10000.0)
    
    # 절리(틈) 부분은 낮게, 기둥 중심은 높게
    # hex_pattern > 0 인 부분이 기둥
    
    elevation += hex_pattern * 5 # 기둥 굴곡
    
    # 침식 작용 (틈이 더 많이 깎임)
    cracks = hex_pattern < -1.0 # 절리 틈
    # [Fix] Deepen cracks over time
    crack_depth = 20 + weathering * 10
    elevation[cracks] -= crack_depth
    
    # 전체적인 단면 (해안 절벽 느낌)
    # Y < 0 인 부분은 바다쪽으로 깎임
    cliff_mask = Y < -10
    elevation[cliff_mask] -= 50
    
    return {'elevation': elevation, 'type': "주상절리 (Columnar Jointing)"}


@st.cache_data(ttl=3600)

def simulate_glacial(theory: str, time_years: int, params: dict, grid_size: int = 100):
    """빙하 지형 시뮬레이션 (물리 엔진 - 빙하 침식 Q^0.5)"""
    
    # [Hybrid Approach]
    # 교과서적인 U자곡 형태를 강제(Template)하고, 물리 엔진으로 질감만 입힘
    
    rows, cols = grid_size, grid_size
    cell_size = 1000.0 / grid_size
    grid = WorldGrid(width=grid_size, height=grid_size, cell_size=cell_size)
    ice_thickness = params.get('ice_thickness', 1.0)
    
    # 1. Ideal U-Shape Template
    center = cols // 2
    u_width = 30 # Half width
    
    # [Fix] Time-dependent depth and shape
    evolution = min(1.0, time_years / 100000.0)
    
    # 시간에 따른 깊이 및 너비 진화
    # Ice thickness determines depth
    target_depth = 200 * ice_thickness * (0.2 + 0.8 * evolution)
    shape_exp = 1.5 + 2.5 * evolution # Morph from V(1.5) to U(4.0)
    
    # Create U-profile
    dist_from_center = np.abs(np.arange(cols) - center)
    
    # U-Shape function: Flat bottom, steep walls
    # Profile ~ (x/w)^4
    normalized_dist = np.minimum(dist_from_center / u_width, 1.5)
    u_profile = -target_depth * (1.0 - np.power(normalized_dist, shape_exp))
    u_profile = np.maximum(u_profile, -target_depth) # Cap depth
    
    # Apply to grid rows
    # V-valley was initial. We morph V to U.
    for r in range(rows):
        # Base slope
        base_h = 300 - (r/rows)*200
        grid.bedrock[r, :] = base_h + u_profile
    
    # 2. Add Physics Detail (Roughness)
    steps = 50
    hydro = HydroKernel(grid)
    grid.update_elevation()
    
    for i in range(steps):
         # Slight erosion to add texture
         precip = np.ones((rows, cols)) * 0.05
         discharge = hydro.route_flow_d8(precipitation=precip)
         # Glacial Polish/Plucking noise
         erosion_amount = discharge * 0.001
         grid.bedrock -= erosion_amount
    
    # Fjord Handling
    valley_type = "빙식곡 (U자곡)"
    if theory == "fjord":
        grid.bedrock -= 120 # Submerge
        grid.bedrock = np.maximum(grid.bedrock, -50)
        valley_type = "피오르 (Fjord)"
        
    grid.update_elevation()
    depth = grid.bedrock.max() - grid.bedrock.min()
    return {'elevation': grid.bedrock, 'width': 300, 'depth': depth, 'type': valley_type}



@st.cache_data(ttl=3600)
def simulate_cirque(time_years: int, params: dict, grid_size: int = 100):
    """권곡 시뮬레이션 - 회전 슬라이딩"""
    x = np.linspace(0, 1000, grid_size)
    y = np.linspace(0, 1000, grid_size)
    X, Y = np.meshgrid(x, y)
    
    # 초기 산 사면 (경사)
    elevation = Y * 0.5 + 100
    
    # 권곡 형성 위치 (중앙 상부)
    cx, cy = 500, 700
    r = 250
    
    dt = 100
    steps = max(1, time_years // dt)
    erosion_rate = params.get('erosion_rate', 0.5)
    
    # 시간 진행
    total_erosion = min(1.0, steps * erosion_rate * 0.001)
    
    # [Hybrid Approach] Check
    # 교과서적인 권곡(Bowl) 형태 강제
    
    # Ideal Bowl Shape
    # cx, cy center
    dx = X - cx
    dy = Y - cy
    dist = np.sqrt(dx**2 + dy**2)
    
    # Bowl depth profile
    # Deepest at 0.5r, Rim at 1.0r
    bowl_mask = dist < r
    
    # Armchair shape: Steep backwall, Deep basin, Shallow lip
    # Backwall (Y > cy)
    normalized_y = (Y - cy) / r
    backwall_effect = np.clip(normalized_y, -1, 1)
    
    # Excavation amount
    excavation = np.zeros_like(elevation)
    
    # Basic Bowl
    excavation[bowl_mask] = 100 * (1 - (dist[bowl_mask]/r)**2)
    
    # Deepen the back (Cirque characteristic)
    excavation[bowl_mask] *= (1.0 + backwall_effect[bowl_mask] * 0.5)
    
    # Parameter scaling
    total_effect = min(1.0, steps * erosion_rate * 0.01)
    elevation -= excavation * total_effect
    
    # Make Rim sharp (Arete precursor)
    # Add roughness
    noise = np.random.rand(grid_size, grid_size) * 5.0
    elevation += noise
    
    return {'elevation': elevation, 'type': "권곡 (Cirque)"}

@st.cache_data(ttl=3600)
def simulate_moraine(time_years: int, params: dict, grid_size: int = 100):
    """모레인 시뮬레이션 (물리 엔진 - 빙하 퇴적)"""
    # 1. 그리드 (U자곡 기반)
    cell_size = 1000.0 / grid_size
    grid = WorldGrid(width=grid_size, height=grid_size, cell_size=cell_size)
    rows, cols = grid_size, grid_size
    
    # U자곡 형태 생성
    center = cols // 2
    for r in range(rows):
        grid.bedrock[r, :] = 200 - (r/rows) * 100
    
    for c in range(cols):
        dist_norm = abs(c - center) / (cols/2)
        # U-shape profile: flat bottom, steep sides
        u_profile = (dist_norm ** 4) * 150
        grid.bedrock[:, c] += u_profile
    
    # 2. 퇴적 시뮬레이션
    debris_supply = params.get('debris_supply', 0.5)
    
    # 빙하 끝(Terminus) 위치 변화
    # 100년 -> 끝(row=cols), 10000년 -> 후퇴(row=0)
    # 여러 단계에 걸쳐 퇴적
    
    # [Hybrid Approach]
    # 교과서적인 모레인(Ridge) 형태 강제
    
    # [Fix] Time-dependent retreat
    # 20,000 years for full retreat
    retreat_progress = min(1.0, time_years / 20000.0)
    
    # We shouldn't loop 50 steps to build the final shape if time is fixed?
    # Actually, we want to show the accumulated sediment up to 'retreat_progress'.
    # So we iterate up to current progress.
    
    total_steps = 50
    current_steps = int(total_steps * retreat_progress)
    
    for i in range(current_steps + 1):
        # 빙하 끝 위치 (Dynamic Retreat)
        # 0 -> 1 (Progress)
        p = i / total_steps
        terminus_row = int(rows * (0.8 - p * 0.6))
        
        # 1. Terminal Moraine (Arc)
        # 퇴적물 집중 (Ridge)
        # Gaussian ridge at terminus_row
        
        # Arc shape: slightly curved back upstream at edges
        
        # Deposit mainly at terminus
        current_flux = debris_supply * 5.0
        
        # Create a ridge mask
        # 2D Gaussian Ridge?
        # Just simple row addition with noise
        
        # Arc curvature
        curvature = 10
        
        for c in range(cols):
            # Row shift for arc
            dist_c = abs(c - center) / (cols/2)
            arc_shift = int(dist_c * dist_c * curvature)
            
            target_r = terminus_row - arc_shift
            if 0 <= target_r < rows:
                # Add sediment pile
                # "Recessional Moraines" - leave small piles as it retreats
                # "Terminal Moraine" - The biggest one at max extent (start)
                
                amount = current_flux
                if i == 0: amount *= 3.0 # Main terminal moraine is huge
                
                # Deposit
                if grid.sediment[target_r, c] < 50: # Limit height
                     grid.sediment[target_r, c] += amount
                     
        # 2. Lateral Moraine (Side ridges)
        # Always deposit at edges of glacier (which is u_profile width)
        # Glacier width ~ where u_profile starts rising steep
        glacier_width_half = cols // 4
        
        # Left Lateral
        l_c = center - glacier_width_half
        grid.sediment[terminus_row:, l_c-2:l_c+3] += current_flux * 0.5
        
        # Right Lateral
        r_c = center + glacier_width_half
        grid.sediment[terminus_row:, r_c-2:r_c+3] += current_flux * 0.5
        
    # Smoothing
    erosion = ErosionProcess(grid)
    erosion.hillslope_diffusion(dt=5.0)

    return {'elevation': grid.elevation, 'type': "모레인 (Moraine)"}



@st.cache_data(ttl=3600)
def simulate_arid(theory: str, time_years: int, params: dict, grid_size: int = 100):
    """건조 지형 시뮬레이션 (물리 엔진 - 바람 이동 및 침식)"""
    
    # 1. 그리드 초기화
    cell_size = 1000.0 / grid_size
    grid = WorldGrid(width=grid_size, height=grid_size, cell_size=cell_size)
    rows, cols = grid_size, grid_size
    
    steps = 100
    wind_speed = params.get('wind_speed', 0.5)
    
    # 2. 이론별 엔진 적용
    if theory == "barchan":
        # [Hybrid Approach]
        # 교과서적인 초승달(Crescent) 모양 강제
        
        # Analytical Barchan Shape
        # Center of dune
        cx, cy = grid_size // 2, grid_size // 3
        
        # Coordinate relative to center
        Y, X = np.ogrid[:grid_size, :grid_size]
        dx = X - cx
        dy = Y - cy
        
        # Dune Size
        W = 15.0 # Width param
        L = 15.0 # Length param
        
        # Crescent Formula (simplified)
        # Body: Gaussian (Height adjusted to 25m based on academic typical range 9-30m)
        body = 25.0 * np.exp(-(dx**2 / (W**2) + dy**2 / (L**2)))
        
        # Horns: Subtract parabolic shape from behind
        # Wind from X (left to right) -> Horns point right
        # Cutout from the back (Scaled down proportionally)
        cutout = 18.0 * np.exp(-((dx + 10)**2 / (W*1.5)**2 + dy**2 / (L*0.8)**2))
        
        dune_shape = np.maximum(0, body - cutout)
        
        # 뿔(Horn)을 더 길게 앞으로 당김
        # Bending
        horns = 6.0 * np.exp(-(dy**2 / 100.0)) * np.exp(-((dx-10)**2 / 200.0))
        # Mask horns to be mainly on sides
        horns_mask = (np.abs(dy) > 10) & (dx > 0)
        dune_shape[horns_mask] += horns[horns_mask] * 2.0
        
        # Apply to Sediment
        grid.sediment[:] = dune_shape
        
        # Physics Drift (Winds)
        # 1. Advection (Move Downwind)
        # [Fix] Move based on time
        shift_amount = int(wind_speed * time_years * 0.05) % cols
        if shift_amount > 0:
            grid.sediment = np.roll(grid.sediment, shift_amount, axis=1) # Move Right
            grid.sediment[:, :shift_amount] = 0
            
        # 2. Diffusion (Smooth slopes)
        erosion = ErosionProcess(grid)
        erosion.hillslope_diffusion(dt=5.0)
        
        landform_type = "바르한 사구 (Barchan)"
        
    elif theory == "mesa":
        # [Hybrid Approach]
        # 교과서적인 메사(Table) 형태 강제
        
        # 1. Base Plateau
        grid.bedrock[:] = 20.0
        
        # 2. Hard Caprock (Circle or Rectangle)
        # Center high
        cx, cy = grid_size // 2, grid_size // 2
        Y, X = np.ogrid[:grid_size, :grid_size]
        dist = np.sqrt((X - cx)**2 + (Y - cy)**2)
        
        # Mesa Radius
        # [Fix] Mesa shrinks over time (Cliff Backwearing)
        # Start wide (Plateau), shrink to Mesa
        initial_r = 45.0
        shrinkage = (time_years / 100000.0) * 20.0 # Shrink 20m over 100ky
        mesa_r = max(10.0, initial_r - shrinkage)
        
        # Steep Cliff (Sigmoid or Step)
        # Height 100m
        height_profile = 80.0 * (1.0 / (1.0 + np.exp((dist - mesa_r) * 1.0)))
        
        grid.bedrock += height_profile
        
        # 3. Physics Erosion (Talus formation)
        # 침식시켜서 절벽 밑에 애추(Talus) 형성
        steps = 50
        erosion = ErosionProcess(grid, K=0.005) # Weak erosion
        hydro = HydroKernel(grid)
        
        for i in range(steps):
             precip = np.ones((rows, cols)) * 0.05
             discharge = hydro.route_flow_d8(precipitation=precip)
             
             # Cliff retreat (very slow)
             # Talus accumulation (High diffusion on slopes)
             erosion.hillslope_diffusion(dt=2.0)
             
        landform_type = "메사 (Mesa)"
        
    elif theory == "pediment":
        # 페디먼트: 산지 앞의 완경사 침식면
        # 산(High) -> 페디먼트(Slope) -> 플라야(Flat)
        
        # Mountain Back
        grid.bedrock[:30, :] = 150.0
        
        # Pediment Slope (Linear)
        for r in range(30, 80):
            grid.bedrock[r, :] = 150.0 - (r-30) * 2.5 # 150 -> 25
            
        # Playa (Flat)
        grid.bedrock[80:, :] = 25.0
        
        # Noise
        grid.bedrock += np.random.rand(rows, cols) * 2.0
        
        landform_type = "페디먼트 (Pediment)"
        
    else:
        landform_type = "건조 지형"
    
    grid.update_elevation()
    return {'elevation': grid.elevation, 'type': landform_type}


@st.cache_data(ttl=3600)
def simulate_plain(theory: str, time_years: int, params: dict, grid_size: int = 100):
    """평야 지형 시뮬레이션 - 교과서적 범람원, 자연제방"""
    
    x = np.linspace(0, 1000, grid_size)
    y = np.linspace(0, 1000, grid_size)
    X, Y = np.meshgrid(x, y)
    
    # 기본 평탄 지형 (약간 상류가 높음)
    base_height = 20
    elevation = np.ones((grid_size, grid_size)) * base_height
    elevation += 5 * (1 - Y / 1000)
    
    flood_freq = params.get('flood_freq', 0.5)
    
    # 하천 중심선 (약간 사행)
    river_x = 500 + 30 * np.sin(np.linspace(0, 3*np.pi, grid_size))
    
    if theory == "floodplain" or theory == "levee":
        # 교과서적 범람원: 자연제방 > 배후습지 구조
        
        # [Fix] Scale Levee growth by time and flood_freq
        # e.g. 1000 years -> small levee, 100,000 years -> huge levee
        time_factor = min(1.0, time_years / 50000.0)
        levee_growth = (base_height + 4 + flood_freq * 2 - base_height) * (0.2 + 0.8 * time_factor)
        backswamp_growth = 0 # stays low usually, or fills up slowly?
        
        for j in range(grid_size):
            rx = int(river_x[j] * grid_size / 1000)
            if 0 < rx < grid_size:
                # 하천 (가장 낮음)
                river_width = 3
                for i in range(max(0, rx-river_width), min(grid_size, rx+river_width)):
                    elevation[j, i] = base_height - 5
                
                # 자연제방 (하천 양쪽, 높음)
                levee_width = 12
                # [Fix] Dynamic height
                levee_height = base_height + levee_growth
                
                for i in range(max(0, rx-levee_width), rx-river_width):
                    dist = abs(i - rx)
                    elevation[j, i] = levee_height - (dist - river_width) * 0.2
                for i in range(rx+river_width, min(grid_size, rx+levee_width)):
                    dist = abs(i - rx)
                    elevation[j, i] = levee_height - (dist - river_width) * 0.2
                
                # 배후습지 (자연제방 바깥쪽, 낮음)
                backswamp_height = base_height - 2
                for i in range(0, max(0, rx-levee_width)):
                    elevation[j, i] = backswamp_height
                for i in range(min(grid_size, rx+levee_width), grid_size):
                    elevation[j, i] = backswamp_height
        
        plain_type = "범람원"
        
    elif theory == "alluvial":
        # 충적평야 (전체적으로 퇴적)
        for j in range(grid_size):
            rx = int(river_x[j] * grid_size / 1000)
            dist_from_river = np.abs(np.arange(grid_size) - rx)
            deposition = flood_freq * 3 * np.exp(-dist_from_river / 30)
            elevation[j, :] += deposition
            elevation[j, max(0,rx-2):min(grid_size,rx+2)] = base_height - 3
        
        plain_type = "충적평야"
    else:
        plain_type = "평야"
    
    # [Fix] Water Depth
    water_depth = np.zeros_like(elevation)
    for j in range(grid_size):
         rx = int(river_x[j] * grid_size / 1000)
         if 0 < rx < grid_size:
             river_width = 3
             water_depth[j, max(0, rx-river_width):min(grid_size, rx+river_width+1)] = 3.0
                
    return {'elevation': elevation, 'type': plain_type, 'water_depth': water_depth}


# ============ 사실적 렌더링 ============

def create_terrain_colormap():
    """자연스러운 지형 색상맵"""
    # 고도별 색상: 물(파랑) → 해안(황토) → 저지대(녹색) → 산지(갈색) → 고산(흰색)
    cdict = {
        'red': [(0.0, 0.1, 0.1), (0.25, 0.9, 0.9), (0.4, 0.4, 0.4), 
                (0.6, 0.6, 0.6), (0.8, 0.5, 0.5), (1.0, 1.0, 1.0)],
        'green': [(0.0, 0.3, 0.3), (0.25, 0.85, 0.85), (0.4, 0.7, 0.7),
                  (0.6, 0.5, 0.5), (0.8, 0.35, 0.35), (1.0, 1.0, 1.0)],
        'blue': [(0.0, 0.6, 0.6), (0.25, 0.6, 0.6), (0.4, 0.3, 0.3),
                 (0.6, 0.3, 0.3), (0.8, 0.2, 0.2), (1.0, 1.0, 1.0)]
    }
    return colors.LinearSegmentedColormap('terrain_natural', cdict)


def render_terrain_3d(elevation, title, add_water=True, water_level=0, view_elev=35, view_azim=225):
    """3D Perspective 렌더링 - 단일 색상(copper)"""
    fig = plt.figure(figsize=(12, 9), facecolor='#1a1a2e')
    ax = fig.add_subplot(111, projection='3d', facecolor='#1a1a2e')
    
    h, w = elevation.shape
    x = np.arange(w)
    y = np.arange(h)
    X, Y = np.meshgrid(x, y)
    
    # 단일 색상 (copper - 갈색 명도 변화)
    elev_norm = (elevation - elevation.min()) / (elevation.max() - elevation.min() + 0.01)
    
    surf = ax.plot_surface(X, Y, elevation, 
                           facecolors=cm.copper(elev_norm),
                           linewidth=0, antialiased=True, 
                           shade=True, lightsource=plt.matplotlib.colors.LightSource(315, 45))
    
    # 물 표면 (어두운 색상)
    if add_water:
        water_mask = elevation < water_level
        if np.any(water_mask):
            ax.plot_surface(X, Y, np.where(water_mask, water_level, np.nan),
                           color='#2C3E50', alpha=0.8, linewidth=0)
    
    ax.view_init(elev=view_elev, azim=view_azim)
    
    # 축 스타일
    ax.set_xlabel('X (m)', fontsize=10, color='white')
    ax.set_ylabel('Y (m)', fontsize=10, color='white')
    ax.set_zlabel('고도 (m)', fontsize=10, color='white')
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20, color='white')
    ax.tick_params(colors='white')
    
    # 컬러바 (copper)
    mappable = cm.ScalarMappable(cmap='copper', 
                                  norm=plt.Normalize(elevation.min(), elevation.max()))
    mappable.set_array([])
    cbar = fig.colorbar(mappable, ax=ax, shrink=0.5, aspect=15, pad=0.1)
    cbar.set_label('고도 (m)', fontsize=10, color='white')
    cbar.ax.yaxis.set_tick_params(color='white')
    plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='white')
    
    if add_water:
        water_patch = mpatches.Patch(color='#2C3E50', alpha=0.8, label='수역')
        ax.legend(handles=[water_patch], loc='upper left', fontsize=9, 
                  facecolor='#1a1a2e', labelcolor='white')
        # 현재 지형면
    plt.tight_layout()
    return fig


def render_terrain_plotly(elevation, title, add_water=True, water_level=0, texture_path=None, force_camera=True, water_depth_grid=None, sediment_grid=None, landform_type=None):
    """Plotly 인터랙티브 3D Surface - 사실적 텍스처(Biome) 또는 위성 이미지 적용
    
    Args:
        landform_type: 'river', 'coastal', 'glacial', 'volcanic', 'karst', 'arid' 중 하나.
                       None이면 기존 로직 사용.
                       'glacial'만 만년설 표시, 나머지는 물/풀/암석만
    """
    h, w = elevation.shape
    x = np.arange(w)
    y = np.arange(h)
    
    # 1. 지형 텍스처링 (Biome Calculation)
    # 경사도 계산
    dy, dx = np.gradient(elevation)
    slope = np.sqrt(dx**2 + dy**2)
    
    # Biome Index (0: 물/모래, 1: 풀, 2: 암석, 3: 눈)
    biome = np.zeros_like(elevation)
    
    # 기본: 풀 (Grass)
    biome[:] = 1 
    
    # 모래/퇴적물 (물 근처 낮은 곳 + 평탄한 곳)
    # add_water가 False여도 골짜기(낮은 곳)는 퇴적물이므로 모래색 적용
    sand_level = water_level + 5 if add_water else elevation.min() + 10
    
    # 퇴적지 판별: 
    # 1) Explicit sediment grid provided (> 0.5m)
    # 2) Or Geometric guess (low & flat)
    is_deposit = np.zeros_like(elevation, dtype=bool)
    
    if sediment_grid is not None:
        is_deposit = (sediment_grid > 0.5)
    else:
        is_deposit = (elevation < sand_level) & (slope < 0.5)
        
    biome[is_deposit] = 0
    
    # 암석 (경사가 급한 곳) - 절벽
    biome[slope > 1.2] = 2
    
    # 지형 유형별 처리
    if landform_type == 'glacial':
        # 빙하 지형: 전체적으로 빙하/눈 표시 (높은 곳 + U자곡 바닥도)
        biome[elevation > 50] = 3  # 빙하 지형은 전체에 눈/빙하
        biome[slope > 1.5] = 2  # 가파른 절벽만 암석
    elif landform_type in ['river', 'coastal']:
        # 하천/해안: 물 영역 명시적 표시 (biome=0을 물색으로)
        if water_depth_grid is not None:
            is_water = water_depth_grid > 0.5
            biome[is_water] = 0  # 물 영역
        # 음수 고도 = 바다/호수
        biome[elevation < 0] = 0
    elif landform_type == 'arid':
        # 건조: 전체 모래색
        biome[slope < 0.8] = 0  # 평탄한 곳은 모래
    # else: 기본 (화산, 카르스트) - 만년설 없음, 풀/암석만
    
    # 조금 더 자연스럽게: 노이즈 추가 (경계면 블렌딩 효과 흉내)
    noise = np.random.normal(0, 0.2, elevation.shape)
    biome_noisy = np.clip(biome + noise, 0, 3).round(2)
    
    # 커스텀 컬러스케일 (Discrete)
    # 0: Soil/Sand (Yellowish), 1: Grass (Green), 2: Rock (Gray), 3: Snow/Water
    if landform_type == 'glacial':
        # 빙하 지형: 눈/빙하 표시
        realistic_colorscale = [
            [0.0, '#E6C288'], [0.25, '#E6C288'],  # Sand/Soil
            [0.25, '#556B2F'], [0.5, '#556B2F'],  # Grass
            [0.5, '#808080'], [0.75, '#808080'],  # Rock
            [0.75, '#E0FFFF'], [1.0, '#FFFFFF']   # Ice/Snow (밝은 청백색)
        ]
        colorbar_labels = ["퇴적(土)", "식생(草)", "암석(岩)", "빙하(氷)"]
    elif landform_type in ['river', 'coastal']:
        # 하천/해안: 물 표시 (파란색)
        realistic_colorscale = [
            [0.0, '#4682B4'], [0.25, '#4682B4'],  # Water (Steel Blue)
            [0.25, '#556B2F'], [0.5, '#556B2F'],  # Grass
            [0.5, '#808080'], [0.75, '#808080'],  # Rock
            [0.75, '#D2B48C'], [1.0, '#D2B48C']   # Sand (밝은 갈색)
        ]
        colorbar_labels = ["수역(水)", "식생(草)", "암석(岩)", "사질(砂)"]
    elif landform_type == 'arid':
        # 건조 지형: 사막 표시 (갈색/주황)
        realistic_colorscale = [
            [0.0, '#EDC9AF'], [0.25, '#EDC9AF'],  # Desert Sand
            [0.25, '#CD853F'], [0.5, '#CD853F'],  # Brown
            [0.5, '#808080'], [0.75, '#808080'],  # Rock
            [0.75, '#DAA520'], [1.0, '#DAA520']   # Gold Sand
        ]
        colorbar_labels = ["사막(砂)", "암질(巖)", "암석(岩)", "모래(沙)"]
    else:
        # 기본 (화산, 카르스트 등)
        realistic_colorscale = [
            [0.0, '#E6C288'], [0.25, '#E6C288'],
            [0.25, '#556B2F'], [0.5, '#556B2F'],
            [0.5, '#808080'], [0.75, '#808080'],
            [0.75, '#A0522D'], [1.0, '#A0522D']   # 갈색 (만년설 제거)
        ]
        colorbar_labels = ["퇴적(土)", "식생(草)", "암석(岩)", "표토(土)"]
    
    # 지형 노이즈 (Fractal Roughness) - 시각적 디테일 추가
    visual_z = (elevation + np.random.normal(0, 0.2, elevation.shape)).round(2)

    # 텍스처 로직 (이미지 매핑)
    final_surface_color = biome_noisy
    final_colorscale = realistic_colorscale
    final_cmin = 0
    final_cmax = 3
    final_colorbar = dict(
        title=dict(text="지표 상태", font=dict(color='white')), 
        tickvals=[0.37, 1.12, 1.87, 2.62], 
        ticktext=colorbar_labels,
        tickfont=dict(color='white')
    )

    if texture_path and os.path.exists(texture_path):
        try:
            img = Image.open(texture_path).convert('L')
            img = img.resize((elevation.shape[1], elevation.shape[0]))
            img_array = np.array(img) / 255.0
            
            final_surface_color = img_array
            
            # 텍스처 테마에 따른 컬러맵 설정
            if "barchan" in texture_path or "arid" in str(texture_path):
                # 사막: 갈색 -> 금색
                final_colorscale = [[0.0, '#8B4513'], [0.3, '#CD853F'], [0.6, '#DAA520'], [1.0, '#FFD700']]
            elif "valley" in texture_path or "meander" in texture_path or "delta" in texture_path:
                # 숲/하천: 짙은 녹색 -> 연두색 -> 흙색
                final_colorscale = [[0.0, '#2F4F4F'], [0.4, '#556B2F'], [0.7, '#8FBC8F'], [1.0, '#D2B48C']]
            elif "volcano" in texture_path:
                # 화산: 검정 -> 회색 -> 붉은기
                final_colorscale = [[0.0, '#000000'], [0.5, '#404040'], [0.8, '#696969'], [1.0, '#8B4513']]
            elif "fjord" in texture_path:
                # 피오르: 짙은 파랑(물) -> 회색(절벽) -> 흰색(눈)
                final_colorscale = [[0.0, '#191970'], [0.4, '#708090'], [0.8, '#C0C0C0'], [1.0, '#FFFFFF']]
            elif "karst" in texture_path:
                # 카르스트: 진녹색(봉우리) -> 연녹색(들판)
                final_colorscale = [[0.0, '#556B2F'], [0.4, '#228B22'], [0.7, '#8FBC8F'], [1.0, '#F5DEB3']]
            elif "fan" in texture_path or "braided" in texture_path:
                # 선상지/망상하천: 황토색(모래) -> 갈색(자갈)
                final_colorscale = [[0.0, '#D2B48C'], [0.4, '#BC8F8F'], [0.8, '#8B4513'], [1.0, '#A0522D']]
            elif "glacier" in texture_path or "cirque" in texture_path:
                # 빙하: 흰색 -> 회색 -> 청회색
                final_colorscale = [[0.0, '#F0F8FF'], [0.4, '#B0C4DE'], [0.7, '#778899'], [1.0, '#2F4F4F']]
            elif "lava" in texture_path:
                # 용암: 검정 -> 진회색
                final_colorscale = [[0.0, '#000000'], [0.5, '#2F4F4F'], [1.0, '#696969']]
            else:
                # 기본: 흑백
                final_colorscale = 'Gray'
            
            final_cmin = 0
            final_cmax = 1
            final_colorbar = dict(title="텍스처 명암")
        except Exception as e:
            print(f"Texture error: {e}")

    # ============ 3D Plot ============
    # 조명 효과
    lighting_effects = dict(ambient=0.4, diffuse=0.5, roughness=0.9, specular=0.1, fresnel=0.2)
    
    # 1. Terrain Surface
    trace_terrain = go.Surface(
        z=visual_z, x=x, y=y,
        surfacecolor=final_surface_color,
        colorscale=final_colorscale,
        cmin=final_cmin, cmax=final_cmax,
        colorbar=final_colorbar,
        lighting=lighting_effects,
        hoverinfo='z'
    )
    
    data = [trace_terrain]
    
    # 2. Water Surface
    # Case A: water_depth_grid (Variable water height for rivers)
    if water_depth_grid is not None:
         # Create water elevation: usually bedrock/sediment + depth
         # We need base elevation. 'elevation' argument includes sediment.
         
         # Filter: Only show water where depth > threshold
         water_mask = water_depth_grid > 0.1
         
         if np.any(water_mask):
             # Water Surface Elevation
             water_z = visual_z.copy()
             # To avoid z-fighting, add depth. But visual_z is noisy. 
             # Use original elevation + depth
             water_z = elevation + water_depth_grid
             
             # Hide dry areas
             water_z[~water_mask] = np.nan
             
             trace_water = go.Surface(
                z=water_z, x=x, y=y,
                colorscale=[[0, 'rgba(30,144,255,0.7)'], [1, 'rgba(30,144,255,0.7)']], # DodgerBlue
                showscale=False,
                lighting=dict(ambient=0.6, diffuse=0.5, specular=0.8, roughness=0.1), # Glossy
                hoverinfo='skip'
             )
             data.append(trace_water)

    # Case B: Flat water_level (Sea/Lake)
    elif add_water:
        # 평면 바다
        water_z = np.ones_like(elevation) * water_level
        
        # Only draw where water is above terrain? Or just draw flat plane?
        # Drawing flat plane is standard for sea.
        # But for aesthetic, maybe mask it? No, sea level is simpler.
        
        trace_water = go.Surface(
            z=water_z,
            x=x, y=y,
            hoverinfo='none',
            lighting = dict(ambient=0.6, diffuse=0.6, specular=0.5)
        )
        data.append(trace_water)
    
    # 레이아웃 (어두운 테마)
    # 레이아웃 (어두운 테마)
    fig = go.Figure(data=data)
    
    # 레이아웃 (어두운 테마)
    fig.update_layout(
        title=dict(text=title, font=dict(color='white', size=16)),
        # [Fix 1] Interaction Persistence (Move to Top Level)
        uirevision='terrain_viz',
        scene=dict(
            xaxis=dict(title='X (m)', backgroundcolor='#1a1a2e', gridcolor='#444', color='#cccccc'),
            yaxis=dict(title='Y (m)', backgroundcolor='#1a1a2e', gridcolor='#444', color='#cccccc'),
            zaxis=dict(title='Elevation', backgroundcolor='#1a1a2e', gridcolor='#444', color='#cccccc'),
            bgcolor='#0e1117', # 
            
            # uirevision removed from here 
            
            # [Fix 2] Better Camera Angle (Isometric) - Optional
            camera=dict(
                eye=dict(x=1.6, y=-1.6, z=0.8), # Isometric-ish
                center=dict(x=0, y=0, z=-0.2),  # Look slightly down
                up=dict(x=0, y=0, z=1)
            ) if force_camera else None,
            
            # [Fix 3] Proportions
            aspectmode='manual',
            aspectratio=dict(x=1, y=1, z=0.35) # Z is flattened slightly for realism
        ),
        paper_bgcolor='#0e1117',
        plot_bgcolor='#0e1117',
        height=700, # Taller
        margin=dict(l=10, r=10, t=50, b=10),
        # Remove modebar to prevent accidental resets? No, keep it.
    )
    
    return fig


def render_v_valley_3d(elevation, x_coords, title, depth):
    """V자곡 전용 3D 렌더링 - 단일 색상(copper)"""
    fig = plt.figure(figsize=(14, 8), facecolor='#1a1a2e')
    
    ax1 = fig.add_subplot(121, projection='3d', facecolor='#1a1a2e')
    ax2 = fig.add_subplot(122, facecolor='#1a1a2e')
    
    h, w = elevation.shape
    x = np.arange(w)
    y = np.arange(h)
    X, Y = np.meshgrid(x, y)
    
    # 단일 색상 (copper)
    elev_norm = (elevation - elevation.min()) / (elevation.max() - elevation.min() + 0.01)
    
    ax1.plot_surface(X, Y, elevation,
                     facecolors=cm.copper(elev_norm),
                     linewidth=0, antialiased=True, shade=True)
    
    # 하천 (어두운 색상)
    min_z = elevation.min()
    water_level = min_z + 3
    channel_mask = elevation < water_level
    if np.any(channel_mask):
        ax1.plot_surface(X, Y, np.where(channel_mask, water_level, np.nan),
                        color='#2C3E50', alpha=0.9, linewidth=0)
    
    ax1.view_init(elev=45, azim=200)
    ax1.set_xlabel('X', color='white')
    ax1.set_ylabel('Y', color='white')
    ax1.set_zlabel('고도', color='white')
    ax1.set_title('3D 조감도', fontsize=12, fontweight='bold', color='white')
    ax1.tick_params(colors='white')
    
    # 단면도 (갈색 계열 통일)
    mid = h // 2
    z = elevation[mid, :]
    
    brown_colors = ['#8B4513', '#A0522D', '#CD853F']  # 갈색 계열
    for i, (color, label) in enumerate(zip(brown_colors, ['표층', '중간층', '하층'])):
        ax2.fill_between(x_coords, z.min() - 80, z - i*3, color=color, alpha=0.8, label=label)
    
    ax2.plot(x_coords, z, color='#D2691E', linewidth=3)
    
    # 하천
    river_idx = np.argmin(z)
    ax2.fill_between(x_coords[max(0,river_idx-5):min(w,river_idx+6)], 
                     z[max(0,river_idx-5):min(w,river_idx+6)], 
                     z.min()+3, color='#2C3E50', alpha=0.9, label='하천')
    
    # 깊이
    ax2.annotate('', xy=(x_coords[river_idx], z.max()-5), 
                 xytext=(x_coords[river_idx], z[river_idx]+5),
                 arrowprops=dict(arrowstyle='<->', color='#FFA500', lw=2))
    ax2.text(x_coords[river_idx]+30, (z.max()+z[river_idx])/2, f'{depth:.0f}m', 
             fontsize=14, color='#FFA500', fontweight='bold')
    
    ax2.set_xlim(x_coords.min(), x_coords.max())
    ax2.set_ylim(z.min()-50, z.max()+20)
    ax2.set_xlabel('거리 (m)', fontsize=11, color='white')
    ax2.set_ylabel('고도 (m)', fontsize=11, color='white')
    ax2.set_title('횡단면', fontsize=12, fontweight='bold', color='white')
    ax2.legend(loc='upper right', fontsize=9, facecolor='#1a1a2e', labelcolor='white')
    ax2.tick_params(colors='white')
    ax2.grid(True, alpha=0.2, color='white')
    
    fig.suptitle(title, fontsize=14, fontweight='bold', y=1.02, color='white')
    plt.tight_layout()
    return fig


def render_meander_realistic(x, y, oxbow_lakes, sinuosity):
    """곡류 하천 렌더링 - 갈색 계열 통일"""
    try:
        fig, ax = plt.subplots(figsize=(14, 5), facecolor='#1a1a2e')
        ax.set_facecolor('#1a1a2e')
        
        # 범람원 배경 (갈색 계열)
        ax.axhspan(y.min()-100, y.max()+100, color='#3D2914', alpha=0.6)
        
        # 하천 (진한 갈색)
        ax.fill_between(x, y - 5, y + 5, color='#8B4513', alpha=0.9)
        ax.plot(x, y, color='#CD853F', linewidth=2)
        
        # 포인트바 (밝은 갈색)
        ddy = np.gradient(np.gradient(y))
        for i in range(20, len(x)-20, 20):
            if np.abs(ddy[i]) > 0.3:
                offset = -np.sign(ddy[i]) * 15
                ax.scatter(x[i], y[i] + offset, s=80, c='#D2691E', 
                          alpha=0.8, marker='o', zorder=5, edgecolors='#8B4513')
        
        # 우각호 (어두운 색)
        for lake_x, lake_y in oxbow_lakes:
            if len(lake_x) > 3:
                ax.fill(lake_x, lake_y, color='#2C3E50', alpha=0.8)
        
        ax.set_xlim(x.min() - 50, x.max() + 50)
        ax.set_ylim(y.min() - 80, y.max() + 80)
        ax.set_xlabel('하류 방향 (m)', fontsize=11, color='white')
        ax.set_ylabel('좌우 변위 (m)', fontsize=11, color='white')
        ax.set_title(f'곡류 하천 (굴곡도: {sinuosity:.2f})', fontsize=13, fontweight='bold', color='white')
        ax.tick_params(colors='white')
        ax.grid(True, alpha=0.15, color='white')
        
        # 범례
        from matplotlib.lines import Line2D
        legend_elements = [
            Line2D([0], [0], color='#8B4513', lw=6, label='하천'),
            Line2D([0], [0], marker='o', color='w', markerfacecolor='#D2691E', markersize=10, label='포인트바'),
            Line2D([0], [0], marker='s', color='w', markerfacecolor='#2C3E50', markersize=10, label='우각호'),
        ]
        ax.legend(handles=legend_elements, loc='upper right', fontsize=9, 
                  facecolor='#1a1a2e', labelcolor='white')
        
        return fig
    except Exception as e:
        fig, ax = plt.subplots(figsize=(12, 4), facecolor='#1a1a2e')
        ax.set_facecolor('#1a1a2e')
        ax.plot(x, y, color='#CD853F', linewidth=3, label='하천')
        ax.set_title(f'곡류 하천 (굴곡도: {sinuosity:.2f})', color='white')
        ax.legend(facecolor='#1a1a2e', labelcolor='white')
        ax.tick_params(colors='white')
        return fig


def render_v_valley_section(x, elevation, depth):
    """V자곡 단면 사실적 렌더링"""
    fig, ax = plt.subplots(figsize=(12, 5))
    
    mid = len(elevation) // 2
    z = elevation[mid, :]
    
    # 암석층 (층리 표현)
    for i, (color, y_offset) in enumerate([
        ('#8B7355', 0), ('#A0522D', -20), ('#CD853F', -40), ('#D2691E', -60)
    ]):
        z_layer = z - i * 5
        ax.fill_between(x, z.min() - 100, z_layer, color=color, alpha=0.7)
    
    # 현재 지형면
    ax.plot(x, z, 'k-', linewidth=3)
    
    # 하천
    river_idx = np.argmin(z)
    river_width = 30
    river_x = x[max(0, river_idx-3):min(len(x), river_idx+4)]
    river_z = z[max(0, river_idx-3):min(len(z), river_idx+4)]
    ax.fill_between(river_x, river_z, river_z.min()+3, color='#4169E1', alpha=0.8)
    
    # 깊이 화살표
    ax.annotate('', xy=(x[river_idx], z.max()), xytext=(x[river_idx], z[river_idx]),
                arrowprops=dict(arrowstyle='<->', color='red', lw=3))
    ax.text(x[river_idx]+50, (z.max()+z[river_idx])/2, f'깊이\n{depth:.0f}m', 
            fontsize=14, color='red', fontweight='bold', ha='left')
    
    ax.set_xlim(x.min(), x.max())
    ax.set_ylim(z.min()-50, z.max()+20)
    ax.set_xlabel('거리 (m)', fontsize=12)
    ax.set_ylabel('고도 (m)', fontsize=12)
    ax.set_title('V자곡 횡단면', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, linestyle='--')
    
    # 범례
    patches = [
        mpatches.Patch(color='#8B7355', label='암석층 1'),
        mpatches.Patch(color='#A0522D', label='암석층 2'),
        mpatches.Patch(color='#4169E1', label='하천')
    ]
    ax.legend(handles=patches, loc='upper right')
    
    return fig


# ============ 이론 설명 카드 ============

def show_theory_card(theory_dict, selected):
    """이론 설명 카드 표시"""
    info = theory_dict[selected]
    st.markdown(f"""
    <div class="theory-card">
        <div class="theory-title">📐 {selected}</div>
        <p><span class="formula">{info['formula']}</span></p>
        <p>{info['description']}</p>
        <p><b>주요 파라미터:</b> {', '.join(info['params'])}</p>
    </div>
    """, unsafe_allow_html=True)


# ============ 메인 앱 ============

def main():
    # ========== 최상단: 제작자 정보 ==========
    st.markdown("""
    <div style='background: linear-gradient(90deg, #1565C0, #42A5F5); padding: 8px 15px; border-radius: 8px; margin-bottom: 10px;'>
        <div style='display: flex; justify-content: space-between; align-items: center; color: white;'>
            <span style='font-size: 0.9rem;'>🌍 <b>Geo-Lab AI</b> - 이상적 지형 시뮬레이터</span>
            <span style='font-size: 0.8rem;'>제작: 2025 한백고등학교 김한솔T</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<p class="main-header">🌍 Geo-Lab AI: 이상적 지형 갤러리</p>', unsafe_allow_html=True)
    st.markdown("_교사를 위한 지형 형성과정 시각화 도구_")
    
    # ========== 방문자 카운터 (Session State) ==========
    if 'visitor_count' not in st.session_state:
        st.session_state.visitor_count = 1
    if 'today_count' not in st.session_state:
        st.session_state.today_count = 1
    
    # 상단 오른쪽 방문자 표시
    col_title, col_visitor = st.columns([4, 1])
    with col_visitor:
        st.markdown(f"""
        <div style='text-align: right; font-size: 0.85rem; color: #666;'>
            👤 오늘: <b>{st.session_state.today_count}</b> | 
            총: <b>{st.session_state.visitor_count}</b>
        </div>
        """, unsafe_allow_html=True)
    
    # ========== 사이드바: 가이드 & 업데이트 ==========
    st.sidebar.title("🌍 Geo-Lab AI")
    
    # 사용자 가이드
    with st.sidebar.expander("📚 사용자 가이드", expanded=False):
        st.markdown("""
        **🎯 이상적 지형 갤러리 (교사용)**
        1. 카테고리 선택 (하천, 빙하, 화산 등)
        2. 원하는 지형 선택
        3. 2D 평면도 확인
        4. "🔲 3D 뷰 보기" 클릭하여 3D 확인
        5. **⬇️ 아래로 스크롤하면 형성과정 애니메이션!**
        
        **💡 팁**
        - 슬라이더로 형성단계 조절 (0%→100%)
        - 자동재생 버튼으로 애니메이션 실행
        """)
    
    # 업데이트 내역
    with st.sidebar.expander("📋 업데이트 내역", expanded=False):
        st.markdown("""
        **v4.1 (2025-12-14)** 🆕
        - 이상적 지형 갤러리 31종 추가
        - 형성과정 애니메이션 기능
        - 7개 카테고리 분류
        
        **v4.0**
        - Project Genesis 통합 물리 엔진
        - 지형 시나리오 탭
        
        **v3.0**
        - 다중 이론 모델 비교
        - 스크립트 랩
        """)
    
    st.sidebar.markdown("---")
    
    # Resolution Control
    grid_size = st.sidebar.slider("해상도 (Grid Size)", 40, 150, 60, 10, help="낮을수록 빠름 / 높을수록 정밀")
    
    # ========== 탭 재배치: 갤러리 먼저 ==========
    t_gallery, t_genesis, t_scenarios, t_lab = st.tabs([
        "📖 이상적 지형 갤러리",
        "🌍 Project Genesis (시뮬레이션)", 
        "📚 지형 시나리오 (Landforms)", 
        "💻 스크립트 랩 (Lab)"
    ])
    
    # 1. Alias for Genesis Main Tab
    tab_genesis = t_genesis
    
    # 2. Ideal Landform Gallery (FIRST TAB - 교사용 메인)
    with t_gallery:
        st.header("📖 이상적 지형 갤러리")
        st.markdown("_교과서적인 지형 형태를 기하학적 모델로 시각화합니다._")
        
        # 강조 메시지
        st.info("💡 **Tip:** 지형 선택 후 **아래로 스크롤**하면 **🎬 형성 과정 애니메이션**을 확인할 수 있습니다!")
        
        # 카테고리별 지형
        st.sidebar.markdown("---")
        st.sidebar.subheader("🗂️ 지형 카테고리")
        category = st.sidebar.radio("카테고리 선택", [
            "🌊 하천 지형",
            "🔺 삼각주 유형", 
            "❄️ 빙하 지형",
            "🌋 화산 지형",
            "🦇 카르스트 지형",
            "🏜️ 건조 지형",
            "🏖️ 해안 지형"
        ], key="gallery_cat")
        
        # 카테고리별 옵션
        if category == "🌊 하천 지형":
            landform_options = {
                "📐 선상지 (Alluvial Fan)": "alluvial_fan",
                "🐍 자유곡류 (Free Meander)": "free_meander",
                "⛰️ 감입곡류+하안단구 (Incised Meander)": "incised_meander",
                "🏔️ V자곡 (V-Valley)": "v_valley",
                "🌊 망상하천 (Braided River)": "braided_river",
                "💧 폭포 (Waterfall)": "waterfall",
            }
        elif category == "🔺 삼각주 유형":
            landform_options = {
                "🔺 일반 삼각주 (Delta)": "delta",
                "🦶 조족상 삼각주 (Bird-foot)": "bird_foot_delta",
                "🌙 호상 삼각주 (Arcuate)": "arcuate_delta",
                "📍 첨두상 삼각주 (Cuspate)": "cuspate_delta",
            }
        elif category == "❄️ 빙하 지형":
            landform_options = {
                "❄️ U자곡 (U-Valley)": "u_valley",
                "🥣 권곡 (Cirque)": "cirque",
                "🏔️ 호른 (Horn)": "horn",
                "🌊 피오르드 (Fjord)": "fjord",
                "🥚 드럼린 (Drumlin)": "drumlin",
                "🪨 빙퇴석 (Moraine)": "moraine",
            }
        elif category == "🌋 화산 지형":
            landform_options = {
                "🛡️ 순상화산 (Shield)": "shield_volcano",
                "🗻 성층화산 (Stratovolcano)": "stratovolcano",
                "🕳️ 칼데라 (Caldera)": "caldera",
                "💧 화구호 (Crater Lake)": "crater_lake",
                "🟫 용암대지 (Lava Plateau)": "lava_plateau",
            }
        elif category == "🦇 카르스트 지형":
            landform_options = {
                "🕳️ 돌리네 (Doline)": "karst_doline",
            }
        elif category == "🏜️ 건조 지형":
            landform_options = {
                "🏜️ 바르한 사구 (Barchan)": "barchan",
                "🗿 메사/뷰트 (Mesa/Butte)": "mesa_butte",
            }
        else:  # 해안 지형
            landform_options = {
                "🏖️ 해안 절벽 (Coastal Cliff)": "coastal_cliff",
                "🌊 사취+석호 (Spit+Lagoon)": "spit_lagoon",
                "🏝️ 육계사주 (Tombolo)": "tombolo",
                "🌀 리아스 해안 (Ria Coast)": "ria_coast",
                "🌉 해식아치 (Sea Arch)": "sea_arch",
                "🏖️ 해안사구 (Coastal Dune)": "coastal_dune",
            }
        
        col_sel, col_view = st.columns([1, 3])
        
        with col_sel:
            selected_landform = st.selectbox("지형 선택", list(landform_options.keys()))
            landform_key = landform_options[selected_landform]
            
            # Parameters based on landform type
            st.markdown("---")
            st.subheader("⚙️ 파라미터")
            
            gallery_grid_size = st.slider("해상도", 50, 150, 80, 10, key="gallery_res")
            
            # 동적 지형 생성 (IDEAL_LANDFORM_GENERATORS 사용)
            if landform_key in IDEAL_LANDFORM_GENERATORS:
                generator = IDEAL_LANDFORM_GENERATORS[landform_key]
                
                # lambda인 경우 grid_size만 전달
                try:
                    elevation = generator(gallery_grid_size)
                except TypeError:
                    # stage 인자가 필요한 경우
                    elevation = generator(gallery_grid_size, 1.0)
            else:
                st.error(f"지형 '{landform_key}' 생성기를 찾을 수 없습니다.")
                elevation = np.zeros((gallery_grid_size, gallery_grid_size))
                
        with col_view:
            # 기본: 2D 평면도 (matplotlib) - WebGL 컨텍스트 사용 안 함
            import matplotlib.pyplot as plt
            import matplotlib.colors as mcolors
            
            fig_2d, ax = plt.subplots(figsize=(8, 8))
            
            # 지형 색상 맵
            cmap = plt.cm.terrain
            
            # 물이 있는 지형은 파란색 오버레이
            water_mask = elevation < 0
            
            im = ax.imshow(elevation, cmap=cmap, origin='upper')
            
            # 물 영역 표시
            if water_mask.any():
                water_overlay = np.ma.masked_where(~water_mask, np.ones_like(elevation))
                ax.imshow(water_overlay, cmap='Blues', alpha=0.6, origin='upper')
            
            ax.set_title(f"{selected_landform}", fontsize=14)
            ax.axis('off')
            
            # 컬러바
            cbar = plt.colorbar(im, ax=ax, shrink=0.6, label='고도 (m)')
            
            st.pyplot(fig_2d)
            plt.close(fig_2d)
            
            # 3D 보기 (버튼 클릭 시에만)
            if st.button("🔲 3D 뷰 보기", key="show_3d_view"):
                fig_3d = render_terrain_plotly(
                    elevation, 
                    f"{selected_landform} - 3D",
                    add_water=(landform_key in ["delta", "meander", "coastal_cliff", "fjord", "ria_coast", "spit_lagoon"]),
                    water_level=0 if landform_key in ["delta", "coastal_cliff"] else -999,
                    force_camera=True
                )
                st.plotly_chart(fig_3d, use_container_width=True)
            
            # Educational Description
            descriptions = {
                # 하천 지형
                "delta": "**삼각주**: 하천이 바다나 호수에 유입될 때 유속이 감소하여 운반 중이던 퇴적물이 쌓여 형성됩니다.",
                "alluvial_fan": "**선상지**: 산지에서 평지로 나오는 곳에서 경사가 급감하여 운반력이 줄어들면서 퇴적물이 부채꼴로 쌓입니다.",
                "meander": "**곡류**: 하천이 중류에서 측방 침식과 퇴적을 반복하며 S자 형태로 사행합니다.",
                "free_meander": "**자유곡류**: 범람원 위를 자유롭게 사행하는 곡류. 자연제방(Levee)과 배후습지가 특징입니다.",
                "incised_meander": "**감입곡류**: 융기로 인해 곡류가 기반암을 파고들면서 형성. 하안단구(River Terrace)가 함께 나타납니다.",
                "v_valley": "**V자곡**: 하천의 하방 침식이 우세하게 작용하여 형성된 V자 단면의 골짜기.",
                # 삼각주 유형
                "bird_foot_delta": "**조족상 삼각주**: 미시시피강형. 파랑 약하고 퇴적물 공급 많을 때 새발 모양으로 길게 뻗습니다.",
                "arcuate_delta": "**호상 삼각주**: 나일강형. 파랑과 퇴적물 공급이 균형을 이루어 부드러운 호(Arc) 형태.",
                "cuspate_delta": "**첨두상 삼각주**: 티베르강형. 파랑이 강해 삼각주가 뾰족한 화살촉 모양으로 형성.",
                # 빙하 지형
                "u_valley": "**U자곡**: 빙하의 침식으로 형성된 U자 단면의 골짜기. 측벽이 급하고 바닥이 평탄합니다.",
                "cirque": "**권곡(Cirque)**: 빙하의 시작점. 반원형 움푹 파인 지형으로, 빙하 융해 후 호수(Tarn)가 형성됩니다.",
                "horn": "**호른(Horn)**: 여러 권곡이 만나는 곳에서 침식되지 않고 남은 뾰족한 피라미드형 봉우리. (예: 마터호른)",
                "fjord": "**피오르드(Fjord)**: 빙하가 파낸 U자곡에 바다가 유입된 좁고 깊은 만. (예: 노르웨이)",
                "drumlin": "**드럼린(Drumlin)**: 빙하 퇴적물이 빙하 흐름 방향으로 길쭉하게 쌓인 타원형 언덕.",
                "moraine": "**빙퇴석(Moraine)**: 빙하가 운반한 암설이 퇴적된 지형. 측퇴석, 종퇴석 등이 있습니다.",
                # 화산 지형
                "shield_volcano": "**순상화산**: 유동성 높은 현무암질 용암이 완만하게(5-10°) 쌓여 방패 형태. (예: 하와이 마우나로아)",
                "stratovolcano": "**성층화산**: 용암과 화산쇄설물이 교대로 쌓여 급한(25-35°) 원뿔형. (예: 후지산, 백두산)",
                "caldera": "**칼데라**: 대규모 분화 후 마그마방 함몰로 형성된 거대한 분지. (예: 백두산 천지)",
                "crater_lake": "**화구호**: 화구나 칼데라에 물이 고여 형성된 호수. (예: 백두산 천지)",
                "lava_plateau": "**용암대지**: 열극 분출로 현무암질 용암이 넓게 펼쳐져 평탄한 대지 형성.",
                # 건조 지형
                "barchan": "**바르한 사구**: 바람이 한 방향에서 불 때 형성되는 초승달 모양의 사구.",
                "mesa_butte": "**메사/뷰트**: 차별침식으로 남은 탁상지. 메사는 크고 평탄, 뷰트는 작고 높습니다.",
                "karst_doline": "**돌리네(Doline)**: 석회암 용식으로 형성된 움푹 파인 와지. 카르스트 지형의 대표적 특징.",
                # 해안 지형
                "coastal_cliff": "**해안 절벽**: 파랑의 침식으로 형성된 절벽. 절벽 후퇴 시 시스택(Sea Stack)이 남기도 합니다.",
                "spit_lagoon": "**사취+석호**: 연안류에 의해 퇴적물이 길게 쌓인 사취가 만을 막아 석호(Lagoon)를 형성합니다.",
                "tombolo": "**육계사주(Tombolo)**: 연안류에 의한 퇴적으로 육지와 섬이 모래톱으로 연결된 지형.",
                "ria_coast": "**리아스식 해안**: 과거 하곡이 해수면 상승으로 침수되어 형성된 톱니 모양 해안선.",
                "sea_arch": "**해식아치(Sea Arch)**: 곶에서 파랑 침식으로 형성된 아치형 지형. 더 진행되면 시스택이 됩니다.",
                "coastal_dune": "**해안사구**: 해빈의 모래가 바람에 의해 육지 쪽으로 운반되어 형성된 모래 언덕.",
                # 하천 추가
                "braided_river": "**망상하천(Braided River)**: 퇴적물이 많고 경사가 급할 때 여러 수로가 갈라졌다 합쳐지는 하천.",
                "waterfall": "**폭포(Waterfall)**: 경암과 연암의 차별침식으로 형성된 급경사 낙차. 후퇴하며 협곡 형성.",
            }
            st.info(descriptions.get(landform_key, "설명 준비 중입니다."))
            
            # 형성과정 애니메이션 (지원 지형만)
            if landform_key in ANIMATED_LANDFORM_GENERATORS:
                st.markdown("---")
                st.subheader("🎬 형성 과정")
                
                # 단일 슬라이더로 형성 단계 조절
                stage_value = st.slider(
                    "형성 단계 (0% = 시작, 100% = 완성)", 
                    0.0, 1.0, 1.0, 0.05, 
                    key="gallery_stage_slider"
                )
                
                # 해당 단계 지형 생성
                anim_func = ANIMATED_LANDFORM_GENERATORS[landform_key]
                stage_elev = anim_func(gallery_grid_size, stage_value)
                
                # 물 생성
                stage_water = np.maximum(0, -stage_elev + 1.0)
                stage_water[stage_elev > 2] = 0
                
                # 특정 지형 물 처리
                if landform_key == "alluvial_fan":
                    apex_y = int(gallery_grid_size * 0.15)
                    center = gallery_grid_size // 2
                    for r in range(apex_y + 5):
                        for dc in range(-2, 3):
                            c = center + dc
                            if 0 <= c < gallery_grid_size:
                                stage_water[r, c] = 3.0
                
                # 단일 3D 렌더링 (WebGL 컨텍스트 절약)
                fig_stage = render_terrain_plotly(
                    stage_elev,
                    f"{selected_landform} - {int(stage_value*100)}%",
                    add_water=True,
                    water_depth_grid=stage_water,
                    water_level=-999,
                    force_camera=True
                )
                st.plotly_chart(fig_stage, use_container_width=True, key="stage_view")
                
                # 자동 재생 버튼
                if st.button("▶️ 자동 재생 (0%→100%)", key="auto_play"):
                    stage_container = st.empty()
                    prog = st.progress(0)
                    
                    for i in range(11):
                        s = i / 10.0
                        elev = anim_func(gallery_grid_size, s)
                        water = np.maximum(0, -elev + 1.0)
                        water[elev > 2] = 0
                        
                        fig = render_terrain_plotly(
                            elev, f"{selected_landform} - {int(s*100)}%",
                            add_water=True, water_depth_grid=water,
                            water_level=-999, force_camera=False
                        )
                        stage_container.plotly_chart(fig, use_container_width=True)
                        prog.progress(s)
                        
                        import time
                        time.sleep(0.4)
                    
                    st.success("✅ 완료!")
    
    # 3. Scenarios Sub-tabs
    with t_scenarios:
        tab_river, tab_coast, tab_karst, tab_volcano, tab_glacial, tab_arid, tab_plain = st.tabs([
            "🌊 하천", "🏖️ 해안", "🦇 카르스트", "🌋 화산", "❄️ 빙하", "🏜️ 건조", "🌾 평야"
        ])
        
    # 4. Lab Tab Alias
    tab_script = t_lab
    
    # ===== 하천 지형 (통합) =====
    with tab_river:
        # 하천 세부 탭
        river_sub = st.tabs(["🏔️ V자곡/협곡", "🐍 곡류/우각호", "🔺 삼각주", "📐 선상지", "📊 하안단구", "⚔️ 하천쟁탈", "🔄 감입곡류", "🌊 망상하천", "💧 폭포/포트홀", "🌾 범람원 상세"])
        
        # V자곡
        with river_sub[0]:
            c1, c2 = st.columns([1, 2])
            
            with c1:
                st.subheader("📚 이론 선택")
                v_theory = st.selectbox("침식 모델", list(V_VALLEY_THEORIES.keys()), key="v_th")
                show_theory_card(V_VALLEY_THEORIES, v_theory)
                
                st.markdown("---")
                st.subheader("⚙️ 파라미터")
                
                st.markdown("**⏱️ 시간 스케일**")
                time_scale = st.radio("시간 범위", ["초기 (0~만년)", "중기 (1만~100만년)", "장기 (100만~1억년)"], 
                                      key="v_ts", horizontal=True)
                
                if time_scale == "초기 (0~만년)":
                    v_time = st.slider("시간 (년)", 0, 10_000, 5_000, 500, key="v_t1")
                elif time_scale == "중기 (1만~100만년)":
                    v_time = st.slider("시간 (년)", 10_000, 1_000_000, 100_000, 10_000, key="v_t2")
                else:
                    v_time = st.slider("시간 (년)", 1_000_000, 100_000_000, 10_000_000, 1_000_000, key="v_t3")
                
                v_rock = st.slider("🪨 암석 경도", 0.1, 0.9, 0.4, 0.1, key="v_r")
                
                theory_key = V_VALLEY_THEORIES[v_theory]['key']
                params = {'K': 0.0001, 'rock_hardness': v_rock}
                
                if theory_key == "shear_stress":
                    params['tau_c'] = st.slider("τc (임계 전단응력)", 1.0, 20.0, 5.0, 1.0)
                elif theory_key == "detachment":
                    params['Qs'] = st.slider("Qs (퇴적물 공급비)", 0.0, 0.8, 0.3, 0.1)
            
            with c2:
                result = simulate_v_valley(theory_key, v_time, params, grid_size=grid_size)
                
                # 결과 표시 및 애니메이션
                col_res, col_anim = st.columns([3, 1])
                col_res.metric("V자곡 깊이", f"{result['depth']:.0f} m")
                col_res.metric("경과 시간", f"{v_time:,} 년")
                
                # Shared Plot Container
                plot_container = st.empty()
                
                # 애니메이션 재생
                do_loop = col_anim.checkbox("🔁 반복", key="v_loop")
                if col_anim.button("▶️ 재생", key="v_anim"):
                    n_reps = 3 if do_loop else 1
                    st.info(f"⏳ {v_time:,}년 시뮬레이션 재생 중...")
                    anim_prog = st.progress(0)
                    step_size = max(1, v_time // 20)
                    
                    for _ in range(n_reps):
                        for t in range(0, v_time + 1, step_size):
                            # 매 프레임 계산
                            r_step = simulate_v_valley(theory_key, t, params, grid_size=grid_size)
                            # Plotly 렌더링 (빠름)
                            fig_step = render_terrain_plotly(r_step['elevation'], 
                                                           f"V자곡 ({t:,}년)", 
                                                           add_water=True, water_level=r_step['elevation'].min() + 3,
                                                           texture_path="assets/reference/v_valley_texture.png", force_camera=False, water_depth_grid=r_step.get('water_depth'))
                            plot_container.plotly_chart(fig_step, use_container_width=True, key="v_plot_shared")
                            anim_prog.progress(min(1.0, t / v_time))
                            time.sleep(0.1)
                    st.success("재생 완료!")
                    # 마지막 상태 유지
                    result = r_step
                
                v_mode = st.radio("보기 모드", ["📊 시뮬레이션 (2D)", "🎮 인터랙티브 3D", "🛰️ 참고 사진"], horizontal=True, key="v_v")
                if "2D" in v_mode:
                    fig = render_v_valley_3d(result['elevation'], result['x'],
                                             f"V자곡 - {v_theory} ({v_time:,}년)",
                                             result['depth'])
                    plot_container.pyplot(fig)
                    plt.close()
                elif "3D" in v_mode:
                    st.caption("🖱️ **마우스 드래그로 회전, 스크롤로 줌**")
                    plotly_fig = render_terrain_plotly(
                        result['elevation'], 
                        f"V자곡 | 깊이: {result['depth']:.0f}m | {v_time:,}년",
                        add_water=True, water_level=result['elevation'].min() + 3,
                        texture_path="assets/reference/v_valley_texture.png",
                        water_depth_grid=result.get('water_depth')
                    )
                    plot_container.plotly_chart(plotly_fig, use_container_width=True, key="v_plot_shared")
                else:
                    image_stretch(st, "assets/reference/v_valley_satellite_1765437288622.png",
                             caption="V자곡 - Google Earth 스타일 (AI 생성)",
                             use_container_width=True)
        
        # 곡류
        with river_sub[1]:
            c1, c2 = st.columns([1, 2])
            
            with c1:
                st.subheader("📚 이론 선택")
                m_theory = st.selectbox("곡류 모델", list(MEANDER_THEORIES.keys()), key="m_th")
                show_theory_card(MEANDER_THEORIES, m_theory)
                
                st.markdown("---")
                st.subheader("⚙️ 파라미터")
                
                st.markdown("**⏱️ 시간 스케일**")
                m_time_scale = st.radio("시간 범위", ["초기 (0~만년)", "중기 (1만~100만년)", "장기 (100만~1억년)"], 
                                        key="m_ts", horizontal=True)
                
                if m_time_scale == "초기 (0~만년)":
                    m_time = st.slider("시간 (년)", 0, 10_000, 5_000, 500, key="m_t1")
                elif m_time_scale == "중기 (1만~100만년)":
                    m_time = st.slider("시간 (년)", 10_000, 1_000_000, 100_000, 10_000, key="m_t2")
                else:
                    m_time = st.slider("시간 (년)", 1_000_000, 100_000_000, 10_000_000, 1_000_000, key="m_t3")
                
                m_amp = st.slider("초기 진폭 (m)", 10, 80, 40, 10, key="m_a")
                
                theory_key = MEANDER_THEORIES[m_theory]['key']
                params = {'init_amplitude': m_amp, 'E0': 0.4}
                
                if theory_key == "ikeda_parker":
                    params['velocity'] = st.slider("U (유속 m/s)", 0.5, 3.0, 1.5, 0.5)
                elif theory_key == "seminara":
                    params['froude'] = st.slider("Fr (Froude수)", 0.1, 0.8, 0.3, 0.1)
            
            with c2:
                result = simulate_meander(theory_key, m_time, params)
                
                # 결과 및 애니메이션
                col_res, col_anim = st.columns([3, 1])
                col_res.metric("굴곡도", f"{result['sinuosity']:.2f}")
                # col_res.metric("우각호", f"{len(result.get('oxbow_lakes', []))} 개")
                
                do_loop = col_anim.checkbox("🔁 반복", key="m_loop")
                if col_anim.button("▶️ 재생", key="m_anim"):
                    n_reps = 3 if do_loop else 1
                    st.info(f"⏳ {m_time:,}년 시뮬레이션 재생 중 (3D)...")
                    anim_chart = st.empty()
                    anim_prog = st.progress(0)
                    step_size = max(1, m_time // 10) # 10 frames
                    
                    for _ in range(n_reps):
                        for t in range(0, m_time + 1, step_size):
                            r_step = simulate_meander(theory_key, t, params)
                            
                            # 3D 렌더링 (가볍게)
                            fig_step = render_terrain_plotly(
                                r_step['elevation'], 
                                f"자유 곡류 ({t:,}년)",
                                water_depth_grid=r_step['water_depth'],
                                texture_path="assets/reference/meander_texture.png"
                            )
                            anim_chart.plotly_chart(fig_step, use_container_width=True, key=f"m_anim_{t}")
                            
                            anim_prog.progress(min(1.0, t / m_time))
                    st.success("재생 완료!")
                    result = r_step
                
                v_mode = st.radio("보기 모드", ["🎮 인터랙티브 3D", "🛰️ 참고 사진"], horizontal=True, key="m_v")
                if "3D" in v_mode:
                    st.caption("🖱️ **마우스 드래그로 회전, 스크롤로 줌**")
                    fig = render_terrain_plotly(
                        result['elevation'], 
                        f"자유 곡류 - {MEANDER_THEORIES[m_theory].get('description', '')[:20]}...",
                        water_depth_grid=result['water_depth'],
                        texture_path="assets/reference/meander_texture.png"
                    )
                    st.plotly_chart(fig, use_container_width=True, key="m_plot")
                else:
                    image_stretch(st, "assets/reference/meander_satellite_1765437309640.png",
                             caption="곡류 하천 - Google Earth 스타일 (AI 생성)",
                             use_container_width=True)
        
        # 삼각주
        with river_sub[2]:
            c1, c2 = st.columns([1, 2])
            
            with c1:
                st.subheader("📚 이론 선택")
                d_theory = st.selectbox("삼각주 모델", list(DELTA_THEORIES.keys()), key="d_th")
                show_theory_card(DELTA_THEORIES, d_theory)
                
                st.markdown("---")
                st.subheader("⚙️ 파라미터")
                
                st.markdown("**⏱️ 시간 스케일**")
                d_time_scale = st.radio("시간 범위", ["초기 (0~만년)", "중기 (1만~100만년)", "장기 (100만~1억년)"], 
                                        key="d_ts", horizontal=True)
                
                if d_time_scale == "초기 (0~만년)":
                    d_time = st.slider("시간 (년)", 0, 10_000, 6_000, 500, key="d_t1")
                elif d_time_scale == "중기 (1만~100만년)":
                    d_time = st.slider("시간 (년)", 10_000, 1_000_000, 200_000, 10_000, key="d_t2")
                else:
                    d_time = st.slider("시간 (년)", 1_000_000, 100_000_000, 20_000_000, 1_000_000, key="d_t3")
                
                theory_key = DELTA_THEORIES[d_theory]['key']
                params = {}
                
                if theory_key == "galloway":
                    params['river'] = st.slider("하천 에너지", 0, 100, 55, 5) / 100
                    params['wave'] = st.slider("파랑 에너지", 0, 100, 30, 5) / 100
                    params['tidal'] = st.slider("조류 에너지", 0, 100, 15, 5) / 100
                elif theory_key == "orton":
                    params['grain'] = st.slider("입자크기 (0=세립, 1=조립)", 0.0, 1.0, 0.5, 0.1)
                    params['wave'] = st.slider("파랑 에너지", 0, 100, 30, 5) / 100
                    params['tidal'] = st.slider("조류 에너지", 0, 100, 20, 5) / 100
                elif theory_key == "bhattacharya":
                    params['Qsed'] = st.slider("퇴적물량 (톤/년)", 10, 100, 50, 10)
                    params['Hs'] = st.slider("유의파고 (m)", 0.5, 4.0, 1.5, 0.5)
                    params['Tr'] = st.slider("조차 (m)", 0.5, 6.0, 2.0, 0.5)
                
                st.markdown("---")
                params['accel'] = st.slider("⚡ 시뮬레이션 가속 (현실성 vs 속도)", 1.0, 20.0, 1.0, 0.5, 
                                          help="1.0은 물리적으로 정확한 속도입니다. 값을 높이면 지형 변화가 과장되어 빠르게 나타납니다.")
            
            with c2:
                result = simulate_delta(theory_key, d_time, params, grid_size=grid_size)
                
                # Shared Plot Container
                plot_container = st.empty()
                
                # 결과 및 애니메이션
                col_res, col_anim = st.columns([3, 1])
                col_res.metric("삼각주 유형", result['delta_type'])
                col_res.metric("면적", f"{result['area']:.2f} km²")
                
                do_loop = col_anim.checkbox("🔁 반복", key="d_loop")
                if col_anim.button("▶️ 재생", key="d_anim"):
                    n_reps = 3 if do_loop else 1
                    st.info(f"⏳ {d_time:,}년 시뮬레이션 재생 중...")
                    anim_prog = st.progress(0)
                    step_size = max(1, d_time // 20)
                    
                    for _ in range(n_reps):
                        for t in range(0, d_time + 1, step_size):
                            r_step = simulate_delta(theory_key, t, params, grid_size=grid_size)
                            fig_step = render_terrain_plotly(r_step['elevation'], 
                                                           f"{r_step['delta_type']} ({t:,}년)", 
                                                           add_water=True, water_level=0, 
                                                           texture_path="assets/reference/delta_texture.png", force_camera=False)
                            plot_container.plotly_chart(fig_step, use_container_width=True, key="d_plot_shared")
                            anim_prog.progress(min(1.0, t / d_time))
                            # time.sleep(0.1) 
                    
                    st.success("재생 완료!")
                    anim_prog.empty()
                    result = r_step
                
                v_mode = st.radio("보기 모드", ["📊 시뮬레이션 (2D)", "🎮 인터랙티브 3D", "🛰️ 참고 사진"], horizontal=True, key="d_v")
                if "2D" in v_mode:
                    fig = render_terrain_3d(result['elevation'],
                                            f"삼각주 - {d_theory} ({d_time:,}년)",
                                            add_water=True, water_level=0,
                                            view_elev=40, view_azim=240)
                    plot_container.pyplot(fig)
                    plt.close()
                elif "3D" in v_mode:
                    st.caption("🖱️ **마우스 드래그로 회전, 스크롤로 줌**")
                    plotly_fig = render_terrain_plotly(
                        result['elevation'], 
                        f"{result['delta_type']} | 면적: {result['area']:.2f} km² | {d_time:,}년",
                        add_water=True, water_level=0,
                        texture_path="assets/reference/delta_texture.png",
                        water_depth_grid=result.get('water_depth')
                    )
                    plot_container.plotly_chart(plotly_fig, use_container_width=True, key="d_plot_shared")
                else:
                    image_stretch(st, "assets/reference/delta_satellite_1765437326499.png",
                             caption="조족상 삼각주 - Google Earth 스타일 (AI 생성)",
                             use_container_width=True)
        
        # 선상지
        with river_sub[3]:
            c1, c2 = st.columns([1, 2])
            with c1:
                st.subheader("📐 선상지")
                st.info("산지에서 평지로 나오는 곳에 형성되는 부채꼴 퇴적 지형")
                st.markdown("---")
                af_time_scale = st.radio("시간 범위", ["초기 (0~만년)", "중기 (1만~100만년)"], key="af_ts", horizontal=True)
                if af_time_scale == "초기 (0~만년)":
                    af_time = st.slider("시간 (년)", 0, 10_000, 5_000, 500, key="af_t1")
                else:
                    af_time = st.slider("시간 (년)", 10_000, 1_000_000, 100_000, 10_000, key="af_t2")
                af_slope = st.slider("경사", 0.1, 0.9, 0.5, 0.1, key="af_s")
                af_sed = st.slider("퇴적물량", 0.1, 1.0, 0.5, 0.1, key="af_sed")
            with c2:
                result = simulate_alluvial_fan(af_time, {'slope': af_slope, 'sediment': af_sed}, grid_size=grid_size)
                col_res, col_anim = st.columns([3, 1])
                
                # Debug Display
                if 'debug_sed_max' in result:
                     st.caption(f"Debug: Max Sediment = {result['debug_sed_max']:.2f}m | Steps = {result.get('debug_steps')}")
                     
                col_res.metric("선상지 면적", f"{result['area']:.2f} km²")
                col_res.metric("선상지 반경", f"{result['radius']:.2f} km")
                
                # Shared Plot Container
                plot_container = st.empty()
                
                # Render using sediment grid for accurate coloring
                fig = render_terrain_plotly(
                    result['elevation'], 
                    "선상지 (Alluvial Fan)",
                    water_depth_grid=result.get('water_depth'),
                    sediment_grid=result.get('sediment'), # Pass sediment layer
                    force_camera=False
                )
                plot_container.plotly_chart(fig, use_container_width=True, key="af_plot_final")
                
                do_loop = col_anim.checkbox("🔁 반복", key="af_loop")
                if col_anim.button("▶️ 재생", key="af_anim"):
                    n_reps = 3 if do_loop else 1
                    st.info(f"⏳ {af_time:,}년 시뮬레이션 재생 중...")
                    anim_prog = st.progress(0)
                    step_size = max(1, af_time // 20)
                    for _ in range(n_reps):
                        for t in range(0, af_time + 1, step_size):
                            r_step = simulate_alluvial_fan(t, {'slope': af_slope, 'sediment': af_sed}, grid_size=grid_size)
                            fig_step = render_terrain_plotly(
                                r_step['elevation'], 
                                f"선상지 ({t:,}년)", 
                                add_water=False, 
                                force_camera=False, 
                                water_depth_grid=r_step.get('water_depth'),
                                sediment_grid=r_step.get('sediment')
                            )
                            plot_container.plotly_chart(fig_step, use_container_width=True, key="af_plot_shared")
                            anim_prog.progress(min(1.0, t / af_time))
                            time.sleep(0.1)
                    st.success("재생 완료!")
                    anim_prog.empty()
                    result = r_step
                v_mode = st.radio("보기 모드", ["📊 시뮬레이션 (2D)", "🎮 인터랙티브 3D"], horizontal=True, key="af_v")
                if "2D" in v_mode:
                    fig = render_terrain_3d(result['elevation'], f"선상지 ({af_time:,}년)", add_water=False)
                    plot_container.pyplot(fig)
                    plt.close()
                else:
                    st.caption("🖱️ **마우스 드래그로 회전, 스크롤로 줌**")
                    plotly_fig = render_terrain_plotly(result['elevation'], f"선상지 | 면적: {result['area']:.2f}km² | {af_time:,}년", add_water=False, texture_path="assets/reference/alluvial_fan_texture.png", water_depth_grid=result.get('water_depth'))
                    plot_container.plotly_chart(plotly_fig, use_container_width=True, key="af_plot_shared")
        
        # 하안단구
        with river_sub[4]:
            c1, c2 = st.columns([1, 2])
            with c1:
                st.subheader("📊 하안단구")
                st.info("하천 옆에 계단 모양으로 형성된 평탄면 (구 범람원)")
                st.markdown("---")
                rt_time_scale = st.radio("시간 범위", ["초기 (0~만년)", "중기 (1만~100만년)"], key="rt_ts", horizontal=True)
                if rt_time_scale == "초기 (0~만년)":
                    rt_time = st.slider("시간 (년)", 0, 10_000, 5_000, 500, key="rt_t1")
                else:
                    rt_time = st.slider("시간 (년)", 10_000, 1_000_000, 100_000, 10_000, key="rt_t2")
                rt_uplift = st.slider("지반 융기율", 0.1, 1.0, 0.5, 0.1, key="rt_u")
                rt_n = st.slider("단구면 수", 1, 5, 3, 1, key="rt_n")
            with c2:
                result = simulate_river_terrace(rt_time, {'uplift': rt_uplift, 'n_terraces': rt_n}, grid_size=grid_size)
                col_res, col_anim = st.columns([3, 1])
                col_res.metric("형성된 단구면", f"{result['n_terraces']} 단")
                
                # Shared Plot Container
                plot_container = st.empty()

                do_loop = col_anim.checkbox("🔁 반복", key="rt_loop")
                if col_anim.button("▶️ 재생", key="rt_anim"):
                    n_reps = 3 if do_loop else 1
                    st.info(f"⏳ {rt_time:,}년 시뮬레이션 재생 중...")
                    anim_prog = st.progress(0)
                    step_size = max(1, rt_time // 20)
                    for _ in range(n_reps):
                        for t in range(0, rt_time + 1, step_size):
                            r_step = simulate_river_terrace(t, {'uplift': rt_uplift, 'n_terraces': rt_n}, grid_size=grid_size)
                            fig_step = render_terrain_plotly(r_step['elevation'], f"하안단구 ({t:,}년)", add_water=True, water_level=r_step['elevation'].min()+5, force_camera=False, water_depth_grid=r_step.get('water_depth'))
                            plot_container.plotly_chart(fig_step, use_container_width=True, key="rt_plot_shared")
                            anim_prog.progress(min(1.0, t / rt_time))
                            time.sleep(0.1)
                    st.success("재생 완료!")
                    anim_prog.empty()
                    result = r_step
                v_mode = st.radio("보기 모드", ["📊 시뮬레이션 (2D)", "🎮 인터랙티브 3D"], horizontal=True, key="rt_v")
                if "2D" in v_mode:
                    fig = render_terrain_3d(result['elevation'], f"하안단구 ({af_time:,}년)", add_water=True, water_level=result['elevation'].min()+5)
                    plot_container.pyplot(fig)
                    plt.close()
                else:
                    st.caption("🖱️ **마우스 드래그로 회전, 스크롤로 줌**")
                    plotly_fig = render_terrain_plotly(result['elevation'], f"하안단구 | {result['n_terraces']}단 | {rt_time:,}년", add_water=True, water_level=result['elevation'].min()+5, water_depth_grid=result.get('water_depth'))
                    plot_container.plotly_chart(plotly_fig, use_container_width=True, key="rt_plot_shared")
        
        # 하천쟁탈
        with river_sub[5]:
            c1, c2 = st.columns([1, 2])
            with c1:
                st.subheader("⚔️ 하천쟁탈")
                st.info("침식력이 강한 하천이 인접 하천의 상류를 빼앗는 현상")
                st.markdown("---")
                sp_time_scale = st.radio("시간 범위", ["초기 (0~만년)", "중기 (1만~100만년)"], key="sp_ts", horizontal=True)
                if sp_time_scale == "초기 (0~만년)":
                    sp_time = st.slider("시간 (년)", 0, 10_000, 5_000, 500, key="sp_t1")
                else:
                    sp_time = st.slider("시간 (년)", 10_000, 1_000_000, 100_000, 10_000, key="sp_t2")
                sp_diff = st.slider("침식력 차이", 0.3, 0.9, 0.7, 0.1, key="sp_d")
            with c2:
                result = simulate_stream_piracy(sp_time, {'erosion_diff': sp_diff}, grid_size=grid_size)
                col_res, col_anim = st.columns([3, 1])
                if result['captured']:
                    col_res.success(f"⚔️ 하천쟁탈 발생! ({result['capture_time']:,}년)")
                else:
                    col_res.warning("아직 하천쟁탈이 발생하지 않음")
                
                # Shared Plot Container
                plot_container = st.empty()

                do_loop = col_anim.checkbox("🔁 반복", key="sp_loop")
                if col_anim.button("▶️ 재생", key="sp_anim"):
                    n_reps = 3 if do_loop else 1
                    st.info(f"⏳ {sp_time:,}년 시뮬레이션 재생 중...")
                    anim_prog = st.progress(0)
                    step_size = max(1, sp_time // 20)
                    for _ in range(n_reps):
                        for t in range(0, sp_time + 1, step_size):
                            r_step = simulate_stream_piracy(t, {'erosion_diff': sp_diff}, grid_size=grid_size)
                            status = "쟁탈 진행 중"
                            if r_step['captured']: status = "쟁탈 발생!"
                            fig_step = render_terrain_plotly(r_step['elevation'], f"하천쟁탈 | {status} | {t:,}년", add_water=False, force_camera=False, water_depth_grid=r_step.get('water_depth'))
                            plot_container.plotly_chart(fig_step, use_container_width=True, key="sp_plot_shared")
                            anim_prog.progress(min(1.0, t / sp_time))
                            time.sleep(0.1)
                    st.success("재생 완료!")
                    anim_prog.empty()
                    result = r_step
                v_mode = st.radio("보기 모드", ["📊 시뮬레이션 (2D)", "🎮 인터랙티브 3D"], horizontal=True, key="sp_v")
                if "2D" in v_mode:
                    fig = render_terrain_3d(result['elevation'], f"하천쟁탈 ({sp_time:,}년)", add_water=True, water_level=result['elevation'].min()+3)
                    plot_container.pyplot(fig)
                    plt.close()
                else:
                    st.caption("🖱️ **마우스 드래그로 회전, 스크롤로 줌**")
                    status = "쟁탈 완료" if result['captured'] else "진행 중"
                    plotly_fig = render_terrain_plotly(result['elevation'], f"하천쟁탈 | {status} | {sp_time:,}년", add_water=False, water_depth_grid=result.get('water_depth'))
                    plot_container.plotly_chart(plotly_fig, use_container_width=True, key="sp_plot_shared")
        
        # 감입곡류
        with river_sub[6]:
            c1, c2 = st.columns([1, 2])
            with c1:
                st.subheader("🔄 감입곡류")
                st.info("지반 융기로 곡류 하천이 깊이 파고든 지형")
                st.markdown("---")
                em_time_scale = st.radio("시간 범위", ["초기 (0~만년)", "중기 (1만~100만년)"], key="em_ts", horizontal=True)
                if em_time_scale == "초기 (0~만년)":
                    em_time = st.slider("시간 (년)", 0, 10_000, 5_000, 500, key="em_t1")
                else:
                    em_time = st.slider("시간 (년)", 10_000, 1_000_000, 100_000, 10_000, key="em_t2")
                em_uplift = st.slider("융기율", 0.1, 1.0, 0.5, 0.1, key="em_u")
                em_type = st.radio("유형", ["착근곡류 (U자)", "감입곡류 (V자)"], key="em_type", horizontal=True)
            with c2:
                inc_type = 'U' if "착근" in em_type else 'V'
                result = simulate_entrenched_meander(em_time, {'uplift': em_uplift, 'incision_type': inc_type}, grid_size=grid_size)
                col_res, col_anim = st.columns([3, 1])
                col_res.metric("유형", result['type'])
                col_res.metric("깊이", f"{result['depth']:.0f} m")
                
                # Shared Plot Container
                plot_container = st.empty()

                do_loop = col_anim.checkbox("🔁 반복", key="em_loop")
                if col_anim.button("▶️ 재생", key="em_anim"):
                    n_reps = 3 if do_loop else 1
                    st.info(f"⏳ {em_time:,}년 시뮬레이션 재생 중...")
                    anim_prog = st.progress(0)
                    step_size = max(1, em_time // 20)
                    for _ in range(n_reps):
                        for t in range(0, em_time + 1, step_size):
                            r_step = simulate_entrenched_meander(t, {'uplift': em_uplift, 'incision_type': inc_type}, grid_size=grid_size)
                            fig_step = render_terrain_plotly(r_step['elevation'], f"{r_step['type']} ({t:,}년)", add_water=True, water_level=r_step['elevation'].min()+5, force_camera=False, water_depth_grid=r_step.get('water_depth'))
                            plot_container.plotly_chart(fig_step, use_container_width=True, key="em_plot_shared")
                            anim_prog.progress(min(1.0, t / em_time))
                            time.sleep(0.1)
                    st.success("재생 완료!")
                    anim_prog.empty()
                    result = r_step
                v_mode = st.radio("보기 모드", ["📊 시뮬레이션 (2D)", "🎮 인터랙티브 3D", "🛰️ 참고 사진"], horizontal=True, key="em_v")
                if "2D" in v_mode:
                    fig = render_terrain_3d(result['elevation'], f"{result['type']} ({em_time:,}년)", add_water=True, water_level=result['elevation'].min()+5)
                    plot_container.pyplot(fig)
                    plt.close()
                elif "3D" in v_mode:
                    st.caption("🖱️ **마우스 드래그로 회전, 스크롤로 줌**")
                    plotly_fig = render_terrain_plotly(result['elevation'], f"{result['type']} | 깊이: {result['depth']:.0f}m | {em_time:,}년", add_water=True, water_level=result['elevation'].min()+2, water_depth_grid=result.get('water_depth'))
                    plot_container.plotly_chart(plotly_fig, use_container_width=True, key="em_plot_shared")
                else:
                    image_stretch(st, "assets/reference/entrenched_meander_ref_1765496053723.png", caption="감입 곡류 (Entrenched Meander) - AI 생성", use_container_width=True)
        
        # 망상하천
        with river_sub[7]:
            c1, c2 = st.columns([1, 2])
            with c1:
                st.subheader("🌊 망상 하천")
                st.info("퇴적물이 많고 유로가 얽혀 있는 하천")
                st.markdown("---")
                bs_time = st.slider("시간 (년)", 0, 10_000, 1000, 100, key="bs_t")
                bs_sed = st.slider("퇴적물량", 0.1, 1.0, 0.8, 0.1, key="bs_sed")
                bs_n = st.slider("수로 개수", 3, 10, 5, 1, key="bs_n")
            with c2:
                result = simulate_braided_stream(bs_time, {'sediment': bs_sed, 'n_channels': bs_n}, grid_size=grid_size)
                # 중첩 제거
                cm1, col_anim = st.columns([3, 1])
                cm1.metric("유형", result['type'])
                # Shared Plot Container
                plot_container = st.empty()

                do_loop = col_anim.checkbox("🔁 반복", key="bs_loop")
                if col_anim.button("▶️ 재생", key="bs_anim"):
                    n_reps = 3 if do_loop else 1
                    for _ in range(n_reps):
                        for t in range(0, bs_time+1, max(1, bs_time//20)):
                            r_step = simulate_braided_stream(t, {'sediment': bs_sed, 'n_channels': bs_n}, grid_size=grid_size)
                            fig_step = render_terrain_plotly(r_step['elevation'], f"망상하천 ({t}년)", add_water=True, water_level=r_step['elevation'].min()+0.5, force_camera=False, water_depth_grid=r_step.get('water_depth'))
                            plot_container.plotly_chart(fig_step, use_container_width=True, key="bs_plot_shared")
                            time.sleep(0.1)
                
                v_mode = st.radio("보기 모드", ["🎮 인터랙티브 3D", "🛰️ 참고 사진"], horizontal=True, key="bs_v")
                if "3D" in v_mode:
                    fig = render_terrain_plotly(result['elevation'], f"망상하천 ({bs_time}년)", add_water=True, water_level=result['elevation'].min()+0.5, texture_path="assets/reference/braided_river_texture.png", water_depth_grid=result.get('water_depth'))
                    plot_container.plotly_chart(fig, use_container_width=True, key="bs_plot_shared")
                else:
                    image_stretch(st, "assets/reference/braided_river_1765410638302.png", caption="망상 하천 (AI 생성)", use_container_width=True)

        # 폭포
        with river_sub[8]:
            c1, c2 = st.columns([1, 2])
            with c1:
                st.subheader("💧 폭포/포트홀")
                st.info("두부 침식으로 후퇴하는 폭포")
                st.markdown("---")
                wf_time = st.slider("시간 (년)", 0, 10_000, 2000, 100, key="wf_t")
                wf_rate = st.slider("후퇴 속도", 0.1, 2.0, 0.5, 0.1, key="wf_r")
            with c2:
                result = simulate_waterfall(wf_time, {'retreat_rate': wf_rate}, grid_size=grid_size)
                cm1, col_anim = st.columns([3, 1])
                cm1.metric("총 후퇴 거리", f"{result['retreat']:.1f} m")
                # Shared Plot Container
                plot_container = st.empty()

                do_loop = col_anim.checkbox("🔁 반복", key="wf_loop")
                if col_anim.button("▶️ 재생", key="wf_anim"):
                    n_reps = 3 if do_loop else 1
                    for _ in range(n_reps):
                        for t in range(0, wf_time+1, max(1, wf_time//20)):
                            r_step = simulate_waterfall(t, {'retreat_rate': wf_rate}, grid_size=grid_size)
                            fig_step = render_terrain_plotly(r_step['elevation'], f"폭포 ({t}년)", add_water=True, water_level=90, force_camera=False, water_depth_grid=r_step.get('water_depth'))
                            plot_container.plotly_chart(fig_step, use_container_width=True, key="wf_plot_shared")
                            time.sleep(0.1)
                
                v_mode = st.radio("보기 모드", ["🎮 인터랙티브 3D", "🛰️ 참고 사진"], horizontal=True, key="wf_v")
                if "3D" in v_mode:
                    fig = render_terrain_plotly(result['elevation'], f"폭포 ({wf_time}년)", add_water=True, water_level=90, water_depth_grid=result.get('water_depth'))
                    plot_container.plotly_chart(fig, use_container_width=True, key="wf_plot_shared")
                else:
                    image_stretch(st, "assets/reference/waterfall_gorge_formation_1765410495876.png", caption="폭포 및 협곡 (AI 생성)", use_container_width=True)

        # 범람원 상세
        with river_sub[9]:
            c1, c2 = st.columns([1, 2])
            with c1:
                st.subheader("🌾 자연제방/배후습지")
                st.info("홍수 시 퇴적 차이로 형성되는 미지형")
                st.markdown("---")
                lv_time = st.slider("시간 (년)", 0, 5000, 1000, 100, key="lv_t")
                lv_freq = st.slider("범람 빈도", 0.1, 1.0, 0.5, 0.1, key="lv_f")
            with c2:
                result = simulate_levee(lv_time, {'flood_freq': lv_freq}, grid_size=grid_size)
                cm1, col_anim = st.columns([3, 1])
                cm1.metric("제방 높이", f"{result['levee_height']:.1f} m")
                # Shared Plot Container
                plot_container = st.empty()

                do_loop = col_anim.checkbox("🔁 반복", key="lv_loop")
                if col_anim.button("▶️ 재생", key="lv_anim"):
                    n_reps = 3 if do_loop else 1
                    for _ in range(n_reps):
                        for t in range(0, lv_time+1, max(1, lv_time//20)):
                            r_step = simulate_levee(t, {'flood_freq': lv_freq}, grid_size=grid_size)
                            fig_step = render_terrain_plotly(r_step['elevation'], f"범람원 ({t}년)", add_water=True, water_level=42, force_camera=False, water_depth_grid=r_step.get('water_depth'))
                            plot_container.plotly_chart(fig_step, use_container_width=True, key="lv_plot_shared")
                            time.sleep(0.1)
                
                v_mode = st.radio("보기 모드", ["🎮 인터랙티브 3D", "🛰️ 참고 사진"], horizontal=True, key="lv_v")
                if "3D" in v_mode:
                    fig = render_terrain_plotly(result['elevation'], f"범람원 상세 ({lv_time}년)", add_water=True, water_level=42, water_depth_grid=result.get('water_depth'))
                    plot_container.plotly_chart(fig, use_container_width=True, key="lv_plot_shared")
                else:
                    image_stretch(st, "assets/reference/floodplain_landforms_1765436731483.png", caption="범람원 - 자연제방과 배후습지 (AI 생성)", use_container_width=True)
    
    # ===== 해안 지형 =====
    with tab_coast:
        c1, c2 = st.columns([1, 2])
        
        with c1:
            st.subheader("📚 이론 선택")
            co_theory = st.selectbox("해안 침식 모델", list(COASTAL_THEORIES.keys()), key="co_th")
            show_theory_card(COASTAL_THEORIES, co_theory)
            
            st.markdown("---")
            st.subheader("⚙️ 파라미터")
            
            # 3단계 시간 스케일
            st.markdown("**⏱️ 시간 스케일**")
            co_time_scale = st.radio("시간 범위", ["초기 (0~만년)", "중기 (1만~100만년)", "장기 (100만~1억년)"], 
                                     key="co_ts", horizontal=True)
            
            if co_time_scale == "초기 (0~만년)":
                co_time = st.slider("시간 (년)", 0, 10_000, 3_000, 500, key="co_t1")
            elif co_time_scale == "중기 (1만~100만년)":
                co_time = st.slider("시간 (년)", 10_000, 1_000_000, 50_000, 10_000, key="co_t2")
            else:
                co_time = st.slider("시간 (년)", 1_000_000, 100_000_000, 5_000_000, 1_000_000, key="co_t3")
            
            co_wave = st.slider("🌊 파고 (m)", 0.5, 5.0, 2.0, 0.5, key="co_w")
            co_rock = st.slider("🪨 암석 저항", 0.1, 0.9, 0.5, 0.1, key="co_r")
            
            theory_key = COASTAL_THEORIES[co_theory]['key']
            params = {'wave_height': co_wave, 'rock_resistance': co_rock}
            
            if theory_key == "cliff_retreat":
                params['Hc'] = st.slider("Hc (임계파고)", 0.5, 3.0, 1.5, 0.5)
            elif theory_key == "cerc":
                params['theta'] = st.slider("θ (파향각)", 0, 45, 15, 5)
            elif theory_key == "spit":
                params['drift_strength'] = st.slider("연안류 강도", 0.1, 1.0, 0.5, 0.1)
                params['sand_supply'] = st.slider("모래 공급량", 0.1, 1.0, 0.5, 0.1)
                params['wave_angle'] = st.slider("파랑 각도", 0, 90, 45, 5)
            elif theory_key == "tombolo":
                params['island_dist'] = st.slider("섬 거리", 0.1, 1.0, 0.5, 0.1)
                params['island_size'] = st.slider("섬 크기", 0.1, 1.0, 0.5, 0.1)
                params['wave_energy'] = st.slider("파랑 에너지", 0.1, 1.0, 0.5, 0.1)
            elif theory_key == "tidal_flat":
                params['tidal_range'] = st.slider("조차(m)", 0.5, 8.0, 4.0, 0.5)
            elif theory_key == "spit":
                params['drift_strength'] = st.slider("연안류 강도", 0.1, 1.0, 0.5, 0.1)
                params['sand_supply'] = st.slider("모래 공급량", 0.1, 1.0, 0.5, 0.1)
                params['wave_angle'] = st.slider("파랑 각도", 0, 90, 45, 5)
            elif theory_key == "tombolo":
                params['island_dist'] = st.slider("섬 거리", 0.1, 1.0, 0.5, 0.1)
                params['island_size'] = st.slider("섬 크기", 0.1, 1.0, 0.5, 0.1)
                params['wave_energy'] = st.slider("파랑 에너지", 0.1, 1.0, 0.5, 0.1)
            elif theory_key == "tidal_flat":
                params['tidal_range'] = st.slider("조차(m)", 0.5, 8.0, 4.0, 0.5)
        
        with c2:
            if theory_key in ["spit", "tombolo", "tidal_flat"]:
                result = simulate_coastal_deposition(theory_key, co_time, params, grid_size=grid_size)
                
                # 퇴적 지형 결과 (메트릭 없음, 유형만 표시)
                st.info(f"지형 유형: {result['type']}")
                
                # Shared Plot Container
                plot_container = st.empty()

                # 애니메이션
                _, col_anim = st.columns([3, 1])
                do_loop = col_anim.checkbox("🔁 반복", key="co_loop_dep")
                if col_anim.button("▶️ 재생", key="co_anim_dep"):
                    n_reps = 3 if do_loop else 1
                    st.info(f"⏳ {co_time:,}년 시뮬레이션 재생 중...")
                    anim_prog = st.progress(0)
                    step_size = max(1, co_time // 20)
                    
                    for _ in range(n_reps):
                        for t in range(0, co_time + 1, step_size):
                            r_step = simulate_coastal_deposition(theory_key, t, params, grid_size=grid_size)
                            fig_step = render_terrain_plotly(r_step['elevation'], 
                                                           f"{r_step['type']} ({t:,}년)", 
                                                           add_water=True, water_level=0, force_camera=False)
                            plot_container.plotly_chart(fig_step, use_container_width=True, key="co_dep_plot_shared")
                            anim_prog.progress(min(1.0, t / co_time))
                            time.sleep(0.1)
                    st.success("재생 완료!")
                    anim_prog.empty()
                    result = r_step
            else:
                result = simulate_coastal(theory_key, co_time, params, grid_size=grid_size)
                
                # Shared Plot Container (Erosion)
                plot_container = st.empty()

                # 결과 및 애니메이션
                # 침식 지형 전용 메트릭
                cm1, cm2, cm3, col_anim = st.columns([1, 1, 1, 1])
                cm1.metric("해식애 후퇴", f"{result['cliff_retreat']:.1f} m")
                cm2.metric("파식대 폭", f"{result['platform_width']:.1f} m")
                cm3.metric("노치 깊이", f"{result['notch_depth']:.1f} m")
                
                do_loop = col_anim.checkbox("🔁 반복", key="co_loop")
                if col_anim.button("▶️ 재생", key="co_anim"):
                    n_reps = 3 if do_loop else 1
                    st.info(f"⏳ {co_time:,}년 시뮬레이션 재생 중...")
                    anim_prog = st.progress(0)
                    step_size = max(1, co_time // 20)
                    
                    for _ in range(n_reps):
                        for t in range(0, co_time + 1, step_size):
                            r_step = simulate_coastal(theory_key, t, params, grid_size=grid_size)
                            fig_step = render_terrain_plotly(r_step['elevation'], 
                                                           f"해안침식 ({t:,}년)", 
                                                           add_water=True, water_level=0, force_camera=False)
                            plot_container.plotly_chart(fig_step, use_container_width=True, key="co_plot_shared")
                            anim_prog.progress(min(1.0, t / co_time))
                            time.sleep(0.1)
                    st.success("재생 완료!")
                    anim_prog.empty()
                    result = r_step
            
            v_mode = st.radio("보기 모드", ["📊 시뮬레이션 (2D)", "🎮 인터랙티브 3D", "🛰️ 참고 사진"], horizontal=True, key="co_v")
            if "2D" in v_mode:
                fig = render_terrain_3d(result['elevation'],
                                        f"해안 지형 - {co_theory} ({co_time:,}년)",
                                        add_water=True, water_level=0,
                                        view_elev=35, view_azim=210)
                plot_container.pyplot(fig)
                plt.close()
            elif "3D" in v_mode:
                st.caption("🖱️ **마우스 드래그로 회전, 스크롤로 줌**")
                plotly_fig = render_terrain_plotly(
                    result['elevation'], 
                    f"해안침식 | 후퇴: {result['cliff_retreat']:.1f}m | {co_time:,}년",
                    add_water=True, water_level=0
                )
                plot_container.plotly_chart(plotly_fig, use_container_width=True, key="co_plot_shared")
            else:
                if theory_key == "cliff_retreat":
                    image_stretch(st, "assets/reference/sea_stack_arch_ref_1765495979396.png", caption="시스택 & 해식아치 - AI 생성", use_container_width=True)
                elif theory_key in ["tombolo", "spit"]:
                    image_stretch(st, "assets/reference/tombolo_sandbar_ref_1765495999194.png", caption="육계도 & 사취 - AI 생성", use_container_width=True)
                else:
                    st.info("이 지형에 대한 참고 사진이 아직 없습니다.")
    
    # ===== 카르스트 =====
    # ===== 카르스트 =====
    with tab_karst:
        ka_subs = st.tabs(["🏜️ 돌리네 (Doline)", "⛰️ 탑 카르스트 (Tower)", "🦇 석회동굴 (Cave)"])

        # 돌리네
        with ka_subs[0]:
            c1, c2 = st.columns([1, 2])
            with c1:
                st.subheader("🏜️ 돌리네 (Doline)")
                ka_theory = st.selectbox("용식 모델", list(KARST_THEORIES.keys()), key="ka_th")
                show_theory_card(KARST_THEORIES, ka_theory)
                st.markdown("---")
                ka_time = st.slider("시간 (년)", 0, 100_000, 10_000, 500, key="ka_t")
                ka_co2 = st.slider("CO₂ 농도", 0.1, 1.0, 0.5, 0.1, key="ka_co2")
                ka_rain = st.slider("강수량", 0.1, 1.0, 0.5, 0.1, key="ka_rain")
            with c2:
                params = {'co2': ka_co2, 'rainfall': ka_rain}
                result = simulate_karst(KARST_THEORIES[ka_theory]['key'], ka_time, params, grid_size=grid_size)
                # Shared Plot Container
                plot_container = st.empty()
                
                _, col_anim = st.columns([3, 1])
                do_loop = col_anim.checkbox("🔁 반복", key="ka_loop")
                if col_anim.button("▶️ 재생", key="ka_anim"):
                    n_reps = 3 if do_loop else 1
                    for _ in range(n_reps):
                        for t in range(0, ka_time+1, max(1, ka_time//20)):
                            r = simulate_karst(KARST_THEORIES[ka_theory]['key'], t, params, grid_size=grid_size)
                            f = render_terrain_plotly(r['elevation'], f"카르스트 ({t:,}년)", add_water=False, force_camera=False)
                            plot_container.plotly_chart(f, use_container_width=True, key="ka_plot_shared")
                            time.sleep(0.1)
                
                v_mode = st.radio("보기 모드", ["📊 시뮬레이션 (2D)", "🎮 인터랙티브 3D", "🛰️ 참고 사진"], horizontal=True, key="ka_v")
                if "2D" in v_mode:
                    f = render_terrain_plotly(result['elevation'], f"카르스트 ({ka_time:,}년)", add_water=False)
                    plot_container.plotly_chart(f, use_container_width=True, key="ka_plot_shared")
                elif "3D" in v_mode:
                    st.caption("🖱️ **마우스 드래그로 회전/줌**")
                    f = render_terrain_plotly(result['elevation'], f"돌리네 | {ka_time:,}년", add_water=False)
                    plot_container.plotly_chart(f, use_container_width=True, key="ka_plot_shared")
                else:
                    image_stretch(st, "assets/reference/doline_sinkhole_1765436375545.png", caption="돌리네 (AI 생성)", use_container_width=True)

        # 탑 카르스트
        with ka_subs[1]:
            c1, c2 = st.columns([1, 2])
            with c1:
                st.subheader("⛰️ 탑 카르스트 (Tower)")
                st.info("차별 용식으로 평야 위에 남은 석회암 봉우리들")
                st.markdown("---")
                tk_time = st.slider("시간 (년)", 0, 500_000, 100_000, 10_000, key="tk_t")
                tk_rate = st.slider("용식률", 0.1, 1.0, 0.5, 0.1, key="tk_r")
            with c2:
                result = simulate_tower_karst(tk_time, {'erosion_rate': tk_rate}, grid_size=grid_size)
                # Shared Plot Container
                plot_container = st.empty()
                
                _, col_anim = st.columns([3, 1])
                do_loop = col_anim.checkbox("🔁 반복", key="tk_loop")
                if col_anim.button("▶️ 재생", key="tk_anim"):
                     n_reps = 3 if do_loop else 1
                     for _ in range(n_reps):
                         for t in range(0, tk_time+1, max(1, tk_time//20)):
                             r = simulate_tower_karst(t, {'erosion_rate': tk_rate}, grid_size=grid_size)
                             f = render_terrain_plotly(r['elevation'], f"탑 카르스트 ({t:,}년)", add_water=False, force_camera=False)
                             plot_container.plotly_chart(f, use_container_width=True, key="tk_plot_shared")
                             time.sleep(0.1)
                
                v_mode = st.radio("보기 모드", ["📊 시뮬레이션 (2D)", "🎮 인터랙티브 3D", "🛰️ AI 위성사진"], horizontal=True, key="tk_v")
                if "2D" in v_mode:
                     f = render_terrain_plotly(result['elevation'], f"탑 카르스트 ({tk_time:,}년)", add_water=False)
                     plot_container.plotly_chart(f, use_container_width=True, key="tk_plot_shared")
                elif "3D" in v_mode:
                     st.caption("🖱️ **마우스 드래그로 회전/줌**")
                     f = render_terrain_plotly(result['elevation'], f"탑 카르스트 | {tk_time:,}년", add_water=False, texture_path="assets/reference/tower_karst_texture.png")
                     plot_container.plotly_chart(f, use_container_width=True, key="tk_plot_shared")
                else:
                    image_stretch(st, "assets/reference/tower_karst_ref.png", caption="탑 카르스트 (Guilin) - AI 생성", use_container_width=True)

        # 석회동굴
        with ka_subs[2]:
            c1, c2 = st.columns([1, 2])
            with c1:
                st.subheader("🦇 석회동굴 (Cave)")
                st.info("지하수의 용식과 침전으로 형성된 동굴과 생성물 (석순)")
                st.markdown("---")
                cv_time = st.slider("시간 (년)", 0, 500_000, 50_000, 5000, key="cv_t")
                cv_rate = st.slider("성장 속도", 0.1, 1.0, 0.5, 0.1, key="cv_r")
            with c2:
                result = simulate_cave(cv_time, {'rate': cv_rate}, grid_size=grid_size)
                # Shared Plot Container
                plot_container = st.empty()
                
                _, col_anim = st.columns([3, 1])
                do_loop = col_anim.checkbox("🔁 반복", key="cv_loop")
                if col_anim.button("▶️ 재생", key="cv_anim"):
                     n_reps = 3 if do_loop else 1
                     for _ in range(n_reps):
                         for t in range(0, cv_time+1, max(1, cv_time//20)):
                             r = simulate_cave(t, {'rate': cv_rate}, grid_size=grid_size)
                             f = render_terrain_plotly(r['elevation'], f"석회동굴 ({t:,}년)", add_water=False, force_camera=False)
                             plot_container.plotly_chart(f, use_container_width=True, key="cv_plot_shared")
                             time.sleep(0.1)
                
                v_mode = st.radio("보기 모드", ["📊 시뮬레이션 (2D)", "🎮 인터랙티브 3D", "🛰️ 참고 사진"], horizontal=True, key="cv_v")
                if "2D" in v_mode:
                     f = render_terrain_plotly(result['elevation'], f"석회동굴 바닥 ({cv_time:,}년)", add_water=False)
                     plot_container.plotly_chart(f, use_container_width=True, key="cv_plot_shared")
                elif "3D" in v_mode:
                     st.caption("🖱️ **마우스 드래그로 회전/줌**")
                     f = render_terrain_plotly(result['elevation'], f"석회동굴 | {cv_time:,}년", add_water=False)
                     plot_container.plotly_chart(f, use_container_width=True, key="cv_plot_shared")
                else:
                    image_stretch(st, "assets/reference/cave_ref.png", caption="석회동굴 내부 - AI 생성", use_container_width=True)
    
    # ===== 화산 =====
    with tab_volcano:
        vo_subs = st.tabs(["🌋 화산체/칼데라", "🏜️ 용암 대지", "🏛️ 주상절리"])
        
        # 기본 화산
        with vo_subs[0]:
            c1, c2 = st.columns([1, 2])
            with c1:
                st.subheader("화산체/칼데라")
                vo_theory = st.selectbox("화산 유형", list(VOLCANIC_THEORIES.keys()), key="vo_th")
                show_theory_card(VOLCANIC_THEORIES, vo_theory)
                st.markdown("---")
                vo_time = st.slider("시간 (년)", 0, 2_000_000, 500_000, 10_000, key="vo_t")
                vo_rate = st.slider("분출률", 0.1, 1.0, 0.5, 0.1, key="vo_rate")
                params = {'eruption_rate': vo_rate}
                if VOLCANIC_THEORIES[vo_theory]['key'] == "shield":
                     params['viscosity'] = st.slider("용암 점성", 0.1, 0.5, 0.3, 0.1)
                elif VOLCANIC_THEORIES[vo_theory]['key'] == "caldera":
                     params['caldera_size'] = st.slider("칼데라 크기", 0.3, 1.0, 0.5, 0.1)
            with c2:
                result = simulate_volcanic(VOLCANIC_THEORIES[vo_theory]['key'], vo_time, params, grid_size=grid_size)
                # Shared Plot Container
                plot_container = st.empty()
                
                _, col_anim = st.columns([3, 1])
                if col_anim.button("▶️ 재생", key="vo_anim"):
                    n_reps = 3 if do_loop else 1
                    for _ in range(n_reps):
                        for t in range(0, vo_time+1, max(1, vo_time//20)):
                            r = simulate_volcanic(VOLCANIC_THEORIES[vo_theory]['key'], t, params, grid_size=grid_size)
                            f = render_terrain_plotly(r['elevation'], f"{r['type']} ({t:,}년)", add_water=False, texture_path="assets/reference/volcano_texture.png", force_camera=False)
                            plot_container.plotly_chart(f, use_container_width=True, key="vo_plot_shared")
                            time.sleep(0.1)
                v_mode = st.radio("보기 모드", ["🎮 인터랙티브 3D", "🛰️ 참고 사진"], horizontal=True, key="vo_v")
                if "3D" in v_mode:
                    f = render_terrain_plotly(result['elevation'], f"{result['type']} ({vo_time:,}년)", add_water=False, texture_path="assets/reference/volcano_texture.png")
                    plot_container.plotly_chart(f, use_container_width=True, key="vo_plot_shared")
                else:
                    # 화산 유형에 따라 다른 이미지
                    if "shield" in VOLCANIC_THEORIES[vo_theory]['key']:
                        image_stretch(st, "assets/reference/shield_vs_stratovolcano_1765436448576.png", caption="순상 화산 (AI 생성)", use_container_width=True)
                    else:
                        image_stretch(st, "assets/reference/caldera_formation_1765436466778.png", caption="칼데라 (AI 생성)", use_container_width=True)

        # 용암 대지
        with vo_subs[1]:
            c1, c2 = st.columns([1, 2])
            with c1:
                st.subheader("🏜️ 용암 대지")
                st.info("유동성이 큰 현무암질 용암이 열하 분출하여 형성된 대지")
                st.markdown("---")
                lp_time = st.slider("시간 (년)", 0, 1_000_000, 100_000, 10_000, key="lp_t")
                lp_rate = st.slider("분출률", 0.1, 1.0, 0.8, 0.1, key="lp_r")
            with c2:
                result = simulate_lava_plateau(lp_time, {'eruption_rate': lp_rate}, grid_size=grid_size)
                # Shared Plot Container
                plot_container = st.empty()
                
                _, col_anim = st.columns([3, 1])
                do_loop = col_anim.checkbox("🔁 반복", key="lp_loop")
                if col_anim.button("▶️ 재생", key="lp_anim"):
                     n_reps = 3 if do_loop else 1
                     for _ in range(n_reps):
                         for t in range(0, lp_time+1, max(1, lp_time//20)):
                             r = simulate_lava_plateau(t, {'eruption_rate': lp_rate}, grid_size=grid_size)
                             f = render_terrain_plotly(r['elevation'], f"용암대지 ({t:,}년)", add_water=False, force_camera=False)
                             plot_container.plotly_chart(f, use_container_width=True, key="lp_plot_shared")
                             time.sleep(0.1)
                
                v_mode = st.radio("보기 모드", ["📊 시뮬레이션 (2D)", "🎮 인터랙티브 3D", "🛰️ AI 위성사진"], horizontal=True, key="lp_v")
                if "2D" in v_mode:
                     f = render_terrain_plotly(result['elevation'], f"용암대지 ({lp_time:,}년)", add_water=False)
                     plot_container.plotly_chart(f, use_container_width=True, key="lp_plot_shared")
                elif "3D" in v_mode:
                     st.caption("🖱️ **마우스 드래그로 회전/줌**")
                     f = render_terrain_plotly(result['elevation'], f"용암대지 | {lp_time:,}년", add_water=False)
                     plot_container.plotly_chart(f, use_container_width=True, key="lp_plot_shared")
                else:
                    image_stretch(st, "assets/reference/lava_plateau_ref.png", caption="용암대지 (Iceland) - AI 생성", use_container_width=True)

        # 주상절리
        with vo_subs[2]:
            c1, c2 = st.columns([1, 2])
            with c1:
                st.subheader("🏛️ 주상절리")
                st.info("용암의 냉각 및 수축으로 형성된 육각형 기둥 패턴")
                st.markdown("---")
                cj_time = st.slider("시간 (년)", 0, 50_000, 5000, 100, key="cj_t")
                cj_rate = st.slider("침식(풍화)률", 0.1, 1.0, 0.5, 0.1, key="cj_r")
            with c2:
                result = simulate_columnar_jointing(cj_time, {'erosion_rate': cj_rate}, grid_size=grid_size)
                # Shared Plot Container
                plot_container = st.empty()
                
                _, col_anim = st.columns([3, 1])
                do_loop = col_anim.checkbox("🔁 반복", key="cj_loop")
                if col_anim.button("▶️ 재생", key="cj_anim"):
                     n_reps = 3 if do_loop else 1
                     for _ in range(n_reps):
                         for t in range(0, cj_time+1, max(1, cj_time//20)):
                             r = simulate_columnar_jointing(t, {'erosion_rate': cj_rate}, grid_size=grid_size)
                             f = render_terrain_plotly(r['elevation'], f"주상절리 ({t:,}년)", add_water=True, water_level=80, force_camera=False)
                             plot_container.plotly_chart(f, use_container_width=True, key="cj_plot_shared")
                             time.sleep(0.1)
                
                v_mode = st.radio("보기 모드", ["📊 시뮬레이션 (2D)", "🎮 인터랙티브 3D", "🛰️ 참고 사진"], horizontal=True, key="cj_v")
                if "2D" in v_mode:
                     f = render_terrain_plotly(result['elevation'], f"주상절리 ({cj_time:,}년)", add_water=True, water_level=80)
                     plot_container.plotly_chart(f, use_container_width=True, key="cj_plot_shared")
                elif "3D" in v_mode:
                     st.caption("🖱️ **마우스 드래그로 회전/줌**")
                     f = render_terrain_plotly(result['elevation'], f"주상절리 | {cj_time:,}년", add_water=True, water_level=80)
                     plot_container.plotly_chart(f, use_container_width=True, key="cj_plot_shared")
                else:
                    image_stretch(st, "assets/reference/columnar_ref.png", caption="주상절리 (Basalt Columns) - AI 생성", use_container_width=True)
    
    # ===== 빙하 =====
    with tab_glacial:
        gl_subs = st.tabs(["🏔️ U자곡/피오르", "🥣 권곡 (Cirque)", "🛤️ 모레인 (Moraine)"])
        
        # U자곡 (기존)
        with gl_subs[0]:
            c1, c2 = st.columns([1, 2])
            with c1:
                st.subheader("U자곡/피오르")
                gl_type = st.radio("유형", ["빙식곡 (U자곡)", "피오르 (Fjord)"], key="gl_t_sel")
                gl_theory = gl_type
                st.markdown("---")
                gl_time = st.slider("시간 (년)", 0, 1_000_000, 500_000, 10_000, key="gl_t")
                gl_ice = st.slider("빙하 두께", 0.1, 1.0, 0.5, 0.1, key="gl_ice")
            with c2:
                key = "fjord" if "피오르" in gl_type else "erosion"
                result = simulate_glacial(key, gl_time, {'ice_thickness': gl_ice}, grid_size=grid_size)
                
                # Shared Plot Container
                plot_container = st.empty()
                
                _, col_anim = st.columns([3, 1])
                do_loop = col_anim.checkbox("🔁 반복", key="gl_loop")
                if col_anim.button("▶️ 재생", key="gl_anim"):
                    n_reps = 3 if do_loop else 1
                    for _ in range(n_reps):
                        for t in range(0, gl_time+1, max(1, gl_time//20)):
                            r = simulate_glacial(key, t, {'ice_thickness': gl_ice}, grid_size=grid_size)
                            tex_path = "assets/reference/fjord_texture.png" if key == "fjord" else None
                            f = render_terrain_plotly(r['elevation'], f"{gl_type} ({t:,}년)", add_water=(key=="fjord"), water_level=100 if key=="fjord" else 0, texture_path=tex_path, force_camera=False)
                            plot_container.plotly_chart(f, use_container_width=True, key="gl_plot_shared")
                            time.sleep(0.1)
                
                tex_path = "assets/reference/fjord_texture.png" if key == "fjord" else None
                f = render_terrain_plotly(result['elevation'], f"{gl_type} ({gl_time:,}년)", add_water=(key=="fjord"), water_level=100 if key=="fjord" else 0, texture_path=tex_path)
                v_mode = st.radio("보기 모드", ["🎮 인터랙티브 3D", "🛰️ 참고 사진"], horizontal=True, key="gl_v")
                if "3D" in v_mode:
                    plot_container.plotly_chart(f, use_container_width=True, key="gl_plot_shared")
                else:
                    image_stretch(st, "assets/reference/fjord_valley_ref_1765495963491.png", caption="피오르 (Fjord) - AI 생성", use_container_width=True)

        # 권곡
        with gl_subs[1]:
            c1, c2 = st.columns([1, 2])
            with c1:
                st.subheader("🥣 권곡 (Cirque)")
                st.info("빙하의 회전 슬라이딩으로 형성된 반원형 와지")
                st.markdown("---")
                cq_time = st.slider("시간 (년)", 0, 500_000, 100_000, 10_000, key="cq_t")
                cq_rate = st.slider("침식률", 0.1, 1.0, 0.5, 0.1, key="cq_r")
            with c2:
                result = simulate_cirque(cq_time, {'erosion_rate': cq_rate}, grid_size=grid_size)
                # Shared Plot Container
                plot_container = st.empty()
                
                _, col_anim = st.columns([3, 1])
                do_loop = col_anim.checkbox("🔁 반복", key="cq_loop")
                if col_anim.button("▶️ 재생", key="cq_anim"):
                    n_reps = 3 if do_loop else 1
                    for _ in range(n_reps):
                        for t in range(0, cq_time+1, max(1, cq_time//20)):
                            r = simulate_cirque(t, {'erosion_rate': cq_rate}, grid_size=grid_size)
                            f = render_terrain_plotly(r['elevation'], f"권곡 ({t:,}년)", add_water=False, force_camera=False)
                            plot_container.plotly_chart(f, use_container_width=True, key="cq_plot_shared")
                            time.sleep(0.1)
                
                v_mode = st.radio("보기 모드", ["📊 시뮬레이션 (2D)", "🎮 인터랙티브 3D", "🛰️ AI 위성사진"], horizontal=True, key="cq_v")
                if "2D" in v_mode:
                     f = render_terrain_plotly(result['elevation'], f"권곡 ({cq_time:,}년)", add_water=False)
                     plot_container.plotly_chart(f, use_container_width=True, key="cq_plot_shared")
                elif "3D" in v_mode:
                     st.caption("🖱️ **마우스 드래그로 회전/줌**")
                     f = render_terrain_plotly(result['elevation'], f"권곡 | {cq_time:,}년", add_water=False, texture_path="assets/reference/cirque_texture.png")
                     plot_container.plotly_chart(f, use_container_width=True, key="cq_plot_shared")
                else:
                    image_stretch(st, "assets/reference/cirque_ref.png", caption="권곡 (Glacial Cirque) - AI 생성", use_container_width=True)

        # 모레인
        with gl_subs[2]:
            c1, c2 = st.columns([1, 2])
            with c1:
                st.subheader("🛤️ 모레인 (Moraine)")
                st.info("빙하가 운반한 퇴적물이 쌓인 제방")
                st.markdown("---")
                mo_time = st.slider("시간 (년)", 0, 100_000, 20_000, 1000, key="mo_t")
                mo_sup = st.slider("퇴적물 공급", 0.1, 1.0, 0.5, 0.1, key="mo_s")
            with c2:
                result = simulate_moraine(mo_time, {'debris_supply': mo_sup}, grid_size=grid_size)
                # Shared Plot Container
                plot_container = st.empty()
                
                _, col_anim = st.columns([3, 1])
                do_loop = col_anim.checkbox("🔁 반복", key="mo_loop")
                if col_anim.button("▶️ 재생", key="mo_anim"):
                    n_reps = 3 if do_loop else 1
                    for _ in range(n_reps):
                        for t in range(0, mo_time+1, max(1, mo_time//20)):
                            r = simulate_moraine(t, {'debris_supply': mo_sup}, grid_size=grid_size)
                            f = render_terrain_plotly(r['elevation'], f"모레인 ({t:,}년)", add_water=False, force_camera=False)
                            plot_container.plotly_chart(f, use_container_width=True, key="mo_plot_shared")
                            time.sleep(0.1)
                
                v_mode = st.radio("보기 모드", ["📊 시뮬레이션 (2D)", "🎮 인터랙티브 3D", "🛰️ AI 위성사진"], horizontal=True, key="mo_v")
                if "2D" in v_mode:
                     f = render_terrain_plotly(result['elevation'], f"모레인 ({mo_time:,}년)", add_water=False)
                     plot_container.plotly_chart(f, use_container_width=True, key="mo_plot_shared")
                elif "3D" in v_mode:
                     st.caption("🖱️ **마우스 드래그로 회전/줌**")
                     f = render_terrain_plotly(result['elevation'], f"모레인 | {mo_time:,}년", add_water=False)
                     plot_container.plotly_chart(f, use_container_width=True, key="mo_plot_shared")
                else:
                    image_stretch(st, "assets/reference/moraine_ref.png", caption="모레인 (Moraine) - AI 생성", use_container_width=True)
    
    # ===== 건조 =====
    with tab_arid:
        c1, c2 = st.columns([1, 2])
        with c1:
            st.subheader("📚 이론 선택")
            ar_theory = st.selectbox("건조 지형", list(ARID_THEORIES.keys()), key="ar_th")
            show_theory_card(ARID_THEORIES, ar_theory)
            st.markdown("---")
            st.subheader("⚙️ 파라미터")
            ar_time_scale = st.radio("시간 범위", ["초기 (0~만년)", "중기 (1만~100만년)", "장기 (100만~1억년)"], key="ar_ts", horizontal=True)
            if ar_time_scale == "초기 (0~만년)":
                ar_time = st.slider("시간 (년)", 0, 10_000, 3_000, 500, key="ar_t1")
            elif ar_time_scale == "중기 (1만~100만년)":
                ar_time = st.slider("시간 (년)", 10_000, 1_000_000, 50_000, 10_000, key="ar_t2")
            else:
                ar_time = st.slider("시간 (년)", 1_000_000, 100_000_000, 5_000_000, 1_000_000, key="ar_t3")
            ar_wind = st.slider("풍속", 0.1, 1.0, 0.5, 0.1, key="ar_wind")
            params = {'wind_speed': ar_wind}
            if ARID_THEORIES[ar_theory]['key'] == "mesa":
                params['rock_hardness'] = st.slider("암석 경도", 0.1, 0.9, 0.5, 0.1)
        with c2:
            result = simulate_arid(ARID_THEORIES[ar_theory]['key'], ar_time, params, grid_size=grid_size)
            
            col_res, col_anim = st.columns([3, 1])
            col_res.metric("지형 유형", result['type'])
            
            # Shared Plot Container
            plot_container = st.empty()
            
            do_loop = col_anim.checkbox("🔁 반복", key="ar_loop")
            if col_anim.button("▶️ 재생", key="ar_anim"):
                n_reps = 3 if do_loop else 1
                st.info(f"⏳ {ar_time:,}년 시뮬레이션 재생 중...")
                anim_prog = st.progress(0)
                step_size = max(1, ar_time // 20)
                
                for _ in range(n_reps):
                    for t in range(0, ar_time + 1, step_size):
                        r_step = simulate_arid(ARID_THEORIES[ar_theory]['key'], t, params, grid_size=grid_size)
                        fig_step = render_terrain_plotly(r_step['elevation'], 
                                                       f"{r_step['type']} ({t:,}년)", 
                                                       add_water=False, force_camera=False)
                        plot_container.plotly_chart(fig_step, use_container_width=True, key="ar_plot_shared")
                        anim_prog.progress(min(1.0, t / ar_time))
                        time.sleep(0.1)
                st.success("재생 완료!")
                anim_prog.empty()
                result = r_step
            v_mode = st.radio("보기 모드", ["📊 시뮬레이션 (2D)", "🎮 인터랙티브 3D", "🛰️ 참고 사진"], horizontal=True, key="ar_v")
            if "2D" in v_mode:
                fig = render_terrain_3d(result['elevation'], f"건조 - {ar_theory} ({ar_time:,}년)", add_water=False)
                plot_container.pyplot(fig)
                plt.close()
            elif "3D" in v_mode:
                st.caption("🖱️ **마우스 드래그로 회전, 스크롤로 줌**")
                
                # 바르한 사구인 경우 텍스처 적용
                tex_path = None
                if ARID_THEORIES[ar_theory]['key'] == "barchan":
                    tex_path = "assets/reference/barchan_dune_texture_topdown_1765496401371.png"
                
                plotly_fig = render_terrain_plotly(result['elevation'], 
                                                 f"{result['type']} | {ar_time:,}년", 
                                                 add_water=False,
                                                 texture_path=tex_path)
                plot_container.plotly_chart(plotly_fig, use_container_width=True, key="ar_plot_shared")
            else:
                # 이론 키에 따라 이미지 분기
                tk = ARID_THEORIES[ar_theory]['key']
                if tk == "barchan":
                    image_stretch(st, "assets/reference/barchan_dune_ref_1765496023768.png", caption="바르한 사구 - AI 생성", use_container_width=True)
                elif tk == "mesa":
                    image_stretch(st, "assets/reference/mesa_butte_ref_1765496038880.png", caption="메사 & 뷰트 - AI 생성", use_container_width=True)
                else:
                    st.info("준비 중입니다.")
    
    # ===== 평야 =====
    with tab_plain:
        c1, c2 = st.columns([1, 2])
        with c1:
            st.subheader("📚 이론 선택")
            pl_theory = st.selectbox("평야 모델", list(PLAIN_THEORIES.keys()), key="pl_th")
            show_theory_card(PLAIN_THEORIES, pl_theory)
            st.markdown("---")
            st.subheader("⚙️ 파라미터")
            pl_time_scale = st.radio("시간 범위", ["초기 (0~만년)", "중기 (1만~100만년)", "장기 (100만~1억년)"], key="pl_ts", horizontal=True)
            if pl_time_scale == "초기 (0~만년)":
                pl_time = st.slider("시간 (년)", 0, 10_000, 5_000, 500, key="pl_t1")
            elif pl_time_scale == "중기 (1만~100만년)":
                pl_time = st.slider("시간 (년)", 10_000, 1_000_000, 100_000, 10_000, key="pl_t2")
            else:
                pl_time = st.slider("시간 (년)", 1_000_000, 100_000_000, 10_000_000, 1_000_000, key="pl_t3")
            pl_flood = st.slider("범람 빈도", 0.1, 1.0, 0.5, 0.1, key="pl_flood")
            params = {'flood_freq': pl_flood}
        with c2:
            result = simulate_plain(PLAIN_THEORIES[pl_theory]['key'], pl_time, params, grid_size=grid_size)
            # Shared Plot Container
            plot_container = st.empty()
            
            st.metric("평야 유형", result['type'])
            v_mode = st.radio("보기 모드", ["📊 시뮬레이션 (2D)", "🎮 인터랙티브 3D", "🛰️ 참고 사진"], horizontal=True, key="pl_v")
            if "2D" in v_mode:
                fig = render_terrain_3d(result['elevation'], f"평야 - {pl_theory} ({pl_time:,}년)", add_water=True, water_level=15)
                plot_container.pyplot(fig)
                plt.close()
            elif "3D" in v_mode:
                st.caption("🖱️ **마우스 드래그로 회전, 스크롤로 줌**")
                plotly_fig = render_terrain_plotly(result['elevation'], f"{result['type']} | {pl_time:,}년", add_water=True, water_level=15)
                plot_container.plotly_chart(plotly_fig, use_container_width=True, key="pl_plot_shared")
            else:
                 st.info("준비 중입니다.")

    # ===== 스크립트 랩 =====
    with tab_script:
        st.header("💻 스크립트 랩 (Script Lab)")
        st.markdown("---")
        st.info("💡 파이썬 코드로 나만의 지형 생성 알고리즘을 실험해보세요!\n\n사용 가능한 변수: `elevation` (고도), `grid` (지형객체), `np` (NumPy), `dt` (시간), `hydro` (수력), `erosion` (침식)")
        
        col_code, col_view = st.columns([1, 1])
        
        with col_code:
            st.subheader("📜 코드 에디터")
            
            # 예제 스크립트
            example_scripts = {
                "01. 초기화 (평지)": """# 100x100 평지 생성
# elevation: 2D numpy array (float)
elevation[:] = 0.0""",
                "02. 사인파 언덕": """# 사인파 형태의 언덕 생성
import numpy as np
rows, cols = elevation.shape
for r in range(rows):
    # r(행)에 따라 높이가 변함
    elevation[r, :] = np.sin(r / 10.0) * 20.0 + 20.0""",
                "03. 랜덤 노이즈": """# 무작위 지형 생성
import numpy as np
# 0 ~ 50m 사이의 랜덤 높이
elevation[:] = np.random.rand(*elevation.shape) * 50.0""",
                "04. 침식 시뮬레이션 Loop": """# 500년 동안 강수 및 침식 시뮬레이션
# *주의: 반복문이 많으면 느려질 수 있습니다.*
import numpy as np

# 1. 초기 지형 설정 (경사면)
rows, cols = elevation.shape
if np.max(elevation) < 1.0: # 평지라면 초기화
    for r in range(rows):
        elevation[r, :] = 50.0 - (r/rows)*50.0

# 2. 시뮬레이션 루프 (100 step)
steps = 50
for i in range(steps):
    # 강수 및 유량 계산 (Precipitation=0.05)
    discharge = hydro.route_flow_d8(precipitation=0.05)
    
    # 하천 침식 (Stream Power)
    erosion.stream_power_erosion(discharge, dt=1.0)
    
    # 진행상황 출력 (마지막만)
    if i == steps - 1:
        print(f"Simulation done: {steps} steps")
"""
            }
            
            selected_example = st.selectbox("예제 코드 선택", list(example_scripts.keys()))
            default_code = example_scripts[selected_example]
            
            user_script = st.text_area("Python Script", value=default_code, height=500, key="editor")
            
            if st.button("🚀 스크립트 실행 (Run)", type="primary"):
                # 1. 그리드 초기화 (기존 session_state 사용 or 새로 생성)
                if 'script_grid' not in st.session_state:
                    st.session_state['script_grid'] = WorldGrid(100, 100, 10.0)
                
                grid_obj = st.session_state['script_grid']
                executor = ScriptExecutor(grid_obj)
                
                with st.spinner("코드를 실행 중입니다..."):
                    # 실행 시작 시간
                    start_t = time.time()
                    success, msg = executor.execute(user_script)
                    end_t = time.time()
                
                if success:
                    st.success(f"✅ 실행 성공 ({end_t - start_t:.3f}s)")
                    if msg != "실행 성공":
                        st.info(f"메시지: {msg}")
                    # 결과 갱신 트리거
                    st.session_state['script_run_count'] = st.session_state.get('script_run_count', 0) + 1
                else:
                    st.error(f"❌ 실행 오류:\n{msg}")
                    
        with col_view:
            st.subheader("👀 결과 뷰어")
            
            # Grid 객체 가져오기
            if 'script_grid' not in st.session_state:
                 st.session_state['script_grid'] = WorldGrid(100, 100, 10.0)
            
            grid_show = st.session_state['script_grid']
            
            # 시각화 옵션
            show_water = st.checkbox("물 표시 (해수면 0m)", value=True)
            
            # 3D 렌더링
            fig = render_terrain_plotly(
                grid_show.elevation, 
                "Script Result", 
                add_water=show_water, 
                water_level=0.0
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # 통계 정보
            st.markdown(f"""
            **지형 통계:**
            - 최대 고도: `{grid_show.elevation.max():.2f} m`
            - 최소 고도: `{grid_show.elevation.min():.2f} m`
            - 평균 고도: `{grid_show.elevation.mean():.2f} m`
            """)
            
            if st.button("🔄 그리드 초기화 (Reset)"):
                st.session_state['script_grid'] = WorldGrid(100, 100, 10.0)
                st.experimental_rerun()
            else:
                 image_stretch(st, "assets/reference/peneplain_erosion_cycle_1765436750353.png", caption="평야 - 준평원화 과정 (AI 생성)", use_container_width=True)
    
    # ===== Project Genesis (Unified Engine) =====
    with tab_genesis:
        st.header("🌍 Project Genesis: Unified Earth Engine")
        st.info("단일 물리 엔진으로 모든 지형을 생성하는 통합 시뮬레이션입니다.")
        
        c1, c2 = st.columns([1, 2])
        
        with c1:
            st.subheader("⚙️ 시스템 제어")
            
            # 1. 시나리오 선택 (Initial Conditions)
            scenario = st.selectbox("시나리오 초기화", 
                                  ["Flat Plain (평지)", "Sloped Terrain (경사지)", "Mountainous (산지)"])
            
            if st.button("🔄 엔진 초기화 (Reset)"):
                # Initialize Grid
                grid_gen = WorldGrid(width=grid_size, height=grid_size, cell_size=1000.0/grid_size)
                
                # Apply Scenario
                if scenario == "Sloped Terrain (경사지)":
                    rows, cols = grid_size, grid_size
                    for r in range(rows):
                        grid_gen.bedrock[r, :] = 100.0 - (r/rows)*50.0 # N->S Slope
                elif scenario == "Mountainous (산지)":
                    grid_gen.bedrock[:] = np.random.rand(grid_size, grid_size) * 50.0 + 50.0
                else:
                    grid_gen.bedrock[:] = 10.0 # Flat
                
                grid_gen.update_elevation()
                
                # Create Engine
                st.session_state['genesis_engine'] = EarthSystem(grid_gen)
                st.success(f"{scenario} 초기화 완료")
                
            st.markdown("---")
            st.subheader("⛈️ 기후 & 지구조 (Processes)")
            
            gen_precip = st.slider("강수량 (Precipitation)", 0.0, 0.2, 0.05, 0.01)
            gen_uplift = st.slider("융기율 (Uplift Rate)", 0.0, 2.0, 0.1, 0.1)
            gen_diff = st.slider("사면 확산 (Diffusion)", 0.0, 0.1, 0.01, 0.001)
            
            # Kernel Toggles (Phase 2)
            st.markdown("---")
            st.subheader("🧩 커널 제어 (Process Toggles)")
            col_k1, col_k2 = st.columns(2)
            with col_k1:
                k_lateral = st.checkbox("측방 침식 (Lateral)", True, help="곡류 형성")
                k_mass = st.checkbox("매스무브먼트 (Mass)", True, help="산사태")
                k_wave = st.checkbox("파랑 (Wave)", False, help="해안 지형")
            with col_k2:
                k_glacier = st.checkbox("빙하 (Glacier)", False, help="U자곡")
                k_wind = st.checkbox("바람 (Wind)", False, help="사구")
            
            st.markdown("---")
            run_steps = st.slider("실행 스텝 수", 10, 200, 50, 10)
            
            if st.button("▶️ 시뮬레이션 실행 (Run Step)"):
                if 'genesis_engine' not in st.session_state:
                    st.error("엔진을 먼저 초기화해주세요.")
                else:
                    engine = st.session_state['genesis_engine']
                    
                    progress_bar = st.progress(0)
                    for i in range(run_steps):
                        # Construct Settings with kernel toggles
                        settings = {
                            'uplift_rate': gen_uplift * 0.01,
                            'precipitation': gen_precip,
                            'diffusion_rate': gen_diff,
                            'lateral_erosion': k_lateral,
                            'mass_movement': k_mass,
                            # Note: Wave/Glacier/Wind require manual step call
                        }
                        
                        engine.step(dt=1.0, settings=settings)
                        
                        # Optional kernel steps
                        if k_wave:
                            engine.wave.step(dt=1.0)
                        if k_glacier:
                            engine.glacier.step(dt=1.0)
                        if k_wind:
                            engine.wind.step(dt=1.0)
                            
                        progress_bar.progress((i+1)/run_steps)
                    
                    st.success(f"{run_steps} 스텝 실행 완료 (Total Time: {engine.time:.1f})")
                    
        with c2:
            st.subheader("👀 실시간 관측 (Observation)")
            
            if 'genesis_engine' in st.session_state:
                engine = st.session_state['genesis_engine']
                state = engine.get_state()
                
                # 탭으로 뷰 모드 분리
                view_type = st.radio("레이어 선택", ["Composite (지형+물)", "Hydrology (유량)", "Sediment (퇴적층)"], horizontal=True)
                
                if view_type == "Composite (지형+물)":
                    fig = render_terrain_plotly(state['elevation'], 
                                              f"Genesis Engine | T={engine.time:.1f}", 
                                              add_water=True, water_depth_grid=state['water_depth'],
                                              sediment_grid=state['sediment'],
                                              force_camera=True)
                    st.plotly_chart(fig, use_container_width=True)
                    
                elif view_type == "Hydrology (유량)":
                    # Proper colormap for discharge
                    fig_hydro, ax_hydro = plt.subplots(figsize=(8, 6))
                    log_q = np.log1p(state['discharge'])
                    im = ax_hydro.imshow(log_q, cmap='Blues', origin='upper')
                    ax_hydro.set_title(f"유량 분포 (Log Scale) | T={engine.time:.1f}")
                    ax_hydro.set_xlabel("X (셀)")
                    ax_hydro.set_ylabel("Y (셀)")
                    plt.colorbar(im, ax=ax_hydro, label="Log(Q+1)")
                    st.pyplot(fig_hydro)
                    plt.close(fig_hydro)
                    
                    # Stats
                    st.caption(f"최대 유량: {state['discharge'].max():.1f} | 평균: {state['discharge'].mean():.2f}")
                    
                else:
                    # Proper colormap for sediment
                    fig_sed, ax_sed = plt.subplots(figsize=(8, 6))
                    im = ax_sed.imshow(state['sediment'], cmap='YlOrBr', origin='upper')
                    ax_sed.set_title(f"퇴적층 두께 (m) | T={engine.time:.1f}")
                    ax_sed.set_xlabel("X (셀)")
                    ax_sed.set_ylabel("Y (셀)")
                    plt.colorbar(im, ax=ax_sed, label="퇴적층 (m)")
                    st.pyplot(fig_sed)
                    plt.close(fig_sed)
                    
                    # Stats
                    st.caption(f"최대 퇴적: {state['sediment'].max():.2f}m | 총량: {state['sediment'].sum():.0f}m³")
                    
            else:
                st.info("좌측 패널에서 엔진을 초기화하세요.")

    st.markdown("---")
    st.caption("🌍 Geo-Lab AI v6.0 | Unified Earth System Project Genesis")


if __name__ == "__main__":
    main()

@st.cache_data(ttl=3600)
def simulate_v_valley(theory: str, time_years: int, params: dict, grid_size: int = 80):
    """Deterministic V-valley model used by tests and the lab UI."""
    rows, cols = grid_size, grid_size
    center = cols // 2

    y = np.arange(rows, dtype=float)[:, None]
    x = np.arange(cols, dtype=float)
    base = 250.0 - (y / max(rows - 1, 1)) * 60.0

    rock_hardness = float(params.get("rock_hardness", 0.5))
    width_cells = max(6.0, grid_size * (0.18 + (1.0 - rock_hardness) * 0.16))
    depth = 150.0 * (1.0 - np.exp(-time_years / 50000.0))

    dist = np.abs(x - center)
    incision_profile = np.clip(1.0 - dist / width_cells, 0.0, None)
    longitudinal_factor = 0.85 + 0.15 * np.sin(np.linspace(0.0, np.pi, rows, dtype=float))[:, None]
    elevation = base - longitudinal_factor * depth * incision_profile[None, :]

    rng = np.random.default_rng(42)
    elevation += rng.normal(0.0, 0.8, size=(rows, cols))

    water_depth = np.zeros_like(elevation)
    river_half_width = max(1, int(width_cells * 0.12))
    left = max(0, center - river_half_width)
    right = min(cols, center + river_half_width + 1)
    water_depth[:, left:right] = 2.0

    return {
        "elevation": elevation,
        "depth": depth,
        "x": np.linspace(0.0, 1000.0, cols),
        "water_depth": water_depth,
    }


@st.cache_data(ttl=3600)
def simulate_river_terrace(time_years: int, params: dict, grid_size: int = 100):
    """Analytical terrace model with a guaranteed incised channel."""
    rows, cols = grid_size, grid_size
    center = cols // 2

    y = np.arange(rows, dtype=float)[:, None]
    x = np.arange(cols, dtype=float)
    dist = np.abs(x - center)

    elevation = np.repeat(150.0 - (y / max(rows - 1, 1)) * 20.0, cols, axis=1)
    floodplain_limit = max(10.0, grid_size * 0.18)
    elevation[:, dist < floodplain_limit] -= 18.0
    elevation += np.clip(dist - floodplain_limit, 0.0, None)[None, :] * 1.1

    uplift_rate = float(params.get("uplift", 0.5))
    n_terraces = int(params.get("n_terraces", 3))
    years_per_cycle = 20000.0
    progress = min(float(n_terraces), time_years / years_per_cycle)
    completed = int(progress)
    fraction = progress - completed
    terrace_heights = []

    for cycle in range(min(completed, n_terraces)):
        width = max(4.0, grid_size * (0.16 - cycle * 0.025))
        incision = 8.0 + uplift_rate * 4.0
        elevation[:, dist < width] -= incision
        terrace_heights.append(float(elevation[rows // 2, center]))

    if completed < n_terraces and fraction > 0.0:
        width = max(4.0, grid_size * (0.16 - completed * 0.025))
        incision = (8.0 + uplift_rate * 4.0) * fraction
        elevation[:, dist < width] -= incision

    water_depth = np.zeros_like(elevation)
    water_depth[:, max(0, center - 3):min(cols, center + 4)] = 4.0

    return {
        "elevation": elevation,
        "n_terraces": n_terraces,
        "heights": terrace_heights,
        "water_depth": water_depth,
    }


@st.cache_data(ttl=3600)
def simulate_moraine(time_years: int, params: dict, grid_size: int = 100):
    """Analytical moraine model with terminal and lateral ridges."""
    rows, cols = grid_size, grid_size
    center = cols // 2

    yy, xx = np.indices((rows, cols), dtype=float)
    dist = np.abs(xx - center)
    valley_width = max(8.0, grid_size * 0.18)

    base = 210.0 - (yy / max(rows - 1, 1)) * 110.0
    valley = 85.0 * np.clip(1.0 - (dist / valley_width) ** 2, 0.0, None)
    elevation = base - valley

    debris_supply = float(params.get("debris_supply", 0.5))
    retreat_progress = min(1.0, time_years / 20000.0)
    terminus_row = rows * (0.78 - retreat_progress * 0.45)

    arc_row = terminus_row - ((dist / max(valley_width, 1.0)) ** 2) * rows * 0.08
    ridge_sigma = max(1.5, rows * 0.025)
    ridge = np.exp(-((yy - arc_row) ** 2) / (2.0 * ridge_sigma ** 2))
    elevation += ridge * (35.0 + 55.0 * debris_supply)

    lateral_offset = max(3.0, valley_width * 0.85)
    lateral_sigma_x = max(1.5, cols * 0.02)
    lateral_sigma_y = max(3.0, rows * 0.16)
    lateral_center_y = terminus_row + rows * 0.12
    for direction in (-1.0, 1.0):
        ridge_x = center + direction * lateral_offset
        lateral = np.exp(-((xx - ridge_x) ** 2) / (2.0 * lateral_sigma_x ** 2))
        lateral *= np.exp(-((yy - lateral_center_y) ** 2) / (2.0 * lateral_sigma_y ** 2))
        elevation += lateral * (18.0 + 22.0 * debris_supply)

    return {
        "elevation": elevation,
        "type": "모레인 (Moraine)",
    }

