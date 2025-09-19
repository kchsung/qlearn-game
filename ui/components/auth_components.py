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
        
        # Google 로그인 버튼
        st.markdown("### 로그인")
        if st.button("🔐 Google로 로그인", key="google_login_btn", use_container_width=True, type="primary"):
            on_google_login()
        
        # 테스트 버튼 (개발용)
        if st.button("🧪 테스트 토큰으로 로그인", key="test_login_btn", use_container_width=True):
            from src.auth.supabase_auth import SupabaseAuth
            from src.auth.authentication import AuthenticationManager
            
            supabase_auth = SupabaseAuth()
            user_data = supabase_auth.test_with_provided_token()
            if user_data:
                st.success("✅ 테스트 로그인 성공!")
                
                # 사용자 정보를 로컬 DB에 동기화
                auth_manager = AuthenticationManager()
                user_id = auth_manager._sync_user_to_local_db(user_data)
                
                if user_id:
                    # 세션에 저장
                    st.session_state.user = user_data
                    st.session_state.user_id = user_id
                    st.session_state.login_completed = True
                    st.session_state.user_email = user_data.get('email', '')
                    st.success("✅ 사용자 정보 동기화 완료!")
                    st.rerun()
                else:
                    st.error("❌ 사용자 정보 동기화 실패")
            else:
                st.error("❌ 테스트 로그인 실패")
        
        st.markdown("---")
        st.markdown("""
        <div style="text-align: center; color: #666; font-size: 14px;">
            Google 계정으로 간편하게<br>
            로그인하고 게임을 시작하세요!
        </div>
        """, unsafe_allow_html=True)
        
        # 디버깅 정보 (개발용)
        with st.expander("🔧 디버깅 정보"):
            st.write(f"**Supabase URL:** {SUPABASE_URL[:30]}..." if SUPABASE_URL else "❌ 설정되지 않음")
            st.write(f"**Supabase Key:** {'✅ 설정됨' if SUPABASE_ANON_KEY else '❌ 설정되지 않음'}")
            st.write(f"**현재 포트:** {st.get_option('server.port')}")
            st.write(f"**리다이렉트 URI:** http://localhost:{st.get_option('server.port') or 8501}")
            st.write(f"**쿼리 파라미터:** {dict(st.query_params)}")
            
            # 인증 상태 디버깅
            st.markdown("---")
            st.markdown("**인증 상태 디버깅:**")
            st.write(f"**user_id:** {st.session_state.get('user_id', 'None')}")
            st.write(f"**user (supabase):** {st.session_state.get('user', 'None')}")
            st.write(f"**login_completed:** {st.session_state.get('login_completed', False)}")
            st.write(f"**user_email:** {st.session_state.get('user_email', 'None')}")
            st.write(f"**access_token:** {'✅ 있음' if st.session_state.get('access_token') else '❌ 없음'}")
            st.write(f"**세션 키들:** {list(st.session_state.keys())}")
            
            # 디버깅 모드 토글
            debug_mode = st.checkbox("인증 디버깅 모드", value=st.session_state.get('debug_auth', False))
            st.session_state.debug_auth = debug_mode
            
            # Supabase 설정 확인 안내
            st.markdown("---")
            st.markdown("""
            **⚠️ Supabase 설정 확인사항:**
            
            **1. Supabase Dashboard에서:**
            - Authentication > Providers > Google 활성화
            - **Site URL**: `http://localhost:8503`
            - **Redirect URLs**: `http://localhost:8503`
            
            **2. Google Cloud Console에서:**
            - OAuth 2.0 클라이언트 ID 생성
            - **승인된 리디렉션 URI**: `http://localhost:8503`
            
            **3. 현재 설정:**
            - 리다이렉트 URI: `http://localhost:8503`
            - 포트: 8503
            """)
            
            # 현재 리다이렉트 URI 강조 표시
            current_redirect = f"http://localhost:{st.get_option('server.port') or 8501}"
            st.warning(f"**중요**: Supabase에서 리다이렉트 URI를 `{current_redirect}`로 설정해야 합니다!")


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
