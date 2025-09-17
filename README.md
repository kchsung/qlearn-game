# AI Master Quest - AI 활용능력평가 게임

AI 활용 능력을 게임화된 방식으로 평가하고 학습할 수 있는 Streamlit 기반 웹 애플리케이션입니다.

## 주요 기능

- 🎮 **게임화된 학습**: 레벨 시스템, 경험치, 업적을 통한 동기부여
- 🤖 **AI 자동 채점**: OpenAI GPT-4를 활용한 자동 채점 시스템
- 📊 **상세한 통계**: 개인 성과 분석 및 리더보드
- 🏆 **승급 시스템**: 레벨별 승급 시험을 통한 단계적 성장
- 🎯 **다양한 난이도**: 초급부터 고급까지 단계별 문제 제공

## 설치 및 실행

### 1. 필요한 패키지 설치

```bash
pip install -r requirements.txt
```

### 2. 환경 변수 설정

`.env` 파일을 생성하고 필요한 API 키들을 설정하세요:

```
# OpenAI API 키 설정
OPENAI_API_KEY=your_openai_api_key_here

# Supabase 설정
SUPABASE_URL=your_supabase_project_url
SUPABASE_ANON_KEY=your_supabase_anon_key
```

#### Supabase 설정 방법:
1. [Supabase](https://supabase.com)에서 새 프로젝트 생성
2. **데이터베이스 테이블 생성**: SQL Editor에서 다음 SQL 실행
   ```sql
   -- users 테이블 생성
   CREATE TABLE IF NOT EXISTS users (
       user_id TEXT PRIMARY KEY,
       username TEXT UNIQUE NOT NULL,
       email TEXT,
       level INTEGER DEFAULT 1,
       experience_points INTEGER DEFAULT 0,
       total_questions_solved INTEGER DEFAULT 0,
       correct_answers INTEGER DEFAULT 0,
       current_streak INTEGER DEFAULT 0,
       best_streak INTEGER DEFAULT 0,
       profile_image TEXT,
       profile_prompt TEXT,
       created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
       last_active TIMESTAMP WITH TIME ZONE DEFAULT NOW()
   );

   -- level_requirements 테이블 생성
   CREATE TABLE IF NOT EXISTS level_requirements (
       level INTEGER PRIMARY KEY,
       required_xp INTEGER,
       title TEXT,
       description TEXT
   );

   -- achievements 테이블 생성
   CREATE TABLE IF NOT EXISTS achievements (
       achievement_id TEXT PRIMARY KEY,
       name TEXT NOT NULL,
       description TEXT,
       icon TEXT,
       requirement_type TEXT,
       requirement_value INTEGER
   );

   -- 초기 데이터 삽입
   INSERT INTO level_requirements (level, required_xp, title, description) VALUES
   (1, 0, '초보자', '게임을 시작하는 단계'),
   (2, 100, '학습자', '기본기를 다지는 단계'),
   (3, 250, '성장자', '실력을 쌓아가는 단계'),
   (4, 450, '숙련자', '전문성을 키우는 단계'),
   (5, 700, '전문가', '높은 수준의 실력자'),
   (6, 1000, '마스터', '최고 수준의 전문가'),
   (7, 1350, '그랜드마스터', '전설적인 실력자'),
   (8, 1750, '레전드', '신화적인 존재'),
   (9, 2200, '미스터리', '신비로운 존재'),
   (10, 2700, '올마이티', '전능한 존재')
   ON CONFLICT (level) DO NOTHING;

   INSERT INTO achievements (achievement_id, name, description, icon, requirement_type, requirement_value) VALUES
   ('first_question', '첫 번째 문제', '첫 번째 문제를 해결했습니다!', '🎯', 'questions_solved', 1),
   ('level_5', '레벨 5 달성', '레벨 5에 도달했습니다!', '⭐', 'level', 5),
   ('level_10', '레벨 10 달성', '레벨 10에 도달했습니다!', '🌟', 'level', 10),
   ('streak_5', '5연속 정답', '5문제 연속으로 정답을 맞췄습니다!', '🔥', 'streak', 5),
   ('streak_10', '10연속 정답', '10문제 연속으로 정답을 맞췄습니다!', '🚀', 'streak', 10),
   ('accuracy_80', '80% 정확도', '80% 이상의 정확도를 달성했습니다!', '🎯', 'accuracy', 80)
   ON CONFLICT (achievement_id) DO NOTHING;

   -- 인덱스 생성 (성능 최적화)
   CREATE INDEX IF NOT EXISTS idx_users_level ON users(level);
   CREATE INDEX IF NOT EXISTS idx_users_experience ON users(experience_points);
   CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
   ```
3. Authentication > Providers에서 Google OAuth 활성화
4. Google Cloud Console에서 OAuth 2.0 클라이언트 ID 생성
5. Supabase에 Google OAuth 설정 추가
6. Settings > API에서 URL과 anon key 복사하여 환경 변수에 설정

### 3. 애플리케이션 실행

```bash
streamlit run main.py
```

## 사용법

1. **Google 로그인**: Google 계정으로 안전하게 로그인
2. **문제 도전**: 메인 탭에서 난이도를 선택하고 문제를 받아 풀어보세요
3. **승급 시험**: 충분한 경험치와 정답률을 쌓으면 승급 시험에 도전할 수 있습니다
4. **통계 확인**: 개인 성과와 리더보드를 통해 성장을 확인하세요

## 레벨 시스템

- **레벨 1 (AI Beginner)**: 기본 문제 접근 가능
- **레벨 2 (AI Explorer)**: 중급 문제 접근, 힌트 기능
- **레벨 3 (AI Practitioner)**: 고급 문제 접근, 상세 피드백
- **레벨 4 (AI Expert)**: 전문가 문제 접근, 문제 제안 권한
- **레벨 5 (AI Master)**: 모든 기능 접근, 멘토 권한

## 프로젝트 구조

```
streamlit-qlearn-game/
├── main.py                          # 메인 실행 파일
├── src/                            # 소스 코드
│   ├── __init__.py
│   ├── app.py                      # 메인 애플리케이션 클래스
│   ├── core/                       # 핵심 모듈
│   │   ├── __init__.py
│   │   ├── config.py               # 설정 및 상수
│   │   └── database.py             # 데이터베이스 관련 클래스
│   ├── services/                   # 서비스 레이어
│   │   ├── __init__.py
│   │   ├── ai_services.py          # AI 서비스 (채점, 프로필 생성)
│   │   └── game_engine.py          # 게임 엔진 및 사용자 관리
│   ├── auth/                       # 인증 모듈
│   │   ├── __init__.py
│   │   └── authentication.py       # 사용자 인증 및 세션 관리
│   └── models/                     # 데이터 모델
│       └── __init__.py
├── ui/                             # UI 컴포넌트
│   ├── __init__.py
│   ├── components/                 # 재사용 가능한 UI 컴포넌트
│   │   ├── __init__.py
│   │   ├── auth_components.py      # 인증 관련 UI
│   │   └── common_components.py    # 공통 UI 컴포넌트
│   ├── pages/                      # 페이지 컴포넌트
│   │   ├── __init__.py
│   │   ├── welcome_page.py         # 환영 페이지
│   │   ├── challenge_page.py       # 문제 도전 페이지
│   │   ├── leaderboard_page.py     # 리더보드 페이지
│   │   ├── stats_page.py           # 통계 페이지
│   │   └── promotion_page.py       # 승급 시험 페이지
│   └── layouts/                    # 레이아웃 컴포넌트
│       └── __init__.py
├── requirements.txt                # 필요한 패키지 목록
├── README.md                      # 프로젝트 설명서
└── ai_assessment_game_backup.py   # 기존 파일 백업
```

## 아키텍처

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   UI Layer      │    │  Service Layer  │    │   Core Layer    │
│                 │    │                 │    │                 │
│ • Pages         │◄──►│ • AI Services   │◄──►│ • Database      │
│ • Components    │    │ • Game Engine   │    │ • Config        │
│ • Layouts       │    │ • Auth Manager  │    │ • Models        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 기술 스택

- **Frontend**: Streamlit
- **Backend**: Python
- **Database**: SQLite + Supabase
- **Authentication**: Supabase Auth + Google OAuth
- **AI**: OpenAI GPT-4
- **Visualization**: Plotly
- **Image Processing**: Pillow

## 주의사항

- OpenAI API 키가 없어도 시뮬레이션 모드로 동작합니다
- 실제 AI 채점을 위해서는 유효한 OpenAI API 키가 필요합니다
- Google OAuth 로그인을 위해서는 Supabase 설정이 필요합니다
- 사용자 데이터는 Supabase와 로컬 SQLite 데이터베이스에 동기화됩니다

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.
