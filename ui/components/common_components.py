# ui_components.py
"""
UI 컴포넌트 및 헬퍼 함수들
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Optional
import sqlite3

from config import LEVEL_ICONS


def safe_rerun():
    """Streamlit 버전에 관계없이 안전하게 페이지를 새로고침합니다."""
    try:
        if hasattr(st, 'rerun'):
            st.rerun()
        elif hasattr(st, 'experimental_rerun'):
            st.experimental_rerun()
        else:
            # 최후의 수단으로 페이지 새로고침
            st.markdown('<script>window.location.reload();</script>', unsafe_allow_html=True)
    except Exception:
        # 모든 방법이 실패하면 아무것도 하지 않음
        pass


def render_user_sidebar(profile: Dict, on_logout):
    """사용자 사이드바 렌더링"""
    with st.sidebar:
        # 사용자명으로 헤더 표시
        username = profile.get('username', '사용자')
        st.header(f"👤 {username}")
        
        # 프로필 이미지
        st.markdown(f'<img src="{profile["profile_image"]}" width="150">', unsafe_allow_html=True)
        
        # 게임 제목
        st.markdown("### AI Master Quest")
        
        # 레벨 정보
        st.markdown(f"**레벨 {profile['level']}** {profile['level_icon']} {profile['level_name']}")
        
        # 경험치 바
        xp_progress = (profile['xp'] / profile['next_level_xp']) * 100
        # 진행률을 0.0과 1.0 사이로 제한
        progress_value = min(1.0, max(0.0, xp_progress / 100))
        st.progress(progress_value)
        st.caption(f"XP: {profile['xp']} / {profile['next_level_xp']}")
        
        # 통계
        col1, col2 = st.columns(2)
        with col1:
            accuracy = profile['accuracy'] if profile['accuracy'] is not None else 0.0
            st.metric("정답률", f"{accuracy:.0f}%")
            st.metric("현재 연속", profile['current_streak'])
        
        with col2:
            st.metric("총 문제", profile['total_questions'])
            st.metric("최고 연속", profile['best_streak'])
        
        # 업적
        if profile['achievements']:
            st.markdown("### 🏆 업적")
            for ach in profile['achievements']:
                st.markdown(f"{ach[3]} **{ach[1]}**")
        
        # 로그아웃
        if st.button("로그아웃"):
            on_logout()


def render_login_form(on_login, on_signup):
    """로그인/회원가입 폼 렌더링"""
    with st.sidebar:
        st.header("👤 사용자 프로필")
        
        # 로그인/회원가입
        tab1, tab2 = st.tabs(["로그인", "회원가입"])
        
        with tab1:
            username = st.text_input("사용자명", key="login_username")
            if st.button("로그인", type="primary"):
                on_login(username)
        
        with tab2:
            new_username = st.text_input("사용자명", key="signup_username")
            email = st.text_input("이메일 (선택사항)")
            
            if st.button("가입하기", type="primary"):
                on_signup(new_username, email)


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
    st.markdown("👈 왼쪽 사이드바에서 로그인하거나 회원가입하여 시작하세요!")


def render_leaderboard(db_path: str, current_username: str):
    """리더보드 렌더링"""
    st.header("🏆 리더보드")
    
    # 리더보드 조회
    conn = sqlite3.connect(db_path)
    leaderboard = pd.read_sql_query('''
        SELECT * FROM leaderboard LIMIT 10
    ''', conn)
    conn.close()
    
    if not leaderboard.empty:
        # 리더보드 표시
        for idx, row in leaderboard.iterrows():
            rank = idx + 1
            medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(rank, "")
            
            col1, col2, col3, col4, col5 = st.columns([1, 3, 2, 2, 2])
            
            with col1:
                st.markdown(f"### {medal} {rank}")
            
            with col2:
                st.markdown(f"**{row['username']}**")
                st.caption(f"레벨 {row['level']}")
            
            with col3:
                st.metric("XP", f"{row['experience_points']:,}")
            
            with col4:
                accuracy = row['accuracy'] if row['accuracy'] is not None else 0.0
                st.metric("정답률", f"{accuracy:.1f}%")
            
            with col5:
                st.metric("최고 연속", row['best_streak'])
            
            if row['username'] == current_username:
                st.markdown("---")
                st.success("👆 내 순위")
                st.markdown("---")


def render_user_stats(db_path: str, user_id: str):
    """사용자 통계 렌더링"""
    st.header("📈 내 통계")
    
    # 상세 통계 조회
    conn = sqlite3.connect(db_path)
    
    # 시간별 활동
    activity = pd.read_sql_query('''
        SELECT 
            DATE(attempt_date) as date,
            COUNT(*) as attempts,
            SUM(passed) as correct,
            AVG(score) as avg_score
        FROM attempt_history
        WHERE user_id = ?
        GROUP BY DATE(attempt_date)
        ORDER BY date DESC
        LIMIT 30
    ''', conn, params=[user_id])
    
    if not activity.empty:
        # 활동 그래프
        fig = px.line(
            activity,
            x='date',
            y='attempts',
            title='일별 문제 풀이 활동',
            markers=True
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # 점수 추이
        fig2 = px.line(
            activity,
            x='date',
            y='avg_score',
            title='평균 점수 추이',
            markers=True
        )
        st.plotly_chart(fig2, use_container_width=True)
    
    # 난이도별 성과
    difficulty_stats = pd.read_sql_query('''
        SELECT 
            CASE 
                WHEN level <= 2 THEN 'basic'
                WHEN level <= 3 THEN 'intermediate'
                ELSE 'advanced'
            END as difficulty,
            COUNT(*) as total,
            SUM(passed) as passed,
            AVG(score) as avg_score
        FROM attempt_history
        WHERE user_id = ?
        GROUP BY difficulty
    ''', conn, params=[user_id])
    
    if not difficulty_stats.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            # 난이도별 정답률
            difficulty_stats['pass_rate'] = difficulty_stats['passed'] / difficulty_stats['total'] * 100
            fig3 = px.bar(
                difficulty_stats,
                x='difficulty',
                y='pass_rate',
                title='난이도별 정답률'
            )
            st.plotly_chart(fig3, use_container_width=True)
        
        with col2:
            # 난이도별 평균 점수
            fig4 = px.bar(
                difficulty_stats,
                x='difficulty',
                y='avg_score',
                title='난이도별 평균 점수'
            )
            st.plotly_chart(fig4, use_container_width=True)
    
    conn.close()


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
                    safe_rerun()
            
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
                else:
                    st.error(f"아쉽네요. {pass_rate*100:.0f}% 정답률로 승급에 실패했습니다.")
                    st.info("더 많은 문제를 풀고 다시 도전하세요!")
                    del st.session_state.promotion_exam
    
    else:
        st.info("승급 시험을 보려면 다음 조건을 충족해야 합니다:")
        
        # 다음 레벨 요구사항 표시
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
