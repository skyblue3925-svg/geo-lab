"""
🌍 Geo-Lab AI - 홈
HuggingFace Spaces Entry Point (Multi-Page Streamlit)
"""
import streamlit as st

st.set_page_config(
    page_title="🌍 Geo-Lab AI",
    page_icon="🌍",
    layout="wide"
)

# ========== 최상단: 제작자 정보 ==========
st.markdown("""
<div style='background: linear-gradient(90deg, #1565C0, #42A5F5); padding: 12px 20px; border-radius: 10px; margin-bottom: 15px;'>
    <div style='display: flex; justify-content: space-between; align-items: center; color: white;'>
        <span style='font-size: 1.1rem;'>🌍 <b>Geo-Lab AI</b> - 이상적 지형 시뮬레이터</span>
        <span style='font-size: 0.85rem;'>제작: 2025 한백고등학교 김한솔T</span>
    </div>
</div>
""", unsafe_allow_html=True)

st.title("🌍 Geo-Lab AI")
st.subheader("_교사를 위한 지형 형성과정 시각화 도구_")

st.markdown("---")

# ========== 기능 소개 ==========
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    ### 📖 이상적 지형 갤러리
    - 31종+ 교과서적 지형 모델
    - 7개 카테고리 분류
    - 2D/3D 시각화
    
    **👈 왼쪽 사이드바에서 페이지 선택**
    """)

with col2:
    st.markdown("""
    ### 🎬 형성 과정 애니메이션
    - 0% → 100% 슬라이더
    - 실시간 지형 변화 관찰
    - 물리 기반 시뮬레이션
    """)

with col3:
    st.markdown("""
    ### 🌍 지형 시나리오
    - 다중 이론 모델 비교
    - 파라미터 조절
    - 과학적 시뮬레이션
    """)

st.markdown("---")

# ========== 사용법 ==========
st.info("""
### 💡 사용법

1. **왼쪽 사이드바**에서 원하는 페이지 선택
2. **📖 이상적 지형 갤러리** - 교과서적 지형 확인
3. **🌍 지형 시나리오** - 상세 시뮬레이션 실행

> ⚠️ **각 페이지는 독립적으로 로드됩니다** - 페이지 이동 시 이전 3D가 해제되어 안정적으로 작동합니다.
""")

# ========== 지원 지형 목록 ==========
with st.expander("📋 지원 지형 목록 (36종)", expanded=False):
    st.markdown("""
    | 카테고리 | 지형 |
    |----------|------|
    | 🌊 하천 | 선상지, 자유곡류, 감입곡류, V자곡, 망상하천, 폭포 |
    | 🔺 삼각주 | 일반, 조족상, 호상, 첨두상 |
    | ❄️ 빙하 | U자곡, 권곡, 호른, 피오르드, 드럼린, 빙퇴석 |
    | 🌋 화산 | 순상화산, 성층화산, 칼데라, 화구호, 용암대지 |
    | 🦇 카르스트 | 돌리네, **우발라, 탑카르스트, 카렌** |
    | 🏜️ 건조 | 바르한, **횡사구, 성사구**, 메사/뷰트 |
    | 🏖️ 해안 | 해안절벽, 사취+석호, 육계사주, 리아스해안, 해식아치, 해안사구 |
    """)

# ========== 업데이트 내역 ==========
with st.expander("📋 업데이트 내역", expanded=False):
    st.markdown("""
    **v4.3 (2025-12-14)** 🆕
    - 새 지형 추가: 우발라, 탑카르스트, 카렌, 횡사구, 성사구
    - 리아스 해안, 해식아치 개선
    - 형성과정 애니메이션 개선 (폭포 두부침식, 피오르드 빙하→물)
    
    **v4.2 (2025-12-14)**
    - Multi-Page 구조로 변경 (안정성 향상)
    - WebGL 컨텍스트 관리 개선
    
    **v4.1 (2025-12-14)**
    - 이상적 지형 갤러리 31종 추가
    - 형성과정 애니메이션 기능
    """)

st.markdown("---")
st.caption("© 2025 한백고등학교 김한솔T | Geo-Lab AI")
