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
    
    # 세션 상태 초기화
    if 'current_step' not in st.session_state:
        st.session_state.current_step = 0
    if 'user_answers' not in st.session_state:
        st.session_state.user_answers = []
    if 'answer_submitted' not in st.session_state:
        st.session_state.answer_submitted = False
    
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
        available_difficulties.append("어려움")
    if profile['level'] >= 4:
        available_difficulties.append("아주 어려움")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # 문제 유형 선택
        db = GameDatabase()
        available_types = db.get_available_question_types()
        
        # 문제 유형 한글 표시명 매핑
        type_display_names = {
            'multiple_choice': '객관식',
            'short_answer': '단답형',
            'essay': '서술형',
            'coding': '코딩',
            'scenario': '시나리오'
        }
        
        # 사용 가능한 유형들을 한글로 표시
        type_options = []
        for q_type in available_types:
            display_name = type_display_names.get(q_type, q_type)
            type_options.append(f"{display_name} ({q_type})")
        
        selected_type_display = st.selectbox(
            "문제 유형 선택",
            type_options,
            index=0  # 기본값은 첫 번째 옵션
        )
        
        # 선택된 유형에서 실제 타입 추출
        selected_type = available_types[0]  # 기본값
        for i, option in enumerate(type_options):
            if option == selected_type_display:
                selected_type = available_types[i]
                break
        
        difficulty = st.selectbox(
            "난이도 선택",
            available_difficulties
        )
        
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button("🎲 문제 받기", type="primary", use_container_width=True):
                # DB에서 문제 가져오기 (PASS한 문제 제외)
                user_id = st.session_state.get('user_id')
                
                # 사용자가 PASS한 문제 ID 목록 조회
                passed_question_ids = []
                if user_id:
                    passed_question_ids = db.get_passed_question_ids(user_id)
                
                question = db.get_random_question(difficulty=difficulty, question_type=selected_type, exclude_question_ids=passed_question_ids)
                
                if question:
                    st.session_state.current_question = question
                    st.session_state.current_step = 0
                    st.session_state.user_answers = []
                    st.session_state.last_difficulty = difficulty  # 난이도 저장
                    st.session_state.last_question_type = selected_type  # 문제 유형 저장
                    st.session_state.question_start_time = st.session_state.get('question_start_time', 0)
                    st.session_state.answer_submitted = False  # 제출 상태 초기화
                    st.rerun()
                else:
                    pass  # 문제가 없어도 메시지 표시하지 않음
        
        with col_btn2:
            if st.button("🔄 다른 문제", use_container_width=True):
                # 다른 문제 가져오기 (현재 문제와 PASS한 문제 제외)
                user_id = st.session_state.get('user_id')
                current_question_id = None
                if 'current_question' in st.session_state:
                    current_question_id = st.session_state.current_question.get('id')
                
                # 사용자가 PASS한 문제 ID 목록 조회
                passed_question_ids = []
                if user_id:
                    passed_question_ids = db.get_passed_question_ids(user_id)
                
                # 현재 문제도 제외 목록에 추가
                exclude_ids = passed_question_ids.copy()
                if current_question_id:
                    exclude_ids.append(current_question_id)
                
                # 최대 5번 시도해서 다른 문제 찾기
                for attempt in range(5):
                    question = db.get_random_question(difficulty=difficulty, question_type=selected_type, exclude_question_ids=exclude_ids)
                    
                    if question and question.get('id') != current_question_id:
                        st.session_state.current_question = question
                        st.session_state.current_step = 0
                        st.session_state.user_answers = []
                        st.session_state.last_difficulty = difficulty  # 난이도 저장
                        st.session_state.last_question_type = selected_type  # 문제 유형 저장
                        st.session_state.question_start_time = st.session_state.get('question_start_time', 0)
                        st.session_state.answer_submitted = False  # 제출 상태 초기화
                        st.rerun()
                        break
                    elif attempt == 4:  # 마지막 시도
                        if question:
                            st.session_state.current_question = question
                            st.session_state.current_step = 0
                            st.session_state.user_answers = []
                            st.session_state.last_difficulty = difficulty
                            st.session_state.last_question_type = selected_type  # 문제 유형 저장
                            st.session_state.question_start_time = st.session_state.get('question_start_time', 0)
                            st.session_state.answer_submitted = False  # 제출 상태 초기화
                            st.rerun()
    
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
                
                # 3. step의 question 필드 내용 표시
                if step.get('question'):
                    st.markdown(f"**{step['question']}**")
                
                # 4. 문제 내용 (text 필드 사용)
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
                        option_id_mapping = {}  # 텍스트 -> ID 매핑
                        
                        for i, option in enumerate(options):
                            if isinstance(option, dict):
                                option_id = option.get('id', f'Option {i+1}')
                                option_text = option.get('text', f'선택지 {i+1}')
                                option_feedback = option.get('feedback', '')
                                
                                # 원본 텍스트 그대로 사용
                                option_texts.append(option_text)
                                option_feedbacks[option_text] = option_feedback
                                option_id_mapping[option_text] = option_id  # 텍스트 -> ID 매핑 저장
                            else:
                                option_texts.append(str(option))
                        
                        selected_option = st.radio(
                            "답안을 선택하세요:",
                            option_texts,
                            key=f"step_{current_step}"
                        )
                        
                        # 선택된 옵션의 ID를 세션에 저장
                        if selected_option in option_id_mapping:
                            st.session_state[f"selected_id_{current_step}"] = option_id_mapping[selected_option]
                        
                        # 피드백 보기 버튼
                        if st.button("💡 피드백 보기", key=f"feedback_{current_step}", use_container_width=True):
                            show_feedback_for_step(step, selected_option)
                    
                    else:
                        # 일반적인 문자열 리스트 처리
                        selected_option = st.radio(
                            "답안을 선택하세요:",
                            options,
                            key=f"step_{current_step}"
                        )
                        
                        # 피드백 보기 버튼
                        if st.button("💡 피드백 보기", key=f"feedback_{current_step}", use_container_width=True):
                            show_feedback_for_step(step, selected_option)
                
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
                            # 현재 답안 저장 (ID만 저장)
                            if 'user_answers' not in st.session_state:
                                st.session_state.user_answers = []
                            
                            # 선택된 옵션의 ID 가져오기
                            selected_id = st.session_state.get(f"selected_id_{current_step}")
                            st.session_state.user_answers.append(selected_id)
                            st.session_state.current_step += 1
                            st.rerun()
                    else:
                        # 마지막 단계 - 제출 버튼
                        if st.button("📤 제출", type="primary", use_container_width=True):
                            # 모든 답안 저장 (ID만 저장)
                            if 'user_answers' not in st.session_state:
                                st.session_state.user_answers = []
                            
                            # 선택된 옵션의 ID 가져오기
                            selected_id = st.session_state.get(f"selected_id_{current_step}")
                            st.session_state.user_answers.append(selected_id)
                            
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
        


