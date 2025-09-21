# ui/components/auth_components.py
"""
인증 관련 UI 컴포넌트
"""

import streamlit as st
from typing import Callable


def render_google_login_only(on_google_login: Callable[[], None]):
    """Google 로그인만 렌더링"""
    with st.sidebar:
        st.header("👤 사용자 프로필")
        
        # 설정 상태 확인
        from src.core.config import SUPABASE_URL, SUPABASE_ANON_KEY
        if not SUPABASE_URL or not SUPABASE_ANON_KEY:
            st.error("⚠️ Supabase 설정이 필요합니다")
            st.markdown("""
            **설정 방법:**
            1. `.env` 파일 생성
            2. `SUPABASE_URL=your_url` 추가
            3. `SUPABASE_ANON_KEY=your_key` 추가
            """)
            return
        
        # Google 로그인 버튼 (iOS 호환성 개선)
        st.markdown("### 로그인")
        if st.button("🔐 Google로 로그인", key="google_login_btn", use_container_width=True, type="primary"):
            on_google_login()
        
        # iOS 호환성 안내
        st.markdown("""
        <div style="text-align: center; color: #666; font-size: 12px; margin-top: 8px;">
            📱 iOS에서 문제가 있다면<br>
            최상위 창에서 로그인해주세요
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("""
        <div style="text-align: center; color: #666; font-size: 14px;">
            Google 계정으로 간편하게<br>
            로그인하고 게임을 시작하세요!
        </div>
        """, unsafe_allow_html=True)


def render_user_sidebar(profile: dict, on_logout: Callable[[], None]):
    """사용자 사이드바 렌더링"""
    with st.sidebar:
        # 사용자명으로 헤더 표시
        username = profile.get('username', '사용자')
        st.header(f"👤 {username}")
        
        # 프로필 이미지
        if profile.get("profile_image"):
            st.markdown(f'<img src="{profile["profile_image"]}" width="150">', unsafe_allow_html=True)
        
        # 게임 제목
        st.markdown("### AI Master Quest")
        
        # 레벨 정보 (기본값 처리)
        level = profile.get('level', 1)
        level_icon = profile.get('level_icon', '⭐')
        level_name = profile.get('level_name', '초보자')
        st.markdown(f"**레벨 {level}** {level_icon} {level_name}")
        
        # 경험치 바 (기본값 처리)
        current_xp = profile.get('experience_points', 0)
        next_level_xp = profile.get('next_level_xp', 100)
        if next_level_xp > 0:
            xp_progress = (current_xp / next_level_xp) * 100
            # 진행률을 0.0과 1.0 사이로 제한
            progress_value = min(1.0, max(0.0, xp_progress / 100))
            st.progress(progress_value)
            st.caption(f"XP: {current_xp} / {next_level_xp}")
        else:
            st.caption(f"XP: {current_xp}")
        
        # 통계
        col1, col2 = st.columns(2)
        with col1:
            accuracy = profile.get('accuracy', 0.0)
            st.metric("정답률", f"{accuracy:.0f}%")
            st.metric("현재 연속", profile.get('current_streak', 0))
        
        with col2:
            st.metric("총 문제", profile.get('total_questions_solved', 0))
            st.metric("최고 연속", profile.get('best_streak', 0))
        
        # 업적
        if profile.get('achievements'):
            st.markdown("### 🏆 업적")
            for ach in profile['achievements']:
                if isinstance(ach, dict):
                    st.markdown(f"{ach.get('icon', '🏆')} **{ach.get('name', '업적')}**")
                else:
                    # 리스트 형태인 경우 (하위 호환성)
                    if len(ach) > 3:
                        st.markdown(f"{ach[3]} **{ach[1]}**")
                    else:
                        st.markdown(f"🏆 **{ach[1] if len(ach) > 1 else '업적'}**")
        
        # 로그아웃
        if st.button("로그아웃"):
            on_logout()


def render_auth_status():
    """인증 상태 표시"""
    if 'user_id' in st.session_state and st.session_state.user_id:
        return True
    return False
