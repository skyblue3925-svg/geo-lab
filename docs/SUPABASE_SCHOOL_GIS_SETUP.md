# Supabase School GIS Setup

이 문서는 `apps/school-neighborhood-gis` 를 실제 학교 서비스로 전환할 때 필요한 최소 설정만 정리합니다.

## 1. Supabase 프로젝트 생성

1. Supabase에서 새 프로젝트를 만듭니다.
2. Project URL 과 anon public key 를 확인합니다.

## 2. 데이터베이스 스키마 적용

1. Supabase SQL Editor를 엽니다.
2. [supabase-schema.sql](C:/Users/HANSOL/OneDrive/Desktop/Geo-lab/apps/school-neighborhood-gis/supabase-schema.sql) 내용을 실행합니다.
3. 기본 교사 이메일 `teacher@school.kr` 대신 실제 교사 이메일을 `gis_moderators` 테이블에 추가합니다.

예시:

```sql
insert into public.gis_moderators (email)
values
  ('teacher1@school.kr'),
  ('teacher2@school.kr')
on conflict (email) do nothing;
```

## 3. 런타임 설정

[runtime-config.js](C:/Users/HANSOL/OneDrive/Desktop/Geo-lab/apps/school-neighborhood-gis/runtime-config.js)에 아래 값을 넣습니다.

```js
window.__SCHOOL_GIS_RUNTIME_CONFIG__ = {
  schoolName: "한백고등학교",
  mapCenter: { lat: 37.5665, lng: 126.978, label: "학교 중심점" },
  storage: {
    useSupabaseWhenConfigured: true,
    supabaseUrl: "https://YOUR_PROJECT.supabase.co",
    supabaseAnonKey: "YOUR_PUBLIC_ANON_KEY",
    tableName: "gis_reports",
  },
  moderation: {
    supportEmail: "teacher@school.kr",
  },
};
```

## 4. 동작 확인

1. 학생용 링크에서 제보를 하나 등록합니다.
2. 교사용 링크에서 OTP 로그인 후 승인합니다.
3. 학생용 화면에 승인된 제보가 보이는지 확인합니다.

## 5. 배포

Cloudflare Pages 배포 절차는 [CLOUDFLARE_PAGES_SCHOOL_GIS.md](C:/Users/HANSOL/OneDrive/Desktop/Geo-lab/docs/CLOUDFLARE_PAGES_SCHOOL_GIS.md)를 봅니다.

## 운영 원칙

- 학생 제보는 처음에 `한 학교`, `한두 개 주제`로만 시작합니다.
- 전국 통계는 처음에 `지표 1개`만 연결합니다.
- 집 주소, 개인 이동경로, 민감정보는 저장하지 않습니다.