def show_feedback_for_step(step: Dict, selected_option: str):
    """선택된 옵션에 대한 피드백 표시"""
    try:
        options = step.get('options', [])
        if isinstance(options, str):
            try:
                options = json.loads(options)
            except:
                return
        
        # 딕셔너리 형태의 옵션들에서 피드백 찾기
        if options and isinstance(options[0], dict):
            option_feedbacks = {}
            for option in options:
                if isinstance(option, dict):
                    option_text = option.get('text', str(option))
                    feedback = option.get('feedback', '')
                    if feedback:
                        option_feedbacks[option_text] = feedback
            
            if selected_option in option_feedbacks and option_feedbacks[selected_option]:
                st.info(f"💡 **피드백**: {option_feedbacks[selected_option]}")
        else:
            # 일반적인 피드백 처리
            if step.get('feedback'):
                feedback = step['feedback']
                if isinstance(feedback, str):
                    try:
                        feedback = json.loads(feedback)
                    except:
                        feedback = {opt: f"{opt}에 대한 피드백" for opt in options}
                
                if selected_option in feedback:
                    st.info(f"💡 **피드백**: {feedback[selected_option]}")
    except Exception as e:
        pass  # 피드백 표시 실패해도 계속 진행


def compare_answers(question: Dict, user_answers: list) -> str:
    """답안 비교를 통한 PASS/FAIL 판정 - ABCD 문자만 비교"""
    try:
        # steps에서 정답 추출
        steps = question.get('steps', [])
        if isinstance(steps, str):
            try:
                steps = json.loads(steps)
            except:
                return 'FAIL'
        
        if not steps or len(steps) != len(user_answers):
            return 'FAIL'
        
        # 각 단계별로 정답 확인
        for i, step in enumerate(steps):
            if i >= len(user_answers):
                return 'FAIL'
            
            # 정답 옵션 찾기 (weight가 1.0인 옵션)
            correct_option_id = None
            options = step.get('options', [])
            if isinstance(options, str):
                try:
                    options = json.loads(options)
                except:
                    return 'FAIL'
            
            for option in options:
                if isinstance(option, dict) and option.get('weight') == 1.0:
                    correct_option_id = option.get('id')
                    break
            
            if not correct_option_id:
                return 'FAIL'
            
            # 정답이 A, B, C, D 중 하나인지 검증
            if correct_option_id not in ['A', 'B', 'C', 'D']:
                return 'FAIL'
            
            # 사용자 답안 확인 - ID만 저장된 구조
            user_answer = user_answers[i]
            selected_id = user_answer  # 이제 ID만 저장되므로 직접 사용
            
            # 사용자 답안이 A, B, C, D 중 하나인지 검증
            if selected_id not in ['A', 'B', 'C', 'D']:
                return 'FAIL'
            
            # 정답과 비교
            if selected_id != correct_option_id:
                return 'FAIL'
        
        return 'PASS'
        
    except Exception as e:
        return 'FAIL'


