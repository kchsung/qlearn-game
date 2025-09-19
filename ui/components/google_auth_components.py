# ui/components/google_auth_components.py
"""
Google OAuth 인증 관련 UI 컴포넌트
"""

import streamlit as st
from typing import Callable, Optional
import base64


def render_google_login_button(on_google_login: Callable[[], None]):
    """Google 로그인 버튼 렌더링"""
    st.markdown("""
    <style>
    .google-login-button {
        background: #4285f4;
        color: white;
        border: none;
        padding: 12px 24px;
        border-radius: 8px;
        font-size: 16px;
        font-weight: 500;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        width: 100%;
        transition: background-color 0.3s;
    }
    .google-login-button:hover {
        background: #3367d6;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Google 로고 SVG (Base64 인코딩)
    google_logo = """
    <svg width="20" height="20" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <path fill="#4285f4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
        <path fill="#34a853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
        <path fill="#fbbc05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
        <path fill="#ea4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
    </svg>
    """
    
    # Google 로그인 버튼
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔐 Google로 로그인", key="google_login", use_container_width=True):
            on_google_login()
    
    # 또는 구분선
    st.markdown("---")
    st.markdown("### 또는")
    st.markdown("---")


def render_user_profile_sidebar(user_data: dict, on_logout: Callable[[], None]):
    """사용자 프로필 사이드바 렌더링"""
    with st.sidebar:
        # 사용자명으로 헤더 표시
        username = user_data.get('name', '사용자')
        st.header(f"👤 {username}")
        
        # 프로필 이미지
        if user_data.get('avatar_url'):
            st.image(user_data['avatar_url'], width=150)
        else:
            # 기본 아바타
            st.markdown("""
            <div style="width: 150px; height: 150px; background: linear-gradient(45deg, #667eea 0%, #764ba2 100%); 
                        border-radius: 50%; display: flex; align-items: center; justify-content: center; 
                        color: white; font-size: 48px; margin: 0 auto;">
                👤
            </div>
            """, unsafe_allow_html=True)
        
        # 게임 제목
        st.markdown("### AI Master Quest")
        
        # 이메일 정보
        st.markdown(f"**이메일:** {user_data.get('email', '')}")
        
        # 로그아웃 버튼
        if st.button("로그아웃", type="secondary", use_container_width=True):
            on_logout()
        
        st.markdown("---")
        
        # 추가 정보
        st.markdown("### 📊 계정 정보")
        st.info("""
        **Google 계정으로 로그인됨**
        
        - 안전한 OAuth 인증
        - 이메일 기반 계정 관리
        - 자동 프로필 동기화
        """)


def render_auth_status():
    """인증 상태 표시"""
    if 'user' in st.session_state and st.session_state.user:
        return True
    return False


def render_welcome_with_google_auth():
    """Google 인증이 포함된 환영 페이지"""
    st.title("🎮 AI Master Quest")
    st.markdown("### AI 마스터가 되는 여정에 오신 것을 환영합니다!")
    
    # Google 로그인 섹션
    st.markdown("## 🔐 로그인")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 20px; border: 2px dashed #ddd; border-radius: 10px;">
            <h3>Google 계정으로 시작하기</h3>
            <p>안전하고 빠른 로그인을 위해 Google 계정을 사용하세요.</p>
        </div>
        """, unsafe_allow_html=True)
    
    # 기능 소개
    st.markdown("---")
    st.markdown("## 🚀 주요 기능")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info("""
        **🎯 AI 문제 도전**
        
        - 다양한 난이도의 AI 활용 문제
        - 실시간 자동 채점
        - 상세한 피드백 제공
        """)
    
    with col2:
        st.success("""
        **📈 레벨 시스템**
        
        - 경험치 기반 레벨업
        - 승급 시험 시스템
        - 업적 및 배지 수집
        """)
    
    with col3:
        st.warning("""
        **🏆 경쟁 요소**
        
        - 실시간 리더보드
        - 개인 통계 분석
        - 성과 추적 및 비교
        """)


def render_loading_spinner(message: str = "처리 중..."):
    """로딩 스피너 렌더링"""
    st.markdown(f"""
    <div style="text-align: center; padding: 20px;">
        <div style="display: inline-block; width: 40px; height: 40px; border: 4px solid #f3f3f3; 
                    border-top: 4px solid #3498db; border-radius: 50%; animation: spin 2s linear infinite;"></div>
        <p style="margin-top: 10px;">{message}</p>
    </div>
    <style>
    @keyframes spin {{
        0% {{ transform: rotate(0deg); }}
        100% {{ transform: rotate(360deg); }}
    }}
    </style>
    """, unsafe_allow_html=True)


def render_error_message(message: str):
    """에러 메시지 렌더링"""
    st.error(f"❌ {message}")


def render_success_message(message: str):
    """성공 메시지 렌더링"""
    st.success(f"✅ {message}")
