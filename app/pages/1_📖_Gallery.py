"""
📖 이상적 지형 갤러리
31종의 교과서적 지형을 시각화합니다.
"""
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import sys
import os

# 상위 디렉토리를 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from engine.ideal_landforms import IDEAL_LANDFORM_GENERATORS, ANIMATED_LANDFORM_GENERATORS
from app.main import render_terrain_plotly
from app.components.animation_renderer import create_animated_terrain_figure

st.header("📖 이상적 지형 갤러리")
st.markdown("_교과서적인 지형 형태를 기하학적 모델로 시각화합니다._")

# 강조 메시지
st.info("💡 **Tip:** 지형 선택 후 **아래로 스크롤**하면 **🎬 형성 과정 애니메이션**을 확인할 수 있습니다!")

# 카테고리별 지형
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

# 카테고리 → landform_type 매핑
CATEGORY_TO_TYPE = {
    "🌊 하천 지형": "river",
    "🔺 삼각주 유형": "river", 
    "❄️ 빙하 지형": "glacial",
    "🌋 화산 지형": "volcanic",
    "🦇 카르스트 지형": "karst",
    "🏜️ 건조 지형": "arid",
    "🏖️ 해안 지형": "coastal"
}
landform_type = CATEGORY_TO_TYPE.get(category, None)

# 카테고리별 옵션
if category == "🌊 하천 지형":
    landform_options = {
        "📐 선상지 (Alluvial Fan)": "alluvial_fan",
        "🐍 자유곡류 (Free Meander)": "free_meander",
        "⛰️ 감입곡류+하안단구 (Incised Meander)": "incised_meander",
        "🏔️ V자곡 (V-Valley)": "v_valley",
        "🌊 망상하천 (Braided River)": "braided_river",
        "💧 폭포 (Waterfall)": "waterfall",
        "🚧 천정천 (Perched River)": "perched_river",
    }
elif category == "🔺 삼각주 유형":
    landform_options = {
        "🔺 일반 삼각주 (Delta)": "delta",
        "🦶 조족상 삼각주 (Bird-foot)": "bird_foot_delta",
        "🌙 호상 삼각주 (Arcuate)": "arcuate_delta",
        "📍 첨두상 삼각주 (Cuspate)": "cuspate_delta",
        "🌊 에스추어리 (Estuary)": "estuary",
    }
elif category == "❄️ 빙하 지형":
    landform_options = {
        "❄️ U자곡 (U-Valley)": "u_valley",
        "🥣 권곡 (Cirque)": "cirque",
        "🏔️ 호른 (Horn)": "horn",
        "🌊 피오르드 (Fjord)": "fjord",
        "🥚 드럼린 (Drumlin)": "drumlin",
        "🪨 빙퇴석 (Moraine)": "moraine",
        "🗡️ 아레트 (Arête)": "arete",
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
        "🥋 우발라 (Uvala)": "uvala",
        "🗼 탑카르스트 (Tower Karst)": "tower_karst",
        "🪨 카렌 (Karren)": "karren",
    }
