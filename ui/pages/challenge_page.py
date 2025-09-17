# ui/pages/challenge_page.py
"""
문제 도전 페이지 컴포넌트
"""

import streamlit as st
from typing import Dict, Callable
from src.services.ai_services import QuestionGenerator


def render_challenge_tab(profile: Dict, on_submit_answer: Callable):
    """도전하기 탭 렌더링"""
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
            # 문제 생성
            st.session_state.current_question = QuestionGenerator.generate_question(
                difficulty, profile['level']
            )
            st.rerun()
    
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
                            result = on_submit_answer(question, answer)
                        
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
                    st.rerun()
        else:
            st.info("👈 왼쪽에서 난이도를 선택하고 '문제 받기' 버튼을 클릭하세요!")
            
            # 난이도별 설명
            st.markdown("### 📚 난이도 가이드")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("""
                **초급 (Basic)**
                - AI 도구 기본 사용법
                - 간단한 프롬프트 작성
                - 기본적인 AI 활용
                """)
            
            with col2:
                st.markdown("""
                **중급 (Intermediate)**
                - 복잡한 작업 자동화
                - 창의적인 AI 활용
                - 비즈니스 응용
                """)
            
            with col3:
                st.markdown("""
                **고급 (Advanced)**
                - 혁신적인 솔루션 설계
                - 전략적 AI 활용
                - 비즈니스 모델 창출
                """)
