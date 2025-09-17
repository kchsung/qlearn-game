# game_engine.py
"""
게임 엔진 및 로직 관련 클래스들
"""

import sqlite3
import hashlib
import random
from typing import Dict, List, Tuple, Optional
import streamlit as st

from src.core.config import XP_REWARDS, PROMOTION_EXAM_CONFIG, DIFFICULTY_MULTIPLIER
from src.core.database import GameDatabase
from src.services.ai_services import ProfileGenerator, QuestionGenerator


class GameEngine:
    """게임 엔진 - 레벨, 경험치, 승급 관리"""
    
    def __init__(self, db: GameDatabase):
        self.db = db
        self.xp_rewards = XP_REWARDS
    
    def calculate_xp_reward(self, score: float, time_taken: int, tokens_used: int, difficulty: str) -> int:
        """경험치 계산"""
        base_xp = self.xp_rewards["correct_answer"] if score >= 60 else 10
        
        # 난이도 보너스
        xp = int(base_xp * DIFFICULTY_MULTIPLIER.get(difficulty, 1.0))
        
        # 추가 보너스
        if score >= 90:
            xp += self.xp_rewards["perfect_score"]
        
        if time_taken < 60:  # 1분 이내
            xp += self.xp_rewards["fast_completion"]
        
        if tokens_used < 500:  # 효율적인 토큰 사용
            xp += self.xp_rewards["efficient_tokens"]
        
        return xp
    
    def check_level_up(self, user_id: str) -> Tuple[bool, Optional[int]]:
        """레벨업 체크"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # 현재 사용자 정보
        cursor.execute('''
            SELECT level, experience_points, total_questions_solved, correct_answers
            FROM users WHERE user_id = ?
        ''', (user_id,))
        
        user = cursor.fetchone()
        if not user:
            conn.close()
            return False, None
        
        current_level, xp, total_q, correct_q = user
        accuracy = (correct_q / total_q * 100) if total_q > 0 else 0
        
        # 다음 레벨 요구사항 확인
        cursor.execute('''
            SELECT required_xp, min_accuracy, required_questions
            FROM level_requirements
            WHERE level = ?
        ''', (current_level + 1,))
        
        next_level_req = cursor.fetchone()
        conn.close()
        
        if not next_level_req:
            return False, None
        
        req_xp, req_accuracy, req_questions = next_level_req
        
        # 레벨업 조건 확인
        if xp >= req_xp and accuracy >= req_accuracy and total_q >= req_questions:
            return True, current_level + 1
        
        return False, None
    
    def generate_promotion_exam(self, user_id: str, target_level: int) -> List[Dict]:
        """승급 시험 문제 생성"""
        config = PROMOTION_EXAM_CONFIG.get(target_level, {"basic": 5})
        exam_questions = []
        
        # 문제 생성
        for difficulty, count in config.items():
            if difficulty == "previous_levels":
                continue
                
            for _ in range(count):
                question = QuestionGenerator.generate_question(difficulty, target_level)
                question["id"] = f"EXAM_{target_level}_{len(exam_questions)+1}"
                question["type"] = "exam"
                exam_questions.append(question)
        
        # 레벨 4, 5의 경우 이전 단계 문제 포함
        if target_level >= 4:
            # 각 이전 레벨에서 1문제씩
            for level in range(1, target_level):
                question = QuestionGenerator.generate_question("basic", level)
                question["id"] = f"EXAM_{target_level}_PREV_{level}"
                question["difficulty"] = "review"
                question["type"] = "exam"
                exam_questions.append(question)
        
        return exam_questions


class UserManager:
    """사용자 관리 클래스"""
    
    def __init__(self, db: GameDatabase):
        self.db = db
        self.profile_gen = ProfileGenerator()
    
    def create_user(self, username: str, email: str = None) -> str:
        """새 사용자 생성"""
        try:
            user_id = hashlib.md5(username.encode()).hexdigest()[:10]
            
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            try:
                # 프로필 이미지 생성
                profile_image = self.profile_gen.generate_profile_image(username, 1)
                
                cursor.execute('''
                    INSERT INTO users (user_id, username, email, profile_image)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, username, email, profile_image))
                
                conn.commit()
                conn.close()
                return user_id
            except sqlite3.IntegrityError:
                conn.close()
                # 이미 존재하는 사용자
                return None
            except Exception as e:
                conn.close()
                st.error(f"사용자 생성 중 오류 발생: {str(e)}")
                return None
        except Exception as e:
            st.error(f"사용자 생성 중 오류 발생: {str(e)}")
            return None
    
    def get_user_profile(self, user_id: str) -> Dict:
        """사용자 프로필 조회"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT u.*, l.level_name, l.level_icon
                FROM users u
                JOIN level_requirements l ON u.level = l.level
                WHERE u.user_id = ?
            ''', (user_id,))
            
            user = cursor.fetchone()
            
            if not user:
                conn.close()
                return None
            
            # 업적 조회
            cursor.execute('''
                SELECT a.* FROM achievements a
                JOIN user_achievements ua ON a.achievement_id = ua.achievement_id
                WHERE ua.user_id = ?
            ''', (user_id,))
            
            achievements = cursor.fetchall()
            
            # 다음 레벨까지 필요한 경험치
            cursor.execute('''
                SELECT required_xp FROM level_requirements WHERE level = ?
            ''', (user[3] + 1,))  # user[3] is level
            
            next_level_xp = cursor.fetchone()
            
            conn.close()
            
            return {
                "user_id": user[0],
                "username": user[1],
                "level": user[3],
                "level_name": user[-2],
                "level_icon": user[-1],
                "xp": user[4],
                "next_level_xp": next_level_xp[0] if next_level_xp else user[4],
                "total_questions": user[5],
                "correct_answers": user[6],
                "accuracy": (user[6] / user[5] * 100) if user[5] > 0 else 0.0,
                "current_streak": user[7],
                "best_streak": user[8],
                "profile_image": user[9],
                "achievements": achievements
            }
        except Exception as e:
            st.error(f"사용자 프로필 조회 중 오류 발생: {str(e)}")
            return None
    
    def update_user_stats(self, user_id: str, grade_result: Dict, xp_earned: int):
        """사용자 통계 업데이트"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        if grade_result['passed']:
            cursor.execute('''
                UPDATE users 
                SET experience_points = experience_points + ?,
                    total_questions_solved = total_questions_solved + 1,
                    correct_answers = correct_answers + 1,
                    current_streak = current_streak + 1,
                    best_streak = MAX(best_streak, current_streak + 1),
                    last_active = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (xp_earned, user_id))
        else:
            cursor.execute('''
                UPDATE users 
                SET experience_points = experience_points + ?,
                    total_questions_solved = total_questions_solved + 1,
                    current_streak = 0,
                    last_active = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (xp_earned // 5, user_id))  # 실패해도 약간의 경험치
        
        # 업적 체크
        self._check_achievements(cursor, user_id, grade_result)
        
        conn.commit()
        conn.close()
    
    def _check_achievements(self, cursor, user_id: str, result: Dict):
        """업적 달성 체크"""
        # 첫 문제 해결
        cursor.execute('''
            SELECT COUNT(*) FROM attempt_history WHERE user_id = ? AND passed = 1
        ''', (user_id,))
        
        if cursor.fetchone()[0] == 1:
            self._grant_achievement(cursor, user_id, "first_solve")
        
        # 연속 정답 체크
        cursor.execute('''
            SELECT current_streak FROM users WHERE user_id = ?
        ''', (user_id,))
        
        streak = cursor.fetchone()[0]
        if streak == 5:
            self._grant_achievement(cursor, user_id, "streak_5")
        elif streak == 10:
            self._grant_achievement(cursor, user_id, "streak_10")
        
        # 스피드 체크
        if result['time_taken'] < 30:
            self._grant_achievement(cursor, user_id, "speed_demon")
        
        # 토큰 효율성
        if result['tokens_used'] < 200:
            self._grant_achievement(cursor, user_id, "token_saver")
    
    def _grant_achievement(self, cursor, user_id: str, achievement_id: str):
        """업적 부여"""
        try:
            cursor.execute('''
                INSERT INTO user_achievements (user_id, achievement_id)
                VALUES (?, ?)
            ''', (user_id, achievement_id))
            
            # 업적 보상 경험치
            cursor.execute('''
                SELECT xp_reward FROM achievements WHERE achievement_id = ?
            ''', (achievement_id,))
            
            xp_reward = cursor.fetchone()[0]
            
            cursor.execute('''
                UPDATE users SET experience_points = experience_points + ?
                WHERE user_id = ?
            ''', (xp_reward, user_id))
            
        except sqlite3.IntegrityError:
            # 이미 획득한 업적
            pass
