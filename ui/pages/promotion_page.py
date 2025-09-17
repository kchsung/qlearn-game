# ui/pages/promotion_page.py
"""
승급 시험 페이지 컴포넌트
"""

import streamlit as st
import sqlite3
from typing import Dict


def render_promotion_exam(profile: Dict, game_engine, db_path: str, user_id: str):
    """승급 시험 렌더링"""
    st.header("📊 승급 시험")
    
    # 레벨업 가능 여부 체크
    can_level_up, next_level = game_engine.check_level_up(user_id)
    
    if can_level_up:
        st.success(f"레벨 {next_level} 승급 시험에 도전할 수 있습니다!")
        
        if st.button("🎯 승급 시험 시작", type="primary"):
            # 승급 시험 문제 생성
            exam_questions = game_engine.generate_promotion_exam(user_id, next_level)
            
            st.session_state.promotion_exam = {
                "questions": exam_questions,
                "current": 0,
                "results": []
            }
            st.rerun()
        
        # 승급 시험 진행
        if 'promotion_exam' in st.session_state:
            exam = st.session_state.promotion_exam
            
            if exam['current'] < len(exam['questions']):
                # 현재 문제 표시
                current_q = exam['questions'][exam['current']]
                
                st.info(f"문제 {exam['current']+1} / {len(exam['questions'])}")
                st.markdown(f"### {current_q['question']}")
                
                answer = st.text_area("답변", key=f"exam_answer_{exam['current']}")
                
                if st.button("다음 문제 →"):
                    # 답변 처리 (간단한 시뮬레이션)
                    exam['results'].append({
                        "question_id": current_q['id'],
                        "passed": st.session_state.get('exam_simulation', True)  # 시뮬레이션 모드
                    })
                    exam['current'] += 1
                    st.rerun()
            
            else:
                # 시험 완료
                passed_count = sum(1 for r in exam['results'] if r['passed'])
                total_count = len(exam['results'])
                pass_rate = passed_count / total_count
                
                if pass_rate >= 0.8:  # 80% 이상 정답
                    st.success(f"🎊 축하합니다! 레벨 {next_level}로 승급했습니다!")
                    st.balloons()
                    
                    # DB 업데이트
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE users SET level = ? WHERE user_id = ?
                    ''', (next_level, user_id))
                    conn.commit()
                    conn.close()
                    
                    del st.session_state.promotion_exam
                    st.rerun()
                else:
                    st.error(f"아쉽네요. {pass_rate*100:.0f}% 정답률로 승급에 실패했습니다.")
                    st.info("더 많은 문제를 풀고 다시 도전하세요!")
                    del st.session_state.promotion_exam
                    st.rerun()
    
    else:
        st.info("승급 시험을 보려면 다음 조건을 충족해야 합니다:")
        
        # 다음 레벨 요구사항 표시
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT required_xp, min_accuracy, required_questions
                FROM level_requirements
                WHERE level = ?
            ''', (profile['level'] + 1,))
            
            req = cursor.fetchone()
            conn.close()
            
            if req:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    current_xp = profile['xp']
                    required_xp = req[0]
                    st.metric(
                        "경험치",
                        f"{current_xp} / {required_xp}",
                        f"{required_xp - current_xp} 필요"
                    )
                
                with col2:
                    current_acc = profile['accuracy'] if profile['accuracy'] is not None else 0.0
                    required_acc = req[1]
                    st.metric(
                        "정답률",
                        f"{current_acc:.1f}% / {required_acc}%",
                        f"{required_acc - current_acc:.1f}% 필요" if current_acc < required_acc else "달성!"
                    )
                
                with col3:
                    current_q = profile['total_questions']
                    required_q = req[2]
                    st.metric(
                        "문제 수",
                        f"{current_q} / {required_q}",
                        f"{required_q - current_q} 필요" if current_q < required_q else "달성!"
                    )
                
                # 진행률 표시
                st.markdown("---")
                st.markdown("### 📊 승급 진행률")
                
                # 경험치 진행률
                xp_progress = min(100, (current_xp / required_xp) * 100)
                st.progress(xp_progress / 100)
                st.caption(f"경험치: {xp_progress:.1f}%")
                
                # 정답률 진행률
                acc_progress = min(100, (current_acc / required_acc) * 100)
                st.progress(acc_progress / 100)
                st.caption(f"정답률: {acc_progress:.1f}%")
                
                # 문제 수 진행률
                q_progress = min(100, (current_q / required_q) * 100)
                st.progress(q_progress / 100)
                st.caption(f"문제 수: {q_progress:.1f}%")
                
        except Exception as e:
            st.error(f"승급 요구사항을 불러오는 중 오류가 발생했습니다: {str(e)}")
    
    # 승급 시험 가이드
    st.markdown("---")
    st.markdown("## 📚 승급 시험 가이드")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 🎯 승급 조건
        - **경험치**: 각 레벨별 요구 경험치 달성
        - **정답률**: 최소 정답률 유지
        - **문제 수**: 최소 문제 해결 수 달성
        
        ### 📝 시험 구성
        - 레벨별로 다른 문제 구성
        - 80% 이상 정답 시 승급
        - 실패 시 재도전 가능
        """)
    
    with col2:
        st.markdown("""
        ### 🏆 승급 혜택
        - **새로운 난이도** 문제 접근
        - **추가 기능** 해금
        - **특별 권한** 부여
        - **리더보드** 순위 상승
        
        ### 💡 팁
        - 꾸준한 연습으로 실력 향상
        - 다양한 난이도 문제 도전
        - 피드백을 통한 개선
        """)
