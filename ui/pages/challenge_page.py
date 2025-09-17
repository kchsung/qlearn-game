# ui/pages/challenge_page.py
"""
도전하기 페이지 컴포넌트 (Supabase 기반)
"""

import streamlit as st
import json
from typing import Dict, Callable
from src.core.database import GameDatabase


def render_challenge_tab(profile: Dict, on_submit_answer: Callable):
    """도전하기 탭 렌더링"""
    
    # 난이도 5단계 정의 (DB의 difficulty 필드와 매칭)
    difficulties = {
        "아주 쉬움": "아주 쉬움",
        "쉬움": "쉬움", 
        "보통": "보통",
        "어려움": "어려움",
        "아주 어려움": "아주 어려움"
    }
    
    # 레벨에 따른 접근 가능 난이도
    available_difficulties = []
    if profile['level'] >= 1:
        available_difficulties.extend(["아주 쉬움", "쉬움"])
    if profile['level'] >= 2:
        available_difficulties.append("보통")
    if profile['level'] >= 3:
        available_difficulties.append("advanced")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        difficulty = st.selectbox(
            "난이도 선택",
            available_difficulties
        )
        
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button("🎲 문제 받기", type="primary", use_container_width=True):
                # DB에서 문제 가져오기
                db = GameDatabase()
                question = db.get_random_question(difficulty=difficulty)
                
                if question:
                    st.session_state.current_question = question
                    st.session_state.current_step = 0
                    st.session_state.user_answers = []
                    st.session_state.last_difficulty = difficulty  # 난이도 저장
                    st.session_state.question_start_time = st.session_state.get('question_start_time', 0)
                    st.rerun()
                else:
                    st.error("해당 난이도의 문제를 찾을 수 없습니다.")
        
        with col_btn2:
            if st.button("🔄 다른 문제", use_container_width=True):
                # 다른 문제 가져오기 (현재 문제와 다른 문제)
                db = GameDatabase()
                current_question_id = None
                if 'current_question' in st.session_state:
                    current_question_id = st.session_state.current_question.get('id')
                
                # 최대 5번 시도해서 다른 문제 찾기
                for attempt in range(5):
                    question = db.get_random_question(difficulty=difficulty)
                    
                    if question and question.get('id') != current_question_id:
                        st.session_state.current_question = question
                        st.session_state.current_step = 0
                        st.session_state.user_answers = []
                        st.session_state.last_difficulty = difficulty  # 난이도 저장
                        st.session_state.question_start_time = st.session_state.get('question_start_time', 0)
                        st.rerun()
                        break
                    elif attempt == 4:  # 마지막 시도
                        st.warning("다른 문제를 찾을 수 없습니다. 같은 문제가 표시됩니다.")
                        if question:
                            st.session_state.current_question = question
                            st.session_state.current_step = 0
                            st.session_state.user_answers = []
                            st.session_state.last_difficulty = difficulty
                            st.session_state.question_start_time = st.session_state.get('question_start_time', 0)
                            st.rerun()
                        else:
                            st.error("해당 난이도의 문제를 찾을 수 없습니다.")
    
    with col2:
        # 현재 문제 표시
        if 'current_question' in st.session_state:
            question = st.session_state.current_question
            current_step = st.session_state.get('current_step', 0)
            
            # steps 정보 파싱
            steps = []
            if question.get('steps'):
                try:
                    if isinstance(question['steps'], str):
                        steps = json.loads(question['steps'])
                    else:
                        steps = question['steps']
                except:
                    steps = []
            
            if not steps:
                st.error("문제에 단계 정보가 없습니다.")
                return
            
            # 현재 단계 표시
            if current_step < len(steps):
                step = steps[current_step]
                
                # 1. 시나리오 내용 표시 (맨 상단)
                if question.get('scenario'):
                    st.markdown("#### 📋 시나리오")
                    st.markdown(question['scenario'])
                    st.markdown("---")
                
                # 2. 단계 정보와 제목 (글씨 크기 맞춤)
                st.markdown(f"**단계 {current_step + 1}/{len(steps)}: {step.get('title', '문제')}**")
                
                # 문제 내용 (text 필드 사용)
                if step.get('text'):
                    st.markdown(step['text'])
                elif step.get('content'):
                    st.markdown(step['content'])
                
                # 객관식 선택지
                if step.get('options'):
                    options = step['options']
                    if isinstance(options, str):
                        try:
                            options = json.loads(options)
                        except:
                            options = [options]
                    
                    # options가 딕셔너리 리스트인 경우 처리
                    if isinstance(options, list) and len(options) > 0 and isinstance(options[0], dict):
                        # 딕셔너리 형태의 선택지 처리
                        option_texts = []
                        option_feedbacks = {}
                        
                        for i, option in enumerate(options):
                            if isinstance(option, dict):
                                option_id = option.get('id', f'Option {i+1}')
                                option_text = option.get('text', f'선택지 {i+1}')
                                option_feedback = option.get('feedback', '')
                                
                                # 텍스트에서 이미 "A. " 형태로 시작하는지 확인
                                if option_text.startswith(f"{option_id}. "):
                                    # 이미 "A. " 형태면 그대로 사용
                                    clean_text = option_text
                                else:
                                    # "A. " 형태가 아니면 텍스트만 사용
                                    clean_text = option_text
                                
                                option_texts.append(clean_text)
                                option_feedbacks[clean_text] = option_feedback
                            else:
                                option_texts.append(str(option))
                        
                        selected_option = st.radio(
                            "답안을 선택하세요:",
                            option_texts,
                            key=f"step_{current_step}"
                        )
                        
                        # 선택된 옵션의 피드백 표시
                        if selected_option in option_feedbacks and option_feedbacks[selected_option]:
                            st.info(f"💡 **피드백**: {option_feedbacks[selected_option]}")
                    
                    else:
                        # 일반적인 문자열 리스트 처리
                        selected_option = st.radio(
                            "답안을 선택하세요:",
                            options,
                            key=f"step_{current_step}"
                        )
                        
                        # 피드백 표시
                        if step.get('feedback'):
                            feedback = step['feedback']
                            if isinstance(feedback, str):
                                try:
                                    feedback = json.loads(feedback)
                                except:
                                    feedback = {opt: f"{opt}에 대한 피드백" for opt in options}
                            
                            if selected_option in feedback:
                                st.info(f"💡 **피드백**: {feedback[selected_option]}")
                
                # 버튼 영역
                col_prev, col_next = st.columns(2)
                
                with col_prev:
                    if current_step > 0:
                        if st.button("⬅️ 이전", use_container_width=True):
                            st.session_state.current_step -= 1
                            st.rerun()
                
                with col_next:
                    if current_step < len(steps) - 1:
                        if st.button("다음 ➡️", type="primary", use_container_width=True):
                            # 현재 답안 저장
                            if 'user_answers' not in st.session_state:
                                st.session_state.user_answers = []
                            st.session_state.user_answers.append(selected_option)
                            st.session_state.current_step += 1
                            st.rerun()
                    else:
                        # 마지막 단계 - 제출 버튼
                        if st.button("📤 제출", type="primary", use_container_width=True):
                            # 모든 답안 저장
                            if 'user_answers' not in st.session_state:
                                st.session_state.user_answers = []
                            st.session_state.user_answers.append(selected_option)
                            
                            # 답안 제출
                            user_id = st.session_state.get('user_id')
                            if user_id:
                                submit_answers(question, st.session_state.user_answers, on_submit_answer, user_id)
                            else:
                                st.error("사용자 ID를 찾을 수 없습니다.")
            
            else:
                st.success("모든 단계를 완료했습니다!")
        
        else:
            st.info("난이도를 선택하고 '문제 받기' 버튼을 클릭하세요.")
        
        # 디버깅 정보 (맨 아래)
        if 'current_question' in st.session_state:
            question = st.session_state.current_question
            st.markdown("---")
            st.markdown("#### 🔍 디버깅 정보")
            st.write("**question.scenario:**", question.get('scenario'))
            st.write("**steps 구조:**", question.get('steps'))


