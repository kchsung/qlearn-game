# game_engine.py
"""
게임 엔진 및 로직 관련 클래스들 (Supabase 기반)
"""

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
        
        # 시간 보너스 (빠른 답변)
        if time_taken < 30:  # 30초 이내
            xp = int(xp * 1.2)
        elif time_taken < 60:  # 1분 이내
            xp = int(xp * 1.1)
        
        # 토큰 효율성 보너스
        if tokens_used < 100:  # 토큰 절약
            xp = int(xp * 1.1)
        
        return max(xp, 1)  # 최소 1 XP
    
    def calculate_simple_xp_reward(self, is_correct: bool, difficulty: str) -> int:
        """단순 정답/오답에 대한 경험치 계산"""
        if not is_correct:
            return 0  # 오답은 경험치 없음
        
        # 정답일 때 기본 경험치
        base_xp = self.xp_rewards["correct_answer"]
        
        # 난이도 보너스
        xp = int(base_xp * DIFFICULTY_MULTIPLIER.get(difficulty, 1.0))
        
        return max(xp, 1)  # 최소 1 XP
    
    def award_experience(self, user_id: str, xp: int) -> bool:
        """경험치 지급"""
        return self.db.add_experience(user_id, xp)
    
    def check_promotion_eligibility(self, user_id: str) -> Tuple[bool, Dict]:
        """승급 시험 자격 확인"""
        profile = self.db.get_user_profile(user_id)
        if not profile:
            return False, {}
        
        current_level = profile.get('level', 1)
        current_xp = profile.get('experience_points', 0)
        
        # 다음 레벨 요구사항 확인
        next_level = current_level + 1
        
        # 레벨별 승급 조건
        if current_level == 1:
            # 레벨 1 → 2: 최소 50 XP 필요
            required_xp = 50
        elif current_level == 2:
            # 레벨 2 → 3: 최소 150 XP 필요
            required_xp = 150
        elif current_level == 3:
            # 레벨 3 → 4: 최소 300 XP 필요
            required_xp = 300
        else:
            # 레벨 4 이상: 현재 레벨 * 100 XP 필요
            required_xp = current_level * 100
        
        can_promote = current_xp >= required_xp
        
        return can_promote, {
            'current_level': current_level,
            'current_xp': current_xp,
            'required_xp': required_xp,
            'next_level': next_level,
            'can_promote': can_promote
        }
    
    def conduct_promotion_exam(self, user_id: str) -> Dict:
        """승급 시험 진행"""
        profile = self.db.get_user_profile(user_id)
        if not profile:
            return {'success': False, 'message': '사용자 정보를 찾을 수 없습니다.'}
        
        current_level = profile.get('level', 1)
        next_level = current_level + 1
        
        # 승급 시험 설정
        exam_config = PROMOTION_EXAM_CONFIG.get(next_level, {
            'questions': 5,
            'passing_score': 80,
            'time_limit': 300,
            'difficulty_distribution': {'basic': 3, 'intermediate': 2}
        })
        
        return {
            'success': True,
            'exam_config': exam_config,
            'current_level': current_level,
            'next_level': next_level
        }
    
    def process_promotion_result(self, user_id: str, score: float, time_taken: int) -> Dict:
        """승급 시험 결과 처리"""
        profile = self.db.get_user_profile(user_id)
        if not profile:
            return {'success': False, 'message': '사용자 정보를 찾을 수 없습니다.'}
        
        current_level = profile.get('level', 1)
        next_level = current_level + 1
        
        # 승급 시험 통과 조건: pass_fail이 "PASS"이고 score가 100 이상
        # 이 조건은 이미 promotion_page.py에서 확인되므로 여기서는 항상 통과로 처리
        if True:  # 승급 시험 통과 조건은 이미 확인됨
            # 승급 성공 - 실제 레벨 업데이트
            xp_reward = self.calculate_xp_reward(score, time_taken, 0, 'hard')
            
            # 레벨 업데이트
            level_update_success = self.db.update_user_profile(user_id, {'level': next_level})
            
            # 경험치 지급
            xp_success = self.award_experience(user_id, xp_reward)
            
            if level_update_success and xp_success:
                return {
                    'success': True,
                    'promoted': True,
                    'new_level': next_level,
                    'xp_reward': xp_reward,
                    'message': f'축하합니다! 레벨 {next_level}로 승급했습니다!'
                }
            else:
                return {
                    'success': False,
                    'promoted': False,
                    'message': '승급 처리 중 오류가 발생했습니다.'
                }
        else:
            # 승급 실패
            return {
                'success': True,
                'promoted': False,
                'current_level': current_level,
                'message': f'아쉽게도 승급에 실패했습니다. {exam_config["passing_score"]}% 이상이 필요합니다.'
            }


