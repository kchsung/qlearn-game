# main.py
"""
AI Master Quest - AI 활용능력평가 게임
메인 실행 파일
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from src.app import AIAssessmentGame

# 페이지 설정
st.set_page_config(
    page_title="AI Master Quest - AI 활용능력평가 게임",
    page_icon="🎮",
    layout="wide"
)

# CSS 스타일
st.markdown("""
<style>
.stProgress > div > div > div > div {
    background-image: linear-gradient(to right, #4CAF50, #45a049);
}
.achievement-badge {
    display: inline-block;
    padding: 5px 10px;
    margin: 2px;
    border-radius: 15px;
    background-color: #f0f0f0;
    font-size: 14px;
}
.level-badge {
    font-size: 24px;
    font-weight: bold;
    color: #4CAF50;
}
</style>
""", unsafe_allow_html=True)

def main():
    """메인 함수"""
    # 애플리케이션 실행
    app = AIAssessmentGame()
    app.run()

if __name__ == "__main__":
    main()
