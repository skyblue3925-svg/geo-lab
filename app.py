"""
🌍 Geo-Lab AI - 홈
Ultimate Hybrid UI (Apple + Scientific + Glassmorphism)
"""
import streamlit as st

# ========== Page Config ==========
st.set_page_config(
    page_title="🌍 Geo-Lab AI",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== CSS 로드 ==========
def load_css():
    """Ultimate Hybrid CSS 로드"""
    css_path = "assets/style.css"
    try:
        with open(css_path, 'r', encoding='utf-8') as f:
            css = f.read()
        st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        pass

load_css()

# ========== 메인 헤더 ==========
st.markdown("""
<div style='text-align: center; padding: 3rem 0 2rem 0;'>
    <h1 style='font-size: 3.5rem; font-weight: 800; margin-bottom: 0.5rem; 
               background: linear-gradient(135deg, #007AFF, #5AC8FA); 
               -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>
        🌍 Geo-Lab AI
    </h1>
    <p style='font-size: 1.3rem; color: #86868b; font-weight: 400;'>
        교사를 위한 지형 형성과정 시각화 도구
    </p>
</div>
""", unsafe_allow_html=True)

# ========== 기능 카드 ==========
st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3, gap="large")

with col1:
    st.markdown("""
    <div style='background: rgba(255,255,255,0.75); backdrop-filter: blur(20px);
                border: 1px solid rgba(255,255,255,0.3); border-radius: 20px;
                padding: 2rem; text-align: center; height: 280px;
                box-shadow: 0 4px 16px rgba(0,0,0,0.06);
                transition: all 0.3s ease;'>
        <div style='font-size: 3rem; margin-bottom: 1rem;'>📖</div>
        <h3 style='font-size: 1.3rem; font-weight: 600; margin-bottom: 0.75rem;'>이상적 지형 갤러리</h3>
        <p style='color: #86868b; font-size: 0.95rem; line-height: 1.6;'>
            36종+ 교과서적 지형 모델<br>
            7개 카테고리 분류<br>
            2D/3D 인터랙티브 시각화
        </p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div style='background: rgba(255,255,255,0.75); backdrop-filter: blur(20px);
                border: 1px solid rgba(255,255,255,0.3); border-radius: 20px;
                padding: 2rem; text-align: center; height: 280px;
                box-shadow: 0 4px 16px rgba(0,0,0,0.06);
                transition: all 0.3s ease;'>
        <div style='font-size: 3rem; margin-bottom: 1rem;'>🎬</div>
        <h3 style='font-size: 1.3rem; font-weight: 600; margin-bottom: 0.75rem;'>형성 과정 애니메이션</h3>
        <p style='color: #86868b; font-size: 0.95rem; line-height: 1.6;'>
            0% → 100% 슬라이더<br>
            실시간 지형 변화 관찰<br>
            물리 기반 시뮬레이션
        </p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div style='background: rgba(255,255,255,0.75); backdrop-filter: blur(20px);
                border: 1px solid rgba(255,255,255,0.3); border-radius: 20px;
                padding: 2rem; text-align: center; height: 280px;
                box-shadow: 0 4px 16px rgba(0,0,0,0.06);
                transition: all 0.3s ease;'>
        <div style='font-size: 3rem; margin-bottom: 1rem;'>🧪</div>
        <h3 style='font-size: 1.3rem; font-weight: 600; margin-bottom: 0.75rem;'>고급 시뮬레이션</h3>
        <p style='color: #86868b; font-size: 0.95rem; line-height: 1.6;'>
            18+ 지질학적 프로세스<br>
            시나리오 기반 설정<br>
            과학적 파라미터 조절
        </p>
    </div>
    """, unsafe_allow_html=True)

# ========== 시작하기 ==========
st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)

st.markdown("""
<div style='background: linear-gradient(135deg, rgba(0,122,255,0.1), rgba(90,200,250,0.1));
            border-radius: 16px; padding: 2rem; text-align: center;
            border: 1px solid rgba(0,122,255,0.2);'>
    <h3 style='font-weight: 600; margin-bottom: 0.5rem;'>👈 시작하기</h3>
    <p style='color: #86868b; margin: 0;'>왼쪽 사이드바에서 원하는 페이지를 선택하세요</p>
</div>
""", unsafe_allow_html=True)

