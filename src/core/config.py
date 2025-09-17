# config.py
"""
AI Master Quest 설정 및 상수 정의
"""

import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 데이터베이스 설정
DATABASE_PATH = "ai_master_quest.db"

# OpenAI 설정
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_MODEL = "gpt-4"
OPENAI_MAX_TOKENS = 1000
OPENAI_TEMPERATURE = 0.3

# Supabase 설정
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY')

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
    2: {"basic": 3, "intermediate": 2},
    3: {"basic": 2, "intermediate": 3, "advanced": 1},
    4: {"intermediate": 3, "advanced": 3},
    5: {"intermediate": 2, "advanced": 4, "previous_levels": True}
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

# 레벨별 아이콘 설정
LEVEL_ICONS = {
    1: '🌱',
    2: '🔍',
    3: '⚙️',
    4: '🎯',
    5: '🏆'
}
