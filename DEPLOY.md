# 🌍 Geo-Lab AI: 웹 배포 가이드

## 배포 옵션

### 1. 🚀 Streamlit Community Cloud (추천 - 무료)

**장점:** 무료, GitHub 연동, 자동 배포

#### 단계별 가이드:

1. **GitHub 저장소 생성**
   ```bash
   cd c:\Users\HANSOL\Desktop\Geo-lab
   git init
   git add .
   git commit -m "Initial commit: 하천 지형 모듈 프로토타입"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/geo-lab-ai.git
   git push -u origin main
   ```

2. **Streamlit Cloud 접속**
   - https://share.streamlit.io 방문
   - GitHub 계정으로 로그인

3. **앱 배포**
   - "New app" 클릭
   - Repository: `YOUR_USERNAME/geo-lab-ai`
   - Branch: `main`
   - Main file path: `app/main.py`
   - "Deploy!" 클릭

4. **완료!**
   - URL 예시: `https://geo-lab-ai.streamlit.app`

---

### 2. 🔧 Hugging Face Spaces

**장점:** 무료, 커뮤니티 공유 용이

1. https://huggingface.co/spaces 에서 새 Space 생성
2. SDK: "Streamlit" 선택
3. 파일 업로드 또는 GitHub 연동

---

### 3. ☁️ 기타 옵션

| 플랫폼 | 비용 | 특징 |
|-------|-----|-----|
| **Render** | 무료 티어 | 자동 슬립, 커스텀 도메인 |
| **Railway** | 무료 $5/월 | 빠른 배포 |
| **Heroku** | 유료 | 안정적 |

---

## 로컬 실행

```bash
# 의존성 설치
pip install -r requirements.txt

# 앱 실행
streamlit run app/main.py

# 브라우저에서 열기
# http://localhost:8501
```

---

## 현재 앱 상태

✅ **로컬 실행 중**: http://localhost:8501

**외부 접속 URL**: http://211.114.121.192:8501
(같은 네트워크에서만 접근 가능)
