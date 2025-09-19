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
        difficulty = st.selectbox(
            "난이도 선택",
            available_difficulties
        )
        
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button("🎲 문제 받기", type="primary", use_container_width=True):
                # DB에서 문제 가져오기 (PASS한 문제 제외)
                db = GameDatabase()
                user_id = st.session_state.get('user_id')
                
                # 사용자가 PASS한 문제 ID 목록 조회
                passed_question_ids = []
                if user_id:
                    passed_question_ids = db.get_passed_question_ids(user_id)
                    if passed_question_ids:
                        st.info(f"🚫 이미 PASS한 문제 {len(passed_question_ids)}개를 제외합니다.")
                
                question = db.get_random_question(difficulty=difficulty, exclude_question_ids=passed_question_ids)
                
                if question:
                    st.session_state.current_question = question
                    st.session_state.current_step = 0
                    st.session_state.user_answers = []
                    st.session_state.last_difficulty = difficulty  # 난이도 저장
                    st.session_state.question_start_time = st.session_state.get('question_start_time', 0)
                    st.session_state.answer_submitted = False  # 제출 상태 초기화
                    st.rerun()
                else:
                    if passed_question_ids:
                        st.warning("해당 난이도의 모든 문제를 이미 통과했습니다! 다른 난이도를 시도해보세요.")
                    else:
                        st.error("해당 난이도의 문제를 찾을 수 없습니다.")
        
        with col_btn2:
            if st.button("🔄 다른 문제", use_container_width=True):
                # 다른 문제 가져오기 (현재 문제와 PASS한 문제 제외)
                db = GameDatabase()
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
                
                if exclude_ids:
                    st.info(f"🚫 이미 PASS한 문제와 현재 문제를 제외합니다. (총 {len(exclude_ids)}개)")
                
                # 최대 5번 시도해서 다른 문제 찾기
                for attempt in range(5):
                    question = db.get_random_question(difficulty=difficulty, exclude_question_ids=exclude_ids)
                    
                    if question and question.get('id') != current_question_id:
                        st.session_state.current_question = question
                        st.session_state.current_step = 0
                        st.session_state.user_answers = []
                        st.session_state.last_difficulty = difficulty  # 난이도 저장
                        st.session_state.question_start_time = st.session_state.get('question_start_time', 0)
                        st.session_state.answer_submitted = False  # 제출 상태 초기화
                        st.rerun()
                        break
                    elif attempt == 4:  # 마지막 시도
                        if exclude_ids:
                            st.warning("해당 난이도에서 새로운 문제를 찾을 수 없습니다. 모든 문제를 이미 통과했거나 현재 문제만 남았습니다.")
                        else:
                            st.warning("다른 문제를 찾을 수 없습니다. 같은 문제가 표시됩니다.")
                        if question:
                            st.session_state.current_question = question
                            st.session_state.current_step = 0
                            st.session_state.user_answers = []
                            st.session_state.last_difficulty = difficulty
                            st.session_state.question_start_time = st.session_state.get('question_start_time', 0)
                            st.session_state.answer_submitted = False  # 제출 상태 초기화
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
        
        # 디버깅 정보 (제출 후에만 표시)
        if 'current_question' in st.session_state and st.session_state.get('answer_submitted', False):
            question = st.session_state.current_question
            st.markdown("---")
            st.markdown("#### 🔍 디버깅 정보")
            st.write("**question.scenario:**", question.get('scenario'))
            st.write("**steps 구조:**", question.get('steps'))
            
            # 프롬프트 입력 데이터 표시
            if 'submission_data' in st.session_state:
                st.markdown("#### 📝 프롬프트 Input JSON")
                st.json(st.session_state.submission_data)
            
            # 프롬프트 텍스트 표시
            if 'prompt_text' in st.session_state:
                st.markdown("#### 📋 System 프롬프트")
                st.text_area("프롬프트 내용:", st.session_state.prompt_text, height=200, disabled=True)
            
            # AI 응답 표시
            if 'ai_response' in st.session_state:
                st.markdown("#### 🤖 AI 응답")
                ai_response = st.session_state.ai_response
                if ai_response.get('error'):
                    st.error(f"AI 응답 오류: {ai_response['error']}")
                else:
                    st.json(ai_response)


