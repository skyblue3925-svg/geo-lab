"""
📖 이상적 지형 갤러리
31종의 교과서적 지형을 시각화합니다.
"""
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import sys
import os
import json

# 상위 디렉토리를 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from engine.ideal_landforms import IDEAL_LANDFORM_GENERATORS, ANIMATED_LANDFORM_GENERATORS
from app.components.renderer import render_terrain_plotly
from app.components.animation_renderer import create_animated_terrain_figure

# ========== CSS 로드 ==========
def load_css():
    css_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "style.css")
    if os.path.exists(css_path):
        with open(css_path, 'r', encoding='utf-8') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

load_css()

# ========== 시네마틱 영상 메타데이터 로드 ==========
def load_cinematic_metadata():
    """시네마틱 영상 메타데이터를 로드합니다."""
    metadata_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                  "assets", "cinematic", "metadata.json")
    try:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"videos": []}

# ========== 헤더 ==========
st.markdown("""
<div style='margin-bottom: 1.5rem;'>
    <h1 style='font-size: 2.2rem; font-weight: 700; margin-bottom: 0.25rem;'>📖 이상적 지형 갤러리</h1>
    <p style='color: #86868b; font-size: 1rem;'>교과서적인 지형 형태를 기하학적 모델로 시각화합니다.</p>
</div>
""", unsafe_allow_html=True)

# ========== 메인 탭 구조 ==========
main_tab1, main_tab2 = st.tabs(["🎮 3D 시뮬레이션", "🎬 시네마틱 영상"])

# ========== 시네마틱 영상 탭 ==========
with main_tab2:
    st.subheader("🎬 나노 바나나 프로 시네마틱 영상")
    st.markdown("_AI로 생성한 고품질 지형 형성 영상을 감상하세요._")
    
    metadata = load_cinematic_metadata()
    videos = metadata.get("videos", [])
    
    if not videos:
        st.warning("아직 등록된 시네마틱 영상이 없습니다.")
    else:
        # 카테고리 필터
        categories = list(set(v.get("category", "other") for v in videos))
        category_names = {
            "glacial": "❄️ 빙하", "river": "🌊 하천", "volcanic": "🌋 화산",
            "arid": "🏜️ 건조", "coastal": "🏖️ 해안", "karst": "🦇 카르스트"
        }
        
        col_filter, col_info = st.columns([2, 1])
        with col_filter:
            selected_cat = st.selectbox(
                "카테고리 필터",
                ["전체"] + [category_names.get(c, c) for c in categories],
                key="cinematic_cat"
            )
        
        # 필터링
        if selected_cat == "전체":
            filtered_videos = videos
        else:
            cat_key = [k for k, v in category_names.items() if v == selected_cat]
            cat_key = cat_key[0] if cat_key else selected_cat
            filtered_videos = [v for v in videos if v.get("category") == cat_key]
        
        # 영상 목록
        for video in filtered_videos:
            with st.expander(f"{video['title']} ({video.get('duration', '?')})", expanded=False):
                st.markdown(f"**설명:** {video.get('description', '')}")
                st.markdown(f"**소스 이미지:** {', '.join(video.get('sources', []))}")
                
                status = video.get("status", "pending")
                if status == "ready":
                    video_path = os.path.join(
                        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "assets", "cinematic", video.get("file", "")
                    )
                    if os.path.exists(video_path):
                        # GIF는 바이너리로 읽어서 표시, MP4는 st.video()
                        if video_path.endswith('.gif'):
                            with open(video_path, 'rb') as f:
                                gif_data = f.read()
                            st.image(gif_data, use_column_width=True)
                        else:
                            st.video(video_path)
                    else:
                        st.error(f"영상 파일을 찾을 수 없습니다: {video.get('file')}")
                elif status == "in_progress":
                    st.info("🔄 제작 중입니다...")
                else:
                    st.warning("⏳ 제작 예정 - 나노 바나나 프로에서 영상을 생성해주세요.")
                    
                    # 프롬프트 템플릿 제안
                    with st.expander("💡 제작 프롬프트 예시"):
                        prompt_templates = {
                            "fjord_formation": "Create a 30-second educational animation showing fjord formation: 1) V-shaped valley carved by river, 2) Glacier advancing and eroding into U-shape, 3) Glacier retreating, 4) Sea flooding the valley. Photorealistic, aerial view.",
                            "delta_development": "Create a 25-second animation of river delta formation: sediment-laden river meeting calm sea, gradual buildup of distributary channels, bird's eye view showing arcuate shape developing.",
                            "barchan_migration": "Create a 20-second animation of barchan dune migration: wind from one direction, sand moving up windward slope, sliding down slip face, crescent shape moving across desert.",
                            "caldera_formation": "Create a 35-second animation of caldera formation: magma chamber filling, massive eruption, collapse of summit, lake filling the depression. Cross-section view.",
                            "sea_stack_evolution": "Create a 30-second coastal erosion animation: waves attacking headland, sea cave forming, arch developing, collapse into sea stack. Side view perspective."
                        }
                        st.code(prompt_templates.get(video['id'], "프롬프트를 작성해주세요."))
        
        st.markdown("---")
        st.caption("💡 **제작 방법:** [nanobanana.pro](https://nanobanana.pro) 에서 영상 생성 → `assets/cinematic/` 폴더에 저장 → `metadata.json`의 status를 'ready'로 변경")