elif category == "🏜️ 건조 지형":
    landform_options = {
        "🌙 바르한 사구 (Barchan)": "barchan",
        "🟰 횡사구 (Transverse Dune)": "transverse_dune",
        "⭐ 성사구 (Star Dune)": "star_dune",
        "🗿 메사/뷰트 (Mesa/Butte)": "mesa_butte",
        "🏜️ 와디 (Wadi)": "wadi",
        "🪶 플라야 (Playa)": "playa",
        "🍄 버섯바위 (Pedestal Rock)": "pedestal_rock",
        "⛰️ 페디먼트 (Pediment)": "pediment",
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
    
    st.markdown("---")
    st.subheader("⚙️ 파라미터")
    
    gallery_grid_size = st.slider("해상도", 50, 150, 80, 10, key="gallery_res")
    
    # ======== 애니메이션 설정 ========
    st.markdown("---")
    st.markdown("### 🎬 애니메이션")
    
    num_frames = st.slider("프레임 수", 10, 100, 40, 5, key="anim_frames", 
                           help="높을수록 애니메이션이 부드러워집니다")
    
    # 동적 지형 생성
    if landform_key in IDEAL_LANDFORM_GENERATORS:
        generator = IDEAL_LANDFORM_GENERATORS[landform_key]
        try:
            elevation = generator(gallery_grid_size)
        except TypeError:
            elevation = generator(gallery_grid_size, 1.0)
    else:
        st.error(f"지형 '{landform_key}' 생성기를 찾을 수 없습니다.")
        elevation = np.zeros((gallery_grid_size, gallery_grid_size))

with col_view:
    # 2D 평면도
    fig_2d, ax = plt.subplots(figsize=(8, 8))
    cmap = plt.cm.terrain
    water_mask = elevation < 0
    
    im = ax.imshow(elevation, cmap=cmap, origin='upper')
    
    if water_mask.any():
        water_overlay = np.ma.masked_where(~water_mask, np.ones_like(elevation))
        ax.imshow(water_overlay, cmap='Blues', alpha=0.6, origin='upper')
    
    ax.set_title(f"{selected_landform}", fontsize=14)
    ax.axis('off')
    plt.colorbar(im, ax=ax, shrink=0.6, label='고도 (m)')
    
    st.pyplot(fig_2d)
    plt.close(fig_2d)
    
    # 3D 보기 버튼
    if st.button("🔲 3D 뷰 보기", key="show_3d_view"):
        fig_3d = render_terrain_plotly(
            elevation, 
            f"{selected_landform} - 3D",
            add_water=(landform_key in ["delta", "meander", "coastal_cliff", "fjord", "ria_coast", "spit_lagoon"]),
            water_level=0 if landform_key in ["delta", "coastal_cliff"] else -999,
            force_camera=True,
            landform_type=landform_type,  # 카테고리에 맞는 색상 적용
            detailed_type=landform_key    # 상세 지형별 Z-scale 적용
        )
        st.plotly_chart(fig_3d, use_container_width=True, key="gallery_3d")
    
    # 설명
    descriptions = {
        "delta": "**삼각주**: 하천이 바다나 호수에 유입될 때 유속이 감소하여 운반 중이던 퇴적물이 쌓여 형성됩니다.",
        "alluvial_fan": "**선상지**: 산지에서 평지로 나오는 곳에서 경사가 급감하여 운반력이 줄어들면서 퇴적물이 부채꼴로 쌓입니다.",
        "free_meander": "**자유곡류**: 범람원 위를 자유롭게 사행하는 곡류. 자연제방(Levee)과 배후습지가 특징입니다.",
        "incised_meander": "**감입곡류**: 융기로 인해 곡류가 기반암을 파고들면서 형성. 하안단구(River Terrace)가 함께 나타납니다.",
        "v_valley": "**V자곡**: 하천의 하방 침식이 우세하게 작용하여 형성된 V자 단면의 골짜기.",
        "braided_river": "**망상하천**: 퇴적물이 많고 경사가 급할 때 여러 수로가 갈라졌다 합쳐지는 하천.",
        "waterfall": "**폭포**: 경암과 연암의 차별침식으로 형성된 급경사 낙차. 후퇴하며 협곡 형성.",
        "bird_foot_delta": "**조족상 삼각주**: 미시시피강형. 파랑 약하고 퇴적물 공급 많을 때 새발 모양으로 길게 뻗습니다.",
        "arcuate_delta": "**호상 삼각주**: 나일강형. 파랑과 퇴적물 공급이 균형을 이루어 부드러운 호(Arc) 형태.",
        "cuspate_delta": "**첨두상 삼각주**: 티베르강형. 파랑이 강해 삼각주가 뾰족한 화살촉 모양으로 형성.",
        "u_valley": "**U자곡**: 빙하의 침식으로 형성된 U자 단면의 골짜기. 측벽이 급하고 바닥이 평탄합니다.",
        "cirque": "**권곡**: 빙하의 시작점. 반원형 움푹 파인 지형으로, 빙하 융해 후 호수(Tarn)가 형성됩니다.",
        "horn": "**호른**: 여러 권곡이 만나는 곳에서 침식되지 않고 남은 뾰족한 피라미드형 봉우리.",
        "fjord": "**피오르드**: 빙하가 파낸 U자곡에 바다가 유입된 좁고 깊은 만.",
        "drumlin": "**드럼린**: 빙하 퇴적물이 빙하 흐름 방향으로 길쭉하게 쌓인 타원형 언덕.",
        "moraine": "**빙퇴석**: 빙하가 운반한 암설이 퇴적된 지형. 측퇴석, 종퇴석 등이 있습니다.",
        "shield_volcano": "**순상화산**: 유동성 높은 현무암질 용암이 완만하게 쌓여 방패 형태.",
        "stratovolcano": "**성층화산**: 용암과 화산쇄설물이 교대로 쌓여 급한 원뿔형.",
        "caldera": "**칼데라**: 대규모 분화 후 마그마방 함몰로 형성된 거대한 분지.",
        "crater_lake": "**화구호**: 화구나 칼데라에 물이 고여 형성된 호수.",
        "lava_plateau": "**용암대지**: 열극 분출로 현무암질 용암이 넓게 펼쳐져 평탄한 대지 형성.",
        "barchan": "**바르한 사구**: 바람이 한 방향에서 불 때 형성되는 초승달 모양의 사구.",
        "mesa_butte": "**메사/뷰트**: 차별침식으로 남은 탁상지. 메사는 크고 평탄, 뷰트는 작고 높습니다.",
        "pediment": "**페디먼트**: 건조 지역 산지 전면에 발달하는 완만한 경사의 침식 암석면(산록 완사촌).",
        "karst_doline": "**돌리네**: 석회암 용식으로 형성된 움푹 파인 와지.",
        "coastal_cliff": "**해안 절벽**: 파랑의 침식으로 형성된 절벽.",
        "spit_lagoon": "**사취+석호**: 연안류에 의해 퇴적물이 길게 쌓인 사취가 만을 막아 석호를 형성합니다.",
        "tombolo": "**육계사주**: 연안류에 의한 퇴적으로 육지와 섬이 모래톱으로 연결된 지형.",
        "ria_coast": "**리아스식 해안**: 과거 하곡이 해수면 상승으로 침수되어 형성된 톱니 모양 해안선.",
        "sea_arch": "**해식아치**: 곶에서 파랑 침식으로 형성된 아치형 지형.",
        "coastal_dune": "**해안사구**: 해빈의 모래가 바람에 의해 육지 쪽으로 운반되어 형성된 모래 언덕.",
        # 새로 추가된 지형
        "uvala": "**우발라**: 여러 돌리네가 합쳐져 형성된 복합 와지. 돌리네보다 크고 불규칙한 형태.",
        "tower_karst": "**탑카르스트**: 수직 절벽을 가진 탑 모양 석회암 봉우리. 중국 구이린이 대표적.",
        "karren": "**카렌**: 빗물에 의한 용식으로 석회암 표면에 형성된 홈과 릿지. 클린트/그라이크 포함.",
        "transverse_dune": "**횡사구**: 바람 방향에 수직으로 길게 형성된 사구열. 모래 공급이 풍부할 때 발달.",
        "star_dune": "**성사구**: 다방향 바람에 의해 별 모양으로 형성된 사구. 높이가 높고 이동이 적음.",
    }
    st.info(descriptions.get(landform_key, "설명 준비 중입니다."))

# ========== 형성 과정 애니메이션 ==========
if landform_key in ANIMATED_LANDFORM_GENERATORS:
    st.markdown("---")
    st.subheader("🎬 형성 과정")
    
    st.markdown(f"""
    <div style='background-color: #2b303b; padding: 15px; border-radius: 10px; border-left: 5px solid #4CAF50;'>
        <p>왼쪽 패널에서 설정한 <b>{num_frames} 프레임</b>으로 부드러운 애니메이션을 생성합니다.</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🚀 애니메이션 생성", use_container_width=True):
        with st.spinner(f"{selected_landform} 형성 과정 시뮬레이션 중... ({num_frames} 프레임)"):
            anim_func = ANIMATED_LANDFORM_GENERATORS[landform_key]
            
            fig_anim = create_animated_terrain_figure(
                landform_func=anim_func,
                grid_size=gallery_grid_size,
                num_frames=num_frames,
                title=f"{selected_landform} 형성과정",
                landform_type=landform_type,
                detailed_type=landform_key
            )
            
            st.plotly_chart(fig_anim, use_container_width=True)
            st.success("✅ 생성 완료! 하단 플레이어 컨트롤러를 사용하여 재생하세요.")
    
    st.caption("💡 **Tip:** 프레임 수가 높을수록 부드럽지만 생성 시간이 길어집니다.")