def submit_answers(question: Dict, user_answers: list, on_submit_answer: Callable, user_id: str):
    """답안 제출 처리"""
    try:
        # 답안을 문자열로 변환
        answer_text = json.dumps(user_answers, ensure_ascii=False)
        
        # 제출 처리
        result = on_submit_answer(
            user_id,
            question,
            answer_text
        )
        
        if result.get('success', True):
            st.success("✅ 답안이 제출되었습니다!")
            
            # 결과 표시
            if result.get('passed'):
                st.success(f"🎉 통과! 점수: {result.get('score', 0):.1f}점")
                st.success(f"💎 획득 XP: {result.get('xp_earned', 0)}")
            else:
                st.warning(f"❌ 실패. 점수: {result.get('score', 0):.1f}점")
            
            # 피드백 표시
            if result.get('feedback'):
                st.info(f"📝 **피드백**: {result['feedback']}")
            
            # 레벨업 체크
            if result.get('level_up'):
                st.balloons()
                st.success(f"🎊 레벨업! 새로운 레벨: {result.get('new_level')}")
            
            # 세션 정리
            if 'current_question' in st.session_state:
                del st.session_state.current_question
            if 'current_step' in st.session_state:
                del st.session_state.current_step
            if 'user_answers' in st.session_state:
                del st.session_state.user_answers
            
            # 다른 문제 받기 버튼 표시
            st.markdown("---")
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                if st.button("🔄 다른 문제 받기", type="primary", use_container_width=True):
                    # 현재 난이도 유지하면서 새 문제 받기
                    difficulty = st.session_state.get('last_difficulty', '보통')
                    db = GameDatabase()
                    current_question_id = None
                    if 'current_question' in st.session_state:
                        current_question_id = st.session_state.current_question.get('id')
                    
                    # 최대 5번 시도해서 다른 문제 찾기
                    for attempt in range(5):
                        question = db.get_random_question(difficulty=difficulty)
                        
                        if question and question.get('id') != current_question_id:
                            st.session_state.current_question = question
                            st.session_state.current_step = 0
                            st.session_state.user_answers = []
                            st.session_state.question_start_time = st.session_state.get('question_start_time', 0)
                            st.rerun()
                            break
                        elif attempt == 4:  # 마지막 시도
                            st.warning("다른 문제를 찾을 수 없습니다. 같은 문제가 표시됩니다.")
                            if question:
                                st.session_state.current_question = question
                                st.session_state.current_step = 0
                                st.session_state.user_answers = []
                                st.session_state.question_start_time = st.session_state.get('question_start_time', 0)
                                st.rerun()
                            else:
                                st.error("해당 난이도의 문제를 찾을 수 없습니다.")
            
            st.rerun()
        else:
            st.error(f"❌ 제출 실패: {result.get('message', '알 수 없는 오류')}")
            
    except Exception as e:
        st.error(f"답안 제출 중 오류가 발생했습니다: {str(e)}")


def render_difficulty_guide():
    """난이도 가이드 표시"""
    st.markdown("### 📚 난이도 가이드")
    
    difficulties_info = {
        "아주 쉬움": "기본적인 AI 개념과 용어",
        "쉬움": "간단한 AI 활용 사례",
        "보통": "AI 모델의 원리와 적용",
        "어려움": "복잡한 AI 시스템 설계",
        "아주 어려움": "고급 AI 기술과 최신 트렌드"
    }
    
    for difficulty, description in difficulties_info.items():
        st.markdown(f"**{difficulty}**: {description}")