# ========== 3D 시뮬레이션 탭 ==========
with main_tab1:
    # 모드 선택 (교사용/전문가)
    mode_col1, mode_col2 = st.columns([3, 1])
    with mode_col2:
        view_mode = st.radio(
            "모드", 
            ["🎓 교사용", "⚙️ 전문가"],
            horizontal=True,
            key="gallery_mode",
            label_visibility="collapsed"
        )
    is_teacher_mode = (view_mode == "🎓 교사용")
    
    # 모드별 안내 메시지
    if is_teacher_mode:
        st.success("🎓 **교사 모드** — 3D 애니메이션이 바로 표시됩니다!")
    else:
        st.info("⚙️ **전문가 모드** — 모든 파라미터를 조정할 수 있습니다.")

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
            "💧 칼데라호 (Caldera Lake)": "crater_lake",
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

    # 지형 선택 (상단에 배치)
    selected_landform = st.selectbox("🏔️ 지형 선택", list(landform_options.keys()), key="landform_select")
    landform_key = landform_options[selected_landform]
    
    # 모드에 따른 파라미터 설정
    if is_teacher_mode:
        # 교사 모드: 기본값 사용
        gallery_grid_size = 60
        num_frames = 30
    else:
        # 전문가 모드: 슬라이더 표시
        col_params1, col_params2 = st.columns(2)
        with col_params1:
            gallery_grid_size = st.slider("해상도", 30, 200, 60, 10, key="gallery_res")
        with col_params2:
            num_frames = st.slider("프레임 수", 10, 100, 30, 5, key="anim_frames")
    
    # 지형 생성
    if landform_key in IDEAL_LANDFORM_GENERATORS:
        generator = IDEAL_LANDFORM_GENERATORS[landform_key]
        try:
            elevation = generator(gallery_grid_size)
        except TypeError:
            elevation = generator(gallery_grid_size, 1.0)
    else:
        st.error(f"지형 '{landform_key}' 생성기를 찾을 수 없습니다.")
        elevation = np.zeros((gallery_grid_size, gallery_grid_size))

    # 지형 설명 (간결하게)
    descriptions = {
        "delta": "하천이 바다/호수에 유입될 때 퇴적물이 쌓여 형성",
        "alluvial_fan": "산지에서 평지로 나오는 경사 급변점에서 퇴적물이 부채꼴로 쌓임",
        "free_meander": "범람원을 사행하는 곡류. 자연제방과 배후습지 형성",
        "incised_meander": "융기로 곡류가 기반암을 파며 형성. 하안단구 발달",
        "v_valley": "하천의 하방 침식이 우세하여 형성된 V자 단면 골짜기",
        "braided_river": "퇴적물이 많고 경사가 급할 때 수로가 분화/합류",
        "waterfall": "경암과 연암의 차별침식으로 형성. 점차 후퇴함",
        "bird_foot_delta": "미시시피강형. 파랑 약하고 퇴적물 많을 때 새발 모양",
        "arcuate_delta": "나일강형. 파랑과 퇴적물 균형으로 호(Arc) 형태",
        "cuspate_delta": "티베르강형. 파랑이 강해 뾰족한 화살촉 모양",
        "u_valley": "빙하 침식으로 형성된 U자 단면의 골짜기",
        "cirque": "빙하 시작점. 반원형 와지, 융해 후 호수(Tarn) 형성",
        "horn": "여러 권곡이 만나 침식되지 않고 남은 피라미드형 봉우리",
        "fjord": "빙하가 파낸 U자곡에 바다가 유입된 좁고 깊은 만",
        "drumlin": "빙하 퇴적물이 흐름 방향으로 타원형으로 쌓인 언덕",
        "moraine": "빙하가 운반한 암설이 퇴적된 지형 (측퇴석/종퇴석)",
        "shield_volcano": "유동성 높은 현무암질 용암이 완만하게 쌓인 방패형",
        "stratovolcano": "용암과 화산쇄설물이 교대로 쌓인 급경사 원뿔형",
        "caldera": "대규모 분화 후 마그마방 함몰로 형성된 거대 분지",
        "crater_lake": "칼데라/화구에 물이 채워진 호수",
        "lava_plateau": "열극 분출로 현무암 용암이 넓게 펼쳐진 평탄 대지",
        "barchan": "바람이 한 방향에서 불 때 형성되는 초승달 사구",
        "mesa_butte": "차별침식으로 남은 탁상지. 메사>뷰트 순으로 작아짐",
        "karst_doline": "석회암 용식으로 형성된 움푹 파인 와지",
        "coastal_cliff": "파랑 침식으로 형성된 해안 절벽",
        "spit_lagoon": "연안류로 퇴적물이 길게 쌓인 사취가 석호를 형성",
        "tombolo": "연안류 퇴적으로 육지와 섬이 모래톱으로 연결",
        "ria_coast": "하곡이 해수면 상승으로 침수된 톱니 해안선",
        "sea_arch": "곶에서 파랑 침식으로 형성된 아치형 지형",
    }
    
    desc = descriptions.get(landform_key, "")
    if desc:
        st.caption(f"📖 {desc}")
    
    st.markdown("---")
    
    # 교사 모드: 3D 애니메이션 먼저 표시
    if is_teacher_mode:
        # 3D 애니메이션 바로 표시
        if landform_key in ANIMATED_LANDFORM_GENERATORS:
            anim_func = ANIMATED_LANDFORM_GENERATORS[landform_key]
            with st.spinner("🎬 애니메이션 생성 중..."):
                try:
                    fig_animated = create_animated_terrain_figure(
                        landform_func=anim_func,
                        grid_size=gallery_grid_size,
                        num_frames=num_frames,
                        title=f"{selected_landform} 형성 과정",
                        landform_type=landform_type,
                        detailed_type=landform_key
                    )
                    st.plotly_chart(fig_animated, use_container_width=True, key="teacher_anim", 
                                   config={'scrollZoom': True, 'displayModeBar': True})
                    st.caption("▶️ **재생** 버튼으로 지형 형성 과정을 확인하세요!")
                except Exception as e:
                    st.error(f"애니메이션 오류: {e}")
        else:
            # 애니메이션 없는 지형: 정적 3D
            fig_3d = render_terrain_plotly(
                elevation,
                f"{selected_landform}",
                add_water=True,
                water_level=-999,
                force_camera=True,
                landform_type=landform_type
            )
            st.plotly_chart(fig_3d, use_container_width=True, key="teacher_3d",
                           config={'scrollZoom': True, 'displayModeBar': True})
        
        # 2D 보기 옵션 (접혀있음)
        with st.expander("🗺️ 2D 평면도 보기"):
            fig_2d, ax = plt.subplots(figsize=(8, 6))
            im = ax.imshow(elevation, cmap='terrain', origin='upper')
            ax.set_title(f"{selected_landform}", fontsize=14)
            ax.axis('off')
            plt.colorbar(im, ax=ax, shrink=0.6, label='고도 (m)')
            st.pyplot(fig_2d)
            plt.close(fig_2d)
    
    else:
        # 전문가 모드: 기존 레이아웃 (2D + 3D 버튼)
        col_sel, col_view = st.columns([1, 3])
        
        with col_sel:
            st.caption("📊 통계")
            st.metric("최고 고도", f"{elevation.max():.1f}m")
            st.metric("최저 고도", f"{elevation.min():.1f}m")
            st.metric("고도차", f"{elevation.max() - elevation.min():.1f}m")
        
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
            
            # 3D 보기 버튼 (두 가지 옵션)
            col_3d_1, col_3d_2 = st.columns(2)
            
            with col_3d_1:
                if st.button("🔲 3D 뷰 (Plotly)", key="show_3d_view"):
                    fig_3d = render_terrain_plotly(
                        elevation, 
                        f"{selected_landform} - 3D",
                        add_water=(landform_key in ["delta", "meander", "coastal_cliff", "fjord", "ria_coast", "spit_lagoon"]),
                        water_level=0 if landform_key in ["delta", "coastal_cliff"] else -999,
                        force_camera=True,
                        landform_type=landform_type
                    )
                    st.plotly_chart(fig_3d, use_container_width=True, key="gallery_3d", config={'scrollZoom': True, 'displayModeBar': True})
            
            with col_3d_2:
                if st.button("🖼️ 3D 뷰 (이미지)", key="show_3d_mpl", help="WebGL이 안 되는 환경용"):
                    from mpl_toolkits.mplot3d import Axes3D
                    
                    fig_mpl = plt.figure(figsize=(10, 8))
                    ax_3d = fig_mpl.add_subplot(111, projection='3d')
                    
                    # 다운샘플링 (성능)
                    step = max(1, gallery_grid_size // 50)
                    h, w = elevation.shape
                    x_mpl = np.arange(0, w, step)
                    y_mpl = np.arange(0, h, step)
                    X, Y = np.meshgrid(x_mpl, y_mpl)
                    Z = elevation[::step, ::step]
                    
                    # 색상 매핑
                    ax_3d.plot_surface(X, Y, Z, cmap='terrain', linewidth=0, antialiased=True, alpha=0.9)
                    ax_3d.set_xlabel('X (m)')
                    ax_3d.set_ylabel('Y (m)')
                    ax_3d.set_zlabel('Elevation (m)')
                    ax_3d.set_title(f"{selected_landform} - 3D")
                    ax_3d.view_init(elev=30, azim=-60)
                    
                    st.pyplot(fig_mpl)
                    plt.close(fig_mpl)
                    st.caption("💡 Matplotlib 3D 이미지 (WebGL 없이 작동)")
        
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
            "crater_lake": "**칼데라호**: 대규모 화산 폭발 후 정상부 함몰로 형성된 호수. 지름 1km 이상.",
            "lava_plateau": "**용암대지**: 열극 분출로 현무암질 용암이 넓게 펼쳐져 평탄한 대지 형성.",
            "barchan": "**바르한 사구**: 바람이 한 방향에서 불 때 형성되는 초승달 모양의 사구.",
            "mesa_butte": "**메사/뷰트**: 차별침식으로 남은 탁상지. 메사는 크고 평탄, 뷰트는 작고 높습니다.",
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
        
        # 자동 재생 중이면 session_state의 stage 사용
        if st.session_state.get('auto_playing', False):
            stage_value = st.session_state.get('auto_stage', 0.0)
            st.slider(
                "형성 단계 (자동 재생 중...)", 
                0.0, 1.0, stage_value, 0.02, 
                key="gallery_stage_slider",
                disabled=True
            )
        else:
            stage_value = st.slider(
                "형성 단계 (0% = 시작, 100% = 완성)", 
                0.0, 1.0, 1.0, 0.02, 
                key="gallery_stage_slider"
            )
        
        anim_func = ANIMATED_LANDFORM_GENERATORS[landform_key]
        
        # 메타데이터 지원 지형 확인
        supported_metadata = [
            'incised_meander', 'alluvial_fan', 'fjord',  # 기존
            'free_meander', 'waterfall', 'cirque', 'horn', 'coastal_cliff',  # 신규
            'bird_foot_delta',  # 추가
            'v_valley',  # V자곡 추가
            'delta',  # 일반 삼각주 추가
            'barchan',  # 바르한 사구 추가
            'mesa_butte',  # 메사/뷰트 추가
            'spit_lagoon',  # 사취+석호 추가
            'stratovolcano',  # 성층화산 추가
            'karst_doline',  # 돌리네 추가
            'u_valley',  # U자곡
            # Phase 2
            'braided_river',  # 망상하천
            'arcuate_delta',  # 호상삼각주
            'cuspate_delta',  # 첨두삼각주
            'drumlin',  # 드럼린
            'moraine',  # 빙퇴석
            'tombolo',  # 육계사주
            'sea_arch',  # 해식아치
            'crater_lake',  # 칼데라호
            'transverse_dune',  # 횡사구
            'star_dune',  # 성사구
            'perched_river',  # 천정천
        ]
        
        if landform_key in supported_metadata:
            try:
                stage_elev, metadata = anim_func(gallery_grid_size, stage_value, return_metadata=True)
                # 단계별 설명 표시
                st.success(metadata.get('stage_description', ''))
                
                # 선상지 존 정보 + 색상 하이라이트
                if landform_key == 'alluvial_fan' and 'zone_info' in metadata:
                    with st.expander("📊 세부 구조 보기", expanded=True):
                        col_z1, col_z2, col_z3 = st.columns(3)
                        col_z1.markdown("🔴 **선정(Apex)**<br>경사 5-15°, 역력", unsafe_allow_html=True)
                        col_z2.markdown("🟡 **선앙(Mid)**<br>경사 2-5°, 사질", unsafe_allow_html=True)
                        col_z3.markdown("🔵 **선단(Toe)**<br>경사 <2°, 니질", unsafe_allow_html=True)
                        
                        show_zones = st.checkbox("🎨 존 색상 오버레이 표시", value=False, key="show_zone_colors")
                        
                        if show_zones and 'zone_mask' in metadata:
                            # 존 마스크를 색상으로 표시
                            st.info("🔴 선정 | 🟡 선앙 | 🔵 선단")
                            
                            import matplotlib.pyplot as plt
                            from matplotlib.colors import ListedColormap
                            
                            zone_mask = metadata['zone_mask']
                            cmap = ListedColormap(['#4682B4', '#FFD700', '#FF6347', '#228B22'])  # 배경, 선단, 선앙, 선정
                            
                            fig_zone, ax = plt.subplots(figsize=(8, 6))
                            im = ax.imshow(zone_mask, cmap=cmap, origin='lower', alpha=0.8)
                            ax.contour(stage_elev, levels=10, colors='white', linewidths=0.5, alpha=0.5)
                            ax.set_title("선상지 존 구분")
                            ax.set_xlabel("X")
                            ax.set_ylabel("Y")
                            
                            # 범례
                            from matplotlib.patches import Patch
                            legend_elements = [
                                Patch(facecolor='#FF6347', label='선정(Apex)'),
                                Patch(facecolor='#FFD700', label='선앙(Mid)'),
                                Patch(facecolor='#4682B4', label='선단(Toe)')
                            ]
                            ax.legend(handles=legend_elements, loc='upper right')
                            
                            st.pyplot(fig_zone)
                            plt.close(fig_zone)
                
                # 피오르드 프로세스 정보
                if landform_key == 'fjord' and 'process_info' in metadata:
                    with st.expander("🧊 빙하 작용 보기"):
                        for process, desc in metadata['process_info'].items():
                            st.markdown(f"- **{process}**: {desc}")
                
                # 자유곡류 정보
                if landform_key == 'free_meander':
                    with st.expander("🌀 곡류 정보 보기"):
                        st.markdown(f"**사행도**: {metadata.get('sinuosity', 1):.2f}")
                        st.markdown(f"**우각호 형성**: {'✅ 예' if metadata.get('oxbow_formed', False) else '❌ 아니오'}")
                
                # 폭포 정보
                if landform_key == 'waterfall' and 'layer_info' in metadata:
                    with st.expander("⛰️ 차별침식 보기"):
                        for layer, info in metadata['layer_info'].items():
                            st.markdown(f"- **{layer}**: {info['description']}")
                        st.markdown(f"**후퇴 거리**: {metadata.get('retreat_distance', 0):.0f}m")
                
                # 권곡 정보
                if landform_key == 'cirque':
                    with st.expander("❄️ 빙하 침식 보기"):
                        st.markdown(f"**권곡 반경**: {metadata.get('cirque_radius', 0)}m")
                        st.markdown(f"**턴(호수) 형성**: {'✅ 예' if metadata.get('tarn_present', False) else '❌ 아니오'}")
                
                # 호른 정보
                if landform_key == 'horn':
                    with st.expander("🗻 다중 권곡 보기"):
                        st.markdown(f"**권곡 개수**: {metadata.get('num_cirques', 0)}개")
                        st.markdown(f"**정상 높이**: {metadata.get('peak_height', 0):.0f}m")
                
                # 해안절벽 정보
                if landform_key == 'coastal_cliff' and 'erosion_processes' in metadata:
                    with st.expander("🌊 파랑 침식 보기"):
                        for process, desc in metadata['erosion_processes'].items():
                            st.markdown(f"- **{process}**: {desc}")
                        st.markdown(f"**후퇴량**: {metadata.get('retreat_amount', 0)}m")
                
                # 조족상 삼각주 정보
                if landform_key == 'bird_foot_delta':
                    with st.expander("🦶 분배수로 보기"):
                        st.markdown(f"**분배수로 개수**: {metadata.get('num_distributaries', 0)}개")
                        st.markdown(f"**최대 길이**: {metadata.get('max_length', 0)}m")
                
                # 빙퇴석 빙하 표시
                if landform_key == 'moraine' and 'glacier_mask' in metadata:
                    with st.expander("❄️ 빙하 시각화", expanded=True):
                        st.markdown(f"**단계**: {metadata.get('phase', '')}")
                        st.markdown(f"**빙하 표시**: {'✅ 있음' if metadata.get('glacier_visible', False) else '❌ 소멸'}")
                        
                        show_glacier = st.checkbox("🧊 빙하 하얀색으로 표시", value=True, key="show_glacier_white")
                        
                        if show_glacier and metadata.get('glacier_visible', False):
                            import matplotlib.pyplot as plt
                            
                            glacier_mask = metadata['glacier_mask']
                            
                            fig_glacier, ax = plt.subplots(figsize=(8, 6))
                            # 기본 지형 표시
                            im = ax.imshow(stage_elev, cmap='terrain', origin='upper')
                            
                            # 빙하 영역 하얀색 오버레이
                            glacier_overlay = np.ma.masked_where(~glacier_mask, np.ones_like(stage_elev))
                            ax.imshow(glacier_overlay, cmap='Blues_r', alpha=0.8, origin='upper', vmin=0, vmax=2)
                            
                            ax.set_title(f"빙퇴석 - {metadata.get('phase', '')}")
                            ax.axis('off')
                            plt.colorbar(im, ax=ax, shrink=0.6, label='고도 (m)')
                            
                            st.pyplot(fig_glacier)
                            plt.close(fig_glacier)
                            st.caption("🧊 하얀색/청백색 영역 = 빙하")
                        
            except TypeError:
                # return_metadata 지원 안 하는 경우
                stage_elev = anim_func(gallery_grid_size, stage_value)
        else:
            stage_elev = anim_func(gallery_grid_size, stage_value)
        
        # 물 생성
        stage_water = np.maximum(0, -stage_elev + 1.0)
        stage_water[stage_elev > 2] = 0
        
        # 선상지 물 처리
        if landform_key == "alluvial_fan":
            apex_y = int(gallery_grid_size * 0.15)
            center = gallery_grid_size // 2
            for r in range(apex_y + 5):
                for dc in range(-2, 3):
                    c = center + dc
                    if 0 <= c < gallery_grid_size:
                        stage_water[r, c] = 3.0
        
        # 애니메이션 모드 선택
        st.markdown("---")
        animation_mode = st.radio(
            "애니메이션 모드",
            ["🎬 부드러운 애니메이션 (추천)", "📊 슬라이더 수동 조작"],
            horizontal=True,
            key="anim_mode"
        )
        
        # 📐 다중 시점 선택
        from app.components.animation_renderer import get_multi_angle_cameras
        camera_presets = get_multi_angle_cameras()
        
        selected_view = st.selectbox(
            "📐 시점 선택",
            list(camera_presets.keys()),
            key="camera_view"
        )
        selected_camera = camera_presets[selected_view]
        
        if animation_mode == "🎬 부드러운 애니메이션 (추천)":
            # Plotly 네이티브 애니메이션 (카메라 유지!)
            st.info("▶️ **재생** 버튼을 누르면 애니메이션이 시작됩니다. **카메라를 자유롭게 조작**할 수 있습니다!")
            
            try:
                fig_animated = create_animated_terrain_figure(
                    landform_func=anim_func,
                    grid_size=gallery_grid_size,
                    num_frames=num_frames,  # 사용자 설정 사용
                    title=f"{selected_landform} 형성 과정",
                    landform_type=landform_type,
                    detailed_type=landform_key  # 세부 지형 타입 전달
                )
                # 선택된 카메라 각도 적용
                fig_animated.update_layout(
                    scene=dict(camera=selected_camera)
                )
                st.plotly_chart(fig_animated, use_container_width=True, key="animated_view", config={'scrollZoom': True, 'displayModeBar': True})
            except Exception as e:
                st.error(f"애니메이션 생성 오류: {e}")
                # 폴백: 정적 렌더링
                fig_stage = render_terrain_plotly(
                    stage_elev,
                    f"{selected_landform} - {int(stage_value*100)}%",
                    add_water=True,
                    water_depth_grid=stage_water,
                    water_level=-999,
                    force_camera=False,
                    landform_type=landform_type
                )
                fig_stage.update_layout(scene=dict(camera=selected_camera))
                st.plotly_chart(fig_stage, use_container_width=True, key="stage_view_fallback", config={'scrollZoom': True, 'displayModeBar': True})
        else:
            # 기존 슬라이더 방식
            fig_stage = render_terrain_plotly(
                stage_elev,
                f"{selected_landform} - {int(stage_value*100)}%",
                add_water=True,
                water_depth_grid=stage_water,
                water_level=-999,
                force_camera=False,
                landform_type=landform_type
            )
            fig_stage.update_layout(scene=dict(camera=selected_camera))
            st.plotly_chart(fig_stage, use_container_width=True, key="stage_view", config={'scrollZoom': True, 'displayModeBar': True})
        
        st.caption("💡 **Tip:** '시점 선택'에서 X축(측면), Y축(정면), Z축(평면도) 등 다양한 각도로 감상할 수 있습니다!")
