# ui/pages/promotion_page.py
"""
승급 시험 페이지 컴포넌트 (Supabase 기반)
도전하기와 동일한 방식으로 구현
"""

import streamlit as st
import json
import time
from typing import Dict, Callable
from src.core.database import GameDatabase


def render_promotion_exam(profile: Dict, game_engine, db, user_id: str):
    """승급 시험 렌더링"""
    
    # 승급 자격 확인
    can_promote, promotion_info = game_engine.check_promotion_eligibility(user_id)
    
    if can_promote:
        st.success(f"🎯 레벨 {promotion_info['next_level']} 승급 시험에 도전할 수 있습니다!")
        st.info(f"📊 현재 상태: 레벨 {promotion_info['current_level']}, XP {promotion_info['current_xp']}/{promotion_info['required_xp']}")
        
        if st.button("🚀 승급 시험 시작", type="primary"):
            # 승급 시험 시작 - "쉬움" 난이도 문제 가져오기 (PASS한 문제 제외)
            passed_question_ids = db.get_passed_question_ids(user_id)
            if passed_question_ids:
                st.info(f"🚫 이미 PASS한 문제 {len(passed_question_ids)}개를 제외합니다.")
            
            question = db.get_random_question(difficulty="쉬움", exclude_question_ids=passed_question_ids)
            
            if question:
                st.session_state.promotion_exam = {
                    'user_id': user_id,
                    'current_level': promotion_info['current_level'],
                    'next_level': promotion_info['next_level'],
                    'question': question,
                    'current_step': 0,
                    'user_answers': [],
                    'start_time': time.time(),
                    'exam_submitted': False
                }
                st.rerun()
            else:
                if passed_question_ids:
                    st.warning("❌ '쉬움' 난이도의 모든 문제를 이미 통과했습니다! 다른 난이도의 문제를 풀어보세요.")
                else:
                    st.error("❌ 승급 시험 문제를 찾을 수 없습니다.")
    else:
        st.warning(f"❌ 레벨 {promotion_info['next_level']} 승급 시험 자격이 없습니다.")
        st.info(f"📊 현재 상태: 레벨 {promotion_info['current_level']}, XP {promotion_info['current_xp']}/{promotion_info['required_xp']}")
        st.info(f"💡 승급을 위해서는 {promotion_info['required_xp'] - promotion_info['current_xp']} XP가 더 필요합니다.")
        return
    
    # 승급 시험 진행 중
    if 'promotion_exam' in st.session_state:
        exam = st.session_state.promotion_exam
        
        # 필수 키들이 없으면 기본값 설정
        if 'exam_submitted' not in exam:
            exam['exam_submitted'] = False
        if 'current_step' not in exam:
            exam['current_step'] = 0
        if 'user_answers' not in exam:
            exam['user_answers'] = []
        if 'start_time' not in exam:
                exam['start_time'] = time.time()
        
        if not exam['exam_submitted']:
            # 승급 시험 문제 표시 (도전하기와 동일한 방식)
            render_promotion_question(exam, db, user_id)
        else:
            # 승급 시험 결과 표시
            render_promotion_result(exam, game_engine, user_id)
    
    else:
        # 승급 자격이 없는 경우
        render_promotion_requirements(profile)


