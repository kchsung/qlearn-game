# Streamlit Cloud 배포 가이드

## 1. 환경별 설정 방법

### 로컬 개발 환경
1. `.env` 파일을 프로젝트 루트에 생성
2. 다음 내용 추가:
```env
OPENAI_API_KEY=your_openai_api_key_here
SUPABASE_URL=your_supabase_url_here
SUPABASE_ANON_KEY=your_supabase_anon_key_here
```

### Streamlit Cloud 배포 환경
1. Streamlit Cloud 대시보드에서 프로젝트 선택
2. "Settings" → "Secrets" 탭으로 이동
3. 다음 secrets 추가:

```toml
OPENAI_API_KEY = "your_openai_api_key_here"
SUPABASE_URL = "your_supabase_url_here"
SUPABASE_ANON_KEY = "your_supabase_anon_key_here"
```

## 2. 자동 환경 감지

애플리케이션이 자동으로 환경을 감지합니다:
- **로컬 환경**: `.env` 파일 사용
- **Streamlit Cloud**: secrets 사용

## 3. 환경변수 우선순위

### 로컬 환경
1. **.env 파일** (최우선)
2. **환경변수** (fallback)

### Streamlit Cloud
1. **Streamlit Secrets** (최우선)
2. **환경변수** (fallback)

## 4. 보안 주의사항

- `.streamlit/secrets.toml` 파일은 `.gitignore`에 포함되어 Git에 커밋되지 않습니다
- API 키는 절대 코드에 하드코딩하지 마세요
- Streamlit Cloud에서는 웹 인터페이스를 통해서만 secrets를 설정하세요

## 5. 배포 후 확인사항

1. 애플리케이션이 정상적으로 로드되는지 확인
2. Google 로그인이 작동하는지 확인
3. 문제 풀이 기능이 정상 작동하는지 확인
4. 데이터베이스 연결이 정상인지 확인
