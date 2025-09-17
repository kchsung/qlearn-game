# ui/pages/stats_page.py
"""
통계 페이지 컴포넌트
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
from typing import Dict


def render_user_stats(db_path: str, user_id: str):
    """사용자 통계 렌더링"""
    st.header("📈 내 통계")
    
    try:
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
        else:
            st.info("아직 문제 풀이 기록이 없습니다. 문제를 풀어보세요!")
        
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
        
        # 상세 통계 테이블
        st.markdown("---")
        st.markdown("## 📋 상세 기록")
        
        # 최근 시도 기록
        recent_attempts = pd.read_sql_query('''
            SELECT 
                attempt_date,
                question_id,
                level,
                passed,
                score,
                time_taken,
                tokens_used
            FROM attempt_history
            WHERE user_id = ?
            ORDER BY attempt_date DESC
            LIMIT 20
        ''', conn, params=[user_id])
        
        if not recent_attempts.empty:
            # 결과 표시를 위한 컬럼 추가
            recent_attempts['결과'] = recent_attempts['passed'].map({True: '✅ 통과', False: '❌ 실패'})
            recent_attempts['난이도'] = recent_attempts['level'].map({1: '초급', 2: '중급', 3: '고급'})
            
            # 표시할 컬럼만 선택
            display_columns = ['attempt_date', '난이도', '결과', 'score', 'time_taken', 'tokens_used']
            recent_attempts_display = recent_attempts[display_columns].copy()
            recent_attempts_display.columns = ['날짜', '난이도', '결과', '점수', '소요시간(초)', '토큰사용량']
            
            st.dataframe(recent_attempts_display, use_container_width=True)
        else:
            st.info("아직 시도 기록이 없습니다.")
        
        conn.close()
        
    except Exception as e:
        st.error(f"통계를 불러오는 중 오류가 발생했습니다: {str(e)}")