def render_promotion_question(exam: Dict, db: GameDatabase, user_id: str):
    """승급 시험 문제 표시 (도전하기와 동일한 방식)"""
    
    st.subheader(f"레벨 {exam['next_level']} 승급 시험")
    
    question = exam['question']
    current_step = exam['current_step']
    
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
        
        # 2. 단계 정보와 제목
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
                            clean_text = option_text
                        else:
                            clean_text = option_text
                        
                        option_texts.append(clean_text)
                        option_feedbacks[clean_text] = option_feedback
                    else:
                        option_texts.append(str(option))
                
                selected_option = st.radio(
                    "답안을 선택하세요:",
                    option_texts,
                    key=f"promotion_step_{current_step}"
                )
                
                # 승급 시험에서는 피드백 표시하지 않음 (시험이므로)
            
            else:
                # 일반적인 문자열 리스트 처리
                selected_option = st.radio(
                    "답안을 선택하세요:",
                    options,
                    key=f"promotion_step_{current_step}"
                )
                
                # 승급 시험에서는 피드백 표시하지 않음 (시험이므로)
        
        # 버튼 영역
        col_prev, col_next = st.columns(2)
        
        with col_prev:
            if current_step > 0:
                if st.button("⬅️ 이전", use_container_width=True, key=f"promotion_prev_{current_step}"):
                    exam['current_step'] -= 1
                    st.rerun()
        
        with col_next:
            if current_step < len(steps) - 1:
                if st.button("다음 ➡️", type="primary", use_container_width=True, key=f"promotion_next_{current_step}"):
                    # 현재 답안 저장
                    if 'user_answers' not in exam:
                        exam['user_answers'] = []
                    exam['user_answers'].append(selected_option)
                    exam['current_step'] += 1
                    st.rerun()
            else:
                # 마지막 단계 - 제출 버튼
                if st.button("📤 승급 시험 제출", type="primary", use_container_width=True, key=f"promotion_submit_{current_step}"):
                    # 모든 답안 저장
                    if 'user_answers' not in exam:
                        exam['user_answers'] = []
                    exam['user_answers'].append(selected_option)
                    
                    # 승급 시험 제출
                    submit_promotion_exam(exam, db, user_id)
    
    else:
        st.success("모든 단계를 완료했습니다!")


def submit_promotion_exam(exam: Dict, db: GameDatabase, user_id: str):
    """승급 시험 제출 처리 (도전하기와 동일한 방식)"""
    try:
        # 1. 답안을 JSON 구조로 변환
        submission_data = create_promotion_submission_json(exam['question'], exam['user_answers'])
        
        # 2. Supabase에서 프롬프트 가져오기
        prompt = db.get_prompt_by_id("1afe1512-9a7a-4eee-b316-1734b9c81f3a")
        
        if not prompt:
            st.error("❌ 프롬프트를 찾을 수 없습니다.")
            return
        
        # 3. 프롬프트 호출 및 답변 받기
        ai_response = call_ai_with_prompt(prompt, submission_data)
        
        # 4. AI 응답을 세션에 저장
        exam['ai_response'] = ai_response
        exam['submission_data'] = submission_data
        exam['exam_submitted'] = True
        
        st.rerun()
        
    except Exception as e:
        st.error(f"승급 시험 제출 중 오류가 발생했습니다: {str(e)}")


