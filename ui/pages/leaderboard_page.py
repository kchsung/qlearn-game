# ui/pages/leaderboard_page.py
"""
리더보드 페이지 컴포넌트
"""

import streamlit as st
import pandas as pd
import sqlite3
from typing import Dict


def render_leaderboard(db_path: str, current_username: str):
    """리더보드 렌더링"""
    st.header("🏆 리더보드")
    
    # 리더보드 조회
    try:
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
        else:
            st.info("아직 리더보드 데이터가 없습니다. 문제를 풀어보세요!")
            
    except Exception as e:
        st.error(f"리더보드를 불러오는 중 오류가 발생했습니다: {str(e)}")
    
    # 추가 통계 정보
    st.markdown("---")
    st.markdown("## 📊 전체 통계")
    
    try:
        conn = sqlite3.connect(db_path)
        
        # 전체 사용자 수
        total_users = pd.read_sql_query("SELECT COUNT(*) as count FROM users", conn)['count'][0]
        
        # 전체 문제 해결 수
        total_solved = pd.read_sql_query("SELECT SUM(total_questions_solved) as count FROM users", conn)['count'][0]
        
        # 평균 정답률
        avg_accuracy = pd.read_sql_query("""
            SELECT AVG(CAST(correct_answers AS REAL) / NULLIF(total_questions_solved, 0) * 100) as avg_acc
            FROM users WHERE total_questions_solved > 0
        """, conn)['avg_acc'][0]
        
        conn.close()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("총 사용자", f"{total_users:,}")
        
        with col2:
            st.metric("해결된 문제", f"{total_solved:,}")
        
        with col3:
            st.metric("평균 정답률", f"{avg_accuracy:.1f}%" if avg_accuracy else "0.0%")
        
        with col4:
            st.metric("활성 사용자", f"{total_users:,}")  # 간단한 예시
        
    except Exception as e:
        st.error(f"통계를 불러오는 중 오류가 발생했습니다: {str(e)}")
