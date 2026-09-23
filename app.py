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
    | ⚠️ 자연재해 | **산사태 댐 붕괴 홍수** |
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

# ========== 사이드바 하단 정보 ==========
st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 방문자 통계")

# 방문자 카운터 (Supabase DB 연동)
from datetime import datetime
import json

def get_visitor_count():
    """Supabase에서 방문자 수 조회/업데이트 (경쟁 조건 수정)"""
    today = datetime.now().strftime("%Y-%m-%d")
    
    try:
        # Supabase 연결 시도
        if 'supabase' in st.secrets:
            from supabase import create_client
            
            supabase = create_client(
                st.secrets["supabase"]["url"],
                st.secrets["supabase"]["key"]
            )
            
            # 새 방문자 카운트 (세션당 1회) - 먼저 증가 처리
            if 'visitor_counted' not in st.session_state:
                st.session_state['visitor_counted'] = True
                
                # 오늘 데이터 확인
                result = supabase.table("visitors").select("*").eq("date", today).execute()
                
                if result.data:
                    # 기존 데이터 있으면 +1 업데이트 (SQL로 안전하게)
                    current_count = result.data[0]["count"]
                    supabase.table("visitors").update({"count": current_count + 1}).eq("date", today).execute()
                else:
                    # 새 날짜면 1로 시작
                    supabase.table("visitors").insert({"date": today, "count": 1}).execute()
            
            # 증가 후 최신 데이터 조회
            today_result = supabase.table("visitors").select("count").eq("date", today).execute()
            today_count = today_result.data[0]["count"] if today_result.data else 0
            
            # 총 방문자 (모든 날짜 합계)
            total_result = supabase.table("visitors").select("count").execute()
            total_count = sum(row["count"] for row in total_result.data)
            
            return {"today": today_count, "total": total_count}
        else:
            # Supabase 미설정 시 로컬 fallback
            return get_local_visitor_count()
    except Exception as e:
        # 오류 시 로컬 fallback
        return get_local_visitor_count()

def get_local_visitor_count():
    """로컬 파일 기반 방문자 카운터 (fallback)"""
    import os
    
    VISITOR_FILE = "visitor_count.json"
    
    def load_data():
        if os.path.exists(VISITOR_FILE):
            try:
                with open(VISITOR_FILE, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {"total": 0, "today": 0, "date": ""}
    
    def save_data(data):
        try:
            with open(VISITOR_FILE, 'w') as f:
                json.dump(data, f)
        except:
            pass
    
    today = datetime.now().strftime("%Y-%m-%d")
    
    if 'visitor_counted' not in st.session_state:
        st.session_state['visitor_counted'] = True
        
        visitor_data = load_data()
        
        if visitor_data["date"] != today:
            visitor_data["date"] = today
            visitor_data["today"] = 0
        
        visitor_data["total"] += 1
        visitor_data["today"] += 1
        
        save_data(visitor_data)
    else:
        visitor_data = load_data()
    
    return {"today": visitor_data.get("today", 0), "total": visitor_data.get("total", 0)}

visitor_data = get_visitor_count()
st.sidebar.metric("오늘 방문자", f"{visitor_data['today']}명")
st.sidebar.metric("총 방문자", f"{visitor_data['total']}명")

st.sidebar.markdown("---")
st.sidebar.markdown("### 📋 업데이트 내역")
st.sidebar.markdown("""
**v4.5** (2025-12-16) 🆕
- Phase 2 지형 메타데이터 완료 (20종)
- 빙하 하얀색 시각화 추가
- 칼데라호 명칭 정정

**v4.4** (2025-12-15)
- 다중 시점 카메라 (X/Y/Z축)
- 지형 형성과정 정확도 개선

**v4.3** (2025-12-14) 🎂 시작
- 31종 이상적 지형 시뮬레이션
- 형성 과정 애니메이션
""")

st.sidebar.markdown("---")
st.sidebar.markdown("### 📖 사용 설명서")
st.sidebar.markdown("""
1. **📖 Gallery**: 지형 선택 → 2D/3D 보기
2. **🎬 애니메이션**: 형성 단계 슬라이더
3. **📐 시점 변경**: 드롭다운에서 각도 선택
4. **🔬 Research**: 고급 분석 (개발중)
5. **🎓 학습 모드**: 학습목표 → 단계별 과제 → 힌트·피드백 (초안)
""")

st.sidebar.markdown("---")
st.sidebar.markdown("### 💬 문의 및 피드백")
st.sidebar.markdown("""
🔗 [티스토리 블로그](https://archiplex.tistory.com/7)

버그 제보, 기능 요청, 수업 활용 사례 등  
블로그 댓글로 남겨주세요!
""")

st.sidebar.markdown("---")
st.sidebar.markdown("### 👨‍🏫 제작자")
st.sidebar.caption("""
**2025 한백고등학교 김한솔T**  
지리 교육용 지형 시뮬레이터

📅 시작: 2025-12-14  
© 2025 Geo-Lab AI
""")