def submit_answers(question: Dict, user_answers: list, on_submit_answer: Callable, user_id: str):
    """답안 제출 처리"""
    try:
        # 1. 답안을 JSON 구조로 변환
        submission_data = create_submission_json(question, user_answers)
        
        # 2. Supabase에서 프롬프트 가져오기
        db = GameDatabase()
        prompt = db.get_prompt_by_id("1afe1512-9a7a-4eee-b316-1734b9c81f3a")
        
        if not prompt:
            st.error("❌ 프롬프트를 찾을 수 없습니다.")
            return
        
        # 3. 프롬프트 호출 및 답변 받기
        ai_response = call_ai_with_prompt(prompt, submission_data)
        
        # 4. AI 응답과 입력 데이터를 세션에 저장 (디버깅 정보용)
        st.session_state.ai_response = ai_response
        st.session_state.submission_data = submission_data
        st.session_state.prompt_text = prompt
        st.session_state.answer_submitted = True  # 제출 상태 설정
        
        # 5. AI 응답에서 pass_fail 정보 추출
        pass_fail = None
        if ai_response and not ai_response.get('error'):
            try:
                # AI 응답에서 pass_fail 추출
                ai_pass_fail = ai_response.get('pass_fail')
                if ai_pass_fail:
                    pass_fail = ai_pass_fail
                    st.info(f"🤖 AI 응답에서 pass_fail 추출: {pass_fail}")
                else:
                    st.info("🤖 AI 응답에 pass_fail 정보가 없습니다.")
            except Exception as e:
                st.warning(f"AI 응답 정보 처리 중 오류: {str(e)}")
        
        # 6. 기존 채점 시스템 호출 (pass_fail 정보 포함)
        answer_text = json.dumps(user_answers, ensure_ascii=False)
        result = on_submit_answer(
            user_id,
            question,
            answer_text,
            pass_fail  # pass_fail 정보 전달
        )
        
        # 7. pass_fail 정보가 없으면 기본 채점 결과 사용
        if pass_fail is None:
            pass_fail = 'PASS' if result.get('passed', False) else 'FAIL'
            st.info(f"📊 기본 채점 결과로 pass_fail 설정: {pass_fail}")
        
        st.success(f"✅ 답안 제출 완료 - pass_fail: {pass_fail}")
        
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
            
            # 세션 정리하지 않고 결과 화면 유지
            # 문제 정보는 유지하되, 단계와 답안만 초기화
            if 'current_step' in st.session_state:
                del st.session_state.current_step
            if 'user_answers' in st.session_state:
                del st.session_state.user_answers
            
            # 다른 문제 받기 버튼 표시
            st.markdown("---")
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                if st.button("🔄 다른 문제 받기", type="primary", use_container_width=True):
                    # 현재 난이도 유지하면서 새 문제 받기 (PASS한 문제 제외)
                    difficulty = st.session_state.get('last_difficulty', '보통')
                    db = GameDatabase()
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
                    
                    if exclude_ids:
                        st.info(f"🚫 이미 PASS한 문제와 현재 문제를 제외합니다. (총 {len(exclude_ids)}개)")
                    
                    # 최대 5번 시도해서 다른 문제 찾기
                    for attempt in range(5):
                        new_question = db.get_random_question(difficulty=difficulty, exclude_question_ids=exclude_ids)
                        
                        if new_question and new_question.get('id') != current_question_id:
                            st.session_state.current_question = new_question
                            st.session_state.current_step = 0
                            st.session_state.user_answers = []
                            st.session_state.question_start_time = st.session_state.get('question_start_time', 0)
                            st.session_state.answer_submitted = False  # 제출 상태 초기화
                            # 결과 화면 관련 세션 정리
                            if 'submission_data' in st.session_state:
                                del st.session_state.submission_data
                            if 'prompt_text' in st.session_state:
                                del st.session_state.prompt_text
                            if 'ai_response' in st.session_state:
                                del st.session_state.ai_response
                            st.rerun()
                            break
                        elif attempt == 4:  # 마지막 시도
                            if exclude_ids:
                                st.warning("해당 난이도에서 새로운 문제를 찾을 수 없습니다. 모든 문제를 이미 통과했거나 현재 문제만 남았습니다.")
                            else:
                                st.warning("다른 문제를 찾을 수 없습니다. 같은 문제가 표시됩니다.")
                            if new_question:
                                st.session_state.current_question = new_question
                                st.session_state.current_step = 0
                                st.session_state.user_answers = []
                                st.session_state.question_start_time = st.session_state.get('question_start_time', 0)
                                st.session_state.answer_submitted = False  # 제출 상태 초기화
                                # 결과 화면 관련 세션 정리
                                if 'submission_data' in st.session_state:
                                    del st.session_state.submission_data
                                if 'prompt_text' in st.session_state:
                                    del st.session_state.prompt_text
                                if 'ai_response' in st.session_state:
                                    del st.session_state.ai_response
                                st.rerun()
                            else:
                                st.error("해당 난이도의 문제를 찾을 수 없습니다.")
        else:
            st.error(f"❌ 제출 실패: {result.get('message', '알 수 없는 오류')}")
            
    except Exception as e:
        st.error(f"답안 제출 중 오류가 발생했습니다: {str(e)}")