# ========== 지원 지형 ==========
st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)

with st.expander("📋 지원 지형 목록 (36종)", expanded=False):
    st.markdown("""
    | 카테고리 | 지형 |
    |----------|------|
    | 🌊 **하천** | 선상지, 자유곡류, 감입곡류, V자곡, 망상하천, 폭포 |
    | 🔺 **삼각주** | 일반, 조족상, 호상, 첨두상 |
    | ❄️ **빙하** | U자곡, 권곡, 호른, 피오르드, 드럼린, 빙퇴석 |
    | 🌋 **화산** | 순상화산, 성층화산, 칼데라, 화구호, 용암대지 |
    | 🦇 **카르스트** | 돌리네, 우발라, 탑카르스트, 카렌 |
    | 🏜️ **건조** | 바르한, 횡사구, 성사구, 메사/뷰트 |
    | 🏖️ **해안** | 해안절벽, 사취+석호, 육계사주, 리아스해안 |
    """)

# ========== 업데이트 ==========
with st.expander("📋 업데이트 내역", expanded=False):
    st.markdown("""
    **v5.0** (2025-12-23) 🆕
    - Ultimate Hybrid UI 완전 개편
    - Apple + Scientific + Glassmorphism 디자인
    
    **v4.5** (2025-12-16)
    - 18+ 지질학적 프로세스 LEM 구현
    - 시나리오 기반 UI 추가
    """)

# ========== Footer ==========
st.markdown("<div style='height: 3rem;'></div>", unsafe_allow_html=True)
st.markdown("""
<div style='text-align: center; padding: 1rem 0; border-top: 1px solid rgba(0,0,0,0.08);'>
    <p style='color: #86868b; font-size: 0.85rem; margin: 0;'>
        © 2025 한백고등학교 김한솔T | Geo-Lab AI
    </p>
</div>
""", unsafe_allow_html=True)

# ========== 사이드바 ==========
st.sidebar.markdown("""
<div style='text-align: center; padding: 1rem 0;'>
    <span style='font-size: 2rem;'>🌍</span>
    <h2 style='font-size: 1.2rem; font-weight: 600; margin: 0.5rem 0 0 0;'>Geo-Lab AI</h2>
    <p style='color: #86868b; font-size: 0.8rem; margin: 0;'>v5.0</p>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("---")

# 방문자 카운터
from datetime import datetime
import json

def get_visitor_count():
    """방문자 수 조회/업데이트"""
    today = datetime.now().strftime("%Y-%m-%d")
    
    try:
        if 'supabase' in st.secrets:
            from supabase import create_client
            
            supabase = create_client(
                st.secrets["supabase"]["url"],
                st.secrets["supabase"]["key"]
            )
            
            if 'visitor_counted' not in st.session_state:
                st.session_state['visitor_counted'] = True
                
                result = supabase.table("visitors").select("*").eq("date", today).execute()
                
                if result.data:
                    current_count = result.data[0]["count"]
                    supabase.table("visitors").update({"count": current_count + 1}).eq("date", today).execute()
                else:
                    supabase.table("visitors").insert({"date": today, "count": 1}).execute()
            
            today_result = supabase.table("visitors").select("count").eq("date", today).execute()
            today_count = today_result.data[0]["count"] if today_result.data else 0
            
            total_result = supabase.table("visitors").select("count").execute()
            total_count = sum(row["count"] for row in total_result.data)
            
            return {"today": today_count, "total": total_count}
        else:
            return {"today": 0, "total": 0}
    except:
        return {"today": 0, "total": 0}

visitor_data = get_visitor_count()

st.sidebar.markdown("### 📊 방문자")
col_v1, col_v2 = st.sidebar.columns(2)
col_v1.metric("오늘", f"{visitor_data['today']}")
col_v2.metric("총", f"{visitor_data['total']}")

st.sidebar.markdown("---")

st.sidebar.markdown("### 💬 피드백")
st.sidebar.markdown("""
[📝 블로그 댓글](https://archiplex.tistory.com/7)
""")

st.sidebar.markdown("---")

st.sidebar.caption("""
**제작자**: 한백고 김한솔T  
**시작**: 2025-12-14
""")