def render_promotion_result(exam: Dict, game_engine, user_id: str):
    """승급 시험 결과 표시"""
    
    st.subheader("🎯 승급 시험 결과")
    
    ai_response = exam.get('ai_response', {})
    
    if ai_response and not ai_response.get('error'):
        # AI 응답에서 결과 추출
        pass_fail = ai_response.get('pass_fail', 'FAIL')
        score_raw = ai_response.get('score', 0)
        
        # score가 딕셔너리인 경우 처리
        if isinstance(score_raw, dict):
            # 새로운 JSON 구조에서 total 값 추출
            score = score_raw.get('total', 0)
            # total이 없으면 quantitative.aggregate + qualitative.overall로 계산
            if score == 0:
                quant_score = score_raw.get('quantitative', {}).get('aggregate', 0)
                qual_score = score_raw.get('qualitative', {}).get('overall', 0)
                score = quant_score + qual_score
        elif isinstance(score_raw, (int, float)):
            score = score_raw
        else:
            score = 0
        
        st.info(f"🤖 AI 평가 결과: {pass_fail}")
        st.info(f"📊 총점: {score}")
        
        # 디버깅: 점수 계산 과정 표시
        if isinstance(score_raw, dict):
            st.info(f"🔍 점수 계산 과정:")
            st.info(f"- total 필드: {score_raw.get('total', '없음')}")
            if score_raw.get('total', 0) == 0:
                quant_score = score_raw.get('quantitative', {}).get('aggregate', 0)
                qual_score = score_raw.get('qualitative', {}).get('overall', 0)
                st.info(f"- 정량적 점수: {quant_score}")
                st.info(f"- 정성적 점수: {qual_score}")
                st.info(f"- 계산된 총점: {quant_score + qual_score}")
        
        # 상세 점수 정보 표시 (딕셔너리인 경우)
        if isinstance(score_raw, dict):
            col1, col2 = st.columns(2)
            with col1:
                if 'quantitative' in score_raw:
                    quant = score_raw['quantitative']
                    st.metric("정량적 점수", f"{quant.get('aggregate', 0)}/100")
            with col2:
                if 'qualitative' in score_raw:
                    qual = score_raw['qualitative']
                    st.metric("정성적 점수", f"{qual.get('overall', 0)}/100")
        
        # 상세 평가 결과 표시 (PASS/FAIL 모두)
        st.markdown("---")
        st.subheader("📋 상세 평가 결과")
        
        # detail 코멘트 표시 (마크다운 형태로 그대로 표시)
        detail = ai_response.get('detail', '')
        if detail:
            st.markdown("#### 💬 AI 평가 코멘트")
            # 줄바꿈 문자를 HTML <br> 태그로 변환하여 표시
            formatted_detail = detail.replace('\n', '\n\n')
            st.markdown(formatted_detail)
        
        # 승급 시험 통과 조건 확인 (200점 만점에서 100점 이상)
        if pass_fail == "PASS" and score >= 100:
            st.success("🎊 축하합니다! 승급 시험에 통과했습니다!")
            st.balloons()
            
            # 승급 처리 상태 확인
            if not exam.get('promotion_processed', False):
                st.info("📝 승급 처리를 진행하시겠습니까?")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ 승급 처리", type="primary", key="promotion_confirm"):
                        # 실제 승급 처리
                        try:
                            promotion_result = game_engine.process_promotion_result(
                                user_id, 
                                score, 
                                int(time.time() - exam['start_time'])
                            )
                            
                            if promotion_result.get('success') and promotion_result.get('promoted'):
                                st.success(f"🎉 레벨 {promotion_result.get('new_level')}로 승급 완료!")
                                st.success(f"💎 획득 XP: {promotion_result.get('xp_reward', 0)}")
                                exam['promotion_processed'] = True
                                st.rerun()
                            else:
                                st.error(f"승급 처리 실패: {promotion_result.get('message', '알 수 없는 오류')}")
                                
                        except Exception as e:
                            st.error(f"승급 처리 중 오류: {str(e)}")
                            import traceback
                            st.error(f"상세 오류: {traceback.format_exc()}")
                
                with col2:
                    if st.button("❌ 취소", key="promotion_cancel"):
                        del st.session_state.promotion_exam
                        st.rerun()
            else:
                st.success("✅ 승급 처리가 완료되었습니다!")
                if st.button("🏠 메인으로 돌아가기", type="primary", key="promotion_home"):
                    del st.session_state.promotion_exam
                    st.rerun()
        
        else:
            st.error("❌ 승급 시험에 실패했습니다.")
            
            # 실패 원인 상세 표시
            st.markdown("#### 📊 실패 원인 분석")
            if pass_fail != "PASS":
                st.warning(f"📝 평가 결과: {pass_fail} (PASS 필요)")
            if score < 100:
                st.warning(f"📊 점수 부족: {score}/200 (100점 이상 필요)")
            
            # 개선 방향 제시
            st.info("💡 **개선 방향**:")
            st.info("- 더 많은 연습을 통해 문제 해결 능력을 향상시키세요")
            st.info("- 각 단계별 선택지의 의미를 정확히 파악하세요")
            st.info("- AI 평가 코멘트를 참고하여 학습하세요")
            
            # 버튼들
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 다시 도전", type="primary", key="promotion_retry_failed"):
                    del st.session_state.promotion_exam
                    st.rerun()
            with col2:
                if st.button("🏠 메인으로 돌아가기", key="promotion_home_failed"):
                    del st.session_state.promotion_exam
                    st.rerun()
    
    else:
        st.error("❌ AI 평가 중 오류가 발생했습니다.")
        if ai_response.get('error'):
            st.error(f"오류 내용: {ai_response['error']}")
        
        # 다시 도전 버튼
        if st.button("🔄 다시 도전", type="primary", key="promotion_retry_error"):
            del st.session_state.promotion_exam
            st.rerun()
    
    # 디버깅 정보 표시
    if st.checkbox("🔍 디버깅 정보 보기", key="promotion_debug_checkbox"):
        st.markdown("---")
        st.subheader("🔍 디버깅 정보")
        
        # 제출 데이터
        st.markdown("#### 📝 제출 데이터")
        submission_data = exam.get('submission_data', {})
        st.json(submission_data)
        
        # AI 응답
        st.markdown("#### 🤖 AI 응답")
        ai_response = exam.get('ai_response', {})
        st.json(ai_response)
        
        # 선택된 답안과 option_id 매칭 정보 표시
        st.markdown("#### 🎯 답안 매칭 정보")
        user_answers = exam.get('user_answers', [])
        sessions = submission_data.get('sessions', [])
        answer_key = submission_data.get('problem', {}).get('answer_key', [])
        
        for i, (answer, session, correct_id) in enumerate(zip(user_answers, sessions, answer_key)):
            st.write(f"**단계 {i+1}**:")
            st.write(f"- 선택된 답안: `{answer}`")
            st.write(f"- 추출된 option_id: `{session.get('selected_option_id', 'N/A')}`")
            st.write(f"- 정답: `{correct_id}`")
            st.write(f"- 정답 여부: {'✅' if session.get('selected_option_id') == correct_id else '❌'}")
            st.write("---")
        
        # 점수 계산 상세 정보
        if ai_response and isinstance(ai_response.get('score'), dict):
            st.markdown("#### 📈 점수 계산 상세")
            score_data = ai_response['score']
            st.write(f"- **Total 필드**: {score_data.get('total', '없음')}")
            st.write(f"- **정량적 점수**: {score_data.get('quantitative', {}).get('aggregate', 0)}")
            st.write(f"- **정성적 점수**: {score_data.get('qualitative', {}).get('overall', 0)}")
            st.write(f"- **계산된 총점**: {score_data.get('quantitative', {}).get('aggregate', 0) + score_data.get('qualitative', {}).get('overall', 0)}")


