# app.py
"""
AI Master Quest 메인 애플리케이션 클래스
"""

import streamlit as st
import json
from datetime import datetime
from typing import Dict, Optional

from src.core.database import GameDatabase
from src.services.ai_services import AutoGrader, QuestionGenerator
from src.services.game_engine import GameEngine, UserManager
from src.auth.authentication import AuthenticationManager


class AIAssessmentGame:
    """메인 게임 애플리케이션"""
    
    def __init__(self):
        self.db = GameDatabase()
        self.grader = AutoGrader()
        self.game_engine = GameEngine(self.db)
        self.user_manager = UserManager(self.db)
        self.auth_manager = AuthenticationManager()
    
    def submit_answer(self, user_id: str, question: Dict, answer: str, pass_fail: str = None) -> Dict:
        """답변 제출 및 처리 (Supabase 기반)"""
        # 자동 채점
        grade_result = self.grader.grade_answer(question, answer, question['difficulty'])
        
        # 경험치 계산
        xp_earned = self.game_engine.calculate_xp_reward(
            grade_result['total_score'],
            grade_result['time_taken'],
            grade_result['tokens_used'],
            question['difficulty']
        )
        
        # 사용자 답변 저장
        success = self.db.save_user_answer(
            user_id=user_id,
            question_id=question['id'],
            user_answer=answer,
            score=grade_result['total_score'],
            time_taken=grade_result['time_taken'],
            tokens_used=grade_result['tokens_used'],
            pass_fail=pass_fail
        )
        
        if not success:
            return {
                'success': False,
                'message': '답변 저장에 실패했습니다.'
            }
        
        # 사용자 통계 업데이트
        is_correct = grade_result['passed']
        stats_success = self.user_manager.update_user_stats(user_id, is_correct, xp_earned)
        
        if not stats_success:
            return {
                'success': False,
                'message': '통계 업데이트에 실패했습니다.'
            }
        
        # 레벨업 체크 (간단한 구현)
        profile = self.user_manager.get_user_profile(user_id)
        current_level = profile.get('level', 1) if profile else 1
        current_xp = profile.get('experience_points', 0) if profile else 0
        
        # 간단한 레벨업 로직
        new_level = current_level
        level_up = False
        if current_xp >= (current_level + 1) * 100:  # 간단한 레벨업 조건
            new_level = current_level + 1
            level_up = True
        
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
    
    def handle_google_login(self):
        """Google 로그인 처리"""
        self.auth_manager.handle_google_login()
    
    def _is_user_authenticated(self) -> bool:
        """Google OAuth 인증 상태 확인"""
        is_auth = self.auth_manager.is_authenticated()
        
        # 디버깅 정보 (개발 중에만)
        if st.session_state.get('debug_auth', False):
            st.write(f"🔍 App 인증 상태: {is_auth}")
            st.write(f"🔍 Auth Manager 상태: {self.auth_manager.is_authenticated()}")
            st.write(f"🔍 User ID: {st.session_state.get('user_id', 'None')}")
            st.write(f"🔍 Supabase User: {st.session_state.get('user', 'None')}")
        
        return is_auth
    
    def _get_current_user_id(self) -> Optional[str]:
        """현재 사용자 ID 반환 (Google OAuth)"""
        if self.auth_manager.is_authenticated():
            return self.auth_manager.get_current_user_id()
        return None
    
    def handle_logout(self):
        """로그아웃 처리"""
        self.auth_manager.logout()
        # 로그아웃 후 페이지 새로고침으로 첫 화면으로 이동
        st.rerun()
    
    def render_main_content(self):
        """메인 콘텐츠 렌더링"""
        # 기존 로그인 또는 Google OAuth 로그인 확인
        if not self._is_user_authenticated():
            from ui.pages.welcome_page import render_welcome_page
            render_welcome_page()
            return
        
        # 로그인된 사용자 화면
        user_id = self._get_current_user_id()
        if not user_id:
            st.error("사용자 ID를 찾을 수 없습니다.")
            return
            
        profile = self.user_manager.get_user_profile(user_id)
        if not profile:
            st.error("사용자 프로필을 불러올 수 없습니다.")
            return
        
        
        # 탭 구성
        tab1, tab2, tab3, tab4 = st.tabs(["🎯 도전하기", "📊 승급 시험", "🏆 리더보드", "📈 통계"])
        
        with tab1:
            self.render_challenge_tab(profile)
        
        with tab2:
            from ui.pages.promotion_page import render_promotion_exam
            render_promotion_exam(profile, self.game_engine, self.db, user_id)
        
        with tab3:
            from ui.pages.leaderboard_page import render_leaderboard
            render_leaderboard(self.db, profile['username'])
        
        with tab4:
            from ui.pages.stats_page import render_user_stats
            render_user_stats(self.db, user_id)
    
    def render_challenge_tab(self, profile: Dict):
        """도전하기 탭 렌더링"""
        from ui.pages.challenge_page import render_challenge_tab
        render_challenge_tab(profile, self._submit_answer_wrapper)
    
    def _submit_answer_wrapper(self, user_id: str, question: Dict, answer: str, pass_fail: str = None) -> Dict:
        """답변 제출 래퍼"""
        return self.submit_answer(user_id, question, answer, pass_fail)
    
    def render_sidebar(self):
        """사이드바 렌더링"""
        if self._is_user_authenticated():
            # 로그인된 사용자 - 기존 UI 유지
            user_id = self._get_current_user_id()
            if user_id:
                profile = self.user_manager.get_user_profile(user_id)
                if profile:
                    from ui.components.auth_components import render_user_sidebar
                    render_user_sidebar(profile, self.handle_logout)
        else:
            # 로그인되지 않은 사용자 - Google OAuth만
            from ui.components.auth_components import render_google_login_only
            
            # Google 로그인만 표시
            render_google_login_only(self.handle_google_login)
    
    def run(self):
        """애플리케이션 실행"""
        # 세션 초기화
        if 'game' not in st.session_state:
            st.session_state.game = self
        
        if 'user_id' not in st.session_state:
            st.session_state.user_id = None
        
        # OAuth 콜백 자동 처리 (URL에 code가 있을 때)
        if not self._is_user_authenticated() and 'code' in st.query_params:
            st.info("🔄 OAuth 콜백을 처리하는 중...")
            self.handle_google_login()
            return  # 콜백 처리 후 리다이렉트되므로 여기서 종료
        
        # 사이드바 렌더링
        self.render_sidebar()
        
        # 메인 콘텐츠 렌더링
        self.render_main_content()
