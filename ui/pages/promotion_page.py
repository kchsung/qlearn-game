# ui/pages/promotion_page.py
"""
승급 시험 페이지 컴포넌트 (Supabase 기반)
"""

import streamlit as st
from typing import Dict


def render_promotion_exam(profile: Dict, game_engine, db, user_id: str):
    """승급 시험 렌더링"""
    
    # 승급 자격 확인
    can_promote, promotion_info = game_engine.check_promotion_eligibility(user_id)
    
    if can_promote:
        st.success(f"레벨 {promotion_info['next_level']} 승급 시험에 도전할 수 있습니다!")
        
        if st.button("🚀 승급 시험 시작", type="primary"):
            # 승급 시험 시작
            exam_result = game_engine.conduct_promotion_exam(user_id)
            
            if exam_result['success']:
                st.session_state.promotion_exam = {
                    'user_id': user_id,
                    'exam_config': exam_result['exam_config'],
                    'current_level': exam_result['current_level'],
                    'next_level': exam_result['next_level'],
                    'questions': [],
                    'answers': [],
                    'start_time': None
                }
                st.rerun()
            else:
                st.error(exam_result['message'])
    
    # 승급 시험 진행 중
    if 'promotion_exam' in st.session_state:
        exam = st.session_state.promotion_exam
        
        if not exam['start_time']:
            exam['start_time'] = st.session_state.get('exam_start_time', 0)
            if exam['start_time'] == 0:
                import time
                exam['start_time'] = time.time()
                st.session_state.exam_start_time = exam['start_time']
        
        st.subheader(f"레벨 {exam['next_level']} 승급 시험")
        
        # 시험 정보 표시
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("문제 수", exam['exam_config']['questions'])
        with col2:
            st.metric("합격 점수", f"{exam['exam_config']['passing_score']}%")
        with col3:
            remaining_time = exam['exam_config']['time_limit'] - (st.session_state.get('exam_start_time', 0) - exam['start_time'])
            st.metric("남은 시간", f"{int(remaining_time)}초")
        
        # 문제 생성 및 표시
        if not exam['questions']:
            st.info("승급 시험 문제를 생성하는 중...")
            # 실제로는 AI 서비스를 통해 문제를 생성해야 함
            exam['questions'] = [
                {
                    'question': f"승급 시험 문제 {i+1}",
                    'difficulty': 'hard',
                    'type': 'multiple_choice'
                }
                for i in range(exam['exam_config']['questions'])
            ]
            st.rerun()
        
        # 현재 문제 표시
        current_q = len(exam['answers'])
        if current_q < len(exam['questions']):
            question = exam['questions'][current_q]
            
            st.subheader(f"문제 {current_q + 1}/{len(exam['questions'])}")
            st.write(question['question'])
            
            # 답변 입력
            answer = st.text_area("답변을 입력하세요:", key=f"promotion_answer_{current_q}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("다음 문제", disabled=not answer):
                    exam['answers'].append(answer)
                    st.rerun()
            
            with col2:
                if st.button("시험 포기"):
                    del st.session_state.promotion_exam
                    st.rerun()
        
        # 시험 완료
        else:
            st.subheader("시험 완료!")
            
            # 답변 채점 (실제로는 AI 서비스를 통해 채점)
            total_questions = len(exam['questions'])
            correct_answers = len([a for a in exam['answers'] if a.strip()])  # 간단한 채점
            score = (correct_answers / total_questions) * 100
            
            st.metric("점수", f"{score:.1f}%")
            
            # 승급 결과 처리
            if score >= exam['exam_config']['passing_score']:
                st.success(f"🎊 축하합니다! 레벨 {exam['next_level']}로 승급했습니다!")
                st.balloons()
                
                # DB 업데이트 (실제로는 game_engine을 통해 처리)
                # 여기서는 간단히 성공 메시지만 표시
                
                del st.session_state.promotion_exam
                st.rerun()
            else:
                st.error(f"아쉽네요. {score:.0f}% 정답률로 승급에 실패했습니다.")
                st.info("더 많은 문제를 풀고 다시 도전하세요!")
                del st.session_state.promotion_exam
                st.rerun()
    
    else:
        st.info("승급 시험을 보려면 다음 조건을 충족해야 합니다:")
        
        # 현재 레벨 정보 표시
        current_level = profile.get('level', 1)
        current_xp = profile.get('experience_points', 0)
        
        # 다음 레벨 요구사항 (간단한 계산)
        next_level = current_level + 1
        required_xp = next_level * 100  # 간단한 계산
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("현재 레벨", current_level)
            st.metric("현재 XP", current_xp)
        
        with col2:
            st.metric("목표 레벨", next_level)
            st.metric("필요 XP", required_xp)
        
        with col3:
            progress = (current_xp / required_xp) * 100 if required_xp > 0 else 0
            st.metric("진행률", f"{progress:.1f}%")
            # 진행률을 0.0과 1.0 사이로 제한
            progress_value = min(1.0, max(0.0, progress / 100))
            st.progress(progress_value)
        
        # 부족한 조건 표시
        if current_xp < required_xp:
            st.warning(f"⚠️ {required_xp - current_xp} XP가 더 필요합니다.")
        
        st.info("💡 더 많은 문제를 풀어서 경험치를 쌓으세요!")