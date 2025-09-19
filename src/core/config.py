# config.py
"""
AI Master Quest 설정 및 상수 정의
"""

import os
import streamlit as st

def is_streamlit_cloud():
    """Streamlit Cloud 환경인지 확인"""
    try:
        # Streamlit Cloud 환경 감지
        return (
            os.getenv('STREAMLIT_SERVER_BASE_URL_PATH') or
            os.getenv('STREAMLIT_SERVER_PORT') == '8501' or
            'streamlit.app' in str(st.get_option('server.headless', '')) or
            os.getenv('STREAMLIT_SHARING_MODE') == 'True' or
            hasattr(st, 'secrets') and hasattr(st.secrets, '_secrets')
        )
    except:
        return False

def get_secret(key: str, default: str = None) -> str:
    """환경에 따라 적절한 방법으로 환경변수 가져오기"""
    if is_streamlit_cloud():
        # Streamlit Cloud 환경: secrets 사용
        try:
            if hasattr(st, 'secrets') and key in st.secrets:
                return st.secrets[key]
        except:
            pass
    else:
        # 로컬 환경: .env 파일 사용
        try:
            from dotenv import load_dotenv
            # 현재 디렉토리에서 .env 파일 로드
            load_dotenv(override=True)
            value = os.getenv(key, default)
            if value and value != default:
                return value
        except ImportError:
            # python-dotenv가 없는 경우 환경변수만 사용
            pass
        except Exception as e:
            # .env 파일 로드 실패 시 환경변수에서 시도
            pass
    
    # fallback: 환경변수에서 시도
    return os.getenv(key, default)

# OpenAI 설정
OPENAI_API_KEY = get_secret('OPENAI_API_KEY')
OPENAI_MODEL = "gpt-5"

# Supabase 설정
SUPABASE_URL = get_secret('SUPABASE_URL')
SUPABASE_ANON_KEY = get_secret('SUPABASE_ANON_KEY')

# 디버깅: 환경변수 로드 상태 확인
def debug_env_loading():
    """환경변수 로드 상태 디버깅"""
    print(f"🔍 환경 감지: {'Streamlit Cloud' if is_streamlit_cloud() else '로컬'}")
    print(f"🔍 OPENAI_API_KEY: {'설정됨' if OPENAI_API_KEY else '없음'}")
    print(f"🔍 SUPABASE_URL: {'설정됨' if SUPABASE_URL else '없음'}")
    print(f"🔍 SUPABASE_ANON_KEY: {'설정됨' if SUPABASE_ANON_KEY else '없음'}")
    
    # .env 파일 존재 확인
    if not is_streamlit_cloud():
        env_file_exists = os.path.exists('.env')
        print(f"🔍 .env 파일 존재: {'예' if env_file_exists else '아니오'}")
        
        if env_file_exists:
            try:
                with open('.env', 'r', encoding='utf-8') as f:
                    content = f.read()
                    print(f"🔍 .env 파일 크기: {len(content)} bytes")
                    print(f"🔍 .env 파일 내용 미리보기: {content[:100]}...")
            except Exception as e:
                print(f"🔍 .env 파일 읽기 오류: {e}")

# 자동 디버깅 실행
debug_env_loading()

# 환경변수 검증
def validate_environment():
    """환경변수 검증"""
    missing_vars = []
    
    if not SUPABASE_URL or SUPABASE_URL == 'your_supabase_url_here':
        missing_vars.append('SUPABASE_URL')
    if not SUPABASE_ANON_KEY or SUPABASE_ANON_KEY == 'your_supabase_anon_key_here':
        missing_vars.append('SUPABASE_ANON_KEY')
    if not OPENAI_API_KEY or OPENAI_API_KEY == 'your_openai_api_key_here':
        missing_vars.append('OPENAI_API_KEY')
    
    if missing_vars:
        print("❌ 다음 환경변수가 설정되지 않았습니다:")
        for var in missing_vars:
            print(f"   - {var}")
        
        if is_streamlit_cloud():
            print("\n📝 Streamlit Cloud에서 secrets를 설정하세요:")
            print("1. Streamlit Cloud 대시보드 → Settings → Secrets")
            print("2. 다음 secrets 추가:")
            print("   OPENAI_API_KEY=your_openai_api_key_here")
            print("   SUPABASE_URL=your_supabase_url_here")
            print("   SUPABASE_ANON_KEY=your_supabase_anon_key_here")
        else:
            print("\n📝 로컬 개발 환경:")
            print("1. .env 파일을 생성하고 다음 내용을 추가하세요:")
            print("   SUPABASE_URL=your_supabase_url_here")
            print("   SUPABASE_ANON_KEY=your_supabase_anon_key_here")
            print("   OPENAI_API_KEY=your_openai_api_key_here")
            print("\n🔗 Supabase 설정 방법:")
            print("1. https://supabase.com 에서 프로젝트 생성")
            print("2. Settings → API에서 URL과 anon key 복사")
            print("3. .env 파일에 추가")
        
        return False
    
    return True