class UserManager:
    """사용자 관리 클래스 (Supabase 기반)"""
    
    def __init__(self, db: GameDatabase):
        self.db = db
        self.profile_gen = ProfileGenerator()
    
    def create_user(self, username: str, email: str) -> Optional[str]:
        """새 사용자 생성"""
        try:
            user_id = hashlib.md5(username.encode()).hexdigest()[:10]
            
            # 프로필 이미지 생성
            profile_image = self.profile_gen.generate_profile_image(username, 1)
            
            # Supabase DB에 사용자 생성
            success = self.db.create_user_profile(user_id, username, email, profile_image)
            
            if success:
                return user_id
            else:
                st.error("사용자 생성 실패")
                return None
                
        except Exception as e:
            st.error(f"사용자 생성 중 오류: {str(e)}")
            return None
    
    def get_user_profile(self, user_id: str) -> Optional[Dict]:
        """사용자 프로필 조회 (UI용 필드 추가)"""
        try:
            # 테스트 사용자인 경우 가상 프로필 반환
            if user_id == "test_user_001":
                return self._get_test_user_profile()
            
            profile = self.db.get_user_profile(user_id)
            if not profile:
                return None
            
            # UI에서 필요한 필드들 추가
            level = profile.get('level', 1)
            current_xp = profile.get('experience_points', 0)
            
            # 레벨 정보 추가
            level_info = self._get_level_info(level)
            profile.update({
                'level_icon': level_info['icon'],
                'level_name': level_info['name'],
                'xp': current_xp,
                'next_level_xp': level_info['next_requirement'],
                'accuracy': self._calculate_accuracy(profile),
                'total_questions': profile.get('total_questions_solved', 0),
                'achievements': self.get_user_achievements(user_id)
            })
            
            return profile
        except Exception as e:
            st.error(f"사용자 프로필 조회 중 오류: {str(e)}")
            return None
    
    def _get_test_user_profile(self) -> Dict:
        """테스트 사용자용 가상 프로필 생성"""
        # 세션에서 테스트 사용자 통계 가져오기
        test_stats = st.session_state.get('test_user_stats', {
            'total_questions_solved': 0,
            'correct_answers': 0,
            'current_streak': 0,
            'best_streak': 0,
            'experience_points': 0,
            'level': 1
        })
        
        # 정답률 계산
        accuracy = 0.0
        if test_stats['total_questions_solved'] > 0:
            accuracy = (test_stats['correct_answers'] / test_stats['total_questions_solved']) * 100
        
        # 다음 레벨 XP 계산
        next_level_xp = test_stats['level'] * 100
        
        return {
            'user_id': 'test_user_001',
            'username': '테스터',
            'email': 'test@example.com',
            'level': test_stats['level'],
            'experience_points': test_stats['experience_points'],
            'total_questions_solved': test_stats['total_questions_solved'],
            'correct_answers': test_stats['correct_answers'],
            'current_streak': test_stats['current_streak'],
            'best_streak': test_stats['best_streak'],
            'level_icon': '🧪',
            'level_name': '테스터',
            'xp': test_stats['experience_points'],
            'next_level_xp': next_level_xp,
            'accuracy': accuracy,
            'achievements': [
                {
                    'id': 'test_achievement',
                    'name': '테스트 모드',
                    'description': '테스트 모드로 게임을 체험해보세요!',
                    'icon': '🧪'
                }
            ]
        }
    
    def _update_test_user_stats(self, is_correct: bool, xp_earned: int = 0) -> bool:
        """테스트 사용자 통계 업데이트 (세션에서만 관리)"""
        try:
            # 세션에서 테스트 사용자 통계 가져오기
            test_stats = st.session_state.get('test_user_stats', {
                'total_questions_solved': 0,
                'correct_answers': 0,
                'current_streak': 0,
                'best_streak': 0,
                'experience_points': 0,
                'level': 1
            })
            
            # 통계 업데이트
            test_stats['total_questions_solved'] += 1
            if is_correct:
                test_stats['correct_answers'] += 1
                test_stats['current_streak'] += 1
                test_stats['best_streak'] = max(test_stats['best_streak'], test_stats['current_streak'])
            else:
                test_stats['current_streak'] = 0
            
            # 경험치 추가
            if xp_earned > 0:
                test_stats['experience_points'] += xp_earned
                # 레벨 업 계산 (간단한 로직)
                new_level = (test_stats['experience_points'] // 100) + 1
                test_stats['level'] = new_level
            
            # 세션에 저장
            st.session_state['test_user_stats'] = test_stats
            
            st.write(f"🔍 테스트 사용자 통계 업데이트: {test_stats}")
            return True
        except Exception as e:
            st.error(f"테스트 사용자 통계 업데이트 중 오류: {str(e)}")
            return False
    
    def _get_level_info(self, level: int) -> Dict:
        """레벨 정보 조회 (DB에서)"""
        try:
            # DB에서 레벨 정보 조회
            level_info = self.db._get_level_info(level)
            
            # 다음 레벨 요구사항 계산
            next_level = level + 1
            next_requirement = next_level * 100  # 간단한 계산
            
            return {
                'name': level_info['name'],
                'icon': level_info['icon'],
                'next_requirement': next_requirement
            }
        except Exception as e:
            st.error(f"레벨 정보 조회 오류: {str(e)}")
            # 기본값 반환
            return {
                'name': '초보자',
                'icon': '🌱',
                'next_requirement': 100
            }
    
    def _calculate_accuracy(self, profile: Dict) -> float:
        """정답률 계산"""
        total_questions = profile.get('total_questions_solved', 0)
        correct_answers = profile.get('correct_answers', 0)
        
        if total_questions == 0:
            return 0.0
        
        return (correct_answers / total_questions) * 100
    
    def get_user_achievements(self, user_id: str) -> List[Dict]:
        """사용자 업적 조회"""
        try:
            profile = self.db.get_user_profile(user_id)
            if not profile:
                return []
            
            level = profile.get('level', 1)
            total_questions = profile.get('total_questions_solved', 0)
            correct_answers = profile.get('correct_answers', 0)
            best_streak = profile.get('best_streak', 0)
            
            unlocked_achievements = []
            
            # 업적 확인 로직
            if total_questions >= 1:
                unlocked_achievements.append({
                    'achievement_id': 'first_question',
                    'name': '첫 번째 문제',
                    'description': '첫 번째 문제를 해결했습니다!',
                    'icon': '🎯'
                })
            
            if level >= 5:
                unlocked_achievements.append({
                    'achievement_id': 'level_5',
                    'name': '레벨 5 달성',
                    'description': '레벨 5에 도달했습니다!',
                    'icon': '⭐'
                })
            
            if level >= 10:
                unlocked_achievements.append({
                    'achievement_id': 'level_10',
                    'name': '레벨 10 달성',
                    'description': '레벨 10에 도달했습니다!',
                    'icon': '🌟'
                })
            
            if best_streak >= 5:
                unlocked_achievements.append({
                    'achievement_id': 'streak_5',
                    'name': '5연속 정답',
                    'description': '5문제 연속으로 정답을 맞췄습니다!',
                    'icon': '🔥'
                })
            
            if best_streak >= 10:
                unlocked_achievements.append({
                    'achievement_id': 'streak_10',
                    'name': '10연속 정답',
                    'description': '10문제 연속으로 정답을 맞췄습니다!',
                    'icon': '🚀'
                })
            
            if total_questions > 0 and (correct_answers / total_questions) >= 0.8:
                unlocked_achievements.append({
                    'achievement_id': 'accuracy_80',
                    'name': '80% 정확도',
                    'description': '80% 이상의 정확도를 달성했습니다!',
                    'icon': '🎯'
                })
            
            return unlocked_achievements
        except Exception as e:
            st.error(f"업적 조회 중 오류: {str(e)}")
            return []
    
    def update_user_stats(self, user_id: str, is_correct: bool, xp_earned: int = 0) -> bool:
        """사용자 통계 업데이트"""
        try:
            st.write(f"🔍 통계 업데이트 시작: user_id={user_id}, is_correct={is_correct}, xp_earned={xp_earned}")
            
            # 테스트 사용자인 경우 세션에서만 관리
            if user_id == "test_user_001":
                return self._update_test_user_stats(is_correct, xp_earned)
            
            # 답변 기록
            success = self.db.record_answer(user_id, is_correct)
            st.write(f"🔍 답변 기록 결과: {success}")
            
            # 경험치 지급
            if xp_earned > 0:
                xp_success = self.db.add_experience(user_id, xp_earned)
                st.write(f"🔍 경험치 지급 결과: {xp_success}")
                success = success and xp_success
            
            st.write(f"🔍 통계 업데이트 최종 결과: {success}")
            return success
        except Exception as e:
            st.error(f"사용자 통계 업데이트 중 오류: {str(e)}")
            return False
    
    def get_user_stats(self, user_id: str) -> Dict:
        """사용자 통계 조회"""
        try:
            return self.db.get_user_stats(user_id)
        except Exception as e:
            st.error(f"사용자 통계 조회 중 오류: {str(e)}")
            return {}
    
    def get_level_progress(self, user_id: str) -> Dict:
        """레벨 진행률 조회"""
        try:
            return self.db.get_level_progress(user_id)
        except Exception as e:
            st.error(f"레벨 진행률 조회 중 오류: {str(e)}")
            return {}
    
    def update_profile_prompt(self, user_id: str, prompt: str) -> bool:
        """프로필 프롬프트 업데이트"""
        try:
            return self.db.update_profile_prompt(user_id, prompt)
        except Exception as e:
            st.error(f"프로필 프롬프트 업데이트 중 오류: {str(e)}")
            return False
    
    def get_profile_prompt(self, user_id: str) -> Optional[str]:
        """프로필 프롬프트 조회"""
        try:
            return self.db.get_profile_prompt(user_id)
        except Exception as e:
            st.error(f"프로필 프롬프트 조회 중 오류: {str(e)}")
            return None