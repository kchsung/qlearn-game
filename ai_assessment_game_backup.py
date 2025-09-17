# ai_assessment_game.py

import streamlit as st
import openai
from openai import OpenAI
import sqlite3
import pandas as pd
import json
from datetime import datetime, timedelta
import random
from typing import Dict, List, Tuple, Optional
import plotly.express as px
import plotly.graph_objects as go
import os
from dotenv import load_dotenv
import time
import base64
from PIL import Image, ImageDraw, ImageFont
import io
import hashlib

# 환경 변수 로드
load_dotenv()

# OpenAI 클라이언트 초기화 (API 키가 없어도 기본 동작하도록)
try:
    api_key = os.getenv('OPENAI_API_KEY')
    if api_key:
        client = OpenAI(api_key=api_key)
    else:
        client = None
        st.warning("⚠️ OPENAI_API_KEY가 설정되지 않았습니다. 일부 기능이 제한될 수 있습니다.")
except Exception as e:
    client = None
    st.error(f"OpenAI 클라이언트 초기화 오류: {str(e)}")

# Streamlit 버전 호환성을 위한 rerun 함수
def safe_rerun():
    """Streamlit 버전에 관계없이 안전하게 페이지를 새로고침합니다."""
    try:
        if hasattr(st, 'rerun'):
            st.rerun()
        elif hasattr(st, 'experimental_rerun'):
            st.experimental_rerun()
        else:
            # 최후의 수단으로 페이지 새로고침
            st.markdown('<script>window.location.reload();</script>', unsafe_allow_html=True)
    except Exception:
        # 모든 방법이 실패하면 아무것도 하지 않음
        pass

