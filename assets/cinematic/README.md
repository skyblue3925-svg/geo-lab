# 🎬 시네마틱 지형 영상

나노 바나나 프로(Nano Banana Pro)로 제작한 고품질 교육용 영상 저장소입니다.

## 파일 명명 규칙
- 형식: `{landform_id}.mp4` 또는 `.webm`
- 예시: `fjord_formation.mp4`, `caldera_formation.webm`

## 제작 워크플로우

### 1. 나노 바나나 프로 접속
- URL: https://nanobanana.pro
- Google 계정으로 로그인

### 2. 소스 이미지 업로드
- `assets/reference/` 폴더의 관련 이미지 업로드
- 예: 피오르드 → `fjord_formation.png`, `fjord_texture.png`

### 3. 프롬프트 작성 예시
```
Create a 30-second educational animation showing fjord formation:
1. A V-shaped valley carved by a river
2. Glacier advancing and eroding into U-shaped valley  
3. Glacier retreating
4. Sea water flooding the valley to form a fjord
Photorealistic style, smooth transitions, aerial perspective.
```

### 4. 영상 저장
- 다운로드 후 이 폴더에 저장
- `metadata.json` 업데이트 (status: "pending" → "ready")

## 상태 값
| 상태 | 의미 |
|-----|-----|
| `pending` | 제작 예정 |
| `in_progress` | 제작 중 |
| `ready` | 완료, 재생 가능 |