def submit_answers(question: Dict, user_answers: list, on_submit_answer: Callable, user_id: str):
    """답안 제출 처리 - 단순 답안 비교 방식"""
    try:
        # 1. 답안 비교를 통한 PASS/FAIL 판정
        pass_fail = compare_answers(question, user_answers)
        
        # 2. 제출 상태 설정
        st.session_state.answer_submitted = True
        
        # 3. 직접 데이터베이스에 저장 (on_submit_answer 호출하지 않음)
        db = GameDatabase()
        success = db.save_user_answer(
            user_id=user_id,
            question_id=question['id'],
            user_answer="",  # answer는 비워둠
            score=100 if pass_fail == 'PASS' else 0,  # PASS면 100점, FAIL이면 0점
            time_taken=0,  # 시간 측정 없음
            tokens_used=0,  # 토큰 사용 없음
            pass_fail=pass_fail
        )
        
        if success:
            # 결과 표시
            if pass_fail == 'PASS':
                st.success(f"🎉 통과! 모든 단계를 정확히 선택했습니다!")
            else:
                st.warning(f"❌ 실패. 일부 단계에서 오답을 선택했습니다.")
            
            # 세션 정리하지 않고 결과 화면 유지
            # 문제 정보는 유지하되, 단계와 답안만 초기화
            if 'current_step' in st.session_state:
                del st.session_state.current_step
            if 'user_answers' in st.session_state:
                del st.session_state.user_answers
            
            # 다른 문제 받기 버튼 표시
            st.markdown("---")
            col1, col2, col3 = st.columns([1, 3, 1])
            with col2:
                if st.button("🔄 다른 문제 받기", type="primary", use_container_width=True):
                    # 현재 난이도와 문제 유형 유지하면서 새 문제 받기 (PASS한 문제 제외)
                    difficulty = st.session_state.get('last_difficulty', '보통')
                    question_type = st.session_state.get('last_question_type', 'multiple_choice')
                    user_id = st.session_state.get('user_id')
                    current_question_id = None
                    if 'current_question' in st.session_state:
                        current_question_id = st.session_state.current_question.get('id')
                    
                    # 사용자가 PASS한 문제 ID 목록 조회
                    passed_question_ids = []
                    if user_id:
                        passed_question_ids = db.get_passed_question_ids(user_id)
                    
                    # 현재 문제도 제외 목록에 추가
                    exclude_ids = passed_question_ids.copy()
                    if current_question_id:
                        exclude_ids.append(current_question_id)
                    
                    # 최대 5번 시도해서 다른 문제 찾기
                    for attempt in range(5):
                        new_question = db.get_random_question(difficulty=difficulty, question_type=question_type, exclude_question_ids=exclude_ids)
                        
                        if new_question and new_question.get('id') != current_question_id:
                            st.session_state.current_question = new_question
                            st.session_state.current_step = 0
                            st.session_state.user_answers = []
                            st.session_state.question_start_time = st.session_state.get('question_start_time', 0)
                            st.session_state.answer_submitted = False  # 제출 상태 초기화
                            # 결과 화면 관련 세션 정리
                            st.rerun()
                            break
                        elif attempt == 4:  # 마지막 시도
                            if new_question:
                                st.session_state.current_question = new_question
                                st.session_state.current_step = 0
                                st.session_state.user_answers = []
                                st.session_state.question_start_time = st.session_state.get('question_start_time', 0)
                                st.session_state.answer_submitted = False  # 제출 상태 초기화
                                # 결과 화면 관련 세션 정리
                                st.rerun()
        else:
            st.error(f"❌ 제출 실패: 데이터베이스 저장에 실패했습니다.")
            
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