# 게임 설정
XP_REWARDS = {
    "correct_answer": 50,
    "perfect_score": 100,
    "fast_completion": 30,
    "efficient_tokens": 20,
    "level_up_bonus": 500
}

# 레벨 설정
LEVEL_REQUIREMENTS = [
    (1, 0, 60.0, 10, "AI Beginner", "🌱", "기본 문제 접근 가능"),
    (2, 500, 70.0, 25, "AI Explorer", "🔍", "중급 문제 접근 가능, 힌트 기능"),
    (3, 1500, 75.0, 50, "AI Practitioner", "⚙️", "고급 문제 접근 가능, 상세 피드백"),
    (4, 3000, 80.0, 100, "AI Expert", "🎯", "전문가 문제 접근 가능, 문제 제안 권한"),
    (5, 5000, 85.0, 200, "AI Master", "🏆", "모든 기능 접근 가능, 멘토 권한")
]

# 업적 설정
ACHIEVEMENTS = [
    ("first_solve", "첫 문제 해결", "첫 번째 문제를 성공적으로 해결했습니다", "🎯", 50, "common"),
    ("streak_5", "5연속 정답", "5문제를 연속으로 맞췄습니다", "🔥", 100, "rare"),
    ("streak_10", "10연속 정답", "10문제를 연속으로 맞췄습니다", "💥", 200, "epic"),
    ("speed_demon", "스피드 데몬", "30초 내에 문제를 해결했습니다", "⚡", 150, "rare"),
    ("perfect_exam", "완벽한 승급", "승급 시험에서 만점을 받았습니다", "💯", 300, "legendary"),
    ("ai_enthusiast", "AI 열정가", "100문제를 해결했습니다", "🤖", 500, "epic"),
    ("token_saver", "토큰 절약가", "최소 토큰으로 문제를 해결했습니다", "💰", 100, "rare"),
    ("comeback_kid", "재도전의 달인", "실패 후 재도전으로 성공했습니다", "💪", 150, "rare")
]

# 채점 기준
GRADING_CRITERIA = {
    "basic": {
        "accuracy": 0.6,
        "completeness": 0.3,
        "clarity": 0.1
    },
    "intermediate": {
        "accuracy": 0.4,
        "approach": 0.3,
        "implementation": 0.2,
        "clarity": 0.1
    },
    "advanced": {
        "innovation": 0.3,
        "feasibility": 0.25,
        "completeness": 0.25,
        "business_impact": 0.2
    }
}

# 승급 시험 설정
PROMOTION_EXAM_CONFIG = {
    2: {
        "questions": 5,
        "passing_score": 80,
        "time_limit": 300,
        "difficulty_distribution": {"basic": 3, "intermediate": 2}
    },
    3: {
        "questions": 6,
        "passing_score": 80,
        "time_limit": 360,
        "difficulty_distribution": {"basic": 2, "intermediate": 3, "advanced": 1}
    },
    4: {
        "questions": 7,
        "passing_score": 85,
        "time_limit": 420,
        "difficulty_distribution": {"intermediate": 3, "advanced": 4}
    },
    5: {
        "questions": 8,
        "passing_score": 85,
        "time_limit": 480,
        "difficulty_distribution": {"intermediate": 2, "advanced": 6}
    }
}

# 난이도 설정
DIFFICULTY_MULTIPLIER = {
    "basic": 1.2,
    "intermediate": 1.0,
    "advanced": 0.8
}

# 레벨별 색상 설정
LEVEL_COLORS = {
    1: '#90EE90',  # Light green
    2: '#87CEEB',  # Sky blue
    3: '#DDA0DD',  # Plum
    4: '#FFD700',  # Gold
    5: '#FF6347'   # Tomato
}

# 레벨별 아이콘 설정 (성장 과정)
LEVEL_ICONS = {
    1: '🌱',  # 새싹 - 시작
    2: '🌿',  # 잎사귀 - 성장
    3: '🌳',  # 나무 - 발전
    4: '🌟',  # 별 - 숙련
    5: '👑'   # 왕관 - 마스터
}