class GameDatabase:
    """게임화된 평가 시스템 데이터베이스"""
    
    def __init__(self, db_path: str = "ai_master_quest.db"):
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
        levels = [
            (1, 0, 60.0, 10, "AI Beginner", "🌱", "기본 문제 접근 가능"),
            (2, 500, 70.0, 25, "AI Explorer", "🔍", "중급 문제 접근 가능, 힌트 기능"),
            (3, 1500, 75.0, 50, "AI Practitioner", "⚙️", "고급 문제 접근 가능, 상세 피드백"),
            (4, 3000, 80.0, 100, "AI Expert", "🎯", "전문가 문제 접근 가능, 문제 제안 권한"),
            (5, 5000, 85.0, 200, "AI Master", "🏆", "모든 기능 접근 가능, 멘토 권한")
        ]
        
        cursor.executemany('''
            INSERT OR REPLACE INTO level_requirements 
            (level, required_xp, min_accuracy, required_questions, level_name, level_icon, perks)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', levels)
    
    def _init_achievements(self, cursor):
        """기본 업적 초기화"""
        achievements = [
            ("first_solve", "첫 문제 해결", "첫 번째 문제를 성공적으로 해결했습니다", "🎯", 50, "common"),
            ("streak_5", "5연속 정답", "5문제를 연속으로 맞췄습니다", "🔥", 100, "rare"),
            ("streak_10", "10연속 정답", "10문제를 연속으로 맞췄습니다", "💥", 200, "epic"),
            ("speed_demon", "스피드 데몬", "30초 내에 문제를 해결했습니다", "⚡", 150, "rare"),
            ("perfect_exam", "완벽한 승급", "승급 시험에서 만점을 받았습니다", "💯", 300, "legendary"),
            ("ai_enthusiast", "AI 열정가", "100문제를 해결했습니다", "🤖", 500, "epic"),
            ("token_saver", "토큰 절약가", "최소 토큰으로 문제를 해결했습니다", "💰", 100, "rare"),
            ("comeback_kid", "재도전의 달인", "실패 후 재도전으로 성공했습니다", "💪", 150, "rare")
        ]
        
        cursor.executemany('''
            INSERT OR REPLACE INTO achievements 
            (achievement_id, name, description, icon, xp_reward, rarity)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', achievements)

class ProfileGenerator:
    """AI 기반 프로필 이미지 생성기"""
    
    @staticmethod
    def generate_profile_image(username: str, level: int, prompt: str = None) -> str:
        """사용자 프로필 이미지 생성"""
        # 간단한 아바타 생성 (실제로는 DALL-E API 사용 가능)
        # 여기서는 시연을 위해 간단한 이미지 생성
        
        img = Image.new('RGB', (200, 200), color='white')
        draw = ImageDraw.Draw(img)
        
        # 레벨에 따른 배경색
        colors = {
            1: '#90EE90',  # Light green
            2: '#87CEEB',  # Sky blue
            3: '#DDA0DD',  # Plum
            4: '#FFD700',  # Gold
            5: '#FF6347'   # Tomato
        }
        
        # 배경 그리기
        draw.rectangle([0, 0, 200, 200], fill=colors.get(level, '#FFFFFF'))
        
        # 사용자 이니셜
        initials = ''.join([word[0].upper() for word in username.split()[:2]])
        
        # 텍스트 그리기
        try:
            font = ImageFont.truetype("arial.ttf", 80)
        except:
            font = ImageFont.load_default()
        
        draw.text((100, 100), initials, fill='white', anchor='mm', font=font)
        
        # 레벨 표시
        level_icons = {1: '🌱', 2: '🔍', 3: '⚙️', 4: '🎯', 5: '🏆'}
        draw.text((170, 170), level_icons.get(level, ''), fill='white', anchor='mm')
        
        # Base64로 인코딩
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"

class AutoGrader:
    """AI 기반 자동 채점 시스템"""
    
    def __init__(self):
        self.grading_criteria = {
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
    
    def grade_answer(self, question: Dict, answer: str, level: str) -> Dict:
        """답변 자동 채점"""
        
        # 시간 및 토큰 측정 시작
        start_time = time.time()
        
        # OpenAI 클라이언트가 없는 경우 시뮬레이션 모드
        if client is None:
            return self._simulate_grading(question, answer, level, start_time)
        
        # 채점 프롬프트 구성
        system_prompt = """당신은 AI 활용능력평가 전문 채점관입니다.
        주어진 답변을 평가하고 점수와 피드백을 제공해주세요.
        평가는 공정하고 객관적이어야 하며, 구체적인 개선점을 제시해야 합니다."""
        
        criteria = self.grading_criteria.get(level, self.grading_criteria["basic"])
        
        user_prompt = f"""
문제: {question['question']}

학생 답변: {answer}

평가 기준:
{json.dumps(criteria, indent=2)}

다음 형식으로 채점해주세요:
{{
    "total_score": 0-100 사이의 점수,
    "criteria_scores": {{각 기준별 점수}},
    "passed": true/false (60점 이상이면 true),
    "strengths": ["강점1", "강점2"],
    "improvements": ["개선점1", "개선점2"],
    "feedback": "종합 피드백"
}}
"""
        
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            # 응답 파싱
            content = response.choices[0].message.content
            
            # 토큰 사용량 계산
            tokens_used = response.usage.total_tokens
            
            # 시간 계산
            time_taken = int(time.time() - start_time)
            
            # JSON 파싱
            try:
                result = json.loads(content)
            except:
                # 파싱 실패 시 기본 구조
                result = {
                    "total_score": 0,
                    "passed": False,
                    "feedback": content
                }
            
            result["time_taken"] = time_taken
            result["tokens_used"] = tokens_used
            
            return result
            
        except Exception as e:
            return {
                "total_score": 0,
                "passed": False,
                "feedback": f"채점 중 오류 발생: {str(e)}",
                "time_taken": int(time.time() - start_time),
                "tokens_used": 0
            }
    
    def _simulate_grading(self, question: Dict, answer: str, level: str, start_time: float) -> Dict:
        """OpenAI API 없이 시뮬레이션 채점"""
        time_taken = int(time.time() - start_time)
        
        # 답변 길이와 내용에 따른 간단한 점수 계산
        answer_length = len(answer.strip())
        base_score = min(100, max(0, answer_length * 2))  # 길이에 따른 기본 점수
        
        # 난이도별 조정
        difficulty_multiplier = {"basic": 1.2, "intermediate": 1.0, "advanced": 0.8}
        adjusted_score = base_score * difficulty_multiplier.get(level, 1.0)
        
        # 랜덤 요소 추가 (실제 AI 채점 시뮬레이션)
        final_score = min(100, max(0, adjusted_score + random.randint(-20, 20)))
        
        passed = final_score >= 60
        
        feedback = f"""
시뮬레이션 모드에서 채점되었습니다.

점수: {final_score:.1f}점
결과: {'통과' if passed else '실패'}

답변 길이: {answer_length}자
소요 시간: {time_taken}초

실제 AI 채점을 위해서는 OpenAI API 키를 설정해주세요.
"""
        
        return {
            "total_score": final_score,
            "criteria_scores": {"accuracy": final_score * 0.6, "completeness": final_score * 0.3, "clarity": final_score * 0.1},
            "passed": passed,
            "strengths": ["답변을 제출했습니다", "문제에 대한 시도를 했습니다"] if answer_length > 10 else [],
            "improvements": ["더 구체적인 답변을 작성해보세요", "실제 사례를 포함해보세요"] if not passed else [],
            "feedback": feedback,
            "time_taken": time_taken,
            "tokens_used": 0
        }

class GameEngine:
    """게임 엔진 - 레벨, 경험치, 승급 관리"""
    
    def __init__(self, db: GameDatabase):
        self.db = db
        self.xp_rewards = {
            "correct_answer": 50,
            "perfect_score": 100,
            "fast_completion": 30,
            "efficient_tokens": 20,
            "level_up_bonus": 500
        }
    
    def calculate_xp_reward(self, score: float, time_taken: int, tokens_used: int, difficulty: str) -> int:
        """경험치 계산"""
        base_xp = self.xp_rewards["correct_answer"] if score >= 60 else 10
        
        # 난이도 보너스
        difficulty_multiplier = {
            "basic": 1.0,
            "intermediate": 1.5,
            "advanced": 2.0
        }
        
        xp = int(base_xp * difficulty_multiplier.get(difficulty, 1.0))
        
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
        conn = sqlite3.connect(self.db.db_path)
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
        # 레벨별 문제 구성
        exam_config = {
            2: {"basic": 3, "intermediate": 2},
            3: {"basic": 2, "intermediate": 3, "advanced": 1},
            4: {"intermediate": 3, "advanced": 3},
            5: {"intermediate": 2, "advanced": 4, "previous_levels": True}
        }
        
        config = exam_config.get(target_level, {"basic": 5})
        exam_questions = []
        
        # 문제 생성
        for difficulty, count in config.items():
            if difficulty == "previous_levels":
                continue
                
            for _ in range(count):
                # 여기서는 간단한 예시 문제 생성
                question = {
                    "id": f"EXAM_{target_level}_{len(exam_questions)+1}",
                    "difficulty": difficulty,
                    "question": f"레벨 {target_level} 승급을 위한 {difficulty} 문제",
                    "type": "exam"
                }
                exam_questions.append(question)
        
        # 레벨 4, 5의 경우 이전 단계 문제 포함
        if target_level >= 4:
            # 각 이전 레벨에서 1문제씩
            for level in range(1, target_level):
                question = {
                    "id": f"EXAM_{target_level}_PREV_{level}",
                    "difficulty": "review",
                    "question": f"레벨 {level} 복습 문제",
                    "type": "exam"
                }
                exam_questions.append(question)
        
        return exam_questions

class AIAssessmentGame:
    """메인 게임 애플리케이션"""
    
    def __init__(self):
        self.db = GameDatabase()
        self.profile_gen = ProfileGenerator()
        self.grader = AutoGrader()
        self.game_engine = GameEngine(self.db)
    
    def create_user(self, username: str, email: str = None) -> str:
        """새 사용자 생성"""
        try:
            user_id = hashlib.md5(username.encode()).hexdigest()[:10]
            
            conn = sqlite3.connect(self.db.db_path)
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
            conn = sqlite3.connect(self.db.db_path)
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
    
    def submit_answer(self, user_id: str, question: Dict, answer: str) -> Dict:
        """답변 제출 및 처리"""
        # 자동 채점
        grade_result = self.grader.grade_answer(question, answer, question['difficulty'])
        
        # 경험치 계산
        xp_earned = self.game_engine.calculate_xp_reward(
            grade_result['total_score'],
            grade_result['time_taken'],
            grade_result['tokens_used'],
            question['difficulty']
        )
        
        # DB 업데이트
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        # 시도 기록 저장
        cursor.execute('''
            INSERT INTO attempt_history 
            (user_id, question_id, level, passed, score, time_taken, tokens_used, feedback)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            question['id'],
            question.get('level', 1),
            grade_result['passed'],
            grade_result['total_score'],
            grade_result['time_taken'],
            grade_result['tokens_used'],
            json.dumps(grade_result)
        ))
        
        # 사용자 통계 업데이트
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
        
        # 레벨업 체크
        level_up, new_level = self.game_engine.check_level_up(user_id)
        
        conn.close()
        
        return {
            "passed": grade_result['passed'],
            "score": grade_result['total_score'],
            "xp_earned": xp_earned,
            "feedback": grade_result['feedback'],
            "level_up": level_up,
            "new_level": new_level,
            "time_taken": grade_result['time_taken'],
            "tokens_used": grade_result['tokens_used']
        }
    
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

# Streamlit UI
def main():
    st.set_page_config(
        page_title="AI Master Quest - AI 활용능력평가 게임",
        page_icon="🎮",
        layout="wide"
    )
    
    # CSS 스타일
    st.markdown("""
    <style>
    .stProgress > div > div > div > div {
        background-image: linear-gradient(to right, #4CAF50, #45a049);
    }
    .achievement-badge {
        display: inline-block;
        padding: 5px 10px;
        margin: 2px;
        border-radius: 15px;
        background-color: #f0f0f0;
        font-size: 14px;
    }
    .level-badge {
        font-size: 24px;
        font-weight: bold;
        color: #4CAF50;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 세션 초기화
    if 'game' not in st.session_state:
        st.session_state.game = AIAssessmentGame()
    
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    
    # 사이드바 - 사용자 프로필
    with st.sidebar:
        st.header("👤 사용자 프로필")
        
        if st.session_state.user_id:
            profile = st.session_state.game.get_user_profile(st.session_state.user_id)
            
            if profile:
                # 프로필 이미지
                st.markdown(f'<img src="{profile["profile_image"]}" width="150">', unsafe_allow_html=True)
                
                # 사용자 정보
                st.markdown(f"### {profile['username']}")
                st.markdown(f"**레벨 {profile['level']}** {profile['level_icon']} {profile['level_name']}")
                
                # 경험치 바
                xp_progress = (profile['xp'] / profile['next_level_xp']) * 100
                st.progress(xp_progress / 100)
                st.caption(f"XP: {profile['xp']} / {profile['next_level_xp']}")
                
                # 통계
                col1, col2 = st.columns(2)
                with col1:
                    accuracy = profile['accuracy'] if profile['accuracy'] is not None else 0.0
                    st.metric("정답률", f"{accuracy:.1f}%")
                    st.metric("현재 연속", profile['current_streak'])
                
                with col2:
                    st.metric("총 문제", profile['total_questions'])
                    st.metric("최고 연속", profile['best_streak'])
                
                # 업적
                if profile['achievements']:
                    st.markdown("### 🏆 업적")
                    for ach in profile['achievements']:
                        st.markdown(f"{ach[3]} **{ach[1]}**")
                
                # 로그아웃
                if st.button("로그아웃"):
                    st.session_state.user_id = None
                    safe_rerun()
        
        else:
            # 로그인/회원가입
            tab1, tab2 = st.tabs(["로그인", "회원가입"])
            
            with tab1:
                username = st.text_input("사용자명", key="login_username")
                if st.button("로그인", type="primary"):
                    # 간단한 로그인 (실제로는 인증 필요)
                    conn = sqlite3.connect(st.session_state.game.db.db_path)
                    cursor = conn.cursor()
                    cursor.execute("SELECT user_id FROM users WHERE username = ?", (username,))
                    user = cursor.fetchone()
                    conn.close()
                    
                    if user:
                        st.session_state.user_id = user[0]
                        st.success("로그인 성공!")
                        safe_rerun()
                    else:
                        st.error("사용자를 찾을 수 없습니다.")
            
            with tab2:
                new_username = st.text_input("사용자명", key="signup_username")
                email = st.text_input("이메일 (선택사항)")
                
                if st.button("가입하기", type="primary"):
                    user_id = st.session_state.game.create_user(new_username, email)
                    if user_id:
                        st.session_state.user_id = user_id
                        st.success("회원가입 성공! 🎉")
                        st.balloons()
                        safe_rerun()
                    else:
                        st.error("이미 존재하는 사용자명입니다.")
    
    # 메인 화면
    if not st.session_state.user_id:
        st.title("🎮 AI Master Quest")
        st.markdown("### AI 마스터가 되는 여정에 오신 것을 환영합니다!")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.info("""
            **🎯 도전하세요**
            
            AI 활용 능력을 테스트하는
            다양한 레벨의 문제들
            """)
        
        with col2:
            st.success("""
            **📈 성장하세요**
            
            경험치를 쌓고 레벨업하며
            AI 전문가로 성장
            """)
        
        with col3:
            st.warning("""
            **🏆 달성하세요**
            
            업적을 달성하고
            리더보드에 도전
            """)
        
        st.markdown("---")
        st.markdown("👈 왼쪽 사이드바에서 로그인하거나 회원가입하여 시작하세요!")
    
    else:
        # 로그인된 사용자 화면
        profile = st.session_state.game.get_user_profile(st.session_state.user_id)
        
        # 메인 타이틀
        st.title(f"🎮 AI Master Quest - {profile['username']}님의 여정")
        
        # 탭 구성
        tab1, tab2, tab3, tab4 = st.tabs(["🎯 도전하기", "📊 승급 시험", "🏆 리더보드", "📈 통계"])
        
        with tab1:
            st.header("문제 도전하기")
            
            # 레벨에 따른 접근 가능 난이도
            available_difficulties = []
            if profile['level'] >= 1:
                available_difficulties.append("basic")
            if profile['level'] >= 2:
                available_difficulties.append("intermediate")
            if profile['level'] >= 3:
                available_difficulties.append("advanced")
            
            col1, col2 = st.columns([1, 2])
            
            with col1:
                difficulty = st.selectbox(
                    "난이도 선택",
                    available_difficulties,
                    format_func=lambda x: {"basic": "초급", "intermediate": "중급", "advanced": "고급"}[x]
                )
                
                if st.button("🎲 문제 받기", type="primary", use_container_width=True):
                    # 문제 생성 (여기서는 간단한 예시)
                    st.session_state.current_question = {
                        "id": f"Q_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                        "difficulty": difficulty,
                        "question": f"{difficulty} 레벨의 AI 활용 문제입니다. AI를 활용하여 다음 과제를 해결하세요...",
                        "level": profile['level']
                    }
            
            with col2:
                if 'current_question' in st.session_state:
                    question = st.session_state.current_question
                    
                    st.info(f"문제 난이도: {question['difficulty']}")
                    st.markdown(f"### 문제")
                    st.markdown(question['question'])
                    
                    # 답변 입력
                    answer = st.text_area("답변을 입력하세요", height=200)
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if st.button("💡 힌트 (XP -10)", disabled=profile['level'] < 2):
                            st.info("힌트: AI 도구의 특성을 고려하여 접근하세요.")
                    
                    with col2:
                        if st.button("📝 제출하기", type="primary"):
                            if answer:
                                with st.spinner("채점 중..."):
                                    result = st.session_state.game.submit_answer(
                                        st.session_state.user_id,
                                        question,
                                        answer
                                    )
                                
                                # 결과 표시
                                if result['passed']:
                                    st.success(f"🎉 정답! 점수: {result['score']:.1f}점")
                                    st.success(f"획득 경험치: +{result['xp_earned']} XP")
                                else:
                                    st.error(f"아쉽네요. 점수: {result['score']:.1f}점")
                                
                                # 피드백
                                with st.expander("상세 피드백"):
                                    st.markdown(result['feedback'])
                                
                                # 레벨업 체크
                                if result['level_up']:
                                    st.balloons()
                                    st.success(f"🎊 레벨업! 레벨 {result['new_level']}에 도달했습니다!")
                                
                                # 효율성 표시
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.metric("소요 시간", f"{result['time_taken']}초")
                                with col2:
                                    st.metric("토큰 사용량", result['tokens_used'])
                            else:
                                st.warning("답변을 입력해주세요.")
                    
                    with col3:
                        if st.button("🔄 다른 문제"):
                            del st.session_state.current_question
                            safe_rerun()
        
        with tab2:
            st.header("📊 승급 시험")
            
            # 레벨업 가능 여부 체크
            can_level_up, next_level = st.session_state.game.game_engine.check_level_up(st.session_state.user_id)
            
            if can_level_up:
                st.success(f"레벨 {next_level} 승급 시험에 도전할 수 있습니다!")
                
                if st.button("🎯 승급 시험 시작", type="primary"):
                    # 승급 시험 문제 생성
                    exam_questions = st.session_state.game.game_engine.generate_promotion_exam(
                        st.session_state.user_id,
                        next_level
                    )
                    
                    st.session_state.promotion_exam = {
                        "questions": exam_questions,
                        "current": 0,
                        "results": []
                    }
                
                # 승급 시험 진행
                if 'promotion_exam' in st.session_state:
                    exam = st.session_state.promotion_exam
                    
                    if exam['current'] < len(exam['questions']):
                        # 현재 문제 표시
                        current_q = exam['questions'][exam['current']]
                        
                        st.info(f"문제 {exam['current']+1} / {len(exam['questions'])}")
                        st.markdown(f"### {current_q['question']}")
                        
                        answer = st.text_area("답변", key=f"exam_answer_{exam['current']}")
                        
                        if st.button("다음 문제 →"):
                            # 답변 처리 (간단한 시뮬레이션)
                            exam['results'].append({
                                "question_id": current_q['id'],
                                "passed": random.random() > 0.3
                            })
                            exam['current'] += 1
                            safe_rerun()
                    
                    else:
                        # 시험 완료
                        passed_count = sum(1 for r in exam['results'] if r['passed'])
                        total_count = len(exam['results'])
                        pass_rate = passed_count / total_count
                        
                        if pass_rate >= 0.8:  # 80% 이상 정답
                            st.success(f"🎊 축하합니다! 레벨 {next_level}로 승급했습니다!")
                            st.balloons()
                            
                            # DB 업데이트
                            conn = sqlite3.connect(st.session_state.game.db.db_path)
                            cursor = conn.cursor()
                            cursor.execute('''
                                UPDATE users SET level = ? WHERE user_id = ?
                            ''', (next_level, st.session_state.user_id))
                            conn.commit()
                            conn.close()
                            
                            del st.session_state.promotion_exam
                        else:
                            st.error(f"아쉽네요. {pass_rate*100:.0f}% 정답률로 승급에 실패했습니다.")
                            st.info("더 많은 문제를 풀고 다시 도전하세요!")
                            del st.session_state.promotion_exam
            
            else:
                st.info("승급 시험을 보려면 다음 조건을 충족해야 합니다:")
                
                # 다음 레벨 요구사항 표시
                conn = sqlite3.connect(st.session_state.game.db.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT required_xp, min_accuracy, required_questions
                    FROM level_requirements
                    WHERE level = ?
                ''', (profile['level'] + 1,))
                
                req = cursor.fetchone()
                conn.close()
                
                if req:
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        current_xp = profile['xp']
                        required_xp = req[0]
                        st.metric(
                            "경험치",
                            f"{current_xp} / {required_xp}",
                            f"{required_xp - current_xp} 필요"
                        )
                    
                    with col2:
                        current_acc = profile['accuracy'] if profile['accuracy'] is not None else 0.0
                        required_acc = req[1]
                        st.metric(
                            "정답률",
                            f"{current_acc:.1f}% / {required_acc}%",
                            f"{required_acc - current_acc:.1f}% 필요" if current_acc < required_acc else "달성!"
                        )
                    
                    with col3:
                        current_q = profile['total_questions']
                        required_q = req[2]
                        st.metric(
                            "문제 수",
                            f"{current_q} / {required_q}",
                            f"{required_q - current_q} 필요" if current_q < required_q else "달성!"
                        )
        
        with tab3:
            st.header("🏆 리더보드")
            
            # 리더보드 조회
            conn = sqlite3.connect(st.session_state.game.db.db_path)
            leaderboard = pd.read_sql_query('''
                SELECT * FROM leaderboard LIMIT 10
            ''', conn)
            conn.close()
            
            if not leaderboard.empty:
                # 리더보드 표시
                for idx, row in leaderboard.iterrows():
                    rank = idx + 1
                    medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(rank, "")
                    
                    col1, col2, col3, col4, col5 = st.columns([1, 3, 2, 2, 2])
                    
                    with col1:
                        st.markdown(f"### {medal} {rank}")
                    
                    with col2:
                        st.markdown(f"**{row['username']}**")
                        st.caption(f"레벨 {row['level']}")
                    
                    with col3:
                        st.metric("XP", f"{row['experience_points']:,}")
                    
                    with col4:
                        accuracy = row['accuracy'] if row['accuracy'] is not None else 0.0
                        st.metric("정답률", f"{accuracy:.1f}%")
                    
                    with col5:
                        st.metric("최고 연속", row['best_streak'])
                    
                    if row['username'] == profile['username']:
                        st.markdown("---")
                        st.success("👆 내 순위")
                        st.markdown("---")
        
        with tab4:
            st.header("📈 내 통계")
            
            # 상세 통계 조회
            conn = sqlite3.connect(st.session_state.game.db.db_path)
            
            # 시간별 활동
            activity = pd.read_sql_query('''
                SELECT 
                    DATE(attempt_date) as date,
                    COUNT(*) as attempts,
                    SUM(passed) as correct,
                    AVG(score) as avg_score
                FROM attempt_history
                WHERE user_id = ?
                GROUP BY DATE(attempt_date)
                ORDER BY date DESC
                LIMIT 30
            ''', conn, params=[st.session_state.user_id])
            
            if not activity.empty:
                # 활동 그래프
                fig = px.line(
                    activity,
                    x='date',
                    y='attempts',
                    title='일별 문제 풀이 활동',
                    markers=True
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # 점수 추이
                fig2 = px.line(
                    activity,
                    x='date',
                    y='avg_score',
                    title='평균 점수 추이',
                    markers=True
                )
                st.plotly_chart(fig2, use_container_width=True)
            
            # 난이도별 성과
            difficulty_stats = pd.read_sql_query('''
                SELECT 
                    CASE 
                        WHEN level <= 2 THEN 'basic'
                        WHEN level <= 3 THEN 'intermediate'
                        ELSE 'advanced'
                    END as difficulty,
                    COUNT(*) as total,
                    SUM(passed) as passed,
                    AVG(score) as avg_score
                FROM attempt_history
                WHERE user_id = ?
                GROUP BY difficulty
            ''', conn, params=[st.session_state.user_id])
            
            if not difficulty_stats.empty:
                col1, col2 = st.columns(2)
                
                with col1:
                    # 난이도별 정답률
                    difficulty_stats['pass_rate'] = difficulty_stats['passed'] / difficulty_stats['total'] * 100
                    fig3 = px.bar(
                        difficulty_stats,
                        x='difficulty',
                        y='pass_rate',
                        title='난이도별 정답률'
                    )
                    st.plotly_chart(fig3, use_container_width=True)
                
                with col2:
                    # 난이도별 평균 점수
                    fig4 = px.bar(
                        difficulty_stats,
                        x='difficulty',
                        y='avg_score',
                        title='난이도별 평균 점수'
                    )
                    st.plotly_chart(fig4, use_container_width=True)
            
            conn.close()

if __name__ == "__main__":
    main()
