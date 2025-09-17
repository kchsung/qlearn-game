# ui/pages/leaderboard_page.py
"""
리더보드 페이지 컴포넌트 (Supabase 기반)
"""

import streamlit as st
import pandas as pd
from typing import Dict


def render_leaderboard(db, current_username: str):
    """리더보드 렌더링"""
    
    # 리더보드 조회
    try:
        leaderboard_data = db.get_leaderboard(limit=10)
        
        if leaderboard_data:
            # DataFrame으로 변환
            leaderboard = pd.DataFrame(leaderboard_data)
            
            # 정답률 계산
            leaderboard['accuracy'] = (leaderboard['correct_answers'] / leaderboard['total_questions_solved'] * 100).fillna(0)
            
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
                    st.metric("문제 수", row['total_questions_solved'])
                
                # 현재 사용자 강조
                if row['username'] == current_username:
                    st.markdown("---")
                    st.success("🎯 이것이 당신의 순위입니다!")
                    st.markdown("---")
            
            # 통계 요약
            st.subheader("📊 통계 요약")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_users = len(leaderboard)
                st.metric("총 사용자", total_users)
            
            with col2:
                avg_xp = leaderboard['experience_points'].mean()
                st.metric("평균 XP", f"{avg_xp:.0f}")
            
            with col3:
                avg_accuracy = leaderboard['accuracy'].mean()
                st.metric("평균 정답률", f"{avg_accuracy:.1f}%")
            
            with col4:
                max_level = leaderboard['level'].max()
                st.metric("최고 레벨", max_level)
            
            # 차트 표시
            st.subheader("📈 레벨 분포")
            
            level_counts = leaderboard['level'].value_counts().sort_index()
            st.bar_chart(level_counts)
            
        else:
            st.info("아직 리더보드 데이터가 없습니다. 문제를 풀어보세요!")
            
    except Exception as e:
        st.error(f"리더보드 조회 중 오류가 발생했습니다: {str(e)}")
        st.info("잠시 후 다시 시도해주세요.")