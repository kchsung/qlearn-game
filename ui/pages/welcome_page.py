# ui/pages/welcome_page.py
"""
환영 페이지 컴포넌트
"""

import streamlit as st


def render_welcome_page():
    """환영 페이지 렌더링"""
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
    st.markdown("👈 왼쪽 사이드바에서 시작하세요!")
    
    # 추가 정보 섹션
    st.markdown("## 🚀 시작하기")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 📋 게임 규칙
        - 각 문제는 난이도별로 분류됩니다
        - 정답 시 경험치를 획득합니다
        - 연속 정답 시 보너스 경험치를 받습니다
        - 레벨업을 통해 새로운 기능을 해금합니다
        """)
    
    with col2:
        st.markdown("""
        ### 🎯 레벨 시스템
        - **레벨 1**: AI Beginner - 기본 문제
        - **레벨 2**: AI Explorer - 중급 문제 + 힌트
        - **레벨 3**: AI Practitioner - 고급 문제 + 상세 피드백
        - **레벨 4**: AI Expert - 전문가 문제 + 문제 제안
        - **레벨 5**: AI Master - 모든 기능 + 멘토 권한
        """)
    
    # 통계 정보
    st.markdown("## 📊 게임 통계")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("총 사용자", "1,234", "12")
    
    with col2:
        st.metric("해결된 문제", "15,678", "234")
    
    with col3:
        st.metric("평균 정답률", "78.5%", "2.1%")
    
    with col4:
        st.metric("활성 사용자", "456", "23")
