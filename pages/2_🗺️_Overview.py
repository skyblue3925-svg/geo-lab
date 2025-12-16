"""
🗺️ 카테고리 전체 뷰
각 카테고리의 모든 지형을 한눈에 비교합니다.
"""
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import sys
import os

# 상위 디렉토리를 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.ideal_landforms import IDEAL_LANDFORM_GENERATORS

st.set_page_config(layout="wide")
st.header("🗺️ 카테고리 전체 뷰")
st.markdown("_각 카테고리의 모든 지형을 한눈에 비교합니다._")

# 카테고리 정의
CATEGORIES = {
    "🌊 하천 지형": {
        "alluvial_fan": "선상지",
        "free_meander": "자유곡류", 
        "incised_meander": "감입곡류",
        "v_valley": "V자곡",
        "braided_river": "망상하천",
        "waterfall": "폭포",
        "perched_river": "천정천",
    },
    "🔺 삼각주 유형": {
        "delta": "일반 삼각주",
        "bird_foot_delta": "조족상",
        "arcuate_delta": "호상",
        "cuspate_delta": "첨두상",
        "estuary": "에스추어리",
    },
    "❄️ 빙하 지형": {
        "u_valley": "U자곡",
        "cirque": "권곡",
        "horn": "호른",
        "fjord": "피오르드",
        "drumlin": "드럼린",
        "moraine": "빙퇴석",
        "arete": "아레트",
    },
    "🌋 화산 지형": {
        "shield_volcano": "순상화산",
        "stratovolcano": "성층화산",
        "caldera": "칼데라",
        "crater_lake": "칼데라호",
        "lava_plateau": "용암대지",
    },
    "🦇 카르스트 지형": {
        "karst_doline": "돌리네",
        "uvala": "우발라",
        "tower_karst": "탑카르스트",
        "karren": "카렌",
    },
    "🏜️ 건조 지형": {
        "barchan": "바르한",
        "transverse_dune": "횡사구",
        "star_dune": "성사구",
        "mesa_butte": "메사/뷰트",
        "wadi": "와디",
        "playa": "플라야",
        "pedestal_rock": "버섯바위",
    },
    "🏖️ 해안 지형": {
        "coastal_cliff": "해안절벽",
        "spit_lagoon": "사취+석호",
        "tombolo": "육계사주",
        "ria_coast": "리아스해안",
        "sea_arch": "해식아치",
        "coastal_dune": "해안사구",
    },
}

# 카테고리 선택
category = st.sidebar.selectbox("카테고리 선택", list(CATEGORIES.keys()))
landforms = CATEGORIES[category]

# 그리드 크기
grid_size = st.sidebar.slider("해상도", 50, 120, 80)

st.subheader(f"{category} - {len(landforms)}종")

# 컬럼 수 계산
num_landforms = len(landforms)
cols_per_row = min(4, num_landforms)
rows = (num_landforms + cols_per_row - 1) // cols_per_row

# 지형 생성 및 표시
landform_items = list(landforms.items())

for row_idx in range(rows):
    cols = st.columns(cols_per_row)
    for col_idx, col in enumerate(cols):
        item_idx = row_idx * cols_per_row + col_idx
        if item_idx < num_landforms:
            key, name = landform_items[item_idx]
            
            with col:
                st.markdown(f"**{name}**")
                
                if key in IDEAL_LANDFORM_GENERATORS:
                    try:
                        elevation = IDEAL_LANDFORM_GENERATORS[key](grid_size)
                        
                        # 2D 탑뷰 이미지
                        fig, ax = plt.subplots(figsize=(4, 4))
                        im = ax.imshow(elevation, cmap='terrain', origin='lower')
                        ax.set_title(name, fontsize=10)
                        ax.axis('off')
                        plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
                        st.pyplot(fig)
                        plt.close(fig)
                    except Exception as e:
                        st.error(f"오류: {e}")
                else:
                    st.warning(f"{key} 미구현")

st.markdown("---")
st.caption("💡 각 지형을 클릭하면 Gallery 페이지에서 3D로 상세하게 볼 수 있습니다.")
