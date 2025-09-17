# ui/pages/stats_page.py
"""
통계 페이지 컴포넌트 (Supabase 기반)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from typing import Dict


def render_user_stats(db, user_id: str):
    """사용자 통계 렌더링"""
    
    try:
        # 사용자 통계 조회
        stats = db.get_user_stats(user_id)
        level_progress = db.get_level_progress(user_id)
        
        if not stats:
            st.info("아직 통계 데이터가 없습니다. 문제를 풀어보세요!")
            return
        
        # 기본 통계 표시
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("현재 레벨", stats.get('level', 1))
        
        with col2:
            st.metric("총 경험치", f"{stats.get('experience_points', 0):,}")
        
        with col3:
            st.metric("총 문제 수", stats.get('total_questions_solved', 0))
        
        with col4:
            st.metric("정답률", f"{stats.get('accuracy', 0):.1f}%")
        
        # 레벨 진행률
        if level_progress:
            st.subheader("🎯 레벨 진행률")
            
            progress_col1, progress_col2 = st.columns([2, 1])
            
            with progress_col1:
                progress = level_progress.get('progress_percentage', 0)
                st.progress(progress / 100)
                st.caption(f"현재 레벨 {level_progress.get('current_level', 1)}에서의 진행률")
            
            with progress_col2:
                st.metric("현재 XP", level_progress.get('level_xp', 0))
                st.metric("필요 XP", level_progress.get('level_requirement', 0))
        
        # 연속 정답 통계
        st.subheader("🔥 연속 정답")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("현재 연속", stats.get('current_streak', 0))
        
        with col2:
            st.metric("최고 연속", stats.get('best_streak', 0))
        
        # 정답률 분석
        if stats.get('total_questions_solved', 0) > 0:
            st.subheader("📊 정답률 분석")
            
            correct = stats.get('correct_answers', 0)
            total = stats.get('total_questions_solved', 0)
            incorrect = total - correct
            
            # 파이 차트
            fig = px.pie(
                values=[correct, incorrect],
                names=['정답', '오답'],
                title="정답률 분포",
                color_discrete_map={'정답': '#4CAF50', '오답': '#f44336'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # 레벨별 성과 (간단한 시뮬레이션)
        st.subheader("📈 레벨별 성과")
        
        # 레벨별 데이터 생성 (실제로는 DB에서 가져와야 함)
        level_data = {
            '레벨': [1, 2, 3, 4, 5],
            '문제 수': [10, 25, 40, 60, 80],
            '정답률': [70, 75, 80, 85, 90]
        }
        
        df = pd.DataFrame(level_data)
        
        # 레벨별 문제 수 차트
        fig1 = px.bar(
            df, 
            x='레벨', 
            y='문제 수',
            title="레벨별 해결한 문제 수",
            color='문제 수',
            color_continuous_scale='Blues'
        )
        st.plotly_chart(fig1, use_container_width=True)
        
        # 레벨별 정답률 차트
        fig2 = px.line(
            df, 
            x='레벨', 
            y='정답률',
            title="레벨별 정답률 추이",
            markers=True
        )
        fig2.update_layout(yaxis_title="정답률 (%)")
        st.plotly_chart(fig2, use_container_width=True)
        
        # 성과 요약
        st.subheader("🏆 성과 요약")
        
        if stats.get('accuracy', 0) >= 80:
            st.success("🎯 우수한 정답률을 유지하고 있습니다!")
        elif stats.get('accuracy', 0) >= 60:
            st.info("📈 꾸준히 실력을 향상시키고 있습니다!")
        else:
            st.warning("💪 더 많은 연습이 필요합니다!")
        
        if stats.get('best_streak', 0) >= 10:
            st.success("🔥 연속 정답 기록이 훌륭합니다!")
        elif stats.get('best_streak', 0) >= 5:
            st.info("⭐ 좋은 연속 정답 기록을 가지고 있습니다!")
        
    except Exception as e:
        st.error(f"통계 조회 중 오류가 발생했습니다: {str(e)}")
        st.info("잠시 후 다시 시도해주세요.")