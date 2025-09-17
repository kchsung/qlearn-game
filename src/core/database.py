# database.py
"""
데이터베이스 관련 클래스 및 함수
"""

import sqlite3
import streamlit as st
from src.core.config import DATABASE_PATH, LEVEL_REQUIREMENTS, ACHIEVEMENTS


class GameDatabase:
    """게임화된 평가 시스템 데이터베이스"""
    
    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """게임 데이터베이스 초기화"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
        except Exception as e:
            st.error(f"데이터베이스 연결 오류: {str(e)}")
            return
        
        # 사용자 프로필 테이블
        cursor.execute('''
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 레벨 요구사항 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS level_requirements (
                level INTEGER PRIMARY KEY,
                required_xp INTEGER,
                min_accuracy REAL,
                required_questions INTEGER,
                level_name TEXT,
                level_icon TEXT,
                perks TEXT
            )
        ''')
        
        # 문제 풀이 기록 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attempt_history (
                attempt_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                question_id TEXT NOT NULL,
                level INTEGER,
                passed BOOLEAN,
                score REAL,
                time_taken INTEGER,
                tokens_used INTEGER,
                attempt_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                feedback TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # 승급 시험 기록 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS promotion_exams (
                exam_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                from_level INTEGER,
                to_level INTEGER,
                exam_questions TEXT,
                passed BOOLEAN,
                total_score REAL,
                exam_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                retry_count INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # 업적/배지 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS achievements (
                achievement_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                icon TEXT,
                xp_reward INTEGER,
                rarity TEXT
            )
        ''')
        
        # 사용자 업적 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_achievements (
                user_id TEXT,
                achievement_id TEXT,
                earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, achievement_id),
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (achievement_id) REFERENCES achievements(achievement_id)
            )
        ''')
        
        # 리더보드 뷰
        cursor.execute('''
            CREATE VIEW IF NOT EXISTS leaderboard AS
            SELECT 
                username,
                level,
                experience_points,
                total_questions_solved,
                CASE 
                    WHEN total_questions_solved = 0 THEN 0.0
                    ELSE ROUND(CAST(correct_answers AS REAL) / total_questions_solved * 100, 2)
                END as accuracy,
                best_streak
            FROM users
            ORDER BY level DESC, experience_points DESC
        ''')
        
        # 레벨 요구사항 초기 데이터
        self._init_level_requirements(cursor)
        
        # 기본 업적 초기화
        self._init_achievements(cursor)
        
        try:
            conn.commit()
            conn.close()
        except Exception as e:
            st.error(f"데이터베이스 초기화 오류: {str(e)}")
            if conn:
                conn.close()
    
    def _init_level_requirements(self, cursor):
        """레벨 요구사항 초기화"""
        cursor.executemany('''
            INSERT OR REPLACE INTO level_requirements 
            (level, required_xp, min_accuracy, required_questions, level_name, level_icon, perks)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', LEVEL_REQUIREMENTS)
    
    def _init_achievements(self, cursor):
        """기본 업적 초기화"""
        cursor.executemany('''
            INSERT OR REPLACE INTO achievements 
            (achievement_id, name, description, icon, xp_reward, rarity)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ACHIEVEMENTS)
    
    def get_connection(self):
        """데이터베이스 연결 반환"""
        return sqlite3.connect(self.db_path)
    
    def execute_query(self, query: str, params: tuple = None):
        """쿼리 실행 및 결과 반환"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            result = cursor.fetchall()
            conn.close()
            return result
        except Exception as e:
            st.error(f"쿼리 실행 오류: {str(e)}")
            return None
    
    def execute_update(self, query: str, params: tuple = None):
        """업데이트 쿼리 실행"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            st.error(f"업데이트 쿼리 실행 오류: {str(e)}")
            return False