def create_submission_json(question: Dict, user_answers: list) -> Dict:
    """문제와 답안을 JSON 구조로 변환"""
    try:
        # question이 딕셔너리가 아닌 경우 처리
        if not isinstance(question, dict):
            st.error(f"❌ question이 딕셔너리가 아닙니다. 타입: {type(question)}")
            return {}
        
        # steps에서 문제 정보 추출
        steps = question.get('steps', [])
        if isinstance(steps, str):
            try:
                steps = json.loads(steps)
            except json.JSONDecodeError as e:
                st.error(f"❌ steps JSON 파싱 오류: {str(e)}")
                return {}
        
        # answer_key, weights_map, feedback_map 생성
        answer_key = []
        weights_map = []
        feedback_map = []
        
        for step in steps:
            options = step.get('options', [])
            if isinstance(options, str):
                try:
                    options = json.loads(options)
                except:
                    options = []
            
            # answer_key (정답) - 가중치가 1.0인 옵션을 정답으로 설정
            correct_answer = 'A'  # 기본값
            if options and len(options) > 0:
                for option in options:
                    if isinstance(option, dict):
                        weight = option.get('weight', 0.5)
                        if weight == 1.0:  # 가중치가 1.0인 옵션이 정답
                            correct_answer = option.get('id', 'A')
                            break
                    else:
                        # 딕셔너리가 아닌 경우 첫 번째 옵션을 정답으로 설정
                        correct_answer = str(option)[0] if str(option) else 'A'
                        break
            answer_key.append(correct_answer)
            
            # weights_map 생성
            weights = {}
            for option in options:
                if isinstance(option, dict):
                    option_id = option.get('id', 'A')
                    weight = option.get('weight', 0.5)  # 기본값 0.5
                    weights[option_id] = weight
            weights_map.append(weights)
            
            # feedback_map 생성
            feedbacks = {}
            for option in options:
                if isinstance(option, dict):
                    option_id = option.get('id', 'A')
                    feedback = option.get('feedback', f'{option_id} 선택지에 대한 피드백')
                    feedbacks[option_id] = feedback
            feedback_map.append(feedbacks)
        
        # sessions 생성
        sessions = []
        for answer in user_answers:
            if isinstance(answer, dict):
                sessions.append({"selected_option_id": answer.get('selected_option_id', 'A')})
            else:
                # 문자열인 경우 첫 번째 문자를 ID로 사용
                option_id = str(answer)[0] if answer else 'A'
                sessions.append({"selected_option_id": option_id})
        
        # 최종 JSON 구조 생성
        submission_data = {
            "problem": {
                "lang": "kr",
                "problemTitle": question.get('question_text', '문제 제목'),
                "scenario": question.get('scenario', ''),
                "answer_key": answer_key,
                "weights_map": weights_map,
                "feedback_map": feedback_map
            },
            "sessions": sessions
        }
        
        return submission_data
        
    except Exception as e:
        st.error(f"JSON 구조 생성 중 오류: {str(e)}")
        return {}


def call_ai_with_prompt(system_prompt: str, submission_data: Dict) -> Dict:
    """프롬프트와 데이터를 사용하여 AI 호출"""
    try:
        # OpenAI 클라이언트 확인
        from src.core.config import OPENAI_API_KEY
        if not OPENAI_API_KEY:
            return {"error": "OpenAI API 키가 설정되지 않았습니다."}
        
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        # 사용자 프롬프트 생성 (제출 데이터 포함)
        user_prompt = f"""
다음 데이터를 분석해주세요:

{json.dumps(submission_data, ensure_ascii=False, indent=2)}

위 데이터를 바탕으로 분석 결과를 JSON 형태로 제공해주세요.
"""
        
        # OpenAI API 호출
        from src.core.config import OPENAI_MODEL
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        
        # 응답 파싱
        content = response.choices[0].message.content
        
        try:
            # JSON 파싱 시도
            ai_response = json.loads(content)
        except Exception as parse_error:
            # JSON 파싱 실패 시 텍스트로 반환
            ai_response = {"response": content, "parsed": False}
        
        return ai_response
        
    except Exception as e:
        return {"error": f"AI 호출 중 오류: {str(e)}"}


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