def create_promotion_submission_json(question: Dict, user_answers: list) -> Dict:
    """승급 시험 문제와 답안을 JSON 구조로 변환 (도전하기와 동일)"""
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
        for i, answer in enumerate(user_answers):
            if isinstance(answer, dict):
                sessions.append({"selected_option_id": answer.get('selected_option_id', 'A')})
            else:
                # 선택된 답안에서 올바른 option_id 추출
                step = steps[i] if i < len(steps) else {}
                options = step.get('options', [])
                if isinstance(options, str):
                    try:
                        options = json.loads(options)
                    except:
                        options = []
                
                # 선택된 답안과 매칭되는 option_id 찾기
                option_id = 'A'  # 기본값
                if isinstance(options, list) and len(options) > 0:
                    for option in options:
                        if isinstance(option, dict):
                            option_text = option.get('text', '')
                            if str(answer) == option_text or str(answer) in option_text:
                                option_id = option.get('id', 'A')
                                break
                        else:
                            if str(answer) == str(option):
                                option_id = str(option)[0] if str(option) else 'A'
                                break
                
                sessions.append({"selected_option_id": option_id})
        
        # 최종 JSON 구조 생성
        submission_data = {
            "problem": {
                "lang": "kr",
                "problemTitle": question.get('question_text', '승급 시험 문제'),
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
    """프롬프트와 데이터를 사용하여 AI 호출 (도전하기와 동일)"""
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


def render_promotion_requirements(profile: Dict):
    """승급 요구사항 표시"""
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