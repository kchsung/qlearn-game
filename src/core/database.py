# database.py
"""
Supabase 데이터베이스 관련 클래스 및 함수
"""

import streamlit as st
from typing import Dict, List, Optional, Any
from src.core.config import LEVEL_REQUIREMENTS, ACHIEVEMENTS, SUPABASE_URL, SUPABASE_ANON_KEY
from src.auth.supabase_auth import _get_supabase


class GameDatabase:
    """Supabase 기반 게임화된 평가 시스템 데이터베이스"""
    
    def __init__(self):
        self.supabase = _get_supabase(SUPABASE_URL, SUPABASE_ANON_KEY)
        if not self.supabase:
            st.error("Supabase 클라이언트를 초기화할 수 없습니다.")
    
    def init_database(self):
        """Supabase 테이블 초기화 (필요시)"""
        try:
            # Supabase에서는 테이블이 이미 존재한다고 가정
            # 필요시 여기서 테이블 생성 로직 추가
            return True
        except Exception as e:
            st.error(f"Supabase 데이터베이스 초기화 오류: {str(e)}")
            return False
    
    def create_user_profile(self, user_id: str, username: str, email: str, profile_image: str = "") -> bool:
        """사용자 프로필 생성"""
        try:
            result = self.supabase.table('users').insert({
                'user_id': user_id,
                'username': username,
                'email': email,
                'level': 1,
                'experience_points': 0,
                'total_questions_solved': 0,
                'correct_answers': 0,
                'current_streak': 0,
                'best_streak': 0,
                'profile_image': profile_image,
                'created_at': 'now()',
                'last_active': 'now()'
            }).execute()
            
            return len(result.data) > 0
        except Exception as e:
            st.error(f"사용자 프로필 생성 오류: {str(e)}")
            return False
    
    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """사용자 프로필 조회 (레벨 아이콘 포함)"""
        try:
            result = self.supabase.table('users').select('*').eq('user_id', user_id).execute()
            
            if result.data:
                profile = result.data[0]
                
                # 레벨 아이콘과 이름이 없으면 level_requirements에서 가져오기
                if not profile.get('level_icon') or not profile.get('level_name'):
                    level = profile.get('level', 1)
                    level_info = self._get_level_info(level)
                    profile['level_icon'] = level_info['icon']
                    profile['level_name'] = level_info['name']
                
                return profile
            return None
        except Exception as e:
            st.error(f"사용자 프로필 조회 오류: {str(e)}")
            return None
    
    def _get_level_info(self, level: int) -> Dict[str, str]:
        """레벨 정보 조회"""
        try:
            result = self.supabase.table('level_requirements').select('icon, title').eq('level', level).execute()
            
            if result.data:
                level_data = result.data[0]
                return {
                    'icon': level_data.get('icon', '🌱'),
                    'name': level_data.get('title', '초보자')
                }
            else:
                # 기본값 반환
                return {'icon': '🌱', 'name': '초보자'}
        except Exception as e:
            st.error(f"레벨 정보 조회 오류: {str(e)}")
            return {'icon': '🌱', 'name': '초보자'}
    
    def update_user_profile(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """사용자 프로필 업데이트"""
        try:
            updates['last_active'] = 'now()'
            result = self.supabase.table('users').update(updates).eq('user_id', user_id).execute()
            
            return len(result.data) > 0
        except Exception as e:
            st.error(f"사용자 프로필 업데이트 오류: {str(e)}")
            return False
    
    def add_experience(self, user_id: str, xp: int) -> bool:
        """경험치 추가"""
        try:
            # 현재 경험치 조회
            profile = self.get_user_profile(user_id)
            if not profile:
                return False
            
            current_xp = profile.get('experience_points', 0)
            new_xp = current_xp + xp
            
            # 레벨 계산
            new_level = self._calculate_level(new_xp)
            
            # 업데이트
            updates = {
                'experience_points': new_xp,
                'level': new_level
            }
            
            return self.update_user_profile(user_id, updates)
        except Exception as e:
            st.error(f"경험치 추가 오류: {str(e)}")
            return False
    
    def record_answer(self, user_id: str, is_correct: bool) -> bool:
        """답변 기록"""
        try:
            profile = self.get_user_profile(user_id)
            if not profile:
                return False
            
            # 현재 통계
            total_questions = profile.get('total_questions_solved', 0) + 1
            correct_answers = profile.get('correct_answers', 0)
            current_streak = profile.get('current_streak', 0)
            best_streak = profile.get('best_streak', 0)
            
            if is_correct:
                correct_answers += 1
                current_streak += 1
                best_streak = max(best_streak, current_streak)
            else:
                current_streak = 0
            
            # 업데이트
            updates = {
                'total_questions_solved': total_questions,
                'correct_answers': correct_answers,
                'current_streak': current_streak,
                'best_streak': best_streak
            }
            
            return self.update_user_profile(user_id, updates)
        except Exception as e:
            st.error(f"답변 기록 오류: {str(e)}")
            return False
    
    def get_leaderboard(self, limit: int = 10) -> List[Dict[str, Any]]:
        """리더보드 조회"""
        try:
            result = self.supabase.table('users').select(
                'user_id, username, level, experience_points, total_questions_solved, correct_answers, profile_image'
            ).order('experience_points', desc=True).limit(limit).execute()
            
            return result.data or []
        except Exception as e:
            st.error(f"리더보드 조회 오류: {str(e)}")
            return []
    
    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """사용자 통계 조회"""
        try:
            profile = self.get_user_profile(user_id)
            if not profile:
                return {}
            
            total_questions = profile.get('total_questions_solved', 0)
            correct_answers = profile.get('correct_answers', 0)
            accuracy = (correct_answers / total_questions * 100) if total_questions > 0 else 0
            
            return {
                'level': profile.get('level', 1),
                'experience_points': profile.get('experience_points', 0),
                'total_questions_solved': total_questions,
                'correct_answers': correct_answers,
                'accuracy': accuracy,
                'current_streak': profile.get('current_streak', 0),
                'best_streak': profile.get('best_streak', 0)
            }
        except Exception as e:
            st.error(f"사용자 통계 조회 오류: {str(e)}")
            return {}
    
    def _calculate_level(self, xp: int) -> int:
        """경험치로 레벨 계산"""
        for level_data in LEVEL_REQUIREMENTS:
            level, required_xp, _, _, _, _, _ = level_data
            if xp < required_xp:
                return level - 1
        return max([level_data[0] for level_data in LEVEL_REQUIREMENTS])
    
    def get_level_progress(self, user_id: str) -> Dict[str, Any]:
        """레벨 진행률 조회"""
        try:
            profile = self.get_user_profile(user_id)
            if not profile:
                return {}
            
            current_level = profile.get('level', 1)
            current_xp = profile.get('experience_points', 0)
            
            # LEVEL_REQUIREMENTS에서 현재 레벨 정보 찾기
            current_level_data = None
            next_level_data = None
            prev_level_data = None
            
            for level_data in LEVEL_REQUIREMENTS:
                level, required_xp, _, _, _, _, _ = level_data
                if level == current_level:
                    current_level_data = level_data
                elif level == current_level + 1:
                    next_level_data = level_data
                elif level == current_level - 1:
                    prev_level_data = level_data
            
            if not current_level_data:
                return {}
            
            current_requirement = current_level_data[1]  # required_xp
            next_requirement = next_level_data[1] if next_level_data else current_requirement
            prev_xp = prev_level_data[1] if prev_level_data else 0
            
            # 현재 레벨에서의 진행률
            level_xp = current_xp - prev_xp
            level_requirement = current_requirement - prev_xp
            
            progress_percentage = (level_xp / level_requirement * 100) if level_requirement > 0 else 100
            
            return {
                'current_level': current_level,
                'current_xp': current_xp,
                'level_xp': level_xp,
                'level_requirement': level_requirement,
                'progress_percentage': progress_percentage,
                'next_level_requirement': next_requirement
            }
        except Exception as e:
            st.error(f"레벨 진행률 조회 오류: {str(e)}")
            return {}
    
    def update_profile_prompt(self, user_id: str, prompt: str) -> bool:
        """프로필 프롬프트 업데이트"""
        try:
            updates = {'profile_prompt': prompt}
            return self.update_user_profile(user_id, updates)
        except Exception as e:
            st.error(f"프로필 프롬프트 업데이트 오류: {str(e)}")
            return False
    
    def get_profile_prompt(self, user_id: str) -> Optional[str]:
        """프로필 프롬프트 조회"""
        try:
            profile = self.get_user_profile(user_id)
            return profile.get('profile_prompt') if profile else None
        except Exception as e:
            st.error(f"프로필 프롬프트 조회 오류: {str(e)}")
            return None
    
    def get_prompt_by_id(self, prompt_id: str) -> Optional[str]:
        """ID로 프롬프트 조회"""
        try:
            result = self.supabase.table('prompts').select('prompt_text').eq('id', prompt_id).execute()
            
            if result.data and len(result.data) > 0:
                return result.data[0].get('prompt_text')
            return None
        except Exception as e:
            st.error(f"프롬프트 조회 오류: {str(e)}")
            return None
    
    def get_random_question(self, difficulty: str = '보통', area: str = 'ai') -> Optional[Dict[str, Any]]:
        """랜덤 문제 조회 (다양한 문제를 위해 랜덤 선택)"""
        try:
            st.info(f"🔍 문제 조회 중... 난이도: {difficulty}")
            
            # 먼저 해당 난이도의 모든 문제 확인
            all_questions = self.supabase.table('questions').select('*').eq('difficulty', difficulty).execute()
            st.info(f"📊 {difficulty} 난이도 전체 문제 수: {len(all_questions.data) if all_questions.data else 0}")
            
            if all_questions.data:
                # 랜덤하게 문제 선택 (다양한 문제를 위해)
                import random
                random_question = random.choice(all_questions.data)
                st.success(f"✅ 랜덤 문제 선택: {random_question.get('id', 'N/A')}")
                
                # steps 필드가 있는지 확인하고 파싱
                if random_question.get('steps'):
                    try:
                        if isinstance(random_question['steps'], str):
                            random_question['steps'] = json.loads(random_question['steps'])
                    except:
                        st.warning("⚠️ steps 필드 파싱 실패")
                
                return random_question
            else:
                st.error(f"❌ {difficulty} 난이도에 문제가 없습니다.")
                return None
                
        except Exception as e:
            st.error(f"문제 조회 오류: {str(e)}")
            return None
    
    def save_user_answer(self, user_id: str, question_id: str, user_answer: str, score: float, time_taken: int, tokens_used: int, pass_fail: str = None, detail: str = None) -> bool:
        """사용자 답변 저장"""
        try:
            data = {
                'user_id': user_id,
                'question_id': question_id,
                'answer': user_answer,  # user_answer -> answer로 변경
                'score': score,
                'time_taken': time_taken,
                'tokens_used': tokens_used
            }
            
            # result 필드에 pass_fail 값 저장 (enum 값 확인 필요)
            # TODO: q_result enum에 정의된 값으로 변경 필요
            # if pass_fail is not None:
            #     data['result'] = pass_fail
            
            result = self.supabase.table('user_answers').insert(data).execute()
            
            return len(result.data) > 0
        except Exception as e:
            st.error(f"답변 저장 오류: {str(e)}")
            return False
    
    def get_user_answers(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """사용자 답변 기록 조회"""
        try:
            result = self.supabase.table('user_answers').select('*').eq('user_id', user_id).order('created_at', desc=True).limit(limit).execute()
            
            return result.data or []
        except Exception as e:
            st.error(f"답변 기록 조회 오류: {str(e)}")
            return []
    
    def get_user_answers_with_questions(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """사용자 답변과 문제 정보 함께 조회"""
        try:
            # user_answers와 questions를 조인해서 조회
            result = self.supabase.table('user_answers').select('*, questions(*)').eq('user_id', user_id).order('created_at', desc=True).limit(limit).execute()
            
            return result.data or []
        except Exception as e:
            st.error(f"답변 기록 조회 오류: {str(e)}")
            return []